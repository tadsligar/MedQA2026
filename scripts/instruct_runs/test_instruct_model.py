"""
Paper 1 EXP2 — Instruction-tuned model evaluation (chat API).

Mirrors the base-model evaluation (same dataset, same first-valid-letter extraction, same
output schema) but uses the vLLM **chat** endpoint (/v1/chat/completions) with the model's
chat template and a minimal instruction. This gives a clean base-vs-instruct controlled
comparison; the base numbers come from results/base_runs/ (Paper 1, verified).

The chat prompt is deliberately minimal (content mirrors the base prompt) so the contrast
isolates instruction tuning, not prompt engineering. The exact template is logged to
`prompt_template.txt` in the output dir for the appendix.

Output schema matches the base runs (question_id, category, correct, predicted, is_correct,
tokens, latency, response). Defaults to the full 3-temperature x 3-run grid to match Paper 1;
use --temperatures / --n-runs to shrink (e.g. t=0.0 x1 for a quick headline table).

Usage (see slurm/instruct/*.sbatch):
    python scripts/instruct_runs/test_instruct_model.py \
        --model-name "Qwen/Qwen2.5-7B-Instruct" \
        --output-dir "results/instruct_runs/qwen25_7b_instruct" \
        --dataset "data/datasets/medqa_focused_1030.json" \
        --vllm-url "http://localhost:8000"
"""
import json
import sys
import time
import re
import argparse
from pathlib import Path
from collections import defaultdict
import requests

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent.parent))  # scripts/ -> shared mcq_options
import mcq_options as mcq

# Minimal instruction mirroring base-prompt content (logged for the appendix).
# {letters} is filled per-question from the options actually present (e.g. four letters for a
# 4-option item, five for a 5-option item) so the model always sees every option.
SYSTEM_MSG = "You are answering a multiple-choice medical exam question."
USER_TEMPLATE = """Question: {question}

Options:
{options_text}

Answer with only the single letter ({letters}) of the best option."""


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


def call_vllm_chat(question, options_text, letters_text, temperature, base_url, max_tokens=512, timeout=120):
    """Call vLLM /v1/chat/completions with the model's chat template."""
    url = f"{base_url}/v1/chat/completions"
    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_MSG},
            {"role": "user", "content": USER_TEMPLATE.format(
                question=question, options_text=options_text, letters=letters_text)},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": 1.0,
        "n": 1,
    }
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        text = data['choices'][0]['message']['content']
        tokens = data['usage'].get('completion_tokens', 0)
        return text, tokens
    except requests.exceptions.Timeout:
        print(f"  WARNING: timeout after {timeout}s, fallback")
        return "A", 0
    except Exception as e:
        print(f"  ERROR: {e}")
        return "A", 0


def load_checkpoint(output_dir, temperature, run_number):
    cf = output_dir / f"temp{temperature}_run{run_number}_checkpoint.json"
    if cf.exists():
        with open(cf, 'r', encoding='utf-8') as f:
            c = json.load(f)
        return c['results'], c['next_index']
    return [], 0


def save_checkpoint(output_dir, temperature, run_number, results, next_index):
    cf = output_dir / f"temp{temperature}_run{run_number}_checkpoint.json"
    with open(cf, 'w', encoding='utf-8') as f:
        json.dump({'temperature': temperature, 'run_number': run_number,
                   'results': results, 'next_index': next_index, 'timestamp': time.time()},
                  f, indent=2, ensure_ascii=False)


def run_one(questions, temperature, run_number, output_dir, model_name, vllm_url):
    print(f"\n{'='*80}\nTEMP {temperature} RUN {run_number} (instruct/chat)  Model: {model_name}\n{'='*80}")
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
        letters_text = mcq.letters_phrase(letters)

        t0 = time.time()
        text, tokens = call_vllm_chat(question, options_text, letters_text, temperature, vllm_url)
        latency = time.time() - t0
        predicted = mcq.extract_first(text, letters)
        is_correct = (predicted == correct_answer)

        results.append({
            'question_id': idx, 'category': category, 'correct': correct_answer,
            'predicted': predicted, 'is_correct': is_correct, 'tokens': tokens,
            'latency': latency, 'response': text[:200],
        })
        if (idx + 1) % 10 == 0:
            save_checkpoint(output_dir, temperature, run_number, results, idx + 1)
            acc = sum(r['is_correct'] for r in results) / len(results) * 100
            print(f"  [{idx+1}/{len(questions)}] acc={acc:.2f}%")
    acc = sum(r['is_correct'] for r in results) / len(results) * 100
    rf = output_dir / f"temp{temperature}_run{run_number}_results.json"
    with open(rf, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Done temp {temperature} run {run_number}: acc={acc:.2f}% -> {rf}")
    return acc


def main():
    ap = argparse.ArgumentParser(description='Instruct model evaluation (Paper 1 EXP2)')
    ap.add_argument('--model-name', required=True)
    ap.add_argument('--output-dir', required=True)
    ap.add_argument('--dataset', default='data/datasets/medqa_focused_1030.json')
    ap.add_argument('--vllm-url', default='http://localhost:8000')
    ap.add_argument('--temperatures', default='0.0,0.3,0.7')
    ap.add_argument('--n-runs', type=int, default=3)
    args = ap.parse_args()

    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    # Log the exact prompt template for the appendix
    with open(out / "prompt_template.txt", "w") as f:
        f.write("SYSTEM:\n" + SYSTEM_MSG + "\n\nUSER:\n" + USER_TEMPLATE + "\n")
    with open(project_root / args.dataset, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    print(f"Loaded {len(questions)} questions; model={args.model_name}")

    temps = [float(t) for t in args.temperatures.split(',')]
    for temp in temps:
        for run in range(1, args.n_runs + 1):
            run_one(questions, temp, run, out, args.model_name, args.vllm_url)


if __name__ == "__main__":
    main()
