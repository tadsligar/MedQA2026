# EXP10 — Ablation Studies

**Priority: MEDIUM** — isolates which symbolic components matter (BRIEF §16).

## Why
Determines which parts of the pipeline carry the gains, so claims are about *specific*
mechanisms rather than the system as a black box.

## Prompt to run it
> You are my neuro-symbolic engineer. Run the ablation suite on the best hybrid/CoVe system,
> removing one component at a time, on the focused 1,030-question set.

## Ablations (each = full system minus one piece)
- remove semantic-type filtering
- remove UMLS relations (concepts only)
- relations only (no concept overlap)
- remove contradiction detector
- remove demographic-plausibility verifier
- remove grounding-coverage scoring
- remove category-specific scoring (one-size-fits-all)
- UMLS-in-prompt but no verifier (= EXP4)
- verifier but no revision (= EXP6 verify-only)
- verifier with revision (= EXP6 revision)

## Expected outputs
`results/ns/ablations/<ablation>_results.json` (standard schema + which component removed).

## Analysis plan
- Accuracy delta vs full system for each ablation, with paired bootstrap CIs.
- Rank components by contribution; flag any that *hurt* when present.
- Per-category sensitivity (does category-specific scoring matter most for Treatment?).

## Acceptance check
Ablation table with deltas and CIs; explicit ranking of component importance.

## Fills
`[TBD-EXP10: ablation table]` Table 7; the mechanism-level claims in §9.
