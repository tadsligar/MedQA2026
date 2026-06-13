"""
Paper 1 EXP1 — Base Model evaluation WITH token log-probabilities (calibration).

Identical decoding/prompt/extraction to scripts/base_runs/test_base_model.py so accuracy
reproduces the verified numbers, but requests vLLM `logprobs` and records, per question,
the model's probability distribution over the option letters present for THAT question
(A-D for the 4-option focused set, A-E for the 5-option full set) at the first answer-letter
position. This enables true calibration analysis (ECE, reliability diagrams, risk-coverage)
instead of the stability proxy used in Paper 1.

Output schema extends the base-run schema with:
    answer_logprob   : logprob assigned to the predicted letter at the answer position
    option_logprobs  : per-present-letter raw logprobs at the answer position (missing -> None)
    option_probs     : softmax of option_logprobs over the present letters (sums to 1)
    confidence       : max(option_probs)
    margin           : top1 - top2 option probability
    answer_pos       : index of the first option-letter token in the generated sequence (or -1)

By default runs only t=0.0, run 1 (the deterministic headline condition). Use
--temperatures / --n-runs to extend (e.g. for confidence-vs-temperature).

Usage (see slurm/logprobs/*.sbatch):
    python scripts/base_runs/test_base_model_logprobs.py \
        --model-name "Qwen/Qwen2.5-7B" \
        --output-dir "results/base_runs_logprobs/qwen25_7b" \
        --dataset "data/datasets/medqa_focused_1030.json" \
        --vllm-url "http://localhost:8000"
"""

import json
import sys
import time
import re
import math
import argparse
from pathlib import Path
from collections import defaultdict
import requests

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent.parent))  # scripts/ -> shared mcq_options
import mcq_options as mcq


def categorize_question(question_text):
    q = question_text.lower()
    if 'most likely diagnosis' in q or 'most likely cause of' in q:
        return 'Diagnosis'
    elif 'next step' in q or 'next best' in q or 'initial step' in q:
        return 'Next Step/Workup'
    elif 'treatment' in q or 'management' in q or 'which drug' in q:
        return 'Treatment/Management'
    elif 'mechanism' in q or 'action' in q or 'pathway' in q:
        return 'Mechanism/Pathophysiology'
    elif 'most likely to show' in q or 'expected finding' in q:
        return 'Clinical Findings'
    else:
        return 'Other/Mixed'


def softmax_over_letters(option_logprobs, letters):
    """Softmax over present (non-None) letter logprobs; returns dict letter->prob."""
    present = {k: v for k, v in option_logprobs.items() if v is not None}
    if not present:
        return {l: None for l in letters}
    m = max(present.values())
    exps = {k: math.exp(v - m) for k, v in present.items()}
    z = sum(exps.values())
    probs = {l: (exps[l] / z if l in exps else 0.0) for l in letters}
    return probs


def parse_letter_logprobs(logprobs_obj, letters):
    """
    From a vLLM completions `logprobs` object, locate the first generated token whose
    stripped text is one of THIS question's option letters, and read that position's top-k
    distribution to get a logprob for each present letter (max over surface variants like
    ' A' vs 'A').

    Returns (answer_pos, {letter: logprob-or-None}).
    """
    letter_set = {l.upper() for l in letters}
    tokens = logprobs_obj.get('tokens') or []
    top = logprobs_obj.get('top_logprobs') or []
    answer_pos = -1
    for i, tok in enumerate(tokens):
        if tok is not None and tok.strip().upper() in letter_set:
            answer_pos = i
            break
    if answer_pos == -1 or answer_pos >= len(top) or top[answer_pos] is None:
        return answer_pos, {l: None for l in letters}
    dist = top[answer_pos]  # dict: token-string -> logprob
    letter_lp = {l: None for l in letters}
    for tok_str, lp in dist.items():
        key = tok_str.strip().upper()
        if key in letter_lp:
            if letter_lp[key] is None or lp > letter_lp[key]:
                letter_lp[key] = lp
    return answer_pos, letter_lp


def call_vllm_logprobs(prompt, temperature, base_url, max_tokens=800, n_logprobs=20, timeout=120):
    """Call vLLM /v1/completions with logprobs enabled."""
    url = f"{base_url}/v1/completions"
    payload = {
        "prompt": prompt,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": 1.0,
        "n": 1,
        "logprobs": n_logprobs,
    }
    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        choice = data['choices'][0]
        text = choice['text']
        tokens = data['usage'].get('completion_tokens', 0)
        logprobs_obj = choice.get('logprobs') or {}
        return text, tokens, logprobs_obj
    except requests.exceptions.Timeout:
        print(f"  WARNING: Request timed out after {timeout}s, using fallback")
        return "A", 0, {}
    except Exception as e:
        print(f"  ERROR: {e}")
        return "A", 0, {}


