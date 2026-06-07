#!/usr/bin/env python3
"""
Paper 2 — base-data seed analysis (no UMLS / neuro-symbolic results exist yet).

Computes, purely from existing repo artifacts, three things that seed Paper 2's
empirical and motivation sections:

  1. Hard-core target set: questions all 5 base models miss at t=0.0 (greedy),
     by category. These are the items a symbolic verifier / hybrid system most
     needs to help on (Paper 1 §5.8 extended for Paper 2 framing).
  2. Groundable-surface proxy: distribution of pre-extracted clinical phrases
     (`metamap_phrases`) per question and per category, and its relationship to
     base-model difficulty — does more groundable surface area track accuracy?
  3. Concept-mismatch motivation: surface-form variant counts for canonical
     clinical concepts, demonstrating empirically that the same clinical idea
     appears under many surfaces (the failure mode that breaks exact matching).

Outputs CSVs to papers/paper2/tables/ and one motivation figure.
"""
import os
import json, os, re
from collections import Counter, defaultdict
from statistics import mean

import pandas as pd

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # repo root from papers/<paper>/analysis/
REPO = _REPO
RES = os.path.join(REPO, "results", "base_runs")
OUT = os.path.join(REPO, "papers", "paper2", "tables")
FIG = os.path.join(REPO, "papers", "paper2", "figures")
os.makedirs(OUT, exist_ok=True); os.makedirs(FIG, exist_ok=True)

MODELS = ["olmo3_7b", "olmo3_32b", "qwen25_7b", "qwen25_14b", "qwen25_32b"]
CATS = ["Clinical Findings", "Diagnosis", "Mechanism/Pathophysiology",
        "Next Step/Workup", "Treatment/Management"]
ds = json.load(open(os.path.join(REPO, "data/datasets/medqa_focused_1030.json")))


def load(m):  # t=0.0 run1, deterministic
    d = json.load(open(os.path.join(RES, m, "temp0.0_run1_results.json")))
    d.sort(key=lambda x: x["question_id"])
    return d

base = {m: load(m) for m in MODELS}
N = 1030

# ---------------------------------------------------------------------------
# 1. Hard-core (all 5 wrong) and all-correct by category
# ---------------------------------------------------------------------------
rows = []
hardcore_ids = []
for i in range(N):
    nwrong = sum(0 if base[m][i]["is_correct"] else 1 for m in MODELS)
    cat = base["olmo3_7b"][i]["category"]
    if nwrong == 5:
        hardcore_ids.append(i)
hc_cat = Counter(base["olmo3_7b"][i]["category"] for i in hardcore_ids)
ac_cat = Counter(base["olmo3_7b"][i]["category"] for i in range(N)
                 if all(base[m][i]["is_correct"] for m in MODELS))
for c in CATS:
    rows.append({"category": c, "hard_core_all5_wrong": hc_cat[c],
                 "all5_correct": ac_cat[c], "n": 206,
                 "hard_core_rate_pct": round(100*hc_cat[c]/206, 1)})
df_hc = pd.DataFrame(rows)
df_hc.loc["TOTAL"] = ["ALL", sum(hc_cat.values()), sum(ac_cat.values()), 1030,
                      round(100*sum(hc_cat.values())/1030, 1)]
df_hc.to_csv(os.path.join(OUT, "seed_hardcore_targets.csv"), index=False)
with open(os.path.join(OUT, "seed_hardcore_ids.json"), "w") as fh:
    json.dump({"all5_wrong_t0_run1_ids": hardcore_ids}, fh)

# ---------------------------------------------------------------------------
# 2. Groundable-surface proxy: metamap phrase density vs difficulty
# ---------------------------------------------------------------------------
# per-question difficulty = #models correct (0..5) at t=0.0
qdiff = {i: sum(1 if base[m][i]["is_correct"] else 0 for m in MODELS) for i in range(N)}
rows = []
for c in CATS:
    idxs = [i for i in range(N) if ds[i].get("validated_category") == c]
    phrase_counts = [len(ds[i].get("metamap_phrases", [])) for i in idxs]
    # base accuracy for this category (mean over 5 models, fraction correct)
    acc = mean(100 * (sum(1 if base[m][i]["is_correct"] else 0 for m in MODELS) / 5)
               for i in idxs)
    rows.append({"category": c, "n": len(idxs),
                 "mean_phrases": round(mean(phrase_counts), 1),
                 "min_phrases": min(phrase_counts), "max_phrases": max(phrase_counts),
                 "mean_base_acc_5model": round(acc, 1)})
