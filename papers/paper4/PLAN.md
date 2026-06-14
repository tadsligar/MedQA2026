# Paper 4 — Research Plan

**Working title:** *Forward, Backward, and Beyond: A Causal-Inference Taxonomy of Medical
Reasoning Reveals Asymmetric Competence in Base Language Models.*

> Status: planning document. This works out the thesis, the taxonomy, how to label it
> reproducibly, the hypotheses and their tests, and what is computable from data already in the
> repo. Numbers are **placeholders** (`[TBD-EXP#]`) until the analysis scripts are run; the
> per-question correctness they consume already exists in `results/base_runs_full/` and the
> focused-set runs (5 models × 3 temps × 3 runs).

---

## 1. Positioning statement

Medical-QA benchmarks report a single accuracy, and even category-resolved work (our Paper 1)
splits questions into surface buckets — "diagnosis," "treatment," "mechanism" — without asking
whether those buckets demand the *same kind of reasoning*. They do not. This paper argues that
the categories index **distinct inference operations over a causal model of disease**:
recognizing a finding is *associative*; explaining a mechanism is *forward/deductive*
(cause → effect); making a diagnosis is *backward/abductive* (effect → cause, inference to the
best explanation); choosing management is *interventional* (predicting the effect of an action).
We test whether base LLMs are **differentially competent** across these operations, whether any
asymmetry is consistent across models and scales, and — critically — whether apparent
competence at abductive diagnosis is genuine inference or multiple-choice pattern recall. The
contribution is threefold: (1) a principled, causal-inference-grounded taxonomy that re-reads an
existing benchmark; (2) an empirical characterization of where base models' reasoning is
directionally weak, with a reasoning-vs-recall analysis; (3) a prescriptive bridge — each
reasoning deficit maps to a *specific* symbolic scaffold, motivating Papers 2 and 3.

---

## 2. Title options

1. *Forward, Backward, and Beyond: A Causal-Inference Taxonomy of Medical Reasoning in Base LLMs.*
2. *Abduction Is Harder: Directional Asymmetry in Base-Model Medical Reasoning.*
3. *Which Way Through the Causal Model? Deductive, Abductive, and Interventional Reasoning in Medical QA.*
4. *Recall or Reason? Separating Pattern Recognition from Abductive Diagnosis in Medical Language Models.*
5. *From Categories to Operations: A Reasoning-Type Benchmark that Targets Neuro-Symbolic Scaffolds.*

---

## 3. Draft abstract (placeholder numbers)

Language models are evaluated on medical multiple-choice benchmarks as if every question
exercised one capability, but the questions differ in the *kind of inference* they require. We
re-cast MedQA along a taxonomy grounded in the philosophy of inference (Peirce) and the ladder
of causation (Pearl): **recognition** (associative recall of a finding), **mechanistic**
reasoning (forward, cause → effect, deductive), **diagnostic** reasoning (backward, effect →
cause, abductive), and **management** reasoning (interventional). Reusing the per-question
results of five open base models (Qwen2.5 7B/14B/32B, OLMo-3 7B/32B) at three decoding
temperatures with repeated runs — no new inference required — we measure accuracy by inference
operation with Wilson intervals and a mixed-effects model that tests whether a *directional
asymmetry* (forward vs backward) is consistent across models. We find [TBD: e.g., a robust
forward-over-backward gap of X–Y pp present in all five models], and that the abductive penalty
[TBD: grows with the number of competing candidate explanations], a signature of weak base-rate
weighting rather than missing knowledge. To separate reasoning from retrieval we relate accuracy
to question structure — differential breadth, integration depth, and pathognomonic-cue strength
(derived from a local UMLS index) — and show [TBD]. We translate each measured deficit into a
targeted neuro-symbolic remedy. We release labels, code, and analysis for full reproducibility,
and make no claims of clinical utility.

---

## 4. The taxonomy (the conceptual core)

We define **reasoning operations** by the direction of traversal over a causal disease model
(latent disease state → mechanisms → observable findings; and actions → effects). Each maps to a
classical inference type and to an observable feature of the question.

