"""
Compare base model results across all models and temperatures.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict


def load_summary(results_dir):
    """Load summary.json from a model's results directory."""
    summary_file = results_dir / "summary.json"
    if not summary_file.exists():
        return None

    with open(summary_file, 'r') as f:
        return json.load(f)


def main():
    if len(sys.argv) < 2:
        print("Usage: python compare_base_models.py <results_base_dir>")
        print("Example: python compare_base_models.py results/base_runs/")
        sys.exit(1)

    base_dir = Path(sys.argv[1])

    if not base_dir.exists():
        print(f"Error: Directory {base_dir} does not exist")
        sys.exit(1)

    # Find all model directories
    model_dirs = [d for d in base_dir.iterdir() if d.is_dir()]

    if not model_dirs:
        print(f"No model directories found in {base_dir}")
        sys.exit(1)

    # Load all summaries
    results = {}
    for model_dir in sorted(model_dirs):
        summary = load_summary(model_dir)
        if summary:
            results[model_dir.name] = summary

    if not results:
        print("No summary files found")
        sys.exit(1)

    # Print comparison table
    print("\n" + "="*100)
    print("BASE MODEL COMPARISON - TEMPERATURE IMPACT")
    print("="*100)
    print()

    # Header
    print(f"{'Model':<20} | {'Temp 0.0':<10} | {'Temp 0.3':<10} | {'Temp 0.7':<10} | {'Average':<10}")
    print("-" * 100)

    # Model results
    for model_name in sorted(results.keys()):
        summary = results[model_name]

        temp_results = {r['temperature']: r['mean_accuracy'] for r in summary['temperature_results']}

        temp_00 = temp_results.get(0.0, 0.0)
        temp_03 = temp_results.get(0.3, 0.0)
        temp_07 = temp_results.get(0.7, 0.0)
        avg = (temp_00 + temp_03 + temp_07) / 3 if temp_results else 0.0

        print(f"{model_name:<20} | {temp_00:>8.2f}% | {temp_03:>8.2f}% | {temp_07:>8.2f}% | {avg:>8.2f}%")

    print()

    # Per-temperature statistics
    print("\n" + "="*100)
    print("TEMPERATURE SENSITIVITY ANALYSIS")
    print("="*100)
    print()

    temperatures = [0.0, 0.3, 0.7]

    for temp in temperatures:
        print(f"\nTemperature {temp}:")
        print(f"{'Model':<20} | {'Mean Accuracy':<15} | {'Std Dev':<10} | {'Best Run':<10} | {'Worst Run':<10}")
        print("-" * 100)

        for model_name in sorted(results.keys()):
            summary = results[model_name]

            # Find this temperature's results
            temp_data = next((r for r in summary['temperature_results'] if r['temperature'] == temp), None)

            if temp_data:
                mean_acc = temp_data['mean_accuracy']
                std_dev = temp_data['std_dev']
                best = max(temp_data['run1_accuracy'], temp_data['run2_accuracy'], temp_data['run3_accuracy'])
                worst = min(temp_data['run1_accuracy'], temp_data['run2_accuracy'], temp_data['run3_accuracy'])

                print(f"{model_name:<20} | {mean_acc:>13.2f}% | {std_dev:>8.2f}% | {best:>8.2f}% | {worst:>8.2f}%")

    # Model size analysis
    print("\n" + "="*100)
    print("MODEL SIZE ANALYSIS")
    print("="*100)
    print()

    # Group by family
    families = defaultdict(list)
    for model_name, summary in results.items():
        if 'qwen25' in model_name.lower():
            families['Qwen2.5'].append((model_name, summary))
        elif 'olmo3' in model_name.lower() or 'olmo-3' in model_name.lower():
            families['Olmo-3'].append((model_name, summary))

    for family, models in sorted(families.items()):
        print(f"\n{family} Family:")
        print(f"{'Model':<20} | {'Size':<6} | {'Avg Accuracy':<15} | {'Temp Sensitivity':<20}")
        print("-" * 100)

        for model_name, summary in sorted(models):
            # Extract size from name
            if '7b' in model_name.lower():
                size = '7B'
            elif '14b' in model_name.lower():
                size = '14B'
            elif '32b' in model_name.lower():
                size = '32B'
            else:
                size = 'Unknown'

            temp_results = {r['temperature']: r['mean_accuracy'] for r in summary['temperature_results']}
            avg_acc = sum(temp_results.values()) / len(temp_results) if temp_results else 0.0

            # Temperature sensitivity = max - min across temperatures
            if temp_results:
                temp_sens = max(temp_results.values()) - min(temp_results.values())
            else:
                temp_sens = 0.0

            print(f"{model_name:<20} | {size:<6} | {avg_acc:>13.2f}% | {temp_sens:>17.2f}pp")

    print()
    print("="*100)
    print("SUMMARY")
    print("="*100)
    print()

    # Overall best
    best_model = None
    best_accuracy = 0.0

    for model_name, summary in results.items():
        temp_results = [r['mean_accuracy'] for r in summary['temperature_results']]
        avg = sum(temp_results) / len(temp_results) if temp_results else 0.0

        if avg > best_accuracy:
            best_accuracy = avg
            best_model = model_name

    print(f"Best Overall Model: {best_model} ({best_accuracy:.2f}% average)")

    # Most temperature-sensitive
    most_sensitive = None
    max_sensitivity = 0.0

    for model_name, summary in results.items():
        temp_results = [r['mean_accuracy'] for r in summary['temperature_results']]
        if temp_results:
            sensitivity = max(temp_results) - min(temp_results)
            if sensitivity > max_sensitivity:
                max_sensitivity = sensitivity
                most_sensitive = model_name

    print(f"Most Temperature-Sensitive: {most_sensitive} ({max_sensitivity:.2f}pp difference)")

    # Least temperature-sensitive
    least_sensitive = None
    min_sensitivity = float('inf')

    for model_name, summary in results.items():
        temp_results = [r['mean_accuracy'] for r in summary['temperature_results']]
        if temp_results:
            sensitivity = max(temp_results) - min(temp_results)
            if sensitivity < min_sensitivity:
                min_sensitivity = sensitivity
                least_sensitive = model_name

    print(f"Least Temperature-Sensitive: {least_sensitive} ({min_sensitivity:.2f}pp difference)")

    print()


if __name__ == "__main__":
    main()
