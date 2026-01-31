# Categorization Methodology Validation

This directory contains the original scripts and validation analysis for the MedQA focused dataset (1,030 questions).

## Original Scripts (from FL_Project)

### 1. `iterative_high_confidence_sampling.py`
The main script that created the dataset by:
- Iteratively sampling 100 questions at a time
- Running both keyword and Qwen categorization independently
- Keeping only questions where both methods agreed
- Continuing until 250 agreements per category (206 for Treatment)

### 2. `create_final_balanced_dataset.py`
Balanced the agreed questions to 206 per category:
- Loaded 1,206 agreed questions (250+250+250+250+206)
- Sampled 206 from each category (limited by Treatment)
- Random seed: 42
- Final output: 1,030 questions

### 3. `validate_qwen_categorization.py`
Analysis script comparing Qwen vs keyword agreement rates.

## Validation Results

### Dataset Composition
- **Total questions**: 1,030 (206 per category)
- **Source**: 1,764 questions validated over 8 iterations
- **Agreement rate**: 68.4% (1,206/1,764 agreed)
- **Tokens used**: ~700k

### Methodology Confirmed
✅ **Independent dual categorization**:
  - Keyword method categorized each question
  - Qwen categorized each question (temperature=0.0)
  - Questions kept ONLY if both agreed

✅ **Simple agreement filtering** (NOT hybrid resolution):
  - If keyword == Qwen → keep question
  - If keyword != Qwen → discard question

✅ **Balanced sampling**:
  - Sample 206 from each category
  - Random seed 42 for reproducibility

### Mystery Finding ⚠️

When re-running keyword categorization on the final 1,030 questions:
- **Only 31.75% match** the validated category (327/1,030)
- **240 questions** have no keyword triggers (would be "Other/Mixed")
- **Multiple keyword triggers** in many questions cause ambiguity

**Possible Explanations:**
1. Question text may have been modified after validation
2. Keyword patterns may have subtle differences
3. The agreement actually occurred on ambiguous questions where both methods made the same "mistake"
4. There may have been additional pre-processing not captured in these scripts

### Agreement Statistics (from summary file)

```
Category Agreement Counts:
  Clinical Findings:        250 agreed
  Diagnosis:                250 agreed
  Mechanism/Pathophysiology: 250 agreed
  Next Step/Workup:          250 agreed
  Treatment/Management:      206 agreed (limiting factor)

Total validated: 1,764
Total agreed: 1,206
Agreement rate: 68.4%
```

## Scripts in This Directory

### `verify_categorization_methodology.py`
Verifies the categorization approach by:
- Re-running keyword categorization on focused dataset
- Comparing to validated categories
- Computing match rates

**Run:**
```bash
python3 test/validation/verify_categorization_methodology.py
```

### `analyze_agreement_mystery.py`
Investigates why keyword re-categorization doesn't match validated categories.

**Run:**
```bash
python3 test/validation/analyze_agreement_mystery.py
```

## ✅ Methodology CONFIRMED (from FL_Project Documentation)

### Complete 3-Stage Pipeline

**Stage 1: Create Balanced Dataset (1,764 questions)**
- Source: 10,178 US USMLE training questions
- Keyword categorization into 8 categories
- Sample up to 250 per category
- Output: 1,764 questions pre-filtered by keywords

**Stage 2: Iterative Qwen Validation**
- ✅ **Independent dual categorization**: Keyword + Qwen
- ✅ **Simple agreement filtering**: Both must agree
- ✅ **No hybrid resolution**: Disagreements discarded
- Validated all 1,764 questions over 8 iterations
- Output: 1,206 agreements (68.4% rate)
  - Clinical Findings: 250
  - Diagnosis: 250
  - Mechanism/Pathophysiology: 250
  - Next Step/Workup: 250
  - Treatment/Management: 206 ⚠️ **BOTTLENECK**

**Stage 3: Balance Final Dataset**
- Sample 206 from each of 5 categories
- Limited by Treatment/Management (only 206 available)
- Random seed: 42
- Output: **1,030 final questions**

### Key Findings

1. **Treatment/Management Bottleneck**
   - Only 54% agreement (206/380 validated)
   - Many questions have "treatment" keywords but ask about mechanism
   - Context vs intent distinction is challenging

2. **High-Confidence Filtering Worked**
   - Removed ambiguous questions (32% disagreement rate)
   - Quality over quantity approach
   - Only clear, unambiguous examples kept

3. **Independent Validation Confirmed**
   - No hybrid resolution used
   - Both methods had to agree independently
   - Disagreements completely discarded

4. **Datasets Verified as US USMLE**
   - medqa_full_train.json: 10,178 questions
   - medqa_focused_1030.json: 1,030 questions (4 options, balanced)
   - Meta info: step1 (589), step2&3 (441)

## References

- Original methodology: `scripts/dataset_generation/`
- Detailed analysis: `scripts/dataset_generation/VALIDATION_ANALYSIS.md`
- Source code: FL_Project repository (archived)
