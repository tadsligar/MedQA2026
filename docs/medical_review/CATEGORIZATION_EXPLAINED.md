# Question Categorization Explained (For Non-Technical Readers)

**Date:** January 31, 2026
**Purpose:** Explain how we organized 1,030 medical questions into 5 categories

---

## The Goal

We're testing how well AI models answer medical questions. To do this scientifically, we need to organize questions by **what type of thinking they require**. Just like medical students learn different skills (diagnosing vs. choosing treatments), AI models might be better or worse at different types of questions.

---

## The 5 Categories We Chose

We grouped questions based on **what the question is asking you to figure out**:

### 1. **Clinical Findings** - "What would you see?"
Questions asking what you would expect to find on physical exam, lab tests, or imaging.

**Example type:** "A patient with condition X would most likely show which finding?"

**Why this matters:** Tests if the AI understands typical presentations and expected results.

---

### 2. **Diagnosis** - "What's wrong?"
Questions asking you to identify the disease, condition, or underlying cause.

**Example type:** "What is the most likely diagnosis?" or "What caused this problem?"

**Why this matters:** Tests if the AI can recognize disease patterns and make accurate diagnoses.

---

### 3. **Mechanism/Pathophysiology** - "How does it work?"
Questions asking about drug mechanisms, disease processes, or biological pathways.

**Example type:** "What is the mechanism by which this drug works?" or "Why does this happen?"

**Why this matters:** Tests if the AI understands the science behind medicine, not just memorized facts.

---

### 4. **Next Step/Workup** - "What should you do next?"
Questions asking what test to order, what action to take, or how to proceed with evaluation.

**Example type:** "What is the most appropriate next step in management?"

**Why this matters:** Tests if the AI can make good clinical decisions about patient care.

---

### 5. **Treatment/Management** - "How do you fix it?"
Questions asking which drug to give, which therapy to choose, or how to manage a condition.

**Example type:** "What is the best treatment?" or "Which medication should be prescribed?"

**Why this matters:** Tests if the AI can choose appropriate treatments safely and effectively.

---

## Why These 5 Categories?

These categories map to the **fundamental cognitive skills** doctors use:

1. **Pattern recognition** (Clinical Findings, Diagnosis)
2. **Scientific understanding** (Mechanism/Pathophysiology)
3. **Clinical decision-making** (Next Step, Treatment)

Medical licensing exams (USMLE) test all these skills. By categorizing questions this way, we can see if AI models are well-rounded or have specific weaknesses.

---

## How We Categorized the Questions

We used a **two-step validation process** to make sure questions were categorized correctly:

### Step 1: Computer Keyword Matching
A computer program looked for specific phrases in each question:
- "most likely diagnosis" → Diagnosis
- "next step" → Next Step/Workup
- "treatment" → Treatment/Management
- "mechanism" → Mechanism/Pathophysiology
- "expected finding" → Clinical Findings

### Step 2: AI Validation
We asked an AI (Qwen 2.5) to independently categorize each question by reading it and understanding what it was really asking.

### Step 3: Agreement Filter
**We only kept questions where both methods agreed.**

**Why this matters:** If keywords and AI agree, we're confident the category is correct. If they disagree (example: question has word "treatment" but is really asking about mechanism), we threw it out as ambiguous.

---

## The Numbers

Starting point:
- **10,178 total questions** from USMLE-style medical exams

After filtering:
- **1,764 questions** pre-filtered by keywords
- **Validated all 1,764** using both methods

Results:
- **1,206 questions** where both methods agreed (68.4%)
- **558 questions** discarded as ambiguous (31.6%)

Final dataset:
- **1,030 questions** (206 per category)
- Perfectly balanced across all 5 categories
- High confidence in categorization

---

## The Challenge: Treatment Questions

**Treatment/Management was the hardest category:**
- Only 54% agreement rate (206 out of 380 validated)
- Many questions had the word "treatment" but were really asking about something else

**Example of a tricky question:**
> "Which treatment is effective in slowing the progression of diabetic nephropathy?"

- **Keywords thought:** Treatment (saw word "treatment")
- **AI thought:** Mechanism (understood it's asking HOW treatments slow progression)
- **Result:** Disagreement → Question discarded as ambiguous

This shows why we needed two independent methods. Simple keyword matching isn't enough for complex medical questions.

---

## What We Need from Medical Professionals

We need your expertise to verify:

1. **Are these 5 categories the right way to organize medical questions?**
   - Do they capture the important types of clinical reasoning?
   - Are we missing any major category?
   - Should any categories be combined or split?

2. **Are the questions categorized correctly?**
   - We've printed 206 questions for each category
   - Please review samples and flag any that seem miscategorized
   - Look especially for edge cases or ambiguous questions

3. **Do the categories align with how you think about medical education?**
   - Do these map to skills you teach medical students?
   - Would these be useful for evaluating clinical competence?

---

## Why This Matters

We're testing whether AI models can safely and effectively answer medical questions. By organizing questions into categories, we can:

- **Identify specific weaknesses** (e.g., "This AI is great at diagnosis but terrible at choosing treatments")
- **Compare models fairly** (balanced categories prevent bias)
- **Understand AI limitations** (know when to trust vs. verify AI answers)

Your medical expertise is critical because:
- We're computer scientists, not doctors
- You understand what these questions are really testing
- You can spot errors we might miss

---

## How to Review

We've created 5 separate documents with all questions for each category:

1. `Clinical_Findings_Questions.md` (206 questions)
2. `Diagnosis_Questions.md` (206 questions)
3. `Mechanism_Questions.md` (206 questions)
4. `Next_Step_Questions.md` (206 questions)
5. `Treatment_Questions.md` (206 questions)

**For each question, please note:**
- ✓ Correctly categorized
- ✗ Miscategorized (suggest correct category)
- ? Ambiguous (could fit multiple categories)

**You don't need to review all 1,030 questions!** Even reviewing 20-30 per category would be incredibly helpful.

---

## Questions for Discussion

1. Do these 5 categories make sense from a medical education perspective?
2. Are there important clinical reasoning skills we're missing?
3. Do you see patterns in miscategorization that suggest our methods need adjustment?
4. Would you organize USMLE questions differently? How?
5. Are there specific question types that don't fit well into any category?

---

## Thank You!

Your medical expertise will help us:
- Improve AI evaluation methods
- Understand AI limitations in medical reasoning
- Build better, safer medical AI tools

We're grateful for your time and insights.

---

**Contact for questions:** [Your contact information here]

**Dataset info:** 1,030 questions from MedQA-USMLE dataset (Jin et al., 2021)
