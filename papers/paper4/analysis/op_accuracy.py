#!/usr/bin/env python3
"""
Paper 4 — accuracy by reasoning OPERATION (R/F/B/I/W) and by ORGAN SYSTEM (multi-label),
computed on the EXISTING full-set base runs (no GPU, no new inference).

Joins operation/system labels (results/reasoning_ops/op_labels.jsonl, keyed by qid) with
results/base_runs_full/<model>/temp0.0_run*_results.json (keyed by question_id). Per-question
correctness = majority across the available greedy runs (integer counts -> clean Wilson CIs).

Outputs (papers/paper4/tables/):
  op_accuracy.csv        model, operation, n, acc, ci_lo, ci_hi
  system_accuracy.csv    model, system, n_questions, acc, ci_lo, ci_hi   (multi-label; rows overlap)
Self-skips if the label file is absent.
"""
import os, json, glob, math, argparse
from collections import defaultdict, Counter
import pandas as pd

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
FULL = os.path.join(_REPO, "results", "base_runs_full")
OUT = os.path.join(_REPO, "papers", "paper4", "tables")
os.makedirs(OUT, exist_ok=True)

MODELS = ["olmo3_7b", "olmo3_32b", "qwen25_7b", "qwen25_14b", "qwen25_32b"]
NAME = {"olmo3_7b": "OLMo-3 7B", "olmo3_32b": "OLMo-3 32B", "qwen25_7b": "Qwen2.5 7B",
        "qwen25_14b": "Qwen2.5 14B", "qwen25_32b": "Qwen2.5 32B"}
OP_NAME = {"R": "Recognition", "F": "Mechanistic (forward)", "B": "Diagnostic (backward)",
           "I": "Interventional", "W": "Workup"}
SYSTEMS = ["Cardiovascular", "Respiratory", "Gastrointestinal", "RenalUrinary", "Reproductive",
           "EndocrineMetabolic", "Nervous", "SpecialSenses", "Hematologic", "Immune",
           "Infectious", "Musculoskeletal", "Skin", "Behavioral", "Multisystem"]


def wilson(k, n, z=1.96):
    if n == 0: return (None, None)
    p = k / n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = (z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))) / d
    return (round(100*(c-h), 2), round(100*(c+h), 2))


def load_runs(model, temp=0.0):
    """qid -> majority-correct (bool) across available runs at this temp."""
    per = defaultdict(list)
    for f in glob.glob(os.path.join(FULL, model, f"temp{temp}_run*_results.json")):
        for r in json.load(open(f)):
            ic = r["is_correct"]
            ic = ic if isinstance(ic, bool) else str(ic).lower() == "true"
            per[int(r["question_id"])].append(ic)
    return {q: (sum(v) * 2 >= len(v)) for q, v in per.items()}  # majority (ties -> correct)


def load_labels(path):
    op, sysmap = {}, {}
    for line in open(path):
        try:
            o = json.loads(line)
        except Exception:
            continue
        if o.get("parse_fail") or not o.get("reasoning_operation"):
            continue
        qid = int(o["qid"])
        op[qid] = o["reasoning_operation"]
        sysmap[qid] = {s for s in SYSTEMS if (o.get("systems", {}) or {}).get(s) == "Y"}
    return op, sysmap


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", default=os.path.join(_REPO, "results/reasoning_ops/op_labels.jsonl"))
    args = ap.parse_args()
    if not os.path.exists(args.labels):
        print("No labels yet:", args.labels, "\nRun the labeler first (API batch or vLLM SLURM).")
        return
    op, sysmap = load_labels(args.labels)
    print(f"labels: {len(op)} questions")
    print("operation distribution:", Counter(op.values()).most_common())
    sys_counts = Counter(s for ss in sysmap.values() for s in ss)
    print("system involvement (multi-label) counts:", sys_counts.most_common())

    op_rows, sys_rows = [], []
    for m in MODELS:
        runs = load_runs(m)
        if not runs:
            continue
        by_op = defaultdict(lambda: [0, 0])     # op -> [k, n]
        by_sys = defaultdict(lambda: [0, 0])
        for qid, o in op.items():
            if qid not in runs:
                continue
            c = 1 if runs[qid] else 0
            by_op[o][0] += c; by_op[o][1] += 1
            for s in sysmap.get(qid, ()):
                by_sys[s][0] += c; by_sys[s][1] += 1
        for o, (k, n) in by_op.items():
            lo, hi = wilson(k, n)
            op_rows.append({"model": NAME[m], "operation": OP_NAME.get(o, o), "code": o,
                            "n": n, "acc": round(100*k/n, 2), "ci_lo": lo, "ci_hi": hi})
        for s, (k, n) in by_sys.items():
            lo, hi = wilson(k, n)
            sys_rows.append({"model": NAME[m], "system": s, "n_questions": n,
                             "acc": round(100*k/n, 2), "ci_lo": lo, "ci_hi": hi})
    pd.DataFrame(op_rows).to_csv(os.path.join(OUT, "op_accuracy.csv"), index=False)
    pd.DataFrame(sys_rows).to_csv(os.path.join(OUT, "system_accuracy.csv"), index=False)
    print("\n=== Accuracy by reasoning operation (t=0.0, majority of runs) ===")
    if op_rows:
        df = pd.DataFrame(op_rows)
        print(df.pivot(index="operation", columns="model", values="acc").to_string())
    print("\nWrote op_accuracy.csv + system_accuracy.csv to", OUT)


if __name__ == "__main__":
    main()
