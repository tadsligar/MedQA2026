"""
Base Model Temperature Impact Testing
Tests base (non-instruct) models on MedQA with simple prompts.
No role-playing, no chain-of-thought - pure base model evaluation.
"""

import json
import sys
import time
import re
import argparse
from pathlib import Path
from collections import defaultdict
import requests

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def categorize_question(question_text):
    """Categorize question based on text patterns."""
    q = question_text.lower()

    if 'most likely diagnosis' in q or 'most likely cause of' in q:
        return 'Diagnosis'
    elif 'next step' in q or 'next best' in q or 'initial step' in q:
        return 'Next Step/Workup'
    elif 'treatment' in q or 'management' in q or 'which drug' in q:
        return 'Treatment/Management'
    elif 'mechanism' in q or 'action' in q or 'pathway' in q:
        return 'Mechanism/Pathophysiology'
    elif 'most likely to show' in q or 'expected finding' in q:
        return 'Clinical Findings'
    else:
        return 'Other/Mixed'


def extract_answer(response_text, valid_letters):
    """
    Extract answer letter from base model response.
    Base models may not follow instructions perfectly, so we try multiple strategies.
    """
    valid_set = set(valid_letters)

    # Remove leading/trailing whitespace
    response_text = response_text.strip()

    # Strategy 1: Check if response starts with a valid letter
    if response_text and response_text[0].upper() in valid_set:
        return response_text[0].upper()

    # Strategy 2: Look for "ANSWER: X" or "Answer: X" pattern
    for pattern in [r'ANSWER[:\s]+([A-D])', r'Answer[:\s]+([A-D])', r'answer[:\s]+([A-D])']:
        match = re.search(pattern, response_text, re.IGNORECASE)
        if match and match.group(1).upper() in valid_set:
            return match.group(1).upper()

    # Strategy 3: Look for standalone letter in first 50 chars
    first_part = response_text[:50]
    for char in first_part:
        if char.upper() in valid_set:
            return char.upper()

    # Strategy 4: Look anywhere in response
    for char in response_text:
        if char.upper() in valid_set:
            return char.upper()

    # Fallback: return first valid letter if exists, else 'A'
    return 'A'


def load_checkpoint(output_dir, temperature, run_number):
    """Load checkpoint if it exists."""
    checkpoint_file = output_dir / f"temp{temperature}_run{run_number}_checkpoint.json"

    if checkpoint_file.exists():
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)
        return checkpoint['results'], checkpoint['next_index']

    return [], 0


def save_checkpoint(output_dir, temperature, run_number, results, next_index):
    """Save checkpoint."""
    checkpoint_file = output_dir / f"temp{temperature}_run{run_number}_checkpoint.json"

    checkpoint = {
        'temperature': temperature,
        'run_number': run_number,
        'results': results,
        'next_index': next_index,
        'timestamp': time.time()
    }

    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump(checkpoint, f, indent=2, ensure_ascii=False)


def call_vllm_completions(prompt, temperature, base_url, max_tokens=800, timeout=120):
    """
    Call vLLM completions endpoint (for base models).
    Base models use /v1/completions, not /v1/chat/completions.
    """
    url = f"{base_url}/v1/completions"

    payload = {
        "prompt": prompt,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": 1.0,
        "n": 1
    }

    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        # Extract text and token count
        text = data['choices'][0]['text']
        tokens = data['usage'].get('completion_tokens', 0)

        return text, tokens

    except requests.exceptions.Timeout:
        print(f"  WARNING: Request timed out after {timeout}s, using fallback")
        return "A", 0
    except Exception as e:
        print(f"  ERROR: {e}")
        return "A", 0


def run_temperature_test(questions, temperature, run_number, output_dir, model_name, vllm_base_url):
    """Run test at specified temperature."""

    print(f"\n{'='*80}")
    print(f"TEMPERATURE {temperature} - RUN {run_number}")
    print(f"Model: {model_name} (BASE MODEL - NO INSTRUCTION TUNING)")
    print(f"{'='*80}\n")

    # Load checkpoint
    results, start_idx = load_checkpoint(output_dir, temperature, run_number)

    if start_idx > 0:
        print(f"Resuming from question {start_idx}/{len(questions)}")
        total_tokens = sum(r['tokens'] for r in results)
        total_time = sum(r['latency'] for r in results)
    else:
        print(f"Starting fresh run...")
        total_tokens = 0
        total_time = 0

    for idx in range(start_idx, len(questions)):
        item = questions[idx]
        question = item['question']
        options_dict = item['options']
        correct_answer_text = item['answer']
        validated_category = item.get('validated_category', categorize_question(question))

        # Convert answer text to letter
        correct_answer = None
        for letter, text in options_dict.items():
            if text == correct_answer_text:
                correct_answer = letter
                break

        if not correct_answer:
            correct_answer = 'A'  # Fallback

        # Format options
        options_text = "\n".join([f"{letter}. {text}" for letter, text in sorted(options_dict.items())])

        # SIMPLE PROMPT - No role-playing, no instructions, just the question
        # This is appropriate for base models
        prompt = f"""Question: {question}

Options:
{options_text}

Answer:"""

        start_time = time.time()
        response_text, tokens_used = call_vllm_completions(
            prompt,
            temperature,
            vllm_base_url
        )
        latency = time.time() - start_time

        predicted = extract_answer(response_text, ['A', 'B', 'C', 'D'])
        is_correct = (predicted == correct_answer)

        total_tokens += tokens_used
        total_time += latency

        results.append({
            'question_id': idx,
            'category': validated_category,
            'correct': correct_answer,
            'predicted': predicted,
            'is_correct': is_correct,
            'tokens': tokens_used,
            'latency': latency,
            'response': response_text[:200]  # Save first 200 chars for debugging
        })

        # Save checkpoint every 10 questions
        if (idx + 1) % 10 == 0:
            save_checkpoint(output_dir, temperature, run_number, results, idx + 1)
            accuracy = sum(1 for r in results if r['is_correct']) / len(results) * 100
            avg_time = total_time / len(results)
            remaining = len(questions) - (idx + 1)
            eta_minutes = (remaining * avg_time) / 60
            print(f"  [{idx + 1}/{len(questions)}] Accuracy: {accuracy:.2f}% | Avg: {avg_time:.1f}s/q | ETA: {eta_minutes:.1f} min")

    overall_accuracy = sum(1 for r in results if r['is_correct']) / len(results) * 100

    print(f"\nTemp {temperature} Run {run_number} Complete:")
    print(f"  Overall Accuracy: {overall_accuracy:.2f}%")
    print(f"  Total Tokens: {total_tokens:,}")
    print(f"  Total Time: {total_time/60:.1f} minutes")
    print(f"  Avg Time: {total_time/len(results):.2f} seconds/question")

    return results, overall_accuracy, total_tokens, total_time


