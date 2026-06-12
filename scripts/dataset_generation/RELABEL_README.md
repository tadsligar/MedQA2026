# Full-set USMLE-competency relabeling — run guide

Replaces the unreliable focused-1030 `validated_category` (confirmed ~26% agreement with content;
near-random) with **official USMLE Physician Competencies** labels on the **full 12,723-question**
MedQA set, which is already benchmarked in `results/base_runs_full/` (5 models × 3 temps × 3 runs).
No GPU and no model re-runs — only classification (API) + CPU analysis.

Rubric (authoritative): `docs/medical_review/USMLE_COMPETENCY_RUBRIC.md`

## Step 1 — classify all 12,723 (you run; strong API model)
```bash
export OPENAI_API_KEY=...                 # do NOT hardcode / commit
export OPENAI_BASE_URL=https://api.openai.com/v1   # or any OpenAI-compatible endpoint
export CLASSIFIER_MODEL=gpt-4o            # use the strongest model you have
python scripts/dataset_generation/classify_competencies.py \
    --dataset data/datasets/medqa_full_combined.json \
    --output results/category_relabel/competency_labels.jsonl
# resumable: safe to interrupt/re-run; skips already-labeled qids.
# tip: test first with --limit 50
```
Output: `results/category_relabel/competency_labels.jsonl`
(`qid, competency∈{MK,PC_DX,PC_MGMT,COMM,PROF,SBP,PBL}, subtask, confidence, reason, model`).

## Step 2 — per-competency analysis (GPU-free)
```bash
python papers/paper1/analysis/compute_competency_full.py
```
Writes `papers/paper1/tables/full_competency_accuracy.csv` (7-way, Wilson CIs, by model) and
`full_reasoning_subcat_accuracy.csv` (the 5 reasoning sub-categories). Reports natural
distribution — not forced balance.

## Step 3 — validation (gold sample)
`results/category_relabel/gold_sample_views.jsonl` is a 120-question stratified sample
(oversamples rare COMM/PROF/PBL items). It is being hand-labeled independently as a gold
standard; agreement/κ between the API labels and the gold set will quantify label quality
(dual-annotator story). qids align to `medqa_full_combined.json` and `base_runs_full/*`.

## Notes
- The 7 competencies map to the 5 reasoning sub-categories per the rubric; the analysis reports
  both. Communication/Professionalism/Systems/Practice-based are reported separately (small but
  real cells — only feasible because the full 12,723 set is large).
- Headline is the full 12,723 (all splits, inference benchmark); the official MedQA test split
  (1,273) can be reported as a held-out robustness check by filtering on the split.
- The focused-1030 (balanced subset for Papers 2/3) should be relabeled with the SAME script
  (`--dataset data/datasets/medqa_focused_1030.json`) for consistency.

## Validation result (rule classifier vs Claude gold, 2026-06)
`gold_labels_opus.jsonl` = 120-item stratified gold set hand-labeled by Claude (oversamples rare
COMM/PROF/PBL — deliberately HARD, so these numbers understate natural-distribution accuracy).
`rule_competency_classifier.py` (rule_v2, mechanism-option + ethics-before-COMM fixes) scores:
- Overall agreement: **66.7%** (80/120); high-confidence subset: **70.1%** (61/87)
- Cohen's kappa: **0.585** (moderate)
- By class recall: PC_DX 85%, COMM 100%, PBL 67%, PC_MGMT 68%, **MK 40%, PROF 40%**
Conclusion: far better than the broken legacy labels (~26–40%) and strong on common categories,
but the small non-clinical cells (MK, PROF) that Paper 1 wants to break out are still weak.
Recommended for the authoritative headline: run `classify_competencies.py` (strong LLM API pass).
Reproduce: `python3 scripts/dataset_generation/rule_competency_classifier.py && python3 /tmp/score_rule.py`
