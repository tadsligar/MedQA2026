# EXP4 — LLM with UMLS Concepts in Prompt

**Priority: MEDIUM** — the simplest neural+symbolic fusion.

## Why
Tests whether merely *injecting* grounded UMLS concepts/relations into the prompt helps the
LLM, before any explicit verification. A modest or null gain here is itself informative: it
shows grounding must be used as *constraint/verification*, not just context.

## Prompt to run it
> You are my neuro-symbolic engineer. Evaluate an LLM that receives the question plus
> EXP2-grounded UMLS concepts and relevant relations appended to the prompt, on the focused
> 1,030-question set.

## Procedure
- For each question, build an enriched prompt: base question + a compact block of grounded
  stem/option concepts (CUI, preferred name, semantic type) and any category-relevant
  relations from EXP1. Cap added context (~the README's ~3,500-char enrichment).
- Run on ≥2 models (e.g., Qwen2.5 14B and a smaller one), t=0.0; keep extraction identical.
- Control: same model, same prompt **without** the UMLS block (this is the Paper 1 baseline).

## Expected outputs
`results/ns/umls_in_prompt/<model>_results.json` + the enriched prompt template (appendix).

## Analysis plan
- Δ accuracy vs LLM-only baseline, overall and per category (paired McNemar).
- Does enrichment help the hard-core set or only easy items?
- Token-cost overhead vs gain.

## Acceptance check
Paired comparison with p-values; explicit statement of whether enrichment alone helps.

## Fills
`[TBD-EXP4: UMLS-in-prompt accuracy]` in Table 3; Discussion on context-vs-constraint.

## Implementation (READY — code written)
See module map + run instructions in `slurm/hybrid/README.md`. GPU-free parts
(CoVe heuristic, rerank, hybrid via logprobs) run on CPU; UMLS-in-prompt and the CoVe LLM
proposer need a vLLM server (7B/14B local on a 4090, 32B on AIAU). Aggregate with
`papers/paper2/analysis/compute_hybrid.py`. Smoke-tested end-to-end on a synthetic UMLS index.
