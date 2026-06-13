#!/usr/bin/env python3
"""
Paper 1 EXP1 — calibration analysis from logprob runs (multi-run aware).

Consumes results/base_runs_logprobs/<model>/temp0.0_run{1,2,3}_results.json (produced by
scripts/base_runs/test_base_model_logprobs.py) and computes:
  - Per-run accuracy, MEDIAN accuracy, and accuracy spread (max-min) across available runs
  - Cross-run determinism: % of questions where ALL available runs predict the identical
    letter. At t=0.0 (greedy) this must be 100%; anything less is a finding (non-determinism
    in serving/decoding), and a WARNING is printed.
  - ECE (expected calibration error) + reliability-diagram bins, per model  [on the MEDIAN run]
  - Risk-coverage curve (accuracy when abstaining below a confidence threshold)
  - Correlation between greedy confidence and Paper 1's t=0.7 cross-run stability
    (validates the logit-free stability proxy)
  - Per-category ECE
  - Qwen2.5-7B diagnosis: every available logprob run vs the verified base run
    (results/base_runs/qwen25_7b/temp0.0_run1_results.json) — does the ~8 pp gap persist?
Outputs CSVs to papers/paper1/tables/ and figures to papers/paper1/figures/.

This script is GPU-free; run it after the SLURM logprob jobs finish. It self-checks that
the re-run t=0.0 accuracy matches the verified base-run numbers within tolerance.
"""
import os
import json, os, math
from collections import defaultdict
from statistics import mean, median

import numpy as np
import pandas as pd
import _full_common as fc

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
RUN_NUMBERS = (1, 2, 3)
SPREAD_WARN_PP = 1.0   # accuracy spread above this (pp) is flagged


def load_runs(model):
    """Return {run_number: results-list-sorted-by-qid} for every run file that exists."""
    runs = {}
    for r in RUN_NUMBERS:
        f = os.path.join(LP_DIR, model, f"temp0.0_run{r}_results.json")
        if os.path.exists(f):
            d = json.load(open(f)); d.sort(key=lambda x: x["question_id"]); runs[r] = d
    return runs


def run_accuracy(run_list):
    return 100.0 * mean(1 if r["is_correct"] else 0 for r in run_list)


def cross_run_agreement(runs):
    """% of common questions where every available run predicts the identical letter.
    Returns (pct, n_common, n_disagree) or (None, 0, 0) when <2 runs are available."""
    nums = sorted(runs)
    if len(nums) < 2:
        return None, 0, 0
    preds = {n: {r["question_id"]: r["predicted"] for r in runs[n]} for n in nums}
    common = sorted(set.intersection(*[set(p) for p in preds.values()]))
    if not common:
        return None, 0, 0
    disagree = [q for q in common if len({preds[n][q] for n in nums}) > 1]
    pct = 100.0 * (len(common) - len(disagree)) / len(common)
    return pct, len(common), len(disagree)


def pick_median_run(runs):
    """Run number whose accuracy is the median across available runs.
    For an even count (no single middle), pick the run closest to the median value;
    ties break to the lower run number. Returns (run_number, {run: acc})."""
    nums = sorted(runs)
    accs = {n: run_accuracy(runs[n]) for n in nums}
    med = median(accs.values())
    best = min(nums, key=lambda n: (abs(accs[n] - med), n))
    return best, accs


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


def qwen7b_diagnosis(runs_by_model):
    """Compare every available qwen25_7b logprob run to the verified base run."""
    m = "qwen25_7b"
    base_f = os.path.join(BASE_DIR, m, "temp0.0_run1_results.json")
    runs = runs_by_model.get(m, {})
    if not runs or not os.path.exists(base_f):
        return []
    base = json.load(open(base_f))
    base_pred = {r["question_id"]: r["predicted"] for r in base}
    base_acc = run_accuracy(base)
    rows = []
    for rn in sorted(runs):
        lp = runs[rn]
        lp_pred = {r["question_id"]: r["predicted"] for r in lp}
        lp_acc = run_accuracy(lp)
        common = sorted(set(base_pred) & set(lp_pred))
        disagree = [q for q in common if base_pred[q] != lp_pred[q]]
        rows.append({
            "run": rn,
            "lp_acc": round(lp_acc, 2),
            "base_acc": round(base_acc, 2),
            "acc_gap_pp": round(lp_acc - base_acc, 2),
            "pred_agreement_pct": round(100.0 * (len(common) - len(disagree)) / len(common), 2) if common else None,
            "n_disagree": len(disagree),
            "n_common": len(common),
        })
    return rows


