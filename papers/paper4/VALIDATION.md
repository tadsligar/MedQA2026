# Paper 4 — operation-label validation (gpt-5.4-mini vs Claude gold)

**Gold sample:** 100 questions, stratified 20/operation over the gpt-5.4-mini labels (oversamples
rare R/W). Hand-labeled independently by Claude (`results/reasoning_ops/gold_op_labels.jsonl`),
scored against the gpt-5.4-mini labels.

## Result
- Agreement: **70/100 (70%)**, Cohen's **κ = 0.625** (substantial, Landis-Koch).
- Reliable cells: **Interventional 17/20**, **Workup 19/21** — "is this a treatment decision /
  a test-selection" is labeled consistently.
- Unreliable cluster: **Recognition / Mechanistic / Diagnostic (R/F/B)** account for nearly all
  disagreement. My R was read as B (6) or F (6); my F as B (6); my B as R (4).

## Why this matters for the headline
The **forward(F)-vs-backward(B) contrast — the central hypothesis — lies on the least separable
boundary.** When two careful annotators can't reliably distinguish "mechanism" from "diagnosis"
on these items, a true accuracy asymmetry would be smeared out by misclassification. So the flat
full-set F−B result (gap ≈ +0.46 pp, n.s.) is **confounded with labeling resolution**: it is NOT
evidence that no asymmetry exists — only that none is detectable at this label quality.

## Coverage gap
Biostatistics items (RR/PPV/risk-difference) and ethics/communication items do not fit the five
operations; both annotators dumped biostats → W and ethics → I as catch-alls (~10% of MedQA).

## Implications / next steps
1. The deduction/abduction (F/B) distinction is not cleanly operationalizable on MedQA MCQs as
   defined. This is itself a reportable methodological finding (and consistent with the MCQ
   recall-confound: if models pattern-match both, no behavioral gap is expected).
2. Concrete salvage test (uses the cluster second annotator): once the Qwen2.5 labels land,
   compute gpt-vs-Qwen agreement on the full set, then **re-test the asymmetry on the
   high-confidence subset where both annotators agree on F vs B.** If still null on clean items,
   that is a strong claim; if an asymmetry emerges, it was masked by noise.
3. I and W are reliable enough to use as-is; the R/F/B trio needs a sharper rubric (or merging
   R into B/F) before any cross-operation claim.

---

## Update — lead-in probe + taxonomy-granularity finding (decisive)

**Lead-in-only labeling does NOT improve reliability.** Sending gpt-5.4-mini only the lead-in
(final sentence) + options for the 100 gold qids: 71% / κ=0.641 — statistically indistinguishable
from the full-question 70% / κ=0.625. Since the human gold was itself labeled from lead-in+options,
this is apples-to-apples: it **refutes** the "gpt drifted to the vignette" explanation. The R/F/B
disagreement is **intrinsic to the categories**, not an input artifact.

**A coarse 3-way taxonomy IS reliable.** Collapsing R/F/B → K (Knowledge/diagnostic-inference) and
keeping I (Management), W (Workup):

| Comparison | Fine 5-way κ | Coarse K/I/W κ |
|---|---|---|
| gold vs full-question gpt | 0.625 | **0.894** |
| gold vs lead-in gpt | 0.641 | **0.911** |
| full-gpt vs lead-in gpt | 0.787 | 0.875 |

So: recognition/deduction/abduction are **not reliably separable** (the forward-vs-backward
asymmetry is therefore not measurable at reliable resolution); Knowledge / Management / Workup
**are** reliable (κ≈0.9).

**But the reliable axis has little accuracy signal.** Full-set accuracy by K/I/W (t=0.0):
gaps are ~1–2 pp across all five models (K slightly highest, W slightly lowest; Qwen-7B W −3.8 pp
the largest). Reasoning-operation type explains little variance in base-LLM MedQA accuracy.

### Honest standing of Paper 4 (two real findings)
1. **Methodological:** fine reasoning-type distinctions (recognition/deduction/abduction) are not
   reliably annotatable on USMLE MCQs even from the designed lead-in cue (κ≈0.63); only a coarse
   Knowledge/Management/Workup partition is reliable (κ≈0.9). The intended deduction-vs-abduction
   asymmetry is not testable at reliable resolution.
2. **Empirical:** on the reliable partition, base-LLM accuracy is nearly flat across operation type
   (~1–2 pp), consistent with the MCQ recall-confound (models solve operation types about equally,
   as if pattern-matching rather than running operation-specific reasoning).

Together: a cautionary/negative result arguing against framing MedQA accuracy as operation-specific
reasoning competence. (Confirm finding 2 with Wilson CIs + the mixed model on K/I/W before claiming
"flat".) Implication for the orchestration extension (§6.6): routing-by-operation has weak
motivation on the accuracy axis, though it could still help via operation-matched *methods*.

---

## Update 2 — official USMLE competency rubric (v2) IS reliable (decisive, positive)

The R/F/B unreliability was the *taxonomy*, not the data. Re-labeling under the official USMLE
Physician Tasks/Competencies (MK / DX / MGMT / COMM / PROF / SBP / PBL; rubric v2) on the same 100
gold qids (gpt-5.4-mini, lead-in+options):

| Condition | Overall | κ | MK-vs-DX κ |
|---|---|---|---|
| Rules ON (official deterministic tie-breaks) | 88% | **0.829** | **0.882** |
| Rules OFF (names + brief defs only) | 82% | **0.744** | 0.790 |

vs R/F/B baseline κ=0.625. Interpretation:
- The official competency taxonomy is **reliable** (κ=0.83), unlike the invented R/F/B operations.
- Rules-off κ=0.74 ⇒ the categories have genuine **construct validity** (not just rule-following);
  explicit NBME rules add a modest +0.08.
- **MK-vs-DX (apply-foundational-science vs diagnose) is reliably separable (κ=0.88)** — the
  principled reasoning contrast survives where the causal-direction (forward/backward) cut failed.
- Residual soft spot: DX→MGMT (workup-vs-"next step in management"), small and expected.

### Revised standing of Paper 4 (now constructive)
- Adopt the **official competency taxonomy (v2), rules ON**, as the labeling scheme.
- Contribution = a reliable, NBME-grounded competency labeling of MedQA, **validated with
  dual-condition κ** (rarely reported in this literature), PLUS the honest negative that the finer
  recognition/deduction/abduction split is not reliably annotatable (κ≈0.63).
- Reasoning contrast becomes MK vs DX vs MGMT (apply-science / diagnose / manage) — reliable.

### Next
1. Relabel the full 12,723 under v2 (rules ON) — new batch (~$8). 
2. Re-run per-competency accuracy + Wilson CIs + mixed model on MK/DX/MGMT (does competency move
   accuracy? — now testable on a reliable axis; K/I/W preview was ~flat, but MK-vs-DX is a new split).
3. Report the v2 κ table above as the labeling-reliability result.
