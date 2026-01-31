"""
Iteratively sample and validate questions until we have 250 agreements per category.
Builds on existing validation results.
"""

import json
import random
import time
from pathlib import Path
from collections import defaultdict
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.llm_client import create_llm_client
from src.config import Config


def categorize_question_keyword(question_text):
    """Keyword-based categorization."""
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


def categorize_with_qwen(question_text, llm):
    """Get Qwen's categorization."""
    prompt = f"""You are a medical education expert. Categorize this medical question into ONE of these 5 categories:

1. Clinical Findings - Questions asking what you would expect to find on exam/lab/imaging
2. Diagnosis - Questions asking for the most likely diagnosis or cause
3. Mechanism/Pathophysiology - Questions about how drugs work, disease mechanisms, pathways
4. Next Step/Workup - Questions about what test or action to do next
5. Treatment/Management - Questions about which drug, therapy, or management approach to use

Question: {question_text}

Respond with ONLY the category number (1, 2, 3, 4, or 5), nothing else."""

    response = llm.complete(prompt, temperature=0.0)

    category_map = {
        '1': 'Clinical Findings',
        '2': 'Diagnosis',
        '3': 'Mechanism/Pathophysiology',
        '4': 'Next Step/Workup',
        '5': 'Treatment/Management'
    }

    response_text = response.content.strip()
    for num, cat in category_map.items():
        if num in response_text:
            return cat, response.tokens_used or 0

    return None, response.tokens_used or 0


def load_checkpoint():
    """Load existing checkpoint if available."""
    checkpoint_file = project_root / "runs" / "high_confidence_iterative" / "checkpoint.json"

    if checkpoint_file.exists():
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    return {
        'category_agreements': {cat: [] for cat in [
            'Clinical Findings',
            'Diagnosis',
            'Mechanism/Pathophysiology',
            'Next Step/Workup',
            'Treatment/Management'
        ]},
        'validated_indices': set(),
        'iteration': 0,
        'total_tokens': 0
    }


def save_checkpoint(checkpoint):
    """Save checkpoint."""
    output_dir = project_root / "runs" / "high_confidence_iterative"
    output_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_file = output_dir / "checkpoint.json"

    # Convert set to list for JSON serialization
    checkpoint_copy = checkpoint.copy()
    checkpoint_copy['validated_indices'] = list(checkpoint['validated_indices'])

    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump(checkpoint_copy, f, indent=2, ensure_ascii=False)


