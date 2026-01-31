# MedQA2026: Base Model Evaluation and Neurosymbolic Reasoning

A comprehensive evaluation framework for testing base language models on medical question answering, with integrated neurosymbolic reasoning approaches.

## Project Overview

This repository contains:
1. **Base Model Evaluation**: Systematic temperature impact testing of 5 base (non-instruct) models
2. **Curated Datasets**: Focused and full MedQA-USMLE datasets
3. **Neurosymbolic Approaches**: Two UMLS-grounded reasoning methods
4. **Reproducible Infrastructure**: vLLM-based testing on HPC cluster

## Base Models Under Test

All models are **base** (pretrained) versions, not instruction-tuned:

| Model | Size | Family | HuggingFace ID |
|-------|------|--------|----------------|
| Qwen2.5-7B | 7B | Qwen 2.5 | `Qwen/Qwen2.5-7B` |
| Qwen2.5-14B | 14B | Qwen 2.5 | `Qwen/Qwen2.5-14B` |
| Qwen2.5-32B | 32B | Qwen 2.5 | `Qwen/Qwen2.5-32B` |
| Olmo-3-1025-7B | 7B | Olmo 3 | `allenai/Olmo-3-1025-7B` |
| Olmo-3-1125-32B | 32B | Olmo 3 | `allenai/Olmo-3-1125-32B` |

**Why base models?**
- Eliminates instruction-tuning confounds
- Tests pure language modeling capabilities
- Provides baseline for comparing fine-tuning approaches

## Testing Protocol

### Temperature Impact Study
- **Temperatures**: 0.0, 0.3, 0.7
- **Runs per temperature**: 3
- **Total experiments per model**: 9
- **Dataset**: Focused 1,030 questions (206 per category)
- **Prompt style**: Simple, no "you're a medical expert" preamble

### Categories Tested
1. Clinical Findings
2. Diagnosis
3. Mechanism/Pathophysiology
4. Next Step/Workup
5. Treatment/Management

### Infrastructure
- **Inference**: vLLM on dual A100 GPUs
- **Cluster**: Auburn University HPC
- **Checkpointing**: Every 10 questions
- **Outputs**: Labeled as "base_runs"

## Project Structure

```
MedQA2026/
├── configs/                    # Model configurations
│   ├── qwen25_7b_base.yaml
│   ├── qwen25_14b_base.yaml
│   ├── qwen25_32b_base.yaml
│   ├── olmo3_7b_base.yaml
│   └── olmo3_32b_base.yaml
│
├── data/
│   ├── datasets/               # MedQA datasets
│   │   ├── medqa_focused_1030.json          # Primary: 1,030 balanced questions
│   │   ├── medqa_focused_1030_summary.json
│   │   ├── medqa_full_train.json            # Full training set (~10k)
│   │   ├── medqa_full_test.json             # Official test set (~1.3k)
│   │   └── medqa_full_dev.json              # Dev set (~1k)
│   └── umls/                   # UMLS data (not in git)
│
├── scripts/
│   ├── base_runs/              # Test scripts for base models
│   └── utils/                  # Helper utilities
│
├── slurm/                      # SLURM batch scripts
│
├── results/
│   ├── base_runs/              # Base model evaluation results
│   └── neurosymbolic/          # Neurosymbolic approach results
│
├── neurosymbolic/
│   ├── umls_verifier/          # Approach 1: Neural + Symbolic verification
│   └── chain_of_verification/  # Approach 2: Iterative CoVe pipeline
│
├── logs/                       # Job logs
└── docs/                       # Additional documentation
```

## Quick Start

### 1. Environment Setup

```bash
# Activate environment
conda activate medqa

# Set HuggingFace cache
export HF_HOME=/aiau010_scratch/tzs0128/hf_cache
export TRANSFORMERS_CACHE=/aiau010_scratch/tzs0128/hf_cache
```

### 2. Run Base Model Test

```bash
# Submit job for a specific model
sbatch slurm/run_qwen25_7b_base.sbatch

# Monitor progress
squeue -u $USER
tail -f logs/qwen25_7b_base_*.out
```

### 3. Check Results

```bash
# View results
ls -lh results/base_runs/qwen25_7b/

# Summary statistics
cat results/base_runs/qwen25_7b/summary.json
```

## Datasets

### Focused Dataset (Primary)
- **File**: `data/datasets/medqa_focused_1030.json`
- **Questions**: 1,030
- **Distribution**: 206 per category (5 categories)
- **Selection**: High inter-annotator agreement
- **Purpose**: Temperature impact testing, base model evaluation

### Full Dataset
- **Train**: ~10,000 questions
- **Test**: ~1,273 questions (official MedQA test set)
- **Dev**: ~1,000 questions
- **Purpose**: Comprehensive evaluation, neurosymbolic testing

