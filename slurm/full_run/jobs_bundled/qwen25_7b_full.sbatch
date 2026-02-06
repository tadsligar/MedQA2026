#!/bin/bash -l
#SBATCH --job-name=qwen25_7b_full
#SBATCH --partition=general
#SBATCH --time=48:00:00
#SBATCH --gres=gpu:2
#SBATCH --cpus-per-task=32
#SBATCH --mem=200G
#SBATCH --output=slurm/full_run/logs/qwen25_7b_full_%j.out
#SBATCH --error=slurm/full_run/logs/qwen25_7b_full_%j.err

echo "=========================================="
echo "Full Dataset Test - Qwen 2.5 7B"
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
echo "Starting vLLM server for Qwen 2.5 7B..."
echo "Model will stay loaded for all temperature experiments"
echo "=========================================="
echo

RANDOM_SEED=$(($(date +%s%N) % 2147483647))
echo "Random seed: $RANDOM_SEED"
echo

vllm serve Qwen/Qwen2.5-7B \
    --port $VLLM_PORT \
    --tensor-parallel-size 2 \
    --gpu-memory-utilization 0.7 \
    --dtype bfloat16 \
    --max-model-len 4096 \
    --disable-log-requests \
    --seed $RANDOM_SEED \
    > slurm/full_run/logs/vllm_qwen25_7b_${SLURM_JOB_ID}.log 2>&1 &

VLLM_PID=$!
echo "vLLM server started with PID: $VLLM_PID"
echo

# Wait for vLLM to be ready
echo "Waiting for vLLM server to be ready..."
MAX_WAIT=1800
ELAPSED=0
while ! curl -s http://localhost:$VLLM_PORT/health > /dev/null 2>&1; do
    if [ $ELAPSED -ge $MAX_WAIT ]; then
        echo "ERROR: vLLM server did not start within ${MAX_WAIT}s"
        kill $VLLM_PID 2>/dev/null
        exit 1
    fi
    sleep 10
    ELAPSED=$((ELAPSED + 10))
    if [ $((ELAPSED % 60)) -eq 0 ]; then
        echo "  Still waiting... (${ELAPSED}s / $((ELAPSED / 60)) min)"
    fi
done
echo "vLLM server ready!"
echo

echo "GPU Status after model loaded:"
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv
echo

# Run all temperatures sequentially
OVERALL_SUCCESS=0
TEMPS=(0.0 0.3 0.7)

for TEMP in "${TEMPS[@]}"; do
    echo
    echo "========================================================================"
    echo "Running Temperature: $TEMP"
    echo "Model: Qwen 2.5 7B"
    echo "Dataset: 12723 questions"
    echo "Started: $(date)"
    echo "========================================================================"
    echo

    python scripts/base_runs/test_base_model_single.py \
        --model-name "Qwen/Qwen2.5-7B" \
        --output-dir "results/base_runs_full/qwen25_7b" \
        --dataset "data/datasets/medqa_full_combined.json" \
        --vllm-url "http://localhost:$VLLM_PORT" \
        --temperature $TEMP \
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

output_dir = Path("results/base_runs_full/qwen25_7b")
temperatures = [0.0, 0.3, 0.7]

temperature_results = []

for temp in temperatures:
    results_file = output_dir / f"temp{temp}_run1_results.json"

    if results_file.exists():
        with open(results_file) as f:
            results = json.load(f)

        correct = sum(1 for r in results if r.get('is_correct', False))
        accuracy = (correct / len(results)) * 100

        temperature_results.append({
            'temperature': temp,
            'run1_accuracy': accuracy,
            'mean_accuracy': accuracy,
            'std_dev': 0.0
        })

        print(f"Temperature {temp}: {accuracy:.2f}%")

summary = {
    'dataset': "data/datasets/medqa_full_combined.json",
    'total_questions': 12723,
    'model': "Qwen/Qwen2.5-7B",
    'model_type': 'base',
    'run_type': 'full_dataset_run',
    'prompt_style': 'simple',
    'temperatures': list(temperatures),
    'n_runs_per_temperature': 1,
    'temperature_results': temperature_results
}

summary_file = output_dir / "summary.json"
with open(summary_file, 'w') as f:
    json.dump(summary, f, indent=2)

print(f"\nSummary saved to {summary_file}")
PYTHON_EOF

    echo
    echo "Creating completion marker..."
    touch slurm/full_run/state/qwen25_7b_full.completed

    echo
    echo "Triggering auto-commit..."
    sbatch slurm/full_run/auto_commit_qwen25_7b.sbatch
else
    echo
    echo "Some experiments failed. Check logs for details."
    echo "Checkpoints saved - can resume failed experiments."
    echo "$OVERALL_SUCCESS" > slurm/full_run/state/qwen25_7b_full.failed
fi

echo
echo "=========================================="
echo "Job completed at: $(date)"
echo "=========================================="
echo

echo "Final GPU Status:"
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv

exit $OVERALL_SUCCESS
