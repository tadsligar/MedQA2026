# EXP4 — Agent Controller + Evidence-Selection Policies

**Priority: CORE.** This is the agent.

## Why
The controller maintains a belief over candidates and chooses the next evidence function under
an evidence budget, then stops adaptively. Comparing selection policies is the paper's central
question (RQ1, RQ3).

## Prompt to run it
> You are my neuro-symbolic engineer. Implement the agent control loop (Algorithm 1) and the
> selection policies A–G, recording an evidence trace per question on the focused 1,030-set.

## Policies to implement & compare
A fixed-order · B category-based · C uncertainty (margin/entropy) · D expected-utility
(info-gain × grounding availability) · E redundancy-aware (mRMR-style) · F LLM-planner ·
G hybrid (symbolic utility + LLM planner).

## Control loop (per Algorithm 1)
init belief → for t in 1..B: estimate uncertainty → select function (policy) → execute →
update belief (EXP5) → append to trace → stop if margin/confidence threshold met → verify (EXP7).

## Expected outputs
`results/agent/runs/<policy>_results.json` with `functions_called`, `n_steps`,
`belief_history`, `evidence_trace`, `final_answer`, `confidence`.

## Analysis plan
- Accuracy per policy vs static baselines and oracle (86.0% ceiling); evidence efficiency
  (mean #calls, stopping depth); function-selection distribution by category (Figure 7).
- Does any adaptive policy (C–G) beat the fixed/category policies (A/B)? (RQ1/RQ3)

## Acceptance check
All policies run end-to-end with traces; accuracy + efficiency table; selection distribution.

## Fills
`[TBD-EXP4]` Figures 3 & 7; policy comparison in Table 4; agentic-efficiency Table 6.

## Implementation (READY — code written)
Agent code in `neurosymbolic/agent/src/` (`evidence_functions.py`, `agent.py`), reusing Paper 2
grounding/verifiers. Run via `slurm/agent/run_agent_cpu.sbatch` (GPU-free; policies, belief
variants, 14 ablations, budget sweep) or `run_agent_llm.sbatch` (LLM-planner). Aggregate with
`papers/paper3/analysis/compute_agent.py` (vs LLM 73.4% / oracle 86.0%). See `slurm/agent/README.md`.
Smoke-tested end-to-end on a synthetic UMLS index across all policies + ablations.
