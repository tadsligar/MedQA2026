# EXP3 — Pure Symbolic Scorer (UMLS-only)

**Priority: HIGH** — establishes the "symbolic alone is insufficient" pillar.

## Why
Score answer choices using **only** UMLS, no LLM. Two variants isolate where symbolic value
comes from: (a) concept-overlap, (b) relation-aware. Expected to be weak (README anecdote:
~30%; TF-IDF ~0%) — the paper needs this established rigorously on all 1,030 questions.

## Prompt to run it
> You are my neuro-symbolic engineer. Implement and evaluate a pure-UMLS answer scorer (no
> LLM) on the focused 1,030-question set, in concept-overlap and relation-aware variants.

## Procedure
- **Overlap scorer:** score(option) = weighted overlap between stem concepts and option
  concepts (semantic-type weighted). Pick argmax; random tie-break (seed 42).
- **Relation-aware scorer:** score via category-appropriate relations from EXP1, e.g.
  Diagnosis → `manifestation_of`/`has_finding` between stem findings and option disease;
  Treatment → `may_treat`/`contraindicated_with` between option drug and stem disease.
- Also run a **lexical TF-IDF** baseline (stem vs option text) for reference.

## Expected outputs
`results/ns/symbolic/{overlap,relation,tfidf}_results.json` (Paper 1 schema + `score`,
`n_supporting_relations`, `tie_broken`).

## Analysis plan
- Overall + per-category accuracy vs random (25%) and vs LLM-only baseline (McNemar,
  bootstrap CIs — reuse `papers/paper1/analysis/compute_stats.py` helpers).
- Where (if anywhere) symbolic beats random meaningfully — likely Diagnosis/Mechanism via
  relations more than Treatment/Workup; test this explicitly (BRIEF H7).
- Failure audit on the 144 hard-core IDs.

## Acceptance check
Accuracy with CIs for all three symbolic variants; explicit statement of whether any exceeds
the LLM-only baseline (expected: no).

## Fills
`[TBD-EXP3: symbolic-only accuracy]` in Tables 3 & 4; the §7 symbolic-insufficiency result.

## Implementation (READY — code written)
- **Scorer:** `neurosymbolic/umls_verifier/src/symbolic_scorer.py` (`--variant overlap|relation|tfidf`),
  emits base-run schema.
- **Analysis (GPU-free):** `papers/paper2/analysis/compute_symbolic.py` → `tables/exp3_symbolic_*.csv`
  (accuracy vs random + vs Qwen2.5-32B LLM baseline, Wilson CIs, McNemar).
- **Run everything:** `slurm/symbolic/run_symbolic_core.sbatch` (see `slurm/symbolic/README.md`).
- Smoke-tested end-to-end on a synthetic RRF index (build → ground → relation-score).
