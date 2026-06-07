#!/usr/bin/env python3
"""Build a print-ready markdown (figures embedded) from DRAFT.md and render to PDF."""
import os, re, subprocess

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # repo root from papers/<paper>/analysis/
P = os.path.join(_REPO, "papers", "paper1")
src = open(os.path.join(P, "DRAFT.md")).read()

# Drop the leading H1 and the working-draft blockquote note, line by line,
# keeping everything from the first "## Title" section onward.
lines = src.splitlines()
start = next(i for i, ln in enumerate(lines) if ln.startswith("## Title"))
src = "\n".join(lines[start:]) + "\n"

def fig(path, caption):
    # Empty alt text => pandoc renders the image without its auto "Figure N:"
    # caption; we supply our own italic caption line below.
    return f'\n\n![]({path}){{width=92%}}\n\n*{caption}*\n\n'

# Insert figures after the paragraph that introduces them.
anchors = [
    ("essentially deterministic (run-to-run std ≤ 0.05 pp).",
     fig("figures/fig2_accuracy_by_model_temp.png",
         "Figure 2. Accuracy by model and decoding temperature (mean of 3 runs; error bars = run std).")),
    ("(Figure 6). This structure is invisible in the aggregate.",
     fig("figures/fig3_category_heatmap.png",
         "Figure 3. Per-category accuracy heatmap at t=0.0.")
     + fig("figures/fig6_category_accuracy_ci.png",
           "Figure 6. Per-category accuracy at t=0.0 with Wilson 95% CIs (n=206/category).")),
    ("more stable at equal temperature.",
     fig("figures/fig4_answer_instability.png",
         "Figure 4. Run-to-run answer instability vs decoding temperature.")),
    ("empirically ~0). [TBD-EXP6: distribution of error types over the hard core, with examples",
     fig("figures/fig5_error_by_category.png",
         "Figure 5. Error rate by reasoning category (t=0.0, run 1).")),
]
for anchor, block in anchors:
    if anchor in src:
        src = src.replace(anchor, anchor + block, 1)
    else:
        print("WARN anchor not found:", anchor[:40])

header = """---
title: "Beyond Aggregate Accuracy: A Category-Balanced Benchmark of Base Language Models on Medical Reasoning under Controlled Decoding Temperature"
subtitle: "Working draft — Paper 1 (MedQA2026). Bracketed [TBD-EXP#] items await new experiments."
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
  - \\fancyhead[L]{MedQA2026 — Paper 1 draft}
  - \\fancyhead[R]{\\thepage}
  - \\fancyfoot[C]{}
---

"""
out_md = os.path.join(P, "DRAFT_print.md")
open(out_md, "w").write(header + src)
print("wrote", out_md)

pdf = os.path.join(P, "Paper1_Draft.pdf")
cmd = ["pandoc", "DRAFT_print.md", "-o", "Paper1_Draft.pdf",
       "--pdf-engine=xelatex", "--toc", "--toc-depth=2",
       "-V", "colorlinks=false"]
r = subprocess.run(cmd, cwd=P, capture_output=True, text=True)
print("pandoc rc:", r.returncode)
if r.returncode != 0:
    print(r.stdout[-2000:]); print(r.stderr[-3000:])
else:
    print("PDF:", pdf, os.path.getsize(pdf), "bytes")
