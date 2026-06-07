#!/usr/bin/env python3
"""
Paper 1 — Section B cheap additions (re-analysis of existing files only).

  1. Paired bootstrap 95% CIs for model-pair accuracy differences (t=0.0)
     and t=0.0 -> t=0.7 within-model drops, + Holm-adjusted McNemar p-values.
  2. Token/length analysis: generation length of right vs wrong answers, and
     truncation rate at the 800-token cap.
  3. Qualitative error samples: hard-core (all-5-wrong) questions per category.
  4. Full-set (12,723, 5-option) vs focused (1,030, 4-option) reconciliation.

Outputs CSVs/MD to papers/paper1/tables/ and samples to papers/paper1/error_samples.md
"""
import json
import os
import random
from collections import Counter, defaultdict
from statistics import mean

import numpy as np
import pandas as pd
from scipy.stats import binomtest

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # repo root from papers/<paper>/analysis/
REPO = _REPO
RESULTS_DIR = os.path.join(REPO, "results", "base_runs")
OUT = os.path.join(REPO, "papers", "paper1", "tables")
PAPER = os.path.join(REPO, "papers", "paper1")
os.makedirs(OUT, exist_ok=True)
random.seed(42); np.random.seed(42)

MODELS = {"qwen25_7b": "Qwen2.5 7B", "qwen25_14b": "Qwen2.5 14B",
          "qwen25_32b": "Qwen2.5 32B", "olmo3_7b": "OLMo-3 7B", "olmo3_32b": "OLMo-3 32B"}
ORDER = ["olmo3_7b", "olmo3_32b", "qwen25_7b", "qwen25_14b", "qwen25_32b"]
TEMPS = [0.0, 0.3, 0.7]; RUNS = [1, 2, 3]
CATEGORIES = ["Clinical Findings", "Diagnosis", "Mechanism/Pathophysiology",
              "Next Step/Workup", "Treatment/Management"]


def load(m, t, r):
    d = json.load(open(os.path.join(RESULTS_DIR, m, f"temp{t}_run{r}_results.json")))
    d.sort(key=lambda x: x["question_id"])
    return d

data = {m: {t: {r: load(m, t, r) for r in RUNS} for t in TEMPS} for m in ORDER}
N = 1030

# ---------------------------------------------------------------------------
# 1a. Paired bootstrap CIs for accuracy differences (t=0.0, run1)
# ---------------------------------------------------------------------------
def correct_vec(m, t, r):
    return np.array([1 if x["is_correct"] else 0 for x in data[m][t][r]])

def boot_diff_ci(vec_a, vec_b, B=10000):
    diff = vec_a - vec_b
    idx = np.random.randint(0, len(diff), size=(B, len(diff)))
    means = diff[idx].mean(axis=1) * 100
    return float(diff.mean() * 100), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))

pairs = [("qwen25_7b", "olmo3_7b"), ("qwen25_32b", "olmo3_32b"),
         ("qwen25_14b", "qwen25_7b"), ("qwen25_32b", "qwen25_14b"),
         ("olmo3_32b", "olmo3_7b"), ("qwen25_7b", "olmo3_32b")]
rows = []
# Holm on McNemar p-values for the same family
def mcnemar_p(m1, m2):
    a = correct_vec(m1, 0.0, 1); b = correct_vec(m2, 0.0, 1)
    b10 = int(((a == 1) & (b == 0)).sum()); b01 = int(((a == 0) & (b == 1)).sum())
    nd = b10 + b01
    return binomtest(min(b10, b01), nd, 0.5).pvalue if nd else 1.0

raw = [(p, mcnemar_p(*p)) for p in pairs]
# Holm-Bonferroni
order_idx = sorted(range(len(raw)), key=lambda i: raw[i][1])
mlen = len(raw); holm = [None] * mlen
prev = 0.0
for rank, i in enumerate(order_idx):
    adj = min(1.0, (mlen - rank) * raw[i][1])
    adj = max(adj, prev); prev = adj
    holm[i] = adj

for i, (m1, m2) in enumerate(pairs):
    d, lo, hi = boot_diff_ci(correct_vec(m1, 0.0, 1), correct_vec(m2, 0.0, 1))
    rows.append({
        "comparison": f"{MODELS[m1]} − {MODELS[m2]}",
        "acc_diff_pp": round(d, 2), "boot_ci_lo": round(lo, 2), "boot_ci_hi": round(hi, 2),
        "mcnemar_p": f"{raw[i][1]:.2e}", "holm_p": f"{holm[i]:.2e}",
        "sig_holm_0.05": holm[i] < 0.05,
    })
df_pair = pd.DataFrame(rows)
df_pair.to_csv(os.path.join(OUT, "sectionB_pair_effect_sizes.csv"), index=False)

# 1b. Within-model t=0.0 -> t=0.7 drop with bootstrap CI (run1 vs run1)
rows = []
for m in ORDER:
    d, lo, hi = boot_diff_ci(correct_vec(m, 0.0, 1), correct_vec(m, 0.7, 1))
    rows.append({"model": MODELS[m], "drop_pp_t0_minus_t7": round(d, 2),
                 "boot_ci_lo": round(lo, 2), "boot_ci_hi": round(hi, 2)})
df_drop = pd.DataFrame(rows)
df_drop.to_csv(os.path.join(OUT, "sectionB_temp_drop_ci.csv"), index=False)

