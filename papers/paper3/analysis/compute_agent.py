#!/usr/bin/env python3
"""
Paper 3 — agent evaluation analysis.

Aggregates agent result files (results/agent/eval/*.json and ablations/*.json) and compares to:
  - LLM-only baseline (Qwen2.5-32B base, t=0.0)  = 73.40%
  - oracle any-of-5 ceiling                       = 86.0% (seed)
Reports overall + per-category accuracy, evidence efficiency (avg steps), McNemar vs LLM
baseline, and an evidence-function-selection distribution. GPU-free; self-skips missing files.
"""
import json, os, glob
from collections import Counter
import pandas as pd
from scipy.stats import binomtest

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
EVAL = os.path.join(_REPO, "results", "agent", "eval")
ABL = os.path.join(_REPO, "results", "agent", "ablations")
BASE = os.path.join(_REPO, "results", "base_runs", "qwen25_32b", "temp0.0_run1_results.json")
OUT = os.path.join(_REPO, "papers", "paper3", "tables")
os.makedirs(OUT, exist_ok=True)
CATS = ["Clinical Findings", "Diagnosis", "Mechanism/Pathophysiology",
        "Next Step/Workup", "Treatment/Management"]
ORACLE = 86.0


def load(p):
    if not os.path.exists(p):
        return None
    d = json.load(open(p)); d.sort(key=lambda x: x["question_id"]); return d


def acc(recs, cat=None):
    rs = [r for r in recs if cat is None or r["category"] == cat]
    return round(100 * sum(r["is_correct"] for r in rs) / len(rs), 2) if rs else None


def mcnemar(a, b):
    if not a or not b or len(a) != len(b):
        return None
    b10 = sum(1 for x, y in zip(a, b) if x["is_correct"] and not y["is_correct"])
    b01 = sum(1 for x, y in zip(a, b) if not x["is_correct"] and y["is_correct"])
    nd = b10 + b01
    return binomtest(min(b10, b01), nd, 0.5).pvalue if nd else 1.0


def collect(dirpath):
    methods = {}
    for p in sorted(glob.glob(os.path.join(dirpath, "*.json"))):
        methods[os.path.basename(p).replace("_results.json", "").replace(".json", "")] = load(p)
    return methods


def main():
    base = load(BASE)
    evalm = collect(EVAL)
    ablm = collect(ABL)
    if not evalm and not ablm:
        print("No agent results under", EVAL, "or", ABL)
        print("Run slurm/agent/* (or python -m neurosymbolic.agent.src.agent ...) first.")
        return

    rows, cat_rows, fn_rows = [], [], []
    for name, recs in {**evalm, **ablm}.items():
        if not recs:
            continue
        steps = sum(r.get("n_steps", 0) for r in recs) / len(recs)
        p = mcnemar(recs, base) if base else None
        rows.append({"system": name, "overall_acc": acc(recs),
                     "avg_steps": round(steps, 2),
                     "vs_LLM_pp": (round(acc(recs) - acc(base), 2) if base else None),
                     "vs_oracle_pp": round(acc(recs) - ORACLE, 2),
                     "mcnemar_p_vs_LLM": (f"{p:.2e}" if p is not None else "—")})
        for c in CATS:
            cat_rows.append({"system": name, "category": c, "acc": acc(recs, c)})
        fc = Counter(f for r in recs for f in r.get("functions_called", []))
        for fn, n in fc.most_common():
            fn_rows.append({"system": name, "function": fn, "calls": n})

    df = pd.DataFrame(rows).sort_values("overall_acc", ascending=False)
    df.to_csv(os.path.join(OUT, "agent_method_comparison.csv"), index=False)
    pd.DataFrame(cat_rows).to_csv(os.path.join(OUT, "agent_category.csv"), index=False)
    pd.DataFrame(fn_rows).to_csv(os.path.join(OUT, "agent_function_selection.csv"), index=False)
    print("=== Agent systems (overall acc, efficiency, vs LLM 73.4% / oracle 86.0%) ===")
    print(df.to_string(index=False))
    print("\nWrote agent_*.csv to", OUT)


if __name__ == "__main__":
    main()
