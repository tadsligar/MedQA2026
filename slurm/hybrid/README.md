# Paper 2 EXP4–EXP7 — hybrid / verification layer

Builds on the symbolic core (run `slurm/symbolic` first → `data/umls/umls_2025AB_index.db`).
Split into a **GPU-free** job and an **LLM** job.

## Prerequisites
- UMLS index: `data/umls/umls_2025AB_index.db` (from `slurm/symbolic/run_symbolic_core.sbatch`).
- For EXP5 rerank & EXP7 hybrid (logprob signal): the Paper 1 EXP1 logprob run
  `results/base_runs_logprobs/qwen25_32b/temp0.0_run1_results.json` (`slurm/logprobs`).

## GPU-free part (CoVe heuristic, rerank, hybrid, aggregate)
```bash
sbatch slurm/hybrid/run_hybrid_cpu.sbatch        # or run the python -m commands locally
```
Produces:
- `results/ns/cove/heuristic_{baseline,verify_only,revision}_results.json` (EXP6) — reproduce
  the README's "verify-only helps, revision can harm" pattern on the full balanced set.
- `results/ns/verifier_rerank/qwen25_32b_results.json` (+ `_lambda_sweep.json`) (EXP5).
- `results/ns/hybrid/qwen25_32b_results.json` (EXP7) — fused LLM+symbolic+verifier decision
  with an evidence trace and confidence proxy.
- `papers/paper2/tables/table3_method_comparison.csv` + `table4_method_category.csv`.

## LLM part (UMLS-in-prompt, CoVe LLM proposer)
```bash
sbatch slurm/hybrid/run_hybrid_llm.sbatch                       # default Qwen2.5-14B, gpu:2
MODEL=Qwen/Qwen2.5-32B KEY=qwen25_32b TP=2 sbatch slurm/hybrid/run_hybrid_llm.sbatch
```
Local 4090 (7B/14B): start `vllm serve Qwen/Qwen2.5-14B` then run the `python -m ...` lines
with `--vllm-url http://localhost:8000` (drop SLURM). 32B → AIAU.
Produces `results/ns/umls_in_prompt/<key>_results.json` (EXP4) and
`results/ns/cove/llm_{verify_only,revision}_results.json` (EXP6, LLM proposer).

## Then aggregate
`papers/paper2/analysis/compute_hybrid.py` auto-discovers every method file and builds the
master comparison (overall + per category, McNemar vs the LLM-only baseline). Fills
`[TBD-EXP4..EXP7]` in `papers/paper2/DRAFT.md` Tables 3–5.

## Module map
- `neurosymbolic/umls_verifier/src/verifiers.py` — 5 symbolic verifiers
- `neurosymbolic/chain_of_verification/src/cove.py` — CoVe pipeline (EXP6)
- `neurosymbolic/umls_verifier/src/umls_in_prompt.py` — EXP4
- `neurosymbolic/umls_verifier/src/verifier_rerank.py` — EXP5
- `neurosymbolic/umls_verifier/src/hybrid_decision.py` — EXP7
- `neurosymbolic/umls_verifier/src/llm_client.py` — shared vLLM client
