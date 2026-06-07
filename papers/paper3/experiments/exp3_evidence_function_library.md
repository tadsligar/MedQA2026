# EXP3 — Evidence-Function Library

**Priority: CORE.** These are the agent's callable "tools."

## Why
Each evidence function returns a structured support/contradiction signal for candidates. The
library is what makes reasoning adaptive and auditable. Build and unit-test all 16 before
wiring the controller.

## Prompt to run it
> You are my neuro-symbolic engineer. Implement and unit-test the evidence-function library:
> each function takes the parsed case + candidates + UMLS grounding and returns per-candidate
> support/contradiction scores with a short justification.

## Functions (name · uses · applies-to)
1. `check_demographic_plausibility` (UMLS+LLM · all)
2. `check_symptom_support` (UMLS+LLM · Dx, Findings)
3. `check_lab_support` (LLM · Dx, Workup)
4. `check_temporal_consistency` (LLM · all)
5. `check_pathophysiology_chain` (UMLS+LLM · Mechanism)
6. `check_disease_finding_relation` (UMLS `manifestation_of`/`has_finding` · Dx, Findings)
7. `check_treatment_indication` (UMLS `may_treat` · Treatment)
8. `check_treatment_contraindication` (UMLS `contraindicated_with` · Treatment)
9. `check_next_best_test` (LLM+guideline heuristic · Workup)
10. `check_mechanism_consistency` (UMLS+LLM · Mechanism)
11. `check_answer_semantic_type` (UMLS semantic-type · all)
12. `check_negation_conflict` (UMLS polarity · all)
13. `check_distractor_similarity` (embedding · all)
14. `estimate_grounding_coverage` (UMLS · all)
15. `estimate_evidence_redundancy` (bookkeeping · all)
16. `check_contradictions` / `summarize_supporting|contradictory_evidence` (UMLS+LLM · all)

Each: defined input/output schema, applicable categories, UMLS/LLM/both, a worked example,
and known failure modes (documented for the failure taxonomy).

## Expected outputs
`src/agent/evidence_functions.py` + `results/agent/evidence/unit_tests.json` (per-function
sanity outputs on a few questions).

## Acceptance check
All 16 functions return well-formed per-candidate scores; unit tests pass; per-function
example documented for Table 2.

## Fills
`[TBD-EXP3]` Table 2 (evidence-function library); tools for the controller (EXP4).

## Implementation (READY — code written)
Agent code in `neurosymbolic/agent/src/` (`evidence_functions.py`, `agent.py`), reusing Paper 2
grounding/verifiers. Run via `slurm/agent/run_agent_cpu.sbatch` (GPU-free; policies, belief
variants, 14 ablations, budget sweep) or `run_agent_llm.sbatch` (LLM-planner). Aggregate with
`papers/paper3/analysis/compute_agent.py` (vs LLM 73.4% / oracle 86.0%). See `slurm/agent/README.md`.
Smoke-tested end-to-end on a synthetic UMLS index across all policies + ablations.
