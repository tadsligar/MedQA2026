# Paper 1 EXP1 — logprobs / calibration runs (AIAU)

Re-runs the focused 1,030-question evaluation with token log-probabilities so we can compute
true calibration (ECE, reliability diagrams, risk-coverage) instead of the stability proxy.

## What runs where
- **32B models require the cluster** (`--gres=gpu:2`, bf16). 7B fits a single 24 GB GPU; 14B
  needs ~28 GB bf16 (cluster, or AWQ/GPTQ locally).
- The **analysis** (`papers/paper1/analysis/compute_calibration.py`) is GPU-free — run it
  anywhere after the jobs finish.

## Submit (from the repo root on AIAU)
Run from `/aiau010_scratch/tzs0128/repo/MedQA2026` (the up-to-date clone; the jobs `cd` here).
The jobs are submitted as a **SLURM dependency chain** so they run strictly one-after-another and
each one auto-commits + pushes its own results to `master` on success:
```bash
cd /aiau010_scratch/tzs0128/repo/MedQA2026
J=$(sbatch --parsable slurm/logprobs/run_qwen25_7b_logprobs.sbatch)
J=$(sbatch --parsable --dependency=afterany:$J slurm/logprobs/run_qwen25_14b_logprobs.sbatch)
J=$(sbatch --parsable --dependency=afterany:$J slurm/logprobs/run_qwen25_32b_logprobs.sbatch)
J=$(sbatch --parsable --dependency=afterany:$J slurm/logprobs/run_olmo3_7b_logprobs.sbatch)
J=$(sbatch --parsable --dependency=afterany:$J slurm/logprobs/run_olmo3_32b_logprobs.sbatch)
```
Each job: starts a vLLM server for its model, waits for `/health`, runs t=0.0 run 1 with
logprobs, writes `results/base_runs_logprobs/<model>/temp0.0_run1_results.json`, then stops the
server and (on exit 0) runs `git add results/... && git commit && git push origin master`.
`afterany` means a failed model is skipped (no commit) and the chain continues to the next.
Jobs checkpoint every 10 questions and resume if resubmitted.

To also capture confidence-vs-temperature, edit the job's final command to
`--temperatures "0.0,0.3,0.7" --n-runs 1`.

## Repeat runs (run2/run3) — cross-run determinism
At t=0.0 (greedy) the logprob runs should be bit-identical, but the Qwen2.5-7B run1 reproduced
only 59.7% vs its verified 67.96% (8.25 pp, 317 prediction disagreements). To test whether that
is reproducible or a one-off bad launch, the jobs accept a `RUN_INDEX` env var (default 1) and
pass it through as `--run-index $RUN_INDEX`, which writes exactly `temp0.0_run<N>_results.json`
(this arg takes precedence over `--n-runs`). Launch run2 + run3 for all 5 models as one
sequential `afterany` chain, each its own fresh vLLM launch, ending in a commit/push flush:
```bash
bash slurm/logprobs/launch_repeat.sh
```
Each run job still auto-commits its own results incrementally; `slurm/commit_and_push.sbatch`
is the final catch-all (scoped to `results/base_runs_logprobs`, never `git add -A`).

`compute_calibration.py` then auto-detects run1/run2/run3 and reports per-run accuracy, median
accuracy, accuracy spread (max−min), and a cross-run determinism check (% of questions where all
available runs predict the same letter — must be 100% at t=0.0). It uses the **median run** for
ECE/reliability, prints a **WARNING** for any model with <100% agreement or >1 pp spread, and
writes `calib_runs.csv` plus `calib_qwen7b_diagnosis.csv` (each Qwen-7B logprob run vs the
verified base run).

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
