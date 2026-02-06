# Full Dataset Experiment Orchestration System

This directory contains an automated job orchestration system for running experiments on the full MedQA dataset (12,723 questions) across multiple models, temperatures, and runs.

## Overview

**Dataset**: `data/datasets/medqa_full_combined.json` (12,723 questions with IDs 0-12722)

**Experiments**:
- 5 models (OLMo-3 7B/32B, Qwen 2.5 7B/14B/32B)
- 3 temperatures (0.0, 0.3, 0.7)
- 3 runs per temperature
- **Total: 45 experiments**

## Directory Structure

```
slurm/full_run/
├── model_configs.json          # Central configuration file
├── setup_and_launch.sh         # Master setup script
├── generate_jobs.py            # Generates individual job scripts
├── generate_auto_commits.py    # Generates auto-commit scripts
├── orchestrator.py             # Main job orchestrator
├── jobs/                       # Individual SLURM job scripts (45 total)
│   ├── olmo3_7b_t0.0_r1.sbatch
│   ├── olmo3_7b_t0.0_r2.sbatch
│   └── ...
├── logs/                       # Job output logs
│   ├── orchestrator.log        # Orchestrator output
│   ├── olmo3_7b_t0.0_r1_*.out  # Individual job logs
│   └── ...
├── state/                      # Job state tracking
│   ├── job_state.json          # Current state of all jobs
│   ├── *.completed             # Completion markers
│   ├── *.failed                # Failure markers
│   └── *_committed.marker      # Git commit markers
└── auto_commit_*.sbatch        # Auto-commit scripts (5 total)
```

## Key Features

### 1. Automatic Job Management
- Monitors cluster resources
- Launches jobs when GPUs available
- Respects max concurrent job limit (default: 8)
- Avoids resource abuse while maximizing utilization

### 2. Fault Tolerance
- Checkpoints every 10 questions
- Automatically resumes from last checkpoint
- Retries failed jobs (max 3 attempts)
- Exponential backoff for retries

### 3. Resource Awareness
- Checks GPU availability before launching
- Balances load across cluster
- Unique ports per job (8000 + job_id % 1000)

### 4. Auto-Commit
- Commits results when all runs for a model complete
- Generates summary statistics
- Pushes to git automatically
- Uses `--dependency=singleton` to avoid duplicate commits

### 5. State Tracking
- Persistent state in `state/job_state.json`
- Tracks: pending, running, completed, failed
- Can stop/resume orchestrator anytime
- Completion markers for reliable status

## Configuration

### `model_configs.json`

Central configuration file containing:
- Model specifications (name, GPUs, memory)
- SLURM settings (time limit, resources)
- Orchestrator settings (max jobs, retries, intervals)

Key settings:
```json
{
  "orchestrator": {
    "max_concurrent_jobs": 8,      // Max simultaneous jobs
    "check_interval": 300,          // Check every 5 minutes
    "max_retries": 3,               // Retry failed jobs 3 times
    "min_gpu_availability": 2       // Min GPUs needed
  }
}
```

## Usage

### Initial Setup (Already Done)

```bash
./slurm/full_run/setup_and_launch.sh
```

This generates all job scripts and prepares the system.

### Launch Orchestrator

**As SLURM Job (recommended)**:
```bash
sbatch slurm/full_run/orchestrator_job.sbatch
```

This launches the orchestrator as a 12-hour SLURM job that:
- Monitors all experiment jobs
- Launches jobs when resources available
- Automatically submits a successor orchestrator before timeout (self-chaining)
- Continues until all jobs complete

**Direct execution (for testing only)**:
```bash
./slurm/full_run/orchestrator.py
```
Note: Direct execution doesn't auto-chain, so only use for testing or short runs.

### Monitor Progress

**Watch orchestrator log**:
```bash
tail -f slurm/full_run/logs/orchestrator.log
```

**Check job queue**:
```bash
watch -n 30 'squeue -u tzs0128'
```

**Check state**:
```bash
cat slurm/full_run/state/job_state.json | jq '.jobs | group_by(.status) | map({status: .[0].status, count: length})'
```

**Check individual job**:
```bash
tail -f slurm/full_run/logs/olmo3_7b_t0.0_r1_*.out
```

### Self-Chaining Mechanism

The orchestrator runs as a 12-hour SLURM job. To handle the multi-week runtime:

1. **Runtime monitoring**: Job tracks elapsed time
2. **Successor submission**: At 11 hours (30 min before timeout), checks if work remains
3. **Automatic handoff**: If jobs still pending/running, submits new orchestrator job
4. **State persistence**: New orchestrator loads existing state and continues
5. **Graceful completion**: If all jobs done, exits without successor

This creates a self-sustaining chain:
```
Orchestrator #1 (12h) → Orchestrator #2 (12h) → ... → Complete
```

Each orchestrator:
- Loads shared state from `state/job_state.json`
- Continues from where previous left off
- Submits its own successor if needed
- No manual intervention required

### Stop Orchestrator

The orchestrator can be safely interrupted:
```bash
# Find orchestrator process
ps aux | grep orchestrator.py

# Kill it
kill <PID>
```

State is saved continuously - just restart the orchestrator to resume.

### Manual Operations

**Submit a single job**:
```bash
sbatch slurm/full_run/jobs/olmo3_7b_t0.0_r1.sbatch
```

