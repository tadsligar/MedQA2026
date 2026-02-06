#!/usr/bin/env python3
"""
Generate individual SLURM job scripts for all model/temperature/run combinations.
"""
import json
from pathlib import Path

def generate_job_script(model_key, model_config, temp, run, config):
    """Generate a single SLURM job script."""

    job_name = f"{model_key}_t{temp}_r{run}"
    script_content = f"""#!/bin/bash -l
#SBATCH --job-name={job_name}
#SBATCH --partition={config['slurm']['partition']}
#SBATCH --time={config['slurm']['time_limit']}
#SBATCH --gres=gpu:{model_config['gpus']}
#SBATCH --cpus-per-task={config['slurm']['cpus_per_task']}
#SBATCH --mem={config['slurm']['mem']}
#SBATCH --output=slurm/full_run/logs/{job_name}_%j.out
#SBATCH --error=slurm/full_run/logs/{job_name}_%j.err

# Print job info
echo "=========================================="
echo "Full Dataset Test - {model_config['display_name']}"
echo "Temperature: {temp} | Run: {run}"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Partition: $SLURM_JOB_PARTITION"
echo "GPUs: $CUDA_VISIBLE_DEVICES"
echo "CPUs: $SLURM_CPUS_PER_TASK"
echo "Start time: $(date)"
echo "=========================================="
echo

# Change to project directory
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

# GPU status before start
echo "GPU Status before start:"
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv
echo

# Use a unique port based on job ID to avoid conflicts
VLLM_PORT=$((8000 + ($SLURM_JOB_ID % 1000)))
echo "Using vLLM port: $VLLM_PORT"
echo

# Start vLLM server in background
echo "Starting vLLM server for {model_config['display_name']}..."
RANDOM_SEED=$(($(date +%s%N) % 2147483647))
echo "Using random seed: $RANDOM_SEED (ensures different runs at same temp vary)"
"""

    # Add vLLM server command with model-specific settings
    vllm_cmd = f"""vllm serve {model_config['model_name']} \\
    --port $VLLM_PORT \\
    --tensor-parallel-size {model_config['tensor_parallel_size']} \\
    --gpu-memory-utilization {model_config['gpu_memory_utilization']} \\
    --dtype bfloat16 \\
    --max-model-len {model_config['max_model_len']} \\
    --disable-log-requests \\
    --seed $RANDOM_SEED"""

    if model_config.get('max_num_seqs'):
        vllm_cmd += f" \\\n    --max-num-seqs {model_config['max_num_seqs']}"

    vllm_cmd += f" \\\n    > slurm/full_run/logs/vllm_{job_name}_${{SLURM_JOB_ID}}.log 2>&1 &"

    script_content += vllm_cmd + f"""

VLLM_PID=$!
echo "vLLM server started with PID: $VLLM_PID"
echo

# Wait for vLLM server to be ready
echo "Waiting for vLLM server to be ready..."
echo "Note: Initial startup may take time for model loading"
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
echo "vLLM server is ready!"
echo

# GPU status after vLLM loads
echo "GPU Status after vLLM loads model:"
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv
echo

echo "Starting Base Model Test..."
echo "  - Model: {model_config['display_name']}"
echo "  - Temperature: {temp}"
echo "  - Run: {run}"
echo "  - Dataset: {config['total_questions']} questions (full MedQA)"
echo "  - Checkpoints: Every 10 questions"
echo

# Create a single-run version of the test script
# We modify the script to only run this specific temperature and run number
python scripts/base_runs/test_base_model_single.py \\
    --model-name "{model_config['model_name']}" \\
    --output-dir "{model_config['output_dir']}" \\
    --dataset "{config['dataset']}" \\
    --vllm-url "http://localhost:$VLLM_PORT" \\
    --temperature {temp} \\
    --run-number {run}

# Capture exit code
TEST_EXIT_CODE=$?

# Cleanup: Kill vLLM server
echo
echo "Shutting down vLLM server..."
kill $VLLM_PID 2>/dev/null
wait $VLLM_PID 2>/dev/null

# Check if test completed successfully
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo
    echo "=========================================="
    echo "Test completed successfully!"
    echo "Creating completion marker..."
    echo "=========================================="

    # Create marker file to signal orchestrator
    touch slurm/full_run/state/{job_name}.completed

    # Trigger auto-commit job (with dependency check to avoid duplicate commits)
    echo "Submitting auto-commit job for {model_key}..."
    sbatch --dependency=singleton slurm/full_run/auto_commit_{model_key}.sbatch
else
    echo
    echo "=========================================="
    echo "Test failed or interrupted (exit code: $TEST_EXIT_CODE)"
    echo "=========================================="
    echo "Checkpoints saved. Job can be relaunched to resume."

    # Create failure marker
    echo "$TEST_EXIT_CODE" > slurm/full_run/state/{job_name}.failed
fi

echo
echo "Job completed at: $(date)"
echo "=========================================="
echo

# Final GPU status
echo "Final GPU Status:"
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv

exit $TEST_EXIT_CODE
"""

    return script_content


def main():
    # Load configuration
    config_path = Path("slurm/full_run/model_configs.json")
    with open(config_path) as f:
        config = json.load(f)

    # Generate job scripts for each combination
    jobs_dir = Path("slurm/full_run/jobs")
    jobs_dir.mkdir(parents=True, exist_ok=True)

    total_jobs = 0

    for model_key, model_config in config['models'].items():
        print(f"\nGenerating jobs for {model_key} ({model_config['display_name']})...")

        # Create output directory
        output_dir = Path(model_config['output_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)

        for temp in config['temperatures']:
            for run in range(1, config['n_runs_per_temperature'] + 1):
                job_name = f"{model_key}_t{temp}_r{run}"
                script_path = jobs_dir / f"{job_name}.sbatch"

                script_content = generate_job_script(
                    model_key, model_config, temp, run, config
                )

                with open(script_path, 'w') as f:
                    f.write(script_content)

                # Make executable
                script_path.chmod(0o755)

                total_jobs += 1
                print(f"  Created: {script_path.name}")

    print(f"\n{'='*60}")
    print(f"Generated {total_jobs} job scripts")
    print(f"  Models: {len(config['models'])}")
    print(f"  Temperatures: {len(config['temperatures'])}")
    print(f"  Runs per temperature: {config['n_runs_per_temperature']}")
    print(f"  Total experiments: {total_jobs}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
