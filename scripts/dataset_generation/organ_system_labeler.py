#!/usr/bin/env python3
"""
Organ-system (Review-of-Systems axis) labeler for MedQA — symbolic, no API, no GPU.

Dual symbolic signal, both auditable and reproducible:
  (1) UMLS gazetteer  : data/umls/derived/organ_system_gazetteer.tsv  (disease/organism/mental
      concepts carrying a MeSH C/B/F tree number, expanded to all synonyms -> organ system).
  (2) Curated lexicon : LEXICON below — anatomy / physiology / modality anchors that UMLS
      exact-match misses (e.g. "ECG", "renal", "seizure"). High precision, hand-authored.

Each question's full vignette + answer options are scanned; system votes are tallied (gazetteer
hits weighted by term specificity, lexicon hits weighted). Output per question:
  {qid, primary, secondary[], confidence, votes{}, n_hits, method}

CONVENTION (TODO: revisit — user undecided, 2026-06): we emit a PRIMARY system + a SECONDARY
cross-system tag list. The label SET and tree rollup live in build_organ_system_gazetteer.py
(SYS_BY_TREE) so the convention can be changed in one place. C18(metabolic)+C19(endocrine) are
merged for reporting via DISPLAY_MERGE; Neoplasm/Trauma/Congenital are low-priority fallbacks.

Output: results/category_relabel/organ_system_labels.jsonl
"""
import os, json, re, argparse
from collections import defaultdict

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GAZ = os.path.join(REPO, "data/umls/derived/organ_system_gazetteer.tsv")

# merge near-duplicate internal codes for reporting; keep cross-system buckets explicit
DISPLAY_MERGE = {"EndocrineMetabolic": "Endocrine/Metabolic", "Endocrine": "Endocrine/Metabolic",
                 "RenalUrinary": "Renal/Urinary", "SpecialSenses": "Nervous/Special-senses",
                 "Nervous": "Nervous/Special-senses", "Neoplasm": "Multisystem",
                 "CongenitalNeonatal": "Multisystem", "Trauma": "Musculoskeletal"}
def disp(s): return DISPLAY_MERGE.get(s, s)

# low-priority systems only win if nothing else fires
LOWPRI = {"Multisystem"}

