#!/usr/bin/env python3
"""
Paper 3 — base-data seed analysis (the agentic system is not yet built).

Quantifies, from existing base-run data, the *headroom* an agentic / adaptive
neuro-symbolic selector could in principle capture, and whether category-specific
routing is motivated:

  1. Oracle 'any-of-5-correct' upper bound vs best single model vs majority-of-5,
     overall and per category. The gap = headroom for an ideal selector/agent.
  2. Per-category best model: does the winning model differ by category?
     (motivates category-specific reasoning / routing, BRIEF RQ2/RQ7)
  3. Answer-agreement distribution across the 5 models as a belief-uncertainty
     proxy: relationship between inter-model agreement and correctness
     (motivates belief-state tracking and stopping, BRIEF RQ4).

All from results/base_runs (t=0.0, run 1, deterministic). Reproducible.
"""
import os
import json, os
from collections import Counter
from statistics import mean

import numpy as np
import pandas as pd

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # repo root from papers/<paper>/analysis/
REPO = _REPO
RES = os.path.join(REPO, "results", "base_runs")
OUT = os.path.join(REPO, "papers", "paper3", "tables")
FIG = os.path.join(REPO, "papers", "paper3", "figures")
os.makedirs(OUT, exist_ok=True); os.makedirs(FIG, exist_ok=True)

MODELS = ["olmo3_7b", "olmo3_32b", "qwen25_7b", "qwen25_14b", "qwen25_32b"]
NAME = {"olmo3_7b": "OLMo-3 7B", "olmo3_32b": "OLMo-3 32B", "qwen25_7b": "Qwen2.5 7B",
        "qwen25_14b": "Qwen2.5 14B", "qwen25_32b": "Qwen2.5 32B"}
CATS = ["Clinical Findings", "Diagnosis", "Mechanism/Pathophysiology",
        "Next Step/Workup", "Treatment/Management"]


def load(m):
    d = json.load(open(os.path.join(RES, m, "temp0.0_run1_results.json")))
    d.sort(key=lambda x: x["question_id"]); return d

base = {m: load(m) for m in MODELS}
N = 1030
idx_by_cat = {c: [i for i in range(N) if base["olmo3_7b"][i]["category"] == c] for c in CATS}


def acc(m, idxs): return 100 * sum(base[m][i]["is_correct"] for i in idxs) / len(idxs)

# ---------------------------------------------------------------------------
# 1. Oracle upper bound vs best single vs majority-of-5
# ---------------------------------------------------------------------------
def oracle_any(idxs):
    return 100 * sum(1 for i in idxs if any(base[m][i]["is_correct"] for m in MODELS)) / len(idxs)

def majority5(idxs):
    c = 0
    for i in idxs:
        preds = [base[m][i]["predicted"] for m in MODELS]
        gold = base[MODELS[0]][i]["correct"]
        if Counter(preds).most_common(1)[0][0] == gold:
            c += 1
    return 100 * c / len(idxs)

rows = []
for scope, idxs in [("Overall", list(range(N)))] + [(c, idx_by_cat[c]) for c in CATS]:
    best_m = max(MODELS, key=lambda m: acc(m, idxs))
    rows.append({
        "scope": scope, "n": len(idxs),
        "best_single_model": NAME[best_m],
        "best_single_acc": round(acc(best_m, idxs), 1),
        "majority_of_5": round(majority5(idxs), 1),
        "oracle_any_of_5": round(oracle_any(idxs), 1),
        "headroom_oracle_minus_best": round(oracle_any(idxs) - acc(best_m, idxs), 1),
    })
df_or = pd.DataFrame(rows)
df_or.to_csv(os.path.join(OUT, "seed_oracle_headroom.csv"), index=False)

# ---------------------------------------------------------------------------
# 2. Per-category best model (routing motivation)
# ---------------------------------------------------------------------------
rows = []
for c in CATS:
    accs = {NAME[m]: round(acc(m, idx_by_cat[c]), 1) for m in MODELS}
    best = max(accs, key=accs.get)
    rows.append({"category": c, **accs, "best_model": best})
df_rt = pd.DataFrame(rows)
df_rt.to_csv(os.path.join(OUT, "seed_category_best_model.csv"), index=False)

# perfect category-routing accuracy (pick best model per category, applied to that category)
route_correct = sum(
    sum(base[max(MODELS, key=lambda m: acc(m, idx_by_cat[c]))][i]["is_correct"]
        for i in idx_by_cat[c])
    for c in CATS)
route_acc = 100 * route_correct / N
best_overall = max(MODELS, key=lambda m: acc(m, list(range(N))))
best_overall_acc = acc(best_overall, list(range(N)))

# ---------------------------------------------------------------------------
# 3. Inter-model agreement as belief-uncertainty proxy
#    For each question, k = number of models predicting the modal answer (1..5).
#    Relate agreement level to correctness of the modal answer.
# ---------------------------------------------------------------------------
rows = []
for k_target in range(1, 6):
    sel = []
    for i in range(N):
        preds = [base[m][i]["predicted"] for m in MODELS]
        modal, modal_n = Counter(preds).most_common(1)[0]
        if modal_n == k_target:
            gold = base[MODELS[0]][i]["correct"]
            sel.append(1 if modal == gold else 0)
    rows.append({"models_agreeing_on_modal_answer": k_target,
                 "n_questions": len(sel),
                 "modal_answer_accuracy_pct": round(100 * mean(sel), 1) if sel else None})
df_ag = pd.DataFrame(rows)
df_ag.to_csv(os.path.join(OUT, "seed_agreement_vs_correctness.csv"), index=False)

# ---------------------------------------------------------------------------
# Figure: oracle headroom bar (best single vs majority vs oracle) by category
# ---------------------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"font.size": 11, "figure.dpi": 150})
fig, ax = plt.subplots(figsize=(9, 5))
scopes = ["Overall"] + CATS
x = np.arange(len(scopes)); w = 0.26
bs = [df_or[df_or.scope == s].best_single_acc.values[0] for s in scopes]
mj = [df_or[df_or.scope == s].majority_of_5.values[0] for s in scopes]
orc = [df_or[df_or.scope == s].oracle_any_of_5.values[0] for s in scopes]
ax.bar(x - w, bs, w, label="Best single model", color="#7570b3")
ax.bar(x, mj, w, label="Majority of 5", color="#1b9e77")
ax.bar(x + w, orc, w, label="Oracle (any of 5 correct)", color="#d95f02")
ax.axhline(25, ls="--", color="gray", lw=1, label="Random (25%)")
ax.set_xticks(x); ax.set_xticklabels([s.replace("/", "/\n") for s in scopes], fontsize=8.5)
ax.set_ylabel("Accuracy (%)"); ax.set_ylim(0, 100)
ax.set_title("Headroom for agentic selection: best single vs majority vs oracle (t=0.0)")
ax.legend(fontsize=8, ncol=2)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_seed_oracle_headroom.png"))

print("=== Oracle headroom ==="); print(df_or.to_string(index=False))
print("\n=== Per-category best model ==="); print(df_rt.to_string(index=False))
print(f"\nPerfect per-category routing accuracy = {route_acc:.1f}%  "
      f"(best single overall = {NAME[best_overall]} {best_overall_acc:.1f}%)")
print("\n=== Agreement vs correctness ==="); print(df_ag.to_string(index=False))
print("\nWrote seed CSVs + figure.")