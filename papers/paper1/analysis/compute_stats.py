#!/usr/bin/env python3
"""
Paper 1 — statistical rigor + behavioral analyses on the focused 1,030 set.

Adds, beyond compute_tables.py:
  - Wilson 95% CIs for overall (n=1030) and per-category (n=206) accuracy
  - Exact McNemar tests for key model pairs (t=0.0, run1)
  - Chi-square test for category x temperature interaction (per model)
  - Letter/positional bias vs gold distribution (chi-square)
  - Stability-as-confidence: accuracy of stable vs unstable questions at t=0.7
  - Temperature "rescue": questions wrong at t=0.0 but majority-correct at t=0.7
  - Cross-model error overlap and the all-models-wrong hard-core set
Outputs CSVs to papers/paper1/tables/ and prints a readable report.
"""
import json
import os
import math
from collections import Counter, defaultdict
from statistics import mean

import pandas as pd
from scipy.stats import binomtest, chi2_contingency

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # repo root from papers/<paper>/analysis/
REPO = _REPO
RESULTS_DIR = os.path.join(REPO, "results", "base_runs")
OUT = os.path.join(REPO, "papers", "paper1", "tables")
os.makedirs(OUT, exist_ok=True)

MODELS = {
    "qwen25_7b": "Qwen2.5 7B", "qwen25_14b": "Qwen2.5 14B", "qwen25_32b": "Qwen2.5 32B",
    "olmo3_7b": "OLMo-3 7B", "olmo3_32b": "OLMo-3 32B",
}
MODEL_ORDER = ["olmo3_7b", "olmo3_32b", "qwen25_7b", "qwen25_14b", "qwen25_32b"]
TEMPS = [0.0, 0.3, 0.7]
RUNS = [1, 2, 3]
CATEGORIES = ["Clinical Findings", "Diagnosis", "Mechanism/Pathophysiology",
              "Next Step/Workup", "Treatment/Management"]


def load(model, temp, run):
    with open(os.path.join(RESULTS_DIR, model, f"temp{temp}_run{run}_results.json")) as fh:
        d = json.load(fh)
    d.sort(key=lambda x: x["question_id"])
    return d


data = {m: {t: {r: load(m, t, r) for r in RUNS} for t in TEMPS} for m in MODEL_ORDER}


