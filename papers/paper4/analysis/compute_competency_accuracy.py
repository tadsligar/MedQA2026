#!/usr/bin/env python3
"""
Paper 4 — per-USMLE-competency accuracy on the full 12,723 base runs, using the reliable v2
labels (results/reasoning_ops/op_labels_v2.jsonl; competency = MK/DX/MGMT/COMM/PROF/SBP/PBL,
κ=0.83 validated). Joins to results/base_runs_full/<model>/temp0.0_run*_results.json by qid.
Per-question correctness = majority across greedy runs. Reports per-competency accuracy + Wilson
95% CIs per model, the natural distribution, and the MK-vs-DX gap (the reliable analog of the
forward/backward contrast). GPU-free.

Run:  python3 papers/paper4/analysis/compute_competency_accuracy.py
Writes: papers/paper4/tables/competency_accuracy_v2.csv
"""
import os, json, glob, math
from collections import defaultdict, Counter
from statistics import mean

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
LABELS = os.path.join(REPO, "results/reasoning_ops/op_labels_v2.jsonl")
FULL = os.path.join(REPO, "results/base_runs_full")
OUT = os.path.join(REPO, "papers/paper4/tables"); os.makedirs(OUT, exist_ok=True)
MODELS = ["olmo3_7b", "olmo3_32b", "qwen25_7b", "qwen25_14b", "qwen25_32b"]
NAME = {"olmo3_7b": "OLMo-3 7B", "olmo3_32b": "OLMo-3 32B", "qwen25_7b": "Qwen2.5 7B",
        "qwen25_14b": "Qwen2.5 14B", "qwen25_32b": "Qwen2.5 32B"}
ORDER = ["MK", "DX", "MGMT", "COMM", "PROF", "SBP", "PBL"]


def wilson(k, n, z=1.96):
    if n == 0: return (None, None)
    p = k/n; d = 1+z*z/n; c = (p+z*z/(2*n))/d; h = (z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)))/d
    return (round(100*(c-h), 1), round(100*(c+h), 1))


def load(m):
    per = defaultdict(list)
    for f in glob.glob(os.path.join(FULL, m, "temp0.0_run*_results.json")):
        for r in json.load(open(f)):
            ic = r["is_correct"]; ic = ic if isinstance(ic, bool) else str(ic).lower() == "true"
            per[int(r["question_id"])].append(ic)
    return {q: (1 if sum(v)*2 >= len(v) else 0) for q, v in per.items()}


def main():
    if not os.path.exists(LABELS):
        print("No v2 labels at", LABELS); return
    lab = {}
    for l in open(LABELS):
        o = json.loads(l)
        if o.get("competency"): lab[int(o["qid"])] = o["competency"]
    dist = Counter(lab.values())
    print(f"v2 labels: {len(lab)}   distribution: {dict(dist.most_common())}")

    rows = []
    print(f"\n{'model':12}" + "".join(f"{c:>8}" for c in ORDER) + "   MK-DX")
    for m in MODELS:
        runs = load(m)
        if not runs: continue
        acc = {}
        for c in ORDER:
            vals = [runs[q] for q in lab if lab[q] == c and q in runs]
            n = len(vals); k = sum(vals)
            a = 100*k/n if n else float('nan'); lo, hi = wilson(k, n)
            acc[c] = a
            if n: rows.append({"model": NAME[m], "competency": c, "n": n, "acc": round(a, 1), "ci_lo": lo, "ci_hi": hi})
        line = f"{NAME[m]:12}" + "".join((f"{acc[c]:>8.1f}" if not math.isnan(acc[c]) else f"{'-':>8}") for c in ORDER)
        line += f"   {acc['MK']-acc['DX']:+.1f}"
        print(line)
    import csv
    with open(os.path.join(OUT, "competency_accuracy_v2.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["model", "competency", "n", "acc", "ci_lo", "ci_hi"]); w.writeheader()
        for r in rows: w.writerow(r)
    print("\nn per competency:", {c: dist.get(c, 0) for c in ORDER})
    print("wrote papers/paper4/tables/competency_accuracy_v2.csv")


if __name__ == "__main__":
    main()
