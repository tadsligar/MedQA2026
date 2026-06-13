"""
Paper 1 EXP3/EXP4/EXP5 — base-model variants runner.

One flexible runner covering three experiments on the focused 1,030-set, all via the vLLM
completions endpoint (base models):

  EXP3 prompt-format ablation  : --prompt-variant {v0,v1,v2,v3}
  EXP4 chain-of-thought vs direct: --mode {direct,cot}  (cot raises max-tokens, extracts the
                                   FINAL letter)
  EXP5 self-consistency scaling : --n-samples K at a fixed temperature (stores all K predictions)

Output schema matches the base runs (+ `all_predictions` when n-samples>1, + `variant`/`mode`).
Extraction is first-valid-letter for direct, last-after-"answer" for CoT.

Examples (see slurm/variants/*.sbatch):
  # EXP3 prompt ablation, greedy, variant v1
  python scripts/base_runs/test_base_model_variants.py --model-name Qwen/Qwen2.5-14B \
      --output-dir results/prompt_ablation/qwen25_14b --prompt-variant v1 --temperatures 0.0 --n-runs 1
  # EXP4 CoT
  python scripts/base_runs/test_base_model_variants.py --model-name Qwen/Qwen2.5-14B \
      --output-dir results/cot_vs_direct/qwen25_14b --mode cot --max-tokens 1024 \
      --temperatures 0.0,0.7 --n-runs 3
  # EXP5 self-consistency k=20 at t=0.7
  python scripts/base_runs/test_base_model_variants.py --model-name Qwen/Qwen2.5-14B \
      --output-dir results/self_consistency/qwen25_14b --temperatures 0.7 --n-runs 1 --n-samples 20
"""
import json, sys, time, re, argparse
from pathlib import Path
from collections import Counter
import requests

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent.parent))  # scripts/ -> shared mcq_options
import mcq_options as mcq

# EXP3 prompt variants (v0 = the original base prompt)
PROMPT_VARIANTS = {
    "v0": "Question: {q}\n\nOptions:\n{opts}\n\nAnswer:",
    "v1": "Question: {q}\n\nOptions:\n{opts}\n\nAnswer with only the letter.\nAnswer:",
    "v2": "{q}\n\n{opts}\n\nThe best answer is option",
    "v3": "The following is a USMLE-style multiple choice question.\n\nQuestion: {q}\n\nOptions:\n{opts}\n\nAnswer:",
}
COT_PROMPT = ("Question: {q}\n\nOptions:\n{opts}\n\n"
              "Let's reason step by step, then end with 'Answer: X' where X is the letter.\n")


def categorize_question(t):
    q = t.lower()
    if 'most likely diagnosis' in q or 'most likely cause of' in q: return 'Diagnosis'
    if 'next step' in q or 'next best' in q or 'initial step' in q: return 'Next Step/Workup'
    if 'treatment' in q or 'management' in q or 'which drug' in q: return 'Treatment/Management'
    if 'mechanism' in q or 'action' in q or 'pathway' in q: return 'Mechanism/Pathophysiology'
    if 'most likely to show' in q or 'expected finding' in q: return 'Clinical Findings'
    return 'Other/Mixed'


def call_completions(prompt, temperature, base_url, max_tokens, n, timeout=180):
    url = f"{base_url}/v1/completions"
    payload = {"prompt": prompt, "temperature": temperature, "max_tokens": max_tokens,
               "top_p": 1.0, "n": n}
    try:
        r = requests.post(url, json=payload, timeout=timeout); r.raise_for_status()
        data = r.json()
        texts = [c['text'] for c in data['choices']]
        tokens = data['usage'].get('completion_tokens', 0)
        return texts, tokens
    except requests.exceptions.Timeout:
        print(f"  WARNING: timeout {timeout}s"); return ["A"] * n, 0
    except Exception as e:
        print(f"  ERROR: {e}"); return ["A"] * n, 0


