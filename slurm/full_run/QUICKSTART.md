# Quick Start Guide

## TL;DR

```bash
# Launch the orchestrator (it handles everything else)
sbatch slurm/full_run/orchestrator_job.sbatch

# Monitor progress
watch -n 30 'squeue -u tzs0128'
```

That's it! The orchestrator will:
- Launch all 45 experiments when resources are available
- Retry failed jobs automatically
- Commit results to git when models complete
- Chain itself to run for weeks if needed
- Stop when everything is done

## What Gets Run

- **5 models**: OLMo-3 (7B, 32B), Qwen 2.5 (7B, 14B, 32B)
- **3 temperatures**: 0.0, 0.3, 0.7
- **3 runs each**: for statistical significance
- **Total: 45 experiments** on 12,723 questions

## How to Monitor

### Quick Status
```bash
# How many jobs running/pending?
squeue -u tzs0128

# What's the overall progress?
python3 << 'EOF'
import json
state = json.load(open('slurm/full_run/state/job_state.json'))
jobs = state['jobs']
total = len(jobs)
completed = sum(1 for j in jobs.values() if j['status'] == 'completed')
running = sum(1 for j in jobs.values() if j['status'] == 'running')
pending = sum(1 for j in jobs.values() if j['status'] == 'pending')
failed = sum(1 for j in jobs.values() if j['status'] == 'failed')
print(f"Completed: {completed}/{total} ({100*completed/total:.1f}%)")
print(f"Running: {running}, Pending: {pending}, Failed: {failed}")
EOF
```

### Detailed Monitoring
```bash
# Watch orchestrator
tail -f slurm/full_run/logs/orchestrator_*.out

# Watch a specific experiment
tail -f slurm/full_run/logs/olmo3_7b_t0.0_r1_*.out

# Check all running jobs
squeue -u tzs0128 -o "%.18i %.9P %.30j %.8u %.2t %.10M %.6D %R"
```

## Expected Timeline

With 8 concurrent jobs (default):
- **Startup**: Jobs begin within minutes
- **First results**: ~50-70 hours (7B models complete)
- **Mid-point**: ~1 week (14B models done)
- **Completion**: ~2-3 weeks (all 32B models done)

Results are committed to git as each model completes (5 total commits).

## Configuration

To adjust behavior, edit `slurm/full_run/model_configs.json`:

```json
{
  "orchestrator": {
    "max_concurrent_jobs": 8,    // More = faster but heavier load
    "check_interval": 300,        // How often to check (seconds)
    "max_retries": 3              // Retries for failed jobs
  }
}
```

After changes, regenerate jobs:
```bash
python3 slurm/full_run/generate_jobs.py
python3 slurm/full_run/generate_auto_commits.py
```

## Common Tasks

### Pause Everything
```bash
scancel -u tzs0128 --name=orchestrator  # Stop orchestrator
scancel -u tzs0128                       # Stop all experiments
```

State is saved - just relaunch orchestrator to resume.

### Resume After Pause
```bash
sbatch slurm/full_run/orchestrator_job.sbatch
```

### Check What Failed
```bash
jq '.jobs | to_entries | map(select(.value.status == "failed")) | map(.key)' \
  slurm/full_run/state/job_state.json
```

### Reset Everything (⚠️ Nuclear Option)
```bash
scancel -u tzs0128                              # Cancel all jobs
rm -f slurm/full_run/state/job_state.json      # Reset state
rm -f slurm/full_run/state/*.completed         # Remove markers
rm -f slurm/full_run/state/*.failed
sbatch slurm/full_run/orchestrator_job.sbatch  # Start fresh
```

## Troubleshooting

**Jobs not launching?**
- Check: `sinfo` - are nodes available?
- Lower `max_concurrent_jobs` in config
- Check orchestrator log for errors

**Jobs failing repeatedly?**
- Check logs: `tail -f slurm/full_run/logs/<job_name>_*.out`
- Common fixes:
  - Reduce GPU memory in config if OOM
  - Increase startup_wait if vLLM timeout

**Orchestrator stopped?**
- Check: `squeue -u tzs0128 --name=orchestrator`
- If gone and jobs still pending: resubmit
- State persists, so no progress lost

## Results

All results go to `results/base_runs_full/<model>/`:
- `temp{T}_run{R}_results.json` - Full results
- `temp{T}_run{R}_checkpoint.json` - Checkpoints
- `summary.json` - Aggregated statistics

Committed to git automatically when models complete.

## Getting Help

1. Check orchestrator log: `slurm/full_run/logs/orchestrator_*.out`
2. Check job log: `slurm/full_run/logs/<job_name>_*.out`
3. Check state: `cat slurm/full_run/state/job_state.json | jq`
4. See full README: `slurm/full_run/README.md`

---

**Ready? Launch it:** `sbatch slurm/full_run/orchestrator_job.sbatch` 🚀
