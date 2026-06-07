# EXP2 — Candidate Hypothesis Generator

**Priority: PREREQUISITE.**

## Why
Turn the four answer choices into typed candidate hypotheses appropriate to the category, so
evidence functions can score them consistently. (In MedQA the candidate set is given by the
options — a simplification vs open differential diagnosis, noted in Limitations.)

## Prompt to run it
> You are my clinical-NLP engineer. Convert each question's answer choices into typed candidate
> hypotheses according to its reasoning category, grounded to UMLS where possible.

## Procedure
- Diagnosis → candidate diseases; Mechanism → causal mechanisms; Treatment → interventions;
  Next Step/Workup → diagnostic actions; Clinical Findings → expected manifestations.
- Ground each candidate to UMLS CUIs + semantic types (reuse Paper 2 EXP2 grounding).
- Flag candidates that fail to ground (concept-mismatch risk).

## Expected outputs
`results/agent/candidates/candidates.jsonl`
(`question_id, category, candidates:[{option, text, type, cui, sty, grounded}]`).

## Analysis plan
- Candidate grounding rate by category; unground rate (links to Paper 2 concept-mismatch).

## Acceptance check
Typed, (mostly) grounded candidates for all 1,030 questions; grounding rate reported.

## Fills
Inputs to all scoring/belief steps; candidate grounding rate in Table 8.

## Implementation (READY — code written)
Agent code in `neurosymbolic/agent/src/` (`evidence_functions.py`, `agent.py`), reusing Paper 2
grounding/verifiers. Run via `slurm/agent/run_agent_cpu.sbatch` (GPU-free; policies, belief
variants, 14 ablations, budget sweep) or `run_agent_llm.sbatch` (LLM-planner). Aggregate with
`papers/paper3/analysis/compute_agent.py` (vs LLM 73.4% / oracle 86.0%). See `slurm/agent/README.md`.
Smoke-tested end-to-end on a synthetic UMLS index across all policies + ablations.
