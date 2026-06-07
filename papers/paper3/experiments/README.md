# Paper 3 — Experiment Prompts (Agentic Neuro-Symbolic Differential Diagnosis)

Self-contained prompts to build and evaluate the adaptive agent. The agent is **not
implemented** in this snapshot, and it **depends on Paper 2's components** (UMLS index,
grounding, verifiers — see `../../paper2/experiments/`). Build Paper 2's EXP1–EXP3 + EXP6
first. UMLS data (~6GB, licensed) and HPC are required.

Shared context:
- Dataset: `data/datasets/medqa_focused_1030.json` (1,030 Q, 206/category, 4-option A–D).
- **Static baselines are verified** (Paper 1): greedy accuracies, best single = Qwen2.5 32B
  73.4%. **Targets/sanity checks (verified seeds):** oracle any-of-5 = 86.0% (the headroom
  ceiling); inter-model agreement predicts correctness (5-agree 83.5% → 2-agree 23.9%).
- **Reuse, do not rebuild:** Paper 1 baselines; Paper 2 grounding/verifiers; the Paper 1/2
  statistics harness (`papers/paper1/analysis/compute_stats.py`).
- Result schema convention: keep `question_id, category, correct, predicted, is_correct`;
  add `evidence_trace`, `belief_history`, `functions_called`, `n_steps`, `flags`, `confidence`.

| # | Experiment | Builds / measures | Fills |
|---|---|---|---|
| 1 | Case parser + category classifier | structured case; predicted category vs gold | EXP1, Tbl agent |
| 2 | Candidate hypothesis generator | options → typed candidates | EXP2 |
| 3 | Evidence-function library | the 16 callable checks (UMLS/LLM/both) | EXP3, Tbl 2 |
| 4 | Agent controller + policies | A–G selection policies; control loop | EXP4, Fig 3/7 |
| 5 | Belief-update variants | additive / weighted / Bayesian / L2R | EXP5, Fig 4 |
| 6 | Redundancy-aware selection (mRMR-style) | evidence efficiency | EXP6, Tbl 6 |
| 7 | Verification & contradiction auditor | flags; error prediction | EXP7, Fig 8 |
| 8 | Full-agent evaluation | accuracy vs all baselines | EXP8, Tbl 4/5 |
| 9 | Ablations + evidence-budget sweep | component contributions; acc vs budget | EXP9, Tbl 7, Fig 5/10 |
| 10 | Case studies + failure-mode annotation | qualitative traces; taxonomy | EXP10, Tbl 9, Fig 9 |

Minimum workshop package: EXP1–EXP4 + EXP8 (a working agent beating static prompting on some
categories). Full conference: add EXP5–EXP7, EXP9. Journal: add EXP10 + clinician trace review.
