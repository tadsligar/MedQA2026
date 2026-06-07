#!/usr/bin/env python3
"""
Paper 2 EXP3 — symbolic-scorer analysis vs the verified LLM-only baseline.

Reads results/ns/symbolic/{overlap,relation,tfidf}_results.json and compares each to:
  - random (25%)
  - the verified LLM-only baseline (best single model Qwen2.5 32B = 73.4% at t=0.0)
Reports overall + per-category accuracy with Wilson CIs and a paired McNemar vs the
Qwen2.5-32B base run (results/base_runs/qwen25_32b/temp0.0_run1_results.json).
GPU-free; self-skips missing inputs.
"""
import os
import json, os, math
from collections import Counter

import pandas as pd
from scipy.stats import binomtest

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # repo root from papers/<paper>/analysis/
REPO = _REPO
SYM = os.path.join(REPO, "results", "ns", "symbolic")
BASE = os.path.join(REPO, "results", "base_runs", "qwen25_32b", "temp0.0_run1_results.json")
OUT = os.path.join(REPO, "papers", "paper2", "tables")
os.makedirs(OUT, exist_ok=True)
CATS = ["Clinical Findings", "Diagnosis", "Mechanism/Pathophysiology",
        "Next Step/Workup", "Treatment/Management"]


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = (z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))) / d
    return (100*(c-h), 100*(c+h))


def load(path):
    if not os.path.exists(path):
        return None
    d = json.load(open(path)); d.sort(key=lambda x: x["question_id"]); return d


def acc(recs, cat=None):
    rs = [r for r in recs if cat is None or r["category"] == cat]
    return 100 * sum(r["is_correct"] for r in rs) / len(rs) if rs else None


def main():
    base = load(BASE)
    variants = {}
    for v in ["overlap", "relation", "tfidf"]:
        d = load(os.path.join(SYM, f"{v}_results.json"))
        if d:
            variants[v] = d
    if not variants:
        print("No symbolic results under", SYM)
        print("Build the index + run scorers first (see slurm/symbolic/README.md).")
        return

    rows, cat_rows = [], []
    for v, recs in variants.items():
        n = len(recs); k = sum(r["is_correct"] for r in recs)
        lo, hi = wilson(k, n)
        row = {"variant": v, "overall_acc": round(100*k/n, 2),
               "ci_lo": round(lo, 2), "ci_hi": round(hi, 2), "vs_random_pp": round(100*k/n - 25, 2)}
        if base and len(base) == n:
            b10 = sum(1 for x, y in zip(recs, base) if x["is_correct"] and not y["is_correct"])
            b01 = sum(1 for x, y in zip(recs, base) if not x["is_correct"] and y["is_correct"])
            nd = b10 + b01
            p = binomtest(min(b10, b01), nd, 0.5).pvalue if nd else 1.0
            row["vs_qwen32b_pp"] = round(100*k/n - acc(base), 2)
            row["mcnemar_p_vs_qwen32b"] = f"{p:.2e}"
        rows.append(row)
        for c in CATS:
            cat_rows.append({"variant": v, "category": c, "acc": round(acc(recs, c), 2)})

    pd.DataFrame(rows).to_csv(os.path.join(OUT, "exp3_symbolic_overall.csv"), index=False)
    pd.DataFrame(cat_rows).to_csv(os.path.join(OUT, "exp3_symbolic_category.csv"), index=False)
    print("=== Symbolic-only accuracy vs baselines ===")
    print(pd.DataFrame(rows).to_string(index=False))
    if base:
        print(f"\n(LLM-only Qwen2.5-32B baseline = {acc(base):.2f}%; random = 25%)")
    print("\nWrote exp3_symbolic_*.csv to", OUT)


if __name__ == "__main__":
    main()