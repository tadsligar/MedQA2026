#!/usr/bin/env python3
"""
Decisive cheap test: does labeling the reasoning operation from the LEAD-IN (final question
sentence) + options agree better with the human gold than the full-question labeling did?

Sends ONLY the lead-in + options (no vignette) for the 100 gold qids to gpt-5.4-mini, using the
SAME operation rubric, and scores vs results/reasoning_ops/gold_op_labels.jsonl.
Baseline to beat: full-question gpt-5.4-mini agreement = 70% / kappa 0.625 (see VALIDATION.md).

The human gold was itself labeled from ask+options only (gold_op_views.jsonl), so this is
apples-to-apples. If kappa jumps, the lead-in rule is confirmed and we relabel the full set
lead-in-only (and likely skip consensus-filtering).

Run (needs openai>=1.x and your key):
  export OPENAI_API_KEY=sk-...
  export CLASSIFIER_MODEL=gpt-5.4-mini
  python papers/paper4/analysis/validate_leadin_labeling.py
"""
import os, json, importlib.util
from collections import Counter

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
HERE = os.path.join(REPO, "scripts", "dataset_generation")
_spec = importlib.util.spec_from_file_location("ol", os.path.join(HERE, "operation_labeler.py"))
ol = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(ol)
OPS = ["R", "F", "B", "I", "W"]
MODEL = os.environ.get("CLASSIFIER_MODEL", "gpt-5.4-mini")


def kappa(pairs):
    N = len(pairs); po = sum(1 for a, b in pairs if a == b)/N
    ga = Counter(a for a, _ in pairs); gb = Counter(b for _, b in pairs)
    pe = sum((ga[c]/N)*(gb[c]/N) for c in set(list(ga)+list(gb)))
    return (po-pe)/(1-pe) if pe < 1 else 1.0


def main():
    from openai import OpenAI
    c = OpenAI()
    views = {json.loads(l)["qid"]: json.loads(l) for l in
             open(os.path.join(REPO, "results/reasoning_ops/gold_op_views.jsonl"))}
    gold = {json.loads(l)["qid"]: json.loads(l)["reasoning_operation"] for l in
            open(os.path.join(REPO, "results/reasoning_ops/gold_op_labels.jsonl"))}
    pairs, leadin_lab = [], {}
    for qid, g in gold.items():
        v = views[qid]
        user = f"Question (final sentence only): {v['ask']}\n\nOptions:\n{v['options']}"
        r = c.chat.completions.create(
            model=MODEL, reasoning_effort="none", max_completion_tokens=512,
            messages=[{"role": "system", "content": ol.RUBRIC}, {"role": "user", "content": user}])
        parsed = ol.parse(r.choices[0].message.content)
        op = parsed["reasoning_operation"] if parsed else "?"
        leadin_lab[qid] = op
        if op in OPS:
            pairs.append((g, op))
    agree = sum(1 for a, b in pairs if a == b)
    print(f"lead-in-only vs human gold: {agree}/{len(pairs)} = {100*agree/len(pairs):.1f}%  "
          f"kappa={kappa(pairs):.3f}")
    print("(baseline full-question gpt vs gold: 70.0% / 0.625)")
    print("\nConfusion (gold rows, lead-in-gpt cols):")
    print("   "+"  ".join(f"{c_:>4}" for c_ in OPS))
    for g in OPS:
        row = Counter(b for a, b in pairs if a == g)
        print(f"{g:>2} "+"  ".join(f"{row.get(c_,0):>4}" for c_ in OPS))
    json.dump({str(k): v for k, v in leadin_lab.items()},
              open(os.path.join(REPO, "results/reasoning_ops/.leadin_gold_probe.json"), "w"))
    print("\nsaved per-qid lead-in labels -> results/reasoning_ops/.leadin_gold_probe.json")


if __name__ == "__main__":
    main()
