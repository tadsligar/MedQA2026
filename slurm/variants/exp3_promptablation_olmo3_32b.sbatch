#!/bin/bash -l
#SBATCH --job-name=exp3_promptablation_olmo3_32b
#SBATCH --partition=general
#SBATCH --time=24:00:00
#SBATCH --gres=gpu:2
#SBATCH --cpus-per-task=32
#SBATCH --mem=200G
#SBATCH --output=logs/exp3_promptablation_olmo3_32b_%j.out
#SBATCH --error=logs/exp3_promptablation_olmo3_32b_%j.err

# Paper 1 EXP3 -- prompt-format ablation (4 variants, t=0.0)
cd /aiau010_scratch/tzs0128/projects/MedQA2026
source ~/.bashrc
conda activate medqa
export HF_HOME=/aiau010_scratch/tzs0128/hf_cache
export TRANSFORMERS_CACHE=/aiau010_scratch/tzs0128/hf_cache
mkdir -p logs results/prompt_ablation/olmo3_32b

echo "Serving allenai/Olmo-3-1125-32B ..."
RANDOM_SEED=$(($(date +%s%N) % 2147483647))
vllm serve allenai/Olmo-3-1125-32B --port 8000 --tensor-parallel-size 2 --gpu-memory-utilization 0.9 \
    --dtype bfloat16 --max-model-len 4096 --disable-log-requests --seed $RANDOM_SEED \
    > logs/vllm_exp3_promptablation_olmo3_32b_${SLURM_JOB_ID}.log 2>&1 &
VLLM_PID=$!
MAX_WAIT=1800; ELAPSED=0
while ! curl -s http://localhost:8000/health > /dev/null 2>&1; do
    if [ $ELAPSED -ge $MAX_WAIT ]; then echo "vLLM start timeout"; kill $VLLM_PID 2>/dev/null; exit 1; fi
    sleep 10; ELAPSED=$((ELAPSED+10)); [ $((ELAPSED % 60)) -eq 0 ] && echo "  waiting $((ELAPSED/60))m"
done
echo "vLLM ready."

python scripts/base_runs/test_base_model_variants.py --model-name allenai/Olmo-3-1125-32B --vllm-url http://localhost:8000 --output-dir results/prompt_ablation/olmo3_32b/v0 --prompt-variant v0 --temperatures 0.0 --n-runs 1
python scripts/base_runs/test_base_model_variants.py --model-name allenai/Olmo-3-1125-32B --vllm-url http://localhost:8000 --output-dir results/prompt_ablation/olmo3_32b/v1 --prompt-variant v1 --temperatures 0.0 --n-runs 1
python scripts/base_runs/test_base_model_variants.py --model-name allenai/Olmo-3-1125-32B --vllm-url http://localhost:8000 --output-dir results/prompt_ablation/olmo3_32b/v2 --prompt-variant v2 --temperatures 0.0 --n-runs 1
python scripts/base_runs/test_base_model_variants.py --model-name allenai/Olmo-3-1125-32B --vllm-url http://localhost:8000 --output-dir results/prompt_ablation/olmo3_32b/v3 --prompt-variant v3 --temperatures 0.0 --n-runs 1
EXIT=$?
kill $VLLM_PID 2>/dev/null; wait $VLLM_PID 2>/dev/null
echo "Done $(date) exit $EXIT"; exit $EXIT
