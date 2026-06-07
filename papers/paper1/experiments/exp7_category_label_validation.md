# EXP7 — Category-Label Validation / Inter-Annotator Agreement

**Priority: MEDIUM-LOW** (see `../ANALYSIS_GAPS.md` C-7).

## Why this matters
The paper's central thesis is that **category-balanced** evaluation reveals weaknesses
hidden by aggregate accuracy. That argument depends on the category labels being valid. The
dataset summary already notes an LLM-validated assignment constrained by Treatment/Management
(54% agreement, 206-item cap). Reporting agreement statistics or a human audit pre-empts the
"your categories are arbitrary" critique head-on.

## Prompt to run it
> You are my dataset-validation engineer. Quantify and document the reliability of the five
> reasoning-category labels in the focused MedQA set, including human spot-check agreement.

## Inputs
- `data/datasets/medqa_focused_1030.json` (`validated_category` per item) and
  `medqa_focused_1030_summary.json` (existing agreement counts, iterations, seed=42).
- The category-generation scripts in `scripts/dataset_generation/`.

## Procedure
1. Recover and document the **original labeling protocol** (how many LLM judges, agreement
   rule, why Treatment/Management was the binding constraint at 206).
2. **Human audit**: sample ~50 items/category (250 total), have a clinically-literate
   annotator assign categories blind; compute agreement with the stored labels and a
   confusion matrix (which categories get conflated).
3. Report Cohen's/Fleiss' κ for the original multi-judge process if recoverable.

## Expected outputs
`results/category_validation/audit.csv` (`question_id, stored_category, human_category,
agree`) and a confusion matrix.

## Analysis plan
1. Human–stored agreement overall and per category; confusion matrix.
2. Identify systematic confusions (e.g., Next Step/Workup vs Treatment/Management) and
   discuss impact on the category-accuracy claims.
3. Sensitivity check: do the headline category findings (Clinical Findings hardest) survive
   if borderline items are dropped?

## Fills in DRAFT.md
`[TBD-EXP7: label agreement κ + confusion matrix]`, the §3 Dataset quality-control
paragraph, and a §8 Limitations sentence.

## Acceptance check
Per-category human agreement and confusion matrix reported; statement on whether category
findings are robust to label noise.
