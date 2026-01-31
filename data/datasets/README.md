# MedQA Datasets

This directory contains the MedQA datasets used for model evaluation.

## Focused Dataset (Primary for Base Runs)

### medqa_focused_1030.json
- **Total questions**: 1,030
- **Questions per category**: 206
- **Categories**: 5 balanced categories
  - Clinical Findings
  - Diagnosis
  - Mechanism/Pathophysiology
  - Next Step/Workup
  - Treatment/Management
- **Source**: High-confidence questions from MedQA-USMLE training set
- **Selection criteria**: Questions with high inter-annotator agreement
- **Use case**: Primary dataset for temperature impact testing and base model evaluation

### medqa_focused_1030_summary.json
Summary statistics and metadata for the focused dataset.

## Full MedQA Dataset

### medqa_full_train.json
- **Questions**: ~10,000
- **Split**: Training set
- **Options**: 4 options per question
- **Source**: MedQA-USMLE full training data

### medqa_full_test.json
- **Questions**: ~1,273
- **Split**: Test set
- **Options**: 4 options per question
- **Source**: MedQA-USMLE official test set

### medqa_full_dev.json
- **Questions**: ~1,000
- **Split**: Development/validation set
- **Options**: 4 options per question
- **Source**: MedQA-USMLE development set

## Data Format

All datasets follow this JSON structure:

```json
{
  "question": "Clinical question text with patient presentation...",
  "options": {
    "A": "Option A text",
    "B": "Option B text",
    "C": "Option C text",
    "D": "Option D text"
  },
  "answer": "A",
  "validated_category": "Diagnosis"
}
```

## Citation

If you use these datasets, please cite the original MedQA paper:

```
@article{jin2021disease,
  title={What disease does this patient have? a large-scale open domain question answering dataset from medical exams},
  author={Jin, Di and Pan, Eileen and Oufattole, Nassim and Weng, Wei-Hung and Fang, Hanyi and Szolovits, Peter},
  journal={Applied Sciences},
  volume={11},
  number={14},
  pages={6421},
  year={2021}
}
```

## Notes

- All questions are from the US Medical Licensing Examination (USMLE) style
- Questions test medical knowledge across various specialties
- The focused dataset is balanced to ensure equal representation across task types
- Random seed 42 was used for dataset sampling and balancing
