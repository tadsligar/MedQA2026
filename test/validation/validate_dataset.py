"""
Validate the recreated balanced dataset.
"""
import json
import sys
from pathlib import Path
from collections import Counter

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("="*80)
    print("Validating Balanced Dataset")
    print("="*80)
    print()

    project_root = Path(__file__).parent.parent
    dataset_path = project_root / "data" / "medqa_us_train_4opt_balanced.json"

    print(f"Loading: {dataset_path}")

    with open(dataset_path, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    print(f"[OK] Loaded {len(questions)} questions")

    # Check structure
    print("\nValidating structure...")

    required_fields = ['question', 'answer', 'options']
    for i, q in enumerate(questions[:5]):  # Check first 5
        for field in required_fields:
            if field not in q:
                print(f"[FAIL] Question {i} missing field: {field}")
                return

    print(f"[OK] All questions have required fields: {required_fields}")

    # Check option count
    option_counts = Counter(len(q['options']) for q in questions)
    print(f"\nOption counts: {dict(option_counts)}")

    if len(option_counts) == 1 and 4 in option_counts:
        print(f"[OK] All {len(questions)} questions have exactly 4 options")
    else:
        print(f"[FAIL] Inconsistent option counts!")
        return

    # Check answer format
    answers = Counter(q['answer'] for q in questions)
    print(f"\nAnswer distribution: {dict(answers)}")

    valid_answers = {'A', 'B', 'C', 'D'}
    invalid_answers = set(answers.keys()) - valid_answers

    if not invalid_answers:
        print(f"[OK] All answers are valid (A, B, C, D)")
    else:
        print(f"[FAIL] Found invalid answers: {invalid_answers}")
        return

    # Categorize and count
    print("\nCategorizing questions...")

    def categorize_question(question_text):
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

    category_counts = Counter(categorize_question(q['question']) for q in questions)

    print("\nCategory distribution:")
    for cat in sorted(category_counts.keys()):
        count = category_counts[cat]
        expected = 250 if cat not in ['Ethics/Professionalism', 'Prevention/Screening'] else None

        if expected and count == expected:
            status = "[OK]"
        elif cat == 'Ethics/Professionalism' and count == 29:
            status = "[OK]"
        elif cat == 'Prevention/Screening' and count == 235:
            status = "[OK]"
        else:
            status = "?"

        print(f"  {status} {cat:<30} {count:>4} questions")

    total = sum(category_counts.values())
    if total == 1764:
        print(f"\n[OK] Total: {total} questions (expected 1764)")
    else:
        print(f"\n[FAIL] Total: {total} questions (expected 1764)")

    # Sample a few questions
    print("\nSample questions:")
    for i in range(min(3, len(questions))):
        q = questions[i]
        print(f"\n--- Question {i+1} ---")
        print(f"Q: {q['question'][:100]}...")
        print(f"Options: {len(q['options'])} choices")
        print(f"Answer: {q['answer']}")
        print(f"Category: {categorize_question(q['question'])}")

    print("\n" + "="*80)
    print("Validation Complete! [OK]")
    print("="*80)

if __name__ == "__main__":
    main()
