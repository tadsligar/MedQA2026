"""
Paper 3 EXP3 — evidence-function library.

Each evidence function inspects the parsed case + grounded candidate analyses + UMLS index
and returns a per-candidate signed delta dict {letter: float} (positive = support, negative =
penalty) plus a short detail string. The agent controller calls these adaptively and folds
the deltas into the belief state (EXP4/EXP5).

Reuses Paper 2's grounding, relation sets, and verifiers so the agent and the static
neuro-symbolic systems share one symbolic substrate.

Each function signature: fn(case, analyses, idx) -> (deltas: dict[letter,float], detail: str)
where `analyses[letter]` carries candidate_cuis, candidate_text, support_cuis, contradict_cuis
(built by cove.build_candidate_analyses) and `case` carries category, age, sex,
grounding_coverage, stem_concepts.
"""
import sys, os
_V = os.path.join(os.path.dirname(__file__), "..", "..", "umls_verifier", "src")
sys.path.insert(0, _V)
from verifiers import (v_demographic, v_type_incompatibility, v_polarity,  # noqa
                       v_internal_contradiction, v_low_coverage)

LETTERS = ["A", "B", "C", "D"]


def _rel_support(case, analyses, idx, relas, sign=1.0):
    """Generic: +sign for each stem concept related to a candidate via any RELA in `relas`."""
    deltas = {l: 0.0 for l in LETTERS}
    stem = [c["cui"] for c in case.get("stem_concepts", [])]
    for l, a in analyses.items():
        for o in a["candidate_cuis"]:
            for s in stem:
                if any(idx.has_relation(o, s, r) or idx.has_relation(s, o, r) for r in relas):
                    deltas[l] += sign
    return deltas


def check_symptom_support(case, analyses, idx):
    d = _rel_support(case, analyses, idx, ["manifestation_of", "has_finding", "disease_has_finding"])
    return d, "symptom/finding relation support"


def check_lab_support(case, analyses, idx):
    # lightweight: reward candidates whose grounded concept is a lab/finding type
    deltas = {l: 0.0 for l in LETTERS}
    for l, a in analyses.items():
        for cui in a["candidate_cuis"]:
            stys = {s[1] for s in idx.semtypes(cui)}
            if stys & {"Laboratory Procedure", "Laboratory or Test Result", "Finding"}:
                deltas[l] += 0.5
    return deltas, "lab/finding semantic-type support"


def check_temporal_consistency(case, analyses, idx):
    # symbolic UMLS has weak temporal signal; neutral here (LLM policy can override). No-op delta.
    return {l: 0.0 for l in LETTERS}, "temporal (neutral without LLM)"


def check_pathophysiology_chain(case, analyses, idx):
    d = _rel_support(case, analyses, idx, ["has_mechanism_of_action", "causes", "associated_with"])
    return d, "pathophysiology/mechanism chain"


def check_disease_finding_relation(case, analyses, idx):
    d = _rel_support(case, analyses, idx, ["manifestation_of", "has_finding"])
    return d, "disease<->finding relation"


def check_treatment_indication(case, analyses, idx):
    d = _rel_support(case, analyses, idx, ["may_treat", "may_prevent"])
    return d, "treatment indication (may_treat)"


def check_treatment_contraindication(case, analyses, idx):
    d = _rel_support(case, analyses, idx, ["contraindicated_with"], sign=-1.5)
    return d, "treatment contraindication penalty"


def check_next_best_test(case, analyses, idx):
    deltas = {l: 0.0 for l in LETTERS}
    for l, a in analyses.items():
        for cui in a["candidate_cuis"]:
            stys = {s[1] for s in idx.semtypes(cui)}
            if stys & {"Diagnostic Procedure", "Laboratory Procedure"}:
                deltas[l] += 0.5
    return deltas, "next-best-test (procedure type)"


def check_mechanism_consistency(case, analyses, idx):
    d = _rel_support(case, analyses, idx, ["causes", "associated_with"])
    return d, "mechanism consistency"


def check_answer_semantic_type(case, analyses, idx):
    deltas = {l: 0.0 for l in LETTERS}
    for l, a in analyses.items():
        v = v_type_incompatibility(a, case, idx)
        if v:
            deltas[l] -= v[0]["severity"]
    return deltas, "answer semantic-type compatibility"


def check_demographic_plausibility(case, analyses, idx):
    deltas = {l: 0.0 for l in LETTERS}
    for l, a in analyses.items():
        v = v_demographic(a, case, idx)
        if v:
            deltas[l] -= v[0]["severity"]
    return deltas, "demographic plausibility"


def check_negation_conflict(case, analyses, idx):
    deltas = {l: 0.0 for l in LETTERS}
    for l, a in analyses.items():
        v = v_polarity(a, case, idx)
        if v:
            deltas[l] -= v[0]["severity"]
    return deltas, "negation/polarity conflict"


def check_distractor_similarity(case, analyses, idx):
    # penalize options whose text is highly token-overlapping with others (ambiguous distractors)
    toks = {l: set((analyses[l]["candidate_text"] or "").lower().split()) for l in analyses}
    deltas = {l: 0.0 for l in LETTERS}
    for l in analyses:
        others = [toks[o] for o in analyses if o != l]
        if toks[l] and others:
            sim = max((len(toks[l] & o) / len(toks[l] | o) if (toks[l] | o) else 0) for o in others)
            deltas[l] -= 0.3 * sim
    return deltas, "distractor similarity penalty"


def check_contradictions(case, analyses, idx):
    deltas = {l: 0.0 for l in LETTERS}
    for l, a in analyses.items():
        v = v_internal_contradiction(a, case, idx)
        if v:
            deltas[l] -= v[0]["severity"]
    return deltas, "internal contradiction"


def estimate_grounding_coverage(case, analyses, idx):
    # global signal (affects controller uncertainty, not candidate ranking)
    return {l: 0.0 for l in LETTERS}, f"grounding coverage={case.get('grounding_coverage', 0):.2f}"


def estimate_evidence_redundancy(case, analyses, idx):
    return {l: 0.0 for l in LETTERS}, "redundancy bookkeeping"


# Registry: name -> (fn, applicable categories)  ('*' = all)
LIBRARY = {
    "demographic_plausibility": (check_demographic_plausibility, "*"),
    "symptom_support": (check_symptom_support, {"Diagnosis", "Clinical Findings"}),
    "lab_support": (check_lab_support, {"Diagnosis", "Next Step/Workup"}),
    "temporal_consistency": (check_temporal_consistency, "*"),
    "pathophysiology_chain": (check_pathophysiology_chain, {"Mechanism/Pathophysiology"}),
    "disease_finding_relation": (check_disease_finding_relation, {"Diagnosis", "Clinical Findings"}),
    "treatment_indication": (check_treatment_indication, {"Treatment/Management"}),
    "treatment_contraindication": (check_treatment_contraindication, {"Treatment/Management"}),
    "next_best_test": (check_next_best_test, {"Next Step/Workup"}),
    "mechanism_consistency": (check_mechanism_consistency, {"Mechanism/Pathophysiology"}),
    "answer_semantic_type": (check_answer_semantic_type, "*"),
    "negation_conflict": (check_negation_conflict, "*"),
    "distractor_similarity": (check_distractor_similarity, "*"),
    "contradictions": (check_contradictions, "*"),
    "grounding_coverage": (estimate_grounding_coverage, "*"),
    "evidence_redundancy": (estimate_evidence_redundancy, "*"),
}


def applicable_functions(category):
    return [name for name, (_, cats) in LIBRARY.items()
            if cats == "*" or category in cats]
