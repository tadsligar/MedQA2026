#!/usr/bin/env bash
# Paper 2 EXP1-3 — run the UMLS symbolic core LOCALLY (no SLURM, no GPU).
# Run from the repo root:  bash scripts/umls/run_symbolic_core_local.sh
set -euo pipefail

# Resolve repo root (this script lives in scripts/umls/)
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

META_DIR="${META_DIR:-data/umls/META}"
INDEX="${INDEX:-data/umls/umls_2025AB_index.db}"

echo "Repo: $ROOT"
echo "META: $META_DIR   INDEX: $INDEX"

# One-time dependencies (sqlite3 is stdlib; pandas/scipy for analysis):
#   pip install pandas scipy           # or: conda install pandas scipy
python3 -c "import pandas, scipy" 2>/dev/null || {
  echo "Installing pandas/scipy..."; pip install pandas scipy; }

mkdir -p results/ns/grounding results/ns/symbolic

# EXP1: build index (skip if present). ~15-40 min, a few GB of RAM/disk.
if [ ! -f "$INDEX" ]; then
  echo "[EXP1] Building UMLS index from $META_DIR ..."
  python3 scripts/umls/build_umls_index.py --meta-dir "$META_DIR" --output "$INDEX"
else
  echo "[EXP1] $INDEX exists; skipping."
fi

# EXP2: grounding
echo "[EXP2] Grounding 1,030 questions ..."
python3 -m neurosymbolic.umls_verifier.src.grounding \
    --index "$INDEX" \
    --dataset data/datasets/medqa_focused_1030.json \
    --output results/ns/grounding/focused_1030.jsonl

# EXP3: symbolic scorers
for V in overlap relation tfidf; do
  echo "[EXP3] Scoring variant: $V ..."
  python3 -m neurosymbolic.umls_verifier.src.symbolic_scorer \
      --index "$INDEX" \
      --dataset data/datasets/medqa_focused_1030.json \
      --variant "$V" \
      --output results/ns/symbolic/${V}_results.json
done

# Analysis
echo "[analysis] compute_symbolic.py ..."
python3 papers/paper2/analysis/compute_symbolic.py
echo "Done. Tables in papers/paper2/tables/exp3_symbolic_*.csv"
