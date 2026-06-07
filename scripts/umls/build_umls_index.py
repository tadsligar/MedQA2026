#!/usr/bin/env python3
"""
Paper 2 EXP1 — build a queryable UMLS index (SQLite) from the .RRF files.

Parses MRCONSO (concepts/terms), MRSTY (semantic types), MRDEF (definitions), and MRREL
(relations) into an indexed SQLite DB used by grounding (EXP2) and the symbolic scorer (EXP3).

CPU-only, no GPU. Memory-light (streamed, batched inserts in one transaction per file).
Takes ~15-40 min depending on disk. Output DB is gitignored.

Usage:
    python scripts/umls/build_umls_index.py \
        --meta-dir data/umls/2025AB/META \
        --output data/umls/umls_2025AB_index.db \
        --rela may_treat,may_prevent,contraindicated_with,manifestation_of,has_finding,\
causes,associated_with,isa,has_mechanism_of_action

RRF column layouts (0-indexed, pipe-delimited):
  MRCONSO: CUI0 LAT1 TS2 LUI3 STT4 SUI5 ISPREF6 AUI7 ... SAB11 TTY12 CODE13 STR14 ... SUPPRESS16
  MRSTY:   CUI0 TUI1 STN2 STY3 ATUI4 CVF5
  MRDEF:   CUI0 AUI1 ATUI2 SATUI3 SAB4 DEF5 SUPPRESS6 CVF7
  MRREL:   CUI1_0 AUI1_1 STYPE1_2 REL3 CUI2_4 AUI2_5 STYPE2_6 RELA7 RUI8 ... SAB10 ... SUPPRESS13
"""
import os
import sys
import argparse
import sqlite3
from pathlib import Path

# Clinical semantic-type groups worth keeping (TUI families); used as a "is clinical" hint.
CLINICAL_STY_KEYWORDS = {
    "Disease or Syndrome", "Sign or Symptom", "Finding", "Pathologic Function",
    "Neoplastic Process", "Pharmacologic Substance", "Clinical Drug",
    "Therapeutic or Preventive Procedure", "Diagnostic Procedure", "Laboratory Procedure",
    "Body Part, Organ, or Organ Component", "Anatomical Abnormality",
    "Mental or Behavioral Dysfunction", "Injury or Poisoning", "Antibiotic",
    "Organic Chemical", "Body Substance", "Cell or Molecular Dysfunction",
}


def fields(line):
    # RRF lines end with a trailing '|'
    return line.rstrip("\n").split("|")


