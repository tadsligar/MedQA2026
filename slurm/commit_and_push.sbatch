#!/bin/bash -l
#SBATCH --job-name=commit_push
#SBATCH --partition=defq
#SBATCH --time=00:20:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --output=logs/commit_push_%j.out
#SBATCH --error=logs/commit_push_%j.err

# Final flush for a results chain: stage the logprob results, commit, and push to master.
# The per-job blocks already commit/push each model incrementally; this is the catch-all
# that captures anything left over (e.g. a per-job push that failed) so master ends clean.
# Scope is limited to results/base_runs_logprobs -- never `git add -A`, so nothing under
# data/umls/ (untracked, large) is ever committed.

cd /aiau010_scratch/tzs0128/repo/MedQA2026

echo "=========================================="
echo "Final commit & push -- job $SLURM_JOB_ID at $(date)"
echo "=========================================="

git add results/base_runs_logprobs

if git diff --cached --quiet; then
    echo "Nothing new to commit."
else
    git commit -m "EXP1 logprobs: repeat-run results flush (job ${SLURM_JOB_ID})"
fi

# Push regardless -- there may be locally-committed-but-unpushed work from the run jobs.
if git push origin master; then
    echo "Pushed to GitHub. origin/master is now: $(git rev-parse --short origin/master)"
else
    echo "WARN: git push failed; commits are local. Flush from the login node: git push origin master"
    exit 1
fi
