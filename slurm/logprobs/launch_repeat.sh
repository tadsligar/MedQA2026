#!/bin/bash
# Paper 1 EXP1 -- logprobs repeat runs (run2 + run3) for cross-run determinism.
#
# Submits, as a single strict afterany dependency chain (one job at a time, each its own
# fresh vLLM launch):
#     run2 for all 5 models, then run3 for all 5 models, then a final commit/push.
# RUN_INDEX is injected per job via --export so the entrypoint writes temp0.0_run<N>_results.json.
# afterany means a failed/cancelled model is skipped and the chain continues to the next.
#
# Usage:  bash slurm/logprobs/launch_repeat.sh
# Run from the repo root: /aiau010_scratch/tzs0128/repo/MedQA2026

set -euo pipefail
cd /aiau010_scratch/tzs0128/repo/MedQA2026

MODELS=(qwen25_7b qwen25_14b qwen25_32b olmo3_7b olmo3_32b)
DEP=""          # grows into "--dependency=afterany:<jobid>" after the first submission
LAST=""

submit() {  # $1 = sbatch script, $2 = RUN_INDEX (optional)
    local script="$1" run="${2:-}"
    local export_arg="ALL"
    [ -n "$run" ] && export_arg="ALL,RUN_INDEX=${run}"
    local jid
    jid=$(sbatch --parsable $DEP --export="${export_arg}" "$script")
    echo "  submitted $(basename "$script") run=${run:-1} -> job $jid${DEP:+  (after $LAST)}"
    DEP="--dependency=afterany:${jid}"
    LAST="$jid"
}

echo "Submitting repeat-run chain (run2 then run3, all 5 models, then commit/push)..."
for RUN in 2 3; do
    echo "--- RUN_INDEX=$RUN ---"
    for m in "${MODELS[@]}"; do
        submit "slurm/logprobs/run_${m}_logprobs.sbatch" "$RUN"
    done
done

echo "--- final commit & push ---"
submit "slurm/commit_and_push.sbatch"

echo
echo "Chain submitted. Tail of the queue:"
squeue -u "$USER" -o "%.10i %.22j %.10T %.12R %E" | tail -n +1
