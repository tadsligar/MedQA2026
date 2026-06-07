#!/usr/bin/env python3
"""Paper 3 Figures 1 (framework) and 3 (agent control loop)."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # repo root from papers/<paper>/analysis/
FIG = os.path.join(_REPO, "papers", "paper3", "figures")
os.makedirs(FIG, exist_ok=True)
NEU = "#cfe8f3"; SYM = "#fde9c8"; HYB = "#d9f0d3"; IO = "#eeeeee"; CTRL = "#f7d4e0"


def box(ax, x, y, w, h, title, lines, fc, ts=9.2, ls=7.4):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.10",
                                fc=fc, ec="#333", lw=1.2))
    ax.text(x+w/2, y+h-0.26, title, ha="center", va="top", fontsize=ts, fontweight="bold")
    if lines:
        ax.text(x+w/2, y+h-0.56, "\n".join(lines), ha="center", va="top", fontsize=ls)


def arrow(ax, x1, y1, x2, y2, style="-|>"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=13,
                                 lw=1.3, color="#444"))


# ---------------- Figure 1: framework (modules A–J) ----------------
fig, ax = plt.subplots(figsize=(11, 6.6)); ax.set_xlim(0, 11); ax.set_ylim(0, 10); ax.axis("off")
box(ax, 0.3, 8.4, 2.3, 1.3, "A. Case Parser", ["vignette → age, sx,", "signs, labs, neg."], NEU)
box(ax, 2.9, 8.4, 2.3, 1.3, "B. Category Classifier", ["one of 5 reasoning", "categories"], NEU)
box(ax, 5.5, 8.4, 2.3, 1.3, "C. Candidate Generator", ["options → typed", "hypotheses"], NEU)
box(ax, 8.1, 8.4, 2.6, 1.3, "D. UMLS Grounding", ["CUIs, sem-types,", "relations (Paper 2)"], SYM)

box(ax, 0.3, 5.8, 3.1, 1.6, "E. Evidence-Function Library",
    ["16 callable checks: demo, sx, lab,", "temporal, pathophys, dx–finding,", "tx-indication/contra, contradictions…"], SYM, ls=7.0)
box(ax, 3.7, 5.8, 3.4, 1.6, "F. Agent Controller / Planner",
    ["belief over candidates;", "select next function by", "uncertainty × utility − redundancy"], CTRL, ls=7.2)
box(ax, 7.4, 5.8, 3.3, 1.6, "G. Belief-State Update",
    ["score = LLM + α·support", "− β·contradiction", "+ γ·grounding_conf"], HYB, ls=7.2)

box(ax, 1.6, 3.4, 3.4, 1.4, "H. Redundancy-Aware Selection",
    ["mRMR-style: distinguish", "top candidates, avoid", "redundant evidence"], SYM, ls=7.2)
box(ax, 5.4, 3.4, 3.6, 1.4, "I. Verification / Contradiction Auditor",
    ["5 verifiers → flags;", "gated revision"], SYM, ls=7.4)

box(ax, 3.0, 1.0, 5.0, 1.4, "J. Final Decision + Evidence Trace",
    ["answer · ranked candidates · confidence proxy",
     "support/contradiction table · explanation trace"], IO, ls=7.4)

for x1,y1,x2,y2 in [(2.6,9.05,2.9,9.05),(5.2,9.05,5.5,9.05),(7.8,9.05,8.1,9.05)]:
    arrow(ax,x1,y1,x2,y2)
arrow(ax, 9.4, 8.4, 9.0, 7.4)     # D->G
arrow(ax, 1.8, 8.4, 1.8, 7.4)     # A->E
arrow(ax, 5.4, 5.8, 5.4, 4.9)     # F<->? down
arrow(ax, 3.4, 6.6, 3.7, 6.6)     # E->F
arrow(ax, 7.1, 6.6, 7.4, 6.6)     # F->G
arrow(ax, 9.0, 5.8, 7.2, 4.8)     # G->I
arrow(ax, 3.3, 5.8, 3.3, 4.8)     # E/F -> H
arrow(ax, 5.0, 3.4, 5.4, 2.4)     # H->J
arrow(ax, 7.0, 3.4, 6.5, 2.4)     # I->J
# feedback loop F<-belief
ax.add_patch(FancyArrowPatch((3.7,6.0),(3.4,4.8),connectionstyle="arc3,rad=0.3",
             arrowstyle="-|>",mutation_scale=12,lw=1.1,color="#999",ls="--"))
ax.text(0.3,0.25,"neural",fontsize=7.5); ax.add_patch(FancyBboxPatch((0.0,0.2),0.25,0.18,boxstyle="round",fc=NEU,ec="#333"))
ax.text(1.4,0.25,"symbolic",fontsize=7.5); ax.add_patch(FancyBboxPatch((1.1,0.2),0.25,0.18,boxstyle="round",fc=SYM,ec="#333"))
ax.text(2.7,0.25,"control",fontsize=7.5); ax.add_patch(FancyBboxPatch((2.4,0.2),0.25,0.18,boxstyle="round",fc=CTRL,ec="#333"))
ax.set_title("Figure 1. Agentic neuro-symbolic MedQA framework (modules A–J)", fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig1_framework.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

# ---------------- Figure 3: agent control loop ----------------
fig, ax = plt.subplots(figsize=(7.2, 7.6)); ax.set_xlim(0, 7.2); ax.set_ylim(0, 11); ax.axis("off")
box(ax, 1.6, 9.6, 4.0, 1.0, "Initialize belief over candidates", [], HYB, ts=10)
box(ax, 1.6, 8.0, 4.0, 1.0, "Estimate uncertainty (margin / entropy)", [], CTRL, ts=9.4)
box(ax, 1.6, 6.4, 4.0, 1.0, "Select evidence function (policy A–G)", [], CTRL, ts=9.4)
box(ax, 1.6, 4.8, 4.0, 1.0, "Execute function → support/contradiction", [], SYM, ts=9.0)
box(ax, 1.6, 3.2, 4.0, 1.0, "Update belief; append to evidence trace", [], HYB, ts=9.2)
box(ax, 0.3, 1.4, 2.7, 1.1, "Stop?\n(margin / budget)", [], IO, ts=9.0)
box(ax, 3.6, 1.4, 3.2, 1.1, "Verify + decide\n→ answer, trace", [], IO, ts=9.0)
for y in [9.6, 8.0, 6.4, 4.8]:
    arrow(ax, 3.6, y, 3.6, y-0.6)
arrow(ax, 3.6, 3.2, 1.65, 2.5)        # to Stop?
# loop back if not stop
ax.add_patch(FancyArrowPatch((0.4,2.0),(0.4,8.5),connectionstyle="arc3,rad=-0.35",
             arrowstyle="-|>",mutation_scale=12,lw=1.2,color="#999"))
ax.text(0.05,5.2,"no (loop t←t+1)",fontsize=7.5,rotation=90,color="#777",va="center")
arrow(ax, 3.0, 1.95, 3.6, 1.95)       # Stop yes -> verify
ax.text(3.05,2.15,"yes",fontsize=7.5,color="#777")
ax.set_title("Figure 3. Agent control loop (Algorithm 1)", fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig3_control_loop.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("wrote fig1_framework.png, fig3_control_loop.png")
