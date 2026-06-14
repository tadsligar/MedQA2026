#!/usr/bin/env python3
"""
Paper 4 HEADLINE TEST — directional asymmetry: forward/mechanistic (F) vs backward/diagnostic (B)
accuracy in base LLMs, on the EXISTING full-set greedy runs (no GPU).

For each model: acc(F), acc(B), gap = acc(F) - acc(B), with a bootstrap 95% CI on the gap
(F and B are different question pools, so we resample each pool independently). Reports whether the
sign is CONSISTENT across all five models (the H1 claim) via a sign test. Optionally fits a
mixed-effects / GLM logistic model if statsmodels is installed (random or fixed model effect),
reporting the pooled F-vs-B contrast in log-odds; otherwise the pooled bootstrap stands alone.

Outputs (papers/paper4/tables/):
  asymmetry_FvsB.csv   model, acc_F, acc_B, gap_pp, gap_lo, gap_hi, n_F, n_B
Self-skips if labels absent.
"""
import os, json, glob, argparse
from collections import defaultdict
import numpy as np
import pandas as pd

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
FULL = os.path.join(_REPO, "results", "base_runs_full")
OUT = os.path.join(_REPO, "papers", "paper4", "tables")
os.makedirs(OUT, exist_ok=True)
MODELS = ["olmo3_7b", "olmo3_32b", "qwen25_7b", "qwen25_14b", "qwen25_32b"]
NAME = {"olmo3_7b": "OLMo-3 7B", "olmo3_32b": "OLMo-3 32B", "qwen25_7b": "Qwen2.5 7B",
        "qwen25_14b": "Qwen2.5 14B", "qwen25_32b": "Qwen2.5 32B"}
RNG = np.random.default_rng(20260612)


def load_runs(model, temp=0.0):
    per = defaultdict(list)
    for f in glob.glob(os.path.join(FULL, model, f"temp{temp}_run*_results.json")):
        for r in json.load(open(f)):
            ic = r["is_correct"]; ic = ic if isinstance(ic, bool) else str(ic).lower() == "true"
            per[int(r["question_id"])].append(ic)
    return {q: (1 if sum(v) * 2 >= len(v) else 0) for q, v in per.items()}


def load_ops(path):
    op = {}
    for line in open(path):
        try: o = json.loads(line)
        except Exception: continue
        if o.get("parse_fail") or not o.get("reasoning_operation"): continue
        op[int(o["qid"])] = o["reasoning_operation"]
    return op


def boot_gap(fc, bc, n=5000):
    """bootstrap CI for mean(fc) - mean(bc) with independent resampling of each pool."""
    fc, bc = np.array(fc), np.array(bc)
    if len(fc) == 0 or len(bc) == 0: return (None, None)
    diffs = np.empty(n)
    for i in range(n):
        diffs[i] = RNG.choice(fc, len(fc)).mean() - RNG.choice(bc, len(bc)).mean()
    return (round(100*np.percentile(diffs, 2.5), 2), round(100*np.percentile(diffs, 97.5), 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", default=os.path.join(_REPO, "results/reasoning_ops/op_labels.jsonl"))
    args = ap.parse_args()
    if not os.path.exists(args.labels):
        print("No labels yet:", args.labels); return
    op = load_ops(args.labels)
    rows, item = [], []
    for m in MODELS:
        runs = load_runs(m)
        if not runs: continue
        fc = [runs[q] for q, o in op.items() if o == "F" and q in runs]
        bc = [runs[q] for q, o in op.items() if o == "B" and q in runs]
        if not fc or not bc: continue
        accF, accB = 100*np.mean(fc), 100*np.mean(bc)
        lo, hi = boot_gap(fc, bc)
        rows.append({"model": NAME[m], "acc_F": round(accF, 2), "acc_B": round(accB, 2),
                     "gap_pp": round(accF-accB, 2), "gap_lo": lo, "gap_hi": hi,
                     "n_F": len(fc), "n_B": len(bc)})
        for q, o in op.items():
            if q in runs and o in ("F", "B"):
                item.append((m, o, runs[q]))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, "asymmetry_FvsB.csv"), index=False)
    print("=== Forward (F) vs Backward (B) accuracy, per model ===")
    print(df.to_string(index=False))

    if len(df):
        gaps = df["gap_pp"].values
        pos, neg = int((gaps > 0).sum()), int((gaps < 0).sum())
        direction = "F>B (forward easier)" if gaps.mean() > 0 else "B>F (backward easier)"
        n_sig = int(((df["gap_lo"] > 0) | (df["gap_hi"] < 0)).sum())
        print(f"\nPooled mean gap (F-B): {gaps.mean():.2f} pp   direction: {direction}")
        print(f"Sign consistency: {pos}/{len(gaps)} models F>B, {neg}/{len(gaps)} B>F; "
              f"{n_sig}/{len(gaps)} models have a CI excluding 0.")
        # binomial sign test vs 0.5
        from math import comb
        k = max(pos, neg); tot = len(gaps)
        p = sum(comb(tot, j) for j in range(k, tot+1)) / (2**tot) * 2
        print(f"Two-sided sign test p = {min(p,1.0):.3f} (H1: asymmetry consistent across models)")

    # optional model-based confirmation
    try:
        import statsmodels.formula.api as smf
        import statsmodels.api as sm
        d = pd.DataFrame(item, columns=["model", "op", "correct"])
        d["op"] = pd.Categorical(d["op"], categories=["B", "F"])  # B = reference
        glm = smf.glm("correct ~ C(op) + C(model)", data=d, family=sm.families.Binomial()).fit()
        coef = glm.params.get("C(op)[T.F]"); ci = glm.conf_int().loc["C(op)[T.F]"]
        print(f"\n[statsmodels GLM] F-vs-B log-odds (model-adjusted): {coef:.3f} "
              f"[{ci[0]:.3f}, {ci[1]:.3f}], p={glm.pvalues['C(op)[T.F]']:.3g}")
        print("  (positive => forward easier than backward, controlling for model)")
    except ImportError:
        print("\n(statsmodels not installed — pooled bootstrap + sign test above stand alone; "
              "`pip install statsmodels` to add the model-adjusted GLM contrast.)")
    print("\nWrote asymmetry_FvsB.csv to", OUT)


if __name__ == "__main__":
    main()
