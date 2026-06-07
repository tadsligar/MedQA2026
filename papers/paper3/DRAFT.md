# DRAFT — Paper 3

> Working draft. **Bold bracketed** items like `[TBD-EXP#: …]` require a new experiment
> (`experiments/`). The agent is not yet implemented, so its results are placeholders. Seeds
> verified from base-run data are in `RESULTS_SEED.md`; static baselines are verified
> (Paper 1); symbolic components are inherited from Paper 2 (pending). Dataset: focused
> balanced MedQA, 1,030 questions, 4-option (A–D), random baseline 25%.

---

## Title (working; alternates below)
**From Answer Selection to Differential Reasoning: An Agentic Neuro-Symbolic Framework for
Adaptive Evidence Acquisition in Medical Question Answering**

Alternates:
1. *Agentic Neuro-Symbolic Differential Diagnosis for Medical Question Answering.* (agentic neuro-symbolic)
2. *Beyond Single-Pass Answers: Differential Reasoning over MedQA Vignettes.* (differential diagnosis)
3. *Adaptive Evidence Acquisition for Medical Reasoning: Selecting What to Check Next.* (adaptive evidence)
4. *Executable Diagnostic Reasoning: UMLS-Grounded Evidence Functions and Belief Updates for MedQA.* (executable reasoning)
5. *Does Adaptive Evidence Selection Help? An Agentic Neuro-Symbolic Study on MedQA.* (MedQA-specific)
6. *Category-Aware Neuro-Symbolic Agents for Clinical Reasoning: A Controlled MedQA Evaluation.* (biomedical informatics)
7. *Belief, Evidence, and Verification: Neuro-Symbolic Agents for Structured Medical Reasoning.* (neuro-symbolic AI)

---

## Abstract

Medical question answering is usually evaluated as static, single-pass answer selection: a
model reads a vignette and emits a letter. Clinical reasoning is better described as
*differential reasoning* — forming candidate hypotheses, deciding what evidence to examine
next, weighing supportive against contradictory findings, updating belief, and producing an
auditable trace. Building on a category-balanced MedQA benchmark (Paper 1) and UMLS-grounded
verification (Paper 2), we propose and evaluate an **agentic neuro-symbolic framework** that
reformulates each question as adaptive evidence acquisition. The system parses the vignette,
classifies the reasoning category, generates typed candidate hypotheses, grounds findings and
candidates to UMLS, and then runs a controller that maintains a belief state over candidates
and **selects evidence functions** — demographic plausibility, symptom/lab support,
pathophysiology and treatment-relation checks, contradiction audits, and others — by expected
utility under a budget, with redundancy-aware selection and a verification pass, before
committing to a final answer and evidence trace. We evaluate on a balanced set of 1,030
MedQA-style questions across five reasoning categories, comparing static zero-shot and
chain-of-thought prompting, self-consistency, UMLS symbolic scoring, Chain-of-Verification,
and ablated and full agent variants. We report accuracy, category-level performance, evidence
efficiency, grounding and contradiction metrics, belief-margin calibration, and error
prediction, with bootstrap intervals and paired tests. Analysis of the base models shows
roughly **12.6 points of headroom** between the best single model (73.4%) and an oracle that
solves any question some model solves (86.0%), and that inter-model agreement strongly tracks
correctness — motivating belief-guided adaptive reasoning, while a control analysis shows the
headroom is **not** reachable by routing among models. We characterize where adaptive evidence
acquisition helps, where it only improves interpretability, and the failure modes that arise
when LLM planning meets symbolic grounding. This is a controlled MedQA-style study; we make no
clinical-deployment claims.

---

## 1. Introduction

**P1 — Answer selection vs reasoning.** LLMs score well on MedQA, but emitting a letter says
nothing about the reasoning behind it. Treating medical QA as single-pass classification
discards the structure of clinical reasoning.

**P2 — Clinical reasoning is differential.** Clinicians entertain competing hypotheses, decide
which evidence to seek next, and revise belief as findings accumulate — a coarse-to-fine,
evidence-guided process producing an interpretable trace.

**P3 — MedQA is heterogeneous.** A single benchmark mixes Clinical Findings, Diagnosis,
Mechanism, Workup, and Treatment — reasoning tasks with different evidence needs, ill-served by
one static prompt.

