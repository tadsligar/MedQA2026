# EXP9 — Ablations + Evidence-Budget Sweep

**Priority: HIGH.** Isolates which mechanisms matter.

## Why
Determines which components carry any agentic gain, and maps the accuracy–budget tradeoff
(diminishing returns), so claims are mechanism-level rather than black-box.

## Prompt to run it
> You are my ML engineer. Run the ablation suite and the evidence-budget sweep on the full
> agent over the focused 1,030-question set.

## Ablations (full agent minus one)
remove UMLS grounding · remove category classifier · fixed evidence sequence (no adaptivity) ·
remove belief updates · remove contradiction auditor · remove redundancy penalty · remove
semantic-type compatibility · remove pathophysiology checker · remove treatment-contraindication
checker · LLM-only evidence functions · symbolic-only evidence functions · random function
selection · full evaluation no adaptivity · adaptive but no final verification · verification
but no revision.

## Budget sweep
Vary evidence budget B = 1..N; record accuracy, mean calls, stopping depth.

## Expected outputs
`results/agent/ablations/<ablation>_results.json`; `results/agent/budget/B{n}_results.json`.

## Analysis plan
- Accuracy delta vs full agent per ablation (paired bootstrap CIs); rank components; flag any
  that *help when removed*.
- Accuracy-vs-budget curve (Figure 5) + diminishing-returns point; ablation chart (Figure 10).
- **Negative-result guidance:** if removing a component doesn't hurt, say so plainly — it
  bounds the contribution and is a legitimate finding.

## Acceptance check
Ablation table with CIs + component ranking; budget curve with identified knee.

## Fills
`[TBD-EXP9]` Table 7; Figures 5 & 10.

## Implementation (READY — code written)
Agent code in `neurosymbolic/agent/src/` (`evidence_functions.py`, `agent.py`), reusing Paper 2
grounding/verifiers. Run via `slurm/agent/run_agent_cpu.sbatch` (GPU-free; policies, belief
variants, 14 ablations, budget sweep) or `run_agent_llm.sbatch` (LLM-planner). Aggregate with
`papers/paper3/analysis/compute_agent.py` (vs LLM 73.4% / oracle 86.0%). See `slurm/agent/README.md`.
Smoke-tested end-to-end on a synthetic UMLS index across all policies + ablations.
