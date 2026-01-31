#!/usr/bin/env python3
"""
Generate medical review documents for each category.
Creates printable PDFs with questions and answers formatted for expert review.
"""

import json
from pathlib import Path

project_root = Path(__file__).parent.parent
output_dir = project_root / "docs" / "medical_review"
output_dir.mkdir(parents=True, exist_ok=True)

# Load dataset
dataset_path = project_root / "data" / "datasets" / "medqa_focused_1030.json"

with open(dataset_path, 'r', encoding='utf-8') as f:
    questions = json.load(f)

# Group by category
categories = {
    'Clinical Findings': [],
    'Diagnosis': [],
    'Mechanism/Pathophysiology': [],
    'Next Step/Workup': [],
    'Treatment/Management': []
}

for q in questions:
    cat = q.get('validated_category')
    if cat in categories:
        categories[cat].append(q)

# Create document for each category
for category, questions_list in sorted(categories.items()):
    # Create filename
    filename = category.replace('/', '_').replace(' ', '_') + '_Questions.md'
    filepath = output_dir / filename

    # Write document
    with open(filepath, 'w', encoding='utf-8') as f:
        # Header
        f.write(f"# {category} Questions\n\n")
        f.write(f"**Category:** {category}\n")
        f.write(f"**Total Questions:** {len(questions_list)}\n")
        f.write(f"**Purpose:** Medical professional review of categorization accuracy\n\n")
        f.write("---\n\n")

        # Instructions
        f.write("## Review Instructions\n\n")
        f.write("For each question below, please mark:\n\n")
        f.write("- ✓ **Correctly categorized** - Question clearly belongs in this category\n")
        f.write("- ✗ **Miscategorized** - Question belongs in a different category (note which one)\n")
        f.write("- ? **Ambiguous** - Question could reasonably fit multiple categories\n\n")
        f.write("**You don't need to review all questions!** Even 20-30 per category is very helpful.\n\n")
        f.write("---\n\n")

        # Category description
        descriptions = {
            'Clinical Findings': "Questions asking what findings you would expect to see on physical exam, lab tests, or imaging studies.",
            'Diagnosis': "Questions asking you to identify the disease, condition, or underlying cause of the patient's presentation.",
            'Mechanism/Pathophysiology': "Questions asking about how drugs work, disease mechanisms, or biological pathways - the 'why' and 'how' questions.",
            'Next Step/Workup': "Questions asking what test to order, what action to take next, or how to proceed with patient evaluation.",
            'Treatment/Management': "Questions asking which drug to prescribe, which therapy to choose, or how to manage the condition."
        }

        f.write(f"## What '{category}' Means\n\n")
        f.write(f"{descriptions.get(category, 'No description available.')}\n\n")
        f.write("---\n\n")

        # Questions
        f.write("## Questions for Review\n\n")

        for i, q in enumerate(questions_list, 1):
            f.write(f"### Question {i}\n\n")

            # Question text
            f.write("**Clinical Scenario:**\n\n")
            f.write(f"{q['question']}\n\n")

            # Options
            f.write("**Answer Choices:**\n\n")
            options = q.get('options', {})
            for key in sorted(options.keys()):
                f.write(f"{key}. {options[key]}\n")
            f.write("\n")

            # Correct answer
            answer = q.get('answer', 'Unknown')
            answer_idx = q.get('answer_idx', 'Unknown')
            f.write(f"**Correct Answer:** {answer_idx}. {answer}\n\n")

            # Review checkbox
            f.write("**Review Assessment:**\n")
            f.write("- [ ] ✓ Correctly categorized\n")
            f.write("- [ ] ✗ Miscategorized (should be: _____________)\n")
            f.write("- [ ] ? Ambiguous\n\n")
            f.write("**Comments:** _______________________________________________\n\n")

            f.write("---\n\n")

        # Summary section
        f.write("## Review Summary\n\n")
        f.write(f"**Category:** {category}\n")
        f.write(f"**Questions Reviewed:** _____ / {len(questions_list)}\n\n")
        f.write("**Overall Assessment:**\n")
        f.write(f"- Correctly categorized: _____ questions\n")
        f.write(f"- Miscategorized: _____ questions\n")
        f.write(f"- Ambiguous: _____ questions\n\n")
        f.write("**General Comments:**\n\n")
        f.write("_" * 80 + "\n\n")
        f.write("_" * 80 + "\n\n")
        f.write("_" * 80 + "\n\n")
        f.write("**Reviewer Name:** _______________________________________________\n\n")
        f.write("**Date:** _______________________________________________\n\n")
        f.write("**Credentials:** _______________________________________________\n\n")

    print(f"Created: {filepath.name} ({len(questions_list)} questions)")

print(f"\n✓ All documents created in: {output_dir}")
print(f"\nTotal: {sum(len(v) for v in categories.values())} questions across 5 categories")
