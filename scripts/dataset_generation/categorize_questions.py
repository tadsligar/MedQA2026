#!/usr/bin/env python3
"""
Question Categorization for MedQA Dataset
==========================================

This script implements the dual validation process for categorizing MedQA questions
into 5 clinical reasoning categories.

Methodology:
1. Keyword-based classification (rule-based)
2. LLM validation using Qwen 2.5
3. Inter-method agreement threshold: 90%+

Categories:
1. Clinical Findings - What findings would you expect?
2. Diagnosis - What is the most likely diagnosis?
3. Mechanism/Pathophysiology - How does this drug/disease work?
4. Next Step/Workup - What should be done next?
5. Treatment/Management - What treatment should be given?

Date: January 2026
"""

from typing import Dict, List, Optional, Tuple
import json
import re
from collections import Counter


# Category mappings
CATEGORY_MAP = {
    1: "Clinical Findings",
    2: "Diagnosis",
    3: "Mechanism/Pathophysiology",
    4: "Next Step/Workup",
    5: "Treatment/Management"
}

CATEGORY_TO_NUM = {v: k for k, v in CATEGORY_MAP.items()}


def categorize_with_qwen(question: str, llm) -> str:
    """
    Categorize a medical question using Qwen LLM.

    This is the LLM validation method that achieved 90%+ agreement
    with keyword-based classification.

    Args:
        question: The medical question text
        llm: LLM interface with .complete() method

    Returns:
        Category name (e.g., "Clinical Findings")
    """
    prompt = f"""You are a medical education expert. Categorize this question into ONE category:

1. Clinical Findings - What findings would you expect?
2. Diagnosis - What is the most likely diagnosis?
3. Mechanism/Pathophysiology - How does this drug/disease work?
4. Next Step/Workup - What should be done next?
5. Treatment/Management - What treatment should be given?

Question: {question}

Respond with ONLY the category number (1-5)."""

    response = llm.complete(prompt, temperature=0.0)
    category_num = extract_category_number(response)
    return map_to_category(category_num)


def map_to_category(category_num: int) -> str:
    """Map category number to category name."""
    return CATEGORY_MAP.get(category_num, "Unknown")


def extract_category_number(response: str) -> int:
    """
    Extract category number from LLM response.

    Handles various response formats:
    - "1"
    - "Category 1"
    - "The answer is 1"
    - etc.
    """
    # Try to find a number 1-5 in the response
    numbers = re.findall(r'\b([1-5])\b', response)
    if numbers:
        return int(numbers[0])

    # Default to unknown if no valid number found
    return 0


def categorize_with_keywords(question: str) -> str:
    """
    Categorize question using keyword-based rules.

    This is the rule-based method used as the first pass
    before LLM validation.

    Args:
        question: The medical question text

    Returns:
        Category name (e.g., "Clinical Findings")
    """
    question_lower = question.lower()

    # Clinical Findings keywords
    if any(phrase in question_lower for phrase in [
        'would you expect',
        'most likely finding',
        'physical examination',
        'examination finding',
        'lab finding',
        'expected finding'
    ]):
        return "Clinical Findings"

    # Diagnosis keywords
    if any(phrase in question_lower for phrase in [
        'most likely diagnosis',
        'diagnosis',
        'condition',
        'disease',
        'what does this patient have'
    ]):
        return "Diagnosis"

    # Mechanism/Pathophysiology keywords
    if any(phrase in question_lower for phrase in [
        'mechanism',
        'pathophysiology',
        'how does',
        'why does',
        'explains',
        'underlying cause',
        'molecular basis'
    ]):
        return "Mechanism/Pathophysiology"

    # Next Step/Workup keywords
    if any(phrase in question_lower for phrase in [
        'next step',
        'next best step',
        'most appropriate next',
        'should be done next',
        'initial step',
        'diagnostic test',
        'workup'
    ]):
        return "Next Step/Workup"

    # Treatment/Management keywords
    if any(phrase in question_lower for phrase in [
        'treatment',
        'management',
        'therapy',
        'should be given',
        'should be administered',
        'best medication',
        'drug of choice'
    ]):
        return "Treatment/Management"

    return "Unknown"


