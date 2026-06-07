#!/usr/bin/env python3
"""Figure 1: neuro-symbolic pipeline diagram for Paper 2."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # repo root from papers/<paper>/analysis/
FIG = os.path.join(_REPO, "papers", "paper2", "figures")
os.makedirs(FIG, exist_ok=True)

fig, ax = plt.subplots(figsize=(10, 6.2))
ax.set_xlim(0, 10); ax.set_ylim(0, 9); ax.axis("off")

def box(x, y, w, h, title, lines, fc):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.12",
                                fc=fc, ec="#333", lw=1.3))
    ax.text(x + w/2, y + h - 0.28, title, ha="center", va="top", fontsize=9.5, fontweight="bold")
    ax.text(x + w/2, y + h - 0.62, "\n".join(lines), ha="center", va="top", fontsize=7.6)

def arrow(x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14,
                                 lw=1.4, color="#444"))

NEU = "#cfe8f3"; SYM = "#fde9c8"; HYB = "#d9f0d3"; IO = "#eeeeee"

# Input
box(0.3, 7.4, 3.0, 1.3, "Input: MedQA question",
    ["stem + 4 options (A–D)", "category, metamap phrases"], IO)
# A Question parser
box(3.8, 7.4, 2.9, 1.3, "A. Question Parser",
    ["demographics, symptoms,", "signs, labs, meds, temporal"], NEU)
# B UMLS grounding
box(7.2, 7.4, 2.6, 1.3, "B. UMLS Grounding",
    ["mentions→CUIs, sem-types,", "aliases, negation (EXP2)"], SYM)

# C symbolic scoring
box(0.3, 5.0, 3.0, 1.5, "C. Symbolic Scoring",
    ["relation support per option", "sem-type compatibility", "penalize contradictions (EXP3)"], SYM)
# D LLM reasoning
box(3.8, 5.0, 2.9, 1.5, "D. LLM Reasoning",
    ["structured rationale +", "per-option support/", "contradiction list (EXP4)"], NEU)
# E Chain-of-Verification
box(7.2, 5.0, 2.6, 1.5, "E. Chain-of-Verification",
    ["5 verifiers: type, demo,", "coverage, polarity,", "contradiction (EXP6)"], SYM)

# F Hybrid decision
box(2.4, 2.4, 5.2, 1.5, "F. Hybrid Decision Module (EXP7)",
    ["fuse LLM likelihood + symbolic support + violation penalties",
     "→ final answer, confidence proxy, gated revision"], HYB)

# G Output
box(2.4, 0.2, 5.2, 1.5, "G. Output / Evidence Trace",
    ["final answer · supporting & contradictory concepts",
     "grounding coverage · verification flags · explanation"], IO)

# arrows
arrow(3.3, 8.05, 3.8, 8.05)
arrow(6.7, 8.05, 7.2, 8.05)
arrow(8.5, 7.4, 8.5, 6.5)      # B -> E
arrow(5.25, 7.4, 5.25, 6.5)    # A -> D
arrow(1.8, 7.4, 1.8, 6.5)      # input col -> C (grounding feeds C)
arrow(1.8, 5.0, 3.2, 3.9)      # C -> F
arrow(5.25, 5.0, 5.0, 3.9)     # D -> F
arrow(8.5, 5.0, 6.8, 3.9)      # E -> F
arrow(5.0, 2.4, 5.0, 1.7)      # F -> G

# legend
ax.add_patch(FancyBboxPatch((0.3, 0.2), 0.3, 0.2, boxstyle="round", fc=NEU, ec="#333"))
ax.text(0.7, 0.3, "neural", fontsize=7.5, va="center")
ax.add_patch(FancyBboxPatch((0.3, -0.15), 0.3, 0.2, boxstyle="round", fc=SYM, ec="#333"))
ax.text(0.7, -0.05, "symbolic", fontsize=7.5, va="center")
ax.add_patch(FancyBboxPatch((1.55, -0.15), 0.3, 0.2, boxstyle="round", fc=HYB, ec="#333"))
ax.text(1.95, -0.05, "hybrid", fontsize=7.5, va="center")

ax.set_title("Figure 1. Neuro-symbolic MedQA pipeline (modules A–G; EXP refs = build steps)",
             fontsize=10.5)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig1_pipeline.png"), dpi=150, bbox_inches="tight")
print("wrote fig1_pipeline.png")
