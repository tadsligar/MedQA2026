# Paper 2 EXP1–EXP3 — UMLS symbolic core (CPU; no GPU)

Builds the UMLS index, grounds the dataset, runs the pure-symbolic scorers, and analyzes them
vs the verified LLM-only baseline. **No GPU needed** — runs on a CPU node or your local machine.

## Prerequisite: UMLS data (licensed; not in git)
1. Sign in at uts.nlm.nih.gov and download the **Metathesaurus Full Subset**
   (`umls-2025AB-metathesaurus-full.zip`, ~5.2 GB). Keep your API key in `$UMLS_API_KEY`
   if using `scripts/umls/download_umls.py`; never commit it.
2. Unzip into `data/umls/` → `data/umls/META/*.RRF`. (`data/umls/` is gitignored.)

## Run (AIAU)
```bash
cd /aiau010_scratch/tzs0128/projects/MedQA2026
# optional download (or place the zip manually):
export UMLS_API_KEY=...        # do not hardcode
python scripts/umls/download_umls.py --release 2025AB --out data/umls && \
  unzip -o data/umls/umls-2025AB-metathesaurus-full.zip -d data/umls/

sbatch slurm/symbolic/run_symbolic_core.sbatch
# override paths if your layout differs:
#   META_DIR=data/umls/META INDEX=data/umls/umls_2025AB_index.db sbatch ...
```

## What it produces
- `data/umls/umls_2025AB_index.db` — SQLite index (concepts, terms, semantic types,
  definitions, selected relations). Build prints concept/term/relation counts.
- `results/ns/grounding/focused_1030.jsonl` — per-question stem+option CUIs, polarity,
  grounding coverage (EXP2).
- `results/ns/symbolic/{overlap,relation,tfidf}_results.json` — base-run-schema results (EXP3).
- `papers/paper2/tables/exp3_symbolic_{overall,category}.csv` — accuracy vs random and vs the
  Qwen2.5-32B LLM baseline (Wilson CIs + McNemar).

## Pipeline steps (also runnable individually, locally)
```bash
python scripts/umls/build_umls_index.py --meta-dir data/umls/META --output data/umls/umls_2025AB_index.db
python -m neurosymbolic.umls_verifier.src.grounding --index data/umls/umls_2025AB_index.db
python -m neurosymbolic.umls_verifier.src.symbolic_scorer --index data/umls/umls_2025AB_index.db --variant relation --output results/ns/symbolic/relation_results.json
python papers/paper2/analysis/compute_symbolic.py
```

Fills `[TBD-EXP2: grounding coverage]` and `[TBD-EXP3: symbolic-only accuracy]` in
`papers/paper2/DRAFT.md`. The relation set kept by the index is configurable via
`build_umls_index.py --rela`.
