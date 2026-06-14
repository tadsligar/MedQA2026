# USMLE Competency Rubric v2 — verbatim-grounded prompt (NBME/USMLE official)

Source: **USMLE Physician Tasks/Competencies** (FSMB/NBME, 2025 public release). This v2 replaces the
invented causal-inference operations (R/F/B/I/W), which proved unreliable (κ≈0.63; the
recognition/deduction/abduction split cuts *across* the official categories). v2 uses the official
competencies with **verbatim subtask definitions** and the **counterintuitive deterministic rules**
that resolve the boundaries annotators previously fought over.

Decide from the **lead-in (final question sentence)** + **answer-option types** (NBME "cover-the-options"
rule). Pick exactly ONE primary competency.

## Categories (official) + verbatim subtask cues
- **MK — Medical Knowledge / Applying Foundational Science.** Choose MK when the question asks for the
  *scientific basis*, even of a patient case:
  - "given an effect, **determines the cause**"; "identifies the cause / infectious agent / predisposing factor"
  - "underlying processes / pathways / **mechanisms**"; drug **mechanism of action**
  - **genetic mechanisms / inheritance** of a condition
  - given clinical/physical findings, **identify the underlying anatomic structure / cell-tissue / location**
  - nutritional underpinnings of disease
  ⇒ lead-ins: "most likely cause of …", "mechanism responsible", "which process/pathway", "inheritance
     pattern", "which structure is injured", "mechanism of action".

- **DX — Patient Care: Diagnosis.** Choose DX for the clinical diagnostic *products* (not the science):
  - `formulate`: "selects the most likely **diagnosis**" (names a disorder)
  - `hx_pe`: "predicts the most likely **additional physical finding**"
  - `labs`: "selects/interprets a **study** to confirm dx" OR "predicts the most likely **lab/study result**"
  - `prognosis`: complications, natural history, severity, factors affecting outcome
  ⇒ lead-ins: "most likely diagnosis", "most likely to show / reveal (finding/lab)", "best test to confirm",
     "at greatest risk for (complication)".

- **MGMT — Patient Care: Management.** pharmacotherapy, clinical interventions/treatment, health
  maintenance & prevention, **mixed management** (choose among studies/drugs/procedures/observation/referral).
  ⇒ lead-ins: "most appropriate treatment / pharmacotherapy", "next step in management", "best initial treatment".

- **COMM** — what to say (response/counseling/breaking news/interpreter).
- **PROF** — consent, confidentiality, autonomy/refusal, minors, reporting, death & dying.
- **SBP** — quality improvement, error/near-miss, patient safety, care settings/teams.
- **PBL** — biostatistics/epidemiology, study design/flaws, screening-test math, literature interpretation.

## Deterministic boundary rules (the ones that fixed the disagreements)
1. **"most likely cause / determine the cause / underlying mechanism" → MK** (foundational science),
   NOT Diagnosis — even within a clinical vignette. (Resolves the old F-vs-B fight, per the official
   "given an effect, determines the cause" subtask.)
2. **"most likely diagnosis" (name the disorder) → DX.** Only naming the disease is DX-formulate.
3. **"predict the finding / lab / study result" → DX** (hx_pe or labs), NOT MK and NOT a separate
   "recognition" class. (Removes the old R↔B ambiguity — predicting a finding is a Diagnosis subtask.)
4. **"which anatomic structure / muscle / location" from findings → MK** (foundational anatomy),
   not DX.
5. **"genetic inheritance / mechanism of action" → MK.**
6. **"next step in management": options are studies → DX(labs-select); options are treatments → MGMT.**
7. Ethics/consent → PROF; what-to-say → COMM; stats/study-design → PBL.

## Why this should be reliable (vs R/F/B)
The official MK/DX/MGMT boundary is "explain the science (MK) vs name the disease / predict the finding
(DX) vs act (MGMT)" — authoritative, item-writer-native, and each boundary case has a verbatim rule.
It does NOT require the recognition/deduction/abduction distinction that two annotators could not draw.

## Test plan
Relabel the 100-item gold under v2 (Claude, independent) + run gpt-5.4-mini under v2 on the same 100;
compute κ. Target: MK/DX/MGMT κ ≥ 0.8 (vs 0.63 for R/F/B). If met, adopt v2 for the full set; the
reliable MK-vs-DX-vs-MGMT axis can then carry the analysis (and a *reliable* version of the
"apply-science vs diagnose vs manage" reasoning contrast).
