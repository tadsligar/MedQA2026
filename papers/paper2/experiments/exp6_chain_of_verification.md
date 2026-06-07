# EXP6 — Chain-of-Verification (CoVe)

**Priority: HIGH** — the verification pillar and explainability story.

## Why
Implements the propose → ground → verify → (revise) → decide pipeline with five symbolic
verifiers. The README's anecdote (heuristic 21% → verify-only 29% → with-revision 28%) must
be reproduced on the full balanced set with proper statistics, and extended to an LLM
proposer (README flags LLM overconfidence).

## Prompt to run it
> You are my neuro-symbolic engineer. Implement a UMLS-grounded Chain-of-Verification
> pipeline with five symbolic verifiers and evaluate verify-only vs with-revision on the
> focused 1,030-question set, for both a heuristic and an LLM proposer.

## Procedure
1. **Propose**: generate a structured analysis per question (proposers: heuristic; LLM, e.g.
   Qwen2.5 14B) producing, per option, a support/contradiction list and an answer.
2. **Ground**: map analysis claims to CUIs (EXP2).
3. **Verify** (5 verifiers, count violations per option/analysis):
   type incompatibility · demographic implausibility · low grounding coverage ·
   polarity/negation conflict · internal contradiction.
4. **Revise** (optional arm): re-propose when violations exceed a threshold.
5. **Decide**: pick the option minimizing violations / maximizing support.

## Conditions
heuristic-baseline · heuristic+verify-only · heuristic+revision ·
LLM-baseline · LLM+verify-only · LLM+revision.

## Expected outputs
`results/ns/cove/<proposer>_<mode>_results.json` with per-question
`violations:{type,demographic,coverage,polarity,contradiction}`, `n_revisions`,
`final_answer`, and the structured analysis (for explainability examples).

## Analysis plan
- Accuracy per condition with bootstrap CIs + McNemar (verify-only vs baseline; revision vs
  verify-only). Reproduce/qualify the README's +38% / −3% pattern.
- Verifier firing rates and which verifier most associates with corrected errors.
- LLM-proposer overconfidence: confidence vs accuracy (calibration).

## Acceptance check
All six conditions evaluated with CIs; explicit verify-only-vs-revision verdict; verifier
firing-rate table.

## Fills
`[TBD-EXP6: CoVe accuracies]` Tables 3/5; verification metrics; case studies (§17); the
"verification helps, revision can harm" result.

## Implementation (READY — code written)
See module map + run instructions in `slurm/hybrid/README.md`. GPU-free parts
(CoVe heuristic, rerank, hybrid via logprobs) run on CPU; UMLS-in-prompt and the CoVe LLM
proposer need a vLLM server (7B/14B local on a 4090, 32B on AIAU). Aggregate with
`papers/paper2/analysis/compute_hybrid.py`. Smoke-tested end-to-end on a synthetic UMLS index.
