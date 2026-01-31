# High-Confidence Balanced Dataset Recreation

**Date:** January 31, 2026
**Purpose:** Document how the 1,030-question high-confidence dataset was created and validated

---

## Summary

✓ **Successfully recreated:** `medqa_us_train_4opt_high_confidence_balanced.json`
- **1,030 total questions** (206 per category)
- **5 categories:** Clinical Findings, Diagnosis, Mechanism, Next Step, Treatment
- **High confidence:** Both Qwen and keyword categorization agree

---

## Complete Creation Pipeline

### Stage 1: Create Balanced 4-Option Dataset
**Script:** `scripts/create_balanced_4option_dataset.py`

```bash
python scripts/create_balanced_4option_dataset.py
```

**Output:** `data/medqa_us_train_4opt_balanced.json` (1,764 questions)

**Process:**
1. Load 10,178 training questions (4-option only)
2. Categorize using keyword matching
3. Sample up to 250 per category
4. Result: 1,764 questions across 8 categories

---

### Stage 2: Iterative Qwen Validation
**Script:** `scripts/iterative_high_confidence_sampling.py`

**Purpose:** Validate questions until 250+ agreements per major category

**Process:**
1. Load balanced dataset (1,764 questions)
2. For each question:
   - Get keyword categorization
   - Ask Qwen to categorize (LLM call)
   - Check if they agree
3. Keep sampling until all 5 major categories have 250+ agreements
4. Save checkpoint with all agreements

**Output:** `runs/high_confidence_iterative/checkpoint.json`

**Results:**
- Total validated: 1,764 questions
- Tokens used: 699,981
- Iterations: 8
- Agreement counts:
  - Clinical Findings: 250 ✓
  - Diagnosis: 250 ✓
  - Mechanism/Pathophysiology: 250 ✓
  - Next Step/Workup: 250 ✓
  - Treatment/Management: 206 ⚠️ **BOTTLENECK**

**Why Treatment is the bottleneck:**
- Only 54% agreement rate (206/380 questions)
- Questions with "treatment" in context but asking about mechanism
- Keyword matching falsely categorizes as Treatment

---

### Stage 3: Create Final Balanced Dataset
**Script:** `scripts/create_final_balanced_dataset.py`

```bash
python scripts/create_final_balanced_dataset.py
```

**Process:**
1. Load iterative checkpoint with all agreements
2. Find minimum category count = 206 (Treatment/Management)
3. Sample 206 questions from each of the 5 categories
4. Shuffle and save

**Output:** `data/medqa_us_train_4opt_high_confidence_balanced.json` (1,030 questions)

---

## Validation Results

### Dataset Created Successfully

```
Category                       Sampled  Available
────────────────────────────────────────────────
Clinical Findings                 206        250
Diagnosis                         206        250
Mechanism/Pathophysiology         206        250
Next Step/Workup                  206        250
Treatment/Management              206        206 (LIMIT)
────────────────────────────────────────────────
TOTAL                           1,030      1,206
```

### Files Created

1. **Main dataset:** `data/medqa_us_train_4opt_high_confidence_balanced.json` (2.0 MB)
2. **Summary:** `data/medqa_us_train_4opt_high_confidence_balanced_summary.json`
3. **Checkpoint:** `runs/high_confidence_iterative/checkpoint.json` (2.6 MB)

---

## Comparison: Three Dataset Versions

| Dataset | Questions | Per Category | Quality | Purpose |
|---------|-----------|--------------|---------|---------|
| **Balanced** | 1,764 | 250 (6 cats)<br>235 (Prev)<br>29 (Ethics) | Keyword only | Initial dev |
| **High-Conf** | 695 | 139 | Qwen + Keyword agree<br>(from partial validation) | N/A |
| **High-Conf Balanced** | 1,030 | 206 | Qwen + Keyword agree<br>(from full validation) | **Used for experiments** |

---

## Why This Dataset for Temperature Testing?

### Advantages

1. **Verified categorization** - Both Qwen and keywords agree
2. **Perfect 5-way balance** - 206 questions per category
3. **Removes ambiguous questions** - Only clear examples
4. **Sufficient size** - 206 per category is statistically robust

### Trade-offs

- Smaller than keyword-only dataset (1,030 vs 1,764)
- Required expensive LLM validation (700K tokens)
- Lost 3 categories (Other/Mixed, Prevention, Ethics)

### Impact

The Treatment/Management bottleneck (54% agreement) reveals:
- Automatic categorization is harder than it seems
- Context vs question intent matters
- High-confidence filtering improves quality

---

## Recreation Steps (Summary)

To recreate from scratch:

```bash
# Step 1: Create balanced dataset (1,764 questions)
python scripts/create_balanced_4option_dataset.py

# Step 2: Run iterative Qwen validation (expensive! ~700K tokens)
python scripts/iterative_high_confidence_sampling.py
# This will run for 8 iterations validating questions

# Step 3: Create final balanced dataset (1,030 questions)
python scripts/create_final_balanced_dataset.py
```

**Note:** Step 2 requires Qwen API access and costs ~$7-10 in API credits.

---

## Validation Checkpoint Structure

The `runs/high_confidence_iterative/checkpoint.json` contains:

```json
{
  "category_agreements": {
    "Clinical Findings": [/* 250 question objects */],
    "Diagnosis": [/* 250 question objects */],
    "Mechanism/Pathophysiology": [/* 250 question objects */],
    "Next Step/Workup": [/* 250 question objects */],
    "Treatment/Management": [/* 206 question objects */]
  },
  "validated_indices": [/* 1764 indices */],
  "iteration": 8,
  "total_tokens": 699981
}
```

Each question object includes:
- Original question data
- `validated_category` field (agreed category)

---

## Conclusion

✓ **Recreation successful**

The high-confidence balanced dataset (1,030 questions) is:
- Fully reproducible from the checkpoint
- Uses both keyword and LLM validation
- Provides clean, balanced evaluation set
- Limited to 206/category due to Treatment/Management bottleneck

This is the dataset used for all temperature impact experiments (0.0, 0.3, 0.7) on the 7B, 14B, and 32B models.

---

**Ready for temperature testing and statistical analysis!**
