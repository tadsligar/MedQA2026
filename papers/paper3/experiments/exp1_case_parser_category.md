# EXP1 — Case Parser + Reasoning-Category Classifier

**Priority: PREREQUISITE.**

## Why
The agent needs a structured representation of each vignette and the reasoning category to
pick a policy. Category classification quality bounds any category-specific gains, so its
accuracy must be measured (against the dataset's `validated_category`).

## Prompt to run it
> You are my clinical-NLP engineer. Implement (a) a case parser that extracts structured
> clinical elements from a MedQA vignette and (b) a reasoning-category classifier, and
> evaluate the classifier against gold categories on the focused 1,030-question set.

## Procedure
- **Parser:** extract age, sex, chief complaint, symptoms, signs, labs, imaging, medications,
  risk factors, timing, and explicit negations; record present vs missing evidence types.
  Reuse `metamap_phrases` as candidate spans.
- **Classifier:** predict one of the 5 categories (allow multi-label) via LLM and/or features;
  evaluate accuracy, per-category F1, confusion matrix vs `validated_category`.

## Expected outputs
`results/agent/parse/cases.jsonl` (structured cases) and
`results/agent/category/preds.csv` (pred vs gold, confidence).

## Analysis plan
- Category-classifier accuracy + confusion matrix (which categories are conflated).
- Downstream sensitivity: how much does a wrong category hurt the full agent? (feeds EXP9
  "sensitivity to category misclassification").

## Acceptance check
Classifier accuracy and confusion matrix reported; parser coverage of evidence fields audited
on a sample.

## Fills
`[TBD-EXP1: category-classifier accuracy/confusion]`; structured cases for EXP2–EXP8.

## Implementation (READY — code written)
Agent code in `neurosymbolic/agent/src/` (`evidence_functions.py`, `agent.py`), reusing Paper 2
grounding/verifiers. Run via `slurm/agent/run_agent_cpu.sbatch` (GPU-free; policies, belief
variants, 14 ablations, budget sweep) or `run_agent_llm.sbatch` (LLM-planner). Aggregate with
`papers/paper3/analysis/compute_agent.py` (vs LLM 73.4% / oracle 86.0%). See `slurm/agent/README.md`.
Smoke-tested end-to-end on a synthetic UMLS index across all policies + ablations.