# ---- curated lexicon: regex -> internal system (high-precision anatomy/physiology/modality) ----
LEXICON = [
    (r"\b(ecg|ekg|electrocardiogram|echocardiogra|murmur|myocard|angina|coronary|atrial|ventric|"
     r"aortic|mitral|tachycard|bradycard|arrhythmia|heart failure|ejection fraction|hypertensi|"
     r"\bvalve|pericard|cardiac output|stroke volume|blood pressure|claudication|\bdvt\b|"
     r"deep ven(ous|e) thromb|pulmonary embol|varicos|atheroscler)\b", "Cardiovascular"),
    (r"\b(dyspnea|wheez|asthma|copd|pneumon|bronch|pleural|pulmonary (function|infiltrat|edema)|"
     r"spirometry|fev1|hemoptys|pneumothorax|respiratory rate|crackles|sputum|tuberculosis|"
     r"interstitial lung|pulmonary fibrosis)\b", "Respiratory"),
    (r"\b(abdomin|diarrh|constipat|nausea|vomit|hematemesis|melena|hepat|liver|cirrhos|pancreat|"
     r"gastr|esophag|colon|colorect|duoden|jejun|ileum|biliary|cholecyst|cholangi|gallbladder|"
     r"ascites|dysphagia|peptic ulcer|bowel|stool|jaundice|splenomeg)\b", "Gastrointestinal"),
    (r"\b(renal|kidney|nephr|glomerul|creatinine|hematuria|proteinuria|dysuria|urin|bladder|"
     r"ureter|urethr|dialysis|gfr|cystitis|pyelonephr)\b", "RenalUrinary"),
    (r"\b(seizure|epilep|stroke|hemiplegi|aphasia|paresthes|neuropath|meningi|encephal|cerebr|"
     r"cranial nerve|spinal cord|radiculopath|parkinson|alzheimer|dementia|migraine|headache|"
     r"ataxia|tremor|myelopath|sciatic|reflex|cerebell|hydrocephal|multiple sclerosis|"
     r"neurolog|gait)\b", "Nervous"),
    (r"\b(retina|cornea|glaucoma|cataract|visual|ophthalm|conjunctiv|otitis|tinnitus|hearing|"
     r"vertigo|nystagmus|uveitis|macular)\b", "SpecialSenses"),
    (r"\b(thyroid|diabet|insulin|glucose|adrenal|cortisol|pituitar|hormone|endocrin|goiter|"
     r"hyperthyroid|hypothyroid|cushing|acromegal|prolactin|parathyroid|calcium homeostas|"
     r"metaboli|electrolyte|acid-?base|acidosis|alkalosis|hyponatrem|hyperkalem)\b",
     "EndocrineMetabolic"),
    (r"\b(anemia|hemoglobin|hematocrit|leukem|lymphoma|thrombocyt|platelet|coagulat|clotting|"
     r"neutropen|pancytopen|hemolyt|sickle cell|thalassem|ferritin|reticulocyt|blood smear|"
     r"bone marrow|hemophilia|von willebrand|splenectomy)\b", "Hematologic"),
    (r"\b(arthrit|joint|bone|fracture|osteo|muscle weakness|myopath|tendon|ligament|cartilage|"
     r"rheumatoid|gout\b|sprain|dislocat|spine|vertebr|scoliosis|myalgia)\b", "Musculoskeletal"),
    (r"\b(rash|skin|derm|eczema|psoriasis|melanoma|pruritus|urticaria|cellulitis|lesion|"
     r"pigmentation|alopecia|nail|epidermis|blister|bullae|macule|papule)\b", "Skin"),
    (r"\b(pregnan|gestation|menstr|menopaus|ovar|uter|cervix|cervical|vagin|endometri|"
     r"prostate|testic|scrotal|penile|breast|mammogr|obstetr|gynecolog|fetal|placenta|"
     r"contracept|amenorrh|preeclampsia|eclampsia|labor|delivery)\b", "Reproductive"),
    (r"\b(immun|autoimmun|hypersensitiv|allerg|lupus|sle\b|vasculit|anaphyl|complement|"
     r"antibod|antinuclear|sarcoid|immunodefic|transplant reject|graft)\b", "Immune"),
    (r"\b(infection|sepsis|bacterem|viremia|fungal infect|parasit|abscess|\bhiv\b|meningitis|"
     r"gram-(positive|negative)|\borganism\b|pathogen|endocarditis|osteomyelitis|"
     r"pneumonia|cellulitis|tuberculosis)\b", "Infectious"),
    (r"\b(major depress|depressive (disorder|episode)|psychos|schizophren|bipolar|\bmania\b|"
     r"suicidal|panic (attack|disorder)|ptsd|\bocd\b|hallucinat|delusion|psychiatr|"
     r"manic|eating disorder|anorexia nervosa|bulimia|generalized anxiety)\b", "Behavioral"),
    (r"\b(relative risk|odds ratio|sensitivity|specificity|predictive value|confidence interval|"
     r"\bp-?value|study design|bias\b|confound|incidence|prevalence|hazard ratio|cohort|"
     r"case-control|randomized|number needed)\b", "Multisystem"),  # biostat -> Multisystem/General
]
LEXICON = [(re.compile(p, re.I), s) for p, s in LEXICON]


def load_gaz():
    by_first = defaultdict(list)
    for line in open(GAZ):
        term, sysname = line.rstrip("\n").split("\t")[:2]
        toks = term.split()
        by_first[toks[0]].append((toks, sysname))
    return by_first


