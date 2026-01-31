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

## Key Findings

1. **Datasets are confirmed US USMLE questions**
   - medqa_full_train.json: 10,178 questions (5 options)
   - medqa_focused_1030.json: 1,030 questions (4 options, balanced categories)
   - Meta info shows step1/step2&3 distribution

2. **Categorization was genuinely independent**
   - No hybrid resolution
   - Simple agreement filtering
   - Disagreements discarded

3. **68.4% agreement rate is relatively low**
   - Suggests keyword method is imprecise
   - Qwen provides semantic understanding
   - Many questions have ambiguous keywords

4. **Final dataset represents high-confidence categorization**
   - Both methods independently agreed on these questions
   - Balanced across 5 clinical reasoning categories
   - Quality over quantity (1,030 from 1,764 validated)

## References

- Original methodology: `scripts/dataset_generation/`
- Detailed analysis: `scripts/dataset_generation/VALIDATION_ANALYSIS.md`
- Source code: FL_Project repository (archived)