| # | Operation | Inference type (Peirce) | Causal direction (Pearl) | Prototype "ask" | Answer-option type |
|---|-----------|-------------------------|--------------------------|-----------------|--------------------|
| R | **Recognition / Recall** | (none — association) | Rung 1 *seeing* | "most likely to show / expected finding" | a finding/sign/lab value |
| F | **Mechanistic (forward)** | Deduction (apply a rule) | cause → effect | "mechanism of / why does X cause Y / responsible for" | a process/mechanism |
| B | **Diagnostic (backward)** | **Abduction** (best explanation) | effect → cause | "most likely diagnosis / underlying cause" | a disease/organism |
| I | **Interventional** | Practical/means-end | Rung 2 *doing* | "best treatment / next step in management" | a therapy/procedure |
| W | **Workup (info-gain)** *(optional 5th)* | Value of information | choosing a test to reduce uncertainty | "best initial test to confirm" | a diagnostic study |

Why this is the right cut:
- **It is principled.** Abduction (effect→cause) is provably harder than deduction (cause→effect)
  in any non-deterministic causal model: the inverse map is one-to-many and requires priors.
  A reviewer gets a *mechanism* for any asymmetry we find, not a folk taxonomy.
- **It is observable.** The operation is keyed off the **ask sentence + answer-option types**,
  i.e. the *task*, not the noisy vignette content. This is exactly the signal our rule
  classifier already reads reliably (`scripts/dataset_generation/rule_competency_classifier.py`,
  κ≈0.59 vs a Claude gold sample, with its strongest separations on diagnosis/mechanism/treatment).
- **It collapses cleanly** from Paper 1's five surface categories: Clinical Findings→R,
  Mechanism/Pathophysiology→F, Diagnosis→B, Treatment/Management→I, Next Step/Workup→W (or fold
  W into I/B by option type).

Mapping from the existing competency labeler (one source of truth, revisable in one place):
`MK → F`; `PC_DX/formulate_dx → B`; `PC_DX/labs_predict, hx_pe, prognosis → R`;
`PC_DX/labs_select → W`; `PC_MGMT/* → I`. COMM/PROF/SBP/PBL are **out of scope** for the
causal-reasoning analysis (they are non-clinical-reasoning) and are reported as an "other" stratum.

---

## 5. Research questions & hypotheses

- **RQ1 (asymmetry).** Do base LLMs differ in accuracy across inference operations beyond what a
  single difficulty scale explains?
  - **H1:** Forward/mechanistic (F) and recognition (R) accuracy exceed backward/abductive (B)
    accuracy, consistently across all five models. *(Directional, but we test both ways.)*
- **RQ2 (why).** Is the abductive penalty driven by candidate competition (base-rate weighting),
  not missing knowledge?
  - **H2:** Within B items, accuracy falls as **differential breadth** rises (more competing
    disease-type options / higher inter-option semantic similarity).
- **RQ3 (reason vs recall).** Is diagnostic success genuine abduction or surface pattern-matching?
  - **H3a:** If recall-driven, accuracy tracks **pathognomonic-cue strength** (a single
    vignette concept strongly associated with the answer) more than **integration depth**
    (number of distinct findings that must be combined).
  - **H3b:** Genuine-reasoning signature = accuracy declines with integration depth *after*
    controlling for cue strength.
- **RQ4 (scale).** Does scaling close or widen the directional gap?
  - **H4:** Scale improves R/F more than B (recall/known-rule application benefits from more
    parameters faster than base-rate-weighted inversion). Test gap vs model size.
- **RQ5 (stochasticity).** Are abductive items less stable across runs?
  - **H5:** Run-to-run instability is higher for B than for F/R at matched accuracy (more
    competing attractors), linking to Paper 1's stability-as-confidence result.

---

## 6. Methodology

### 6.1 Labeling (reproducible, no GPU)
1. Assign each question an operation R/F/B/I/W from the ask + option types (reuse + extend the
   rule classifier; the mapping in §4). Emit `results/reasoning_ops/op_labels.jsonl`.
2. **Validate** against a stratified Claude/strong-LLM gold sample (≥150, oversampling B vs F
   since that contrast is the headline) → report accuracy + Cohen's κ. Reuse the gold-sample
   harness already built for the competency check.
