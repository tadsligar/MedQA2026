# Paper 4 — Results (v2 official-competency labeling, full 12,723)

Labels: `results/reasoning_ops/op_labels_v2.jsonl` (gpt-5.4-mini, lead-in+options, v2 rubric rules-ON;
reliability κ=0.83 / MK-vs-DX κ=0.88, see VALIDATION.md). Accuracy = full base runs, t=0.0,
majority of 3 runs. Table: `tables/competency_accuracy_v2.csv`.

## Distribution (natural)
DX 4551 (35.8%) · MK 4323 (34.0%) · MGMT 3359 (26.4%) · PBL 316 · PROF 88 · COMM 68 · SBP 18.
The three clinical competencies (MK/DX/MGMT) cover ~96%; non-clinical cells are small.

## Per-competency accuracy (%)
| model | MK | DX | MGMT | COMM | PROF | SBP | PBL | MK−DX |
|---|---|---|---|---|---|---|---|---|
| OLMo-3 7B  | 38.9 | 39.0 | 41.2 | 51.5 | 44.3 | 61.1 | 46.8 | −0.1 |
| OLMo-3 32B | 51.2 | 52.5 | 51.5 | 67.6 | 59.1 | 77.8 | 59.2 | −1.3 |
| Qwen2.5 7B | 52.3 | 54.5 | 53.6 | 69.1 | 56.8 | 66.7 | 58.2 | −2.2 |
| Qwen2.5 14B| 59.7 | 62.0 | 59.9 | 77.9 | 63.6 | 72.2 | 65.8 | −2.3 |
| Qwen2.5 32B| 65.6 | 68.2 | 66.4 | 82.4 | 75.0 | 66.7 | 71.8 | −2.6 |

## Findings
1. **Diagnosis (DX) is the easiest clinical competency; Medical Knowledge (MK) the hardest.**
   MK < DX in **5/5** models. Two-proportion z-test (MK vs DX): significant for all three Qwen
   (p=0.038, 0.027, 0.0093), n.s. for OLMo. The gap **grows monotonically with Qwen scale**
   (−2.2 → −2.3 → −2.6 pp). MGMT also sits just below DX (marginal for larger Qwen).
2. **This inverts the original hypothesis.** We expected forward/mechanistic (≈MK) to be *easier*
   than backward/diagnostic (≈DX); the data show MK is *harder*, and increasingly so with scale —
   i.e., scaling improves pattern-style diagnosis faster than foundational-science application.
3. **Magnitude is modest** (~2–3 pp). Reasoning competency explains only a small share of accuracy
   variance — consistent with the MCQ recall-confound — but the MK-deficit is a real, directional,
   scale-dependent effect on a reliable axis (not the noise-confounded null of the R/F/B attempt).
4. Non-clinical competencies (COMM/PROF/SBP) show higher accuracy than clinical ones, but n is
   small (18–88); treat as suggestive only.

## Caveats / next
- Cross-model sign test for MK<DX p=0.062 (borderline); the strength is the per-model Qwen
  significance + monotonic scale trend, not the 5-way sign test.
- Confirm with a mixed-effects logistic model (correct ~ competency + scale + (competency|model))
  for a pooled MK−DX estimate + CI; add held-out test-split (1,273) replication.
- OLMo weaker/non-significant — note as lower-SNR, not contradiction (same direction).

## Confirmatory stats + robustness (compute_competency_stats.py)
**(A) Pooled, model-adjusted (GLM logit, ref=DX, all 12,723).** MK vs DX OR=0.93,
log-odds −0.070 [−0.108, −0.032], **p=3.1e-4**; MGMT vs DX n.s. (p=0.15). Omnibus LRT for the
competency factor χ²(2)=13.1, **p=1.5e-3**. → competency has a *statistically real but small*
effect; MK is the relative weak spot.

**(B) Held-out test split (source_split=='test', 1,273) — does NOT robustly replicate.** Per-model
MK−DX: OLMo 7B +2.3, OLMo 32B +2.5, Qwen 7B −1.6, Qwen 14B −1.3, Qwen 32B −5.2; **no model
significant** (p=0.10–0.62) and the **direction flips by family** (OLMo MK>DX, Qwen MK<DX).
n≈425/455/338 per competency on test. ⇒ the full-set MK<DX effect is partly carried by train+dev;
on contamination-clean held-out data it is underpowered and inconsistent.

**(C) Temperature & stability.** MK−DX gap is temperature-stable for Qwen (~−2 to −3 pp at
t=0.0/0.3/0.7) — not a greedy artifact. DX is the **most run-to-run-stable** competency in every
model (instability DX < MK < MGMT), consistent with Paper 1's stability↔accuracy link.

### Final framing (honest)
- **Headline = the reliable labeling** (κ=0.83, NBME-grounded, dual-condition validated) + the
  methodological negative (finer recognition/deduction/abduction not reliably annotatable).
- **Empirical MK<DX is a small, pooled-significant, temperature-robust effect that does not
  robustly survive on the held-out test split** — report as suggestive / contamination-sensitive,
  not a strong capability claim. It *inverts* the original deduction-easier hypothesis.
- Figures: fig1 (per-competency accuracy + CIs), fig2 (MK−DX vs scale, full vs test), fig3
  (instability by competency).
