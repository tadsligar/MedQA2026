# EXP8 — Full-Agent Evaluation vs All Baselines

**Priority: HIGH.** The headline results table.

## Why
Evaluate the complete agent against the full ladder of baselines to answer RQ1/RQ2/RQ7: does
adaptive neuro-symbolic reasoning beat static prompting, and where?

## Prompt to run it
> You are my ML engineer. Evaluate the full adaptive neuro-symbolic agent against all baseline
> and agentic conditions on the focused 1,030-question set, with proper statistics.

## Conditions (BRIEF §11)
Baselines: random; static zero-shot LLM; static CoT; self-consistency; category-prompt-only;
UMLS symbolic-only (Paper 2 EXP3); UMLS-grounded prompt (Paper 2 EXP4); CoVe (Paper 2 EXP6).
Agentic: agent w/o UMLS; +grounding no belief-update; +belief no auditor; +auditor no adaptive
selection; **full agent**; full agent fixed-budget; full agent dynamic-stopping; oracle bound.

## Expected outputs
`results/agent/eval/<condition>_results.json` (standard + agent fields).

## Analysis plan
- Overall + per-category accuracy (Tables 4/5) with bootstrap CIs and McNemar vs static LLM
  and vs CoVe; Holm correction over the comparison family.
- Position results against the verified ceiling: best single 73.4%, oracle 86.0%.
- Category-gain heatmap (Figure 6): where the agent helps (RQ7) — recall the seed shows
  model-routing yields nothing, so any category gain must come from reasoning, not model choice.
- **Anti-overclaim:** if gains are interpretability-only or category-specific, report exactly
  that with CIs; do not headline a non-significant accuracy bump.

## Acceptance check
Full conditions table with CIs + corrected p-values; category heatmap; explicit comparison to
73.4% and 86.0%.

## Fills
`[TBD-EXP8]` Tables 4 & 5; Figure 6; the main contribution claims.

## Implementation (READY — code written)
Agent code in `neurosymbolic/agent/src/` (`evidence_functions.py`, `agent.py`), reusing Paper 2
grounding/verifiers. Run via `slurm/agent/run_agent_cpu.sbatch` (GPU-free; policies, belief
variants, 14 ablations, budget sweep) or `run_agent_llm.sbatch` (LLM-planner). Aggregate with
`papers/paper3/analysis/compute_agent.py` (vs LLM 73.4% / oracle 86.0%). See `slurm/agent/README.md`.
Smoke-tested end-to-end on a synthetic UMLS index across all policies + ablations.
