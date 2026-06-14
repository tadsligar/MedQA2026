# DRAFT — Paper 4

> Working draft. All numbers verified from the repository: labels in
> `results/reasoning_ops/op_labels_v2.jsonl`; reliability in `VALIDATION.md`; accuracy/stats in
> `RESULTS_v2.md` (reproducible via `analysis/compute_competency_accuracy.py`,
> `compute_competency_stats.py`, `make_figures.py`). Base models: Qwen2.5 (7B/14B/32B),
> OLMo-3 (7B/32B). Dataset: full MedQA, 12,723 questions, 5-option (A–E). No claims of clinical utility.

## Title (working)
**What MedQA Actually Tests: A Reliable, NBME-Grounded Competency Labeling of a Medical-QA
Benchmark — and What It Reveals (and Doesn't) About Base-LLM Reasoning.**

Alternates: *Labeling the Lead-In: Reliable Physician-Competency Annotation of MedQA*; *Reasoning
Type Barely Moves the Needle: A Competency-Resolved Analysis of Base Medical LLMs*.

## Abstract (draft)
Medical-QA benchmarks are reported as a single accuracy, and attempts to resolve performance by
"reasoning type" rest on category schemes whose *labeling reliability is almost never measured*.
We show this matters. We first attempt an intuitive, theory-driven taxonomy of reasoning
*operations* (recognition / forward-mechanistic / backward-diagnostic / interventional / workup)
motivated by the philosophy of inference; two independent strong annotators (a human expert and
gpt-5.4-mini), labeling from the question's NBME **lead-in** + options, agree only moderately
(Cohen's κ=0.63), with disagreement concentrated in the recognition/deduction/abduction cluster.
We demonstrate the failure is intrinsic to the *taxonomy*, not the input: labeling from the
lead-in alone reproduces the same κ. Re-anchoring on the **official USMLE Physician
Tasks/Competencies** — with verbatim subtask definitions and explicit tie-break rules — yields a
**reliable** labeling (κ=0.83; Medical-Knowledge vs Diagnosis κ=0.88), validated both with and
without the explicit rules (κ=0.74 rules-off → genuine construct validity). We release competency
labels for all 12,723 MedQA questions. Using existing base-model runs, we then ask whether
competency predicts accuracy: it does, but weakly — a small, pooled-significant deficit on Medical
Knowledge relative to Diagnosis (OR 0.93, p=3×10⁻⁴), which is temperature-robust but **does not
reliably replicate on the held-out test split**. The result *inverts* the intuitive
"deduction-is-easier" hypothesis and is consistent with multiple-choice answering being dominated
by pattern recognition rather than operation-specific reasoning. Our central contribution is
methodological: a reproducible, validated competency labeling of MedQA and evidence that
finer reasoning-type distinctions are not reliably annotatable.

## 1. Introduction (outline)
- P1. Aggregate MedQA accuracy hides structure; "reasoning-type" breakdowns are increasingly used
  but their *label reliability* is unreported.
- P2. We test an inference-grounded operation taxonomy (Peirce/Pearl) and find it unreliable.
- P3. We trace the failure to the taxonomy (lead-in probe), then recover reliability via the
  official USMLE competencies (NBME lead-in principle: the closed lead-in fixes the answer type).
- P4. Contributions: (i) released, validated competency labels for all 12,723 MedQA; (ii) a
  dual-condition κ methodology for benchmark category reliability; (iii) the honest negative that
  recognition/deduction/abduction is not reliably separable; (iv) a competency-resolved accuracy
  analysis showing reasoning type explains little variance (small MK<DX deficit, not robust on test).

## 2. The taxonomy attempt and why it failed
- Operations R/F/B/I/W; grounding in inference types + Pearl's ladder (PLAN §4).
- κ=0.63 vs Claude gold; confusion concentrated in R/F/B. Lead-in-only probe (κ=0.64) rules out
  vignette drift ⇒ intrinsic. Collapsing R/F/B→K gives κ≈0.9 but discards the distinction of interest.

## 3. A reliable labeling: official USMLE competencies
- NBME Item-Writing Guide closed-lead-in principle (`LABELING_RATIONALE.md`); official subtasks
  with the counterintuitive deterministic rules ("given an effect determine the cause"→MK;
  "predict the finding"→DX; anatomy/inheritance→MK).
- Reliability table (VALIDATION.md Update 2): κ=0.83 rules-on / 0.74 rules-off; MK-vs-DX κ=0.88.
- Full-set labeling of 12,723; distribution DX 35.8% / MK 34.0% / MGMT 26.4% / non-clinical ~4%.

## 4. Competency-resolved accuracy of base LLMs
- Per-competency accuracy table + Wilson CIs (Table; fig1). Pooled GLM: MK<DX OR 0.93, p=3e-4;
  omnibus LRT p=1.5e-3 — small but real.
- **Held-out test split does not replicate** (fig2): underpowered + direction flips by family.
- Temperature-robust gap (Qwen); DX most run-to-run-stable (fig3).
- Interpretation: inverts deduction-easier hypothesis; consistent with MCQ recall-confound —
  reasoning *type* is not a major axis of base-LLM MedQA difficulty.

## 5. Limitations
- MCQ ≠ free-form reasoning; competency labels are operationally (rule-)defined, not claimed
  cognitively fundamental. Full set includes train (contamination) — hence the test-split check,
  which tempers the MK<DX claim. Non-clinical competencies have small n (treat as suggestive).

## 6. Relation to the program & future work
- Bridges Paper 1 (aggregate→structure) to a *validated* competency axis. Motivates **Paper 5**:
  competency-routed orchestration (route on the lead-in → competency-matched solver), where the
  measured MK weak spot is the natural target — though Paper 4's small accuracy spread sets modest
  expectations on the accuracy axis.

## Tables / Figures
- T1 reliability (κ rules-on/off, MK-vs-DX). T2 per-competency accuracy + CIs. T3 pooled GLM + test-split.
- F1 `figures/fig1_competency_accuracy.png`; F2 `fig2_mk_dx_gap.png`; F3 `fig3_instability_by_competency.png`.
