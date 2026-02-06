#!/usr/bin/env python3
"""
Generate auto-commit scripts for each model.
These run when all experiments for a model complete.
"""

import json
from pathlib import Path

def generate_auto_commit(model_key, model_config, config):
    """Generate auto-commit script for a model."""

    script = f"""#!/bin/bash -l
#SBATCH --job-name=commit_{model_key}
#SBATCH --partition=general
#SBATCH --time=00:10:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --output=slurm/full_run/logs/commit_{model_key}_%j.out
#SBATCH --error=slurm/full_run/logs/commit_{model_key}_%j.err

echo "=========================================="
echo "Auto-commit for {model_config['display_name']}"
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo "=========================================="
echo

cd /aiau010_scratch/tzs0128/projects/MedQA2026

# Check if all runs are complete
EXPECTED_FILES={config['n_runs_per_temperature'] * len(config['temperatures']) * 2}  # results + checkpoints
ACTUAL_FILES=$(find {model_config['output_dir']} -name "temp*.json" -type f | wc -l)

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

output_dir = Path("{model_config['output_dir']}")
temperatures = {config['temperatures']}
n_runs = {config['n_runs_per_temperature']}

# Collect results for each temperature
temperature_results = []

for temp in temperatures:
    accuracies = []

    for run in range(1, n_runs + 1):
        results_file = output_dir / f"temp{{temp}}_run{{run}}_results.json"

        if results_file.exists():
            with open(results_file) as f:
                results = json.load(f)

            correct = sum(1 for r in results if r.get('is_correct', False))
            accuracy = (correct / len(results)) * 100
            accuracies.append(accuracy)
        else:
            print(f"Warning: Missing {{results_file}}")

    if len(accuracies) == n_runs:
        mean_acc = sum(accuracies) / len(accuracies)

        if len(accuracies) > 1:
            variance = sum((x - mean_acc) ** 2 for x in accuracies) / (len(accuracies) - 1)
            std_dev = variance ** 0.5
        else:
            std_dev = 0

        temp_result = {{
            'temperature': temp,
            'mean_accuracy': mean_acc,
            'std_dev': std_dev
        }}

        for i, acc in enumerate(accuracies, 1):
            temp_result[f'run{{i}}_accuracy'] = acc

        temperature_results.append(temp_result)
        print(f"Temperature {{temp}}: {{mean_acc:.2f}}% (±{{std_dev:.2f}}%)")

# Save summary
summary = {{
    'dataset': "{config['dataset']}",
    'total_questions': {config['total_questions']},
    'model': "{model_config['model_name']}",
    'model_type': 'base',
    'run_type': 'full_dataset_run',
    'prompt_style': 'simple',
    'temperatures': list(temperatures),
    'n_runs_per_temperature': n_runs,
    'temperature_results': temperature_results
}}

summary_file = output_dir / "summary.json"
with open(summary_file, 'w') as f:
    json.dump(summary, f, indent=2)

print(f"\\nSummary saved to {{summary_file}}")
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
git add {model_config['output_dir']}/*.json

echo "Creating commit..."
git commit -m "$(cat <<'EOF'
Complete {model_config['display_name']} full dataset experiments

- Dataset: {config['total_questions']} questions (full MedQA US combined)
- Temperatures: {', '.join(map(str, config['temperatures']))}
- Runs per temperature: {config['n_runs_per_temperature']}
- Total experiments: {len(config['temperatures']) * config['n_runs_per_temperature']}
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
        touch slurm/full_run/state/{model_key}_committed.marker
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
"""

    return script


def main():
    # Load configuration
    config_path = Path("slurm/full_run/model_configs.json")
    with open(config_path) as f:
        config = json.load(f)

    # Generate auto-commit scripts
    for model_key, model_config in config['models'].items():
        script_path = Path(f"slurm/full_run/auto_commit_{model_key}.sbatch")

        script = generate_auto_commit(model_key, model_config, config)

        with open(script_path, 'w') as f:
            f.write(script)

        script_path.chmod(0o755)

        print(f"Created: {script_path.name}")

    print(f"\nGenerated {len(config['models'])} auto-commit scripts")


if __name__ == "__main__":
    main()
