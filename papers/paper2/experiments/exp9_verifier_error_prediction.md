# EXP9 — Verifier Scores as Error Predictors

**Priority: HIGH** — likely the most novel quantitative result (BRIEF RQ7).

## Why
Tests whether grounding coverage and symbolic violation scores **predict when an LLM answer
is wrong** — i.e., whether symbolic signal is a useful uncertainty/error detector even when it
cannot pick the right answer. This connects to Paper 1's stability-as-confidence finding and
motivates abstention/verification in Paper 3.

## Prompt to run it
> You are my ML engineer. Using EXP2 grounding and EXP6 violation features, fit and evaluate a
> model that predicts whether the LLM-only answer is correct, on the focused 1,030-question set.

## Procedure
- Label: per question, is the LLM-only (Paper 1 baseline) answer correct?
- Features: grounding coverage, answer-choice grounding rate, symbolic support margin
  (top1−top2), violation counts (5 verifiers), semantic-type compatibility. Optionally add
  Paper 1's cross-run stability and (if EXP1-logprobs done) LLM confidence.
- Fit logistic regression with cross-validation; report coefficients (interpretability).

## Expected outputs
`results/ns/error_prediction/features.csv` + `metrics.json` (AUROC, AUPRC, calibration).

## Analysis plan
- AUROC/AUPRC for predicting correctness from symbolic features alone, and combined with
  LLM confidence/stability.
- Risk–coverage curve: accuracy when abstaining on high-violation / low-coverage items.
- Which features carry signal (coefficients with CIs); per-category AUROC.

## Acceptance check
AUROC with CI for symbolic-only and combined predictors; risk–coverage curve; coefficient
table.

## Fills
`[TBD-EXP9: error-prediction AUROC]` Figures 5 & 6; the RQ7 result; abstract clause.