def build(meta_dir, output, rela_keep, langs):
    meta = Path(meta_dir)
    paths = {f: meta / f for f in ["MRCONSO.RRF", "MRSTY.RRF", "MRDEF.RRF", "MRREL.RRF"]}
    for f, p in paths.items():
        if not p.exists():
            sys.exit(f"ERROR: {p} not found. Point --meta-dir at the extracted META/ dir.")

    if os.path.exists(output):
        os.remove(output)
    con = sqlite3.connect(output)
    con.execute("PRAGMA journal_mode=OFF")
    con.execute("PRAGMA synchronous=OFF")
    cur = con.cursor()
    cur.executescript("""
        CREATE TABLE concept   (cui TEXT PRIMARY KEY, pref_name TEXT);
        CREATE TABLE term      (cui TEXT, term_lc TEXT, sab TEXT, tty TEXT);
        CREATE TABLE semtype   (cui TEXT, tui TEXT, sty TEXT, is_clinical INTEGER);
        CREATE TABLE definition(cui TEXT, sab TEXT, def TEXT);
        CREATE TABLE relation  (cui1 TEXT, rela TEXT, rel TEXT, cui2 TEXT, sab TEXT);
        CREATE TABLE meta_info (k TEXT, v TEXT);
    """)

    # ---- MRCONSO: terms + preferred names (English, non-suppressed) ----
    n_terms = 0
    pref = {}
    cur.execute("BEGIN")
    with open(paths["MRCONSO.RRF"], encoding="utf-8") as fh:
        batch = []
        for line in fh:
            f = fields(line)
            if len(f) < 17:
                continue
            cui, lat, ts, stt, ispref, sab, tty, string, suppress = (
                f[0], f[1], f[2], f[4], f[6], f[11], f[12], f[14], f[16])
            if langs and lat not in langs:
                continue
            if suppress in ("O", "E", "Y"):  # obsolete/suppressible
                continue
            term_lc = string.strip().lower()
            if not term_lc:
                continue
            batch.append((cui, term_lc, sab, tty))
            n_terms += 1
            # preferred name: TS=P (preferred LUI) and STT=PF and ISPREF=Y
            if cui not in pref and ts == "P" and stt == "PF" and ispref == "Y":
                pref[cui] = string.strip()
            if len(batch) >= 50000:
                cur.executemany("INSERT INTO term VALUES (?,?,?,?)", batch); batch = []
        if batch:
            cur.executemany("INSERT INTO term VALUES (?,?,?,?)", batch)
    cur.executemany("INSERT INTO concept VALUES (?,?)", list(pref.items()))
    con.commit()
    print(f"MRCONSO: {n_terms:,} terms, {len(pref):,} preferred concept names")

    # ---- MRSTY: semantic types ----
    n_sty = 0
    cur.execute("BEGIN")
    with open(paths["MRSTY.RRF"], encoding="utf-8") as fh:
        batch = []
        for line in fh:
            f = fields(line)
            if len(f) < 4:
                continue
            cui, tui, sty = f[0], f[1], f[3]
            is_clin = 1 if sty in CLINICAL_STY_KEYWORDS else 0
            batch.append((cui, tui, sty, is_clin)); n_sty += 1
            if len(batch) >= 50000:
                cur.executemany("INSERT INTO semtype VALUES (?,?,?,?)", batch); batch = []
        if batch:
            cur.executemany("INSERT INTO semtype VALUES (?,?,?,?)", batch)
    con.commit()
    print(f"MRSTY: {n_sty:,} semantic-type rows")

    # ---- MRDEF: definitions (one per cui kept, first non-suppressed) ----
    n_def = 0
    seen_def = set()
    cur.execute("BEGIN")
    with open(paths["MRDEF.RRF"], encoding="utf-8") as fh:
        batch = []
        for line in fh:
            f = fields(line)
            if len(f) < 7:
                continue
            cui, sab, definition, suppress = f[0], f[4], f[5], f[6]
            if suppress in ("O", "E", "Y") or cui in seen_def:
                continue
            seen_def.add(cui)
            batch.append((cui, sab, definition)); n_def += 1
            if len(batch) >= 20000:
                cur.executemany("INSERT INTO definition VALUES (?,?,?)", batch); batch = []
        if batch:
            cur.executemany("INSERT INTO definition VALUES (?,?,?)", batch)
    con.commit()
    print(f"MRDEF: {n_def:,} definitions")

    # ---- MRREL: relations (keep selected RELA; skip suppressed & self-loops) ----
    keep = set(r.strip() for r in rela_keep if r.strip()) if rela_keep else None
    n_rel = 0
    cur.execute("BEGIN")
    with open(paths["MRREL.RRF"], encoding="utf-8") as fh:
        batch = []
        for line in fh:
            f = fields(line)
            if len(f) < 14:
                continue
            cui1, rel, cui2, rela, sab, suppress = f[0], f[3], f[4], f[7], f[10], f[13]
            if suppress in ("O", "E", "Y"):
                continue
            if cui1 == cui2:
                continue
            if keep is not None and rela not in keep:
                continue
            batch.append((cui1, rela, rel, cui2, sab)); n_rel += 1
            if len(batch) >= 50000:
                cur.executemany("INSERT INTO relation VALUES (?,?,?,?,?)", batch); batch = []
        if batch:
            cur.executemany("INSERT INTO relation VALUES (?,?,?,?,?)", batch)
    con.commit()
    print(f"MRREL: {n_rel:,} relations kept" + (f" (RELA in {sorted(keep)})" if keep else ""))

    # ---- indices ----
    print("Building indices...")
    cur.executescript("""
        CREATE INDEX idx_term_lc   ON term(term_lc);
        CREATE INDEX idx_term_cui  ON term(cui);
        CREATE INDEX idx_sty_cui   ON semtype(cui);
        CREATE INDEX idx_rel_c1    ON relation(cui1, rela);
        CREATE INDEX idx_rel_c2    ON relation(cui2, rela);
    """)
    cur.execute("INSERT INTO meta_info VALUES ('n_terms', ?)", (str(n_terms),))
    cur.execute("INSERT INTO meta_info VALUES ('n_concepts', ?)", (str(len(pref)),))
    cur.execute("INSERT INTO meta_info VALUES ('n_relations', ?)", (str(n_rel),))
    cur.execute("INSERT INTO meta_info VALUES ('n_definitions', ?)", (str(n_def),))
    con.commit(); con.close()
    print(f"\nDONE -> {output}")
    print(f"  concepts={len(pref):,} terms={n_terms:,} relations={n_rel:,} definitions={n_def:,}")


def main():
    ap = argparse.ArgumentParser(description="Build UMLS SQLite index (Paper 2 EXP1)")
    ap.add_argument("--meta-dir", required=True, help="extracted UMLS META/ dir with *.RRF")
    ap.add_argument("--output", default="data/umls/umls_2025AB_index.db")
    ap.add_argument("--rela", default=("may_treat,may_prevent,contraindicated_with,"
                                       "manifestation_of,has_finding,causes,associated_with,"
                                       "isa,has_mechanism_of_action,disease_has_finding,"
                                       "has_causative_agent,occurs_in"),
                    help="comma-separated RELA values to keep (empty = keep all)")
    ap.add_argument("--langs", default="ENG", help="comma-separated LAT codes to keep")
    args = ap.parse_args()
    rela = args.rela.split(",") if args.rela else None
    langs = set(args.langs.split(",")) if args.langs else None
    build(args.meta_dir, args.output, rela, langs)


if __name__ == "__main__":
    main()
