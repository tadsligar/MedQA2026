# EXP1 — Token Log-Probabilities for Calibration

**Priority: HIGHEST** (see `../ANALYSIS_GAPS.md` C-1).

## Why this matters
Paper 1's strongest behavioral result is that **cross-run answer stability predicts
correctness** (stable items +23 to +42 pp over unstable, t=0.7). Today that is a *proxy*
because the runs stored only the decoded letter. Capturing token log-probabilities turns it
into a real calibration result — confidence, Expected Calibration Error (ECE), reliability
diagrams — addressing the first objection a serious reviewer will raise. Lowest-effort,
highest-impact: no new architecture, just re-run inference with logprobs on.

## Prompt to run it
> You are my AI/ML research engineer in the MedQA2026 repo. Re-run the focused
> 1,030-question evaluation with token log-probabilities enabled so we can compute true
> calibration metrics, replacing the stability-based confidence proxy in Paper 1.

## Exact configuration
Re-run all 5 base models; **t=0.0 run 1 is strictly required** (greedy headline condition).
Optionally add t=0.3/0.7 run 1 for confidence-vs-temperature.

- Reuse `configs/*_base.yaml`, completions endpoint (`use_chat_api: false`),
  `max_output_tokens: 800`, bf16, TP=2, A100 80GB.
- Enable logprobs: completions request `logprobs: 20`, `echo: false`
  (vLLM `SamplingParams(logprobs=20)`).
- Capture the logprob of each option letter (A/B/C/D) at the first answer position. If the
  letter is the first generated token, record top-k at position 0; else locate the first
  A–D token. Store full top-k for offline recomputation.
- Keep the original base-run prompt template **unchanged** so accuracy stays comparable.

## Expected outputs
Augment the result schema with:
```
answer_logprob     # logprob of the predicted letter
option_logprobs    # {A,B,C,D} logprobs, renormalized over the 4 letters
confidence         # softmax over the 4 option logprobs, max value
margin             # top1 - top2 option probability
```
Save to `results/base_runs_logprobs/<model>/temp0.0_run1_results.json`.

## Analysis plan
1. Reliability diagram + ECE per model (10 confidence bins vs empirical accuracy).
2. Confidence histogram, correct vs wrong (separation = usable signal).
3. Confidence-vs-stability cross-check: correlate greedy `confidence` with the t=0.7
   stability label from `compute_stats.py`. Hypothesis: they agree → proxy validated.
4. Selective accuracy / risk–coverage curve (abstain below a confidence threshold).
5. Per-category calibration — over/under-confidence on hard Clinical Findings?

## Fills in DRAFT.md
`[TBD-EXP1: ECE per model]`, `[TBD-EXP1: reliability diagram]`,
`[TBD-EXP1: confidence–stability r]`, the §6 calibration paragraph, and an abstract clause.

## Acceptance check
ECE for all 5 models; reliability diagram renders; greedy-confidence vs t=0.7-stability
correlation with CI. Sanity: re-run t=0.0 accuracy must match verified numbers
(OLMo-3 7B 46.18 … Qwen2.5 32B 73.40) within rounding.

## Implementation (READY — code written)
- **Runner:** `scripts/base_runs/test_base_model_logprobs.py` — same prompt/decoding/extraction
  as the base runner, adds vLLM `logprobs:20`, records per-question `option_logprobs`,
  `option_probs` (softmax over A–D), `confidence`, `margin`, `answer_pos`. Defaults to t=0.0
  run 1; `--temperatures "0.0,0.3,0.7" --n-runs 1` extends it.
- **AIAU SLURM:** `slurm/logprobs/run_<model>_logprobs.sbatch` (all 5 models). Submit:
  `sbatch slurm/logprobs/run_qwen25_32b_logprobs.sbatch` (32B needs gpu:2 — cluster only).
- **Analysis (GPU-free, run after jobs finish):**
  `python papers/paper1/analysis/compute_calibration.py` → writes
  `tables/calib_{ece,reliability_bins,risk_coverage,category_ece,selfcheck}.csv` and
  `figures/fig7_reliability.png`. The self-check CSV compares re-run accuracy to the verified
  numbers (must match) and reports confidence-vs-t0.7-instability correlation.