3. Pre-register the F-vs-B contrast as the confirmatory test; everything else is exploratory.

### 6.2 Core analysis — reuse existing runs
- Per-operation accuracy by model at t=0.0 (mean of 3 runs) with **Wilson 95% CIs**.
- **Directional asymmetry test.** Because categories are *unpaired* (different questions), do
  not use McNemar across operations. Fit a **mixed-effects logistic model**:
  `correct ~ operation + scale + operation:scale + (operation | model)`.
  The random slopes on `operation | model` quantify *consistency across models* (small variance
  ⇒ the asymmetry is general). Report the F−B fixed-effect contrast with bootstrap CI and a
  likelihood-ratio test for the operation main effect.
- Robustness: repeat on (a) the focused balanced 1,030 set and (b) the official MedQA **test
  split** (1,273) as held-out; report both so the asymmetry isn't an artifact of set construction.

### 6.3 Probes that separate reasoning from recall (no GPU; use local UMLS index)
- **Differential breadth (H2):** for B items, count disease-type options and compute mean
  pairwise UMLS/embedding similarity among options (closely-spaced differentials = harder).
  Logistic regression of correctness on breadth, per model.
- **Integration depth (H3):** proxy = number of distinct clinical-finding concepts grounded in
  the vignette (reuse Paper 2 grounding) and/or clause count. Regress accuracy on depth.
- **Pathognomonic-cue strength (H3):** max associative strength between any single vignette
  concept and the correct answer (UMLS co-occurrence / PMI, or a lexical-overlap proxy). High
  cue strength + high accuracy independent of depth ⇒ recall, not reasoning.
- **Decompose:** 2×2 of (high/low cue) × (shallow/deep integration); a recall model predicts
  cue dominates; a reasoning model predicts depth matters within low-cue items.

### 6.4 Stability (H5) — reuse Paper 1 stability metric
- Run-to-run answer instability per operation; compare B vs F/R at matched accuracy bands.

### 6.5 Prescriptive mapping (the bridge to Papers 2/3)
Translate each measured deficit into a symbolic scaffold:
- **B weak (abduction):** Bayesian/causal-network layer doing explicit effect→cause inversion
  with disease priors (Paper 3 belief module).
- **F weak (mechanism):** ontology / knowledge-graph lookup & path verification (Paper 2 UMLS).
- **I weak (intervention):** guideline/treatment-rule checking + contraindication audit (Paper 2 verifier).
- **W weak (workup):** value-of-information / test-selection policy (Paper 3 controller).

---

### 6.6 Lead-in-conditioned reasoning orchestration (constructive extension)
Grounded in the NBME closed-lead-in principle (see `LABELING_RATIONALE.md`): the **lead-in** (final
sentence) reliably signals the reasoning operation, so it can *route* the solver. Pipeline:
1. **Parse** each question into stem (vignette) + lead-in (final sentence).
2. **Route** on the lead-in → operation R/F/B/I/W (the labeling classifier, used live).
3. **Solve** with an operation-specific reasoning path, given the full stem + lead-in:
   - B (abductive diagnosis) → generate-and-rank differential with base-rate weighting / Bayesian belief.
   - F (forward mechanism) → ontology / knowledge-graph path lookup.
   - I (intervention) → guideline / contraindication check.
   - W (workup) → value-of-information test-selection.
   - R (recognition) → direct recall.
Evaluate **orchestration × operation**: does routing to an operation-matched solver beat a single
uniform prompt, and *differentially* by operation? This is the compute-bearing arm (new model runs)
and the bridge that turns §6.5's prescription into an implemented system. Reuses Paper 2 grounding/
verifiers and Paper 3 belief/controller modules. *(Depends on the asymmetry/structure results first.)*

### 6.7 External validity — second dataset
Replicate the operation taxonomy + lead-in routing on a second corpus to show it isn't a MedQA
artifact. Candidates: **MedMCQA** (already carries reasoning-type labels — lets us validate our
lead-in operation labels against an independent scheme) and/or a non-MCQ / free-response medical set
(tests whether the lead-in signal survives outside multiple-choice). Report operation-distribution
and the asymmetry on the second set alongside MedQA.

