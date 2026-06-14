# Paper 4 — operation-label validation (gpt-5.4-mini vs Claude gold)

**Gold sample:** 100 questions, stratified 20/operation over the gpt-5.4-mini labels (oversamples
rare R/W). Hand-labeled independently by Claude (`results/reasoning_ops/gold_op_labels.jsonl`),
scored against the gpt-5.4-mini labels.

## Result
- Agreement: **70/100 (70%)**, Cohen's **κ = 0.625** (substantial, Landis-Koch).
- Reliable cells: **Interventional 17/20**, **Workup 19/21** — "is this a treatment decision /
  a test-selection" is labeled consistently.
- Unreliable cluster: **Recognition / Mechanistic / Diagnostic (R/F/B)** account for nearly all
  disagreement. My R was read as B (6) or F (6); my F as B (6); my B as R (4).

## Why this matters for the headline
The **forward(F)-vs-backward(B) contrast — the central hypothesis — lies on the least separable
boundary.** When two careful annotators can't reliably distinguish "mechanism" from "diagnosis"
on these items, a true accuracy asymmetry would be smeared out by misclassification. So the flat
full-set F−B result (gap ≈ +0.46 pp, n.s.) is **confounded with labeling resolution**: it is NOT
evidence that no asymmetry exists — only that none is detectable at this label quality.

## Coverage gap
Biostatistics items (RR/PPV/risk-difference) and ethics/communication items do not fit the five
operations; both annotators dumped biostats → W and ethics → I as catch-alls (~10% of MedQA).

## Implications / next steps
1. The deduction/abduction (F/B) distinction is not cleanly operationalizable on MedQA MCQs as
   defined. This is itself a reportable methodological finding (and consistent with the MCQ
   recall-confound: if models pattern-match both, no behavioral gap is expected).
2. Concrete salvage test (uses the cluster second annotator): once the Qwen2.5 labels land,
   compute gpt-vs-Qwen agreement on the full set, then **re-test the asymmetry on the
   high-confidence subset where both annotators agree on F vs B.** If still null on clean items,
   that is a strong claim; if an asymmetry emerges, it was masked by noise.
3. I and W are reliable enough to use as-is; the R/F/B trio needs a sharper rubric (or merging
   R into B/F) before any cross-operation claim.
