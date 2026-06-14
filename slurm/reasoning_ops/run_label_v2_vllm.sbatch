#!/bin/bash -l
#SBATCH --job-name=p4_v2_qwen_label
#SBATCH --partition=general
#SBATCH --time=12:00:00
#SBATCH --gres=gpu:a100:2
#SBATCH --cpus-per-task=16
#SBATCH --mem=120G
#SBATCH --output=logs/p4_v2_qwen_label_%j.out
#SBATCH --error=logs/p4_v2_qwen_label_%j.err

# Paper 4 — SECOND ANNOTATOR (Qwen) under the VALIDATED v2 competency rubric (lead-in + options,
# rules-ON), identical to the gpt-5.4-mini batch. Produces full-set inter-annotator agreement.
# Default Qwen2.5-32B-Instruct on 2 A100; override: --export=ALL,MODEL=...,TP=...
MODEL=${MODEL:-Qwen/Qwen2.5-32B-Instruct}
TP=${TP:-2}
DATASET=${DATASET:-data/datasets/medqa_full_combined.json}
OUTPUT=results/reasoning_ops/op_labels_v2_qwen.jsonl

echo "Paper4 v2 Qwen labeling -- $MODEL (TP=$TP)  $(date)"
cd /aiau010_scratch/tzs0128/repo/MedQA2026
source ~/.bashrc; conda activate medqa
export HF_HOME=/aiau010_scratch/tzs0128/hf_cache
export TRANSFORMERS_CACHE=/aiau010_scratch/tzs0128/hf_cache
mkdir -p logs results/reasoning_ops

RANDOM_SEED=$(($(date +%s%N) % 2147483647))
vllm serve "$MODEL" --port 8000 --tensor-parallel-size "$TP" --gpu-memory-utilization 0.9 \
    --dtype bfloat16 --max-model-len 4096 --disable-log-requests --seed $RANDOM_SEED \
    > logs/vllm_p4_v2_qwen_${SLURM_JOB_ID}.log 2>&1 &
VLLM_PID=$!
MAX_WAIT=1800; ELAPSED=0
while ! curl -s http://localhost:8000/health > /dev/null 2>&1; do
    [ $ELAPSED -ge $MAX_WAIT ] && { echo "vLLM timeout"; kill $VLLM_PID 2>/dev/null; exit 1; }
    sleep 10; ELAPSED=$((ELAPSED+10)); [ $((ELAPSED % 60)) -eq 0 ] && echo "  waiting $((ELAPSED/60))m"
done
echo "vLLM ready."

export OPENAI_BASE_URL=http://localhost:8000/v1
export OPENAI_API_KEY=EMPTY
export CLASSIFIER_MODEL="$MODEL"
python scripts/dataset_generation/competency_labeler_vllm.py --dataset "$DATASET" --output "$OUTPUT"
EXIT=$?

kill $VLLM_PID 2>/dev/null; wait $VLLM_PID 2>/dev/null

# full-set inter-annotator agreement vs gpt-5.4-mini labels (if present)
if [ -f results/reasoning_ops/op_labels_v2.jsonl ]; then
    echo "=== gpt-5.4-mini vs Qwen agreement (v2 competency) ==="
    python scripts/dataset_generation/score_competency_agreement.py \
        --a results/reasoning_ops/op_labels_v2.jsonl --b "$OUTPUT" || true
fi
echo "Finished $(date) exit $EXIT"; exit $EXIT
