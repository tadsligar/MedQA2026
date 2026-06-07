#!/usr/bin/env python3
"""
Paper 1 analysis: compute all benchmark tables from the focused 1,030-question
balanced MedQA result JSONs (results/base_runs).

Each results JSON is a list of per-question records:
  {question_id, category, correct, predicted, is_correct, tokens, latency, response}

Outputs CSVs into papers/paper1/tables/.
All numbers are computed directly from the raw per-question records (no reliance
on precomputed summaries) so the paper's tables are reproducible from source.
"""
import json
import os
from collections import defaultdict, Counter
from statistics import mean, pstdev

import pandas as pd

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # repo root from papers/<paper>/analysis/
REPO = _REPO
RESULTS_DIR = os.path.join(REPO, "results", "base_runs")
OUT = os.path.join(REPO, "papers", "paper1", "tables")
os.makedirs(OUT, exist_ok=True)

# Canonical model display names and ordering (by family then size)
MODELS = {
    "qwen25_7b":  ("Qwen2.5 7B",  "Qwen2.5", 7),
    "qwen25_14b": ("Qwen2.5 14B", "Qwen2.5", 14),
    "qwen25_32b": ("Qwen2.5 32B", "Qwen2.5", 32),
    "olmo3_7b":   ("OLMo-3 7B",   "OLMo-3", 7),
    "olmo3_32b":  ("OLMo-3 32B",  "OLMo-3", 32),
}
MODEL_ORDER = ["olmo3_7b", "olmo3_32b", "qwen25_7b", "qwen25_14b", "qwen25_32b"]
TEMPS = [0.0, 0.3, 0.7]
RUNS = [1, 2, 3]
CATEGORIES = ["Clinical Findings", "Diagnosis", "Mechanism/Pathophysiology",
              "Next Step/Workup", "Treatment/Management"]
RANDOM_BASELINE = 25.0  # focused set is 4-option (A-D)


def load(model, temp, run):
    f = os.path.join(RESULTS_DIR, model, f"temp{temp}_run{run}_results.json")
    with open(f) as fh:
        return json.load(fh)


def acc(records):
    return 100.0 * sum(r["is_correct"] for r in records) / len(records)


# ---------------------------------------------------------------------------
# Load everything into a tidy long-form structure
# data[model][temp][run] = list of records (sorted by question_id)
# ---------------------------------------------------------------------------
data = {}
for m in MODEL_ORDER:
    data[m] = {}
    for t in TEMPS:
        data[m][t] = {}
        for r in RUNS:
            recs = load(m, t, r)
            recs.sort(key=lambda x: x["question_id"])
            data[m][t][r] = recs

# Sanity checks
for m in MODEL_ORDER:
    for t in TEMPS:
        for r in RUNS:
            recs = data[m][t][r]
            assert len(recs) == 1030, f"{m} t{t} r{r}: {len(recs)} != 1030"
            cc = Counter(x["category"] for x in recs)
            for c in CATEGORIES:
                assert cc[c] == 206, f"{m} t{t} r{r} cat {c} = {cc[c]} != 206"
print("Sanity checks passed: 1030 questions, 206/category, all files load.")


# ---------------------------------------------------------------------------
# Table 3: Overall accuracy by model x temperature (per-run + mean + std)
# ---------------------------------------------------------------------------
rows = []
for m in MODEL_ORDER:
    name, fam, size = MODELS[m]
    for t in TEMPS:
        accs = [acc(data[m][t][r]) for r in RUNS]
        rows.append({
            "model": name, "family": fam, "size_b": size, "temp": t,
            "run1": round(accs[0], 3), "run2": round(accs[1], 3),
            "run3": round(accs[2], 3),
            "mean_acc": round(mean(accs), 3),
            "std_acc": round(pstdev(accs), 4),
        })
df_overall = pd.DataFrame(rows)
df_overall.to_csv(os.path.join(OUT, "table3_overall_accuracy.csv"), index=False)

# ---------------------------------------------------------------------------
# Table 4: Per-category accuracy by model (mean over 3 runs) at each temp
# ---------------------------------------------------------------------------
rows = []
for m in MODEL_ORDER:
    name, fam, size = MODELS[m]
    for t in TEMPS:
        row = {"model": name, "temp": t}
        for c in CATEGORIES:
            cat_accs = []
            for r in RUNS:
                recs = [x for x in data[m][t][r] if x["category"] == c]
                cat_accs.append(acc(recs))
            row[c] = round(mean(cat_accs), 2)
        # overall mean for reference
        row["Overall"] = round(mean([acc(data[m][t][r]) for r in RUNS]), 2)
        rows.append(row)
df_cat = pd.DataFrame(rows)
df_cat.to_csv(os.path.join(OUT, "table4_category_accuracy.csv"), index=False)

# ---------------------------------------------------------------------------
# Table 5: Run-to-run variability (std of accuracy across runs) +
#          answer instability (fraction of questions where the 3 runs
#          do NOT all agree on the predicted letter)
# ---------------------------------------------------------------------------
rows = []
for m in MODEL_ORDER:
    name, fam, size = MODELS[m]
    for t in TEMPS:
        accs = [acc(data[m][t][r]) for r in RUNS]
        # instability: per question, do all 3 predictions agree?
        n = len(data[m][t][1])
        unstable = 0
        for i in range(n):
            preds = {data[m][t][r][i]["predicted"] for r in RUNS}
            if len(preds) > 1:
                unstable += 1
        rows.append({
            "model": name, "temp": t,
            "mean_acc": round(mean(accs), 3),
            "std_acc": round(pstdev(accs), 4),
            "acc_range": round(max(accs) - min(accs), 3),
            "answer_instability_pct": round(100.0 * unstable / n, 2),
        })