def norm(t):
    t = t.lower()
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _scan_one(text, gaz, weight, votes):
    hits = 0
    toks = norm(text).split()
    for i, w in enumerate(toks):
        for full, sysname in gaz.get(w, ()):
            L = len(full)
            if toks[i:i+L] == full:
                votes[sysname] += weight * (1.0 + 0.6*(L-1)); hits += 1
    for rx, sysname in LEXICON:
        m = rx.findall(text.lower())
        if m:
            votes[sysname] += weight * 1.5 * min(len(m), 3); hits += 1
    return hits


def split_sents(q):
    parts = re.split(r'(?<=[.?!])\s+', q.strip())
    return [p for p in parts if p.strip()]


def scan(question, answer, options, gaz):
    """Section-aware: chief complaint (lead sentences) and the CORRECT answer drive the system;
    the rest of the vignette is supporting; distractor OPTIONS are weak. This counters USMLE
    vignettes that pile on incidental comorbidities/social history from other systems."""
    votes = defaultdict(float); hits = 0
    sents = split_sents(question)
    lead = " ".join(sents[:2])          # chief complaint / presenting illness
    body = " ".join(sents[2:-1]) if len(sents) > 3 else ""
    ask = sents[-1] if sents else ""
    hits += _scan_one(lead, gaz, 3.0, votes)     # presenting illness dominates
    hits += _scan_one(str(answer), gaz, 3.0, votes)  # the crux concept
    hits += _scan_one(ask, gaz, 1.5, votes)
    hits += _scan_one(body, gaz, 1.0, votes)
    # non-answer options are frequently other-system distractors -> weak secondary signal only
    ovals = list(options.values()) if isinstance(options, dict) else list(options)
    hits += _scan_one(" ".join(str(o) for o in ovals), gaz, 0.3, votes)
    return votes, hits


def decide(votes):
    if not votes:
        return ("Multisystem", [], "low")
    merged = defaultdict(float)
    for s, w in votes.items():
        merged[disp(s)] += w
    # suppress low-priority unless it's all we have
    nonlow = {s: w for s, w in merged.items() if s not in {disp(x) for x in LOWPRI}}
    pool = nonlow if nonlow else merged
    ranked = sorted(pool.items(), key=lambda kv: -kv[1])
    primary, pv = ranked[0]
    secondary = [s for s, w in ranked[1:] if w >= 0.5*pv][:2]
    top2 = pv - (ranked[1][1] if len(ranked) > 1 else 0)
    conf = "high" if pv >= 4 and (top2 >= 1.5 or len(ranked) == 1) else ("med" if pv >= 2 else "low")
    return (primary, secondary, conf)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="data/datasets/medqa_full_combined.json")
    ap.add_argument("--output", default="results/category_relabel/organ_system_labels.jsonl")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    gaz = load_gaz()
    data = json.load(open(os.path.join(REPO, args.dataset), encoding="utf-8"))
    out = os.path.join(REPO, args.output); os.makedirs(os.path.dirname(out), exist_ok=True)
    from collections import Counter
    dist = Counter(); conf_d = Counter()
    with open(out, "w", encoding="utf-8") as f:
        for i, q in enumerate(data):
            if args.limit and i >= args.limit: break
            qid = int(q.get("question_id", i))
            opts = q["options"]
            ans = q.get("answer", "")
            votes, hits = scan(q["question"], ans, opts, gaz)
            primary, secondary, conf = decide(votes)
            dist[primary] += 1; conf_d[conf] += 1
            f.write(json.dumps({"qid": qid, "primary": primary, "secondary": secondary,
                                "confidence": conf, "n_hits": hits,
                                "votes": {k: round(v, 1) for k, v in sorted(votes.items(),
                                          key=lambda kv: -kv[1])[:5]}}, ensure_ascii=False) + "\n")
    print("distribution:", dict(dist.most_common()))
    print("confidence:", dict(conf_d))


if __name__ == "__main__":
    main()
