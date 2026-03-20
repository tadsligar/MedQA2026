# MedQA Full Dataset — Base Model Evaluation Results

## Overview

Evaluation of 5 base language models on the full MedQA USMLE dataset across 3 temperatures, with 3 independent runs per condition to assess reproducibility.

- **Dataset**: `data/datasets/medqa_full_combined.json`
- **Questions**: 12,723 (train + dev + test splits combined)
- **Options per question**: 5 (A–E); random baseline = 20%
- **Prompt style**: Simple zero-shot (no chain-of-thought, no few-shot)
- **Runs per condition**: 3
- **Temperatures tested**: 0.0, 0.3, 0.7
- **Infrastructure**: SLURM cluster, vLLM serving, A100 80GB GPUs

---

## Models Evaluated

| Model | HuggingFace ID | Parameters |
|---|---|---|
| OLMo-3 7B | `allenai/Olmo-3-1025-7B` | 7B |
| OLMo-3 32B | `allenai/Olmo-3-1125-32B` | 32B |
| Qwen2.5 7B | `Qwen/Qwen2.5-7B` | 7B |
| Qwen2.5 14B | `Qwen/Qwen2.5-14B` | 14B |
| Qwen2.5 32B | `Qwen/Qwen2.5-32B` | 32B |

---

## Results

### Accuracy by Model, Temperature, and Run

| Model | Temp | Run 1 | Run 2 | Run 3 | **Mean** | StdDev |
|---|---|---|---|---|---|---|
| OLMo-3 7B | 0.0 | 39.86% | 39.86% | 39.86% | **39.86%** | 0.000% |
| OLMo-3 7B | 0.3 | 38.96% | 38.91% | 38.51% | **38.79%** | 0.203% |
| OLMo-3 7B | 0.7 | 34.19% | 34.16% | 34.82% | **34.39%** | 0.304% |
| OLMo-3 32B | 0.0 | 52.13% | 52.12% | 52.12% | **52.12%** | 0.004% |
| OLMo-3 32B | 0.3 | 50.63% | 50.58% | 50.71% | **50.64%** | 0.055% |
| OLMo-3 32B | 0.7 | 44.92% | 44.49% | 44.38% | **44.60%** | 0.232% |
| Qwen2.5 7B | 0.0 | 53.72% | 53.72% | 53.66% | **53.70%** | 0.030% |
| Qwen2.5 7B | 0.3 | 51.88% | 51.87% | 52.18% | **51.98%** | 0.145% |
| Qwen2.5 7B | 0.7 | 45.93% | 46.76% | 46.51% | **46.40%** | 0.345% |
| Qwen2.5 14B | 0.0 | 60.95% | 60.78% | 60.90% | **60.88%** | 0.072% |
| Qwen2.5 14B | 0.3 | 59.32% | 59.66% | 59.63% | **59.54%** | 0.154% |
| Qwen2.5 14B | 0.7 | 53.49% | 53.60% | 53.86% | **53.65%** | 0.156% |
| Qwen2.5 32B | 0.0 | 66.99% | 67.04% | 66.99% | **67.01%** | 0.023% |
| Qwen2.5 32B | 0.3 | 65.46% | 65.48% | 65.94% | **65.63%** | 0.219% |
| Qwen2.5 32B | 0.7 | 59.81% | 60.47% | 59.64% | **59.97%** | 0.359% |

### Best Accuracy per Model (t=0.0, mean of 3 runs)

| Rank | Model | Accuracy | vs. Random Baseline |
|---|---|---|---|
| 1 | Qwen2.5 32B | **67.01%** | +47.0 pp |
| 2 | Qwen2.5 14B | **60.88%** | +40.9 pp |
| 3 | Qwen2.5 7B | **53.70%** | +33.7 pp |
| 4 | OLMo-3 32B | **52.12%** | +32.1 pp |
| 5 | OLMo-3 7B | **39.86%** | +19.9 pp |

*Random baseline = 20.0% (5-option questions)*

---

## Key Findings

### 1. Exceptional Reproducibility
Standard deviations at t=0.0 are near-zero for all models, with OLMo-3 7B producing bit-for-bit identical results across all 3 runs. Even at higher temperatures, std dev stays below 0.4%. This confirms that 3 runs is more than sufficient for reliable estimates on a dataset of this size.

### 2. Temperature Consistently Degrades Accuracy
Higher temperature monotonically reduces accuracy for every model:

| Model | t=0.0 → t=0.7 drop |
|---|---|
| OLMo-3 7B | −5.5 pp |
| OLMo-3 32B | −7.5 pp |
| Qwen2.5 7B | −7.3 pp |
| Qwen2.5 14B | −7.2 pp |
| Qwen2.5 32B | −7.0 pp |

The degradation is remarkably consistent across model families (~7 pp for most models), suggesting this is a general property of temperature on medical QA rather than model-specific.

### 3. Qwen2.5 Outperforms OLMo-3 at Equivalent Scale
At the 7B scale, Qwen2.5 7B (53.7%) substantially outperforms OLMo-3 7B (39.9%) — a 13.8 pp gap. Notably, Qwen2.5 7B (53.7%) even edges out OLMo-3 32B (52.1%), meaning the smaller Qwen model matches or beats the larger OLMo model on this benchmark.

### 4. Scaling Yields Consistent Gains for Qwen2.5
Within the Qwen2.5 family, each size step provides meaningful improvement:
- 7B → 14B: +7.2 pp (60.88% vs 53.70%)
- 14B → 32B: +6.1 pp (67.01% vs 60.88%)

### 5. Context: USMLE Passing and Human Performance
For reference, the USMLE Step 1 passing score is approximately 60% correct. By this bar:
- Qwen2.5 32B (67.0%) and Qwen2.5 14B (60.9%) exceed the passing threshold at t=0.0
- OLMo-3 32B (52.1%), Qwen2.5 7B (53.7%), and OLMo-3 7B (39.9%) fall below it

---

## Dataset Notes

The full MedQA dataset used here is the **5-option USMLE version** (Jin et al., 2021). All 12,723 questions have exactly 5 answer choices (A–E). This is distinct from the 4-option version also released with the same paper, where one distractor was removed per question. The focused 1,030-question dataset used in earlier experiments (`medqa_focused_1030.json`) is derived from this dataset with one distractor removed per question (4-option, A–D).

---

## Experimental Configuration

| Parameter | Value |
|---|---|
| vLLM version | 0.14.1 |
| Tensor parallel size | 2 (all models) |
| GPU memory utilization | 0.7 |
| Max model length | 4096 tokens |
| Max sequences | 128 |
| dtype | bfloat16 |
| GPU | NVIDIA A100-SXM4-80GB |
| Checkpoint interval | Every 10 questions |

---

## Citation

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
