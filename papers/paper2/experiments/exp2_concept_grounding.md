# EXP2 — Concept Grounding (Entity Linking)

**Priority: PREREQUISITE.**

## Why
Ground every question stem and answer choice to UMLS concepts, with semantic types, aliases,
confidence, and negation handling. Produces the grounding logs and **grounding-coverage**
metric used everywhere downstream, and the worked grounding example (Figure 2).

## Prompt to run it
> You are my biomedical-NLP engineer. Implement UMLS entity linking that grounds each MedQA
> question stem and each answer choice to CUIs with semantic-type filtering and negation
> detection, logging coverage.

## Procedure
1. Mention detection: use the dataset's `metamap_phrases` as candidate mentions plus a
   tokenizer/n-gram scan of the stem and each option (the seed analysis shows ~35 candidate
   phrases/question, but canonical concepts appear under ≥6 surface forms — link variants,
   not just canonical surfaces).
2. Candidate linking: match mention → CUI via the EXP1 term/alias map (case-insensitive,
   light normalization). Keep top-k candidates with a confidence score.
3. Semantic-type filtering: prefer clinical types (Disease, Sign/Symptom, Pharmacologic
   Substance, Procedure, Finding); down-weight administrative concepts.
4. Negation & uncertainty: detect "no", "denies", "without", "rule out" → flag mention
   polarity (present/absent/uncertain).
5. Record per-question grounding for stem and each option.

## Expected outputs
`results/ns/grounding/<split>.jsonl`, per question:
```
question_id, category,
stem_concepts:   [{mention, cui, sty, conf, polarity}],
option_concepts: {A:[...], B:[...], C:[...], D:[...]},
grounding_coverage:        # fraction of mentions linked to a CUI
answer_choice_grounding_rate # fraction of options with >=1 grounded clinical concept
```

## Analysis plan
- Grounding coverage overall and per category (relate to the seed phrase-density table).
- Linking-failure audit: sample unlinked mentions → seeds the concept-mismatch taxonomy.

## Acceptance check
Coverage reported with per-category breakdown; a worked example (one question with stem +
option CUIs and polarities) exported for Figure 2.

## Fills
`[TBD-EXP2: grounding coverage table]`, Figure 2 (grounding example), inputs to EXP3–EXP10.

> Note: this is the **Paper 2** EXP2 (UMLS grounding). The **Paper 1** EXP2 (instruct
> comparison) is a different experiment with its own code — see `papers/paper1/experiments/`.

## Implementation (READY — code written)
- **Accessor:** `neurosymbolic/umls_verifier/src/umls_index.py`.
- **Grounding:** `neurosymbolic/umls_verifier/src/grounding.py` (metamap-phrase + n-gram linking,
  semantic-type preference, negation/uncertainty polarity, coverage). Run via the CPU SLURM job.