def wilson(k, n, z=1.96):
    """Wilson score 95% CI, returns (lo, hi) in percent."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (100 * (center - half), 100 * (center + half))


# ---------------------------------------------------------------------------
# 1) Wilson CIs (overall + per category) at t=0.0 run1 (deterministic)
# ---------------------------------------------------------------------------
rows = []
for m in MODEL_ORDER:
    recs = data[m][0.0][1]
    k = sum(x["is_correct"] for x in recs); n = len(recs)
    lo, hi = wilson(k, n)
    row = {"model": MODELS[m], "scope": "Overall", "n": n,
           "acc": round(100 * k / n, 2), "ci_lo": round(lo, 2), "ci_hi": round(hi, 2)}
    rows.append(row)
    for c in CATEGORIES:
        cr = [x for x in recs if x["category"] == c]
        k = sum(x["is_correct"] for x in cr); n = len(cr)
        lo, hi = wilson(k, n)
        rows.append({"model": MODELS[m], "scope": c, "n": n,
                     "acc": round(100 * k / n, 2), "ci_lo": round(lo, 2), "ci_hi": round(hi, 2)})
df_ci = pd.DataFrame(rows)
df_ci.to_csv(os.path.join(OUT, "stats_wilson_ci.csv"), index=False)

# ---------------------------------------------------------------------------
# 2) Exact McNemar tests for adjacent / cross-family model pairs (t=0.0 run1)
#    Uses exact binomial on discordant pairs.
# ---------------------------------------------------------------------------
def mcnemar(m1, m2):
    a = data[m1][0.0][1]; b = data[m2][0.0][1]
    b01 = b10 = 0  # b01: m1 wrong, m2 right ; b10: m1 right, m2 wrong
    for x, y in zip(a, b):
        if x["is_correct"] and not y["is_correct"]:
            b10 += 1
        elif (not x["is_correct"]) and y["is_correct"]:
            b01 += 1
    nd = b01 + b10
    p = binomtest(min(b01, b10), nd, 0.5).pvalue if nd else 1.0
    return b10, b01, nd, p

pairs = [("olmo3_7b", "qwen25_7b"), ("olmo3_32b", "qwen25_32b"),
         ("qwen25_7b", "qwen25_14b"), ("qwen25_14b", "qwen25_32b"),
         ("olmo3_7b", "olmo3_32b"), ("qwen25_7b", "olmo3_32b")]
rows = []
for m1, m2 in pairs:
    b10, b01, nd, p = mcnemar(m1, m2)
    rows.append({
        "model_A": MODELS[m1], "model_B": MODELS[m2],
        "A_right_B_wrong": b10, "B_right_A_wrong": b01,
        "discordant": nd, "p_value": f"{p:.2e}",
        "significant_0.05": p < 0.05,
    })
df_mc = pd.DataFrame(rows)
df_mc.to_csv(os.path.join(OUT, "stats_mcnemar.csv"), index=False)

# ---------------------------------------------------------------------------
# 3) Category x temperature interaction (chi-square per model)
#    Contingency: rows = categories, cols = [correct, wrong] pooled over 3 runs,
#    tested separately at each temp is not interaction; instead build
#    category x temp table of correct-counts and test independence.
# ---------------------------------------------------------------------------
rows = []
for m in MODEL_ORDER:
    # table[cat][temp] = (#correct, #total) pooled over runs
    table = []
    for c in CATEGORIES:
        row = []
        for t in TEMPS:
            corr = sum(x["is_correct"] for r in RUNS for x in data[m][t][r] if x["category"] == c)
            tot = sum(1 for r in RUNS for x in data[m][t][r] if x["category"] == c)
            row.append(corr)  # correct counts; totals equal across cells (206*3)
        table.append(row)
    chi2, p, dof, _ = chi2_contingency(table)
    rows.append({"model": MODELS[m], "chi2": round(chi2, 2), "dof": dof,
                 "p_value": f"{p:.2e}", "interaction_sig_0.05": p < 0.05})
df_int = pd.DataFrame(rows)
df_int.to_csv(os.path.join(OUT, "stats_cat_temp_interaction.csv"), index=False)

# ---------------------------------------------------------------------------
# 4) Letter/positional bias: predicted letter dist vs gold dist (t=0.0 run1)
# ---------------------------------------------------------------------------
rows = []
gold = Counter(x["correct"] for x in data["qwen25_7b"][0.0][1])
for m in MODEL_ORDER:
    pred = Counter(x["predicted"] for x in data[m][0.0][1])
    obs = [pred[l] for l in "ABCD"]
    exp = [gold[l] for l in "ABCD"]
    chi2, p, dof, _ = chi2_contingency([obs, exp])
    row = {"model": MODELS[m]}
    for l in "ABCD":
        row[f"pred_{l}"] = pred[l]
    row["chi2_vs_gold"] = round(chi2, 2)
    row["p_value"] = f"{p:.2e}"
    row["bias_sig_0.05"] = p < 0.05
    rows.append(row)
rows.append({"model": "GOLD", **{f"pred_{l}": gold[l] for l in "ABCD"},
             "chi2_vs_gold": 0.0, "p_value": "1.0", "bias_sig_0.05": False})
df_bias = pd.DataFrame(rows)
df_bias.to_csv(os.path.join(OUT, "stats_letter_bias.csv"), index=False)

# ---------------------------------------------------------------------------
# 5) Stability-as-confidence (calibration proxy w/o logits) at t=0.7
#    For each question: stable = all 3 runs agree. Compare accuracy (run1)
#    of stable vs unstable questions.
# ---------------------------------------------------------------------------
rows = []
for m in MODEL_ORDER:
    n = 1030
    stable_correct = stable_n = unstable_correct = unstable_n = 0
    for i in range(n):
        preds = [data[m][0.7][r][i]["predicted"] for r in RUNS]
        is_corr = data[m][0.7][1][i]["is_correct"]
        if len(set(preds)) == 1:
            stable_n += 1; stable_correct += int(is_corr)
        else:
            unstable_n += 1; unstable_correct += int(is_corr)
    rows.append({
        "model": MODELS[m],
        "stable_n": stable_n,
        "stable_acc": round(100 * stable_correct / stable_n, 2) if stable_n else None,
        "unstable_n": unstable_n,
        "unstable_acc": round(100 * unstable_correct / unstable_n, 2) if unstable_n else None,
        "acc_gap_pp": round((100 * stable_correct / stable_n) - (100 * unstable_correct / unstable_n), 2)
                       if stable_n and unstable_n else None,
    })
df_conf = pd.DataFrame(rows)
df_conf.to_csv(os.path.join(OUT, "stats_stability_confidence.csv"), index=False)

# ---------------------------------------------------------------------------
# 6) Temperature rescue: wrong at t=0.0 but majority-correct at t=0.7 (and vice versa)
# ---------------------------------------------------------------------------
def maj_correct(m, t, i):
    preds = [data[m][t][r][i]["predicted"] for r in RUNS]
    gold = data[m][t][1][i]["correct"]
    return Counter(preds).most_common(1)[0][0] == gold

rows = []
for m in MODEL_ORDER:
    rescued = lost = 0
    for i in range(1030):
        g0 = data[m][0.0][1][i]["is_correct"]
        m7 = maj_correct(m, 0.7, i)
        if (not g0) and m7:
            rescued += 1
        if g0 and (not m7):
            lost += 1
    rows.append({"model": MODELS[m], "rescued_by_sampling": rescued,
                 "lost_by_sampling": lost, "net_pp": round(100 * (rescued - lost) / 1030, 2)})
df_resc = pd.DataFrame(rows)
df_resc.to_csv(os.path.join(OUT, "stats_temp_rescue.csv"), index=False)

# ---------------------------------------------------------------------------
# 7) Cross-model error overlap + hard-core (all 5 models wrong) at t=0.0 run1
# ---------------------------------------------------------------------------
n = 1030
wrong_by_count = Counter()  # how many models got each question wrong
q_cat = {}
for i in range(n):
    qid = data["olmo3_7b"][0.0][1][i]["question_id"]
    q_cat[qid] = data["olmo3_7b"][0.0][1][i]["category"]
    nwrong = sum(0 if data[m][0.0][1][i]["is_correct"] else 1 for m in MODEL_ORDER)
    wrong_by_count[nwrong] += 1
# hard-core breakdown
hardcore_cat = Counter()
allcorrect_cat = Counter()
for i in range(n):
    nwrong = sum(0 if data[m][0.0][1][i]["is_correct"] else 1 for m in MODEL_ORDER)
    cat = data["olmo3_7b"][0.0][1][i]["category"]
    if nwrong == 5:
        hardcore_cat[cat] += 1
    if nwrong == 0:
        allcorrect_cat[cat] += 1
rows = [{"models_wrong": k, "num_questions": wrong_by_count[k]} for k in range(6)]
df_overlap = pd.DataFrame(rows)
df_overlap.to_csv(os.path.join(OUT, "stats_error_overlap.csv"), index=False)
df_hard = pd.DataFrame([
    {"category": c, "all5_wrong": hardcore_cat[c], "all5_correct": allcorrect_cat[c]}
    for c in CATEGORIES
])
df_hard.to_csv(os.path.join(OUT, "stats_hardcore_by_category.csv"), index=False)

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
pd.set_option("display.width", 200); pd.set_option("display.max_columns", 25)
print("=== Wilson 95% CI (overall, t=0.0) ===")
print(df_ci[df_ci.scope == "Overall"].to_string(index=False))
print("\n=== McNemar pairwise (t=0.0) ===")
print(df_mc.to_string(index=False))
print("\n=== Category x temperature interaction ===")
print(df_int.to_string(index=False))
print("\n=== Letter bias vs gold (t=0.0) ===")
print(df_bias.to_string(index=False))
print("\n=== Stability-as-confidence (t=0.7) ===")
print(df_conf.to_string(index=False))
print("\n=== Temperature rescue vs loss (t=0.0 -> t=0.7 majority) ===")
print(df_resc.to_string(index=False))
print("\n=== Error overlap (how many of 5 models wrong, t=0.0) ===")
print(df_overlap.to_string(index=False))
print("\n=== Hard-core (all 5 wrong) by category ===")
print(df_hard.to_string(index=False))
print("\nWrote stats CSVs to", OUT)
