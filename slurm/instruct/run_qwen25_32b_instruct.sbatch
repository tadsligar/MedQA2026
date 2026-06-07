#!/bin/bash -l
#SBATCH --job-name=qwen25_32b_instruct
#SBATCH --partition=general
#SBATCH --time=48:00:00
#SBATCH --gres=gpu:2
#SBATCH --cpus-per-task=32
#SBATCH --mem=200G
#SBATCH --output=logs/qwen25_32b_instruct_%j.out
#SBATCH --error=logs/qwen25_32b_instruct_%j.err

# Paper 1 EXP2 -- instruction-tuned comparison for Qwen/Qwen2.5-32B-Instruct
# Chat endpoint (model's chat template). For a quick headline table use t=0.0 x1 run:
#   ... --temperatures "0.0" --n-runs 1
# NOTE: confirm the exact instruct model ID on HuggingFace before launching.

echo "=========================================="
echo "EXP2 instruct -- Qwen/Qwen2.5-32B-Instruct"
echo "Job ID: $SLURM_JOB_ID  Node: $SLURM_NODELIST  GPUs: $CUDA_VISIBLE_DEVICES"
echo "Start: $(date)"
echo "=========================================="

cd /aiau010_scratch/tzs0128/projects/MedQA2026
source ~/.bashrc
conda activate medqa
export HF_HOME=/aiau010_scratch/tzs0128/hf_cache
export TRANSFORMERS_CACHE=/aiau010_scratch/tzs0128/hf_cache

mkdir -p logs results/instruct_runs/qwen25_32b_instruct

echo "Starting vLLM server for Qwen/Qwen2.5-32B-Instruct (INSTRUCT -- chat template)..."
RANDOM_SEED=$(($(date +%s%N) % 2147483647))
echo "Using random seed: $RANDOM_SEED"
vllm serve Qwen/Qwen2.5-32B-Instruct \
    --port 8000 \
    --tensor-parallel-size 2 \
    --gpu-memory-utilization 0.9 \
    --dtype bfloat16 \
    --max-model-len 4096 \
    --disable-log-requests \
    --seed $RANDOM_SEED \
    > logs/vllm_qwen25_32b_instruct_${SLURM_JOB_ID}.log 2>&1 &
VLLM_PID=$!
echo "vLLM PID: $VLLM_PID"

echo "Waiting for vLLM server (model load ~10-15 min)..."
MAX_WAIT=1800; ELAPSED=0
while ! curl -s http://localhost:8000/health > /dev/null 2>&1; do
    if [ $ELAPSED -ge $MAX_WAIT ]; then
        echo "ERROR: vLLM did not start within ${MAX_WAIT}s"; kill $VLLM_PID 2>/dev/null; exit 1
    fi
    sleep 10; ELAPSED=$((ELAPSED + 10))
    if [ $((ELAPSED % 60)) -eq 0 ]; then echo "  waiting... ($((ELAPSED/60)) min)"; fi
done
echo "vLLM ready."

python scripts/instruct_runs/test_instruct_model.py \
    --model-name "Qwen/Qwen2.5-32B-Instruct" \
    --output-dir "results/instruct_runs/qwen25_32b_instruct" \
    --dataset "data/datasets/medqa_focused_1030.json" \
    --vllm-url "http://localhost:8000" \
    --temperatures "0.0,0.3,0.7" \
    --n-runs 3
EXIT=$?

echo "Shutting down vLLM..."; kill $VLLM_PID 2>/dev/null; wait $VLLM_PID 2>/dev/null
echo "Finished at $(date) with exit $EXIT"
exit $EXIT
