# EXP7 — Hybrid Decision Module

**Priority: MEDIUM-HIGH** — the paper's headline system.

## Why
Combine LLM answer likelihood with symbolic support/violations into a final decision that
also emits a confidence proxy and an evidence trace. This is the "best of both" system the
thesis argues for; its job is to **match or beat the LLM baseline while adding auditability**.

## Prompt to run it
> You are my neuro-symbolic engineer. Implement the hybrid decision module that fuses LLM
> likelihood with EXP3 symbolic support and EXP6 violation counts, emitting a final answer,
> confidence proxy, and evidence trace; evaluate on the focused 1,030-question set.

## Procedure
- Decision function over per-option features: LLM score, symbolic support, violation count,
  grounding coverage. Start simple (weighted sum / small logistic model fit on a dev split),
  then report.
- Use symbolic violations as **penalties/warnings**; optionally revise only when LLM
  confidence is low AND violations are high (gated revision, to avoid the EXP6 revision harm).
- Emit evidence trace: supporting concepts, contradictory concepts, coverage, flags.

## Expected outputs
`results/ns/hybrid/<model>_results.json` with `final_answer`, `confidence_proxy`,
`evidence_trace`, component features per option.

## Analysis plan
- Accuracy vs LLM-only (primary), symbolic-only, UMLS-in-prompt, verifier-rerank, CoVe.
- Per-category gains (heatmap, Figure 4): which categories benefit (BRIEF H3/H7).
- Auditability: fraction of correct answers with a faithful supporting evidence trace.
- Harm accounting: wrong→right vs right→wrong vs baseline.

## Acceptance check
Paired comparison to LLM baseline with CIs; per-category gain heatmap; harm table.

## Fills
`[TBD-EXP7: hybrid accuracy]` Table 3; Figure 4; the main contribution claim.

## Implementation (READY — code written)
See module map + run instructions in `slurm/hybrid/README.md`. GPU-free parts
(CoVe heuristic, rerank, hybrid via logprobs) run on CPU; UMLS-in-prompt and the CoVe LLM
proposer need a vLLM server (7B/14B local on a 4090, 32B on AIAU). Aggregate with
`papers/paper2/analysis/compute_hybrid.py`. Smoke-tested end-to-end on a synthetic UMLS index.
