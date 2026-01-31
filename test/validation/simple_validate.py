"""
Simple validation of the recreated balanced dataset.
"""
import json
import sys
from pathlib import Path
from collections import Counter

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def categorize_question(question_text):
    """Categorize a question based on its content."""
    q = question_text.lower()
    if 'most likely diagnosis' in q or 'most likely cause of' in q or 'most likely underlying' in q:
        return 'Diagnosis'
    elif 'next step' in q or 'next best' in q or 'initial step' in q or 'first step' in q or 'appropriate test' in q:
        return 'Next Step/Workup'
    elif 'should tell' in q or 'appropriate action' in q or 'correct action' in q or 'ethics' in q or 'consent' in q:
        return 'Ethics/Professionalism'
    elif 'treatment' in q or 'management' in q or 'which drug' in q or 'which medication' in q or 'therapy' in q:
        return 'Treatment/Management'
    elif 'mechanism' in q or 'action' in q or 'pathway' in q or 'due to which' in q or 'result of' in q:
        return 'Mechanism/Pathophysiology'
    elif 'most likely to show' in q or 'expected finding' in q or 'most likely finding' in q:
        return 'Clinical Findings'
    elif 'prevent' in q or 'screening' in q or 'prophylaxis' in q:
        return 'Prevention/Screening'
    else:
        return 'Other/Mixed'

def main():
    print("="*80)
    print("Simple Validation of Balanced Dataset")
    print("="*80)
    print()

    project_root = Path(__file__).parent.parent
    dataset_path = project_root / "data" / "medqa_us_train_4opt_balanced.json"

    print(f"Loading: {dataset_path}")

    with open(dataset_path, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    print(f"[OK] Loaded {len(questions)} questions")

    # Check option count
    option_counts = Counter(len(q['options']) for q in questions)

    if len(option_counts) == 1 and 4 in option_counts:
        print(f"[OK] All {len(questions)} questions have exactly 4 options")
    else:
        print(f"[FAIL] Inconsistent option counts: {dict(option_counts)}")
        return

    # Categorize and count
    print("\nCategorizing questions...")
    category_counts = Counter(categorize_question(q['question']) for q in questions)

    # Expected distribution
    expected = {
        'Clinical Findings': 250,
        'Diagnosis': 250,
        'Mechanism/Pathophysiology': 250,
        'Next Step/Workup': 250,
        'Other/Mixed': 250,
        'Treatment/Management': 250,
        'Prevention/Screening': 235,
        'Ethics/Professionalism': 29
    }

    print("\nCategory Distribution Validation:")
    print(f"{'Category':<30} {'Count':>6} {'Expected':>8} {'Status'}")
    print("-" * 70)

    all_match = True
    for cat in sorted(expected.keys()):
        count = category_counts.get(cat, 0)
        exp = expected[cat]
        status = "[OK]" if count == exp else "[MISMATCH]"
        if count != exp:
            all_match = False
        print(f"{cat:<30} {count:>6} {exp:>8}     {status}")

    total = sum(category_counts.values())
    expected_total = 1764

    print("-" * 70)
    print(f"{'TOTAL':<30} {total:>6} {expected_total:>8}     {'[OK]' if total == expected_total else '[FAIL]'}")

    # Sample questions
    print("\nSample Questions (first 3):")
    for i in range(min(3, len(questions))):
        q = questions[i]
        print(f"\n--- Question {i+1} ---")
        print(f"Question: {q['question'][:80]}...")
        print(f"Options: {len(q['options'])} choices")
        print(f"Category: {categorize_question(q['question'])}")

    print("\n" + "="*80)
    if all_match and total == expected_total:
        print("VALIDATION PASSED!")
        print("Dataset successfully recreated with correct distribution!")
    else:
        print("VALIDATION FAILED - Counts do not match expected distribution")
    print("="*80)

if __name__ == "__main__":
    main()
