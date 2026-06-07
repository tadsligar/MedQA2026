# MedQA2026 — Papers

Three-paper research program evaluating and extending medical reasoning on a category-balanced
MedQA subset (1,030 questions; 206 each across Clinical Findings, Diagnosis,
Mechanism/Pathophysiology, Next Step/Workup, Treatment/Management; 4-option A–D; random
baseline 25%). Each paper folder is self-contained: a `BRIEF.md` (the original prompt), a
results layer, experiment prompts, analysis scripts, figures, a prose `DRAFT.md`, and a
rendered PDF.

## The three papers

| | Paper 1 | Paper 2 | Paper 3 |
|---|---|---|---|
| **Theme** | Base-LLM benchmark | Neuro-symbolic grounding & verification | Agentic differential-diagnosis |
| **Core question** | How do base LLMs reason across categories, scale, temperature, runs? | Where does UMLS grounding/verification help vs fail (concept mismatch)? | Does adaptive evidence acquisition beat static prompting? |
| **Data status** | **Real results** (45 base-run files) | System not in repo; base-data seeds + unverified README numbers | Agent not built; base-data seeds; depends on Paper 2 |
| **Draft** | `paper1/DRAFT.md` → `Paper1_Draft.pdf` (12 pp) | `paper2/DRAFT.md` → `Paper2_Draft.pdf` (10 pp) | `paper3/DRAFT.md` → `Paper3_Draft.pdf` (11 pp) |
| **Results doc** | `paper1/RESULTS.md` (verified) | `paper2/RESULTS_SEED.md` | `paper3/RESULTS_SEED.md` |
| **Experiments** | 7 prompts (`paper1/experiments/`) | 10 prompts (`paper2/experiments/`) | 10 prompts (`paper3/experiments/`) |

## Dependency order (build this way)

```
Paper 1  (DONE: verified empirical results)
   │  provides the LLM-only baselines (greedy accuracies, category structure)
   ▼
Paper 2  (UMLS index → grounding → symbolic/CoVe/hybrid)
   │  EXP1 UMLS index ─► EXP2 grounding ─► EXP3 symbolic, EXP6 CoVe …
   │  provides grounding + verifier components
   ▼
Paper 3  (agent reuses Paper 2's grounding/verifiers)
      EXP1 parser+category ─► EXP3 evidence functions ─► EXP4 controller ─► EXP8 full eval
```

- **Paper 1 is the foundation and is empirically complete.** Its verified t=0.0 accuracies
  (OLMo-3 7B 46.18 / OLMo-3 32B 58.64 / Qwen2.5 7B 67.96 / 14B 68.48 / 32B 73.40) are the
  **static LLM-only baseline** reused by Papers 2 and 3 — do not recompute them.
- **Paper 2 must run before Paper 3.** Paper 3's evidence-function library and contradiction
  auditor reuse Paper 2's UMLS index, grounding, and verifiers. Build Paper 2's
  EXP1–EXP3 + EXP6 first.
- **Shared infrastructure note:** the neuro-symbolic work (Papers 2 & 3) needs the UMLS
  Metathesaurus (~6 GB, licensed) and is intended to run on HPC; it is not present in this
  repo snapshot. The experiment prompts are written to run there.

## What is verified vs pending

- **Verified (reproducible from this repo):** all Paper 1 tables/figures; Paper 2 & 3 base-data
  seeds (hard-core set, concept-variant prevalence, phrase-density, oracle headroom, agreement
  curve). Seeds are computed by each paper's `analysis/seed_analysis.py` (or `compute_*.py`).
- **Pending new experiments (placeholders `[TBD-EXP#]` in the drafts):** all neuro-symbolic and
  agentic results. Each placeholder maps to a numbered prompt in that paper's `experiments/`.
- **Unverified, quoted for context only:** the preliminary numbers in `neurosymbolic/README.md`
  (e.g., pure-UMLS ~30%, CoVe 21%→29%→28%) — flagged in `paper2/RESULTS_SEED.md`; reproduce
  before citing.

## Cross-paper through-lines (the research arc)

1. **Aggregate accuracy hides structure** (Paper 1: Clinical Findings hardest for every model;
   category × difficulty unrelated to groundable surface area — Paper 2 seed).
2. **Confidence without logits** — cross-run stability predicts correctness (Paper 1) →
   grounding/violation scores predict errors (Paper 2 EXP9) → belief margin predicts
   correctness (Paper 3 EXP5/EXP7). The agreement curve (5-agree 83.5% → 2-agree 23.9%) ties
   these together.
3. **Symbolic knowledge as auditor, not solver** (Paper 2 thesis) → used inside the agent's
   verification loop (Paper 3).
4. **Headroom exists but needs reasoning, not routing** — oracle 86.0% vs best single 73.4%,
   uncapturable by model routing or voting (Paper 3 seed), motivating adaptive evidence
   acquisition.

## Reproducing the verified layer

```bash
# Paper 1 (real results)
python papers/paper1/analysis/compute_tables.py
python papers/paper1/analysis/compute_stats.py
python papers/paper1/analysis/compute_sectionB.py
python papers/paper1/analysis/make_figures.py
python papers/paper1/analysis/make_figures_ci.py
# Paper 2 / 3 base-data seeds
python papers/paper2/analysis/seed_analysis.py
python papers/paper3/analysis/seed_analysis.py
# Rebuild any PDF after editing its DRAFT.md
python papers/paperN/analysis/build_pdf.py     # N = 1,2,3
```

Rendering requires `pandoc` + `xelatex`; analysis requires `pandas, numpy, scipy, matplotlib,
statsmodels`.
