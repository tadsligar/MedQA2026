#!/usr/bin/env python3
"""Build a print-ready markdown (figures embedded) from Paper 2 DRAFT.md and render to PDF."""
import os, subprocess

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # repo root from papers/<paper>/analysis/
P = os.path.join(_REPO, "papers", "paper2")
src = open(os.path.join(P, "DRAFT.md")).read()

# Drop leading H1 + working-draft blockquote; keep from "## Title" onward.
lines = src.splitlines()
start = next(i for i, ln in enumerate(lines) if ln.startswith("## Title"))
src = "\n".join(lines[start:]) + "\n"

def fig(path, caption):
    return f'\n\n![]({path}){{width=95%}}\n\n*{caption}*\n\n'

anchors = [
    ("**G. Output / evidence trace.** Final answer with supporting and contradictory concepts,\ngrounding coverage, verification flags, and a human-readable explanation trace.",
     fig("figures/fig1_pipeline.png",
         "Figure 1. Neuro-symbolic MedQA pipeline (modules A–G). Build steps map to EXP1–EXP10.")),
    ("difficulty is *uncorrelated* with groundable phrase count (r=−0.02).",
     fig("figures/fig_seed_phrase_vs_acc.png",
         "Seed figure. Groundable surface area (mean extractable clinical phrases) vs base-model "
         "accuracy by category. Difficulty is not explained by how much there is to ground.")),
]
for anchor, block in anchors:
    if anchor in src:
        src = src.replace(anchor, anchor + block, 1)
    else:
        print("WARN anchor not found:", anchor[:50])

header = """---
title: "Grounded but Brittle: UMLS-Based Verification and the Concept Mismatch Problem in Neuro-Symbolic Medical Question Answering"
subtitle: "Working draft — Paper 2 (MedQA2026). [TBD-EXP#] items await neuro-symbolic experiments; LLM-only baseline is verified."
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
  - \\fancyhead[L]{MedQA2026 — Paper 2 draft}
  - \\fancyhead[R]{\\thepage}
  - \\fancyfoot[C]{}
---

"""
open(os.path.join(P, "DRAFT_print.md"), "w").write(header + src)
cmd = ["pandoc", "DRAFT_print.md", "-o", "Paper2_Draft.pdf",
       "--pdf-engine=xelatex", "--toc", "--toc-depth=2", "-V", "colorlinks=false"]
r = subprocess.run(cmd, cwd=P, capture_output=True, text=True)
print("pandoc rc:", r.returncode)
if r.returncode != 0:
    print(r.stdout[-1500:]); print(r.stderr[-2500:])
else:
    print("PDF:", os.path.join(P, "Paper2_Draft.pdf"),
          os.path.getsize(os.path.join(P, "Paper2_Draft.pdf")), "bytes")