# ---------------------------------------------------------------------------
# 2. Token/length analysis (run1 each temp): right vs wrong; truncation at cap
# ---------------------------------------------------------------------------
caps = Counter(x["tokens"] for m in ORDER for x in data[m][0.0][1])
TOKEN_CAP = max(caps)  # observed max -> treat as the generation cap
rows = []
for m in ORDER:
    for t in TEMPS:
        recs = data[m][t][1]
        right = [x["tokens"] for x in recs if x["is_correct"]]
        wrong = [x["tokens"] for x in recs if not x["is_correct"]]
        at_cap = sum(1 for x in recs if x["tokens"] >= TOKEN_CAP)
        rows.append({
            "model": MODELS[m], "temp": t,
            "mean_tokens_right": round(mean(right), 1) if right else None,
            "mean_tokens_wrong": round(mean(wrong), 1) if wrong else None,
            "pct_at_token_cap": round(100 * at_cap / len(recs), 1),
        })
df_tok = pd.DataFrame(rows)
df_tok.to_csv(os.path.join(OUT, "sectionB_token_analysis.csv"), index=False)

# ---------------------------------------------------------------------------
# 3. Qualitative error samples: hard-core (all 5 models wrong at t=0.0)
# ---------------------------------------------------------------------------
ds = json.load(open(os.path.join(REPO, "data/datasets/medqa_focused_1030.json")))
hardcore_by_cat = defaultdict(list)
for i in range(N):
    nwrong = sum(0 if data[m][0.0][1][i]["is_correct"] else 1 for m in ORDER)
    if nwrong == 5:
        cat = data["olmo3_7b"][0.0][1][i]["category"]
        hardcore_by_cat[cat].append(i)

lines = ["# Paper 1 — Qualitative Error Samples (hard-core: all 5 models wrong, t=0.0)\n",
         "Each item below was answered **incorrectly by all five base models** at greedy "
         "decoding — candidate cases for the Error Analysis section. `question_id` indexes "
         "`data/datasets/medqa_focused_1030.json`.\n"]
for c in CATEGORIES:
    lines.append(f"\n## {c}  (hard-core count: {len(hardcore_by_cat[c])})\n")
    for qid in hardcore_by_cat[c][:3]:
        q = ds[qid]
        gold = q["answer_idx"]
        preds = {MODELS[m]: data[m][0.0][1][qid]["predicted"] for m in ORDER}
        opts = "; ".join(f"{k}) {v}" for k, v in q["options"].items())
        lines.append(f"**Q{qid}.** {q['question']}\n")
        lines.append(f"- Options: {opts}")
        lines.append(f"- Gold: **{gold}) {q['options'][gold]}**")
        lines.append(f"- Model predictions: " +
                     ", ".join(f"{k.split()[0]}…={v}" for k, v in preds.items()))
        lines.append("")
with open(os.path.join(PAPER, "error_samples.md"), "w") as fh:
    fh.write("\n".join(lines))

# ---------------------------------------------------------------------------
# 4. Full-set vs focused-set reconciliation
#    Full-set numbers from results/base_runs_full/RESULTS_SUMMARY.md (5-option).
# ---------------------------------------------------------------------------
full = {  # mean acc at t=0.0 (5-option set), from RESULTS_SUMMARY.md
    "OLMo-3 7B": 39.86, "OLMo-3 32B": 52.12, "Qwen2.5 7B": 53.70,
    "Qwen2.5 14B": 60.88, "Qwen2.5 32B": 67.01,
}
focused = {MODELS[m]: round(mean([100 * np.mean(correct_vec(m, 0.0, r)) for r in RUNS]), 2)
           for m in ORDER}
rows = []
for name in ["OLMo-3 7B", "OLMo-3 32B", "Qwen2.5 7B", "Qwen2.5 14B", "Qwen2.5 32B"]:
    rows.append({"model": name, "full_5opt_acc": full[name],
                 "focused_4opt_acc": focused[name],
                 "delta_pp": round(focused[name] - full[name], 2)})
df_rec = pd.DataFrame(rows)
# scaling steps
def step(d, a, b): return round(d[b] - d[a], 2)
notes = {
    "Qwen 7B→14B (full)": step(full, "Qwen2.5 7B", "Qwen2.5 14B"),
    "Qwen 7B→14B (focused)": step(focused, "Qwen2.5 7B", "Qwen2.5 14B"),
    "Qwen 14B→32B (full)": step(full, "Qwen2.5 14B", "Qwen2.5 32B"),
    "Qwen 14B→32B (focused)": step(focused, "Qwen2.5 14B", "Qwen2.5 32B"),
}
df_rec.to_csv(os.path.join(OUT, "sectionB_fullset_reconciliation.csv"), index=False)

# ---------------------------------------------------------------------------
print("=== Pair effect sizes (bootstrap + Holm), t=0.0 ===")
print(df_pair.to_string(index=False))
print("\n=== Within-model temp drop (bootstrap CI) ===")
print(df_drop.to_string(index=False))
print("\n=== Token analysis (run1) ===")
print(df_tok.to_string(index=False))
print(f"\n(observed token cap = {TOKEN_CAP})")
print("\n=== Full vs focused reconciliation ===")
print(df_rec.to_string(index=False))
print("Scaling steps:", notes)
print("\nHard-core counts per category:",
      {c: len(hardcore_by_cat[c]) for c in CATEGORIES})
print("Wrote Section B CSVs to", OUT, "and error_samples.md to", PAPER)
