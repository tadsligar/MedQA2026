# EXP5 — UMLS Verifier Reranking

**Priority: MEDIUM.**

## Why
Instead of feeding UMLS to the LLM, use symbolic support to **rerank** the LLM's option
preferences. Tests whether symbolic signal is more useful as a post-hoc filter than as prompt
context (EXP4).

## Prompt to run it
> You are my neuro-symbolic engineer. Use the EXP3 symbolic support scores to rerank the LLM's
> answer-option ranking and evaluate the combined ranker.

## Procedure
- Obtain the LLM's per-option scores (logprobs from Paper 1 EXP1 if available, else verbalized
  ranking). Obtain symbolic support per option (EXP3 relation-aware).
- Combine: `final = (1-λ)·LLM_score + λ·symbolic_score`, normalized; sweep λ ∈ {0.1..0.5}.
- Pick the best λ on a dev split; report on the rest (avoid tuning on test).

## Expected outputs
`results/ns/verifier_rerank/<model>_lambda{λ}_results.json` (+ both component scores per option).

## Analysis plan
- Accuracy vs LLM-only and vs symbolic-only; per category.
- λ sensitivity curve; does any λ>0 beat λ=0 (LLM alone)?
- Item analysis: cases where reranking flips a wrong→right vs right→wrong (revision harm).

## Acceptance check
λ-sweep reported with dev/test split; statement of whether reranking helps and at what λ.

## Fills
`[TBD-EXP5: verifier-rerank accuracy]` in Table 3; revision-harm framing for §9.

## Implementation (READY — code written)
See module map + run instructions in `slurm/hybrid/README.md`. GPU-free parts
(CoVe heuristic, rerank, hybrid via logprobs) run on CPU; UMLS-in-prompt and the CoVe LLM
proposer need a vLLM server (7B/14B local on a 4090, 32B on AIAU). Aggregate with
`papers/paper2/analysis/compute_hybrid.py`. Smoke-tested end-to-end on a synthetic UMLS index.
