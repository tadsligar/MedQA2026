# Paper 4 — labeling rationale: the lead-in determines the reasoning operation

## The principle (why the last sentence is the right signal)
USMLE/NBME items have two parts: a **stem** (the clinical vignette) and a **lead-in** (the final
question sentence). The **NBME Item-Writing Guide** prescribes a *"closed lead-in,"* whose explicit
purpose is to "direct the focus and grammatical form of the answer options," producing homogeneous
options the test-taker weighs "within a single mindset." In other words, the lead-in is *designed*
to fix the answer type. So classifying a question's reasoning **operation** from its lead-in is not
an arbitrary shortcut — it is reading the cue the item was constructed around.

This resolves the gpt-vs-Claude labeling disagreement (κ=0.625; F/B the weak boundary, see
`VALIDATION.md`). The disagreements were a *convention* conflict, not random noise:
- The rubric instructs labeling from the **lead-in + answer-option types** (surface rule).
- gpt-5.4-mini frequently drifted to a **whole-stem diagnostic reading** (e.g. qid 11794, 11578:
  the stem is a diagnosis, so it answered B even though the lead-in asks for a mechanism/inheritance).
We adopt the **lead-in rule explicitly** (NBME-grounded) and treat whole-stem drift as the deviation.
Under the lead-in rule, the operation labels are far more separable and reproducible.

## Operation ↔ lead-in mapping (the routing signal)
| Operation | Prototypical lead-in (final sentence) |
|---|---|
| R Recognition | "most likely to show / expected finding / will be detected" |
| F Mechanistic (forward) | "mechanism of / which process is responsible / pathogenesis" |
| B Diagnostic (backward) | "most likely diagnosis / most likely cause of this condition" |
| I Interventional | "best treatment / most appropriate next step in management" |
| W Workup | "best initial test / most appropriate next step in diagnosis" |

## Prior work (precedent + what's novel)
Established / citable:
- **NBME Item-Writing Guide** — the closed-lead-in principle (the methodological anchor).
- MedQA classified by lead-in phrasing: prior analyses isolate "diagnosis" items by the literal
  word "diagnosis" in the query (dominant lead-ins: "which of the following is the most likely
  diagnosis?" ~588; "what is the most likely diagnosis?" ~131).
- **MedMCQA** ships explicit reasoning-type labels (Treatment, Diagnosis, …).
- USMLE-Physician-Task stratifications of LLM MedQA accuracy (Diagnosis / Pharmacotherapy &
  Management / Foundational-Science / Health-Maintenance) with 95% CIs already exist.

Apparently novel (our contribution):
1. Framing the split as a **causal-inference taxonomy** (forward/deduction vs backward/abduction
   vs interventional), not just descriptive buckets.
2. **Validating** the lead-in labeling with inter-annotator agreement (κ, two independent models +
   a human gold set) — labeling reliability is normally unreported.
3. Testing a **directional asymmetry** in model accuracy across operations.
4. A **lead-in-conditioned reasoning orchestration** (route on the lead-in → operation-specific
   solver) as the constructive payoff (see PLAN §6.6).

> Caveat: a proper related-work pass is still required before claiming novelty (esp. vs the
> USMLE-competency stratification papers and MedMCQA's reasoning-type labels).

## Sources
- NBME Item-Writing Guide: https://www.nbme.org/sites/default/files/2021-02/NBME_Item%20Writing%20Guide_R_6.pdf
- MedMCQA (reasoning-type labels): https://arxiv.org/pdf/2203.14371
- Counting Clues (MedQA lead-in / diagnosis-subset analysis): https://arxiv.org/pdf/2512.12868
- Medical LLM benchmarks & construct validity: https://arxiv.org/pdf/2503.10694
