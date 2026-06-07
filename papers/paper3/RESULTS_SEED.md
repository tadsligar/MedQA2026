# Paper 3 — Results Seed & Status

Paper 3 proposes an **agentic neuro-symbolic differential-diagnosis** framework. The agent is
**not implemented** in this repo snapshot, so its results are placeholders. This document
separates (A) **verified seeds from existing base-run data** that motivate and bound the
approach, (B) **inputs inherited from Papers 1–2** (Paper 1 verified; Paper 2 pending), and
(C) what the agent experiments must produce.

---

## A. Verified seeds from base-run data (`analysis/seed_analysis.py`)
All from `results/base_runs/` (t=0.0, run 1, deterministic). Reproducible.

### A1. Headroom for agentic selection (oracle bound)
"Oracle any-of-5-correct" = a question is solvable if **any** of the five base models gets it.
This upper-bounds what a perfect selector/agent over this model pool could reach.

| Scope | Best single model | Best single | Majority of 5 | Oracle (any of 5) | Headroom |
|---|---|---|---|---|---|
| Overall | Qwen2.5 32B | 73.4 | 69.3 | **86.0** | **+12.6** |
| Clinical Findings | Qwen2.5 32B | 67.0 | 59.7 | 80.1 | +13.1 |
| Diagnosis | Qwen2.5 32B | 70.9 | 67.0 | 85.4 | +14.6 |
| Mechanism/Pathophysiology | Qwen2.5 32B | 76.2 | 75.2 | 89.3 | +13.1 |
| Next Step/Workup | Qwen2.5 32B | 75.7 | 73.3 | 85.4 | +9.7 |
| Treatment/Management | Qwen2.5 32B | 77.2 | 71.4 | 89.8 | +12.6 |

Two findings: (i) there is **~10–15 pp of headroom** above the best single model that a better
reasoning/selection process could in principle capture; (ii) **naive majority voting is below
the best single model** (69.3 < 73.4) — so the headroom is *not* reachable by simple ensembling.
This motivates **adaptive, evidence-guided belief updating** rather than voting.

### A2. Model-level routing is a dead end — reframe toward adaptive evidence
Qwen2.5 32B is the best model in **every** category, so a perfect per-category *model* router
reaches only **73.4%** — identical to using Qwen2.5 32B everywhere.

| Category | OLMo-3 7B | OLMo-3 32B | Qwen2.5 7B | Qwen2.5 14B | Qwen2.5 32B | Best |
|---|---|---|---|---|---|---|
| Clinical Findings | 41.7 | 51.0 | 57.3 | 57.8 | 67.0 | Qwen2.5 32B |
| Diagnosis | 41.3 | 56.8 | 65.0 | 65.5 | 70.9 | Qwen2.5 32B |
| Mechanism/Pathophys. | 54.4 | 62.1 | 72.3 | 72.8 | 76.2 | Qwen2.5 32B |
| Next Step/Workup | 43.2 | 60.2 | 70.9 | 71.4 | 75.7 | Qwen2.5 32B |
| Treatment/Management | 50.0 | 63.1 | 74.3 | 74.8 | 77.2 | Qwen2.5 32B |

**Honest implication for the paper:** the agent's value cannot come from *choosing which model
to ask* (no model-routing gain exists). Category-specific value, if any, must come from
**category-specific reasoning policies and evidence functions applied within a single strong
model** — exactly the agentic mechanism Paper 3 proposes. This negative result sharpens the
thesis and should be stated explicitly.

### A3. Inter-model agreement predicts correctness (belief-state motivation)
Treating the number of base models agreeing on the modal answer as a crude "belief" signal:

| Models agreeing on modal answer | # questions | Modal-answer accuracy |
|---|---|---|
| 5 | 393 | 83.5% |
| 4 | 314 | 72.9% |
| 3 | 252 | 55.6% |
| 2 | 71 | 23.9% |

Strongly monotonic: agreement (a cheap uncertainty proxy) tracks correctness from 83.5% down
to 23.9%. This directly motivates **maintaining a belief state over candidates**, using its
**margin/entropy as the uncertainty signal** that drives adaptive evidence selection and
**stopping** (BRIEF RQ4, the agent controller in §9-F/G).

*Figure:* `figures/fig_seed_oracle_headroom.png`.

---

## B. Inherited inputs
- **Paper 1 (verified):** LLM-only baselines (greedy accuracies, category structure,
  temperature/stability behavior). The static-prompting baselines for Paper 3 are these.
- **Paper 2 (pending):** UMLS grounding, symbolic scorers, CoVe verifiers, concept-mismatch
  taxonomy. Paper 3's evidence-function library and contradiction auditor reuse Paper 2's
  components, so Paper 3 depends on Paper 2's experiments (`../paper2/experiments/`).

---

## C. What the agent experiments must produce (see `experiments/`)
Everything agentic — case parser, category classifier, candidate generation, evidence-function
library, the controller/policies, belief-update variants, redundancy-aware selection, the
verifier pass, full-agent accuracy, efficiency metrics, ablations, evidence-budget sweeps,
case studies, and failure-mode annotations. The draft (`DRAFT.md`) marks every such number
`[TBD-EXP#]`. The oracle bound (86.0%) and the agreement curve above are the **targets and
sanity checks** the agent is measured against.
