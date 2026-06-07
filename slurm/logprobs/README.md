# Paper 1 EXP1 — logprobs / calibration runs (AIAU)

Re-runs the focused 1,030-question evaluation with token log-probabilities so we can compute
true calibration (ECE, reliability diagrams, risk-coverage) instead of the stability proxy.

## What runs where
- **32B models require the cluster** (`--gres=gpu:2`, bf16). 7B fits a single 24 GB GPU; 14B
  needs ~28 GB bf16 (cluster, or AWQ/GPTQ locally).
- The **analysis** (`papers/paper1/analysis/compute_calibration.py`) is GPU-free — run it
  anywhere after the jobs finish.

## Submit (from the repo root on AIAU)
```bash
cd /aiau010_scratch/tzs0128/projects/MedQA2026
sbatch slurm/logprobs/run_qwen25_7b_logprobs.sbatch
sbatch slurm/logprobs/run_qwen25_14b_logprobs.sbatch
sbatch slurm/logprobs/run_qwen25_32b_logprobs.sbatch
sbatch slurm/logprobs/run_olmo3_7b_logprobs.sbatch
sbatch slurm/logprobs/run_olmo3_32b_logprobs.sbatch
```
Each job: starts a vLLM server for its model, waits for `/health`, runs t=0.0 run 1 with
logprobs, writes `results/base_runs_logprobs/<model>/temp0.0_run1_results.json`, then stops the
server. Jobs checkpoint every 10 questions and resume if resubmitted.

To also capture confidence-vs-temperature, edit the job's final command to
`--temperatures "0.0,0.3,0.7" --n-runs 1`.

## Then analyze (local or cluster)
```bash
python papers/paper1/analysis/compute_calibration.py
```
Outputs `tables/calib_*.csv` and `figures/fig7_reliability.png`. **Check `calib_selfcheck.csv`:**
`rerun_acc` must match the verified t=0.0 numbers (OLMo-3 7B 46.18 … Qwen2.5 32B 73.40); a large
`abs_diff` means decoding/prompt diverged. The `corr_conf_vs_t07_instability` column validates
that greedy confidence agrees with Paper 1's stability signal.

## Fills in the paper
`[TBD-EXP1: ECE per model]`, `[TBD-EXP1: reliability diagram]` (Figure 7),
`[TBD-EXP1: confidence–stability correlation]`, and the §6 calibration paragraph + abstract clause.
