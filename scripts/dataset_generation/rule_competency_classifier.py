#!/usr/bin/env python3
"""
Rule-based USMLE Physician-Competency classifier (NO API, NO GPU).

Encodes the USMLE competency rubric (docs/medical_review/USMLE_COMPETENCY_RUBRIC.md) as
high-precision heuristics over each question's final "ask" sentence + the TYPE of its answer
options. Far stronger than the original 5-keyword matcher; intended as a fast, free, reproducible
labeling that is then validated against a Claude-labeled gold sample.

Output (same schema as the API classifier so the analysis just works):
  results/category_relabel/competency_labels_rule.jsonl
  {"qid","competency","subtask","confidence","reason","model":"rule_v1"}

Competency codes: MK, PC_DX, PC_MGMT, COMM, PROF, SBP, PBL
"""
import os, json, re, argparse

# ---------- option-type detectors ----------
DRUG_RE = re.compile(r"\b\w+(cillin|mycin|micin|prazole|olol|pril|sartan|statin|tinib|ciclib|"
                     r"mab|nib|parin|azepam|azolam|cycline|conazole|vir|dipine|caine|"
                     r"floxacin|triptan|glitazone|gliptin|metformin|insulin|warfarin|heparin|"
                     r"aspirin|acetaminophen|ibuprofen|prednisone|prednisolone|epinephrine|"
                     r"atropine|naloxone|digoxin|furosemide|enalapril)\b", re.I)
TREAT_WORD = re.compile(r"\b(therapy|treatment|vaccine|surgery|resection|transplant|dialysis|"
                        r"chemotherapy|radiation|antibiotic|transfusion|reassurance|observation|"
                        r"discontinue|administer|prescribe|initiate|cesarean|drainage|repair)\b", re.I)
TEST_WORD = re.compile(r"\b(ct|mri|x-?ray|ultrasound|echocardiograph|endoscop|colonoscop|biopsy|"
                       r"ecg|ekg|culture|smear|titer|antibody|serolog|panel|assay|scan|imaging|"
                       r"radiograph|angiograph|lumbar puncture|paracentesis|aspiration|"
                       r"\blevel\b|\btest\b|\bstudy\b|electromyograph|spirometry)\b", re.I)
LABVAL_RE = re.compile(r"\d+\s*(mg/dl|mg/dL|mmol|mEq|g/dl|g/dL|%|/min|mm hg|mmhg|ng/ml|iu/l|u/l|cells)", re.I)
QUOTE_RE = re.compile(r'^\s*[\"“‘\']')
# mechanism/process-type option (foundational science answer, not a named disease/finding/drug)
MECH_RE = re.compile(r"^\s*(inhibition of|activation of|deficiency of|loss of|impaired |defective |"
                     r"absence of|reduced |reduction of|decreased |increased |excessive |overproduction|"
                     r"underproduction|insensitivity|resistance to|accumulation of|depletion of|"
                     r"degradation of|upregulation|downregulation|blockade of|stimulation of|"
                     r"end-organ|monosomy|mosaicism|nondisjunction|agenesis of|inactivation of)", re.I)

def opt_types(options):
    vals = list(options.values()) if isinstance(options, dict) else list(options)
    t = {"drug": 0, "treat": 0, "test": 0, "labval": 0, "quote": 0, "mech": 0, "n": len(vals)}
    for v in vals:
        v = str(v)
        if QUOTE_RE.search(v): t["quote"] += 1
        if DRUG_RE.search(v): t["drug"] += 1
        if TREAT_WORD.search(v): t["treat"] += 1
        if TEST_WORD.search(v): t["test"] += 1
        if LABVAL_RE.search(v): t["labval"] += 1
        if MECH_RE.search(v): t["mech"] += 1
    return t

def ask_of(q):
    parts = re.split(r'(?<=[.?!])\s+', q.strip())
    qs = [p for p in parts if p.strip().endswith('?')]
    return (qs[-1] if qs else parts[-1]).lower()

def has(s, *subs): return any(x in s for x in subs)