See `data/datasets/README.md` for details.

## Neurosymbolic Approaches

### 1. Hybrid UMLS Verifier ⭐ **Updated January 2026**
**Major Evolution**: Now a hybrid UMLS + LLM system (evolved from pure symbolic approach)

Combines UMLS medical knowledge with LLM reasoning through 3-layer architecture:

**Performance**:
| Approach | Accuracy | Notes |
|----------|----------|-------|
| Pure UMLS | 30% | Concept mismatch problem |
| **Hybrid (UMLS + LLM)** | **60-70%** (expected) | 2.0-2.3x improvement |

**3-Layer Architecture**:
1. **UMLS Grounding**: Extract 20-30 clinical concepts, 695k relationships
2. **Prompt Enrichment**: Category-specific templates with clinical context
3. **LLM Reasoning**: Local (Qwen 2.5) or API (Claude/GPT-4)

**Key Innovation**: Solves "concept mismatch problem" where pure symbolic matching fails due to terminology gaps (e.g., "chest pain" ≠ "chest discomfort" in UMLS despite same meaning).

**Components**:
- Category-specific scorers (Diagnosis, Treatment)
- Hybrid scorers combining UMLS + LLM
- Advanced entity extraction with semantic filtering
- 9 comprehensive documentation files (~35k words)

**Documentation**: `neurosymbolic/umls_verifier/DOCUMENTATION_INDEX.md`

See `neurosymbolic/umls_verifier/README.md` for full details

### 2. Chain of Verification (CoVe)
Iterative propose-ground-verify-revise pipeline.

**Performance**: 29% accuracy (verify-only mode, +38% over heuristic baseline)

**Components**:
- Structured analysis generation
- UMLS grounding
- 5 symbolic verifiers
- Iterative revision

**Key Finding**: Verification helps (+38%) but revision doesn't for heuristic proposers

See `neurosymbolic/chain_of_verification/README.md`

### Comparison
- **Hybrid UMLS**: Best for high accuracy (60-70%), fast inference
- **CoVe**: Best for explainable structured reasoning, violation detection

See `neurosymbolic/README.md` for detailed comparison

## Evaluation Metrics

### Per-Run Metrics
- Accuracy (fraction correct)
- Per-category accuracy
- Average latency per question
- Token statistics

### Aggregate Metrics
- Mean accuracy across 3 runs
- Standard deviation
- Temperature sensitivity
- Category-wise performance

## Prompt Design

### Base Model Prompt (Simple)
```
Question: [Patient presentation and clinical question]

Options:
A. [Option A]
B. [Option B]
C. [Option C]
D. [Option D]

Answer:
```

**Key principles**:
- No role-playing ("you're a medical expert")
- No chain-of-thought prompting
- Direct question → answer format
- Minimal tokens for fair comparison

## Results Comparison

### Expected Baselines
Based on literature and preliminary tests:
- Base models: 20-40% accuracy (no instruction tuning)
- Instruct models: 60-75% accuracy
- Neurosymbolic augmentation: +5-15pp improvement

### Analysis Goals
1. Quantify base model medical knowledge
2. Measure temperature sensitivity
3. Identify category-specific strengths/weaknesses
4. Compare model families (Qwen vs Olmo)
5. Evaluate neurosymbolic integration potential

## Hardware Requirements

### Minimum (per model)
- **GPUs**: 2× A100 80GB
- **RAM**: 200GB
- **Storage**: 50GB for model + results
- **Time**: ~6-8 hours per model (depends on verbosity)

### Current Setup
- **Cluster**: Auburn AIAU HPC
- **Node**: aiau001 (8× A100 GPUs)
- **vLLM**: Tensor parallelism across 2 GPUs

## Reproducibility

All experiments are designed for reproducibility:
- ✅ Fixed random seeds
- ✅ Checkpointing every 10 questions
- ✅ Full prompt/response logging
- ✅ Configuration snapshots saved with results
- ✅ Git version control

## Citation

### MedQA Dataset
```bibtex
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

### UMLS
```
Bodenreider O. The Unified Medical Language System (UMLS): integrating biomedical terminology.
Nucleic Acids Research. 2004 Jan 1;32(Database issue):D267-70.
```

## License

Research and educational use only. Datasets and UMLS subject to their respective licenses.

## Contact

- **Author**: Tad Sligar
- **Email**: tadsligar@hotmail.com
- **Institution**: Auburn University

## Acknowledgments

- MedQA dataset creators
- HuggingFace model providers (Qwen, Allen AI)
- Auburn University HPC support
- UMLS/NLM for medical terminology resources

## Status

🟢 **Active Development** - Base model testing in progress (Jan 2026)

Last updated: 2026-01-31
