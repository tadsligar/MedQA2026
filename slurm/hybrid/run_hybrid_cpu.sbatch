#!/bin/bash -l
#SBATCH --job-name=ns_hybrid_cpu
#SBATCH --partition=general
#SBATCH --time=06:00:00
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --output=logs/ns_hybrid_cpu_%j.out
#SBATCH --error=logs/ns_hybrid_cpu_%j.err

# Paper 2 EXP5/EXP6(heuristic)/EXP7 -- GPU-FREE parts.
# Requires: data/umls/umls_2025AB_index.db (build via slurm/symbolic) and, for rerank/hybrid,
# the Paper 1 EXP1 logprob run (results/base_runs_logprobs/qwen25_32b/temp0.0_run1_results.json).
cd /aiau010_scratch/tzs0128/projects/MedQA2026
source ~/.bashrc; conda activate medqa
INDEX=${INDEX:-data/umls/umls_2025AB_index.db}
LOGP=${LOGP:-results/base_runs_logprobs/qwen25_32b/temp0.0_run1_results.json}
mkdir -p logs results/ns/cove results/ns/verifier_rerank results/ns/hybrid

# EXP6 Chain-of-Verification (heuristic proposer): baseline / verify_only / revision
for MODE in baseline verify_only revision; do
  python -m neurosymbolic.chain_of_verification.src.cove \
      --index "$INDEX" --proposer heuristic --mode $MODE \
      --output results/ns/cove/heuristic_${MODE}_results.json
done

# EXP5 verifier reranking (needs logprobs) + EXP7 hybrid (logprobs LLM signal)
if [ -f "$LOGP" ]; then
  python -m neurosymbolic.umls_verifier.src.verifier_rerank \
      --index "$INDEX" --llm-logprobs "$LOGP" \
      --output results/ns/verifier_rerank/qwen25_32b_results.json
  python -m neurosymbolic.umls_verifier.src.hybrid_decision \
      --index "$INDEX" --llm-logprobs "$LOGP" \
      --output results/ns/hybrid/qwen25_32b_results.json
else
  echo "WARN: $LOGP missing -> skipping rerank/hybrid. Run Paper 1 EXP1 first."
fi

python papers/paper2/analysis/compute_hybrid.py
echo "Done $(date)"
