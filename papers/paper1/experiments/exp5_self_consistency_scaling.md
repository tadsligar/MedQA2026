# EXP5 — Self-Consistency Scaling (k samples)

**Priority: MEDIUM** (see `../ANALYSIS_GAPS.md` C-5).

## Why this matters
With only 3 samples, majority vote already recovers ~3–4 pp at t=0.7 (but never beats
greedy). Sweeping k = 5/10/20 maps the self-consistency curve: where it saturates and
whether it can close the gap to greedy. Cheap, and directly motivates the verification /
aggregation methods in later papers.

## Prompt to run it
> You are my AI/ML research engineer in the MedQA2026 repo. Run a self-consistency scaling
> sweep on the focused 1,030-question set for one model at a fixed temperature.

## Exact configuration
- Model: **Qwen2.5 14B** (or 7B for cheapest). Temperature fixed at **0.7** (the
  interesting stochastic regime).
- Draw k = 20 independent samples per question (reuse the runner with 20 seeds, or vLLM
  `n=20`), then compute majority-vote accuracy for k ∈ {1,3,5,10,20} by subsampling.
- Record per-question vote distributions to enable confidence-by-agreement analysis.

## Expected outputs
`results/self_consistency/<model>/temp0.7_k20_results.json` storing all k predictions per
question.

## Analysis plan
1. Majority-vote accuracy vs k (with bootstrap CIs) — the self-consistency curve.
2. Compare asymptote to greedy t=0.0 accuracy: does SC close the gap?
3. Agreement fraction as confidence: accuracy when ≥80% of votes agree vs split votes
   (complements EXP1 calibration).
4. Per-category SC gain — does it help the hard categories most?

## Fills in DRAFT.md
`[TBD-EXP5: self-consistency curve → Figure]`, a §6 Analysis paragraph, future-work bridge.

## Acceptance check
Accuracy-vs-k curve with CIs; explicit statement of whether SC at k=20 reaches greedy
accuracy.

## Implementation (READY — code written)
- **Runner:** `scripts/base_runs/test_base_model_variants.py` (shared by EXP3/4/5):
  `--prompt-variant {v0..v3}`, `--mode {direct,cot}`, `--n-samples K`.
- **AIAU SLURM:** `slurm/variants/*.sbatch` (see `slurm/variants/README.md`).
- **Analysis (GPU-free):** `python papers/paper1/analysis/compute_variants.py` → writes the
  EXP3/4/5 tables + `figures/fig8_self_consistency.png`; self-skips missing inputs.