df_var = pd.DataFrame(rows)
df_var.to_csv(os.path.join(OUT, "table5_variability.csv"), index=False)

# ---------------------------------------------------------------------------
# Table 6: Majority-vote accuracy (per question, majority of 3 runs;
#          ties broken by run1) vs single-run mean accuracy
# ---------------------------------------------------------------------------
rows = []
for m in MODEL_ORDER:
    name, fam, size = MODELS[m]
    for t in TEMPS:
        n = len(data[m][t][1])
        correct_mv = 0
        for i in range(n):
            preds = [data[m][t][r][i]["predicted"] for r in RUNS]
            gold = data[m][t][1][i]["correct"]
            cnt = Counter(preds)
            top = cnt.most_common()
            # tie-break: prefer run1's answer if tied
            best_count = top[0][1]
            tied = [p for p, c in top if c == best_count]
            mv = preds[0] if preds[0] in tied else tied[0]
            if mv == gold:
                correct_mv += 1
        mv_acc = 100.0 * correct_mv / n
        single_mean = mean([acc(data[m][t][r]) for r in RUNS])
        rows.append({
            "model": name, "temp": t,
            "single_run_mean_acc": round(single_mean, 3),
            "majority_vote_acc": round(mv_acc, 3),
            "mv_gain_pp": round(mv_acc - single_mean, 3),
        })
df_mv = pd.DataFrame(rows)
df_mv.to_csv(os.path.join(OUT, "table6_majority_vote.csv"), index=False)

# ---------------------------------------------------------------------------
# Table 7: Temperature sensitivity (t=0.0 -> t=0.7 drop), overall + per category
# ---------------------------------------------------------------------------
rows = []
for m in MODEL_ORDER:
    name, fam, size = MODELS[m]
    def macc(t, cat=None):
        vals = []
        for r in RUNS:
            recs = data[m][t][r]
            if cat:
                recs = [x for x in recs if x["category"] == cat]
            vals.append(acc(recs))
        return mean(vals)
    row = {"model": name,
           "acc_t0.0": round(macc(0.0), 2),
           "acc_t0.7": round(macc(0.7), 2),
           "overall_drop_pp": round(macc(0.0) - macc(0.7), 2)}
    for c in CATEGORIES:
        row[f"drop_{c}"] = round(macc(0.0, c) - macc(0.7, c), 2)
    rows.append(row)
df_temp = pd.DataFrame(rows)
df_temp.to_csv(os.path.join(OUT, "table7_temp_sensitivity.csv"), index=False)

# ---------------------------------------------------------------------------
# Table 8: Scale effects within family (t=0.0 mean accuracy deltas)
# ---------------------------------------------------------------------------
rows = []
for m in MODEL_ORDER:
    name, fam, size = MODELS[m]
    a = mean([acc(data[m][0.0][r]) for r in RUNS])
    rows.append({"family": fam, "size_b": size, "model": name,
                 "acc_t0.0": round(a, 3)})
df_scale = pd.DataFrame(rows).sort_values(["family", "size_b"])
df_scale.to_csv(os.path.join(OUT, "table8_scale.csv"), index=False)

# ---------------------------------------------------------------------------
# Table 9: Error distribution by category (count + share of total errors)
#          at t=0.0, run1 (deterministic), per model
# ---------------------------------------------------------------------------
rows = []
for m in MODEL_ORDER:
    name, fam, size = MODELS[m]
    recs = data[m][0.0][1]
    errs = [x for x in recs if not x["is_correct"]]
    total_err = len(errs)
    cc = Counter(x["category"] for x in errs)
    for c in CATEGORIES:
        rows.append({
            "model": name, "category": c,
            "errors": cc[c],
            "total_errors": total_err,
            "share_of_errors_pct": round(100.0 * cc[c] / total_err, 2) if total_err else 0.0,
            "category_error_rate_pct": round(100.0 * cc[c] / 206, 2),
        })
df_err = pd.DataFrame(rows)
df_err.to_csv(os.path.join(OUT, "table9_error_distribution.csv"), index=False)

# ---------------------------------------------------------------------------
# Question-level difficulty: consistently easy / hard / unstable
# Aggregate across all models at t=0.0 (deterministic), run1.
# ---------------------------------------------------------------------------
n = 1030
q_correct = defaultdict(int)   # how many models got it right (t=0.0 r1)
q_cat = {}
for m in MODEL_ORDER:
    for x in data[m][0.0][1]:
        q_correct[x["question_id"]] += int(x["is_correct"])
        q_cat[x["question_id"]] = x["category"]
qrows = [{"question_id": qid, "category": q_cat[qid],
          "models_correct": q_correct[qid]} for qid in sorted(q_correct)]
df_q = pd.DataFrame(qrows)
df_q.to_csv(os.path.join(OUT, "question_difficulty.csv"), index=False)

print("\nWrote tables to", OUT)
for f in sorted(os.listdir(OUT)):
    print("  ", f)

# Print key tables to stdout for inspection
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)
print("\n=== Table 3: overall accuracy ===")
print(df_overall.to_string(index=False))
print("\n=== Table 5: variability / answer instability ===")
print(df_var.to_string(index=False))
print("\n=== Table 7: temperature sensitivity ===")
print(df_temp.to_string(index=False))