df_ph = pd.DataFrame(rows)
df_ph.to_csv(os.path.join(OUT, "seed_phrase_density_by_category.csv"), index=False)

# correlation: per-question phrase count vs #models-correct
import numpy as np
pc = np.array([len(ds[i].get("metamap_phrases", [])) for i in range(N)])
dc = np.array([qdiff[i] for i in range(N)])
corr = float(np.corrcoef(pc, dc)[0, 1])

# ---------------------------------------------------------------------------
# 3. Concept-mismatch motivation: surface-form variant prevalence
#    For canonical clinical ideas, count questions whose metamap_phrases / stem
#    contain each surface variant. Demonstrates many surfaces -> exact match fails.
# ---------------------------------------------------------------------------
concept_variants = {
    "Chest pain / discomfort": [r"chest pain", r"chest discomfort", r"chest tightness",
                                 r"chest pressure", r"retrosternal", r"substernal"],
    "Dyspnea / shortness of breath": [r"dyspnea", r"shortness of breath", r"\bsob\b",
                                       r"short of breath", r"difficulty breathing",
                                       r"respiratory distress", r"breathless"],
    "Myocardial infarction": [r"myocardial infarction", r"\bmi\b", r"heart attack",
                              r"stemi", r"nstemi", r"acute coronary"],
    "Hypertension": [r"hypertension", r"high blood pressure", r"elevated blood pressure",
                     r"\bhtn\b"],
    "Fever": [r"fever", r"febrile", r"pyrexia", r"elevated temperature"],
}
texts = []
for q in ds:
    blob = (q.get("question", "") + " " + " ".join(q.get("metamap_phrases", []))).lower()
    texts.append(blob)

rows = []
for concept, variants in concept_variants.items():
    variant_hits = {}
    any_hit_ids = set()
    for v in variants:
        ids = {i for i, t in enumerate(texts) if re.search(v, t)}
        variant_hits[v] = len(ids)
        any_hit_ids |= ids
    present = sorted([(v, n) for v, n in variant_hits.items() if n > 0],
                     key=lambda x: -x[1])
    rows.append({
        "concept": concept,
        "n_questions_any_variant": len(any_hit_ids),
        "n_distinct_surface_forms_present": len(present),
        "surface_forms": "; ".join(f"{v}({n})" for v, n in present),
    })
df_cm = pd.DataFrame(rows)
df_cm.to_csv(os.path.join(OUT, "seed_concept_variant_prevalence.csv"), index=False)

# ---------------------------------------------------------------------------
# Figure: phrase density vs base accuracy by category (the "groundable surface
# area does NOT predict ease" motivation)
# ---------------------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"font.size": 11, "figure.dpi": 150})
fig, ax = plt.subplots(figsize=(7.5, 5))
xs = df_ph["mean_phrases"]; ys = df_ph["mean_base_acc_5model"]
ax.scatter(xs, ys, s=80, color="#2c7fb8", zorder=3)
for _, r in df_ph.iterrows():
    ax.annotate(r["category"].replace("/", "/\n"), (r["mean_phrases"], r["mean_base_acc_5model"]),
                fontsize=8, xytext=(5, 4), textcoords="offset points")
ax.set_xlabel("Mean extractable clinical phrases per question (metamap_phrases)")
ax.set_ylabel("Mean base-model accuracy (5 models, t=0.0, %)")
ax.set_title("Groundable surface area vs difficulty by category")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_seed_phrase_vs_acc.png"))

print("=== Hard-core targets by category ===")
print(df_hc.to_string(index=False))
print("\n=== Phrase density vs base accuracy by category ===")
print(df_ph.to_string(index=False))
print(f"\nPer-question corr(phrase count, #models correct) = {corr:.3f}")
print("\n=== Concept-variant prevalence (concept-mismatch motivation) ===")
print(df_cm.to_string(index=False))
print("\nWrote seed CSVs to", OUT, "and figure to", FIG)