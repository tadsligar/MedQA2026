#!/usr/bin/env python3
"""Generate publication figures for Paper 1 from the computed tables."""
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # repo root from papers/<paper>/analysis/
REPO = _REPO
TBL = os.path.join(REPO, "papers", "paper1", "tables")
FIG = os.path.join(REPO, "papers", "paper1", "figures")
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({"font.size": 11, "figure.dpi": 150,
                     "axes.grid": True, "grid.alpha": 0.3})

MODEL_ORDER = ["OLMo-3 7B", "OLMo-3 32B", "Qwen2.5 7B", "Qwen2.5 14B", "Qwen2.5 32B"]
CATEGORIES = ["Clinical Findings", "Diagnosis", "Mechanism/Pathophysiology",
              "Next Step/Workup", "Treatment/Management"]
CAT_SHORT = ["Clinical\nFindings", "Diagnosis", "Mechanism/\nPathophys.",
             "Next Step/\nWorkup", "Treatment/\nMgmt."]
TEMPS = [0.0, 0.3, 0.7]

overall = pd.read_csv(os.path.join(TBL, "table3_overall_accuracy.csv"))
cat = pd.read_csv(os.path.join(TBL, "table4_category_accuracy.csv"))
var = pd.read_csv(os.path.join(TBL, "table5_variability.csv"))
err = pd.read_csv(os.path.join(TBL, "table9_error_distribution.csv"))

# --- Figure 2: Accuracy by model scale and temperature -----------------------
fig, ax = plt.subplots(figsize=(8, 5))
colors = {0.0: "#1b9e77", 0.3: "#d95f02", 0.7: "#7570b3"}
x = np.arange(len(MODEL_ORDER))
w = 0.25
for i, t in enumerate(TEMPS):
    means = [overall[(overall.model == m) & (overall.temp == t)].mean_acc.values[0] for m in MODEL_ORDER]
    stds = [overall[(overall.model == m) & (overall.temp == t)].std_acc.values[0] for m in MODEL_ORDER]
    ax.bar(x + (i - 1) * w, means, w, yerr=stds, capsize=3,
           label=f"t={t}", color=colors[t])
ax.axhline(25, ls="--", color="gray", lw=1, label="Random (25%)")
ax.set_xticks(x)
ax.set_xticklabels(MODEL_ORDER, rotation=20, ha="right")
ax.set_ylabel("Accuracy (%)")
ax.set_title("Accuracy by Model and Decoding Temperature (focused 1,030, mean of 3 runs)")
ax.legend(ncol=2, fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig2_accuracy_by_model_temp.png"))
plt.close(fig)

# --- Figure 3: Category-level heatmap (at t=0.0) -----------------------------
sub = cat[cat.temp == 0.0].set_index("model")
mat = np.array([[sub.loc[m, c] for c in CATEGORIES] for m in MODEL_ORDER])
fig, ax = plt.subplots(figsize=(8, 5))
im = ax.imshow(mat, cmap="YlGnBu", aspect="auto", vmin=mat.min(), vmax=mat.max())
ax.set_xticks(range(len(CATEGORIES)))
ax.set_xticklabels(CAT_SHORT, fontsize=9)
ax.set_yticks(range(len(MODEL_ORDER)))
ax.set_yticklabels(MODEL_ORDER)
for i in range(len(MODEL_ORDER)):
    for j in range(len(CATEGORIES)):
        ax.text(j, i, f"{mat[i, j]:.1f}", ha="center", va="center",
                color="black" if mat[i, j] < (mat.min()+mat.max())/2 else "white", fontsize=9)
ax.set_title("Per-Category Accuracy (%) at t=0.0")
fig.colorbar(im, ax=ax, label="Accuracy (%)")
ax.grid(False)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig3_category_heatmap.png"))
plt.close(fig)

# --- Figure 4: Answer instability vs temperature -----------------------------
fig, ax = plt.subplots(figsize=(7.5, 5))
markers = {"OLMo-3 7B": "o", "OLMo-3 32B": "s", "Qwen2.5 7B": "^",
           "Qwen2.5 14B": "D", "Qwen2.5 32B": "v"}
for m in MODEL_ORDER:
    s = var[var.model == m].sort_values("temp")
    ax.plot(s.temp, s.answer_instability_pct, marker=markers[m], label=m)
ax.set_xlabel("Decoding temperature")
ax.set_ylabel("Answer instability (% of questions\nwith disagreement across 3 runs)")
ax.set_xticks(TEMPS)
ax.set_title("Run-to-Run Answer Instability vs Temperature")
ax.legend(fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig4_answer_instability.png"))
plt.close(fig)

# --- Figure 5: Error distribution by category (t=0.0) ------------------------
fig, ax = plt.subplots(figsize=(8.5, 5))
x = np.arange(len(CATEGORIES))
w = 0.16
for i, m in enumerate(MODEL_ORDER):
    rates = [err[(err.model == m) & (err.category == c)].category_error_rate_pct.values[0]
             for c in CATEGORIES]
    ax.bar(x + (i - 2) * w, rates, w, label=m)
ax.set_xticks(x)
ax.set_xticklabels(CAT_SHORT, fontsize=9)
ax.set_ylabel("Error rate within category (%)")
ax.set_title("Error Rate by Reasoning Category (t=0.0, run 1)")
ax.legend(fontsize=8, ncol=2)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig5_error_by_category.png"))
plt.close(fig)

print("Figures written to", FIG)
for f in sorted(os.listdir(FIG)):
    print("  ", f)
