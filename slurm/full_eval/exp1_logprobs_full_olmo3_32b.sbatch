#!/bin/bash -l
#SBATCH --job-name=exp1_logprobs_full_olmo3_32b
#SBATCH --partition=general
#SBATCH --time=72:00:00
#SBATCH --gres=gpu:2
#SBATCH --cpus-per-task=32
#SBATCH --mem=200G
#SBATCH --output=logs/exp1_logprobs_full_olmo3_32b_%j.out
#SBATCH --error=logs/exp1_logprobs_full_olmo3_32b_%j.err

# Paper1 EXP1 calibration (base, logprobs) -- 3 temps x 1 run
# Full 12,723-question 5-option set -> results/base_runs_logprobs_full/olmo3_32b (focused results untouched).
# Unique port (8100+JOB_ID%800) so this never collides with another vLLM on :8000 (e.g. Paper 4),
# even if co-located on a node. Runner resumes from checkpoint on resubmit if wall-limited.
cd /aiau010_scratch/tzs0128/repo/MedQA2026
source ~/.bashrc
conda activate medqa
export HF_HOME=/aiau010_scratch/tzs0128/hf_cache
export TRANSFORMERS_CACHE=/aiau010_scratch/tzs0128/hf_cache
mkdir -p logs results/base_runs_logprobs_full/olmo3_32b

VLLM_PORT=$((8100 + (SLURM_JOB_ID % 800)))
echo "Job $SLURM_JOB_ID node $SLURM_NODELIST gpus $CUDA_VISIBLE_DEVICES port $VLLM_PORT start $(date)"
RANDOM_SEED=$(($(date +%s%N) % 2147483647))
vllm serve allenai/Olmo-3-1125-32B --port $VLLM_PORT --tensor-parallel-size 2 --gpu-memory-utilization 0.9 \
    --dtype bfloat16 --max-model-len 4096 --disable-log-requests --seed $RANDOM_SEED \
    > logs/vllm_exp1_logprobs_full_olmo3_32b_${SLURM_JOB_ID}.log 2>&1 &
VLLM_PID=$!
MAX_WAIT=1800; ELAPSED=0
while ! curl -s http://localhost:$VLLM_PORT/health > /dev/null 2>&1; do
    if [ $ELAPSED -ge $MAX_WAIT ]; then echo "vLLM start timeout"; kill $VLLM_PID 2>/dev/null; exit 1; fi
    sleep 10; ELAPSED=$((ELAPSED+10)); [ $((ELAPSED % 60)) -eq 0 ] && echo "  waiting $((ELAPSED/60))m"
done
echo "vLLM ready $(date)."

python scripts/base_runs/test_base_model_logprobs.py --model-name allenai/Olmo-3-1125-32B --output-dir results/base_runs_logprobs_full/olmo3_32b --dataset data/datasets/medqa_full_combined.json --vllm-url http://localhost:$VLLM_PORT --temperatures 0.0,0.3,0.7 --n-runs 1
EXIT=$?
kill $VLLM_PID 2>/dev/null; wait $VLLM_PID 2>/dev/null
echo "Done $(date) exit $EXIT"; exit $EXIT
