# EXP7 — Verification & Contradiction Auditor

**Priority: HIGH.** Reuses Paper 2's verifiers in the agent loop.

## Why
A final (and optional in-loop) verification pass detects internal contradictions, answer-choice
incompatibilities, unsupported claims, and negation conflicts, producing warning flags and an
error signal. Tests RQ6 (contradiction scores predict wrong answers).

## Prompt to run it
> You are my neuro-symbolic engineer. Integrate Paper 2's symbolic verifiers as the agent's
> auditor: run a verification pass over the chosen answer + evidence trace, emit flags, and test
> whether violation scores predict errors on the focused 1,030-question set.

## Procedure
- Verifiers: semantic-type incompatibility, demographic implausibility, low grounding coverage,
  polarity/negation conflict, internal contradiction (Paper 2 EXP6).
- Two arms: flag-only (no change to answer) vs gated revision (revise only when confidence low
  AND violations high — designed to avoid Paper 2's revision-harm).

## Expected outputs
`results/agent/verify/{flag,revise}_results.json` with `flags`, violation counts, and
pre/post-revision answers.

## Analysis plan
- AUROC/AUPRC: predict agent-answer correctness from violation/coverage features (+ belief
  margin from EXP5). Risk–coverage curve for abstention.
- Revision success vs harm rate (gated vs ungated).
- Verifier precision/recall on a manually labeled sample (links EXP10).

## Acceptance check
Error-prediction AUROC with CI; revision success/harm table; flag rates.

## Fills
`[TBD-EXP7]` Figure 8 (contradiction score vs error prob); verification metrics Table 8.

## Implementation (READY — code written)
Agent code in `neurosymbolic/agent/src/` (`evidence_functions.py`, `agent.py`), reusing Paper 2
grounding/verifiers. Run via `slurm/agent/run_agent_cpu.sbatch` (GPU-free; policies, belief
variants, 14 ablations, budget sweep) or `run_agent_llm.sbatch` (LLM-planner). Aggregate with
`papers/paper3/analysis/compute_agent.py` (vs LLM 73.4% / oracle 86.0%). See `slurm/agent/README.md`.
Smoke-tested end-to-end on a synthetic UMLS index across all policies + ablations.
