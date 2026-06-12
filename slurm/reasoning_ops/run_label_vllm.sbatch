#!/bin/bash -l
#SBATCH --job-name=p4_label_vllm
#SBATCH --partition=general
#SBATCH --time=24:00:00
#SBATCH --gres=gpu:2
#SBATCH --cpus-per-task=32
#SBATCH --mem=200G
#SBATCH --output=logs/p4_label_vllm_%j.out
#SBATCH --error=logs/p4_label_vllm_%j.err

# Paper 4 -- reasoning-operation + 15-system labeling via a LOCAL open model (vLLM), as an
# INDEPENDENT SECOND ANNOTATOR to the gpt-5.4-mini API pass. Agreement between the two becomes a
# label-reliability number (inter-annotator). Free, no data egress.
#
# Defaults to Qwen2.5-32B-Instruct on 2 GPUs (matches the repo's proven instruct jobs). For the
# stronger 72B annotator, launch with:  sbatch --gres=gpu:4 --export=ALL,MODEL=Qwen/Qwen2.5-72B-Instruct,TP=4 ...
#
# IMPORTANT: CLASSIFIER_MODEL must equal the served model id EXACTLY (vLLM matches on it).

MODEL=${MODEL:-Qwen/Qwen2.5-32B-Instruct}
TP=${TP:-2}
DATASET=${DATASET:-data/datasets/medqa_full_combined.json}
OUTTAG=${OUTTAG:-qwen25_32b}     # output filename suffix; keeps it separate from the API labels
OUTPUT=results/reasoning_ops/op_labels_${OUTTAG}.jsonl

echo "=========================================="
echo "Paper 4 vLLM labeling -- $MODEL (TP=$TP)"
echo "Job $SLURM_JOB_ID  Node $SLURM_NODELIST  GPUs $CUDA_VISIBLE_DEVICES  Start $(date)"
echo "dataset=$DATASET  output=$OUTPUT"
echo "=========================================="

cd /aiau010_scratch/tzs0128/repo/MedQA2026
source ~/.bashrc
conda activate medqa
export HF_HOME=/aiau010_scratch/tzs0128/hf_cache
export TRANSFORMERS_CACHE=/aiau010_scratch/tzs0128/hf_cache
mkdir -p logs results/reasoning_ops

# --- serve the model (OpenAI-compatible endpoint at :8000/v1) ---
RANDOM_SEED=$(($(date +%s%N) % 2147483647))
echo "Starting vLLM ($MODEL) seed=$RANDOM_SEED ..."
vllm serve "$MODEL" \
    --port 8000 \
    --tensor-parallel-size "$TP" \
    --gpu-memory-utilization 0.9 \
    --dtype bfloat16 \
    --max-model-len 4096 \
    --disable-log-requests \
    --seed $RANDOM_SEED \
    > logs/vllm_p4_label_${SLURM_JOB_ID}.log 2>&1 &
VLLM_PID=$!
echo "vLLM PID $VLLM_PID; waiting for health (model load ~10-15 min)..."
MAX_WAIT=1800; ELAPSED=0
while ! curl -s http://localhost:8000/health > /dev/null 2>&1; do
    if [ $ELAPSED -ge $MAX_WAIT ]; then
        echo "ERROR: vLLM did not start within ${MAX_WAIT}s"; kill $VLLM_PID 2>/dev/null; exit 1
    fi
    sleep 10; ELAPSED=$((ELAPSED + 10))
    [ $((ELAPSED % 60)) -eq 0 ] && echo "  waiting... ($((ELAPSED/60)) min)"
done
echo "vLLM ready."

# --- run the labeler against the local endpoint (resumable; same script as the API path) ---
export OPENAI_BASE_URL=http://localhost:8000/v1
export OPENAI_API_KEY=EMPTY
export CLASSIFIER_MODEL="$MODEL"
python scripts/dataset_generation/operation_labeler.py \
    --dataset "$DATASET" \
    --output "$OUTPUT"
EXIT=$?

echo "Shutting down vLLM..."; kill $VLLM_PID 2>/dev/null; wait $VLLM_PID 2>/dev/null

# --- quick agreement check vs the API labels, if present (operation: acc/kappa; systems: F1) ---
if [ -f results/reasoning_ops/op_labels.jsonl ]; then
    echo "Computing agreement vs gpt-5.4-mini labels (op_labels.jsonl)..."
    python scripts/dataset_generation/score_op_labels.py \
        --pred "$OUTPUT" \
        --gold results/reasoning_ops/op_labels.jsonl || true
fi
echo "Finished at $(date) with exit $EXIT"
exit $EXIT
