"""
Create final balanced high-confidence dataset with 206 questions per category (1,030 total).
This is the maximum balanced dataset possible given Treatment constraint.
"""

import json
import random
from pathlib import Path

project_root = Path(__file__).parent.parent

# Load checkpoint with all agreements
checkpoint_file = project_root / "runs" / "high_confidence_iterative" / "checkpoint.json"

with open(checkpoint_file, 'r', encoding='utf-8') as f:
    checkpoint = json.load(f)

category_agreements = checkpoint['category_agreements']

target_categories = [
    'Clinical Findings',
    'Diagnosis',
    'Mechanism/Pathophysiology',
    'Next Step/Workup',
    'Treatment/Management'
]

print("="*80)
print("FINAL BALANCED HIGH-CONFIDENCE DATASET")
print("="*80)
print()

print("Available agreements by category:")
for cat in target_categories:
    count = len(category_agreements[cat])
    print(f"  {cat:<30} {count:>3} questions")

# Find minimum (limiting category)
min_count = min(len(category_agreements[cat]) for cat in target_categories)

print()
print(f"Minimum agreements: {min_count} (Treatment/Management)")
print(f"Creating balanced dataset with {min_count} questions per category")
print()

# Sample min_count from each category
random.seed(42)
final_questions = []

for cat in target_categories:
    available = category_agreements[cat]
    selected = random.sample(available, min_count)
    final_questions.extend(selected)
    print(f"  {cat:<30} {len(selected):>3} sampled")

# Shuffle final dataset
random.shuffle(final_questions)

print()
print(f"Total questions: {len(final_questions)} ({min_count} × 5 categories)")

# Save dataset
output_file = project_root / "data" / "medqa_us_train_4opt_high_confidence_balanced.json"

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(final_questions, f, indent=2, ensure_ascii=False)

print(f"\nDataset saved: {output_file}")

# Save summary
summary = {
    'total_questions': len(final_questions),
    'questions_per_category': min_count,
    'categories': target_categories,
    'category_distribution': {cat: min_count for cat in target_categories},
    'total_validated': len(checkpoint['validated_indices']),
    'validation_tokens_used': checkpoint['total_tokens'],
    'iterations_required': checkpoint['iteration'],
    'constraint': f'Limited by Treatment/Management with only {min_count} agreements (54% agreement rate)',
    'agreement_counts': {
        cat: len(category_agreements[cat]) for cat in target_categories
    },
    'random_seed': 42
}

summary_file = project_root / "data" / "medqa_us_train_4opt_high_confidence_balanced_summary.json"
with open(summary_file, 'w', encoding='utf-8') as f:
    json.dump(summary, f, indent=2)

print(f"Summary saved: {summary_file}")

print()
print("="*80)
print("DATASET CREATION COMPLETE")
print("="*80)
print()
print(f"Final dataset: {len(final_questions)} questions ({min_count} per category)")
print(f"All questions have both Qwen and keyword categorization agreement")
print()
print("Ready for temperature impact testing!")
