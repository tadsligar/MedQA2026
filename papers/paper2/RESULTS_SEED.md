# Paper 2 — Results Seed & Status

Paper 2 is the **neuro-symbolic grounding & verification** paper. Unlike Paper 1, the
neuro-symbolic system has **not been run in this repo snapshot**: `neurosymbolic/umls_verifier/`
and `neurosymbolic/chain_of_verification/` are empty, and there are **no result files** to
verify. This document separates (A) what is **verified from existing repo data** from
(B) **preliminary numbers quoted in the neurosymbolic README** (unverified, must be
reproduced) and (C) what the experiments must still produce.

---

## A. Verified seeds from existing base-run data (`analysis/seed_analysis.py`)

These are computed directly from `results/base_runs/` (t=0.0, run 1) and the dataset's
pre-extracted `metamap_phrases`, and are reproducible.

### A1. Hard-core target set — where a verifier/hybrid most needs to help
Of 1,030 questions, **144 (14.0%)** are answered incorrectly by **all five** base models at
greedy decoding, and **328 (31.8%)** correctly by all five. The hard core skews toward
Clinical Findings:

| Category | Hard-core (all 5 wrong) | All 5 correct | Hard-core rate |
|---|---|---|---|
| Clinical Findings | 41 | 52 | 19.9% |
| Diagnosis | 30 | 58 | 14.6% |
| Next Step/Workup | 30 | 62 | 14.6% |
| Mechanism/Pathophysiology | 22 | 78 | 10.7% |
| Treatment/Management | 21 | 78 | 10.2% |
| **Total** | **144** | **328** | **14.0%** |

The hard-core IDs are saved (`tables/seed_hardcore_ids.json`) as the evaluation focus for
verifier/hybrid gains and concept-mismatch annotation (EXP8).

### A2. Groundable surface area does NOT predict difficulty
Using `metamap_phrases` as a proxy for "how much groundable clinical surface" a question
has (mean 34.9 phrases/question):

| Category | Mean phrases | Mean base acc (5 models, t=0.0) |
|---|---|---|
| Clinical Findings | 34.2 | 55.0% |
| Diagnosis | 35.6 | 59.9% |
| Mechanism/Pathophysiology | 31.6 | 67.6% |
| Next Step/Workup | 37.0 | 64.3% |
| Treatment/Management | 36.0 | 67.9% |

Per-question correlation between phrase count and number-of-models-correct is **−0.02**
(no relationship). The hardest category (Clinical Findings) does not have fewer extractable
phrases — so **naive concept-overlap grounding cannot explain or fix difficulty**. This is a
direct empirical motivation for why *pure symbolic* grounding is insufficient and why
relation-aware + LLM-bridged grounding is needed (Paper 2 thesis).

### A3. Concept-mismatch is empirically prevalent
Canonical clinical ideas appear under **many surface forms** in the benchmark, which breaks
exact-match grounding to a single canonical UMLS surface:

| Concept | Questions w/ any variant | Distinct surface forms | Examples (count) |
|---|---|---|---|
| Dyspnea / SOB | 113 | 6 | shortness of breath (57), dyspnea (28), difficulty breathing (21), breathless (8), short of breath (7), respiratory distress (7) |
| Chest pain / discomfort | 55 | 6 | chest pain (48), substernal (4), retrosternal (3), chest discomfort (2), chest pressure (2), chest tightness (1) |
| Myocardial infarction | 27 | 5 | myocardial infarction (14), STEMI (10), MI (3), heart attack (1), acute coronary (1) |
| Hypertension | 125 | 3 | hypertension (121), high blood pressure (3), elevated BP (3) |
| Fever | 148 | 2 | fever (136), febrile (16) |

For dyspnea, the canonical term "dyspnea" covers only **28 of 113** mentions; an exact match
to one surface form would miss ~75% of clinically equivalent mentions. This reproduces the
README's "chest discomfort vs chest pain" anecdote **quantitatively** and seeds the Concept
Mismatch Analysis (Paper 2 §8). *Figure:* `figures/fig_seed_phrase_vs_acc.png`.

---

## B. Preliminary numbers from the neurosymbolic README — UNVERIFIED
Quoted for context only; **must be reproduced** before any appear in the paper. No backing
result files exist in this snapshot.

| System | README-quoted accuracy | Note |
|---|---|---|
| Random baseline | 25% | 4-option reference |
| TF-IDF only | 0% | "vocabulary overlap insufficient" |
| Pure UMLS symbolic | 30% | "concept mismatch problem" |
| Hybrid (UMLS + LLM) | 60–70% (expected) | not yet run |
| CoVe heuristic baseline | 21.0% | |
| CoVe verify-only | 29.0% (+38% rel.) | |
| CoVe full (with revision) | 28.0% (−3% vs verify-only) | revision did not help |

README claims to reproduce: pure symbolic is insufficient; verification helps a weak
proposer; revision can harm; LLM proposers are overconfident. These are exactly the claims
Paper 2 should establish on the **full balanced 1,030-set** with proper statistics — they are
currently anecdotal.

Infrastructure the README describes (to be located/rebuilt): UMLS index with 695,642
relationships, semantic-type filtering, category-specific scorers (Diagnosis/Treatment),
5 CoVe verifiers (type incompatibility, demographic implausibility, low grounding coverage,
polarity conflict, internal contradiction). Requires UMLS Metathesaurus (MRCONSO/MRSTY/
MRDEF/MRREL, ~6GB) and a license — **not present here**.

---

## C. What experiments must produce (see `experiments/`)
The verified Paper 1 base-run accuracies (OLMo-3 7B 46.18 … Qwen2.5 32B 73.40, t=0.0) are the
**LLM-only baseline** for Paper 2's comparison table. Everything else — symbolic-only,
UMLS-in-prompt, verifier-rerank, CoVe, hybrid, and all grounding/verification metrics — must
be generated by EXP1–EXP10. The draft (`DRAFT.md`) marks every such number `[TBD-EXP#]`.