**Cancel all jobs**:
```bash
scancel -u tzs0128 --name=olmo3_7b_t0.0_r1
# Or cancel all:
scancel -u tzs0128
```

**Reset state** (⚠️ caution):
```bash
rm slurm/full_run/state/job_state.json
rm slurm/full_run/state/*.completed
rm slurm/full_run/state/*.failed
```

**Manually trigger auto-commit**:
```bash
sbatch slurm/full_run/auto_commit_olmo3_7b.sbatch
```

## Job Lifecycle

1. **Pending**: Job created, waiting to be submitted
2. **Running**: Job submitted to SLURM and executing
3. **Completed**: Job finished successfully, marker created
4. **Failed**: Job failed, eligible for retry (up to max_retries)

## How It Works

### Orchestrator Loop

Every 5 minutes (configurable):
1. Check SLURM queue for running jobs
2. Check for completion/failure markers
3. Update job state
4. Check available resources
5. Launch pending jobs (respecting max_concurrent limit)
6. Retry failed jobs (if retries remaining)
7. Print status summary
8. Exit when all jobs complete or max retries exhausted

### Job Execution

Each job:
1. Requests 2 GPUs, 32 CPUs, 200GB RAM
2. Starts vLLM server on unique port
3. Runs single temperature/run combination
4. Checkpoints every 10 questions
5. Creates completion marker on success
6. Triggers auto-commit for its model
7. Can be safely killed and restarted

### Auto-Commit

When all 9 runs for a model complete:
1. Verifies all result files exist
2. Generates summary.json with statistics
3. Stages result files
4. Creates descriptive commit
5. Pushes to remote
6. Creates commit marker

## Tuning Parameters

### More Aggressive (Use More Resources)

```json
"max_concurrent_jobs": 12,    // Launch more jobs
"check_interval": 180,         // Check more frequently
```

### More Conservative (Lighter Load)

```json
"max_concurrent_jobs": 4,     // Fewer simultaneous jobs
"check_interval": 600,         // Check less frequently
```

### GPU Memory Issues

If jobs fail due to OOM:
- Reduce `gpu_memory_utilization` in model_configs.json
- Reduce `max_model_len` for smaller context window

## Time Estimates

Based on 1,030-question focused dataset (~10 hours for 32B models):
- **12,723 questions ≈ 12.35× larger**
- Estimated runtime per experiment:
  - 7B models: ~50-70 hours
  - 14B models: ~80-100 hours
  - 32B models: ~120-140 hours

With 8 concurrent jobs, full completion: **~2-3 weeks**

## Troubleshooting

### Jobs stuck in pending
- Check: `sinfo` for cluster status
- Check: Node availability and GPU resources
- Reduce `max_concurrent_jobs` if overwhelming scheduler

### Jobs failing repeatedly
- Check individual log: `slurm/full_run/logs/<job_name>_*.out`
- Common issues:
  - vLLM startup timeout (increase `startup_wait`)
  - OOM (reduce `gpu_memory_utilization`)
  - Port conflict (should auto-resolve with unique ports)

### Orchestrator not launching jobs
- Check state file: `cat slurm/full_run/state/job_state.json`
- Verify job scripts exist: `ls slurm/full_run/jobs/`
- Check orchestrator log for errors

### Results not committing
- Check auto-commit logs: `slurm/full_run/logs/commit_*`
- Verify all 18 files exist (9 results + 9 checkpoints)
- Manually trigger: `sbatch slurm/full_run/auto_commit_<model>.sbatch`

## Results Location

Results will be saved to:
```
results/base_runs_full/
├── olmo3_7b/
│   ├── temp0.0_run1_results.json
│   ├── temp0.0_run1_checkpoint.json
│   ├── ...
│   └── summary.json
├── olmo3_32b/
├── qwen25_7b/
├── qwen25_14b/
└── qwen25_32b/
```

Each summary.json contains:
- Mean accuracy per temperature
- Standard deviation
- Individual run results

## Safety Features

- **Checkpointing**: Never lose progress
- **Idempotent**: Can safely rerun setup/orchestrator
- **State persistence**: Survives restarts
- **Resource limits**: Won't overwhelm cluster
- **Retry logic**: Handles transient failures
- **Singleton commits**: Prevents duplicate commits

## Advanced Usage

### Running Subset of Models

Edit `model_configs.json` to comment out models:
```json
"models": {
  "olmo3_7b": { ... },
  // "qwen25_32b": { ... }  // Skip this model
}
```

Then regenerate:
```bash
python3 slurm/full_run/generate_jobs.py
python3 slurm/full_run/generate_auto_commits.py
```

### Changing Temperatures

Edit `temperatures` in `model_configs.json`:
```json
"temperatures": [0.0, 0.5, 1.0],
```

Then regenerate job scripts.

### Dry Run

To see what would be launched without actually submitting:
```python
# Modify orchestrator.py submit_job() to print instead of submit
print(f"Would submit: {script_path}")
return "DRY_RUN_ID"
```

## Support

For issues:
1. Check orchestrator log: `slurm/full_run/logs/orchestrator.log`
2. Check job logs: `slurm/full_run/logs/<job_name>_*.out`
3. Check state: `slurm/full_run/state/job_state.json`
4. Review this README

---

**Happy experimenting! 🚀**