**P4 — Paper 1.** Base-model behavior is category- and temperature-dependent, with substantial
run-to-run instability — accuracy alone hides this structure.

**P5 — Paper 2.** UMLS grounding and symbolic verification help audit reasoning but static
symbolic scoring is brittle (the concept-mismatch problem); symbolic signal is more useful for
*verification* than for solving.

**P6 — The need for adaptivity.** These motivate a system that *adapts* what evidence it
examines to the case and its current uncertainty, rather than applying a fixed pipeline.
Our seed analysis sharpens the target: an oracle over five base models reaches 86.0% vs the
best single model's 73.4% (≈12.6 pp headroom), and inter-model agreement predicts correctness
(83.5% when all agree, 23.9% when split) — yet that headroom is **not** capturable by choosing
which model to ask (the best model wins every category), so the lever must be *reasoning*, not
model routing.

**P7 — Proposed framework.** We present an agentic neuro-symbolic system (Figure 1, Algorithm
1): parse → categorize → generate candidates → ground → adaptively select evidence functions →
update belief → verify → decide, emitting an evidence trace.

**P8 — Experiments.** We compare static prompting, self-consistency, symbolic-only,
Chain-of-Verification, and ablated/full agents across categories, measuring accuracy,
efficiency, grounding/verification quality, calibration, and failure modes.

**P9 — Contributions** (Section 1.1).

### 1.1 Contributions
1. A reformulation of MedQA as **adaptive evidence acquisition**, with a concrete agentic
   neuro-symbolic framework and algorithm.
2. An **evidence-function library** of UMLS- and LLM-based clinical checks, with a controller
   that selects them by uncertainty and expected utility under a budget.
3. **Transparent neuro-symbolic belief updates** and a verification/contradiction auditor that
   yield ranked candidates, a confidence proxy, and an interpretable evidence trace.
4. A **controlled comparison** against static and symbolic baselines with proper statistics,
   including the honest finding that base-model headroom is not reachable by model routing.
5. A **failure-mode taxonomy** for agentic neuro-symbolic medical reasoning.
6. Released, reproducible code and analysis. No clinical-deployment claims.

---

## 2. Related Work

Clusters, what to cite, positioning, gap. **Medical QA / MedQA** (Jin et al. 2021) — we move
from answer selection toward differential reasoning. **Clinical reasoning & differential
diagnosis** (cognitive models; Bayesian diagnosis) — we operationalize it for exam QA.
**LLMs for medical reasoning** (Med-PaLM, GPT-4 medical) — we add structure and auditability.
**Agentic LLMs / tool use** (ReAct, Toolformer) — we instantiate medical evidence functions as
tools with symbolic grounding. **Neuro-symbolic AI** — a medical control-loop instantiation.
**Biomedical KGs / UMLS** (Bodenreider 2004) — grounding/verification substrate. **CoVe &
self-refinement** (Dhuliawala et al.) — we ground verification in a KG and add adaptive
selection. **Adaptive computation / active feature selection** (mRMR; active testing) — source
of redundancy-aware evidence selection. **Probabilistic reasoning / belief update**, and
**explanation faithfulness / clinical interpretability**. *Gap:* no prior work couples
category-aware adaptive evidence selection, UMLS grounding, transparent belief updates, and
verification into a single controlled MedQA evaluation with a failure-mode analysis.

---

## 3. Background and Motivation

We adapt a coarse-to-fine diagnostic framework (originally for human-motion diagnosis) to
clinical-vignette reasoning. The source method estimates coarse context, narrows hypotheses,
selectively evaluates biomarkers, maintains belief over competing diagnoses, accumulates
probabilistic evidence with minimum-redundancy/maximum-relevance selection, and emits an
interpretable trace. **Table A (mapping):**