def load_checkpoint(output_dir, temperature, run_number):
    cf = output_dir / f"temp{temperature}_run{run_number}_checkpoint.json"
    if cf.exists():
        with open(cf, 'r', encoding='utf-8') as f:
            ckpt = json.load(f)
        return ckpt['results'], ckpt['next_index']
    return [], 0


def save_checkpoint(output_dir, temperature, run_number, results, next_index):
    cf = output_dir / f"temp{temperature}_run{run_number}_checkpoint.json"
    with open(cf, 'w', encoding='utf-8') as f:
        json.dump({'temperature': temperature, 'run_number': run_number,
                   'results': results, 'next_index': next_index,
                   'timestamp': time.time()}, f, indent=2, ensure_ascii=False)


def run_one(questions, temperature, run_number, output_dir, model_name, vllm_url):
    print(f"\n{'='*80}\nTEMP {temperature} RUN {run_number} (logprobs)  Model: {model_name}\n{'='*80}")
    results, start_idx = load_checkpoint(output_dir, temperature, run_number)
    if start_idx > 0:
        print(f"Resuming from {start_idx}/{len(questions)}")

    for idx in range(start_idx, len(questions)):
        item = questions[idx]
        question = item['question']
        options = mcq.normalize_options(item['options'])
        letters = mcq.option_letters(options)
        category = item.get('validated_category', categorize_question(question))

        correct_answer = mcq.answer_letter(item, options)
        options_text = mcq.render_options(options)
        prompt = f"""Question: {question}

Options:
{options_text}

Answer:"""

        t0 = time.time()
        text, tokens, lp_obj = call_vllm_logprobs(prompt, temperature, vllm_url)
        latency = time.time() - t0

        predicted = mcq.extract_first(text, letters)
        is_correct = (predicted == correct_answer)
        answer_pos, option_logprobs = parse_letter_logprobs(lp_obj, letters)
        option_probs = softmax_over_letters(option_logprobs, letters)
        # confidence + margin from probs
        present_probs = sorted([p for p in option_probs.values() if p is not None], reverse=True)
        confidence = present_probs[0] if present_probs else None
        margin = (present_probs[0] - present_probs[1]) if len(present_probs) >= 2 else None
        answer_logprob = option_logprobs.get(predicted)

        results.append({
            'question_id': idx,
            'category': category,
            'correct': correct_answer,
            'predicted': predicted,
            'is_correct': is_correct,
            'tokens': tokens,
            'latency': latency,
            'response': text[:200],
            'answer_pos': answer_pos,
            'answer_logprob': answer_logprob,
            'option_logprobs': option_logprobs,
            'option_probs': option_probs,
            'confidence': confidence,
            'margin': margin,
        })

        if (idx + 1) % 10 == 0:
            save_checkpoint(output_dir, temperature, run_number, results, idx + 1)
            acc = sum(r['is_correct'] for r in results) / len(results) * 100
            cov = sum(1 for r in results if r['confidence'] is not None) / len(results) * 100
            print(f"  [{idx+1}/{len(questions)}] acc={acc:.2f}% logprob-coverage={cov:.1f}%")

    acc = sum(r['is_correct'] for r in results) / len(results) * 100
    rf = output_dir / f"temp{temperature}_run{run_number}_results.json"
    with open(rf, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Done temp {temperature} run {run_number}: acc={acc:.2f}%  -> {rf}")
    return acc


def main():
    ap = argparse.ArgumentParser(description='Base model logprobs/calibration run (Paper 1 EXP1)')
    ap.add_argument('--model-name', required=True)
    ap.add_argument('--output-dir', required=True)
    ap.add_argument('--dataset', default='data/datasets/medqa_focused_1030.json')
    ap.add_argument('--vllm-url', default='http://localhost:8000')
    ap.add_argument('--temperatures', default='0.0',
                    help='comma-separated, e.g. "0.0" or "0.0,0.3,0.7"')
    ap.add_argument('--n-runs', type=int, default=1)
    ap.add_argument('--run-index', type=int, default=None,
                    help='Write exactly this single run number (e.g. 2 -> temp{T}_run2_results.json). '
                         'Takes precedence over --n-runs. Everything else (prompt, greedy t=0.0, '
                         'logprobs, first-valid-letter extraction) is identical.')
    args = ap.parse_args()

    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    with open(project_root / args.dataset, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    print(f"Loaded {len(questions)} questions; model={args.model_name}")

    temps = [float(t) for t in args.temperatures.split(',')]
    for temp in temps:
        if args.run_index is not None:
            # Explicit single run number; takes precedence over --n-runs.
            run_one(questions, temp, args.run_index, out, args.model_name, args.vllm_url)
        else:
            for run in range(1, args.n_runs + 1):
                run_one(questions, temp, run, out, args.model_name, args.vllm_url)


if __name__ == "__main__":
    main()
