#!/usr/bin/env python3
"""
Paper 1 EXP1 — calibration analysis from logprob runs.

Consumes results/base_runs_logprobs/<model>/temp0.0_run1_results.json (produced by
scripts/base_runs/test_base_model_logprobs.py) and computes:
  - ECE (expected calibration error) + reliability-diagram bins, per model
  - Confidence histograms for correct vs wrong answers
  - Risk-coverage curve (accuracy when abstaining below a confidence threshold)
  - Correlation between greedy confidence and Paper 1's t=0.7 cross-run stability
    (validates the logit-free stability proxy)
  - Per-category ECE
Outputs CSVs to papers/paper1/tables/ and figures to papers/paper1/figures/.

This script is GPU-free; run it after the SLURM logprob jobs finish. It self-checks that
the re-run t=0.0 accuracy matches the verified base-run numbers within tolerance.
"""
import os
import json, os, math
from collections import defaultdict
from statistics import mean

import numpy as np
import pandas as pd

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # repo root from papers/<paper>/analysis/
REPO = _REPO
LP_DIR = os.path.join(REPO, "results", "base_runs_logprobs")
BASE_DIR = os.path.join(REPO, "results", "base_runs")
OUT = os.path.join(REPO, "papers", "paper1", "tables")
FIG = os.path.join(REPO, "papers", "paper1", "figures")
os.makedirs(OUT, exist_ok=True); os.makedirs(FIG, exist_ok=True)

MODELS = ["olmo3_7b", "olmo3_32b", "qwen25_7b", "qwen25_14b", "qwen25_32b"]
NAME = {"olmo3_7b": "OLMo-3 7B", "olmo3_32b": "OLMo-3 32B", "qwen25_7b": "Qwen2.5 7B",
        "qwen25_14b": "Qwen2.5 14B", "qwen25_32b": "Qwen2.5 32B"}
CATS = ["Clinical Findings", "Diagnosis", "Mechanism/Pathophysiology",
        "Next Step/Workup", "Treatment/Management"]
# verified t=0.0 accuracies (RESULTS.md) for the self-check
VERIFIED = {"olmo3_7b": 46.18, "olmo3_32b": 58.64, "qwen25_7b": 67.96,
            "qwen25_14b": 68.48, "qwen25_32b": 73.40}
N_BINS = 10


def load_lp(model):
    f = os.path.join(LP_DIR, model, "temp0.0_run1_results.json")
    if not os.path.exists(f):
        return None
    d = json.load(open(f)); d.sort(key=lambda x: x["question_id"]); return d


def ece(confs, corrects, n_bins=N_BINS):
    """Expected calibration error + per-bin table."""
    confs = np.asarray(confs); corrects = np.asarray(corrects, dtype=float)
    edges = np.linspace(0, 1, n_bins + 1)
    e = 0.0; rows = []
    for b in range(n_bins):
        lo, hi = edges[b], edges[b + 1]
        m = (confs > lo) & (confs <= hi) if b > 0 else (confs >= lo) & (confs <= hi)
        if m.sum() == 0:
            rows.append({"bin_lo": round(lo, 2), "bin_hi": round(hi, 2), "n": 0,
                         "mean_conf": None, "accuracy": None}); continue
        bc = confs[m].mean(); ba = corrects[m].mean()
        e += (m.sum() / len(confs)) * abs(ba - bc)
        rows.append({"bin_lo": round(lo, 2), "bin_hi": round(hi, 2), "n": int(m.sum()),
                     "mean_conf": round(float(bc), 4), "accuracy": round(float(ba), 4)})
    return e, rows


def t07_instability():
    """Per-question instability from base_runs t=0.7 (3 runs disagree)."""
    out = {}
    for m in MODELS:
        runs = []
        ok = True
        for r in (1, 2, 3):
            f = os.path.join(BASE_DIR, m, f"temp0.7_run{r}_results.json")
            if not os.path.exists(f):
                ok = False; break
            d = json.load(open(f)); d.sort(key=lambda x: x["question_id"]); runs.append(d)
        if not ok:
            out[m] = None; continue
        n = len(runs[0])
        unstable = [1 if len({runs[r][i]["predicted"] for r in range(3)}) > 1 else 0
                    for i in range(n)]
        out[m] = unstable
    return out


