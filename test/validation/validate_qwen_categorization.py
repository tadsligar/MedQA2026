"""
Validate Qwen's categorization accuracy on full balanced dataset.
Compare Qwen categorization to keyword-based categorization.
Uses checkpointing for resumability.
"""

import json
import sys
import time
from pathlib import Path
from collections import defaultdict

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.llm_client import create_llm_client
from src.config import Config


def categorize_question_keywords(question_text):
    """Keyword-based categorization (baseline)."""
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
    elif 'prevent' in q or 'screening' in q or 'prophylaxis' in q:
        return 'Prevention/Screening'
    elif 'should tell' in q or 'appropriate action' in q or 'correct action' in q or 'ethics' in q or 'consent' in q:
        return 'Ethics/Professionalism'
    else:
        return 'Other/Mixed'


def categorize_question_qwen(question_text, llm):
    """Ask Qwen to categorize the question."""

    prompt = f"""You are a medical education expert. Categorize this medical question into ONE of these 5 categories:

1. Clinical Findings - Questions asking what you would expect to find on exam/lab/imaging
2. Diagnosis - Questions asking for the most likely diagnosis or cause
3. Mechanism/Pathophysiology - Questions about how drugs work, disease mechanisms, pathways
4. Next Step/Workup - Questions about what test or action to do next
5. Treatment/Management - Questions about which drug, therapy, or management approach to use

Question: {question_text}

Respond with ONLY the category number (1, 2, 3, 4, or 5), nothing else."""

    response = llm.complete(prompt, temperature=0.0)

    # Extract number from response
    content = response.content.strip()

    # Map number to category
    category_map = {
        '1': 'Clinical Findings',
        '2': 'Diagnosis',
        '3': 'Mechanism/Pathophysiology',
        '4': 'Next Step/Workup',
        '5': 'Treatment/Management'
    }

    # Try to find number in response
    for num in ['1', '2', '3', '4', '5']:
        if num in content:
            return category_map[num], response.tokens_used or 0

    # Fallback: parse from text
    content_lower = content.lower()
    if 'clinical finding' in content_lower:
        return 'Clinical Findings', response.tokens_used or 0
    elif 'diagnosis' in content_lower:
        return 'Diagnosis', response.tokens_used or 0
    elif 'mechanism' in content_lower or 'pathophysiology' in content_lower:
        return 'Mechanism/Pathophysiology', response.tokens_used or 0
    elif 'next step' in content_lower or 'workup' in content_lower:
        return 'Next Step/Workup', response.tokens_used or 0
    elif 'treatment' in content_lower or 'management' in content_lower:
        return 'Treatment/Management', response.tokens_used or 0
    else:
        return 'Other/Mixed', response.tokens_used or 0


def load_checkpoint(output_dir):
    """Load checkpoint if it exists."""
    checkpoint_file = output_dir / "qwen_categorization_checkpoint.json"

    if checkpoint_file.exists():
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)
        return checkpoint['results'], checkpoint['next_index']

    return [], 0


def save_checkpoint(output_dir, results, next_index):
    """Save checkpoint."""
    checkpoint_file = output_dir / "qwen_categorization_checkpoint.json"

    checkpoint = {
        'results': results,
        'next_index': next_index,
        'timestamp': time.time()
    }

    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump(checkpoint, f, indent=2, ensure_ascii=False)


