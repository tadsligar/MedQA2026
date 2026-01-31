#!/usr/bin/env python3
"""
Analyze why keyword categorization doesn't match validated categories
even though the dataset was created using keyword+Qwen agreement.
"""

import json
from pathlib import Path
from collections import Counter, defaultdict

project_root = Path(__file__).parent.parent.parent


def categorize_question_keyword(question_text):
    """EXACT keyword function from original FL_Project script."""
    q = question_text.lower()

    if 'most likely diagnosis' in q or 'most likely cause of' in q or 'most likely underlying' in q:
        return 'Diagnosis'
    elif 'next step' in q or 'next best' in q or 'initial step' in q or 'first step' in q or 'appropriate test' in q:
        return 'Next Step/Workup'
    elif 'treatment' in q or 'management' in q or 'which drug' in q or 'which medication' in q or 'therapy' in q:
        return 'Treatment/Management'
    elif 'mechanism' in q or 'action' in q or 'pathway' in q or 'due to which' in q or 'result of' in q:
        return 'Mechanism/Pathophysiology'
    elif 'most likely to show' in q or 'expected finding' in q or 'most likely finding' in q:
        return 'Clinical Findings'
    else:
        return 'Other/Mixed'


def main():
    print("="*80)
    print("KEYWORD AGREEMENT MYSTERY ANALYSIS")
    print("="*80)
    print()

    # Load dataset
    with open(project_root / "data" / "datasets" / "medqa_focused_1030.json", 'r') as f:
        questions = json.load(f)

    print(f"Analyzing {len(questions)} questions...")
    print()

    # Analyze mismatches by pattern
    transitions = defaultdict(list)

    for i, q in enumerate(questions):
        validated = q.get('validated_category', 'Unknown')
        keyword = categorize_question_keyword(q['question'])

        if validated != keyword:
            transitions[f"{validated} → {keyword}"].append({
                'index': i,
                'question': q['question'],
                'validated': validated,
                'keyword': keyword
            })

    print("Mismatch Patterns (Validated → Keyword Now):")
    print("-" * 80)
    for transition, items in sorted(transitions.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {transition:<50} {len(items):>4} questions")

    print()
    print("="*80)
    print("HYPOTHESIS:")
    print("="*80)
    print()
    print("The keyword function uses a PRIORITY ORDER (if-elif chain).")
    print("The first matching pattern wins.")
    print()
    print("For example:")
    print('  if "most likely diagnosis" → Diagnosis')
    print('  elif "next step" → Next Step')
    print('  elif "treatment" → Treatment  <- This matches SECOND')
    print('  elif "mechanism" → Mechanism   <- This would match FIRST if "mechanism" appears')
    print()
    print("A question asking 'Which treatment helps prevent mechanism X?'")
    print("  - Contains 'mechanism' (matches 4th priority)")
    print("  - Contains 'treatment' (matches 3rd priority)")
    print("  - Keyword function returns: Treatment (higher priority)")
    print()
    print("But what if QWEN understood this as a Mechanism question?")
    print("And what if during validation, they happened to AGREE on Mechanism?")
    print()
    print("Let's check if this is what happened...")
    print()

    # Check for questions with multiple keyword triggers
    print("="*80)
    print("MULTI-TRIGGER ANALYSIS")
    print("="*80)
    print()

    multi_trigger_cases = []

    for q_data in questions:
        q = q_data['question'].lower()
        triggers = []

        if 'most likely diagnosis' in q or 'most likely cause of' in q or 'most likely underlying' in q:
            triggers.append('Diagnosis')
        if 'next step' in q or 'next best' in q or 'initial step' in q or 'first step' in q or 'appropriate test' in q:
            triggers.append('Next Step/Workup')
        if 'treatment' in q or 'management' in q or 'which drug' in q or 'which medication' in q or 'therapy' in q:
            triggers.append('Treatment/Management')
        if 'mechanism' in q or 'action' in q or 'pathway' in q or 'due to which' in q or 'result of' in q:
            triggers.append('Mechanism/Pathophysiology')
        if 'most likely to show' in q or 'expected finding' in q or 'most likely finding' in q:
            triggers.append('Clinical Findings')

        if len(triggers) > 1:
            validated = q_data.get('validated_category')
            keyword_result = categorize_question_keyword(q_data['question'])
            multi_trigger_cases.append({
                'triggers': triggers,
                'validated': validated,
                'keyword': keyword_result,
                'match': validated == keyword_result,
                'question': q_data['question'][:150]
            })

    print(f"Questions with multiple keyword triggers: {len(multi_trigger_cases)}/{len(questions)}")
    print()

    # Show examples where multiple triggers led to mismatch
    mismatched_multi = [c for c in multi_trigger_cases if not c['match']]
    print(f"Multi-trigger questions with MISMATCHES: {len(mismatched_multi)}")
    print()

    if mismatched_multi:
        print("Sample cases:")
        print("-" * 80)
        for i, case in enumerate(mismatched_multi[:5], 1):
            print(f"\n{i}. Triggers present: {', '.join(case['triggers'])}")
            print(f"   Validated as: {case['validated']}")
            print(f"   Keyword says: {case['keyword']}")
            print(f"   Question: {case['question']}...")

    print()
    print("="*80)
    print("CONCLUSION:")
    print("="*80)
    print()

    if len(mismatched_multi) > 300:
        print("✓ CONFIRMED: Priority order explains most mismatches!")
        print()
        print("The dataset was created with keyword+Qwen agreement, but:")
        print("1. Many questions have MULTIPLE keyword triggers")
        print("2. The if-elif priority order picks one category")
        print("3. Qwen likely picked a DIFFERENT category based on intent")
        print("4. When they AGREED, that became the validated category")
        print("5. But now re-running keywords gives a different result due to priority")
        print()
        print("This means:")
        print("- The 'agreement' was NOT on simple keyword matching")
        print("- Qwen categorization was trusted when keywords were ambiguous")
        print("- The validated_category represents CONSENSUS understanding")
        print("- Not just mechanical keyword matching")
    else:
        print("This doesn't fully explain the mystery.")
        print("Further investigation needed.")


if __name__ == "__main__":
    main()
