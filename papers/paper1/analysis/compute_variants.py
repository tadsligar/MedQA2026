#!/usr/bin/env python3
"""
Paper 1 EXP3/4/5 — analysis of prompt-ablation, CoT-vs-direct, and self-consistency runs.

Reads (whichever exist):
  EXP3: results/prompt_ablation/<model>/<variant>/temp0.0_run1_results.json
        (or a single dir with `variant` field per record)
  EXP4: results/cot_vs_direct/<model>/{direct,cot}/temp{t}_run{r}_results.json
  EXP5: results/self_consistency/<model>/temp0.7_run1_results.json (records carry all_predictions)
Each block self-skips if its inputs are absent. GPU-free.
"""
import os
import json, os, glob
from collections import Counter
from statistics import mean

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import _full_common as fc

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # repo root from papers/<paper>/analysis/
REPO = _REPO
OUT = os.path.join(REPO, "papers", "paper1", "tables")
FIG = os.path.join(REPO, "papers", "paper1", "figures")
os.makedirs(OUT, exist_ok=True); os.makedirs(FIG, exist_ok=True)
CATS = ["Clinical Findings", "Diagnosis", "Mechanism/Pathophysiology",
        "Next Step/Workup", "Treatment/Management"]


def acc(recs, cat=None):
    rs = [r for r in recs if cat is None or r["category"] == cat]
    return 100 * sum(r["is_correct"] for r in rs) / len(rs) if rs else None


def load(path):
    if not os.path.exists(path):
        return None
    d = json.load(open(path)); d.sort(key=lambda x: x["question_id"]); return d


# ----------------------------- EXP3 prompt ablation -----------------------------
def exp3(full=False):
    base = os.path.join(REPO, "results", "prompt_ablation_full" if full else "prompt_ablation")
    sfx = "_full" if full else ""
    if not os.path.isdir(base):
        print(f"EXP3: no {base} — skip"); return
    rows, slice_rows = [], []
    cat_profiles = {}  # variant -> [cat accs]  (focused only; full is category-free)
    for model_dir in sorted(glob.glob(os.path.join(base, "*"))):
        model = os.path.basename(model_dir)
        for vdir in sorted(glob.glob(os.path.join(model_dir, "*"))):
            variant = os.path.basename(vdir)
            recs = load(os.path.join(vdir, "temp0.0_run1_results.json"))
            if not recs:
                continue
            row = {"model": model, "variant": variant, "overall": round(acc(recs), 2), "n": len(recs)}
            if not full:
                for c in CATS:
                    row[c] = round(acc(recs, c), 2)
                cat_profiles.setdefault(model, {})[variant] = [acc(recs, c) for c in CATS]
            rows.append(row)
            if full:
                s = fc.slice_to_test(recs)
                slice_rows.append({"model": model, "variant": variant,
                                   "overall_testslice": round(acc(s), 2), "n": len(s)})
    if not rows:
        print("EXP3: no variant results found — skip"); return
    pd.DataFrame(rows).to_csv(os.path.join(OUT, f"exp3_prompt_ablation{sfx}.csv"), index=False)
    if slice_rows:
        pd.DataFrame(slice_rows).to_csv(os.path.join(OUT, "exp3_prompt_ablation_full_testslice.csv"), index=False)
    # overall accuracy range per model (always)
    for model in sorted({r["model"] for r in rows}):
        accs = [r["overall"] for r in rows if r["model"] == model]
        print(f"EXP3 {model}: overall acc range across variants = {min(accs):.2f}-{max(accs):.2f} "
              f"(spread {max(accs)-min(accs):.2f} pp)")
    if not full:  # category-rank stability only when categories are present
        for model, profs in cat_profiles.items():
            variants = list(profs)
            if len(variants) >= 2:
                rhos = []
                for i in range(len(variants)):
                    for j in range(i + 1, len(variants)):
                        rho, _ = spearmanr(profs[variants[i]], profs[variants[j]])
                        rhos.append(rho)
                print(f"EXP3 {model}: mean category-rank Spearman across variants = {np.nanmean(rhos):.3f}")
    print(f"EXP3: wrote exp3_prompt_ablation{sfx}.csv")


