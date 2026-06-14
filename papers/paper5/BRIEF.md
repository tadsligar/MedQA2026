You are my senior PhD research advisor, AI/ML research collaborator, and scientific writing partner. I am developing a publication from my GitHub repository MedQA2026, which evaluates and extends base-LLM medical reasoning on MedQA.

The goal is Paper 5: a **systems / method** paper that turns Paper 4's reliable competency labeling into an *intervention* — a **competency-routed reasoning orchestration**. Where Paper 4 measured and prescribed, Paper 5 builds and tests.

Context (what's already established in the repo):
- Repository: https://github.com/tadsligar/MedQA2026
- Paper 1: category-balanced base-LLM benchmark (decoding temperature, run-to-run stability, scaling) — empirically complete.
- Paper 2: UMLS neuro-symbolic grounding & verification (design + seeds).
- Paper 3: agentic differential-diagnosis (design + seeds).
- Paper 4: a **reliable, NBME-grounded competency labeling** of all 12,723 MedQA questions (official USMLE Physician Tasks/Competencies: MK / DX / MGMT / COMM / PROF / SBP / PBL), validated dual-condition (κ=0.83; MK-vs-DX κ=0.88). Key empirical finding: competency explains *little* base-LLM accuracy variance — a small, pooled-significant **Medical-Knowledge deficit relative to Diagnosis** (OR 0.93, p=3e-4) that is temperature-robust but does **not** robustly replicate on the held-out test split. The categorization is read off the **lead-in** (final question sentence), per the NBME closed-lead-in item-writing principle.
- Models: Qwen2.5 7B/14B/32B, OLMo-3 7B/32B. Infrastructure: AIAU HPC (vLLM), local 4090, OpenAI Batch API for labeling.

The core idea to test:
- A **router** reads the lead-in, assigns the question to a competency (MK/DX/MGMT/…), then **dispatches** to a competency-matched reasoning strategy/scaffold, given the full stem + lead-in:
  - DX (diagnosis) → generate-and-rank differential / base-rate-weighted hypothesis selection.
  - MK (apply foundational science) → ontology / knowledge-graph path lookup & mechanism verification (reuse Paper 2 UMLS grounding/verifier).
  - MGMT (management) → guideline / contraindication checking (reuse Paper 2 verifier).
  - (small cells COMM/PROF/SBP/PBL → direct or a light default.)
- Evaluate **orchestration × competency**: does competency-matched routing beat (a) a single uniform prompt and (b) a single best-overall strategy applied to everything? Is any gain *concentrated* on the competency the base model was weakest at (MK)?

Honest framing (must be stated):
- Paper 4 showed competency moves accuracy only ~2–3 pp and the MK deficit is fragile on held-out data, so **routing-by-competency has limited headroom on the accuracy axis**. Paper 5 must therefore (i) be powered/honest about small effects, (ii) treat a null or modest result as a legitimate finding, and (iii) also report non-accuracy benefits if present (calibration, stability, interpretability of the per-competency trace, compute cost of routing).
- The router itself should be cheap and its accuracy reported (it's the Paper 4 labeler applied live).

Your task:
Produce a complete plan for Paper 5: positioning statement; title options; draft abstract; research questions/hypotheses; the orchestration architecture (router → competency-matched solvers, reusing Paper 2/3 modules); experimental conditions and baselines (uniform prompt, best-single-strategy, oracle-routing upper bound, learned/lead-in routing); datasets (focused + full + held-out test split); metrics (accuracy by competency, routing accuracy, calibration/stability, compute overhead); ablations; what runs on AIAU (GPU) vs CPU; expected contributions; limitations; and publication strategy. Emphasize rigor, honest treatment of small/null effects, and reuse of existing repo infrastructure. No claims of clinical utility.