def main():
    print("="*80)
    print("ITERATIVE HIGH-CONFIDENCE DATASET CREATION")
    print("="*80)
    print()

    # Load full training dataset
    dataset_path = project_root / "data" / "medqa_us_train_4opt_balanced.json"

    print(f"Loading dataset: {dataset_path}")
    with open(dataset_path, 'r', encoding='utf-8') as f:
        full_dataset = json.load(f)

    print(f"Total questions available: {len(full_dataset)}")
    print()

    # Load LLM
    config = Config.from_yaml(str(project_root / "configs" / "qwen25_32b.yaml"))
    llm = create_llm_client(config)

    # Load checkpoint
    checkpoint = load_checkpoint()

    # Convert validated_indices back to set
    if isinstance(checkpoint['validated_indices'], list):
        checkpoint['validated_indices'] = set(checkpoint['validated_indices'])

    category_agreements = checkpoint['category_agreements']
    validated_indices = checkpoint['validated_indices']
    iteration = checkpoint['iteration']
    total_tokens = checkpoint['total_tokens']

    target_categories = [
        'Clinical Findings',
        'Diagnosis',
        'Mechanism/Pathophysiology',
        'Next Step/Workup',
        'Treatment/Management'
    ]

    # Check current status
    print("Current agreement counts:")
    for cat in target_categories:
        count = len(category_agreements[cat])
        need = max(0, 250 - count)
        print(f"  {cat:<30} {count:>3}/250 (need {need} more)")

    print(f"\nQuestions validated so far: {len(validated_indices)}")
    print(f"Iterations completed: {iteration}")
    print(f"Total tokens used: {total_tokens:,}")
    print()

    # Check if we're done
    all_complete = all(len(category_agreements[cat]) >= 250 for cat in target_categories)

    if all_complete:
        print("All categories have 250+ agreements! Creating final dataset...")

        # Sample exactly 250 from each
        random.seed(42)
        final_questions = []

        for cat in target_categories:
            available = category_agreements[cat]
            selected = random.sample(available, 250)
            final_questions.extend(selected)

        random.shuffle(final_questions)

        output_file = project_root / "data" / "medqa_us_train_4opt_high_confidence_250.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_questions, f, indent=2, ensure_ascii=False)

        print(f"\nFinal dataset saved: {output_file}")
        print(f"Total questions: {len(final_questions)} (250 per category)")
        return

    # Run sampling iterations
    batch_size = 100  # Validate 100 questions per iteration

    while not all_complete:
        iteration += 1

        print(f"\n{'='*80}")
        print(f"ITERATION {iteration}")
        print(f"{'='*80}\n")

        # Get unvalidated indices
        all_indices = set(range(len(full_dataset)))
        unvalidated = list(all_indices - validated_indices)

        if not unvalidated:
            print("No more questions available to validate!")
            print("Cannot reach 250 per category with available data.")
            break

        # Sample batch
        sample_size = min(batch_size, len(unvalidated))
        sample_indices = random.sample(unvalidated, sample_size)

        print(f"Sampling {sample_size} new questions for validation...")
        print()

        # Validate each question
        agreements_this_iteration = 0

        for idx in sample_indices:
            question_data = full_dataset[idx]
            question_text = question_data['question']

            # Get both categorizations
            keyword_cat = categorize_question_keyword(question_text)
            qwen_cat, tokens = categorize_with_qwen(question_text, llm)

            total_tokens += tokens
            validated_indices.add(idx)

            # Check if they agree and in target categories
            if keyword_cat == qwen_cat and keyword_cat in target_categories:
                # Add to agreements if not already at 250
                if len(category_agreements[keyword_cat]) < 250:
                    question_data['validated_category'] = keyword_cat
                    category_agreements[keyword_cat].append(question_data)
                    agreements_this_iteration += 1

        print(f"New agreements found: {agreements_this_iteration}")
        print()

        # Show updated counts
        print("Updated agreement counts:")
        for cat in target_categories:
            count = len(category_agreements[cat])
            need = max(0, 250 - count)
            status = "COMPLETE" if count >= 250 else f"need {need}"
            print(f"  {cat:<30} {count:>3}/250 ({status})")

        print(f"\nTotal validated: {len(validated_indices)}/{len(full_dataset)}")
        print(f"Total tokens: {total_tokens:,}")

        # Save checkpoint
        checkpoint['category_agreements'] = category_agreements
        checkpoint['validated_indices'] = validated_indices
        checkpoint['iteration'] = iteration
        checkpoint['total_tokens'] = total_tokens
        save_checkpoint(checkpoint)

        # Check if complete
        all_complete = all(len(category_agreements[cat]) >= 250 for cat in target_categories)

        if all_complete:
            print("\nAll categories reached 250! Creating final dataset...")

            # Sample exactly 250 from each
            random.seed(42)
            final_questions = []

            for cat in target_categories:
                available = category_agreements[cat]
                selected = random.sample(available, 250)
                final_questions.extend(selected)

            random.shuffle(final_questions)

            output_file = project_root / "data" / "medqa_us_train_4opt_high_confidence_250.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(final_questions, f, indent=2, ensure_ascii=False)

            print(f"\nFinal dataset saved: {output_file}")
            print(f"Total questions: {len(final_questions)} (250 per category)")

            # Save summary
            summary = {
                'total_questions': len(final_questions),
                'questions_per_category': 250,
                'categories': target_categories,
                'iterations_required': iteration,
                'total_validated': len(validated_indices),
                'total_tokens_used': total_tokens,
                'agreement_rate': len(final_questions) / len(validated_indices)
            }

            summary_file = project_root / "data" / "medqa_us_train_4opt_high_confidence_250_summary.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2)

            print(f"Summary saved: {summary_file}")
            break


if __name__ == "__main__":
    main()
