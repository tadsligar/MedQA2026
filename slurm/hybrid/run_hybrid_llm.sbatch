#!/bin/bash -l
#SBATCH --job-name=ns_hybrid_llm
#SBATCH --partition=general
#SBATCH --time=24:00:00
#SBATCH --gres=gpu:2
#SBATCH --cpus-per-task=32
#SBATCH --mem=200G
#SBATCH --output=logs/ns_hybrid_llm_%j.out
#SBATCH --error=logs/ns_hybrid_llm_%j.err

# Paper 2 EXP4 (UMLS-in-prompt) + EXP6 (LLM proposer). Serves a vLLM model.
# MODEL/TP overridable; 7B/14B fit a 4090 (drop --gres for local), 32B needs gpu:2.
MODEL=${MODEL:-Qwen/Qwen2.5-14B}; KEY=${KEY:-qwen25_14b}; TP=${TP:-2}
cd /aiau010_scratch/tzs0128/projects/MedQA2026
source ~/.bashrc; conda activate medqa
export HF_HOME=/aiau010_scratch/tzs0128/hf_cache
export TRANSFORMERS_CACHE=/aiau010_scratch/tzs0128/hf_cache
INDEX=${INDEX:-data/umls/umls_2025AB_index.db}
mkdir -p logs results/ns/umls_in_prompt results/ns/cove

RANDOM_SEED=$(($(date +%s%N) % 2147483647))
vllm serve $MODEL --port 8000 --tensor-parallel-size $TP --gpu-memory-utilization 0.9 \
    --dtype bfloat16 --max-model-len 4096 --disable-log-requests --seed $RANDOM_SEED \
    > logs/vllm_hybrid_${KEY}_${SLURM_JOB_ID}.log 2>&1 &
VLLM_PID=$!; MAX_WAIT=1800; ELAPSED=0
while ! curl -s http://localhost:8000/health > /dev/null 2>&1; do
  [ $ELAPSED -ge $MAX_WAIT ] && { echo "vLLM timeout"; kill $VLLM_PID; exit 1; }
  sleep 10; ELAPSED=$((ELAPSED+10)); [ $((ELAPSED % 60)) -eq 0 ] && echo "  waiting $((ELAPSED/60))m"
done
echo "vLLM ready."

# EXP4 UMLS-in-prompt
python -m neurosymbolic.umls_verifier.src.umls_in_prompt \
    --index "$INDEX" --model-name "$MODEL" --vllm-url http://localhost:8000 \
    --output results/ns/umls_in_prompt/${KEY}_results.json

# EXP6 CoVe with LLM proposer (verify_only + revision)
for MODE in verify_only revision; do
  python -m neurosymbolic.chain_of_verification.src.cove \
      --index "$INDEX" --proposer llm --mode $MODE --vllm-url http://localhost:8000 \
      --output results/ns/cove/llm_${MODE}_results.json
done

kill $VLLM_PID 2>/dev/null; wait $VLLM_PID 2>/dev/null
python papers/paper2/analysis/compute_hybrid.py
echo "Done $(date)"
