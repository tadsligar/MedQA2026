#!/usr/bin/env python3
"""
Paper 1 (full-set) — per-USMLE-competency accuracy on the full 12,723-question runs.

Joins competency labels (results/category_relabel/competency_labels.jsonl, keyed by qid) with
the existing full-dataset results (results/base_runs_full/<model>/temp*_run*_results.json, keyed
by question_id) and reports:
  - competency natural distribution (7-way) + the 5 reasoning sub-categories
  - per-competency accuracy by model (t=0.0, mean of 3 runs) with Wilson 95% CIs
  - per-reasoning-subcategory accuracy by model
GPU-free; self-skips if labels are absent. No re-runs needed (results already exist).
"""
import os, json, glob, math
from collections import defaultdict, Counter
from statistics import mean
import pandas as pd

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
LABELS = os.path.join(_REPO, "results", "category_relabel", "competency_labels.jsonl")
FULL = os.path.join(_REPO, "results", "base_runs_full")
OUT = os.path.join(_REPO, "papers", "paper1", "tables")
os.makedirs(OUT, exist_ok=True)

MODELS = ["olmo3_7b", "olmo3_32b", "qwen25_7b", "qwen25_14b", "qwen25_32b"]
NAME = {"olmo3_7b": "OLMo-3 7B", "olmo3_32b": "OLMo-3 32B", "qwen25_7b": "Qwen2.5 7B",
        "qwen25_14b": "Qwen2.5 14B", "qwen25_32b": "Qwen2.5 32B"}
COMP_NAME = {"MK": "Medical Knowledge", "PC_DX": "Patient Care: Diagnosis",
             "PC_MGMT": "Patient Care: Management", "COMM": "Communication",
             "PROF": "Professionalism/Ethical", "SBP": "Systems-based Practice",
             "PBL": "Practice-based Learning"}


def wilson(k, n, z=1.96):
    if n == 0: return (None, None)
    p = k / n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = (z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))) / d
    return (round(100*(c-h), 2), round(100*(c+h), 2))


def reasoning_subcat(comp, subtask):
    s = (subtask or "").lower()
    if comp == "MK": return "Mechanism/Pathophysiology"
    if comp == "PC_MGMT": return "Treatment/Management"
    if comp == "PC_DX":
        if "formulate" in s or s == "diagnosis": return "Diagnosis"
        if "labs_dx_studies" in s and ("select" in s): return "Next Step/Workup"
        # default for hx_pe / prognosis / predict-result
        return "Clinical Findings"
    return "Non-clinical (COMM/PROF/SBP/PBL)"


def load_full(model, temp, run):
    f = os.path.join(FULL, model, f"temp{temp}_run{run}_results.json")
    if not os.path.exists(f): return None
    d = json.load(open(f))
    return {int(r["question_id"]): bool(r["is_correct"]) if isinstance(r["is_correct"], bool)
            else str(r["is_correct"]).lower() == "true" for r in d}


def main():
    if not os.path.exists(LABELS):
        print("No competency labels yet:", LABELS)
        print("Run scripts/dataset_generation/classify_competencies.py first.")
        return
    lab = {}
    for line in open(LABELS):
        try:
            o = json.loads(line); lab[int(o["qid"])] = (o["competency"], o.get("subtask", ""))
        except Exception: pass
    print(f"labels: {len(lab)}")
    print("competency distribution:", Counter(c for c, _ in lab.values()).most_common())
    sub = Counter(reasoning_subcat(c, s) for c, s in lab.values())
    print("reasoning sub-category distribution:", sub.most_common())

    # per-competency accuracy by model at t=0.0 (mean over available runs)
    rows, sub_rows = [], []
    for m in MODELS:
        runs = [load_full(m, 0.0, r) for r in (1, 2, 3)]
        runs = [x for x in runs if x]
        if not runs:
            continue
        # aggregate correctness per qid = mean over runs (then per question use run-mean)
        def correct_frac(qid):
            vals = [rn[qid] for rn in runs if qid in rn]
            return mean(vals) if vals else None
        # competency-level
        by_comp = defaultdict(list)
        by_sub = defaultdict(list)
        for qid, (comp, st) in lab.items():
            cf = correct_frac(qid)
            if cf is None: continue
            by_comp[comp].append(cf)
            by_sub[reasoning_subcat(comp, st)].append(cf)
        for comp, vals in by_comp.items():
            n = len(vals); k = sum(vals)
            lo, hi = wilson(k, n)
            rows.append({"model": NAME[m], "competency": COMP_NAME.get(comp, comp),
                         "n": n, "acc": round(100*k/n, 2), "ci_lo": lo, "ci_hi": hi})
        for sc, vals in by_sub.items():
            n = len(vals); k = sum(vals)
            lo, hi = wilson(k, n)
            sub_rows.append({"model": NAME[m], "subcategory": sc, "n": n,
                             "acc": round(100*k/n, 2), "ci_lo": lo, "ci_hi": hi})
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "full_competency_accuracy.csv"), index=False)
    pd.DataFrame(sub_rows).to_csv(os.path.join(OUT, "full_reasoning_subcat_accuracy.csv"), index=False)
    print("\n=== Per-competency accuracy (t=0.0) ===")
    print(pd.DataFrame(rows).to_string(index=False))
    print("\nWrote full_competency_accuracy.csv + full_reasoning_subcat_accuracy.csv")


if __name__ == "__main__":
    main()
