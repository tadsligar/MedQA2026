"""
Shared helpers for running the Paper 1 analyses on the FULL 12,723-question 5-option set
(the *_full result dirs) and for carving out the held-out test split as a clean slice.

--full mode: read from results/<exp>_full/, write CSVs/figures with a _full suffix (focused
outputs are never overwritten), report category-FREE metrics only (per-category labels are
under revision for Paper 4), and additionally emit a *_full_testslice view restricted to the
1,273 held-out test questions.

Test-slice identity: the runners set question_id = the item's index in the dataset they were
given. The full combined file's `id` field equals that index, and each item carries a
`source_split` tag. The held-out test split is exactly the items with source_split == "test"
(cross-checked against data/datasets/medqa_full_test.json by question text). test_qids() returns
those question_ids so any full result file can be filtered with `r["question_id"] in test_qids()`.
"""
import os
import json
import argparse
from functools import lru_cache

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
FULL_DATASET = os.path.join(REPO, "data", "datasets", "medqa_full_combined.json")
TEST_DATASET = os.path.join(REPO, "data", "datasets", "medqa_full_test.json")


def add_full_arg(desc):
    ap = argparse.ArgumentParser(description=desc)
    ap.add_argument("--full", action="store_true",
                    help="Analyze the full 12,723-question 5-option *_full result dirs "
                         "(category-free) and also emit a held-out test-split slice.")
    return ap.parse_args()


@lru_cache(maxsize=1)
def test_qids():
    """Frozenset of question_ids (== full-dataset index) for the held-out test split."""
    full = json.load(open(FULL_DATASET, encoding="utf-8"))
    by_split = {i for i, it in enumerate(full) if it.get("source_split") == "test"}
    # Cross-check against the standalone test file by question text; prefer whichever set has
    # the expected 1,273 and warn if they disagree.
    test = json.load(open(TEST_DATASET, encoding="utf-8"))
    tq = {t["question"] for t in test}
    by_text = {i for i, it in enumerate(full) if it["question"] in tq}
    if by_split and len(by_split) == len(test):
        chosen = by_split
        if by_split != by_text:
            print(f"  [test_qids] note: source_split and text-match sets differ "
                  f"(split={len(by_split)}, text={len(by_text)}); using source_split.")
    else:
        chosen = by_text
        print(f"  [test_qids] using text-match split (source_split test count="
              f"{len(by_split)}, expected {len(test)}).")
    return frozenset(chosen)


def slice_to_test(recs):
    """Filter a results list to the held-out test split."""
    tq = test_qids()
    return [r for r in recs if r["question_id"] in tq]


def suffix(full, testslice=False):
    """CSV/figure filename suffix for the current mode."""
    if not full:
        return ""
    return "_full_testslice" if testslice else "_full"
