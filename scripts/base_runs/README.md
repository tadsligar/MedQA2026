# Base Model Testing Scripts

Scripts for testing base (non-instruct) language models on MedQA with temperature impact analysis.

## Overview

These scripts test 5 base models with simple prompts (no instruction tuning, no role-playing):
- Qwen2.5-7B
- Qwen2.5-14B
- Qwen2.5-32B
- Olmo-3-1025-7B (7B)
- Olmo-3-1125-32B (32B)

## Testing Protocol

**Temperatures**: 0.0, 0.3, 0.7
**Runs per temperature**: 3
**Total experiments per model**: 9
**Dataset**: Focused 1,030 questions (206 per category)
**Prompt style**: Simple - just question + options + "Answer:"

## Simple Prompt Format

```
Question: [Patient presentation and clinical question]

Options:
A. [Option A]
B. [Option B]
C. [Option C]
D. [Option D]

Answer:
```

**No "you're a medical expert"** - This is a pure base model evaluation.

## Main Script

### `test_base_model.py`

Generic test script that works for all base models.

**Usage**:
```bash
python test_base_model.py \
    --model-name "Qwen/Qwen2.5-7B" \
    --output-dir "results/base_runs/qwen25_7b" \
    --dataset "data/datasets/medqa_focused_1030.json" \
    --vllm-url "http://localhost:8000"
```

**Features**:
- Simple prompt format (appropriate for base models)
- Uses vLLM completions endpoint (`/v1/completions`)
- Checkpoint support (saves every 10 questions)
- Temperature impact testing (0.0, 0.3, 0.7)
- Full result logging with metadata

**Arguments**:
- `--model-name`: HuggingFace model ID
- `--output-dir`: Where to save results
- `--dataset`: Path to dataset JSON
- `--vllm-url`: vLLM server URL (default: http://localhost:8000)

## Running Tests

### Option 1: Submit SLURM Jobs (Recommended)

```bash
# Submit job for a specific model
sbatch slurm/run_qwen25_7b_base.sbatch
sbatch slurm/run_qwen25_14b_base.sbatch
sbatch slurm/run_qwen25_32b_base.sbatch
sbatch slurm/run_olmo3_7b_base.sbatch
sbatch slurm/run_olmo3_32b_base.sbatch

# Check status
squeue -u $USER

# Monitor progress
tail -f logs/qwen25_7b_base_*.out
```

### Option 2: Manual Execution

1. **Start vLLM server**:
```bash
vllm serve Qwen/Qwen2.5-7B \
    --port 8000 \
    --tensor-parallel-size 2 \
    --gpu-memory-utilization 0.9 \
    --dtype bfloat16 \
    --max-model-len 4096
```

2. **Run test** (in another terminal):
```bash
python scripts/base_runs/test_base_model.py \
    --model-name "Qwen/Qwen2.5-7B" \
    --output-dir "results/base_runs/qwen25_7b"
```

## Output Structure

```
results/base_runs/qwen25_7b/
├── temp0.0_run1_results.json       # Detailed results
├── temp0.0_run1_checkpoint.json    # Checkpoint (for resume)
├── temp0.0_run2_results.json
├── temp0.0_run2_checkpoint.json
├── temp0.0_run3_results.json
├── temp0.0_run3_checkpoint.json
├── temp0.3_run1_results.json
├── ... (9 runs total)
└── summary.json                     # Aggregate statistics
```

### Results Format

**Individual Results** (`temp0.0_run1_results.json`):
```json
[
  {
    "question_id": 0,
    "category": "Diagnosis",
    "correct": "A",
    "predicted": "A",
    "is_correct": true,
    "tokens": 5,
    "latency": 0.123,
    "response": "A"
  },
  ...
]
```

**Summary** (`summary.json`):
```json
{
  "model": "Qwen/Qwen2.5-7B",
  "model_type": "base",
  "run_type": "base_run",
  "prompt_style": "simple",
  "total_questions": 1030,
  "temperature_results": [
    {
      "temperature": 0.0,
      "run1_accuracy": 35.2,
      "run2_accuracy": 34.8,
      "run3_accuracy": 35.5,
      "mean_accuracy": 35.17,
      "std_dev": 0.35
    },
    ...
  ]
}
```

## Checkpoint & Resume

The test script automatically saves checkpoints every 10 questions. If interrupted:

```bash
# Simply resubmit the same job
sbatch slurm/run_qwen25_7b_base.sbatch

# The script will detect existing checkpoints and resume
```

Checkpoint files are saved as `temp{temperature}_run{run_number}_checkpoint.json`

## Expected Performance

Base models (no instruction tuning) typically achieve:
- **Random baseline**: 25%
- **Expected base model**: 20-40% (depends on model size and pretraining)
- **For comparison, instruct models**: 60-75%

Lower accuracy is expected for base models - this is the baseline we're establishing!

## Computational Requirements

**Per model**:
- GPUs: 2× A100 80GB
- RAM: 200GB
- Time: ~6-12 hours (depends on model verbosity)
- Storage: ~500MB per model results

**7B models**: ~6-8 hours
**14B models**: ~8-10 hours
**32B models**: ~10-15 hours

## Troubleshooting

### vLLM server doesn't start
- Check GPU availability: `nvidia-smi`
- Check vLLM logs: `tail -f logs/vllm_server_*.log`
- Increase MAX_WAIT if model loading is slow

### Low accuracy (< 20%)
- Expected for base models without instruction tuning
- Check response extraction: Review `response` field in results
- Base models may not follow simple "Answer: X" format

### Timeout errors
- Increase timeout in script (default: 120s)
- Check vLLM server load
- Reduce batch processing if memory constrained

### Checkpoint not loading
- Check file permissions
- Verify JSON is not corrupted
- Delete checkpoint to force fresh start if needed

## Comparing Results

After all models complete:

```bash
# Compare all models
python scripts/utils/compare_base_models.py results/base_runs/

# Expected output:
# Model              | Temp 0.0 | Temp 0.3 | Temp 0.7 | Avg
# -------------------|----------|----------|----------|------
# Qwen2.5-7B        | 35.2%    | 34.8%    | 33.5%    | 34.5%
# Qwen2.5-14B       | 38.1%    | 37.6%    | 36.2%    | 37.3%
# Qwen2.5-32B       | 42.3%    | 41.8%    | 40.1%    | 41.4%
# Olmo-3-1025-7B    | 28.5%    | 28.1%    | 27.3%    | 28.0%
# Olmo-3-1125-32B   | 36.7%    | 36.2%    | 34.9%    | 35.9%
```

## Notes

- Base models are NOT instruction-tuned, so lower accuracy is expected
- Simple prompts work best for base models
- Temperature sensitivity varies by model
- Results establish baseline for neurosymbolic augmentation
- All runs use the same random seed per temperature for reproducibility

## Next Steps

After base runs complete:
1. Analyze temperature sensitivity per model
2. Compare category-specific performance
3. Test neurosymbolic augmentation (Hybrid UMLS Verifier)
4. Compare base vs instruct vs neurosymbolic approaches
