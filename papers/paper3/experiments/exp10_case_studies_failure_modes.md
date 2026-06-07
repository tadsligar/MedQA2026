# EXP10 — Case Studies + Failure-Mode Annotation

**Priority: MEDIUM** (high for journal). The qualitative/interpretability evidence.

## Why
Evidence traces are a core claimed benefit; case studies show them, and a failure-mode
taxonomy characterizes where agentic neuro-symbolic reasoning breaks (BRIEF §19/§20).

## Prompt to run it
> You are my clinical-AI analyst. Produce annotated case studies of the agent's evidence traces
> and label agent failures using the taxonomy below.

## Case studies (5, per BRIEF §19)
1. Diagnosis where adaptive evidence selection improves the answer.
2. Treatment where contraindication checking prevents a wrong answer.
3. Workup where next-best-test reasoning helps.
4. Mechanism where pathophysiology-chain reasoning helps.
5. Failure where the agent selects misleading evidence or UMLS grounding fails.
For each: show vignette, choices, evidence calls, belief updates, contradiction flags, final
answer; state the lesson. Draw from the 144 hard-core IDs where relevant.

## Failure-mode taxonomy (label agent errors)
category misclassification · bad candidate representation · grounding error · concept mismatch ·
missing relation · overweighting symbolic · overweighting LLM · redundant-evidence loop ·
misleading evidence function · contradiction FP · contradiction FN · belief instability ·
premature stopping · excessive gathering · revision harm · wrong answer despite good trace ·
right answer with unfaithful trace.

## Expected outputs
`results/agent/cases/case_studies.md` and `results/agent/failures/annotations.csv`
(`question_id, failure_modes, notes`); double-annotate a subset for κ.

## Analysis plan
- Failure-mode distribution; most common modes; faithful-vs-correct cross-tab
  (right/wrong × faithful/unfaithful trace).

## Acceptance check
5 worked case studies; failure-mode table with counts + κ on the double-annotated subset.

## Fills
`[TBD-EXP10]` Table 9 (failure taxonomy); Figure 9 (example evidence trace); §10 case studies.
> Manual/clinical judgment — route traces to a qualified reviewer; do not fabricate labels.

## Implementation (READY — code written)
Agent code in `neurosymbolic/agent/src/` (`evidence_functions.py`, `agent.py`), reusing Paper 2
grounding/verifiers. Run via `slurm/agent/run_agent_cpu.sbatch` (GPU-free; policies, belief
variants, 14 ablations, budget sweep) or `run_agent_llm.sbatch` (LLM-planner). Aggregate with
`papers/paper3/analysis/compute_agent.py` (vs LLM 73.4% / oracle 86.0%). See `slurm/agent/README.md`.
Smoke-tested end-to-end on a synthetic UMLS index across all policies + ablations.
