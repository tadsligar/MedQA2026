#!/bin/bash -l
#SBATCH --job-name=agent_cpu
#SBATCH --partition=general
#SBATCH --time=12:00:00
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --output=logs/agent_cpu_%j.out
#SBATCH --error=logs/agent_cpu_%j.err

# Paper 3 EXP4/5/8/9 -- GPU-FREE agent (LLM signal from Paper 1 EXP1 logprobs).
# Prereqs: data/umls/umls_2025AB_index.db (slurm/symbolic) and the logprob run.
cd /aiau010_scratch/tzs0128/projects/MedQA2026
source ~/.bashrc; conda activate medqa
INDEX=${INDEX:-data/umls/umls_2025AB_index.db}
LOGP=${LOGP:-results/base_runs_logprobs/qwen25_32b/temp0.0_run1_results.json}
A="python -m neurosymbolic.agent.src.agent --index $INDEX --llm-logprobs $LOGP"
mkdir -p logs results/agent/eval results/agent/ablations results/agent/budget

# EXP4: policy comparison (full agent under each selection policy)
for POL in fixed category uncertainty utility redundancy; do
  $A --policy $POL --belief weighted --budget 6 \
     --output results/agent/eval/full_${POL}_results.json
done

# EXP5: belief-update variants (utility policy)
for B in additive weighted bayesian; do
  $A --policy utility --belief $B --budget 6 \
     --output results/agent/eval/belief_${B}_results.json
done

# EXP9: ablations (full agent minus one component)
for ABL in none no_umls no_category fixed_sequence no_belief_update no_contradiction \
           no_redundancy no_semtype no_pathophys no_contraindication \
           symbolic_only_functions random_selection no_adaptivity no_final_verify; do
  $A --policy utility --belief weighted --budget 6 --ablation $ABL \
     --output results/agent/ablations/${ABL}_results.json
done

# EXP9: evidence-budget sweep
for B in 1 2 3 4 6 8; do
  $A --policy utility --belief weighted --budget $B \
     --output results/agent/budget/B${B}_results.json
done

python papers/paper3/analysis/compute_agent.py
echo "Done $(date)"
