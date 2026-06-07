# Paper 1 — Analysis Status & What Would Strengthen the Paper

This documents (A) what the existing data already supports, (B) gaps that need only
re-analysis of current files, and (C) gaps that require **new experiments**. Use this
to decide scope before drafting.

---

## A. Already done and verified (no further work needed)
- Overall, per-category, per-temperature accuracy with per-run detail.
- Run-to-run variance + answer instability; majority-vote accuracy.
- Wilson 95% CIs (overall + per category).
- Exact McNemar tests for model pairs; logistic-regression interaction test.
- Letter-bias control; stability-as-confidence; temperature rescue/loss.
- Cross-model error overlap and the 14% all-models-wrong hard core.
- Data-quality audit: 0 malformed outputs in 46,350 predictions.

**These cover RQs on scale, temperature, category structure, stability, and
"aggregate accuracy hides weaknesses."** This is enough for a credible empirical
benchmark paper (workshop / short-paper strength) **today**.

---

## B. Cheap additions from existing files (re-analysis only, ~hours)
1. **Per-category Wilson CIs on figures** — add error bars to the heatmap / category bars
   (CIs already computed in `stats_wilson_ci.csv`). Reviewers expect uncertainty on
   category numbers given n=206.
2. **Bootstrap CIs for paired *differences*** (model A − model B, and t=0.0 − t=0.7)
   to accompany McNemar — gives effect sizes, not just p-values.
3. **Holm/Bonferroni correction** note for the McNemar family (6 comparisons).
4. **Response-length / token analysis** — `tokens` and `latency` fields exist; check
   whether wrong answers correlate with truncation or runaway generation (the stored
   `response` text suggests base models sometimes continue past the answer).
5. **Qualitative error samples** — pull 2–3 example wrong responses per error-taxonomy
   category from the `response` field for the Error Analysis section (paper1.md §13).
6. **Full-set vs focused-set reconciliation table** — one table contrasting the
   12,723-question (5-option) `RESULTS_SUMMARY.md` numbers with the focused (4-option)
   numbers, so the two are not confused. The 7B→14B scaling story differs between them
   and that contrast is itself interesting.

## C. Gaps that need NEW experiments (the real "strengthen acceptance" list)
Ordered by impact-per-effort for a serious venue.

1. **Token log-probabilities for true calibration.** The single biggest gap. Current
   runs store only the decoded letter, so calibration is a stability *proxy*. Re-running
   with vLLM `logprobs` enabled lets you compute confidence, ECE, and reliability diagrams
   — turning "stability correlates with correctness" into a real calibration result.
   *Effort: re-run inference (config already exists); no new code architecture.*

2. **Instruction-tuned comparison.** A reviewer will immediately ask how base models
   compare to their `-Instruct` counterparts (Qwen2.5-*-Instruct, OLMo-3-Instruct).
   Adding even t=0.0 instruct runs sharpens the "base-model behavior" framing and is a
   natural controlled contrast. *Effort: 5 more models × 1–3 temps.*

3. **Prompt-format / robustness ablation.** Current results use one zero-shot prompt.
   Temperature and category conclusions are confounded with prompt choice. Add 2–3
   prompt variants (e.g., letter-only vs "answer:" vs minimal CoT) on a subset to show
   the findings are not prompt artifacts. *Effort: 1 model × few prompts × focused set.*

4. **Chain-of-thought vs direct decoding.** The brief positions later work around
   reasoning; a CoT-vs-direct contrast (accuracy, instability, token cost) on at least
   one model would (a) strengthen Paper 1 and (b) seed the neuro-symbolic arc.

5. **Self-consistency scaling.** You have 3 samples; majority-vote already gains ~4 pp at
   t=0.7. Running k=5/10/20 samples at a fixed temperature shows the self-consistency
   curve — strong, cheap, and directly motivates the verification papers.

6. **Human / clinician spot-check of the hard core.** A small expert review of the 144
   all-models-wrong items (are they genuinely hard, ambiguous, or mislabeled?) would
   greatly strengthen the dataset-quality and error-analysis sections. *Effort: manual,
   ~144 items; partially supported by `docs/medical_review/`.*

7. **Category-label validation / inter-annotator agreement.** The dataset summary notes
   an LLM-validated category assignment (54% agreement constraint on Treatment/Mgmt).
   Reporting agreement statistics or a human audit of category labels pre-empts the
   "your categories are arbitrary" critique central to the paper's thesis.

---

## Recommended scope decision
- **Minimum publishable (workshop/arXiv now):** current analysis + section B items 1–5.
  The statistics are already sound and the category/stability findings are novel enough.
- **Conference-grade:** add C-1 (logprobs/calibration) and C-2 (instruct comparison);
  these address the two most likely reviewer objections.
- **Journal extension:** add C-3 through C-7.

The only existing claim that required correction during this pass was the category ×
temperature *interaction* (descriptively suggestive, not statistically significant) —
now fixed in `RESULTS.md`. No other computed result needed revision.
