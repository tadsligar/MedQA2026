# EXP6 — Hard-Core Expert Clinical Review

**Priority: MEDIUM-LOW** (see `../ANALYSIS_GAPS.md` C-6).

## Why this matters
144 questions (14% of the set) are missed by **all 5 models** at t=0.0, skewed toward
Clinical Findings. A small expert review establishes *why*: genuinely hard reasoning vs
ambiguous/mislabeled items. This strengthens both the dataset-quality and error-analysis
sections and guards against "your hard core is just noise."

## Prompt to run it
> You are my clinical-reasoning reviewer. For each hard-core MedQA item (missed by all five
> base models), classify the failure type and flag any ambiguous or mislabeled questions.

## Inputs
- `../error_samples.md` (3 examples per category already extracted) plus the full hard-core
  list: regenerate the all-5-wrong question_ids from `compute_stats.py` logic, then pull
  full text/options/gold from `data/datasets/medqa_focused_1030.json`.
- The error taxonomy from `BRIEF.md` §13 (misread finding, incorrect diagnosis, mechanism
  confusion, treatment-guideline confusion, next-step sequencing, distractor attraction,
  overgeneralization, ignored age/sex/risk, temporal reasoning, pharmacology confusion).

## Procedure
- For each of the 144 items, a clinically-trained reviewer (or careful LLM-assisted pass
  with human confirmation) assigns: (a) primary error type, (b) item-quality flag
  {clean / ambiguous / likely-mislabeled-category / disputed-key}.
- Two reviewers on a subset (≥30 items) to report inter-rater agreement (Cohen's κ).

## Expected outputs
`results/hardcore_review/hardcore_annotations.csv`
(`question_id, category, error_type, quality_flag, reviewer, notes`).

## Analysis plan
1. Error-type distribution over the hard core (which failure modes dominate per category).
2. % flagged ambiguous/mislabeled — if low, the hard core is genuinely hard (good).
3. Cohen's κ on the double-annotated subset.

## Fills in DRAFT.md
`[TBD-EXP6: hard-core error-type breakdown]`, the §6.x Error Analysis table, a
dataset-quality sentence in §3.

## Acceptance check
All 144 items annotated; error-type table and ambiguity rate reported; κ on the overlap set.
> Note: this is a manual/clinical task — do not fabricate clinical judgments; route to a
> qualified reviewer.
