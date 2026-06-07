#!/usr/bin/env python3
"""Figure 6: per-category accuracy at t=0.0 with Wilson 95% CI error bars (n=206)."""
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # repo root from papers/<paper>/analysis/
REPO = _REPO
TBL = os.path.join(REPO, "papers", "paper1", "tables")
FIG = os.path.join(REPO, "papers", "paper1", "figures")

ci = pd.read_csv(os.path.join(TBL, "stats_wilson_ci.csv"))
CATEGORIES = ["Clinical Findings", "Diagnosis", "Mechanism/Pathophysiology",
              "Next Step/Workup", "Treatment/Management"]
CAT_SHORT = ["Clinical\nFindings", "Diagnosis", "Mechanism/\nPathophys.",
             "Next Step/\nWorkup", "Treatment/\nMgmt."]
MODEL_ORDER = ["OLMo-3 7B", "OLMo-3 32B", "Qwen2.5 7B", "Qwen2.5 14B", "Qwen2.5 32B"]

plt.rcParams.update({"font.size": 11, "figure.dpi": 150, "axes.grid": True, "grid.alpha": 0.3})
fig, ax = plt.subplots(figsize=(9, 5.5))
x = np.arange(len(CATEGORIES)); w = 0.16
for i, m in enumerate(MODEL_ORDER):
    sub = ci[(ci.model == m) & (ci.scope.isin(CATEGORIES))].set_index("scope")
    acc = [sub.loc[c, "acc"] for c in CATEGORIES]
    lo = [sub.loc[c, "acc"] - sub.loc[c, "ci_lo"] for c in CATEGORIES]
    hi = [sub.loc[c, "ci_hi"] - sub.loc[c, "acc"] for c in CATEGORIES]
    ax.bar(x + (i - 2) * w, acc, w, yerr=[lo, hi], capsize=2, label=m)
ax.axhline(25, ls="--", color="gray", lw=1, label="Random (25%)")
ax.set_xticks(x); ax.set_xticklabels(CAT_SHORT, fontsize=9)
ax.set_ylabel("Accuracy (%)")
ax.set_title("Per-Category Accuracy at t=0.0 with Wilson 95% CIs (n=206/category)")
ax.legend(fontsize=8, ncol=3)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig6_category_accuracy_ci.png"))
print("wrote fig6_category_accuracy_ci.png")
