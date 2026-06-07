# Paper 1 EXP2 — instruction-tuned comparison (AIAU)

Runs the five `-Instruct` models on the focused 1,030-set via the vLLM chat endpoint, for a
controlled base-vs-instruct contrast. Base numbers come from `results/base_runs/` (verified).

## Before launching — confirm model IDs
The job files use these HF IDs; **verify they exist** (especially OLMo-3 instruct naming):
`Qwen/Qwen2.5-{7B,14B,32B}-Instruct`, `allenai/Olmo-3-1025-7B-Instruct`,
`allenai/Olmo-3-1125-32B-Instruct`. Edit the `vllm serve` and `--model-name` lines if names differ.

## What runs where
32B-Instruct needs `--gres=gpu:2` (cluster). 7B-Instruct fits a single 24 GB GPU; 14B needs
~28 GB bf16 (cluster or quantized).

## Submit (from repo root on AIAU)
```bash
cd /aiau010_scratch/tzs0128/projects/MedQA2026
for m in qwen25_7b qwen25_14b qwen25_32b olmo3_7b olmo3_32b; do
  sbatch slurm/instruct/run_${m}_instruct.sbatch
done
```
Each job serves the model (chat template), runs 3 temps × 3 runs by default, and writes
`results/instruct_runs/<model>_instruct/`. For a quick headline-only table, change the final
command to `--temperatures "0.0" --n-runs 1`.

## Then analyze (GPU-free)
```bash
python papers/paper1/analysis/compute_instruct_comparison.py
```
Outputs base-vs-instruct accuracy (overall + per category, McNemar), temperature-degradation
contrast, and a token/stability contrast (cap-hit rate, t=0.7 instability). Fills the
`[TBD-EXP2]` items in `papers/paper1/DRAFT.md` and the base-vs-instruct discussion.
