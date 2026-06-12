#!/usr/bin/env python3
"""
Build a UMLS-derived organ-system gazetteer (symbolic, reproducible).

For every UMLS concept that carries a MeSH DISEASE (C), ORGANISM (B), or MENTAL-DISORDER (F)
tree number, roll the tree number up to one of our organ systems, then expand the concept to
all of its English synonym strings (from the local UMLS index `term` table). The result is a
term_lc -> system map used to label MedQA questions by scanning the vignette + answer.

Input : data/umls/derived/cui_mesh_tree.tsv  (CUI|MeSH-tree-number ; extracted from MRSAT)
        data/umls/umls_2025AB_index.db        (term table)
Output: data/umls/derived/organ_system_gazetteer.tsv  (term_lc \t system \t cui \t tree)

NOTE: organ-system label set + tree rollup are intentionally in ONE place (SYS_BY_TREE) so the
primary/secondary convention can be revised later (see TODO in organ_system_labeler.py).
"""
import os, sqlite3, re
from collections import defaultdict

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TREE = os.path.join(REPO, "data/umls/derived/cui_mesh_tree.tsv")
DB   = os.path.join(REPO, "data/umls/umls_2025AB_index.db")
OUT  = os.path.join(REPO, "data/umls/derived/organ_system_gazetteer.tsv")

# tree-prefix -> (system, priority)  high priority beats cross-cutting buckets
HI, LO = 2, 1
SYS_BY_TREE = {
    # C = diseases
    "C01": ("Infectious", HI), "C05": ("Musculoskeletal", HI), "C06": ("Gastrointestinal", HI),
    "C07": ("Gastrointestinal", HI), "C08": ("Respiratory", HI), "C09": ("SpecialSenses", HI),
    "C10": ("Nervous", HI), "C11": ("SpecialSenses", HI), "C12": ("RenalUrinary", HI),
    "C13": ("Reproductive", HI), "C14": ("Cardiovascular", HI), "C15": ("Hematologic", HI),
    "C17": ("Skin", HI), "C18": ("EndocrineMetabolic", HI), "C19": ("Endocrine", HI),
    "C20": ("Immune", HI),
    "C04": ("Neoplasm", LO), "C16": ("CongenitalNeonatal", LO), "C21": ("Multisystem", LO),
    "C23": ("Multisystem", LO), "C24": ("Multisystem", LO), "C25": ("Multisystem", LO),
    "C26": ("Trauma", LO),
    # B = organisms -> infectious
    "B01": ("Infectious", HI), "B02": ("Infectious", HI), "B03": ("Infectious", HI),
    "B04": ("Infectious", HI), "B05": ("Infectious", HI),
    # F03 = mental DISORDERS only (F01 Behavior / F02 Psychological Phenomena are too generic:
    # memory, mood, sleep, pain, stress... flood the vignette with noise)
    "F03": ("Behavioral", HI),
}

def rollup(trees):
    """trees: set of MeSH tree numbers -> dict(system->best priority)."""
    out = {}
    for tn in trees:
        p3 = tn[:3]
        if p3 in SYS_BY_TREE:
            sysname, pr = SYS_BY_TREE[p3]
            out[sysname] = max(out.get(sysname, 0), pr)
    return out

def main():
    cui_trees = defaultdict(set)
    for line in open(TREE):
        cui, tn = line.rstrip("\n").split("|", 1)
        cui_trees[cui].add(tn)
    # CUI -> best system (prefer HI-priority; if a concept has both organ & neoplasm, organ wins)
    cui_sys = {}
    for cui, trees in cui_trees.items():
        ru = rollup(trees)
        if not ru: continue
        # choose highest-priority system; tie -> deterministic by name
        best = sorted(ru.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        cui_sys[cui] = (best, sorted(trees)[0])
    print(f"concepts with a system: {len(cui_sys)}")

    con = sqlite3.connect(DB)
    GOOD_SAB = ("MSH", "SNOMEDCT_US", "NCI", "MEDLINEPLUS", "ICD10CM")
    GENERIC = {"disease","disorder","syndrome","infection","fever","pain","masses","lesion",
               "edema","shock","death","injury","wound","tumor","cancer","carcinoma","neoplasm",
               "inflammation","necrosis","abnormal","acute","chronic","disorders","diseases",
               "deficiency","failure","insufficiency","swelling","bleeding","hemorrhage"}
    seen = set()
    n = 0
    with open(OUT, "w") as f:
        # pull english terms for our CUIs
        q = "SELECT term_lc, sab FROM term WHERE cui=?"
        for cui, (sysname, tree) in cui_sys.items():
            for term_lc, sab in con.execute(q, (cui,)):
                t = (term_lc or "").strip()
                if len(t) < 6: continue
                if t in GENERIC: continue
                if sab not in GOOD_SAB: continue
                if not re.search(r"[a-z]", t): continue
                key = (t, sysname)
                if key in seen: continue
                seen.add(key)
                f.write(f"{t}\t{sysname}\t{cui}\t{tree}\n"); n += 1
    print(f"gazetteer terms: {n} -> {OUT}")

if __name__ == "__main__":
    main()
