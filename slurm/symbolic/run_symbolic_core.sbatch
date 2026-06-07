#!/bin/bash -l
#SBATCH --job-name=umls_symbolic_core
#SBATCH --partition=general
#SBATCH --time=08:00:00
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --output=logs/umls_symbolic_core_%j.out
#SBATCH --error=logs/umls_symbolic_core_%j.err

# Paper 2 EXP1-3 -- UMLS index build + grounding + pure-symbolic scorers.
# CPU-ONLY (no --gres=gpu). Assumes the Metathesaurus Full Subset is already unzipped to
# data/umls/<release>/META/ (download requires your UMLS license; not committed to git).

cd /aiau010_scratch/tzs0128/projects/MedQA2026
source ~/.bashrc
conda activate medqa
mkdir -p logs results/ns/grounding results/ns/symbolic

META_DIR=${META_DIR:-data/umls/META}
INDEX=${INDEX:-data/umls/umls_2025AB_index.db}

# EXP1: build index (skip if it already exists)
if [ ! -f "$INDEX" ]; then
  echo "Building UMLS index from $META_DIR ..."
  python scripts/umls/build_umls_index.py --meta-dir "$META_DIR" --output "$INDEX"
else
  echo "Index $INDEX exists; skipping build."
fi

# EXP2: grounding logs + coverage
python -m neurosymbolic.umls_verifier.src.grounding \
    --index "$INDEX" \
    --dataset data/datasets/medqa_focused_1030.json \
    --output results/ns/grounding/focused_1030.jsonl

# EXP3: pure-symbolic scorers
for V in overlap relation tfidf; do
  python -m neurosymbolic.umls_verifier.src.symbolic_scorer \
      --index "$INDEX" \
      --dataset data/datasets/medqa_focused_1030.json \
      --variant $V \
      --output results/ns/symbolic/${V}_results.json
done

# Analysis (also fine to run locally afterwards)
python papers/paper2/analysis/compute_symbolic.py
echo "Done $(date)"
