#!/usr/bin/env python3
"""
Paper 1 EXP2 — base vs instruction-tuned comparison.

Pairs results/base_runs/<base> with results/instruct_runs/<instruct> on the focused 1,030-set
and computes, per model:
  - overall + per-category accuracy (base vs instruct), with paired McNemar at t=0.0
  - temperature degradation (t=0.0 - t=0.7) base vs instruct
  - answer instability at t=0.7 base vs instruct
  - generation-length / token contrast (base models hit the 800-token cap ~75% of the time;
    instruct models should stop cleanly)
GPU-free; run after the instruct SLURM jobs finish. Skips models whose instruct results are
missing so it degrades gracefully.
"""
import os
import json, os
from collections import Counter
from statistics import mean, pstdev

import pandas as pd
from scipy.stats import binomtest

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # repo root from papers/<paper>/analysis/
REPO = _REPO
BASE = os.path.join(REPO, "results", "base_runs")
INST = os.path.join(REPO, "results", "instruct_runs")
OUT = os.path.join(REPO, "papers", "paper1", "tables")
os.makedirs(OUT, exist_ok=True)

# base_key -> instruct_key
PAIRS = [
    ("olmo3_7b", "olmo3_7b_instruct", "OLMo-3 7B"),
    ("olmo3_32b", "olmo3_32b_instruct", "OLMo-3 32B"),
    ("qwen25_7b", "qwen25_7b_instruct", "Qwen2.5 7B"),
    ("qwen25_14b", "qwen25_14b_instruct", "Qwen2.5 14B"),
    ("qwen25_32b", "qwen25_32b_instruct", "Qwen2.5 32B"),
]
CATS = ["Clinical Findings", "Diagnosis", "Mechanism/Pathophysiology",
        "Next Step/Workup", "Treatment/Management"]
TOKEN_CAP = 800


def load(root, key, temp, run):
    f = os.path.join(root, key, f"temp{temp}_run{run}_results.json")
    if not os.path.exists(f):
        return None
    d = json.load(open(f)); d.sort(key=lambda x: x["question_id"]); return d


def acc(recs, cat=None):
    rs = [r for r in recs if (cat is None or r["category"] == cat)]
    return 100 * sum(r["is_correct"] for r in rs) / len(rs)


def instability(key, root, temp=0.7):
    runs = [load(root, key, temp, r) for r in (1, 2, 3)]
    if any(x is None for x in runs):
        return None
    n = len(runs[0])
    u = sum(1 for i in range(n) if len({runs[r][i]["predicted"] for r in range(3)}) > 1)
    return 100 * u / n


def mcnemar(a, b):
    b10 = sum(1 for x, y in zip(a, b) if x["is_correct"] and not y["is_correct"])
    b01 = sum(1 for x, y in zip(a, b) if not x["is_correct"] and y["is_correct"])
    nd = b10 + b01
    p = binomtest(min(b10, b01), nd, 0.5).pvalue if nd else 1.0
    return b10, b01, p


def main():
    overall_rows, cat_rows, temp_rows, tok_rows = [], [], [], []
    found = False
    for bkey, ikey, name in PAIRS:
        b0 = load(BASE, bkey, 0.0, 1); i0 = load(INST, ikey, 0.0, 1)
        if b0 is None or i0 is None:
            print(f"skip {name}: missing {'base' if b0 is None else 'instruct'} t=0.0 run1")
            continue
        found = True
        b10, b01, p = mcnemar(b0, i0)
        overall_rows.append({
            "model": name, "base_acc": round(acc(b0), 2), "instruct_acc": round(acc(i0), 2),
            "delta_pp": round(acc(i0) - acc(b0), 2),
            "instruct_right_base_wrong": b01, "base_right_instruct_wrong": b10,
            "mcnemar_p": f"{p:.2e}", "sig_0.05": p < 0.05,
        })
        for c in CATS:
            cat_rows.append({"model": name, "category": c,
                             "base_acc": round(acc(b0, c), 2), "instruct_acc": round(acc(i0, c), 2),
                             "delta_pp": round(acc(i0, c) - acc(b0, c), 2)})
        # temperature degradation (run1)
        b7 = load(BASE, bkey, 0.7, 1); i7 = load(INST, ikey, 0.7, 1)
        if b7 and i7:
            temp_rows.append({"model": name,
                              "base_drop_t0_t7": round(acc(b0) - acc(b7), 2),
                              "instruct_drop_t0_t7": round(acc(i0) - acc(i7), 2)})
        # instability
        bi = instability(bkey, BASE); ii = instability(ikey, INST)
        if bi is not None and ii is not None:
            temp_rows[-1] if temp_rows else None
        # token / cap contrast (t=0.0 run1)
        b_cap = 100 * sum(1 for r in b0 if r.get("tokens", 0) >= TOKEN_CAP) / len(b0)
        i_cap = 100 * sum(1 for r in i0 if r.get("tokens", 0) >= TOKEN_CAP) / len(i0)
        tok_rows.append({"model": name,
                         "base_mean_tokens": round(mean(r.get("tokens", 0) for r in b0), 1),
                         "instruct_mean_tokens": round(mean(r.get("tokens", 0) for r in i0), 1),
                         "base_pct_at_cap": round(b_cap, 1),
                         "instruct_pct_at_cap": round(i_cap, 1),
                         "base_instability_t07": instability(bkey, BASE),
                         "instruct_instability_t07": instability(ikey, INST)})

    if not found:
        print("No instruct results found under", INST)
        print("Run slurm/instruct/*.sbatch first, then re-run this script.")
        return

    pd.DataFrame(overall_rows).to_csv(os.path.join(OUT, "exp2_base_vs_instruct_overall.csv"), index=False)
    pd.DataFrame(cat_rows).to_csv(os.path.join(OUT, "exp2_base_vs_instruct_category.csv"), index=False)
    if temp_rows:
        pd.DataFrame(temp_rows).to_csv(os.path.join(OUT, "exp2_temp_degradation.csv"), index=False)
    pd.DataFrame(tok_rows).to_csv(os.path.join(OUT, "exp2_token_contrast.csv"), index=False)

    print("=== Base vs Instruct (t=0.0) ===")
    print(pd.DataFrame(overall_rows).to_string(index=False))
    if tok_rows:
        print("\n=== Token / stability contrast ===")
        print(pd.DataFrame(tok_rows).to_string(index=False))
    print("\nWrote exp2_*.csv to", OUT)


if __name__ == "__main__":
    main()