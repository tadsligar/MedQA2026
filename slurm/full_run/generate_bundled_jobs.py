#!/usr/bin/env python3
"""
Generate bundled job scripts - one per model, runs all temperatures sequentially.
Optimizes resource usage by loading model once.
"""
import json
from pathlib import Path

def generate_bundled_job(model_key, model_config, config):
    """Generate a single job script that runs all temperatures for a model."""

    script = f"""#!/bin/bash -l
#SBATCH --job-name={model_key}_full
#SBATCH --partition={config['slurm']['partition']}
#SBATCH --time={config['slurm']['time_limit']}
#SBATCH --gres=gpu:{model_config['gpus']}
#SBATCH --cpus-per-task={config['slurm']['cpus_per_task']}
#SBATCH --mem={config['slurm']['mem']}
#SBATCH --output=slurm/full_run/logs/{model_key}_full_%j.out
#SBATCH --error=slurm/full_run/logs/{model_key}_full_%j.err

echo "=========================================="
echo "Full Dataset Test - {model_config['display_name']}"
echo "All Temperatures (Bundled Job)"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Partition: $SLURM_JOB_PARTITION"
echo "GPUs: $CUDA_VISIBLE_DEVICES"
echo "Start time: $(date)"
echo "=========================================="
echo

cd /aiau010_scratch/tzs0128/projects/MedQA2026

# Activate conda environment
source ~/.bashrc
conda activate medqa

# Set cache directory
export HF_HOME=/aiau010_scratch/tzs0128/hf_cache
export TRANSFORMERS_CACHE=/aiau010_scratch/tzs0128/hf_cache

# GPU check
echo "Checking GPU availability..."
python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('GPU count:', torch.cuda.device_count())"
echo

echo "GPU Status before start:"
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv
echo

# Use unique port based on job ID
VLLM_PORT=$((8000 + ($SLURM_JOB_ID % 1000)))
echo "Using vLLM port: $VLLM_PORT"
echo

# Start vLLM server
echo "=========================================="
echo "Starting vLLM server for {model_config['display_name']}..."
echo "Model will stay loaded for all temperature experiments"
echo "=========================================="
echo

RANDOM_SEED=$(($(date +%s%N) % 2147483647))
echo "Random seed: $RANDOM_SEED"
echo

vllm serve {model_config['model_name']} \\
    --port $VLLM_PORT \\
    --tensor-parallel-size {model_config['tensor_parallel_size']} \\
    --gpu-memory-utilization {model_config['gpu_memory_utilization']} \\
    --dtype bfloat16 \\
    --max-model-len {model_config['max_model_len']} \\
    --disable-log-requests \\
    --seed $RANDOM_SEED"""

    if model_config.get('max_num_seqs'):
        script += f" \\\n    --max-num-seqs {model_config['max_num_seqs']}"

    script += f""" \\
    > slurm/full_run/logs/vllm_{model_key}_${{SLURM_JOB_ID}}.log 2>&1 &

VLLM_PID=$!
echo "vLLM server started with PID: $VLLM_PID"
echo

# Wait for vLLM to be ready
echo "Waiting for vLLM server to be ready..."
MAX_WAIT={model_config['startup_wait']}
ELAPSED=0
while ! curl -s http://localhost:$VLLM_PORT/health > /dev/null 2>&1; do
    if [ $ELAPSED -ge $MAX_WAIT ]; then
        echo "ERROR: vLLM server did not start within ${{MAX_WAIT}}s"
        kill $VLLM_PID 2>/dev/null
        exit 1
    fi
    sleep 10
    ELAPSED=$((ELAPSED + 10))
    if [ $((ELAPSED % 60)) -eq 0 ]; then
        echo "  Still waiting... (${{ELAPSED}}s / $((ELAPSED / 60)) min)"
    fi
done
echo "vLLM server ready!"
echo

echo "GPU Status after model loaded:"
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv
echo

# Run all temperatures sequentially
OVERALL_SUCCESS=0
TEMPS=({' '.join(map(str, config['temperatures']))})

for TEMP in "${{TEMPS[@]}}"; do
    echo
    echo "========================================================================"
    echo "Running Temperature: $TEMP"
    echo "Model: {model_config['display_name']}"
    echo "Dataset: {config['total_questions']} questions"
    echo "Started: $(date)"
    echo "========================================================================"
    echo

    python scripts/base_runs/test_base_model_single.py \\
        --model-name "{model_config['model_name']}" \\
        --output-dir "{model_config['output_dir']}" \\
        --dataset "{config['dataset']}" \\
        --vllm-url "http://localhost:$VLLM_PORT" \\
        --temperature $TEMP \\
        --run-number 1

    TEST_EXIT_CODE=$?

    if [ $TEST_EXIT_CODE -eq 0 ]; then
        echo
        echo "✓ Temperature $TEMP completed successfully!"
        echo "  Completed at: $(date)"
    else
        echo
        echo "✗ Temperature $TEMP failed with exit code: $TEST_EXIT_CODE"
        echo "  Note: Checkpoint saved, can resume if needed"
        OVERALL_SUCCESS=1
    fi
done

# Cleanup: Kill vLLM server
echo
echo "=========================================="
echo "Shutting down vLLM server..."
kill $VLLM_PID 2>/dev/null
wait $VLLM_PID 2>/dev/null
echo "vLLM server stopped"
echo "=========================================="
echo

# Generate summary if all experiments succeeded
if [ $OVERALL_SUCCESS -eq 0 ]; then
    echo
    echo "All temperatures completed successfully!"
    echo "Generating summary..."

    python3 << 'PYTHON_EOF'
import json
from pathlib import Path

output_dir = Path("{model_config['output_dir']}")
temperatures = {config['temperatures']}

temperature_results = []

for temp in temperatures:
    results_file = output_dir / f"temp{{temp}}_run1_results.json"

    if results_file.exists():
        with open(results_file) as f:
            results = json.load(f)

        correct = sum(1 for r in results if r.get('is_correct', False))
        accuracy = (correct / len(results)) * 100

        temperature_results.append({{
            'temperature': temp,
            'run1_accuracy': accuracy,
            'mean_accuracy': accuracy,
            'std_dev': 0.0
        }})

        print(f"Temperature {{temp}}: {{accuracy:.2f}}%")

summary = {{
    'dataset': "{config['dataset']}",
    'total_questions': {config['total_questions']},
    'model': "{model_config['model_name']}",
    'model_type': 'base',
    'run_type': 'full_dataset_run',
    'prompt_style': 'simple',
    'temperatures': list(temperatures),
    'n_runs_per_temperature': 1,
    'temperature_results': temperature_results
}}

summary_file = output_dir / "summary.json"
with open(summary_file, 'w') as f:
    json.dump(summary, f, indent=2)

print(f"\\nSummary saved to {{summary_file}}")
PYTHON_EOF

    echo
    echo "Creating completion marker..."
    touch slurm/full_run/state/{model_key}_full.completed

    echo
    echo "Triggering auto-commit..."
    sbatch slurm/full_run/auto_commit_{model_key}.sbatch
else
    echo
    echo "Some experiments failed. Check logs for details."
    echo "Checkpoints saved - can resume failed experiments."
    echo "$OVERALL_SUCCESS" > slurm/full_run/state/{model_key}_full.failed
fi

echo
echo "=========================================="
echo "Job completed at: $(date)"
echo "=========================================="
echo

echo "Final GPU Status:"
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv

exit $OVERALL_SUCCESS
"""

    return script


def main():
    config_path = Path("slurm/full_run/model_configs.json")
    with open(config_path) as f:
        config = json.load(f)

    # Create jobs directory
    jobs_dir = Path("slurm/full_run/jobs_bundled")
    jobs_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("GENERATING BUNDLED JOB SCRIPTS")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Models: {len(config['models'])}")
    print(f"  Temperatures per model: {len(config['temperatures'])}")
    print(f"  Runs per temperature: {config['n_runs_per_temperature']}")
    print(f"  Total experiments: {len(config['models']) * len(config['temperatures']) * config['n_runs_per_temperature']}")
    print()

    for model_key, model_config in config['models'].items():
        job_name = f"{model_key}_full"
        script_path = jobs_dir / f"{job_name}.sbatch"

        script = generate_bundled_job(model_key, model_config, config)

        with open(script_path, 'w') as f:
            f.write(script)

        script_path.chmod(0o755)

        print(f"✓ Created: {script_path.name}")
        print(f"    {model_config['display_name']}")
        print(f"    Will run: {', '.join(f'temp {t}' for t in config['temperatures'])}")
        print()

    print("=" * 70)
    print(f"Generated {len(config['models'])} bundled job scripts")
    print("=" * 70)


if __name__ == "__main__":
    main()