def main():
    parser = argparse.ArgumentParser(description='Test base model on MedQA')
    parser.add_argument('--model-name', required=True, help='Model name (e.g., Qwen/Qwen2.5-7B)')
    parser.add_argument('--output-dir', required=True, help='Output directory for results')
    parser.add_argument('--dataset', default='data/datasets/medqa_focused_1030.json',
                       help='Path to dataset')
    parser.add_argument('--vllm-url', default='http://localhost:8000',
                       help='vLLM base URL')

    args = parser.parse_args()

    print("="*80)
    print("BASE MODEL TEMPERATURE IMPACT TEST")
    print("="*80)
    print()
    print(f"Model: {args.model_name}")
    print(f"Dataset: {args.dataset}")
    print(f"Output: {args.output_dir}")
    print()

    # Setup output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load dataset
    dataset_path = project_root / args.dataset
    print(f"Loading dataset: {dataset_path}")
    with open(dataset_path, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    print(f"Total questions: {len(questions)}")

    # Count per category
    category_counts = defaultdict(int)
    for q in questions:
        category = q.get('validated_category', categorize_question(q['question']))
        category_counts[category] += 1

    print("\nCategory distribution:")
    for cat in sorted(category_counts.keys()):
        print(f"  {cat:<30} {category_counts[cat]:>4} questions")

    # Test temperatures
    temperatures = [0.0, 0.3, 0.7]
    n_runs = 3

    print("\n" + "="*80)
    print(f"BASE RUN: {len(temperatures)} TEMPERATURES × {n_runs} RUNS = {len(temperatures) * n_runs} TOTAL EXPERIMENTS")
    print("Simple prompts (no instruction tuning, no role-playing)")
    print("="*80)

    all_results = {}

    for temp in temperatures:
        all_results[temp] = []

        for run_num in range(1, n_runs + 1):
            results, accuracy, tokens, time_sec = run_temperature_test(
                questions,
                temp,
                run_num,
                output_dir,
                args.model_name,
                args.vllm_url
            )

            # Save final results
            results_file = output_dir / f"temp{temp}_run{run_num}_results.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            all_results[temp].append({
                'run_number': run_num,
                'accuracy': accuracy,
                'tokens': tokens,
                'time': time_sec,
            })

    # Calculate statistics
    print("\n" + "="*80)
    print("TEMPERATURE COMPARISON")
    print("="*80)
    print()

    print(f"{'Temperature':<12} | {'Run 1':<8} | {'Run 2':<8} | {'Run 3':<8} | {'Mean':<8} | {'Std Dev':<8}")
    print("-" * 80)

    summary_data = []

    for temp in temperatures:
        accuracies = [run['accuracy'] for run in all_results[temp]]
        mean_acc = sum(accuracies) / len(accuracies)

        # Calculate std dev
        if len(accuracies) > 1:
            variance = sum((x - mean_acc) ** 2 for x in accuracies) / (len(accuracies) - 1)
            std_dev = variance ** 0.5
        else:
            std_dev = 0

        print(f"temp={temp:<6} | {accuracies[0]:>7.2f}% | {accuracies[1]:>7.2f}% | {accuracies[2]:>7.2f}% | {mean_acc:>7.2f}% | {std_dev:>7.2f}%")

        summary_data.append({
            'temperature': temp,
            'run1_accuracy': accuracies[0],
            'run2_accuracy': accuracies[1],
            'run3_accuracy': accuracies[2],
            'mean_accuracy': mean_acc,
            'std_dev': std_dev
        })

    # Save summary
    summary = {
        'dataset': args.dataset,
        'total_questions': len(questions),
        'model': args.model_name,
        'model_type': 'base',
        'run_type': 'base_run',
        'prompt_style': 'simple',
        'temperatures': temperatures,
        'n_runs_per_temperature': n_runs,
        'temperature_results': summary_data
    }

    summary_file = output_dir / "summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    print(f"\n\nSummary saved to: {summary_file}")

    print("\n" + "="*80)
    print("BASE MODEL TEMPERATURE IMPACT TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
