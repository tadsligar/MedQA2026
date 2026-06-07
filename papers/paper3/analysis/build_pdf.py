#!/usr/bin/env python3
"""Build print-ready markdown (figures embedded) from Paper 3 DRAFT.md and render to PDF."""
import os, subprocess

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # repo root from papers/<paper>/analysis/
P = os.path.join(_REPO, "papers", "paper3")
src = open(os.path.join(P, "DRAFT.md")).read()
lines = src.splitlines()
start = next(i for i, ln in enumerate(lines) if ln.startswith("## Title"))
src = "\n".join(lines[start:]) + "\n"

def figblock(path, caption):
    return f'\n\n![]({path}){{width=98%}}\n\n*{caption}*\n\n'

# Insert each figure immediately BEFORE a unique heading line.
inserts = [
    ("### 5.1 Belief-update formulations (EXP5)",
     figblock("figures/fig1_framework.png",
              "Figure 1. Agentic neuro-symbolic MedQA framework (modules A–J).")),
    ("### 6.1 Scoring formulation",
     figblock("figures/fig3_control_loop.png",
              "Figure 3. Agent control loop (Algorithm 1): estimate uncertainty, select an "
              "evidence function, execute, update belief, stop adaptively, verify, decide.")),
    ("## 9. Ablation Studies",
     figblock("figures/fig_seed_oracle_headroom.png",
              "Seed figure. Headroom for agentic selection: best single model vs majority-of-5 "
              "vs oracle (any-of-5 correct) at t=0.0. Oracle exceeds best single by ~10–15 pp; "
              "majority voting is below best single.")),
]
for heading, block in inserts:
    if heading in src:
        src = src.replace(heading, block + heading, 1)
    else:
        print("WARN heading not found:", heading)

header = """---
title: "From Answer Selection to Differential Reasoning: An Agentic Neuro-Symbolic Framework for Adaptive Evidence Acquisition in Medical Question Answering"
subtitle: "Working draft — Paper 3 (MedQA2026). [TBD-EXP#] items await agent experiments; static baselines & seed bounds are verified."
date: "June 2026"
geometry: "margin=1in"
fontsize: 11pt
linkcolor: black
urlcolor: black
mainfont: "DejaVu Serif"
monofont: "DejaVu Sans Mono"
header-includes:
  - \\usepackage{fancyhdr}
  - \\pagestyle{fancy}
  - \\fancyhead[L]{MedQA2026 — Paper 3 draft}
  - \\fancyhead[R]{\\thepage}
  - \\fancyfoot[C]{}
---

"""
open(os.path.join(P, "DRAFT_print.md"), "w").write(header + src)
cmd = ["pandoc", "DRAFT_print.md", "-o", "Paper3_Draft.pdf",
       "--pdf-engine=xelatex", "--toc", "--toc-depth=2", "-V", "colorlinks=false"]
r = subprocess.run(cmd, cwd=P, capture_output=True, text=True)
print("pandoc rc:", r.returncode)
if r.returncode != 0:
    print(r.stdout[-1500:]); print(r.stderr[-2500:])
else:
    print("PDF bytes:", os.path.getsize(os.path.join(P, "Paper3_Draft.pdf")))