def dual_validate_question(question: str, llm) -> Tuple[str, str, bool]:
    """
    Validate question category using both methods.

    Args:
        question: The medical question text
        llm: LLM interface

    Returns:
        Tuple of (keyword_category, llm_category, agreement)
    """
    keyword_category = categorize_with_keywords(question)
    llm_category = categorize_with_qwen(question, llm)

    agreement = (keyword_category == llm_category) and (keyword_category != "Unknown")

    return keyword_category, llm_category, agreement


def validate_dataset(questions: List[Dict], llm) -> Dict:
    """
    Validate entire dataset using dual categorization.

    Args:
        questions: List of question dictionaries with 'question' field
        llm: LLM interface

    Returns:
        Dictionary with validation statistics and categorized questions
    """
    results = {
        'total': len(questions),
        'agreed': 0,
        'disagreed': 0,
        'by_category': Counter(),
        'questions': []
    }

    for i, q_dict in enumerate(questions):
        question_text = q_dict.get('question', '')

        keyword_cat, llm_cat, agreement = dual_validate_question(question_text, llm)

        result = {
            'index': i,
            'question': question_text,
            'keyword_category': keyword_cat,
            'llm_category': llm_cat,
            'agreement': agreement,
            'final_category': llm_cat if agreement else None
        }

        results['questions'].append(result)

        if agreement:
            results['agreed'] += 1
            results['by_category'][llm_cat] += 1
        else:
            results['disagreed'] += 1

    results['agreement_rate'] = results['agreed'] / results['total'] if results['total'] > 0 else 0

    return results


def balance_dataset(categorized_questions: List[Dict], target_per_category: int = 206,
                   random_seed: int = 42) -> List[Dict]:
    """
    Balance dataset to have equal questions per category.

    Args:
        categorized_questions: List of questions with 'final_category' field
        target_per_category: Number of questions to sample per category
        random_seed: Random seed for reproducibility

    Returns:
        Balanced list of questions
    """
    import random
    random.seed(random_seed)

    # Group by category
    by_category = {}
    for q in categorized_questions:
        cat = q.get('final_category')
        if cat and cat != "Unknown":
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(q)

    # Sample target_per_category from each
    balanced = []
    for cat, questions in by_category.items():
        if len(questions) >= target_per_category:
            sampled = random.sample(questions, target_per_category)
        else:
            sampled = questions  # Take all if fewer than target
        balanced.extend(sampled)

    return balanced


def main():
    """
    Example usage for categorizing and validating a MedQA dataset.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Categorize MedQA questions')
    parser.add_argument('--input', required=True, help='Input JSON file with questions')
    parser.add_argument('--output', required=True, help='Output JSON file for categorized questions')
    parser.add_argument('--model', default='Qwen/Qwen2.5-7B', help='Model for LLM validation')
    parser.add_argument('--balance', action='store_true', help='Balance categories to 206 each')

    args = parser.parse_args()

    # Load questions
    with open(args.input, 'r') as f:
        questions = json.load(f)

    print(f"Loaded {len(questions)} questions")

    # Initialize LLM (pseudo-code, adjust based on your LLM interface)
    # from your_llm_interface import LLM
    # llm = LLM(model=args.model)

    print("Running dual validation...")
    # results = validate_dataset(questions, llm)

    # print(f"\nValidation Results:")
    # print(f"  Total: {results['total']}")
    # print(f"  Agreed: {results['agreed']} ({results['agreement_rate']:.1%})")
    # print(f"  Disagreed: {results['disagreed']}")
    # print(f"\nBy Category:")
    # for cat, count in results['by_category'].items():
    #     print(f"  {cat}: {count}")

    # if args.balance:
    #     balanced = balance_dataset(results['questions'], target_per_category=206)
    #     print(f"\nBalanced to {len(balanced)} questions ({len(balanced)//5} per category)")
    #
    #     with open(args.output, 'w') as f:
    #         json.dump(balanced, f, indent=2)
    # else:
    #     with open(args.output, 'w') as f:
    #         json.dump(results, f, indent=2)

    print(f"Note: LLM interface code commented out. Implement based on your setup.")


if __name__ == '__main__':
    main()
