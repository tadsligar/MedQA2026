# EXP2 — Instruction-Tuned Comparison

**Priority: HIGH** (see `../ANALYSIS_GAPS.md` C-2).

## Why this matters
A reviewer will immediately ask how base models compare to their `-Instruct` siblings.
Adding instruct runs sharpens the paper's "base-model behavior" framing into a *controlled
contrast* (base vs instruct, same family/scale) and pre-empts "your base numbers don't
reflect deployed systems." It also tests whether instruction tuning fixes the
Clinical-Findings weakness and the temperature degradation seen in base models.

## Prompt to run it
> You are my AI/ML research engineer in the MedQA2026 repo. Add instruction-tuned
> counterparts of our five base models to the focused 1,030-question evaluation, matching
> the existing protocol so base-vs-instruct is a clean controlled comparison.

## Exact configuration
Models (instruct/chat versions): `Qwen/Qwen2.5-7B-Instruct`, `Qwen2.5-14B-Instruct`,
`Qwen2.5-32B-Instruct`, `allenai/OLMo-3-1025-7B-Instruct`, `OLMo-3-1125-32B-Instruct`
(use the exact instruct IDs available on HF; confirm names before launching).

- Clone each `configs/*_base.yaml` to `*_instruct.yaml`, set the instruct model ID and
  **`use_chat_api: true`** (chat template), keep `max_output_tokens: 800`, bf16, TP=2.
- Use a minimal chat prompt mirroring the base prompt content (question + options + "Answer
  with a single letter."). Document the exact template — it is a confound to control.
- Same grid: temps 0.0 / 0.3 / 0.7, 3 runs each. (If compute-limited, t=0.0 × 3 runs
  suffices for the headline base-vs-instruct table.)
- Same answer-extraction rule (first valid A–D letter).

## Expected outputs
`results/instruct_runs/<model>/temp{t}_run{r}_results.json`, identical schema to base runs,
so `compute_tables.py` / `compute_stats.py` can be pointed at it with a path change.

## Analysis plan
1. Base-vs-instruct accuracy delta per model and per category (paired McNemar at t=0.0).
2. Does instruction tuning reduce the **temperature degradation** (recompute Table 7)?
3. Does it reduce **answer instability** at t=0.7 (recompute Table 5)?
4. Does it shrink the **Clinical Findings** gap specifically?
5. Generation-length contrast — instruct models should stop cleanly (vs base hitting the
   800-token cap on ~75% of Qwen items); report cap-hit rate.

## Fills in DRAFT.md
`[TBD-EXP2: base-vs-instruct table]`, `[TBD-EXP2: instruct temp/stability deltas]`, a
Related-Work/Discussion paragraph, and a contribution bullet.

## Acceptance check
Instruct accuracies computed for all available models with McNemar p-values vs their base
counterpart; chat template documented verbatim in the appendix.

## Implementation (READY — code written)
- **Runner:** `scripts/instruct_runs/test_instruct_model.py` — vLLM **chat** endpoint with the
  model's chat template, minimal instruction (logged to `prompt_template.txt`), same
  first-valid-letter extraction and output schema as the base runs. Default grid 3 temps × 3
  runs; use `--temperatures "0.0" --n-runs 1` for a quick headline table.
- **AIAU SLURM:** `slurm/instruct/run_<model>_instruct.sbatch` (5 models).
  **Confirm the exact `-Instruct` HF IDs before launching** (esp. OLMo-3 instruct names).
- **Analysis (GPU-free):** `python papers/paper1/analysis/compute_instruct_comparison.py` →
  `tables/exp2_base_vs_instruct_overall.csv`, `_category.csv`, `exp2_temp_degradation.csv`,
  `exp2_token_contrast.csv` (incl. cap-hit and t=0.7 instability, base vs instruct).
