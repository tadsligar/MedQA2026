#!/bin/bash -l
#SBATCH --job-name=exp5_selfconsistency_qwen25_14b
#SBATCH --partition=general
#SBATCH --time=24:00:00
#SBATCH --gres=gpu:2
#SBATCH --cpus-per-task=32
#SBATCH --mem=200G
#SBATCH --output=logs/exp5_selfconsistency_qwen25_14b_%j.out
#SBATCH --error=logs/exp5_selfconsistency_qwen25_14b_%j.err

# Paper 1 EXP5 -- self-consistency k=20 at t=0.7
cd /aiau010_scratch/tzs0128/repo/MedQA2026
source ~/.bashrc
conda activate medqa
export HF_HOME=/aiau010_scratch/tzs0128/hf_cache
export TRANSFORMERS_CACHE=/aiau010_scratch/tzs0128/hf_cache
mkdir -p logs results/self_consistency/qwen25_14b

echo "Serving Qwen/Qwen2.5-14B ..."
RANDOM_SEED=$(($(date +%s%N) % 2147483647))
vllm serve Qwen/Qwen2.5-14B --port 8000 --tensor-parallel-size 2 --gpu-memory-utilization 0.9 \
    --dtype bfloat16 --max-model-len 4096 --disable-log-requests --seed $RANDOM_SEED \
    > logs/vllm_exp5_selfconsistency_qwen25_14b_${SLURM_JOB_ID}.log 2>&1 &
VLLM_PID=$!
MAX_WAIT=1800; ELAPSED=0
while ! curl -s http://localhost:8000/health > /dev/null 2>&1; do
    if [ $ELAPSED -ge $MAX_WAIT ]; then echo "vLLM start timeout"; kill $VLLM_PID 2>/dev/null; exit 1; fi
    sleep 10; ELAPSED=$((ELAPSED+10)); [ $((ELAPSED % 60)) -eq 0 ] && echo "  waiting $((ELAPSED/60))m"
done
echo "vLLM ready."

python scripts/base_runs/test_base_model_variants.py --model-name Qwen/Qwen2.5-14B --vllm-url http://localhost:8000 --output-dir results/self_consistency/qwen25_14b --temperatures 0.7 --n-runs 1 --n-samples 20
EXIT=$?
kill $VLLM_PID 2>/dev/null; wait $VLLM_PID 2>/dev/null
echo "Done $(date) exit $EXIT"; exit $EXIT
