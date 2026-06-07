# Paper 2 — Experiment Prompts (Neuro-Symbolic Grounding & Verification)

Each file is a **self-contained prompt** to produce one piece of Paper 2. They are ordered
as a build-then-evaluate pipeline. The neuro-symbolic code is **not present** in this repo
snapshot and the README's numbers are unverified, so EXP1–EXP2 rebuild infrastructure before
any evaluation. **UMLS Metathesaurus (MRCONSO/MRSTY/MRDEF/MRREL, ~6GB) and a UMLS license are
required and are not in this environment — run these on your HPC.**

Shared context:
- Dataset: `data/datasets/medqa_focused_1030.json` (1,030 Q, 206/category, 4-option A–D,
  random baseline 25%). Category in `validated_category`; pre-extracted clinical phrases in
  `metamap_phrases`.
- **LLM-only baseline is already verified** (Paper 1): t=0.0 greedy accuracies OLMo-3 7B
  46.18 / OLMo-3 32B 58.64 / Qwen2.5 7B 67.96 / 14B 68.48 / 32B 73.40. Reuse these; do not
  recompute.
- Evaluation focus set: the 144 all-models-wrong hard-core IDs in
  `../tables/seed_hardcore_ids.json` (where symbolic help matters most).
- Serving for LLM components: vLLM completions endpoint, configs in `configs/`.
- Result schema convention (extend Paper 1's): keep `question_id, category, correct,
  predicted, is_correct` and add system-specific fields (grounding, violations, confidence).

| # | Experiment | Builds / measures | Fills |
|---|---|---|---|
| 1 | Build UMLS index | concepts, semantic types, relations DB | infra |
| 2 | Concept grounding | ground stem+options to CUIs; coverage logs | EXP2, Fig 2 |
| 3 | Pure symbolic scorer | UMLS-only accuracy (overlap + relation-aware) | EXP3, Tbl 3/4 |
| 4 | UMLS-in-prompt | LLM + appended UMLS concepts | EXP4, Tbl 3 |
| 5 | UMLS verifier rerank | verifier reranks LLM options | EXP5, Tbl 3 |
| 6 | Chain-of-Verification | verify-only & with-revision; 5 verifiers | EXP6, Tbl 3/5 |
| 7 | Hybrid decision | combine LLM likelihood + symbolic support | EXP7, Tbl 3 |
| 8 | Concept-mismatch annotation | taxonomy labels on failures | EXP8, Tbl 6 |
| 9 | Verifier-as-error-predictor | grounding/violation → correctness AUROC | EXP9, Fig 5/6 |
| 10 | Ablations | drop each symbolic component | EXP10, Tbl 7 |

Recommended minimum to make Paper 2 submittable: EXP1–EXP3, EXP6, EXP9 (establishes
symbolic-insufficient, verification-helps, scores-predict-error). EXP4/5/7 complete the
hybrid story; EXP8/10 add depth.
