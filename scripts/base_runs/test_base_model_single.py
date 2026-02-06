"""
Base Model Single Run Testing
Tests a single temperature/run combination for a base model on MedQA.
Used by the orchestrated job system for parallel execution.
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
    """Extract answer letter from base model response."""
    valid_set = set(valid_letters)

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

    # Fallback
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
    """Call vLLM completions endpoint."""
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

        text = data['choices'][0]['text']
        tokens = data['usage'].get('completion_tokens', 0)

        return text, tokens

    except requests.exceptions.Timeout:
        print(f"  WARNING: Request timed out after {timeout}s, using fallback")
        return "A", 0
    except Exception as e:
        print(f"  ERROR: {e}")
        return "A", 0


def run_single_experiment(questions, temperature, run_number, output_dir, model_name, vllm_base_url):
    """Run a single temperature/run experiment."""

    print(f"\n{'='*80}")
    print(f"TEMPERATURE {temperature} - RUN {run_number}")
    print(f"Model: {model_name}")
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

        # Support both formats: with/without explicit 'id' field
        question_id = item.get('id', item.get('question_id', idx))
        question = item['question']
        options_raw = item['options']
        correct_answer_text = item['answer']
        validated_category = item.get('validated_category', categorize_question(question))

        # Handle both list and dict formats for options
        if isinstance(options_raw, list):
            # Format: ['A. Text', 'B. Text', ...]
            options_dict = {}
            for option in options_raw:
                letter = option[0]  # First character is the letter
                text = option[3:].strip()  # Skip 'A. ' prefix
                options_dict[letter] = text
        else:
            # Already a dict
            options_dict = options_raw

        # Convert answer text to letter
        correct_answer = None
        for letter, text in options_dict.items():
            if text == correct_answer_text:
                correct_answer = letter
                break

        if not correct_answer:
            correct_answer = 'A'

        # Format options
        options_text = "\n".join([f"{letter}. {text}" for letter, text in sorted(options_dict.items())])

        # Simple prompt for base models
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

        predicted = extract_answer(response_text, ['A', 'B', 'C', 'D', 'E'])
        is_correct = (predicted == correct_answer)

        total_tokens += tokens_used
        total_time += latency

        results.append({
            'question_id': question_id,
            'array_index': idx,
            'category': validated_category,
            'correct': correct_answer,
            'predicted': predicted,
            'is_correct': is_correct,
            'tokens': tokens_used,
            'latency': latency,
            'response': response_text[:200]
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

    # Save final checkpoint (complete state)
    save_checkpoint(output_dir, temperature, run_number, results, len(questions))
    print(f"  Final checkpoint saved: {len(results)} questions")

    # Save final results
    results_file = output_dir / f"temp{temperature}_run{run_number}_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"  Results saved: {results_file}")

    return overall_accuracy


def main():
    parser = argparse.ArgumentParser(description='Test base model - single run')
    parser.add_argument('--model-name', required=True, help='Model name')
    parser.add_argument('--output-dir', required=True, help='Output directory')
    parser.add_argument('--dataset', required=True, help='Path to dataset')
    parser.add_argument('--vllm-url', required=True, help='vLLM base URL')
    parser.add_argument('--temperature', type=float, required=True, help='Temperature')
    parser.add_argument('--run-number', type=int, required=True, help='Run number')

    args = parser.parse_args()

    print("="*80)
    print("BASE MODEL SINGLE RUN TEST")
    print("="*80)
    print()
    print(f"Model: {args.model_name}")
    print(f"Temperature: {args.temperature}")
    print(f"Run: {args.run_number}")
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

    # Run experiment
    accuracy = run_single_experiment(
        questions,
        args.temperature,
        args.run_number,
        output_dir,
        args.model_name,
        args.vllm_url
    )

    print(f"\n{'='*80}")
    print(f"EXPERIMENT COMPLETE - Accuracy: {accuracy:.2f}%")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