| Motion-diagnosis concept | MedQA analogue |
|---|---|
| video segment | clinical vignette |
| subject/body-region visibility | available evidence type (present vs missing) |
| motion biomarker | clinical finding or relation |
| gait asymmetry | asymmetric symptom pattern / focal deficit |
| tremor marker | lab abnormality / symptom pattern / mechanism cue |
| latent neurological factor | candidate diagnosis / mechanism / workup / treatment |
| diagnostic graph | UMLS-grounded clinical reasoning graph |
| adaptive biomarker selection | adaptive evidence-function selection |
| probabilistic evidence accumulation | answer-choice belief update |
| mRMR feature selection | redundancy-aware evidence selection |
| clip diagnostic score | candidate answer posterior |
| interpretable evidence trace | structured rationale with support/contradiction trace |

The translation is the conceptual backbone of the framework: diagnosis as adaptive,
evidence-guided belief refinement rather than flat classification.

---

## 4. Dataset

The focused balanced MedQA subset: **1,030** questions, **206 per category**, 4-option (A–D),
random baseline 25% (shared with Papers 1–2; **Table 1**). We reuse the verified static
baselines and the 144-question hard-core set (all five base models wrong) as a stress target.
In MedQA the candidate set is supplied by the answer choices, a simplification relative to
open-ended differential diagnosis (Limitations).

---

## 5. Agentic Neuro-Symbolic Framework

Figure 1 shows modules A–J. **A. Case parser** — extract demographics, symptoms, signs, labs,
imaging, medications, risk factors, timing, negations, and which evidence is present vs missing.
**B. Reasoning-category classifier** — assign category (optionally multi-label) to select a
reasoning policy. **C. Candidate hypothesis generator** — options → typed candidates
(diseases / mechanisms / interventions / next steps / expected findings). **D. UMLS grounding**
— stem findings and candidates → CUIs, semantic types, relation candidates, confidence;
preserve negation; flag unmapped concepts (Paper 2). **E. Evidence-function library** — sixteen
callable checks returning per-candidate support/contradiction (Table 2; EXP3). **F. Agent
controller/planner** — maintains belief, selects the next function by uncertainty × expected
utility − redundancy, stops on confidence/budget. **G. Belief-state update** — transparent
neuro-symbolic scoring (below). **H. Redundancy-aware selection** — mRMR-style, prioritizing
evidence that separates top candidates. **I. Verification/contradiction auditor** — five
verifiers → warning flags; optional gated revision. **J. Final decision** — answer, ranked
candidates, confidence proxy, support/contradiction table, evidence trace.

### 5.1 Belief-update formulations (EXP5)
We compare: (A) additive `score += support − contradiction`; (B, recommended)
weighted neuro-symbolic `score = LLM + α·support − β·contradiction + γ·grounding_conf`;
(C) Bayesian-style prior × evidence likelihood; (D) learning-to-rank over evidence features
(future-leaning); (E) calibration-aware confidence from margin, coverage, and flags.

---

## 6. Algorithm

**Algorithm 1: Agentic Neuro-Symbolic Medical Reasoning**
```
Input : vignette x, answer choices A, evidence budget B, UMLS graph K
Output: final answer a*, ranked candidates, evidence trace T
 1  c ← ParseCase(x)                         # module A
 2  cat ← ClassifyCategory(c)                 # module B
 3  H ← GenerateCandidates(A, cat)            # module C
 4  G ← GroundConcepts(c, H, K)               # module D
 5  belief ← InitPrior(H, G, cat)             # module G (init)
 6  T ← [ ]
 7  for t = 1 … B do
 8      u ← Uncertainty(belief)               # margin / entropy
 9      f ← SelectFunction(cat, belief, G, T) # module F/H: argmax utility − λ·redundancy
10      e ← Execute(f, c, H, G)               # module E
11      belief ← UpdateBelief(belief, e)      # module G
12      T.append((f, e, snapshot(belief)))
13      if Margin(belief) ≥ τ or u ≤ ε then break   # adaptive stopping
14  end for
15  flags ← Verify(belief, T, G)              # module I
16  belief ← AdjustOrFlag(belief, flags)      # gated revision
17  a* ← argmax belief
18  return a*, Rank(belief), T
```