# ---------- main classifier ----------
def classify(question, options):
    a = ask_of(question); full = question.lower(); ot = opt_types(options)
    def L(comp, sub, conf, why): return {"competency": comp, "subtask": sub, "confidence": conf, "reason": why}

    # 1) Practice-based learning / biostatistics (high precision)
    if re.search(r"relative risk|odds ratio|number needed|positive predictive|negative predictive|"
                 r"sensitivity|specificity|confidence interval|\bp-?value\b|study design|"
                 r"selection bias|confounding|incidence of|prevalence of|hazard ratio|"
                 r"absolute risk|likelihood ratio|number needed to treat", a+" "+full):
        return L("PBL", "biostatistics_epi", "high", "statistics/epidemiology")
    # 2) Professionalism / legal / ethical (checked BEFORE COMM: ethics content phrased as a "response"
    #    must not be stolen by the quote/response heuristic). Tightened vocabulary to avoid eating
    #    genuine counseling items.
    if has(a+" "+full, "informed consent", "consent for the procedure", "get consent", "obtain consent",
           "confidential", "autonomy", "advance directive", "refuse treatment", "refuse testing",
           "refuse the", "decision-making capacity", "capacity to make", "against medical advice",
           "ethics committee", "ethical principle", "principles of medical ethics", "involuntary",
           "report to", "mandatory report", "duty to warn", "child protective", "court order",
           "health care proxy", "healthcare proxy", "power of attorney", "next of kin", "guardian",
           "parental permission", "parents' consent", "jehovah", "do not resuscitate", "minor",
           "accept these gifts", "accept the", "surrogate", "competence to", "release information",
           "release of information"):
        return L("PROF", "legal_ethical", "high", "ethics/legal/consent")
    # 3) Communication (what to SAY) — only after PROF
    if (ot["quote"] >= 2) or has(a, "most appropriate response", "best response", "most appropriate statement",
                                 "how should the physician respond", "what should you say", "respond to the patient",
                                 "best response to", "appropriate response to"):
        return L("COMM", "communication", "high", "physician response/statement")
    # 4) Systems-based practice / safety
    if has(a+" "+full, "patient safety", "quality improvement", "root cause", "near miss",
           "medical error", "sentinel event", "systems-based"):
        return L("SBP", "patient_safety", "med", "systems/safety")

    # 5) Mechanism / Medical Knowledge — strong ask-cues OR (cause/explanation ask + mechanism-type options)
    mk_ask = has(a, "mechanism of action", "second messenger", "site of action", "mechanism by which",
                 "most likely mechanism", "pathophysiolog", "pathway", "responsible for the",
                 "responsible for", "mode of action", "mechanism responsible", "underlying mechanism",
                 "mechanism of", "which mechanism", "inheritance", "explains the", "best explains",
                 "explanation for this finding", "pathogenesis", "process is responsible")
    cause_ask = has(a, "underlying cause", "most likely cause", "underlying mechanism", "responsible for",
                    "explanation", "explains", "indication of")
    if mk_ask and not (ot["drug"] + ot["test"] >= 3):
        return L("MK", "foundational_science", "high", "mechanism/pathophysiology")
    # cause/underlying-cause question whose OPTIONS are mechanisms/processes (not named diseases) -> MK
    if cause_ask and ot["mech"] >= 2 and ot["mech"] >= ot["test"] and ot["drug"] == 0:
        return L("MK", "foundational_science", "med", "cause via mechanism-type options")

    # 6) Diagnosis (formulate)
    if has(a, "most likely diagnosis", "is the diagnosis", "most likely underlying condition",
           "most likely organism", "most likely pathogen", "causal organism", "bacterium responsible") or \
       (has(a, "most likely cause", "most likely etiolog", "underlying cause") and ot["drug"]+ot["test"] == 0
        and ot["mech"] < 2):
        return L("PC_DX", "formulate_dx", "high", "name the diagnosis/cause")

    # 7) Next Step / Workup vs Treatment — decide by ask + option type
    is_nextstep = has(a, "next step", "next best step", "initial step", "first step",
                      "most appropriate next", "best initial test", "initial diagnostic",
                      "most appropriate investigation", "confirm the diagnosis", "to establish the diagnosis",
                      "most appropriate study", "diagnostic test")
    is_treat = has(a, "treatment", "manage", "management", "pharmacotherap", "which drug",
                   "which medication", "best therapy", "definitive", "most appropriate therapy",
                   "first-line", "prevent", "prophylaxis")
    if is_nextstep and not is_treat:
        # if options are clearly treatments -> management; if tests -> workup
        if ot["test"] >= ot["drug"] + ot["treat"]:
            return L("PC_DX", "labs_dx_studies_select", "high", "select diagnostic next step")
        if ot["drug"] + ot["treat"] >= 2:
            return L("PC_MGMT", "clinical_interventions", "med", "next step is treatment")
        return L("PC_DX", "labs_dx_studies_select", "med", "next diagnostic step")
    if is_treat:
        if has(a, "prevent", "prophylaxis", "screening", "vaccin"):
            return L("PC_MGMT", "health_maint_prevention", "high", "prevention/screening")
        return L("PC_MGMT", "pharmacotherapy" if (ot["drug"] >= ot["test"]) else "clinical_interventions",
                 "high", "treatment/management")
    if is_nextstep and is_treat:
        return L("PC_MGMT", "mixed_management", "med", "mixed next-step management")

    # 8) Clinical Findings (predict/observe) — labs, exam, biopsy, complication, prognosis
    if has(a, "most likely to show", "most likely to reveal", "expected finding", "most likely finding",
           "additional finding", "most likely additional", "would you expect", "biopsy is most likely",
           "examination is most likely", "auscultation", "most likely to be present", "closest to which",
           "complication", "at greatest risk", "most at risk", "laboratory findings", "would most expect",
           "histolog", "is most likely associated"):
        sub = "prognosis" if has(a, "complication", "at risk", "prognos", "natural history", "mortality") else \
              ("labs_dx_studies_predict" if (ot["labval"] >= 1 or ot["test"] >= 1) else "hx_pe")
        return L("PC_DX", sub, "med", "predict/observe finding")

    # 9) fall-throughs by option type
    if ot["drug"] + ot["treat"] >= 3:
        return L("PC_MGMT", "clinical_interventions", "low", "treatment-type options")
    if ot["test"] >= 3:
        return L("PC_DX", "labs_dx_studies_select", "low", "test-type options")
    if has(a, "cause", "explanation", "explains"):
        return L("PC_DX", "formulate_dx", "low", "cause/explanation default")
    return L("PC_DX", "formulate_dx", "low", "default")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="data/datasets/medqa_full_combined.json")
    ap.add_argument("--output", default="results/category_relabel/competency_labels_rule.jsonl")
    args = ap.parse_args()
    data = json.load(open(args.dataset, encoding="utf-8"))
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    from collections import Counter
    dist = Counter()
    with open(args.output, "w", encoding="utf-8") as f:
        for i, q in enumerate(data):
            qid = int(q.get("question_id", i))
            r = classify(q["question"], q["options"])
            dist[r["competency"]] += 1
            f.write(json.dumps({"qid": qid, **r, "model": "rule_v1"}, ensure_ascii=False) + "\n")
    print(f"labeled {len(data)} -> {args.output}")
    print("distribution:", dict(dist))


if __name__ == "__main__":
    main()
