# Paper 1 EXP3 / EXP4 / EXP5 — base-model variants (AIAU)

One runner (`scripts/base_runs/test_base_model_variants.py`) drives three experiments via the
vLLM completions endpoint. All use base models; 14B/32B need `--gres=gpu:2` (cluster).

| Job | Experiment | What it runs |
|---|---|---|
| `exp3_promptablation_qwen25_14b.sbatch` | EXP3 prompt ablation | Qwen2.5-14B, variants v0–v3, t=0.0 |
| `exp3_promptablation_olmo3_32b.sbatch`  | EXP3 prompt ablation | OLMo-3-32B, variants v0–v3, t=0.0 |
| `exp4_cotvsdirect_qwen25_14b.sbatch`    | EXP4 CoT vs direct | Qwen2.5-14B, direct & cot, t=0.0/0.7 |
| `exp5_selfconsistency_qwen25_14b.sbatch`| EXP5 self-consistency | Qwen2.5-14B, k=20 samples, t=0.7 |

Prompt variants (EXP3): `v0` = original base prompt; `v1` = letter-only instruction;
`v2` = "The best answer is option"; `v3` = one-line USMLE role. CoT (EXP4) raises max-tokens
to 1024 and extracts the FINAL letter (after "Answer:"). Self-consistency (EXP5) stores all
k predictions per question so k∈{1,3,5,10,20} curves are computed offline.

## Submit (from repo root on AIAU)
```bash
cd /aiau010_scratch/tzs0128/projects/MedQA2026
sbatch slurm/variants/exp3_promptablation_qwen25_14b.sbatch
sbatch slurm/variants/exp3_promptablation_olmo3_32b.sbatch
sbatch slurm/variants/exp4_cotvsdirect_qwen25_14b.sbatch
sbatch slurm/variants/exp5_selfconsistency_qwen25_14b.sbatch
```

## Then analyze (GPU-free)
```bash
python papers/paper1/analysis/compute_variants.py
```
Writes `tables/exp3_prompt_ablation.csv` (+ prints category-rank Spearman across variants),
`tables/exp4_cot_vs_direct.csv`, `tables/exp5_self_consistency.csv` and
`figures/fig8_self_consistency.png`. Each block self-skips if its inputs are absent, so you can
run the analysis after any single job finishes. Fills `[TBD-EXP3/4/5]` in `papers/paper1/DRAFT.md`.