def main():
    global LP_DIR
    args = fc.add_full_arg("EXP1 calibration (focused or --full)")
    full = args.full
    sfx = "_full" if full else ""
    if full:
        LP_DIR = os.path.join(REPO, "results", "base_runs_logprobs_full")
    runs_by_model = {m: load_runs(m) for m in MODELS}
    present = [m for m in MODELS if runs_by_model[m]]
    if not present:
        print("No logprob results found under", LP_DIR)
        print("Run the SLURM jobs first, then re-run this script.")
        return

    # --- Multi-run summary: per-run acc, median, spread, cross-run determinism ---
    have = {}            # model -> median-run results list (used for ECE/reliability downstream)
    median_run = {}      # model -> chosen run number
    runs_rows = []
    warnings = []
    for m in present:
        runs = runs_by_model[m]
        mrun, accs = pick_median_run(runs)
        median_run[m] = mrun
        have[m] = runs[mrun]
        spread = (max(accs.values()) - min(accs.values())) if len(accs) > 1 else 0.0
        agree_pct, n_common, n_disagree = cross_run_agreement(runs)
        warn = []
        if agree_pct is not None and agree_pct < 100.0:
            warn.append(f"cross-run agreement {agree_pct:.2f}% (<100%); {n_disagree} questions differ")
        if spread > SPREAD_WARN_PP:
            warn.append(f"accuracy spread {spread:.2f} pp (>{SPREAD_WARN_PP} pp)")
        if warn:
            warnings.append((NAME[m], warn))
        runs_rows.append({
            "model": NAME[m],
            "runs_available": ",".join(str(r) for r in sorted(runs)),
            "acc_run1": round(accs[1], 2) if 1 in accs else None,
            "acc_run2": round(accs[2], 2) if 2 in accs else None,
            "acc_run3": round(accs[3], 2) if 3 in accs else None,
            "median_acc": round(median(accs.values()), 2),
            "acc_spread_pp": round(spread, 2),
            "cross_run_agreement_pct": round(agree_pct, 2) if agree_pct is not None else None,
            "median_run_used": mrun,
            "warning": "; ".join(warn) if warn else "",
        })

    ece_rows, rel_rows, rc_rows, catece_rows, check_rows, slice_rows = [], [], [], [], [], []
    # t=0.7 cross-run instability is a focused-set, 3-run quantity; the full EXP1 grid is 1-run
    # and its qids don't align with the focused base_runs, so disable the correlation in --full.
    instab = {m: None for m in MODELS} if full else t07_instability()

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
        check_rows.append({"model": NAME[m], "median_run": median_run[m],
                           "rerun_acc": round(acc, 2),
                           "verified_acc": (None if full else VERIFIED[m]),
                           "abs_diff": (None if full else round(abs(acc - VERIFIED[m]), 2)),
                           "logprob_coverage_pct": round(cov, 1)})
        e, bins = ece(confs, corr)
        ece_rows.append({"model": NAME[m], "ECE": round(e, 4), "n": len(recs),
                         "mean_conf": round(mean(confs), 4),
                         "accuracy": round(mean(corr), 4)})
        if full:  # held-out test slice: accuracy + ECE
            shave = fc.slice_to_test(have[m])
            srecs = [r for r in shave if r.get("confidence") is not None]
            if shave:
                slice_rows.append({
                    "model": NAME[m], "n": len(shave),
                    "accuracy": round(100 * mean(1 if r["is_correct"] else 0 for r in shave), 2),
                    "ECE": round(ece([r["confidence"] for r in srecs],
                                     [1 if r["is_correct"] else 0 for r in srecs])[0], 4) if srecs else None,
                    "mean_conf": round(mean(r["confidence"] for r in srecs), 4) if srecs else None,
                    "logprob_coverage_pct": round(100 * len(srecs) / len(shave), 1)})
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
        # per-category ECE (focused only — full per-category labels are under revision)
        if not full:
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
    fig_rel.tight_layout(); fig_rel.savefig(os.path.join(FIG, f"fig7_reliability{sfx}.png"))

    diag_rows = [] if full else qwen7b_diagnosis(runs_by_model)

    pd.DataFrame(runs_rows).to_csv(os.path.join(OUT, f"calib_runs{sfx}.csv"), index=False)
    pd.DataFrame(ece_rows).to_csv(os.path.join(OUT, f"calib_ece{sfx}.csv"), index=False)
    pd.DataFrame(rel_rows).to_csv(os.path.join(OUT, f"calib_reliability_bins{sfx}.csv"), index=False)
    pd.DataFrame(rc_rows).to_csv(os.path.join(OUT, f"calib_risk_coverage{sfx}.csv"), index=False)
    if catece_rows:
        pd.DataFrame(catece_rows).to_csv(os.path.join(OUT, "calib_category_ece.csv"), index=False)
    pd.DataFrame(check_rows).to_csv(os.path.join(OUT, f"calib_selfcheck{sfx}.csv"), index=False)
    if slice_rows:
        pd.DataFrame(slice_rows).to_csv(os.path.join(OUT, "calib_ece_full_testslice.csv"), index=False)
    if diag_rows:
        pd.DataFrame(diag_rows).to_csv(os.path.join(OUT, "calib_qwen7b_diagnosis.csv"), index=False)

    print("=== Cross-run determinism (t=0.0 should be 100% agreement, 0 spread) ===")
    print(pd.DataFrame(runs_rows).to_string(index=False))
    if warnings:
        print()
        for name, ws in warnings:
            for w in ws:
                print(f"  *** WARNING [{name}]: {w}")
    else:
        print("\n  All models: 100% cross-run agreement and spread <= "
              f"{SPREAD_WARN_PP} pp (or single-run only).")

    print("\n=== Accuracy + coverage" + (" (FULL 12,723, 5-option)" if full
          else " vs verified") + " ===")
    print(pd.DataFrame(check_rows).to_string(index=False))
    print("\n=== ECE per model (median run) ===")
    print(pd.DataFrame(ece_rows).to_string(index=False))
    if slice_rows:
        print("\n=== Held-out test slice (1,273): accuracy + ECE ===")
        print(pd.DataFrame(slice_rows).to_string(index=False))

    if diag_rows:
        print("\n=== Qwen2.5-7B diagnosis: logprob runs vs verified base run "
              "(base_runs/qwen25_7b/temp0.0_run1) ===")
        print(pd.DataFrame(diag_rows).to_string(index=False))
        gaps = [r["acc_gap_pp"] for r in diag_rows]
        if all(abs(g) > SPREAD_WARN_PP for g in gaps):
            print(f"  *** The base-vs-logprob gap PERSISTS across all {len(gaps)} runs "
                  f"(gaps pp: {gaps}) — reproducible, not a one-off bad launch.")
        elif any(abs(g) > SPREAD_WARN_PP for g in gaps):
            print(f"  *** The gap is INCONSISTENT across runs (gaps pp: {gaps}) — "
                  "at least one run reproduces the base, so suspect a one-off bad launch.")
        else:
            print(f"  All runs reproduce the base within {SPREAD_WARN_PP} pp (gaps pp: {gaps}).")

    print("\nWrote calibration CSVs to", OUT, "and fig7_reliability.png")
    print("NOTE: if abs_diff is large, decoding/prompt diverged from the base run — investigate.")


if __name__ == "__main__":
    main()
