# EXP8 — Concept-Mismatch Annotation

**Priority: MEDIUM** — the paper's distinctive analytical contribution (§8).

## Why
The seed analysis shows canonical concepts appear under ≥6 surface forms (e.g., dyspnea: 6
forms across 113 questions; canonical "dyspnea" covers only 28). Turn this into a labeled
taxonomy of concept-mismatch failures grounded in actual symbolic-scorer errors.

## Prompt to run it
> You are my biomedical-NLP annotator. Label concept-mismatch failure types on the questions
> where the symbolic scorer (EXP3) fails, using the taxonomy below.

## Inputs
- EXP3 symbolic failures, especially intersected with the 144 hard-core IDs
  (`../tables/seed_hardcore_ids.json`).
- EXP2 grounding logs (linked vs unlinked mentions).

## Taxonomy (from BRIEF §14) — label each failure with one or more
lexical synonym · clinical paraphrase · granularity · symptom↔diagnosis · mechanism↔disease ·
treatment-indication · lab-value normalization · negation/uncertainty · temporal · relation
sparsity · missing UMLS relation · overly-broad semantic type · overly-narrow mapping ·
answer-choice abstraction.

## Procedure
- For a stratified sample (≥30/category, plus all hard-core symbolic failures), a reviewer
  assigns mismatch type(s) and notes whether an LLM bridges it (and whether the LLM still
  fails). Double-annotate ≥40 items → Cohen's κ.
- Auto-pre-fill candidates where possible (e.g., unlinked mention that has a known synonym in
  the index = lexical/paraphrase mismatch) for reviewer confirmation.

## Expected outputs
`results/ns/concept_mismatch/annotations.csv`
(`question_id, category, mismatch_types, llm_bridges, llm_still_fails, notes`).

## Analysis plan
- Distribution of mismatch types overall and per category; most common failure mode.
- For each type: a MedQA example, effect on symbolic scoring, whether the LLM helps.
- κ on the double-annotated subset.

## Acceptance check
Taxonomy table with counts and ≥1 example per populated type; κ reported.

## Fills
`[TBD-EXP8: concept-mismatch taxonomy]` Table 6, Figure 7; the §8 analysis.
> Manual/clinical judgment — route to a qualified annotator; do not fabricate labels.
