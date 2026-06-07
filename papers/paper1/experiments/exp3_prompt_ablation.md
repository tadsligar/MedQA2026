# EXP3 — Prompt-Format Robustness Ablation

**Priority: MEDIUM** (see `../ANALYSIS_GAPS.md` C-3).

## Why this matters
All headline numbers use one zero-shot prompt. Temperature and category conclusions are
therefore confounded with prompt choice. A small ablation showing the *ordering* of
findings (Clinical Findings hardest; temperature degrades accuracy) is stable across prompt
variants converts a vulnerability into a robustness claim.

## Prompt to run it
> You are my AI/ML research engineer in the MedQA2026 repo. Run a prompt-format ablation on
> the focused 1,030-question set to test whether Paper 1's findings are prompt artifacts.

## Exact configuration
- Pick 2 representative models (one per family, e.g. **Qwen2.5 14B** and **OLMo-3 32B**).
- 3 prompt variants beyond the original:
  V0 = original base prompt (baseline);
  V1 = letter-only instruction ("Answer with only the letter.");
  V2 = explicit "Answer:" cue appended;
  V3 = minimal one-line role ("The following is a USMLE question.").
- Conditions: t=0.0 (×1 run is enough; the question is *ordering stability*, not variance).
- Same extraction rule; record which variant changes the extracted answer.

## Expected outputs
`results/prompt_ablation/<model>/<variant>_temp0.0_results.json` (standard schema).

## Analysis plan
1. Overall + per-category accuracy by variant; report max swing.
2. **Rank stability**: does the category difficulty ordering (Clinical Findings last) hold
   across all variants? Spearman ρ of category ranks across variants.
3. Fraction of questions whose answer flips between variants (prompt sensitivity rate).

## Fills in DRAFT.md
`[TBD-EXP3: prompt-ablation table]`, a robustness sentence in §8 Limitations / §6 Analysis.

## Acceptance check
Category-rank Spearman ρ across variants reported; if ordering holds (ρ high), state the
findings are prompt-robust; if not, scope the claims accordingly.

## Implementation (READY — code written)
- **Runner:** `scripts/base_runs/test_base_model_variants.py` (shared by EXP3/4/5):
  `--prompt-variant {v0..v3}`, `--mode {direct,cot}`, `--n-samples K`.
- **AIAU SLURM:** `slurm/variants/*.sbatch` (see `slurm/variants/README.md`).
- **Analysis (GPU-free):** `python papers/paper1/analysis/compute_variants.py` → writes the
  EXP3/4/5 tables + `figures/fig8_self_consistency.png`; self-skips missing inputs.