## 7. Metrics & deliverables (tables/figures)

- **T1.** Per-operation accuracy × model (t=0.0), Wilson CIs, natural N per operation.
- **T2.** Mixed-model fixed effects; F−B contrast per model + pooled, bootstrap CIs, LRT.
- **T3.** Differential-breadth and integration-depth regressions (odds ratios) by operation.
- **T4.** Reasoning-vs-recall 2×2 (cue × depth) accuracy table.
- **T5.** Instability rate by operation.
- **F1.** Concept figure: the causal disease model with the four traversal directions annotated.
- **F2.** Forest plot of the F−B gap across the five models (consistency = H1).
- **F3.** Accuracy vs differential breadth (B items) and vs integration depth, per model.
- **F4.** Operation × scale interaction (does the gap close with size?).
- **F5.** Prescriptive matrix: deficit → symbolic scaffold → which later paper.

---

## 8. What is computable now vs new work

| Component | Needs new GPU runs? | Source |
|---|---|---|
| Operation labels + gold validation | No | rule classifier + Claude/LLM gold |
| Per-operation accuracy, CIs, mixed model | **No** | existing `results/base_runs_full/` + focused runs |
| Directional asymmetry, scale interaction, stability | **No** | existing runs |
| Breadth / integration / cue probes | No (CPU) | local UMLS index + datasets |
| (Optional) confirmatory cue-ablation generation | Maybe | only if reviewers want a controlled stimulus set |

**Implication:** like Paper 1, Paper 4 can become **empirically complete from data already in
the repo**. This is its biggest practical advantage and should be stated up front.

---

## 9. Limitations (state honestly)
- **MCQ ≠ free-form reasoning.** Multiple choice can be solved associatively; §6.3 mitigates but
  cannot fully eliminate the recall confound. We claim evidence about *MedQA-style* reasoning, not
  unconstrained diagnosis.
- **Label noise.** Operation labels are heuristic; we bound their reliability with κ and run the
  asymmetry test under a label-noise sensitivity check (e.g., drop low-confidence items, re-test).
- **Proxy probes.** Breadth/depth/cue are operationalizations; we report several and check agreement.
- **Base models only.** No instruction-tuned or RLHF models in the headline; cross-version note as in Paper 1.
- **No causal-effect claims about the models' internals** — we infer reasoning type from behavior + question structure, not mechanistic interpretability.

---

## 10. Relation to the four-paper arc
- **Paper 1** established that aggregate accuracy hides category structure. **Paper 4** explains
  *why those categories differ* (they are different inference operations) and turns the category
  axis from a labeling liability into a theory-driven instrument.
- **Papers 2 & 3** are the *remedies* Paper 4 prescribes: Paper 4's measured deficit profile
  tells you which symbolic scaffold (grounding/verification vs Bayesian abduction vs
  value-of-information workup) to deploy for which operation.
- Suggested arc ordering for the program narrative: 1 (benchmark) → 4 (diagnosis of *which
  reasoning* is weak) → 2 (symbolic grounding/verification) → 3 (agentic acquisition).

---

## 11. Build order (proposed)
1. Operation labeler + mapping from competency labels; emit `op_labels.jsonl`. *(½ day, no GPU)*
2. Claude/LLM gold validation of operation labels (κ). *(½ day)*
3. `analysis/op_accuracy.py` — per-operation accuracy + Wilson CIs from existing runs. *(reuses Paper 1 code)*
4. `analysis/asymmetry_mixed_model.py` — mixed-effects + bootstrap F−B contrast. 
5. `analysis/structure_probes.py` — breadth / integration / cue strength via UMLS index.
6. `analysis/stability_by_op.py` — reuse Paper 1 stability.
7. Figures F1–F5; tables T1–T5.
8. **Lead-in router + operation-conditioned solvers (§6.6)** — the constructive orchestration arm
   (new model runs; reuses Paper 2/3 modules). Build only after the asymmetry/structure results.
9. **Second-dataset replication (§6.7)** — MedMCQA (reasoning-type labels) and/or a non-MCQ set.
10. DRAFT.md prose + PDF (match Papers 1–3 format). Methods cite `LABELING_RATIONALE.md` (NBME lead-in).
