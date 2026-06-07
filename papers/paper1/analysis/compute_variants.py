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
def exp3():
    base = os.path.join(REPO, "results", "prompt_ablation")
    if not os.path.isdir(base):
        print("EXP3: no results/prompt_ablation/ — skip"); return
    rows = []
    cat_profiles = {}  # variant -> [cat accs]
    for model_dir in sorted(glob.glob(os.path.join(base, "*"))):
        model = os.path.basename(model_dir)
        for vdir in sorted(glob.glob(os.path.join(model_dir, "*"))):
            variant = os.path.basename(vdir)
            recs = load(os.path.join(vdir, "temp0.0_run1_results.json"))
            if not recs:
                continue
            row = {"model": model, "variant": variant, "overall": round(acc(recs), 2)}
            for c in CATS:
                row[c] = round(acc(recs, c), 2)
            rows.append(row)
            cat_profiles.setdefault(model, {})[variant] = [acc(recs, c) for c in CATS]
    if not rows:
        print("EXP3: no variant results found — skip"); return
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "exp3_prompt_ablation.csv"), index=False)
    # rank stability: Spearman of category ranks across variants (per model)
    for model, profs in cat_profiles.items():
        variants = list(profs)
        if len(variants) >= 2:
            rhos = []
            for i in range(len(variants)):
                for j in range(i + 1, len(variants)):
                    rho, _ = spearmanr(profs[variants[i]], profs[variants[j]])
                    rhos.append(rho)
            print(f"EXP3 {model}: mean category-rank Spearman across variants = {np.nanmean(rhos):.3f}")
    print("EXP3: wrote exp3_prompt_ablation.csv")


# ----------------------------- EXP4 CoT vs direct -----------------------------
def exp4():
    base = os.path.join(REPO, "results", "cot_vs_direct")
    if not os.path.isdir(base):
        print("EXP4: no results/cot_vs_direct/ — skip"); return
    rows = []
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
    if not rows:
        print("EXP4: no paired direct/cot results — skip"); return
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "exp4_cot_vs_direct.csv"), index=False)
    print("EXP4: wrote exp4_cot_vs_direct.csv")
    print(pd.DataFrame(rows).to_string(index=False))


# ----------------------------- EXP5 self-consistency -----------------------------
def exp5():
    base = os.path.join(REPO, "results", "self_consistency")
    if not os.path.isdir(base):
        print("EXP5: no results/self_consistency/ — skip"); return
    rows = []
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 5))
    for model_dir in sorted(glob.glob(os.path.join(base, "*"))):
        model = os.path.basename(model_dir)
        recs = None
        for f in glob.glob(os.path.join(model_dir, "temp*_run1_results.json")):
            recs = load(f); break
        if not recs or "all_predictions" not in recs[0]:
            continue
        K = len(recs[0]["all_predictions"])
        ks = [k for k in [1, 3, 5, 10, 20] if k <= K]
        accs = []
        for k in ks:
            c = 0
            for r in recs:
                sub = r["all_predictions"][:k]
                modal = Counter(sub).most_common(1)[0][0]
                if modal == r["correct"]:
                    c += 1
            a = 100 * c / len(recs); accs.append(a)
            rows.append({"model": model, "k": k, "majority_vote_acc": round(a, 2)})
        ax.plot(ks, accs, marker="o", label=model)
    if not rows:
        print("EXP5: no self-consistency results — skip"); return
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "exp5_self_consistency.csv"), index=False)
    ax.axhline(73.4, ls="--", color="gray", lw=1, label="best single greedy (73.4%)")
    ax.set_xlabel("k samples"); ax.set_ylabel("Majority-vote accuracy (%)")
    ax.set_title("Self-consistency scaling (t=0.7)"); ax.legend(fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig8_self_consistency.png"))
    print("EXP5: wrote exp5_self_consistency.csv + fig8_self_consistency.png")


if __name__ == "__main__":
    exp3(); exp4(); exp5()
    print("\nDone. (Blocks with no inputs were skipped.)")