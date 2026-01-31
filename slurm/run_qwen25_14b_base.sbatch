#!/bin/bash -l
#SBATCH --job-name=qwen25_14b_base
#SBATCH --partition=general
#SBATCH --time=48:00:00
#SBATCH --gres=gpu:2
#SBATCH --cpus-per-task=32
#SBATCH --mem=200G
#SBATCH --output=logs/qwen25_14b_base_%j.out
#SBATCH --error=logs/qwen25_14b_base_%j.err

# Print job info
echo "=========================================="
echo "Base Model Test - Qwen2.5-14B"
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

# Start vLLM server in background
echo "Starting vLLM server for Qwen2.5-14B (BASE MODEL)..."
RANDOM_SEED=$(($(date +%s%N) % 2147483647))
echo "Using random seed: $RANDOM_SEED"
vllm serve Qwen/Qwen2.5-14B \
    --port 8000 \
    --tensor-parallel-size 2 \
    --gpu-memory-utilization 0.9 \
    --dtype bfloat16 \
    --max-model-len 4096 \
    --disable-log-requests \
    --seed $RANDOM_SEED \
    > logs/vllm_server_qwen25_14b_base_${SLURM_JOB_ID}.log 2>&1 &

VLLM_PID=$!
echo "vLLM server started with PID: $VLLM_PID"
echo

# Wait for vLLM server to be ready
echo "Waiting for vLLM server to be ready..."
echo "Note: Initial startup takes ~10-15 minutes for model loading"
MAX_WAIT=1800  # 30 minutes
ELAPSED=0
while ! curl -s http://localhost:8000/health > /dev/null 2>&1; do
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

echo "Starting Base Model Temperature Impact Test..."
echo "  - Model: Qwen2.5-14B (BASE - no instruction tuning)"
echo "  - Temperatures: 0.0, 0.3, 0.7"
echo "  - Runs per temperature: 3"
echo "  - Total experiments: 9"
echo "  - Dataset: Focused 1,030 questions"
echo "  - Prompt: Simple (no role-playing)"
echo "  - Checkpoints: Every 10 questions"
echo
echo "Note: This job can be safely interrupted and will resume from checkpoints."
echo

# Run the base model test
python scripts/base_runs/test_base_model.py \
    --model-name "Qwen/Qwen2.5-14B" \
    --output-dir "results/base_runs/qwen25_14b" \
    --dataset "data/datasets/medqa_focused_1030.json" \
    --vllm-url "http://localhost:8000"

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
    echo "Base model test completed successfully!"
    echo "=========================================="
else
    echo
    echo "=========================================="
    echo "Test failed or interrupted"
    echo "=========================================="
    echo "Checkpoints saved. Job will resume from last checkpoint if resubmitted."
fi

echo
echo "Job completed at: $(date)"
echo "=========================================="
echo

# Final GPU status
echo "Final GPU Status:"
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv

exit $TEST_EXIT_CODE
