#!/usr/bin/env python3
"""
Paper 2 — assemble the master method-comparison table (Table 3 / Table 4).

Collects whichever method result files exist and reports overall + per-category accuracy,
each with a paired McNemar vs the LLM-only baseline (Qwen2.5-32B base run, t=0.0).
Methods auto-discovered:
  LLM-only (base)        results/base_runs/qwen25_32b/temp0.0_run1_results.json
  symbolic-{overlap,relation,tfidf}  results/ns/symbolic/*_results.json
  umls-in-prompt         results/ns/umls_in_prompt/*_results.json
  verifier-rerank        results/ns/verifier_rerank/*_results.json
  cove-*                 results/ns/cove/*_results.json
  hybrid                 results/ns/hybrid/*_results.json
GPU-free; self-skips missing files.
"""
import os
import json, os, glob, math
from scipy.stats import binomtest
import pandas as pd

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # repo root from papers/<paper>/analysis/
REPO = _REPO
NS = os.path.join(REPO, "results", "ns")
BASE = os.path.join(REPO, "results", "base_runs", "qwen25_32b", "temp0.0_run1_results.json")
OUT = os.path.join(REPO, "papers", "paper2", "tables")
os.makedirs(OUT, exist_ok=True)
CATS = ["Clinical Findings", "Diagnosis", "Mechanism/Pathophysiology",
        "Next Step/Workup", "Treatment/Management"]


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


def discover():
    methods = {}
    base = load(BASE)
    if base:
        methods["LLM-only (Qwen2.5-32B)"] = base
    for p in sorted(glob.glob(os.path.join(NS, "symbolic", "*_results.json"))):
        methods[f"symbolic-{os.path.basename(p).split('_')[0]}"] = load(p)
    for sub, label in [("umls_in_prompt", "UMLS-in-prompt"), ("verifier_rerank", "verifier-rerank"),
                       ("hybrid", "hybrid")]:
        for p in sorted(glob.glob(os.path.join(NS, sub, "*_results.json"))):
            if "_lambda_sweep" in p:
                continue
            methods[label] = load(p)
    for p in sorted(glob.glob(os.path.join(NS, "cove", "*_results.json"))):
        name = os.path.basename(p).replace("_results.json", "")
        methods[f"cove-{name}"] = load(p)
    return methods, base


def main():
    methods, base = discover()
    methods = {k: v for k, v in methods.items() if v}
    if not methods:
        print("No method results found under", NS, "and", BASE)
        print("Run the symbolic core + hybrid/verification jobs first.")
        return
    rows, cat_rows = [], []
    for name, recs in methods.items():
        row = {"method": name, "overall": acc(recs)}
        p = mcnemar(recs, base) if (base and name != "LLM-only (Qwen2.5-32B)") else None
        row["mcnemar_p_vs_LLM"] = (f"{p:.2e}" if p is not None else "—")
        rows.append(row)
        for c in CATS:
            cat_rows.append({"method": name, "category": c, "acc": acc(recs, c)})
    df = pd.DataFrame(rows).sort_values("overall", ascending=False)
    df.to_csv(os.path.join(OUT, "table3_method_comparison.csv"), index=False)
    pd.DataFrame(cat_rows).to_csv(os.path.join(OUT, "table4_method_category.csv"), index=False)
    print("=== Table 3: method comparison (overall, McNemar vs LLM-only) ===")
    print(df.to_string(index=False))
    print("\nWrote table3_method_comparison.csv + table4_method_category.csv to", OUT)


if __name__ == "__main__":
    main()