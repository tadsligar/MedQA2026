#!/bin/bash -l
#SBATCH --job-name=qwen25_7b_t0.3_r2
#SBATCH --partition=general
#SBATCH --time=48:00:00
#SBATCH --gres=gpu:2
#SBATCH --cpus-per-task=32
#SBATCH --mem=200G
#SBATCH --output=slurm/full_run/logs/qwen25_7b_t0.3_r2_%j.out
#SBATCH --error=slurm/full_run/logs/qwen25_7b_t0.3_r2_%j.err

# Print job info
echo "=========================================="
echo "Full Dataset Test - Qwen 2.5 7B"
echo "Temperature: 0.3 | Run: 2"
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
echo "Starting vLLM server for Qwen 2.5 7B..."
RANDOM_SEED=$(($(date +%s%N) % 2147483647))
echo "Using random seed: $RANDOM_SEED (ensures different runs at same temp vary)"
vllm serve Qwen/Qwen2.5-7B \
    --port $VLLM_PORT \
    --tensor-parallel-size 2 \
    --gpu-memory-utilization 0.9 \
    --dtype bfloat16 \
    --max-model-len 4096 \
    --disable-log-requests \
    --seed $RANDOM_SEED \
    > slurm/full_run/logs/vllm_qwen25_7b_t0.3_r2_${SLURM_JOB_ID}.log 2>&1 &

VLLM_PID=$!
echo "vLLM server started with PID: $VLLM_PID"
echo

# Wait for vLLM server to be ready
echo "Waiting for vLLM server to be ready..."
echo "Note: Initial startup may take time for model loading"
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
echo "vLLM server is ready!"
echo

# GPU status after vLLM loads
echo "GPU Status after vLLM loads model:"
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv
echo

echo "Starting Base Model Test..."
echo "  - Model: Qwen 2.5 7B"
echo "  - Temperature: 0.3"
echo "  - Run: 2"
echo "  - Dataset: 12723 questions (full MedQA)"
echo "  - Checkpoints: Every 10 questions"
echo

# Create a single-run version of the test script
# We modify the script to only run this specific temperature and run number
python scripts/base_runs/test_base_model_single.py \
    --model-name "Qwen/Qwen2.5-7B" \
    --output-dir "results/base_runs_full/qwen25_7b" \
    --dataset "data/datasets/medqa_full_combined.json" \
    --vllm-url "http://localhost:$VLLM_PORT" \
    --temperature 0.3 \
    --run-number 2

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
    touch slurm/full_run/state/qwen25_7b_t0.3_r2.completed

    # Trigger auto-commit job (with dependency check to avoid duplicate commits)
    echo "Submitting auto-commit job for qwen25_7b..."
    sbatch --dependency=singleton slurm/full_run/auto_commit_qwen25_7b.sbatch
else
    echo
    echo "=========================================="
    echo "Test failed or interrupted (exit code: $TEST_EXIT_CODE)"
    echo "=========================================="
    echo "Checkpoints saved. Job can be relaunched to resume."

    # Create failure marker
    echo "$TEST_EXIT_CODE" > slurm/full_run/state/qwen25_7b_t0.3_r2.failed
fi

echo
echo "Job completed at: $(date)"
echo "=========================================="
echo

# Final GPU status
echo "Final GPU Status:"
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv

exit $TEST_EXIT_CODE
