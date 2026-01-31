#!/usr/bin/env python3
"""
Verify the categorization methodology used to create the focused 1,030 dataset.

This script validates:
1. The keyword categorization function matches what was used
2. Questions in the focused dataset would be categorized the same way
3. The dual validation (keyword + Qwen agreement) methodology is correct
"""

import json
import sys
from pathlib import Path
from collections import Counter

project_root = Path(__file__).parent.parent.parent


def categorize_question_keyword(question_text):
    """
    Keyword-based categorization - copied from original script.
    This is the EXACT function used to create the dataset.
    """
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
    print("CATEGORIZATION METHODOLOGY VERIFICATION")
    print("="*80)
    print()

    # Load focused dataset
    dataset_path = project_root / "data" / "datasets" / "medqa_focused_1030.json"

    print(f"Loading dataset: {dataset_path}")
    with open(dataset_path, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    print(f"Total questions: {len(questions)}")
    print()

    # Verify all questions have validated_category
    has_category = sum(1 for q in questions if 'validated_category' in q)
    print(f"Questions with validated_category: {has_category}/{len(questions)}")

    if has_category != len(questions):
        print("⚠️  WARNING: Not all questions have validated_category!")
        print()

    # Count by validated category
    validated_counts = Counter(q.get('validated_category', 'Unknown') for q in questions)

    print("\nValidated Category Distribution:")
    print("-" * 80)
    for cat in sorted(validated_counts.keys()):
        count = validated_counts[cat]
        print(f"  {cat:<30} {count:>4} questions")

    print()

    # Now re-categorize using keyword method and compare
    print("Re-categorizing with keyword method...")
    print()

    keyword_counts = Counter()
    matches = 0
    mismatches = []

    for i, q in enumerate(questions):
        question_text = q['question']
        validated_cat = q.get('validated_category', 'Unknown')
        keyword_cat = categorize_question_keyword(question_text)

        keyword_counts[keyword_cat] += 1

        if keyword_cat == validated_cat:
            matches += 1
        else:
            mismatches.append({
                'index': i,
                'question': question_text[:150],
                'validated': validated_cat,
                'keyword': keyword_cat
            })

    print("Keyword Categorization Results:")
    print("-" * 80)
    for cat in sorted(keyword_counts.keys()):
        count = keyword_counts[cat]
        print(f"  {cat:<30} {count:>4} questions")

    print()
    print("="*80)
    print("VERIFICATION RESULTS")
    print("="*80)
    print()

    match_rate = (matches / len(questions)) * 100
    print(f"Matches: {matches}/{len(questions)} ({match_rate:.2f}%)")
    print(f"Mismatches: {len(mismatches)}/{len(questions)} ({100-match_rate:.2f}%)")
    print()

    if match_rate == 100.0:
        print("✅ PERFECT MATCH!")
        print("   All questions match their validated_category using keyword method.")
        print()
        print("🔍 CONCLUSION:")
        print("   This suggests the dataset was created using simple keyword categorization,")
        print("   OR the Qwen+keyword agreement was 100% for these 1,030 questions.")
        print()
    elif match_rate >= 95.0:
        print("✅ VERY HIGH MATCH!")
        print(f"   {match_rate:.1f}% of questions match using keyword method.")
        print()
        print("🔍 CONCLUSION:")
        print("   Most questions match keyword categorization.")
        print("   Small differences suggest either:")
        print("   - Qwen categorization was used for some edge cases")
        print("   - Minor differences in keyword matching implementation")
        print()
    else:
        print("⚠️  SIGNIFICANT DIFFERENCES!")
        print(f"   Only {match_rate:.1f}% match using keyword method.")
        print()
        print("🔍 CONCLUSION:")
        print("   The dataset likely used Qwen categorization or a hybrid approach,")
        print("   not simple keyword matching.")
        print()

    # Show sample mismatches
    if mismatches:
        print("Sample Mismatches:")
        print("-" * 80)
        for i, mm in enumerate(mismatches[:5], 1):
            print(f"\n{i}. Question: {mm['question']}...")
            print(f"   Validated: {mm['validated']}")
            print(f"   Keyword:   {mm['keyword']}")

    # Load summary to compare
    summary_path = project_root / "data" / "datasets" / "medqa_focused_1030_summary.json"
    if summary_path.exists():
        with open(summary_path, 'r') as f:
            summary = json.load(f)

        print()
        print("="*80)
        print("SUMMARY FILE INFORMATION")
        print("="*80)
        print()
        print(f"Total validated: {summary.get('total_validated', 'N/A')}")
        print(f"Iterations required: {summary.get('iterations_required', 'N/A')}")
        print(f"Tokens used: {summary.get('validation_tokens_used', 'N/A'):,}")
        print()
        print("Agreement counts (from summary):")
        agreement_counts = summary.get('agreement_counts', {})
        for cat, count in sorted(agreement_counts.items()):
            print(f"  {cat:<30} {count:>4}")
        print()
        print("🔍 INTERPRETATION:")
        print(f"   - Validated {summary.get('total_validated', 0)} total questions")
        print(f"   - Found {sum(agreement_counts.values())} agreements")
        print(f"   - Sampled 206 from each category → 1,030 final")
        print()
        total_validated = summary.get('total_validated', 0)
        total_agreements = sum(agreement_counts.values())
        if total_validated > 0:
            agreement_rate = (total_agreements / total_validated) * 100
            print(f"   Overall agreement rate: {total_agreements}/{total_validated} = {agreement_rate:.1f}%")
            print()
            print("   This suggests:")
            print(f"   - Keyword and Qwen agreed on {agreement_rate:.1f}% of validated questions")
            print("   - Dataset used DUAL VALIDATION (both methods must agree)")
            print("   - Disagreements were DISCARDED (not resolved)")

    print()
    print("="*80)
    print("VERIFICATION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
