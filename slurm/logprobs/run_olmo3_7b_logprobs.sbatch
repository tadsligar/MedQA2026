#!/bin/bash -l
#SBATCH --job-name=olmo3_7b_logprobs
#SBATCH --partition=general
#SBATCH --time=24:00:00
#SBATCH --gres=gpu:2
#SBATCH --cpus-per-task=32
#SBATCH --mem=200G
#SBATCH --output=logs/olmo3_7b_logprobs_%j.out
#SBATCH --error=logs/olmo3_7b_logprobs_%j.err

# Paper 1 EXP1 -- logprobs / calibration run for allenai/Olmo-3-1025-7B
# Re-runs t=0.0 run 1 (deterministic) WITH token logprobs to enable ECE/reliability.
# To extend to confidence-vs-temperature, pass: --temperatures "0.0,0.3,0.7" --n-runs 1

echo "=========================================="
echo "EXP1 logprobs -- allenai/Olmo-3-1025-7B"
echo "Job ID: $SLURM_JOB_ID  Node: $SLURM_NODELIST  GPUs: $CUDA_VISIBLE_DEVICES"
echo "Start: $(date)"
echo "=========================================="

cd /aiau010_scratch/tzs0128/repo/MedQA2026
source ~/.bashrc
conda activate medqa
export HF_HOME=/aiau010_scratch/tzs0128/hf_cache
export TRANSFORMERS_CACHE=/aiau010_scratch/tzs0128/hf_cache

mkdir -p logs results/base_runs_logprobs/olmo3_7b

echo "Starting vLLM server for allenai/Olmo-3-1025-7B (BASE MODEL)..."
RANDOM_SEED=$(($(date +%s%N) % 2147483647))
echo "Using random seed: $RANDOM_SEED"
vllm serve allenai/Olmo-3-1025-7B \
    --port 8000 \
    --tensor-parallel-size 2 \
    --gpu-memory-utilization 0.9 \
    --dtype bfloat16 \
    --max-model-len 4096 \
    --disable-log-requests \
    --seed $RANDOM_SEED \
    > logs/vllm_olmo3_7b_logprobs_${SLURM_JOB_ID}.log 2>&1 &
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

python scripts/base_runs/test_base_model_logprobs.py \
    --model-name "allenai/Olmo-3-1025-7B" \
    --output-dir "results/base_runs_logprobs/olmo3_7b" \
    --dataset "data/datasets/medqa_focused_1030.json" \
    --vllm-url "http://localhost:8000" \
    --temperatures "0.0" \
    --n-runs 1
EXIT=$?

echo "Shutting down vLLM..."; kill $VLLM_PID 2>/dev/null; wait $VLLM_PID 2>/dev/null
echo "Finished at $(date) with exit $EXIT"

# --- Paper1 EXP1: auto commit & push results (sequential calibration run) ---
if [ $EXIT -eq 0 ]; then
    echo "Committing results to git..."
    cd /aiau010_scratch/tzs0128/repo/MedQA2026
    git add results/base_runs_logprobs/olmo3_7b
    if git commit -m "EXP1 logprobs: OLMo-3-7B calibration results (job ${SLURM_JOB_ID})"; then
        git push origin master && echo "Pushed results to GitHub." \
            || echo "WARN: git push failed; commit is local. Flush from login node: git push origin master"
    else
        echo "Nothing new to commit."
    fi
else
    echo "Run exited $EXIT; skipping git commit."
fi

exit $EXIT
