# Medical Professional Review Documentation

This folder contains materials for medical professionals to review our question categorization methodology and accuracy.

## Purpose

We're evaluating AI models on medical questions and need expert validation that:
1. Our 5 categories make sense clinically
2. Questions are correctly categorized
3. The categories align with medical education and clinical reasoning

## Files in This Directory

### Overview Document
- **`CATEGORIZATION_EXPLAINED.md`** - Lay person explanation of categorization methodology
  - Why we chose these 5 categories
  - How the two-step validation process works
  - What we need medical professionals to verify

### Question Review Documents (One per Category)

Each document contains all 206 questions for that category in a printable, reviewable format:

1. **`Clinical_Findings_Questions.md`** (206 questions)
   - Questions asking "What findings would you expect?"

2. **`Diagnosis_Questions.md`** (206 questions)
   - Questions asking "What is the diagnosis/cause?"

3. **`Mechanism_Pathophysiology_Questions.md`** (206 questions)
   - Questions asking "How does this work/why does this happen?"

4. **`Next_Step_Workup_Questions.md`** (206 questions)
   - Questions asking "What should you do next?"

5. **`Treatment_Management_Questions.md`** (206 questions)
   - Questions asking "How do you treat this?"

## How to Use These Documents

### For Quick Review (Recommended)
1. Read `CATEGORIZATION_EXPLAINED.md` first
2. Pick 1-2 categories to review in depth
3. Review 20-30 questions from each category
4. Note any miscategorizations or ambiguous cases
5. Provide feedback on overall category definitions

### For Comprehensive Review
1. Review all 206 questions in each category
2. Mark each question as:
   - ✓ Correctly categorized
   - ✗ Miscategorized (suggest correct category)
   - ? Ambiguous (could fit multiple categories)
3. Complete the summary section at the end of each document

## What We're Looking For

### Category Validation
- Do these 5 categories capture the main types of clinical reasoning?
- Are there important reasoning skills we're missing?
- Should any categories be combined or split?

### Question Accuracy
- Are questions correctly categorized?
- Are there systematic patterns in miscategorization?
- Which categories have the most ambiguous questions?

### Clinical Relevance
- Do these categories align with medical education frameworks?
- Would this categorization be useful for evaluating clinical competence?
- How would you improve the categorization scheme?

## Key Statistics

- **Total questions:** 1,030 (perfectly balanced)
- **Per category:** 206 questions each
- **Source:** USMLE-style medical exam questions
- **Validation method:** Dual independent categorization (keywords + AI)
- **Agreement rate:** 68.4% (only kept questions where both methods agreed)

## Categorization Challenge: Treatment Questions

Treatment/Management had the lowest agreement rate (54%) because many questions contained the word "treatment" but were actually asking about mechanisms or other concepts.

**Example:**
> "Which treatment is effective in slowing progression of diabetic nephropathy?"

- Keyword method: Treatment (saw word "treatment")
- AI method: Mechanism (understood it's asking HOW treatments work)
- Result: Disagreement → Question discarded

This shows why we needed two independent validation methods.

## How to Provide Feedback

You can provide feedback by:

1. **Annotating the printed documents**
   - Print the category documents you want to review
   - Mark questions directly on the printouts
   - Fill out the summary section at the end

2. **Creating a summary document**
   - Note overall impressions of each category
   - List specific question numbers that are miscategorized
   - Suggest improvements to category definitions

3. **Discussion meeting**
   - Schedule a meeting to discuss findings
   - Review examples together
   - Brainstorm alternative categorization schemes

## Converting to PDF (Optional)

To convert these markdown files to PDF for easier printing:

```bash
# Using pandoc (if installed)
pandoc Diagnosis_Questions.md -o Diagnosis_Questions.pdf

# Or use any markdown to PDF converter
```

Or simply print directly from your markdown viewer.

## Questions?

If anything is unclear or you need more context:
- Review the `CATEGORIZATION_EXPLAINED.md` document
- Check the main project README at `../../README.md`
- Contact: [Your contact information]

## Thank You!

Your medical expertise is invaluable for validating our AI evaluation methodology. Even reviewing a small subset of questions will significantly improve the quality of our research.

---

**Generated:** January 31, 2026
**Dataset:** MedQA-USMLE (Jin et al., 2021)
**Total Questions:** 1,030 (206 per category)
