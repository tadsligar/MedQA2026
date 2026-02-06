#!/bin/bash -l
#SBATCH --job-name=orchestrator
#SBATCH --partition=general
#SBATCH --time=12:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --output=slurm/full_run/logs/orchestrator_%j.out
#SBATCH --error=slurm/full_run/logs/orchestrator_%j.err

echo "=========================================="
echo "JOB ORCHESTRATOR (SLURM Mode)"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Start time: $(date)"
echo "Runtime limit: 12 hours"
echo "=========================================="
echo

cd /aiau010_scratch/tzs0128/projects/MedQA2026

# Activate conda environment
source ~/.bashrc
conda activate medqa

# Calculate when to submit successor (30 minutes before timeout)
# 12 hours = 43200 seconds, submit at 41400 seconds (11.5 hours)
RUNTIME_LIMIT=41400
START_TIME=$(date +%s)

# Function to check if we should submit successor
should_submit_successor() {
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))

    # Submit successor after 11 hours
    if [ $ELAPSED -ge $RUNTIME_LIMIT ]; then
        return 0  # true
    fi
    return 1  # false
}

# Function to check if all jobs are complete
check_completion() {
    python3 << 'PYTHON_EOF'
import json
from pathlib import Path

state_file = Path("slurm/full_run/state/job_state.json")
if not state_file.exists():
    print("STATE_NOT_FOUND")
    exit(0)

with open(state_file) as f:
    state = json.load(f)

total = len(state['jobs'])
completed = sum(1 for j in state['jobs'].values() if j['status'] == 'completed')
failed = sum(1 for j in state['jobs'].values()
             if j['status'] == 'failed' and j['retries'] >= 3)

if completed + failed == total:
    print("ALL_COMPLETE")
else:
    print("IN_PROGRESS")
PYTHON_EOF
}

# Track if we've submitted a successor
SUCCESSOR_SUBMITTED=0

# Wrapper around orchestrator that handles time limit
run_orchestrator_with_timeout() {
    # Run orchestrator in background
    python3 ./slurm/full_run/orchestrator.py &
    ORCH_PID=$!

    echo "Orchestrator started with PID: $ORCH_PID"
    echo

    # Monitor orchestrator and time limit
    while kill -0 $ORCH_PID 2>/dev/null; do
        # Check if we should submit successor
        if [ $SUCCESSOR_SUBMITTED -eq 0 ]; then
            if should_submit_successor; then
                echo
                echo "=========================================="
                echo "Runtime limit approaching (11 hours elapsed)"
                echo "Checking if successor needed..."
                echo "=========================================="
                echo

                COMPLETION_STATUS=$(check_completion)

                if [ "$COMPLETION_STATUS" == "ALL_COMPLETE" ]; then
                    echo "All jobs complete! No successor needed."
                    echo "Allowing orchestrator to finish gracefully..."
                elif [ "$COMPLETION_STATUS" == "IN_PROGRESS" ]; then
                    echo "Jobs still in progress. Submitting successor orchestrator..."

                    SUCCESSOR_ID=$(sbatch --parsable slurm/full_run/orchestrator_job.sbatch)

                    if [ $? -eq 0 ]; then
                        echo "✓ Successor submitted: Job ID $SUCCESSOR_ID"
                        echo "  Current orchestrator will continue until completion or timeout"
                        echo "  Successor will take over automatically"
                        SUCCESSOR_SUBMITTED=1
                    else
                        echo "✗ Failed to submit successor"
                        echo "  Will retry on next iteration"
                    fi
                else
                    echo "Could not determine completion status. Will retry."
                fi
                echo
            fi
        fi

        # Sleep for 1 minute before checking again
        sleep 60
    done

    # Orchestrator exited
    wait $ORCH_PID
    ORCH_EXIT=$?

    echo
    echo "Orchestrator exited with code: $ORCH_EXIT"

    return $ORCH_EXIT
}

# Run the orchestrator
run_orchestrator_with_timeout

EXIT_CODE=$?

echo
echo "=========================================="
echo "Orchestrator job completed at: $(date)"

if [ $SUCCESSOR_SUBMITTED -eq 1 ]; then
    echo "Status: Successor submitted, handoff complete"
else
    # Check final status
    COMPLETION_STATUS=$(check_completion)
    if [ "$COMPLETION_STATUS" == "ALL_COMPLETE" ]; then
        echo "Status: All jobs complete!"
    else
        echo "Status: Orchestrator exited without submitting successor"
        echo "        You may need to restart manually"
    fi
fi

echo "=========================================="

exit $EXIT_CODE