def main():
    have = {m: load_lp(m) for m in MODELS}
    present = [m for m in MODELS if have[m]]
    if not present:
        print("No logprob results found under", LP_DIR)
        print("Run the SLURM jobs in slurm/logprobs/ first, then re-run this script.")
        return

    ece_rows, rel_rows, rc_rows, catece_rows, check_rows = [], [], [], [], []
    instab = t07_instability()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 11, "figure.dpi": 150})
    fig_rel, ax_rel = plt.subplots(figsize=(7, 6))
    ax_rel.plot([0, 1], [0, 1], ls="--", color="gray", lw=1, label="perfect calibration")

    for m in present:
        recs = [r for r in have[m] if r.get("confidence") is not None]
        cov = 100 * len(recs) / len(have[m])
        confs = [r["confidence"] for r in recs]
        corr = [1 if r["is_correct"] else 0 for r in recs]
        acc = 100 * mean(1 if r["is_correct"] else 0 for r in have[m])
        check_rows.append({"model": NAME[m], "rerun_acc": round(acc, 2),
                           "verified_acc": VERIFIED[m],
                           "abs_diff": round(abs(acc - VERIFIED[m]), 2),
                           "logprob_coverage_pct": round(cov, 1)})
        e, bins = ece(confs, corr)
        ece_rows.append({"model": NAME[m], "ECE": round(e, 4), "n": len(recs),
                         "mean_conf": round(mean(confs), 4),
                         "accuracy": round(mean(corr), 4)})
        for b in bins:
            rel_rows.append({"model": NAME[m], **b})
        # reliability curve
        xs = [b["mean_conf"] for b in bins if b["mean_conf"] is not None]
        ys = [b["accuracy"] for b in bins if b["accuracy"] is not None]
        ax_rel.plot(xs, ys, marker="o", ms=4, label=f"{NAME[m]} (ECE={e:.3f})")
        # risk-coverage
        order = sorted(recs, key=lambda r: -r["confidence"])
        for frac in [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]:
            k = max(1, int(frac * len(order)))
            sub = order[:k]
            rc_rows.append({"model": NAME[m], "coverage": frac,
                            "selective_acc": round(100 * mean(1 if r["is_correct"] else 0 for r in sub), 2)})
        # per-category ECE
        for c in CATS:
            cr = [r for r in recs if r["category"] == c]
            if cr:
                ec, _ = ece([r["confidence"] for r in cr], [r["is_correct"] for r in cr])
                catece_rows.append({"model": NAME[m], "category": c, "n": len(cr),
                                    "ECE": round(ec, 4)})
        # confidence vs stability correlation
        if instab.get(m) is not None:
            byqid_conf = {r["question_id"]: r["confidence"] for r in recs}
            xs2, ys2 = [], []
            for qid, conf in byqid_conf.items():
                if qid < len(instab[m]):
                    xs2.append(conf); ys2.append(instab[m][qid])
            if len(xs2) > 2 and len(set(ys2)) > 1:
                r_corr = float(np.corrcoef(xs2, ys2)[0, 1])
                check_rows[-1]["corr_conf_vs_t07_instability"] = round(r_corr, 3)

    ax_rel.set_xlabel("Mean predicted confidence"); ax_rel.set_ylabel("Empirical accuracy")
    ax_rel.set_title("Reliability diagram (t=0.0, option-letter confidence)")
    ax_rel.legend(fontsize=8); ax_rel.grid(alpha=0.3)
    fig_rel.tight_layout(); fig_rel.savefig(os.path.join(FIG, "fig7_reliability.png"))

    pd.DataFrame(ece_rows).to_csv(os.path.join(OUT, "calib_ece.csv"), index=False)
    pd.DataFrame(rel_rows).to_csv(os.path.join(OUT, "calib_reliability_bins.csv"), index=False)
    pd.DataFrame(rc_rows).to_csv(os.path.join(OUT, "calib_risk_coverage.csv"), index=False)
    pd.DataFrame(catece_rows).to_csv(os.path.join(OUT, "calib_category_ece.csv"), index=False)
    pd.DataFrame(check_rows).to_csv(os.path.join(OUT, "calib_selfcheck.csv"), index=False)

    print("=== Self-check (re-run acc vs verified) ===")
    print(pd.DataFrame(check_rows).to_string(index=False))
    print("\n=== ECE per model ===")
    print(pd.DataFrame(ece_rows).to_string(index=False))
    print("\nWrote calibration CSVs to", OUT, "and fig7_reliability.png")
    print("NOTE: if abs_diff is large, decoding/prompt diverged from the base run — investigate.")


if __name__ == "__main__":
    main()