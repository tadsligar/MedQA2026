#!/usr/bin/env python3
"""
Test whether the NBME/USMLE-official competency rubric (v2) is more reliably annotatable than the
invented R/F/B/I/W operations. Sends lead-in + options for the 100 gold qids to gpt-5.4-mini under
the v2 rubric (MK/DX/MGMT/COMM/PROF/SBP/PBL with the official deterministic boundary rules), scores
vs the Claude v2 gold (results/reasoning_ops/gold_v2_labels.jsonl).

Baselines to beat: R/F/B/I/W fine κ=0.625 ; coarse K/I/W κ≈0.89.
Run:
  export OPENAI_API_KEY=sk-...  ; export CLASSIFIER_MODEL=gpt-5.4-mini
  python papers/paper4/analysis/validate_v2_labeling.py
"""
import os, json, re
from collections import Counter

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
MODEL = os.environ.get("CLASSIFIER_MODEL", "gpt-5.4-mini")
CODES = ["MK", "DX", "MGMT", "COMM", "PROF", "SBP", "PBL"]

RUBRIC = """You classify a USMLE multiple-choice question into ONE official USMLE Physician
Tasks/Competency, deciding from the LEAD-IN (final question sentence) + the answer-option types.

Codes (use the OFFICIAL boundaries — note the counterintuitive rules):
- MK  Medical Knowledge / foundational science: "given an effect, DETERMINE THE CAUSE",
      cause/infectious agent/predisposing factor, underlying process/pathway/MECHANISM, drug
      mechanism of action, GENETIC mechanism/INHERITANCE, identify the underlying ANATOMIC
      STRUCTURE/location from findings, nutritional basis. (Options are processes/mechanisms/
      structures/agents.)
- DX  Patient Care: Diagnosis: selects the most likely DIAGNOSIS (names a disorder); PREDICTS the
      most likely additional physical finding or lab/study RESULT; SELECTS/INTERPRETS a study to
      confirm dx (workup); PROGNOSIS/complications/natural history.
- MGMT Patient Care: Management: pharmacotherapy, treatment/clinical intervention, prevention/health
      maintenance/screening, mixed-management choice.
- COMM what to say to patient/family.   - PROF consent/confidentiality/autonomy/minors/reporting/ethics.
- SBP quality improvement / patient safety / care systems.   - PBL biostatistics/epidemiology/study design.

Deterministic rules:
- "most likely cause / underlying mechanism" with PROCESS/MECHANISM options -> MK; with NAMED-DISEASE
  options -> DX. "most likely diagnosis" -> DX. "predict the finding/lab result" -> DX.
- "which anatomic structure/muscle/location" -> MK. "inheritance / mechanism of action" -> MK.
- "next step": study options -> DX(workup); treatment options -> MGMT.
- ethics->PROF ; what-to-say->COMM ; statistics/study-design->PBL.

Respond with ONLY a JSON object: {"competency":"<MK|DX|MGMT|COMM|PROF|SBP|PBL>"}"""

# Two conditions: V2_RULES=1 (default) gives the deterministic tie-break rules (tests rule-governed
# REPRODUCIBILITY); V2_RULES=0 strips them (tests independent CONSTRUCT convergence). Run both and
# compare the kappas — the gap is how much the explicit rules are doing the work.
if os.environ.get("V2_RULES", "1") == "0":
    RUBRIC = RUBRIC.split("Deterministic rules:")[0].rstrip() + \
        '\n\nRespond with ONLY a JSON object: {"competency":"<MK|DX|MGMT|COMM|PROF|SBP|PBL>"}'


def parse(t):
    m = re.search(r"\{.*\}", t, re.S)
    if not m: return None
    try: o = json.loads(m.group(0))
    except Exception: return None
    return o.get("competency") if o.get("competency") in CODES else None


def kappa(pairs):
    N = len(pairs); po = sum(1 for a, b in pairs if a == b)/N
    ga = Counter(a for a, _ in pairs); gb = Counter(b for _, b in pairs)
    pe = sum((ga[c]/N)*(gb[c]/N) for c in set(list(ga)+list(gb)))
    return (po-pe)/(1-pe) if pe < 1 else 1.0


def main():
    from openai import OpenAI
    c = OpenAI()
    views = {json.loads(l)["qid"]: json.loads(l) for l in
             open(os.path.join(REPO, "results/reasoning_ops/gold_op_views.jsonl"))}
    gold = {json.loads(l)["qid"]: json.loads(l)["competency"] for l in
            open(os.path.join(REPO, "results/reasoning_ops/gold_v2_labels.jsonl"))}
    pairs, lab = [], {}
    for qid, g in gold.items():
        v = views[qid]
        user = f"Question (final sentence only): {v['ask']}\n\nOptions:\n{v['options']}"
        r = c.chat.completions.create(model=MODEL, reasoning_effort="none", max_completion_tokens=400,
                                      messages=[{"role": "system", "content": RUBRIC},
                                                {"role": "user", "content": user}])
        p = parse(r.choices[0].message.content); lab[qid] = p or "?"
        if p: pairs.append((g, p))
    agree = sum(1 for a, b in pairs if a == b)
    mode = "RULES OFF (construct)" if os.environ.get("V2_RULES", "1") == "0" else "RULES ON (reproducibility)"
    print(f"v2 [{mode}] lead-in vs Claude v2 gold: {agree}/{len(pairs)} = "
          f"{100*agree/len(pairs):.1f}%  kappa={kappa(pairs):.3f}")
    print("baselines: R/F/B/I/W fine=0.625 ; coarse K/I/W=0.89")
    print("\nConfusion (gold rows, gpt cols):")
    cs = [c_ for c_ in CODES if any(g == c_ for g in gold.values())]
    print("     "+"  ".join(f"{c_:>4}" for c_ in cs))
    for g in cs:
        row = Counter(b for a, b in pairs if a == g)
        print(f"{g:>4} "+"  ".join(f"{row.get(c_,0):>4}" for c_ in cs))
    # MK-vs-DX specific agreement (the boundary that matters)
    mkdx = [(a, b) for a, b in pairs if a in ("MK", "DX") and b in ("MK", "DX")]
    if mkdx:
        ag = sum(1 for a, b in mkdx if a == b)
        print(f"\nMK-vs-DX only: {ag}/{len(mkdx)} = {100*ag/len(mkdx):.1f}%  kappa={kappa(mkdx):.3f}")
    json.dump({str(k): v for k, v in lab.items()},
              open(os.path.join(REPO, "results/reasoning_ops/.v2_gold_probe.json"), "w"))


if __name__ == "__main__":
    main()
