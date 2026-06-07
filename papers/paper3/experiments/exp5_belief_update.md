# EXP5 — Belief-Update Formulations

**Priority: CORE.**

## Why
How evidence changes candidate scores determines accuracy and calibration. Compare transparent
formulations; start simple. Motivated by the seed result that inter-model *agreement* predicts
correctness (5-agree 83.5% → 2-agree 23.9%) — belief margin should carry similar signal.

## Prompt to run it
> You are my ML engineer. Implement and compare belief-update formulations inside the agent on
> the focused 1,030-question set, reporting accuracy and calibration of the resulting margin.

## Formulations
A. additive: `score += support − contradiction`
B. weighted neuro-symbolic: `score = LLM + α·support − β·contradiction + γ·grounding_conf`
   (**recommended first**; tune α,β,γ on a dev split)
C. Bayesian-style: prior over candidates × evidence likelihood
D. learning-to-rank over evidence features (future-work-leaning)
E. calibration-aware confidence: combine margin, coverage, contradiction flags

## Expected outputs
`results/agent/belief/<formulation>_results.json` (+ `belief_history`, final `margin`).

## Analysis plan
- Accuracy per formulation; calibration of belief margin (reliability/ECE).
- Margin vs correctness curve — compare to the seed agreement curve.
- Recommend one formulation for the main results; note others as ablations/future work.

## Acceptance check
≥3 formulations evaluated with dev/test split; calibration of margin reported.

## Fills
`[TBD-EXP5]` Figure 4 (belief update over candidates for one example); belief design in §6.

## Implementation (READY — code written)
Agent code in `neurosymbolic/agent/src/` (`evidence_functions.py`, `agent.py`), reusing Paper 2
grounding/verifiers. Run via `slurm/agent/run_agent_cpu.sbatch` (GPU-free; policies, belief
variants, 14 ablations, budget sweep) or `run_agent_llm.sbatch` (LLM-planner). Aggregate with
`papers/paper3/analysis/compute_agent.py` (vs LLM 73.4% / oracle 86.0%). See `slurm/agent/README.md`.
Smoke-tested end-to-end on a synthetic UMLS index across all policies + ablations.