def main():
    print("="*80)
    print("QWEN CATEGORIZATION VALIDATION")
    print("="*80)
    print()

    # Setup output directory
    output_dir = project_root / "runs" / "qwen_categorization_validation"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load balanced dataset
    dataset_path = project_root / "data" / "medqa_us_train_4opt_balanced.json"

    with open(dataset_path, 'r', encoding='utf-8') as f:
        all_questions = json.load(f)

    # Filter to 5 target categories using keyword method
    target_categories = [
        'Clinical Findings',
        'Diagnosis',
        'Mechanism/Pathophysiology',
        'Next Step/Workup',
        'Treatment/Management'
    ]

    filtered_questions = []
    for q in all_questions:
        keyword_cat = categorize_question_keywords(q['question'])
        if keyword_cat in target_categories:
            q['keyword_category'] = keyword_cat
            filtered_questions.append(q)

    print(f"Total questions: {len(all_questions)}")
    print(f"Filtered to 5 categories: {len(filtered_questions)}")

    # Count per category (keyword baseline)
    keyword_counts = defaultdict(int)
    for q in filtered_questions:
        keyword_counts[q['keyword_category']] += 1

    print("\nKeyword categorization distribution:")
    for cat in sorted(target_categories):
        print(f"  {cat:<30} {keyword_counts[cat]:>4} questions")

    # Load LLM
    config = Config.from_yaml(str(project_root / "configs" / "qwen25_32b.yaml"))
    llm = create_llm_client(config)

    # Load checkpoint
    results, start_idx = load_checkpoint(output_dir)

    if start_idx > 0:
        print(f"\nResuming from question {start_idx}/{len(filtered_questions)}")
        total_tokens = sum(r['tokens'] for r in results)
    else:
        print(f"\nStarting fresh validation...")
        total_tokens = 0

    # Run Qwen categorization
    print("\nAsking Qwen to categorize each question...")
    print("(This will take ~20-30 minutes)")
    print()

    for idx in range(start_idx, len(filtered_questions)):
        question = filtered_questions[idx]

        # Get Qwen's categorization
        qwen_cat, tokens = categorize_question_qwen(question['question'], llm)
        total_tokens += tokens

        # Compare to keyword categorization
        keyword_cat = question['keyword_category']
        agreement = (qwen_cat == keyword_cat)

        results.append({
            'question_id': idx,
            'question': question['question'][:200],  # Truncate for readability
            'keyword_category': keyword_cat,
            'qwen_category': qwen_cat,
            'agreement': agreement,
            'tokens': tokens
        })

        # Save checkpoint every 10 questions
        if (idx + 1) % 10 == 0:
            save_checkpoint(output_dir, results, idx + 1)

            agreements = sum(1 for r in results if r['agreement'])
            accuracy = agreements / len(results) * 100
            avg_tokens = total_tokens / len(results)

            remaining = len(filtered_questions) - (idx + 1)
            eta_seconds = remaining * 1.5  # Estimate 1.5s per question
            eta_minutes = eta_seconds / 60

            print(f"  [{idx + 1}/{len(filtered_questions)}] Agreement: {accuracy:.2f}% | Avg tokens: {avg_tokens:.0f} | ETA: {eta_minutes:.1f} min")

    # Final save
    save_checkpoint(output_dir, results, len(filtered_questions))

    # Calculate statistics
    print("\n" + "="*80)
    print("VALIDATION RESULTS")
    print("="*80)
    print()

    total_agreement = sum(1 for r in results if r['agreement'])
    total_questions = len(results)
    overall_accuracy = total_agreement / total_questions * 100

    print(f"Overall Agreement: {total_agreement}/{total_questions} = {overall_accuracy:.2f}%")
    print(f"Total tokens used: {total_tokens:,}")
    print(f"Avg tokens per question: {total_tokens/total_questions:.1f}")
    print()

    # Per-category agreement
    print("Agreement by Category (Keyword baseline):")
    print("-" * 80)

    category_stats = defaultdict(lambda: {'agree': 0, 'total': 0})

    for r in results:
        keyword_cat = r['keyword_category']
        category_stats[keyword_cat]['total'] += 1
        if r['agreement']:
            category_stats[keyword_cat]['agree'] += 1

    for cat in sorted(target_categories):
        agree = category_stats[cat]['agree']
        total = category_stats[cat]['total']
        pct = (agree / total * 100) if total > 0 else 0
        print(f"  {cat:<30} {agree:>4}/{total:<4} = {pct:>6.2f}%")

    # Analyze disagreements
    disagreements = [r for r in results if not r['agreement']]

    print("\n" + "="*80)
    print(f"DISAGREEMENTS ({len(disagreements)} questions)")
    print("="*80)
    print()

    # Group disagreements by transition
    transitions = defaultdict(list)
    for r in disagreements:
        transition = f"{r['keyword_category']} → {r['qwen_category']}"
        transitions[transition].append(r)

    print("Disagreement patterns:")
    for transition, items in sorted(transitions.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {transition:<60} {len(items):>3} questions")

    # Show examples of common disagreements
    print("\nExamples of disagreements:")
    print("-" * 80)

    for transition, items in sorted(transitions.items(), key=lambda x: len(x[1]), reverse=True)[:3]:
        print(f"\n{transition} ({len(items)} questions)")
        for i, r in enumerate(items[:2], 1):
            print(f"\n  Example {i}: {r['question']}...")
            print(f"    Keyword: {r['keyword_category']}")
            print(f"    Qwen:    {r['qwen_category']}")

    # Save summary
    summary = {
        'total_questions': total_questions,
        'total_agreement': total_agreement,
        'overall_accuracy': overall_accuracy,
        'total_tokens': total_tokens,
        'avg_tokens_per_question': total_tokens / total_questions,
        'category_agreement': {
            cat: {
                'agree': category_stats[cat]['agree'],
                'total': category_stats[cat]['total'],
                'accuracy': (category_stats[cat]['agree'] / category_stats[cat]['total'] * 100) if category_stats[cat]['total'] > 0 else 0
            }
            for cat in target_categories
        },
        'disagreement_patterns': {k: len(v) for k, v in transitions.items()},
        'disagreement_examples': [
            {
                'question': r['question'],
                'keyword': r['keyword_category'],
                'qwen': r['qwen_category']
            }
            for r in disagreements[:20]  # First 20 examples
        ]
    }

    summary_file = output_dir / "summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    print(f"\n\nSummary saved to: {summary_file}")

    # Recommendation
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)
    print()

    if overall_accuracy >= 90:
        print("✅ EXCELLENT: Qwen categorization is highly reliable (≥90% agreement)")
        print("   → Ready to use for category-based routing")
    elif overall_accuracy >= 85:
        print("✅ GOOD: Qwen categorization is reliable (≥85% agreement)")
        print("   → Can use for routing, consider refining prompts for edge cases")
    elif overall_accuracy >= 80:
        print("⚠️  ACCEPTABLE: Qwen categorization is mostly reliable (≥80% agreement)")
        print("   → Usable but consider hybrid approach (Qwen + keyword fallback)")
    else:
        print("❌ CONCERNING: Qwen categorization shows significant disagreement (<80%)")
        print("   → Need to refine categorization prompt or use keyword baseline")

    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