### 6.1 Scoring formulation
For candidate `i` and accumulated evidence `E`:
- support `S_i = Σ_e w(e)·support(e, i)`; contradiction `C_i = Σ_e w(e)·contra(e, i)`
- grounding confidence `g_i ∈ [0,1]`; redundancy penalty `R(f) = sim(f, prior evidence)`
- belief `b_i ∝ exp(LLM_i + α·S_i − β·C_i + γ·g_i)` (softmax over candidates)
- next-function utility `U(f) = E[Δmargin | f] − λ·R(f)`; stop when `margin ≥ τ` or budget spent
- final score `= b_i`, downweighted by verifier flags.
α, β, γ, λ, τ tuned on a dev split (EXP5/EXP9); we report sensitivity.

---

## 7. Experimental Design

**Conditions (Table 3; EXP8).** Baselines: random (25%); static zero-shot LLM (verified
Paper 1); static CoT; self-consistency; category-prompt-only; UMLS symbolic-only (Paper 2);
UMLS-grounded prompt (Paper 2); CoVe (Paper 2). Agentic: agent w/o UMLS; +grounding no
belief-update; +belief no auditor; +auditor no adaptive selection; **full agent**; full agent
fixed-budget; full agent dynamic-stopping; oracle bound (86.0%). **Statistics:** bootstrap CIs,
McNemar, paired bootstrap for category deltas, logistic regression for correctness prediction,
AUROC/AUPRC for error prediction, mixed-effects for method×category, correlation of budget vs
accuracy, ablation significance with multiple-comparison correction — reusing the Paper 1/2
harness. **Anti-overclaim:** modest, category-specific, or interpretability-only gains will be
reported as such, with CIs, and not headlined as accuracy wins.

---

## 8. Results

*Agent numbers are placeholders; static baselines and seed bounds are verified.*

**8.1 Overall accuracy by method (Table 4).** Static LLM-only baseline: best single Qwen2.5
32B 73.4% (Paper 1). Symbolic-only / UMLS-prompt / CoVe [TBD-Paper2]. Agent variants
[TBD-EXP8], positioned against best-single 73.4% and oracle 86.0%.

**8.2 Category-specific accuracy (Table 5, Figure 6).** [TBD-EXP8] per method × category;
test whether agentic gains concentrate in Diagnosis/Workup/Treatment (RQ7). Seed caution: since
the best model wins every category, category gains must come from reasoning, not model choice.

**8.3 Agentic efficiency (Table 6, Figures 5, 7).** Mean evidence calls, stopping depth,
function-selection distribution by category, accuracy vs budget (diminishing returns), adaptive
vs fixed-policy delta [TBD-EXP4/EXP6/EXP9].

**8.4 Belief calibration (Figure 4).** Belief-margin reliability and the margin-vs-correctness
curve [TBD-EXP5], compared to the verified agreement-vs-correctness seed (5-agree 83.5% →
2-agree 23.9%).

**8.5 Grounding & verification (Table 8, Figure 8).** Grounding coverage, contradiction scores,
verifier precision/recall, and error-prediction AUROC [TBD-EXP7].

---

## 9. Ablation Studies

[TBD-EXP9] Remove, one at a time: UMLS grounding, category classifier, adaptive selection
(→ fixed sequence), belief updates, contradiction auditor, redundancy penalty, semantic-type
compatibility, pathophysiology checker, contraindication checker; plus LLM-only vs symbolic-only
evidence functions, random selection, no-adaptivity, no-final-verification, no-revision. Report
accuracy deltas with CIs, rank component contributions, and flag any component that does not
help (a legitimate negative result given the §8.2 caution). Evidence-budget sweep B=1..N
(Figure 10).

---

## 10. Case Studies

[TBD-EXP10] Five worked traces: (1) Diagnosis improved by adaptive evidence selection; (2)
Treatment saved by a contraindication check; (3) Workup helped by next-best-test reasoning;
(4) Mechanism helped by pathophysiology-chain reasoning; (5) a failure where the agent selects
misleading evidence or grounding fails. Each shows vignette, choices, evidence calls, belief
trajectory (Figure 4), flags, and final answer, drawn where possible from the 144 hard-core
items. Figure 9 shows an example evidence trace.

---

## 11. Discussion

