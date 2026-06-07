# EXP6 — Redundancy-Aware Evidence Selection (mRMR-style)

**Priority: MEDIUM-HIGH.**

## Why
Translates the source framework's minimum-redundancy maximum-relevance evidence selection to
MedQA: prefer evidence functions that **distinguish the top competing candidates** and avoid
re-running checks that support all options equally. Tests RQ5 (efficiency without accuracy loss).

## Prompt to run it
> You are my ML engineer. Add redundancy-aware (mRMR-style) evidence selection to the agent and
> measure whether it reduces evidence calls without hurting accuracy.

## Procedure
- Relevance: expected belief-margin change between current top-2 candidates if function f is run.
- Redundancy: similarity of f's signal to evidence already gathered.
- Select argmax(relevance − λ·redundancy); sweep λ.
- Compare against policy A (fixed, runs everything) and policy D (utility, no redundancy term).

## Expected outputs
`results/agent/redundancy/lambda{λ}_results.json` (+ per-step relevance/redundancy logs).

## Analysis plan
- Accuracy vs mean #evidence-calls (efficiency frontier) for redundancy-aware vs baselines.
- Diminishing-returns curve: accuracy vs evidence budget (links EXP9).

## Acceptance check
Efficiency frontier plotted; statement of whether redundancy-awareness cuts calls at equal
accuracy.

## Fills
`[TBD-EXP6]` agentic-efficiency Table 6; evidence-efficiency discussion.

## Implementation (READY — code written)
Agent code in `neurosymbolic/agent/src/` (`evidence_functions.py`, `agent.py`), reusing Paper 2
grounding/verifiers. Run via `slurm/agent/run_agent_cpu.sbatch` (GPU-free; policies, belief
variants, 14 ablations, budget sweep) or `run_agent_llm.sbatch` (LLM-planner). Aggregate with
`papers/paper3/analysis/compute_agent.py` (vs LLM 73.4% / oracle 86.0%). See `slurm/agent/README.md`.
Smoke-tested end-to-end on a synthetic UMLS index across all policies + ablations.
