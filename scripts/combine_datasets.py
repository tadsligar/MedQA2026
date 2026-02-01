#!/usr/bin/env python3
"""
Combine dev, test, and train datasets into a single combined dataset.
"""

import json
from pathlib import Path

# Paths
project_root = Path(__file__).parent.parent
data_dir = project_root / "data" / "datasets"

dev_file = data_dir / "medqa_full_dev.json"
test_file = data_dir / "medqa_full_test.json"
train_file = data_dir / "medqa_full_train.json"
output_file = data_dir / "medqa_full_combined.json"

print("Combining MedQA datasets...")
print()

# Load all datasets
print(f"Loading {dev_file.name}...")
with open(dev_file, 'r', encoding='utf-8') as f:
    dev_data = json.load(f)
print(f"  ✓ {len(dev_data):,} questions")

print(f"Loading {test_file.name}...")
with open(test_file, 'r', encoding='utf-8') as f:
    test_data = json.load(f)
print(f"  ✓ {len(test_data):,} questions")

print(f"Loading {train_file.name}...")
with open(train_file, 'r', encoding='utf-8') as f:
    train_data = json.load(f)
print(f"  ✓ {len(train_data):,} questions")

print()

# Combine all data
combined_data = []

# Add dev data with source tag
for item in dev_data:
    item['source_split'] = 'dev'
    combined_data.append(item)

# Add test data with source tag
for item in test_data:
    item['source_split'] = 'test'
    combined_data.append(item)

# Add train data with source tag
for item in train_data:
    item['source_split'] = 'train'
    combined_data.append(item)

print(f"Combined dataset statistics:")
print(f"  Dev:   {len(dev_data):,} questions")
print(f"  Test:  {len(test_data):,} questions")
print(f"  Train: {len(train_data):,} questions")
print(f"  ─────────────────────────")
print(f"  Total: {len(combined_data):,} questions")
print()

# Save combined dataset
print(f"Saving to {output_file.name}...")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(combined_data, f, indent=2, ensure_ascii=False)

file_size_mb = output_file.stat().st_size / (1024 * 1024)
print(f"  ✓ Saved {len(combined_data):,} questions ({file_size_mb:.1f} MB)")
print()
print("✓ Dataset combination complete!")