The thesis is methodological: medical QA is more faithfully modeled as adaptive differential
reasoning than as single-pass selection. The research question is not only whether the agent
raises accuracy, but whether adaptive evidence selection, grounding, contradiction auditing,
and belief updates yield more **reliable, interpretable, uncertainty-aware** reasoning. The
seed analysis frames expectations honestly: there is real headroom (oracle 86.0% vs 73.4%), but
it is invisible to model routing and not reachable by naive voting, so any gain must come from
*better reasoning within a model*. We expect the agent's clearest value in **error detection
and interpretability** (belief margin and contradiction flags predicting wrong answers) and in
specific categories, with accuracy gains possibly modest — and we will report that plainly.

---

## 12. Limitations

MedQA is exam-style, not clinical practice; multiple-choice supplies candidates, simplifying
the differential. Agentic tool calls add compute. UMLS is incomplete and not a causal reasoning
engine; concept mismatch (Paper 2) remains unresolved. LLM rationales may be unfaithful, so
trace-quality needs manual validation. Belief weights (α, β, γ, λ, τ) require tuning and may
overfit dataset structure; evidence-function outputs can be noisy. The agent is **not yet
implemented** in this snapshot — all agentic results are pending experiments. No patient-safety
or clinical-deployment claims are made.

---

## 13. Future Work

Open-ended differential diagnosis without supplied choices; retrieval-augmented literature
grounding; integration with SNOMED CT, RxNorm, MeSH, and guidelines; **learned**
evidence-selection policies; clinician evaluation of evidence traces; application to real
clinical notes; uncertainty-aware abstention; causal medical knowledge graphs; multi-agent
specialist reasoning; and dedicated patient-safety evaluation. The framework's grounding,
verification, and belief machinery are the substrate for these extensions.

---

## 14. Conclusion

We reformulate MedQA as adaptive evidence acquisition and present an agentic neuro-symbolic
framework — parse, categorize, hypothesize, ground, adaptively gather evidence, update belief,
verify, and decide with an interpretable trace. Grounded in verified base-model analysis
(≈12.6 pp oracle headroom, agreement-tracks-correctness, no model-routing gain), the study asks
where adaptive, grounded, verified reasoning improves reliability and interpretability over
static prompting, and characterizes its failure modes. Code and analysis are released; we make
no clinical-utility claims.

---

## Appendix / Reproducibility (outline)
- A. Prompt templates (parser, classifier, planner) — EXP1/EXP4.
- B. Evidence-function specifications and unit tests — EXP3.
- C. Belief-update equations and tuned weights — EXP5.
- D. Full per-condition, per-category tables — EXP8/EXP9.
- E. Agent trace schema; example traces — EXP4/EXP10.
- F. Failure-mode annotation guide + κ — EXP10.

## Figures and tables (asset map)
- Table 1 dataset · Table 2 evidence-function library (EXP3) · Table 3 system variants ·
  Table 4 overall accuracy (EXP8) · Table 5 category accuracy (EXP8) · Table 6 agentic
  efficiency (EXP4/6) · Table 7 ablations (EXP9) · Table 8 grounding/verification (EXP7) ·
  Table 9 failure taxonomy (EXP10).
- Figure 1 framework (`figures/fig1_framework.png`, ready) · Figure 2 vignette→trace mapping
  [TBD-EXP4] · Figure 3 control loop (`figures/fig3_control_loop.png`, ready) · Figure 4 belief
  update example [TBD-EXP5] · Figure 5 accuracy vs budget [TBD-EXP9] · Figure 6 category-gain
  heatmap [TBD-EXP8] · Figure 7 function-selection distribution [TBD-EXP4] · Figure 8
  contradiction vs error prob [TBD-EXP7] · Figure 9 example evidence trace [TBD-EXP10] ·
  Figure 10 ablation chart [TBD-EXP9]. Seed figure: oracle headroom
  (`figures/fig_seed_oracle_headroom.png`).

## Publication strategy (notes)
arXiv-first. Venues: ML4H, CHIL, AMIA (informatics), neuro-symbolic / KR workshops, medical-AI
workshops. **Minimum workshop package:** EXP1–EXP4 + EXP8 (a working agent vs static prompting
on some categories). **Full conference:** add EXP5–EXP7 and EXP9 (belief, verification,
ablations, budget). **Journal:** add EXP10 with clinician trace review and broader baselines.
