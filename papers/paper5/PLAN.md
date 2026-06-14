# Paper 5 — Research Plan: Competency-Routed Reasoning Orchestration

**Working title:** *Route, Then Reason: Lead-In-Conditioned Orchestration for Medical QA — and the
Limits of Competency Routing.*

> Builds directly on Paper 4's validated competency labeling (κ=0.83). Numbers are placeholders
> until run.
>
> **Headroom note (corrected):** Paper 4's ~2–3 pp is only how unevenly the *base* model handles
> competencies with no orchestration. It does NOT cap how much a tailored scaffold can help — a
> scaffold targets the ~30–35 pp gap between current accuracy and 100%, and may lift any competency
> by any amount (or none). The relevant open question is empirical: does a competency-matched
> scaffold beat a uniform prompt (and the best single scaffold applied to all)? That requires
> actually running the scaffolds — there is no cheap pre-check that bounds it.

## 1. Positioning
Paper 4 produced a reliable, NBME-grounded competency labeling read off the question lead-in.
Paper 5 asks the natural systems question: if we *route* each question on its lead-in to a
**competency-matched reasoning scaffold**, do we beat uniform prompting? The contribution is a
clean, reproducible orchestration framework + an honest measurement of how much (little) routing
buys on a benchmark where reasoning type barely moves accuracy — plus whatever it buys in
calibration, stability, interpretability, and compute.

## 2. Title options
1. *Route, Then Reason: Lead-In-Conditioned Orchestration for Medical QA.*
2. *Does Competency Routing Help? An Honest Test of Reasoning-Matched Orchestration on MedQA.*
3. *The Oracle-Routing Ceiling: How Much Can Competency-Aware Orchestration Gain?*

## 3. Draft abstract (placeholder)
We test whether routing medical-QA questions to competency-matched reasoning scaffolds improves
base-LLM accuracy. A cheap router reads the NBME **lead-in** and assigns one of the official USMLE
competencies (validated κ=0.83, Paper 4); each competency is dispatched to a matched strategy —
diagnosis→generate-and-rank differential, medical-knowledge→UMLS ontology/mechanism lookup,
management→guideline/contraindication check — reusing our neuro-symbolic modules. We compare
against (i) a uniform prompt, (ii) the single best overall strategy, and (iii) an **oracle-routing
upper bound** that quantifies the maximum achievable gain. We find [TBD]. Consistent with Paper 4,
the accuracy headroom for routing is small; we therefore also report calibration, run-to-run
stability, interpretability of the per-competency trace, and the compute overhead of routing.

## 4. Architecture
```
question ──► parse(stem, lead-in) ──► ROUTER (lead-in → competency, the Paper-4 labeler, live)
                                          │
        ┌─────────────────┬───────────────┼────────────────┬───────────────┐
       DX                MK              MGMT             W/COMM/...        (fallback)
 generate-and-rank   UMLS ontology /   guideline /     direct / light    uniform prompt
 differential        mechanism path    contraindication  default
 (base-rate weight)  lookup+verify     check
        └─────────────────┴───────────────┴────────────────┴───────────────┘
                                   answer + per-competency reasoning trace
```
Reuse: Paper 2 UMLS grounding/verifier for MK/MGMT scaffolds; Paper 3 belief/controller for DX.

## 5. Conditions & baselines (the honest design)
1. **Uniform** — one fixed prompt for all (Paper 1 base prompt).
2. **Best-single** — the single strategy with the best *overall* accuracy, applied to everything
   (controls for "the scaffold is just better," independent of routing).
3. **Routed** — competency-matched dispatch (the proposed system).
4. **Best-per-competency selection (routing upper bound, post-hoc)** — AFTER running the candidate
   strategies, route on *gold* competency and pick, per competency, whichever strategy scored best.
   This bounds only the *routing decision* over the strategies we actually ran (i.e. "did routing
   pick well"), NOT how good a scaffold could ever be. It is computed from the strategy runs, so it
   is not a cheap pre-check and does not gate the work.
5. **Router-ablation** — routed with the *live* lead-in router vs gold labels, to separate router
   error from scaffold value.

## 6. Metrics
- Accuracy overall and **by competency** (Wilson CIs); Routed−Uniform and Routed−BestSingle (paired
  McNemar, bootstrap CI); gain *concentration* on MK (the Paper-4 weak spot).
- **Router accuracy** live vs gold (it's the Paper-4 labeler; report κ/accuracy + error cost).
- **Oracle ceiling** (condition 4) — the max gain; the key honesty number.
- Non-accuracy: calibration (ECE) and run-to-run stability by condition; **compute overhead**
  (extra tokens/calls/UMLS lookups per routed question); interpretability (does the trace help?).

## 7. Datasets & models
- Focused-1,030 for fast iteration; full 12,723 + **held-out test split (1,273)** for the headline
  (contamination-clean). Models: start Qwen2.5 14B/32B (where Paper 4's MK effect was clearest);
  extend to the 5-model panel if signal warrants.

## 8. What runs where
- **CPU/local:** router (lead-in labeler, already built), oracle-ceiling analysis on existing runs
  (estimate the from per-competency-best-strategy if strategy runs exist), trace/interpretability,
  cost accounting.
- **AIAU GPU (new runs):** the scaffold executions (generate-and-rank, UMLS-augmented prompts,
  guideline checks) via vLLM. This is the compute-bearing core. Reuse Paper 2/3 SLURM patterns.

## 9. Expected contributions
- A reproducible lead-in-routed orchestration framework for medical QA.
- An **oracle-ceiling** result bounding how much competency routing can help (likely modest — a
  useful, honest community signal).
- If routing helps: evidence it concentrates on the model's weak competency (MK).
- Non-accuracy benefits (calibration/stability/interpretability/cost) reported regardless.

## 10. Limitations
- Paper 4 ⇒ small accuracy headroom; a null is plausible and acceptable. MCQ ≠ free-form. Routing
  adds compute; net value must weigh overhead. Scaffolds reuse unproven Paper 2/3 components —
  validate those first. Full set includes train (use test-split for the clean headline).

## 11. Build order
1. Live router = Paper-4 labeler wrapper (CPU; done-ish).
2. Implement the competency scaffolds (reuse Paper 2/3 modules) — start with ONE high-value
   scaffold (e.g. UMLS mechanism lookup for MK, the model's relative weak spot) as a pilot.
3. **Pilot on focused-1,030, one model (Qwen 14B)** — cheapest real test of "does any scaffold beat
   uniform on its target competency?" before scaling. This is the go/no-go, and it requires GPU
   (there's no analysis-only shortcut, per the headroom note).
4. If the pilot shows lift, expand scaffolds + models + full/test split via SLURM.
5. Analysis (per-competency Routed−Uniform, McNemar/bootstrap; best-per-competency upper bound;
   calibration/stability/cost) + figures + DRAFT.
