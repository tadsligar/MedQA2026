# EXP1 — Build the UMLS Index

**Priority: PREREQUISITE.** Everything symbolic depends on this.

## Why
The neuro-symbolic methods need a queryable UMLS index (concepts, semantic types,
definitions, and relations). The README references a prior index with 695,642 relationships,
but no index or build artifact exists in this snapshot. Rebuild it reproducibly.

## Prompt to run it
> You are my biomedical-NLP engineer. Build a reproducible UMLS index for the MedQA2026
> neuro-symbolic pipeline from the UMLS Metathesaurus release.

## Inputs / environment (HPC, not this sandbox)
- UMLS Metathesaurus Full (2025AB recommended): `MRCONSO.RRF` (concepts/terms),
  `MRSTY.RRF` (semantic types), `MRDEF.RRF` (definitions), `MRREL.RRF` (relations).
- Requires a UMLS license (https://uts.nlm.nih.gov). ~6GB raw.

## Procedure
1. Filter MRCONSO to English (`LAT=ENG`), keep CUI ↔ term/alias map; record source (SAB).
2. Load MRSTY → CUI → semantic type(s) (TUI/STY). Tag clinical vs administrative types.
3. Load MRDEF → CUI → definition (optional, for explanations).
4. Load MRREL → (CUI1, REL, RELA, CUI2); keep clinically useful relations
   (e.g., `may_treat`, `may_prevent`, `manifestation_of`, `causes`, `associated_with`,
   `contraindicated_with`, `has_finding`, parent/child `isa`).
5. Persist to SQLite (`data/umls/umls_2025AB_index.db`) with indices on CUI, term (lowercased),
   semantic type, and (CUI1, RELA). Record build manifest (release, counts, date).

## Expected outputs
- `data/umls/umls_2025AB_index.db` and `data/umls/build_manifest.json`
  (n_concepts, n_terms, n_relations, n_semantic_types, release).

## Acceptance check
Report indexed counts (target: relations on the order of the README's ~700k). Spot-check
that `myocardial infarction` resolves to its CUI and that `may_treat` edges exist for a known
drug→disease pair.

## Fills
Infrastructure for EXP2–EXP10; Reproducibility appendix (environment/index manifest).

## Implementation (READY — code written)
- **Download (optional):** `scripts/umls/download_umls.py` (reads `$UMLS_API_KEY`).
- **Index builder:** `scripts/umls/build_umls_index.py` — MRCONSO/MRSTY/MRDEF/MRREL → SQLite
  (`data/umls/umls_2025AB_index.db`), configurable `--rela`. CPU-only.
- **CPU SLURM:** `slurm/symbolic/run_symbolic_core.sbatch` (builds index, grounds, scores, analyzes).