# ----------------------------- EXP4 CoT vs direct -----------------------------
def exp4(full=False):
    base = os.path.join(REPO, "results", "cot_vs_direct_full" if full else "cot_vs_direct")
    sfx = "_full" if full else ""
    if not os.path.isdir(base):
        print(f"EXP4: no {base} — skip"); return
    rows, slice_rows = [], []
    for model_dir in sorted(glob.glob(os.path.join(base, "*"))):
        model = os.path.basename(model_dir)
        for temp in ["0.0", "0.7"]:
            d = load(os.path.join(model_dir, "direct", f"temp{temp}_run1_results.json"))
            c = load(os.path.join(model_dir, "cot", f"temp{temp}_run1_results.json"))
            if not d or not c:
                continue
            rows.append({"model": model, "temp": temp,
                         "direct_acc": round(acc(d), 2), "cot_acc": round(acc(c), 2),
                         "delta_pp": round(acc(c) - acc(d), 2),
                         "direct_mean_tokens": round(mean(r["tokens"] for r in d), 1),
                         "cot_mean_tokens": round(mean(r["tokens"] for r in c), 1)})
            if full:
                ds, cs = fc.slice_to_test(d), fc.slice_to_test(c)
                slice_rows.append({"model": model, "temp": temp,
                                   "direct_acc": round(acc(ds), 2), "cot_acc": round(acc(cs), 2),
                                   "delta_pp": round(acc(cs) - acc(ds), 2), "n": len(ds)})
    if not rows:
        print("EXP4: no paired direct/cot results — skip"); return
    pd.DataFrame(rows).to_csv(os.path.join(OUT, f"exp4_cot_vs_direct{sfx}.csv"), index=False)
    if slice_rows:
        pd.DataFrame(slice_rows).to_csv(os.path.join(OUT, "exp4_cot_vs_direct_full_testslice.csv"), index=False)
    print(f"EXP4: wrote exp4_cot_vs_direct{sfx}.csv")
    print(pd.DataFrame(rows).to_string(index=False))


# ----------------------------- EXP5 self-consistency -----------------------------
def _greedy_ref(model, full):
    """Best single-greedy accuracy to draw as the reference line. For --full, read the model's
    full t=0.0 run (base logprob run, else prompt-ablation v0); for focused, the verified 73.4."""
    if not full:
        return 73.4, "best single greedy (73.4%)"
    for cand in (os.path.join(REPO, "results", "base_runs_logprobs_full", model, "temp0.0_run1_results.json"),
                 os.path.join(REPO, "results", "prompt_ablation_full", model, "v0", "temp0.0_run1_results.json")):
        recs = load(cand)
        if recs:
            a = acc(recs)
            return a, f"greedy t=0.0 ({a:.1f}%)"
    return None, None


def _curve(recs, ks):
    accs = []
    for k in ks:
        c = sum(1 for r in recs if Counter(r["all_predictions"][:k]).most_common(1)[0][0] == r["correct"])
        accs.append(100 * c / len(recs))
    return accs


def exp5(full=False):
    base = os.path.join(REPO, "results", "self_consistency_full" if full else "self_consistency")
    sfx = "_full" if full else ""
    if not os.path.isdir(base):
        print(f"EXP5: no {base} — skip"); return
    rows, slice_rows = [], []
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 5))
    ref_drawn = False
    for model_dir in sorted(glob.glob(os.path.join(base, "*"))):
        model = os.path.basename(model_dir)
        recs = None
        for f in glob.glob(os.path.join(model_dir, "temp*_run1_results.json")):
            recs = load(f); break
        if not recs or "all_predictions" not in recs[0]:
            continue
        K = len(recs[0]["all_predictions"])
        ks = [k for k in [1, 3, 5, 10, 20] if k <= K]
        accs = _curve(recs, ks)
        for k, a in zip(ks, accs):
            rows.append({"model": model, "k": k, "majority_vote_acc": round(a, 2)})
        ax.plot(ks, accs, marker="o", label=model)
        if full:
            saccs = _curve(fc.slice_to_test(recs), ks)
            for k, a in zip(ks, saccs):
                slice_rows.append({"model": model, "k": k, "majority_vote_acc": round(a, 2)})
        ref, lbl = _greedy_ref(model, full)
        if ref is not None and not ref_drawn:
            ax.axhline(ref, ls="--", color="gray", lw=1, label=lbl); ref_drawn = True
    if not rows:
        print("EXP5: no self-consistency results — skip"); return
    pd.DataFrame(rows).to_csv(os.path.join(OUT, f"exp5_self_consistency{sfx}.csv"), index=False)
    if slice_rows:
        pd.DataFrame(slice_rows).to_csv(os.path.join(OUT, "exp5_self_consistency_full_testslice.csv"), index=False)
    ax.set_xlabel("k samples"); ax.set_ylabel("Majority-vote accuracy (%)")
    ax.set_title("Self-consistency scaling (t=0.7)"); ax.legend(fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, f"fig8_self_consistency{sfx}.png"))
    print(f"EXP5: wrote exp5_self_consistency{sfx}.csv + fig8_self_consistency{sfx}.png")


if __name__ == "__main__":
    args = fc.add_full_arg("Paper1 EXP3/4/5 variants (focused or --full)")
    exp3(args.full); exp4(args.full); exp5(args.full)
    print("\nDone. (Blocks with no inputs were skipped.)")