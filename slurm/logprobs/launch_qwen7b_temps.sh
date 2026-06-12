#!/bin/bash
# Paper 1 EXP1 -- Qwen2.5-7B t=0.3 / t=0.7 in the LOGPROB env (temperature-curve consistency).
#
# The new canonical greedy for Qwen2.5-7B in the logprob env is 59.71% (vs 67.96% in the old
# base-run env). Its t=0.3/0.7 numbers still came from the OLD env, which would make the curve
# non-monotonic. This re-runs ONLY Qwen2.5-7B at t=0.3 and t=0.7, 3 runs each, in the logprob
# env, using run_qwen25_7b_logprobs_temp.sbatch (same model/vLLM/dtype/seed-handling).
#
# Submitted as ONE strict afterany dependency chain (one job at a time, each its own fresh vLLM
# launch + fresh random seed, to capture instability the way the base-run protocol does). Each
# job auto-commits+pushes its own result file; afterany means a failed run is skipped and the
# chain continues. Sequential => no concurrent git writes in the shared working tree.
#
# Usage:  bash slurm/logprobs/launch_qwen7b_temps.sh
# Run from the repo root: /aiau010_scratch/tzs0128/repo/MedQA2026

set -euo pipefail
cd /aiau010_scratch/tzs0128/repo/MedQA2026

SCRIPT="slurm/logprobs/run_qwen25_7b_logprobs_temp.sbatch"
DEP=""
LAST=""

submit() {  # $1 = TEMP, $2 = RUN_INDEX
    local temp="$1" run="$2" jid
    jid=$(sbatch --parsable $DEP --export="ALL,TEMP=${temp},RUN_INDEX=${run}" "$SCRIPT")
    echo "  submitted t=${temp} run${run} -> job $jid${LAST:+  (after $LAST)}"
    DEP="--dependency=afterany:${jid}"
    LAST="$jid"
}

echo "Submitting Qwen2.5-7B logprob-env temperature chain (t=0.3 then t=0.7, runs 1-3)..."
for TEMP in 0.3 0.7; do
    echo "--- TEMP=$TEMP ---"
    for RUN in 1 2 3; do
        submit "$TEMP" "$RUN"
    done
done

# Final catch-all flush (scoped; the per-job pushes usually already covered everything).
echo "--- final commit & push ---"
jid=$(sbatch --parsable $DEP slurm/commit_and_push.sbatch)
echo "  submitted commit_and_push -> job $jid  (after $LAST)"

echo
echo "Chain submitted. Current queue:"
squeue -u "$USER" -o "%.10i %.24j %.10T %.12R %.20E" || true
