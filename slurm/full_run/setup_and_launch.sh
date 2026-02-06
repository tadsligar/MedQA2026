#!/bin/bash
#
# Master setup script for full dataset experiments
# This script:
# 1. Generates all job scripts
# 2. Generates auto-commit scripts
# 3. Creates necessary directories
# 4. Launches the orchestrator
#

set -e

echo "=========================================="
echo "FULL DATASET EXPERIMENT SETUP"
echo "=========================================="
echo

cd /aiau010_scratch/tzs0128/projects/MedQA2026

# Create directory structure
echo "Creating directories..."
mkdir -p slurm/full_run/jobs
mkdir -p slurm/full_run/logs
mkdir -p slurm/full_run/state
mkdir -p results/base_runs_full

echo "  ✓ slurm/full_run/jobs/"
echo "  ✓ slurm/full_run/logs/"
echo "  ✓ slurm/full_run/state/"
echo "  ✓ results/base_runs_full/"
echo

# Generate job scripts
echo "Generating individual job scripts..."
python3 slurm/full_run/generate_jobs.py

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to generate job scripts"
    exit 1
fi
echo

# Generate auto-commit scripts
echo "Generating auto-commit scripts..."
python3 slurm/full_run/generate_auto_commits.py

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to generate auto-commit scripts"
    exit 1
fi
echo

# Make orchestrator executable
chmod +x slurm/full_run/orchestrator.py

echo "=========================================="
echo "SETUP COMPLETE"
echo "=========================================="
echo
echo "Generated:"
echo "  - 45 individual job scripts (5 models × 3 temps × 3 runs)"
echo "  - 5 auto-commit scripts (one per model)"
echo "  - State tracking directory"
echo
echo "Next steps:"
echo "  1. Review configuration: slurm/full_run/model_configs.json"
echo "  2. Check job scripts: slurm/full_run/jobs/"
echo "  3. Launch orchestrator: sbatch slurm/full_run/orchestrator_job.sbatch"
echo
echo "To launch orchestrator:"
echo "  sbatch slurm/full_run/orchestrator_job.sbatch"
echo
echo "The orchestrator runs as a SLURM job and automatically:"
echo "  - Monitors all experiment jobs"
echo "  - Launches new jobs when resources available"
echo "  - Retries failed jobs"
echo "  - Submits a successor before timeout (self-chaining)"
echo "  - Stops when all jobs complete"
echo
echo "To monitor:"
echo "  tail -f slurm/full_run/logs/orchestrator_*.out"
echo "  watch -n 30 'squeue -u tzs0128'"
echo
echo "=========================================="
