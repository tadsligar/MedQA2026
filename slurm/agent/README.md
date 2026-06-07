# Paper 3 — agentic neuro-symbolic reasoner

Reuses Paper 2's UMLS index, grounding, candidate analyses, and verifiers. The agent runs
**GPU-free** when given the Paper 1 EXP1 logprob run as its LLM signal; only the LLM-planner
policy needs a live model.

## Prerequisites
- `data/umls/umls_2025AB_index.db` (from `slurm/symbolic`).
- `results/base_runs_logprobs/qwen25_32b/temp0.0_run1_results.json` (Paper 1 EXP1 → `option_probs`).
  Without it the agent falls back to a uniform LLM prior (symbolic-only mode).

## GPU-free: policies, belief variants, ablations, budget sweep
```bash
sbatch slurm/agent/run_agent_cpu.sbatch      # or run python -m ... locally
```
Produces under `results/agent/`:
- `eval/full_{fixed,category,uncertainty,utility,redundancy}_results.json` (EXP4 policies)
- `eval/belief_{additive,weighted,bayesian}_results.json` (EXP5)
- `ablations/<ablation>_results.json` × 14 (EXP9)
- `budget/B{1,2,3,4,6,8}_results.json` (EXP9 budget sweep)
- `papers/paper3/tables/agent_{method_comparison,category,function_selection}.csv`

## LLM-planner policy (needs vLLM)
```bash
sbatch slurm/agent/run_agent_llm.sbatch                          # Qwen2.5-14B, gpu:2
MODEL=Qwen/Qwen2.5-32B TP=2 sbatch slurm/agent/run_agent_llm.sbatch
```
Local 4090: `vllm serve Qwen/Qwen2.5-14B` then
`python -m neurosymbolic.agent.src.agent --policy llm_planner --vllm-url http://localhost:8000 ...`.

## Single-question / interactive
```bash
python -m neurosymbolic.agent.src.agent \
    --index data/umls/umls_2025AB_index.db \
    --llm-logprobs results/base_runs_logprobs/qwen25_32b/temp0.0_run1_results.json \
    --policy utility --belief weighted --budget 6 \
    --output results/agent/eval/full_utility_results.json
```
Each result record carries an `evidence_trace` (per-step function, deltas, belief), `flags`,
`n_steps`, and `confidence` — the interpretable trace for case studies (EXP10) and Figures 4/9.

## Analysis targets (verified seeds)
`compute_agent.py` positions every system against the **LLM-only baseline 73.4%** and the
**oracle ceiling 86.0%**, with McNemar vs the baseline and evidence-efficiency (avg steps).

## Module map
- `neurosymbolic/agent/src/evidence_functions.py` — 16 evidence functions (EXP3)
- `neurosymbolic/agent/src/agent.py` — controller, policies A–G, Algorithm 1, belief, ablations
- reuses `neurosymbolic/{umls_verifier,chain_of_verification}/src/*`