def build_prompt(item, options, mode, variant):
    opts = mcq.render_options(options)
    if mode == "cot":
        return COT_PROMPT.format(q=item['question'], opts=opts)
    return PROMPT_VARIANTS[variant].format(q=item['question'], opts=opts)


def load_ckpt(d, temp, run):
    f = d / f"temp{temp}_run{run}_checkpoint.json"
    if f.exists():
        c = json.load(open(f)); return c['results'], c['next_index']
    return [], 0


def save_ckpt(d, temp, run, results, nxt):
    json.dump({'results': results, 'next_index': nxt, 'timestamp': time.time()},
              open(d / f"temp{temp}_run{run}_checkpoint.json", 'w'), indent=2, ensure_ascii=False)


def run_one(questions, temp, run, out, model, url, mode, variant, max_tokens, n_samples):
    print(f"\n{'='*80}\nTEMP {temp} RUN {run} mode={mode} variant={variant} k={n_samples}\n{'='*80}")
    results, start = load_ckpt(out, temp, run)
    for idx in range(start, len(questions)):
        item = questions[idx]
        options = mcq.normalize_options(item['options'])
        letters = mcq.option_letters(options)
        correct = mcq.answer_letter(item, options)
        cat = item.get('validated_category', categorize_question(item['question']))
        prompt = build_prompt(item, options, mode, variant)
        t0 = time.time()
        texts, tokens = call_completions(prompt, temp, url, max_tokens, n_samples)
        latency = time.time() - t0
        preds = [(mcq.extract_cot(t, letters) if mode == "cot" else mcq.extract_first(t, letters))
                 for t in texts]
        if n_samples > 1:
            modal = Counter(preds).most_common(1)[0][0]
            predicted = modal
        else:
            predicted = preds[0]
        rec = {'question_id': idx, 'category': cat, 'correct': correct,
               'predicted': predicted, 'is_correct': predicted == correct,
               'tokens': tokens, 'latency': latency, 'response': texts[0][:200],
               'mode': mode, 'variant': variant}
        if n_samples > 1:
            rec['all_predictions'] = preds
        results.append(rec)
        if (idx + 1) % 10 == 0:
            save_ckpt(out, temp, run, results, idx + 1)
            acc = sum(r['is_correct'] for r in results) / len(results) * 100
            print(f"  [{idx+1}/{len(questions)}] acc={acc:.2f}%")
    acc = sum(r['is_correct'] for r in results) / len(results) * 100
    json.dump(results, open(out / f"temp{temp}_run{run}_results.json", 'w'),
              indent=2, ensure_ascii=False)
    print(f"Done temp {temp} run {run}: acc={acc:.2f}%")
    return acc


def main():
    ap = argparse.ArgumentParser(description='Base-model variants (Paper 1 EXP3/4/5)')
    ap.add_argument('--model-name', required=True)
    ap.add_argument('--output-dir', required=True)
    ap.add_argument('--dataset', default='data/datasets/medqa_focused_1030.json')
    ap.add_argument('--vllm-url', default='http://localhost:8000')
    ap.add_argument('--mode', choices=['direct', 'cot'], default='direct')
    ap.add_argument('--prompt-variant', choices=list(PROMPT_VARIANTS), default='v0')
    ap.add_argument('--max-tokens', type=int, default=800)
    ap.add_argument('--temperatures', default='0.0')
    ap.add_argument('--n-runs', type=int, default=1)
    ap.add_argument('--n-samples', type=int, default=1, help='samples/question (EXP5 self-consistency)')
    args = ap.parse_args()
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    questions = json.load(open(project_root / args.dataset, encoding='utf-8'))
    print(f"Loaded {len(questions)} questions; model={args.model_name} mode={args.mode} "
          f"variant={args.prompt_variant} k={args.n_samples}")
    for temp in [float(t) for t in args.temperatures.split(',')]:
        for run in range(1, args.n_runs + 1):
            run_one(questions, temp, run, out, args.model_name, args.vllm_url,
                    args.mode, args.prompt_variant, args.max_tokens, args.n_samples)


if __name__ == "__main__":
    main()
