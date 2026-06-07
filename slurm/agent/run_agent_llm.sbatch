#!/bin/bash -l
#SBATCH --job-name=agent_llm
#SBATCH --partition=general
#SBATCH --time=24:00:00
#SBATCH --gres=gpu:2
#SBATCH --cpus-per-task=32
#SBATCH --mem=200G
#SBATCH --output=logs/agent_llm_%j.out
#SBATCH --error=logs/agent_llm_%j.err

# Paper 3 -- LLM-planner policy (agent asks the model which check to run next). Serves vLLM.
MODEL=${MODEL:-Qwen/Qwen2.5-14B}; TP=${TP:-2}
cd /aiau010_scratch/tzs0128/projects/MedQA2026
source ~/.bashrc; conda activate medqa
export HF_HOME=/aiau010_scratch/tzs0128/hf_cache
export TRANSFORMERS_CACHE=/aiau010_scratch/tzs0128/hf_cache
INDEX=${INDEX:-data/umls/umls_2025AB_index.db}
LOGP=${LOGP:-results/base_runs_logprobs/qwen25_32b/temp0.0_run1_results.json}
mkdir -p logs results/agent/eval

RANDOM_SEED=$(($(date +%s%N) % 2147483647))
vllm serve $MODEL --port 8000 --tensor-parallel-size $TP --gpu-memory-utilization 0.9 \
    --dtype bfloat16 --max-model-len 4096 --disable-log-requests --seed $RANDOM_SEED \
    > logs/vllm_agent_${SLURM_JOB_ID}.log 2>&1 &
VLLM_PID=$!; MAX_WAIT=1800; ELAPSED=0
while ! curl -s http://localhost:8000/health > /dev/null 2>&1; do
  [ $ELAPSED -ge $MAX_WAIT ] && { echo "vLLM timeout"; kill $VLLM_PID; exit 1; }
  sleep 10; ELAPSED=$((ELAPSED+10)); [ $((ELAPSED % 60)) -eq 0 ] && echo "  waiting $((ELAPSED/60))m"
done
echo "vLLM ready."

python -m neurosymbolic.agent.src.agent --index "$INDEX" --llm-logprobs "$LOGP" \
    --policy llm_planner --belief weighted --budget 6 --vllm-url http://localhost:8000 \
    --output results/agent/eval/full_llm_planner_results.json

kill $VLLM_PID 2>/dev/null; wait $VLLM_PID 2>/dev/null
python papers/paper3/analysis/compute_agent.py
echo "Done $(date)"
