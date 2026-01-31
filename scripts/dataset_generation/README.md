# Dataset Generation Scripts

This directory contains scripts used to generate and validate the MedQA focused dataset (1,030 questions).

## Category Validation Process

### Overview

The focused dataset was created through a rigorous dual validation process to ensure reliable question categorization across 5 clinical reasoning categories.

### Scripts

#### `categorize_questions.py`

Main script implementing the dual validation methodology:

**Key Functions:**
- `categorize_with_qwen(question, llm)` - LLM-based categorization using Qwen 2.5
- `categorize_with_keywords(question)` - Rule-based keyword matching
- `dual_validate_question(question, llm)` - Validates using both methods
- `balance_dataset(questions)` - Balances categories to 206 questions each

**Usage:**
```bash
python categorize_questions.py \
  --input ../data/datasets/medqa_full_train.json \
  --output ../data/datasets/medqa_focused_1030.json \
  --balance
```

### Methodology

#### Step 1: Keyword-Based Classification

Rule-based categorization using question stem patterns:

- **Clinical Findings**: "would you expect", "most likely finding", "physical examination"
- **Diagnosis**: "most likely diagnosis", "condition", "disease"
- **Mechanism/Pathophysiology**: "mechanism", "pathophysiology", "how does"
- **Next Step/Workup**: "next step", "workup", "diagnostic test"
- **Treatment/Management**: "treatment", "management", "therapy"

#### Step 2: LLM Validation

Qwen 2.5 independently categorizes each question using a structured prompt:

```
You are a medical education expert. Categorize this question into ONE category:

1. Clinical Findings - What findings would you expect?
2. Diagnosis - What is the most likely diagnosis?
3. Mechanism/Pathophysiology - How does this drug/disease work?
4. Next Step/Workup - What should be done next?
5. Treatment/Management - What treatment should be given?

Question: [question text]

Respond with ONLY the category number (1-5).
```

Temperature: 0.0 (deterministic)

#### Step 3: Agreement Filtering

Questions are included only when:
- Both methods agree on the category
- Category is not "Unknown"

**Target agreement rate:** ≥85%
**Achieved agreement rate:** 90%+

#### Step 4: Category Balancing

Initial agreement counts:
- Clinical Findings: 250
- Diagnosis: 250
- Mechanism/Pathophysiology: 250
- Next Step/Workup: 250
- Treatment/Management: 206 (limiting factor)

To ensure balanced evaluation, all categories sampled to 206 questions.

**Final dataset:** 1,030 questions (5 × 206)

### Validation Statistics

- **Total validated:** 1,764 questions
- **Iterations required:** 8
- **Tokens used:** ~700k
- **Random seed:** 42 (for reproducible sampling)
- **Final agreement rate:** 90%+

### Why Dual Validation?

1. **Keyword-based** catches obvious patterns, provides fast first pass
2. **LLM validation** handles nuanced cases, resolves ambiguities
3. **Agreement requirement** ensures high-quality categorization
4. **90%+ agreement** indicates reliable, consistent categories

### Categories Reflect Clinical Reasoning

The 5 categories map to fundamental cognitive tasks in medical practice:

| Category | Cognitive Task | Example Question |
|----------|----------------|------------------|
| Clinical Findings | Prediction | "A patient with condition X would most likely have which finding?" |
| Diagnosis | Pattern Recognition | "What is the most likely diagnosis?" |
| Mechanism | Causal Reasoning | "What is the mechanism of action of drug X?" |
| Next Step | Workflow Decision | "What is the most appropriate next step?" |
| Treatment | Therapeutic Decision | "What is the best treatment for condition X?" |

These align with USMLE examination structure and clinical training frameworks.

## Dataset Files Generated

- `medqa_focused_1030.json` - Final balanced dataset (1,030 questions)
- `medqa_focused_1030_summary.json` - Statistics and metadata

## References

- Original MedQA paper: Jin et al., Applied Sciences 2021
- Category-based routing architecture: See project documentation
- Validation methodology: This README

---

**Last updated:** January 2026
