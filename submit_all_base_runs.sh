#!/bin/bash
#
# Submit all base model test jobs
# Run from project root: ./submit_all_base_runs.sh
#

echo "=========================================="
echo "Submitting Base Model Test Jobs"
echo "=========================================="
echo

# Array of models
models=(
    "qwen25_7b_base"
    "qwen25_14b_base"
    "qwen25_32b_base"
    "olmo3_7b_base"
    "olmo3_32b_base"
)

job_ids=()

# Submit each job
for model in "${models[@]}"; do
    echo "Submitting: ${model}"
    job_output=$(sbatch slurm/run_${model}.sbatch)
    job_id=$(echo $job_output | grep -oP '\d+')
    job_ids+=($job_id)
    echo "  Job ID: $job_id"
    echo
done

echo "=========================================="
echo "All jobs submitted!"
echo "=========================================="
echo
echo "Job IDs: ${job_ids[*]}"
echo
echo "Monitor status:"
echo "  squeue -u \$USER"
echo
echo "View logs:"
echo "  tail -f logs/qwen25_7b_base_*.out"
echo "  tail -f logs/qwen25_14b_base_*.out"
echo "  tail -f logs/qwen25_32b_base_*.out"
echo "  tail -f logs/olmo3_7b_base_*.out"
echo "  tail -f logs/olmo3_32b_base_*.out"
echo
echo "Compare results (after completion):"
echo "  python scripts/utils/compare_base_models.py results/base_runs/"
echo
