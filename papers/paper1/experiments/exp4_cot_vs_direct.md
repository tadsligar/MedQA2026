# EXP4 — Chain-of-Thought vs Direct Decoding

**Priority: MEDIUM** (see `../ANALYSIS_GAPS.md` C-4).

## Why this matters
The brief positions later work around reasoning. A CoT-vs-direct contrast (accuracy,
instability, token cost) both strengthens Paper 1 and seeds the neuro-symbolic arc by
showing where free-form reasoning helps and where it adds cost without accuracy. Base
models already run long (Qwen hits the 800-token cap ~75% of the time at t=0.0), so the
token-cost angle is concrete here.

## Prompt to run it
> You are my AI/ML research engineer in the MedQA2026 repo. Compare direct answer decoding
> vs chain-of-thought prompting on the focused 1,030-question set for at least one model.

## Exact configuration
- Model(s): **Qwen2.5 14B** (strong, mid-scale); optionally OLMo-3 32B.
- Two conditions, t=0.0 and t=0.7 (×3 runs at t=0.7 for instability):
  Direct = current base prompt;
  CoT = append "Let's reason step by step, then give the final answer as a single letter."
- Raise `max_output_tokens` to 1024–1536 for CoT so reasoning is not truncated; record
  truncation rate.
- Extraction: parse the final letter after the reasoning (define and document the rule;
  validate no malformed outputs).

## Expected outputs
`results/cot_vs_direct/<model>/{direct,cot}_temp{t}_run{r}_results.json` plus a `tokens`
field for cost analysis.

## Analysis plan
1. Accuracy delta CoT − direct, overall and per category (paired McNemar).
2. Token cost: mean generated tokens and cap-hit rate, CoT vs direct.
3. Instability at t=0.7: does CoT increase or decrease run-to-run answer flips?
4. Category interaction: does CoT help Mechanism/Pathophysiology more than Clinical Findings?

## Fills in DRAFT.md
`[TBD-EXP4: CoT vs direct table]`, a §6 Analysis paragraph, and future-work bridge text.

## Acceptance check
CoT vs direct accuracy with McNemar p and token-cost comparison reported for ≥1 model;
extraction rule documented.

## Implementation (READY — code written)
- **Runner:** `scripts/base_runs/test_base_model_variants.py` (shared by EXP3/4/5):
  `--prompt-variant {v0..v3}`, `--mode {direct,cot}`, `--n-samples K`.
- **AIAU SLURM:** `slurm/variants/*.sbatch` (see `slurm/variants/README.md`).
- **Analysis (GPU-free):** `python papers/paper1/analysis/compute_variants.py` → writes the
  EXP3/4/5 tables + `figures/fig8_self_consistency.png`; self-skips missing inputs.
