#!/bin/bash -l
#SBATCH --job-name=commit_qwen25_14b
#SBATCH --partition=general
#SBATCH --time=00:10:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --output=slurm/full_run/logs/commit_qwen25_14b_%j.out
#SBATCH --error=slurm/full_run/logs/commit_qwen25_14b_%j.err

echo "=========================================="
echo "Auto-commit for Qwen 2.5 14B"
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo "=========================================="
echo

cd /aiau010_scratch/tzs0128/projects/MedQA2026

# Check if all runs are complete
EXPECTED_FILES=18  # results + checkpoints
ACTUAL_FILES=$(find results/base_runs_full/qwen25_14b -name "temp*.json" -type f | wc -l)

echo "Checking completion status..."
echo "  Expected files: $EXPECTED_FILES"
echo "  Actual files:   $ACTUAL_FILES"

if [ "$ACTUAL_FILES" -lt "$EXPECTED_FILES" ]; then
    echo
    echo "⚠ WARNING: Not all runs complete yet. Skipping commit."
    echo "Expected at least $EXPECTED_FILES files, found $ACTUAL_FILES"
    exit 0
fi

echo
echo "All runs complete! Proceeding with commit..."
echo

# Generate summary file
echo "Generating summary..."
python3 << 'PYTHON_EOF'
import json
from pathlib import Path
from collections import defaultdict

output_dir = Path("results/base_runs_full/qwen25_14b")
temperatures = [0.0, 0.3, 0.7]
n_runs = 3

# Collect results for each temperature
temperature_results = []

for temp in temperatures:
    accuracies = []

    for run in range(1, n_runs + 1):
        results_file = output_dir / f"temp{temp}_run{run}_results.json"

        if results_file.exists():
            with open(results_file) as f:
                results = json.load(f)

            correct = sum(1 for r in results if r.get('is_correct', False))
            accuracy = (correct / len(results)) * 100
            accuracies.append(accuracy)
        else:
            print(f"Warning: Missing {results_file}")

    if len(accuracies) == n_runs:
        mean_acc = sum(accuracies) / len(accuracies)

        if len(accuracies) > 1:
            variance = sum((x - mean_acc) ** 2 for x in accuracies) / (len(accuracies) - 1)
            std_dev = variance ** 0.5
        else:
            std_dev = 0

        temp_result = {
            'temperature': temp,
            'mean_accuracy': mean_acc,
            'std_dev': std_dev
        }

        for i, acc in enumerate(accuracies, 1):
            temp_result[f'run{i}_accuracy'] = acc

        temperature_results.append(temp_result)
        print(f"Temperature {temp}: {mean_acc:.2f}% (±{std_dev:.2f}%)")

# Save summary
summary = {
    'dataset': "data/datasets/medqa_full_combined.json",
    'total_questions': 12723,
    'model': "Qwen/Qwen2.5-14B",
    'model_type': 'base',
    'run_type': 'full_dataset_run',
    'prompt_style': 'simple',
    'temperatures': list(temperatures),
    'n_runs_per_temperature': n_runs,
    'temperature_results': temperature_results
}

summary_file = output_dir / "summary.json"
with open(summary_file, 'w') as f:
    json.dump(summary, f, indent=2)

print(f"\nSummary saved to {summary_file}")
PYTHON_EOF

if [ $? -ne 0 ]; then
    echo "ERROR: Summary generation failed"
    exit 1
fi

echo
echo "Summary generated successfully!"
echo

# Git operations
echo "Staging results..."
git add results/base_runs_full/qwen25_14b/*.json

echo "Creating commit..."
git commit -m "$(cat <<'EOF'
Complete Qwen 2.5 14B full dataset experiments

- Dataset: 12723 questions (full MedQA US combined)
- Temperatures: 0.0, 0.3, 0.7
- Runs per temperature: 3
- Total experiments: 9
- Results include checkpoints and full response data

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"

COMMIT_STATUS=$?

if [ $COMMIT_STATUS -eq 0 ]; then
    echo
    echo "=========================================="
    echo "Commit successful!"
    echo "=========================================="
    git log -1 --oneline
    echo

    # Push to remote
    echo "Pushing to remote repository..."
    git push
    PUSH_STATUS=$?

    if [ $PUSH_STATUS -eq 0 ]; then
        echo "Push successful!"

        # Create completion marker
        touch slurm/full_run/state/qwen25_14b_committed.marker
    else
        echo "ERROR: Push failed with status: $PUSH_STATUS"
        exit $PUSH_STATUS
    fi
else
    echo
    echo "=========================================="
    echo "Commit failed with status: $COMMIT_STATUS"
    echo "=========================================="
    exit $COMMIT_STATUS
fi

echo
echo "Job completed at: $(date)"
echo "=========================================="

exit 0
