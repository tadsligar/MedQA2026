#!/bin/bash -l
#SBATCH --job-name=qwen25_7b_lp_temp
#SBATCH --partition=general
#SBATCH --time=24:00:00
#SBATCH --gres=gpu:2
#SBATCH --cpus-per-task=32
#SBATCH --mem=200G
#SBATCH --output=logs/qwen25_7b_lp_temp_%j.out
#SBATCH --error=logs/qwen25_7b_lp_temp_%j.err

# Paper 1 EXP1 -- temperature consistency re-run for Qwen/Qwen2.5-7B in the LOGPROB env.
#
# Re-runs a SINGLE (temperature, run) of the focused-1030 base eval using the *exact same*
# model / vLLM / dtype / seed-handling as run_qwen25_7b_logprobs.sbatch, so that Qwen2.5-7B's
# full temperature curve is internally consistent with the new t=0.0 greedy = 59.71% (vs the
# old base-run env's 67.96%). The reusable logprobs runner is used as-is: requesting logprobs
# does NOT change sampling, and its decoding/prompt/answer-extraction (first valid A-D letter)
# are identical to the canonical base runner -- guaranteeing the curve is extraction-consistent
# with the existing t=0.0 logprob runs. The logprob fields are written too (harmless) so this
# results dir stays schema-uniform.
#
# Parameters (inject via --export):
#   TEMP        temperature to run, e.g. 0.3 or 0.7   (REQUIRED)
#   RUN_INDEX   run number to write, 1/2/3            (default 1)
#
# Writes: results/base_runs_logprobs/qwen25_7b/temp${TEMP}_run${RUN_INDEX}_results.json

set -uo pipefail

TEMP="${TEMP:?Set TEMP via --export, e.g. --export=ALL,TEMP=0.3,RUN_INDEX=1}"
RUN_INDEX="${RUN_INDEX:-1}"

echo "=========================================="
echo "EXP1 logprob-env temp consistency -- Qwen/Qwen2.5-7B"
echo "TEMP=$TEMP  RUN_INDEX=$RUN_INDEX"
echo "Job ID: $SLURM_JOB_ID  Node: $SLURM_NODELIST  GPUs: $CUDA_VISIBLE_DEVICES"
echo "Start: $(date)"
echo "=========================================="

cd /aiau010_scratch/tzs0128/repo/MedQA2026
source ~/.bashrc
conda activate medqa
export HF_HOME=/aiau010_scratch/tzs0128/hf_cache
export TRANSFORMERS_CACHE=/aiau010_scratch/tzs0128/hf_cache

mkdir -p logs results/base_runs_logprobs/qwen25_7b

# --- Reproducibility provenance (for paper appendix) ---------------------------
echo "------ PROVENANCE ------"
SNAP_REF="$(cat $HF_HOME/hub/models--Qwen--Qwen2.5-7B/refs/main 2>/dev/null)"
echo "Served model: Qwen/Qwen2.5-7B"
echo "HF snapshot (refs/main): ${SNAP_REF:-UNKNOWN}"
echo "Snapshot dir(s) present:"
ls -1 "$HF_HOME/hub/models--Qwen--Qwen2.5-7B/snapshots/" 2>/dev/null | sed 's/^/  /'
echo "pip show vllm transformers:"
pip show vllm transformers 2>/dev/null | grep -E '^(Name|Version):' | sed 's/^/  /'
python -c "import vllm, transformers, torch; print(f'  vllm={vllm.__version__} transformers={transformers.__version__} torch={torch.__version__}')" 2>/dev/null
echo "------------------------"

# Unique port per job so a lingering server never collides.
VLLM_PORT=$((8000 + (SLURM_JOB_ID % 1000)))
echo "vLLM port: $VLLM_PORT"

# Seed handling IDENTICAL to the logprob job: fresh random seed per job launch.
RANDOM_SEED=$(($(date +%s%N) % 2147483647))
echo "Using random seed: $RANDOM_SEED"

vllm serve Qwen/Qwen2.5-7B \
    --port $VLLM_PORT \
    --tensor-parallel-size 2 \
    --gpu-memory-utilization 0.9 \
    --dtype bfloat16 \
    --max-model-len 4096 \
    --disable-log-requests \
    --seed $RANDOM_SEED \
    > logs/vllm_qwen25_7b_lp_temp${TEMP}_run${RUN_INDEX}_${SLURM_JOB_ID}.log 2>&1 &
VLLM_PID=$!
echo "vLLM PID: $VLLM_PID"

echo "Waiting for vLLM server (model load ~10-15 min)..."
MAX_WAIT=1800; ELAPSED=0
while ! curl -s http://localhost:$VLLM_PORT/health > /dev/null 2>&1; do
    if [ $ELAPSED -ge $MAX_WAIT ]; then
        echo "ERROR: vLLM did not start within ${MAX_WAIT}s"; kill $VLLM_PID 2>/dev/null; exit 1
    fi
    sleep 10; ELAPSED=$((ELAPSED + 10))
    if [ $((ELAPSED % 60)) -eq 0 ]; then echo "  waiting... ($((ELAPSED/60)) min)"; fi
done
echo "vLLM ready."

python scripts/base_runs/test_base_model_logprobs.py \
    --model-name "Qwen/Qwen2.5-7B" \
    --output-dir "results/base_runs_logprobs/qwen25_7b" \
    --dataset "data/datasets/medqa_focused_1030.json" \
    --vllm-url "http://localhost:$VLLM_PORT" \
    --run-index "$RUN_INDEX" \
    --temperatures "$TEMP"
EXIT=$?

echo "Shutting down vLLM..."; kill $VLLM_PID 2>/dev/null; wait $VLLM_PID 2>/dev/null
echo "Finished at $(date) with exit $EXIT"

# --- Auto commit & push only this run's result file --------------------------
if [ $EXIT -eq 0 ]; then
    echo "Committing result to git..."
    cd /aiau010_scratch/tzs0128/repo/MedQA2026
    git add "results/base_runs_logprobs/qwen25_7b/temp${TEMP}_run${RUN_INDEX}_results.json" \
            "results/base_runs_logprobs/qwen25_7b/temp${TEMP}_run${RUN_INDEX}_checkpoint.json"
    if git commit -m "EXP1 logprob-env: Qwen2.5-7B t=${TEMP} run${RUN_INDEX} (job ${SLURM_JOB_ID})"; then
        git push origin master && echo "Pushed." \
            || echo "WARN: git push failed; commit is local. Flush from login node: git push origin master"
    else
        echo "Nothing new to commit."
    fi
else
    echo "Run exited $EXIT; skipping git commit."
fi

exit $EXIT
