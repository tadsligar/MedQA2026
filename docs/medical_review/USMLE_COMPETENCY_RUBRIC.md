# USMLE Physician-Competency Labeling Rubric (authoritative)

Source of truth: **USMLE Physician Tasks/Competencies** outline (FSMB/NBME, 2025 public release,
`https://www.usmle.org/usmle-physician-taskscompetencies`). MedQA provides **no** reasoning-type
labels (only `meta_info` = exam step). We assign each question to one official competency, using
the verbatim USMLE sub-tasks as decision criteria. A finer `subtask` is also recorded.

The category is decided by **what the question asks you to produce** (the final "ask" sentence)
together with **what the answer options are** (mechanisms vs findings vs studies vs diagnoses vs
treatments).

## The 7 competencies (label set) + sub-tasks and cues

1. **Medical Knowledge / Scientific Concepts** (`MK`)
   Applying foundational science: mechanisms, pathways, drug mechanism of action, genetics,
   "given an effect, determine the cause", anatomic/physiologic basis.
   Cues: "mechanism of action", "underlying mechanism/pathway", "second messenger", "most
   likely cause" when options are *processes/mechanisms*, inheritance pattern, "site of action".
   Subtasks: foundational_science.

2. **Patient Care: Diagnosis** (`PC_DX`) — four sub-tasks:
   - `hx_pe` History & Physical: "predict the most likely additional physical finding / sign".
   - `labs_dx_studies` Laboratory & diagnostic studies: **select** most appropriate study to
     confirm dx, **interpret** a study, **predict** the most likely lab/study result.
   - `formulate_dx` Formulating the diagnosis: "most likely diagnosis", identify disorder/organism.
   - `prognosis` Prognosis/outcome: complications, natural history, severity, prognostic factors.
   Cues: "most likely diagnosis", "most likely to show/reveal", "serum X closest to", "biopsy
   shows", "most likely additional finding", "complication at greatest risk for".

3. **Patient Care: Management** (`PC_MGMT`) — sub-tasks:
   - `health_maint_prevention` screening/prevention/vaccines/risk-reduction in a not-yet-affected patient.
   - `pharmacotherapy` select drug, adverse effects, contraindications, dosing, monitoring.
   - `clinical_interventions` treatment/procedure/surgery, acute/emergency management, follow-up.
   - `mixed_management` choose among a mix (studies/drugs/procedures/observation/referral).
   Cues: "best/most appropriate treatment/management", "next step in management" when options are
   *therapies*, "which drug", "most appropriate pharmacotherapy", "would have prevented".

4. **Communication & Interpersonal Skills** (`COMM`)
   "Most appropriate response/statement by the physician", breaking news, counseling, using an
   interpreter, supporting emotions.

5. **Professionalism, Legal & Ethical** (`PROF`)
   Informed consent, confidentiality, autonomy/refusal, advance directives, involuntary admission,
   reporting, impaired/erring colleagues, minors.

6. **Systems-based Practice & Patient Safety** (`SBP`)
   Quality improvement, error/near-miss analysis, teams, care settings/handoffs, patient safety.

7. **Practice-based Learning** (`PBL`)
   Biostatistics & epidemiology, study design/flaws, screening-test math (sens/spec/PPV/NPV,
   RR/OR/NNT), interpreting the medical literature, research ethics/regulatory.

## Tie-breakers (decide by OPTIONS)
- "next step in management" → options are **diagnostic studies** ⇒ PC_DX/`labs_dx_studies`;
  options are **treatments/procedures** ⇒ PC_MGMT.
- "most likely cause" → options are **diseases/organisms** ⇒ PC_DX/`formulate_dx`; options are
  **mechanisms/processes** ⇒ MK.
- "predict the lab/finding result" ⇒ PC_DX (`labs_dx_studies` or `hx_pe`), NOT MK.
- Ethics/consent ⇒ PROF; "what to say" ⇒ COMM; statistics/study ⇒ PBL.

## Output schema (per question)
`{"qid": <int question_id>, "competency": <one of MK,PC_DX,PC_MGMT,COMM,PROF,SBP,PBL>,
  "subtask": <string>, "confidence": "high|med|low", "reason": "<=15 words"}`

## Coarse → fine map (for analysis)
- `MK` ↔ "Mechanism/Pathophysiology"
- `PC_DX/formulate_dx` ↔ "Diagnosis"; `PC_DX/hx_pe` + `PC_DX/labs_dx_studies(predict)` +
  `PC_DX/prognosis` ↔ "Clinical Findings"; `PC_DX/labs_dx_studies(select)` ↔ "Next Step/Workup"
- `PC_MGMT` ↔ "Treatment/Management"
- `COMM`, `PROF`, `SBP`, `PBL` ↔ non-clinical-reasoning competencies (reported separately)

The two-level scheme lets Paper 1 report the **7 official competencies** (natural distribution)
and the **5 reasoning sub-categories** (well-populated) from one labeling pass.
