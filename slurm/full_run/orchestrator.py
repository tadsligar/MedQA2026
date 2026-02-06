#!/usr/bin/env python3
"""
Job Orchestrator for Full Dataset Experiments

Monitors cluster resources, launches jobs when available, and relaunches failed jobs.
Tracks job state and ensures all experiments complete successfully.
"""

import json
import subprocess
import time
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class JobOrchestrator:
    def __init__(self, config_path="slurm/full_run/model_configs.json"):
        with open(config_path) as f:
            self.config = json.load(f)

        self.state_dir = Path("slurm/full_run/state")
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.state_file = self.state_dir / "job_state.json"
        self.jobs_dir = Path("slurm/full_run/jobs")

        self.max_concurrent = self.config['orchestrator']['max_concurrent_jobs']
        self.check_interval = self.config['orchestrator']['check_interval']
        self.max_retries = self.config['orchestrator']['max_retries']

        self.state = self.load_state()

    def load_state(self):
        """Load or initialize job state."""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)

        # Initialize state for all jobs
        state = {
            'jobs': {},
            'start_time': datetime.now().isoformat(),
            'last_update': datetime.now().isoformat()
        }

        for model_key in self.config['models'].keys():
            for temp in self.config['temperatures']:
                for run in range(1, self.config['n_runs_per_temperature'] + 1):
                    job_name = f"{model_key}_t{temp}_r{run}"
                    state['jobs'][job_name] = {
                        'status': 'pending',
                        'slurm_id': None,
                        'retries': 0,
                        'last_attempt': None,
                        'completed_at': None,
                        'model': model_key,
                        'temperature': temp,
                        'run': run
                    }

        self.save_state(state)
        return state

    def save_state(self, state=None):
        """Save job state to disk."""
        if state is None:
            state = self.state

        state['last_update'] = datetime.now().isoformat()

        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def get_running_jobs(self):
        """Get currently running SLURM jobs."""
        try:
            result = subprocess.run(
                ['squeue', '-u', 'tzs0128', '-h', '-o', '%i %j %t'],
                capture_output=True,
                text=True,
                timeout=30
            )

            running = {}
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 3:
                    job_id, job_name, status = parts[0], parts[1], parts[2]
                    running[job_name] = {
                        'slurm_id': job_id,
                        'status': status
                    }

            return running
        except Exception as e:
            print(f"Error getting running jobs: {e}")
            return {}

    def check_job_completion(self, job_name):
        """Check if a job has completed successfully."""
        completed_marker = self.state_dir / f"{job_name}.completed"
        failed_marker = self.state_dir / f"{job_name}.failed"

        if completed_marker.exists():
            return 'completed'
        elif failed_marker.exists():
            return 'failed'
        return None

    def get_available_resources(self):
        """Check available GPU resources."""
        try:
            # Get node info
            result = subprocess.run(
                ['sinfo', '-N', '-h', '-o', '%N %G %t'],
                capture_output=True,
                text=True,
                timeout=30
            )

            total_idle_gpus = 0
            for line in result.stdout.strip().split('\n'):
                if 'idle' in line.lower():
                    # Parse GPU count (format: gpu:2)
                    parts = line.split()
                    if len(parts) >= 2:
                        gpu_info = parts[1]
                        if ':' in gpu_info:
                            try:
                                gpus = int(gpu_info.split(':')[1])
                                total_idle_gpus += gpus
                            except:
                                pass

            return {'idle_gpus': total_idle_gpus}
        except Exception as e:
            print(f"Error checking resources: {e}")
            return {'idle_gpus': 0}

    def submit_job(self, job_name):
        """Submit a job to SLURM."""
        script_path = self.jobs_dir / f"{job_name}.sbatch"

        if not script_path.exists():
            print(f"ERROR: Job script not found: {script_path}")
            return None

        try:
            result = subprocess.run(
                ['sbatch', str(script_path)],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                # Parse job ID from output
                output = result.stdout.strip()
                if 'Submitted batch job' in output:
                    job_id = output.split()[-1]
                    return job_id
            else:
                print(f"Error submitting {job_name}: {result.stderr}")

        except Exception as e:
            print(f"Exception submitting {job_name}: {e}")

        return None

    def update_job_statuses(self):
        """Update job statuses based on SLURM and completion markers."""
        running_jobs = self.get_running_jobs()

        for job_name, job_info in self.state['jobs'].items():
            # Check completion markers first
            completion_status = self.check_job_completion(job_name)

            if completion_status == 'completed':
                if job_info['status'] != 'completed':
                    print(f"✓ {job_name} completed!")
                    job_info['status'] = 'completed'
                    job_info['completed_at'] = datetime.now().isoformat()

            elif completion_status == 'failed':
                if job_info['status'] not in ['failed', 'completed']:
                    print(f"✗ {job_name} failed (attempt {job_info['retries'] + 1})")
                    job_info['status'] = 'failed'

            # Check if job is still running in SLURM
            elif job_name in running_jobs:
                slurm_status = running_jobs[job_name]['status']
                if slurm_status in ['R', 'PD', 'CG']:  # Running, Pending, Completing
                    job_info['status'] = 'running'
                    job_info['slurm_id'] = running_jobs[job_name]['slurm_id']

            # If job was running but isn't anymore and has no completion marker
            elif job_info['status'] == 'running':
                # Job disappeared without completion - likely failed
                print(f"⚠ {job_name} disappeared from queue without completion marker")
                job_info['status'] = 'failed'

        self.save_state()

    def launch_pending_jobs(self):
        """Launch pending jobs based on available resources."""
        resources = self.get_available_resources()
        running_count = sum(1 for j in self.state['jobs'].values() if j['status'] == 'running')

        print(f"\nResources: {resources['idle_gpus']} idle GPUs | Running: {running_count}/{self.max_concurrent}")

        if running_count >= self.max_concurrent:
            return 0

        launched = 0

        for job_name, job_info in sorted(self.state['jobs'].items()):
            if running_count + launched >= self.max_concurrent:
                break

            # Launch pending jobs
            if job_info['status'] == 'pending':
                job_id = self.submit_job(job_name)
                if job_id:
                    print(f"→ Launched {job_name} (SLURM ID: {job_id})")
                    job_info['status'] = 'running'
                    job_info['slurm_id'] = job_id
                    job_info['last_attempt'] = datetime.now().isoformat()
                    launched += 1

            # Retry failed jobs
            elif job_info['status'] == 'failed' and job_info['retries'] < self.max_retries:
                # Clean up failure marker
                failed_marker = self.state_dir / f"{job_name}.failed"
                if failed_marker.exists():
                    failed_marker.unlink()

                job_id = self.submit_job(job_name)
                if job_id:
                    job_info['retries'] += 1
                    print(f"↻ Retrying {job_name} (attempt {job_info['retries'] + 1}/{self.max_retries + 1}) (SLURM ID: {job_id})")
                    job_info['status'] = 'running'
                    job_info['slurm_id'] = job_id
                    job_info['last_attempt'] = datetime.now().isoformat()
                    launched += 1

        if launched > 0:
            self.save_state()

        return launched

    def print_summary(self):
        """Print current status summary."""
        by_status = defaultdict(int)
        by_model = defaultdict(lambda: defaultdict(int))

        for job_name, job_info in self.state['jobs'].items():
            status = job_info['status']
            model = job_info['model']

            by_status[status] += 1
            by_model[model][status] += 1

        print("\n" + "="*70)
        print("ORCHESTRATOR STATUS")
        print("="*70)

        total = len(self.state['jobs'])
        completed = by_status.get('completed', 0)
        running = by_status.get('running', 0)
        failed = by_status.get('failed', 0)
        pending = by_status.get('pending', 0)

        print(f"Total Jobs: {total}")
        print(f"  ✓ Completed: {completed}/{total} ({100*completed/total:.1f}%)")
        print(f"  ▶ Running:   {running}")
        print(f"  ⏸ Pending:   {pending}")
        print(f"  ✗ Failed:    {failed}")

        print("\nPer Model:")
        for model in sorted(by_model.keys()):
            stats = by_model[model]
            model_total = sum(stats.values())
            model_completed = stats.get('completed', 0)
            print(f"  {model:12} {model_completed:2}/{model_total} completed")

        print("="*70)

    def run(self):
        """Main orchestrator loop."""
        print("="*70)
        print("JOB ORCHESTRATOR STARTED")
        print("="*70)
        print(f"Total jobs: {len(self.state['jobs'])}")
        print(f"Max concurrent: {self.max_concurrent}")
        print(f"Check interval: {self.check_interval}s")
        print(f"Max retries: {self.max_retries}")
        print("="*70)

        iteration = 0

        while True:
            iteration += 1
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iteration {iteration}")

            # Update statuses
            self.update_job_statuses()

            # Check if all jobs are complete
            all_done = all(
                j['status'] in ['completed', 'failed'] and
                (j['status'] == 'completed' or j['retries'] >= self.max_retries)
                for j in self.state['jobs'].values()
            )

            if all_done:
                self.print_summary()
                print("\n" + "="*70)
                print("ALL JOBS COMPLETE!")
                print("="*70)
                break

            # Launch new jobs
            launched = self.launch_pending_jobs()

            # Print summary
            if iteration % 5 == 0 or launched > 0:
                self.print_summary()

            # Wait before next check
            time.sleep(self.check_interval)


def main():
    try:
        orchestrator = JobOrchestrator()
        orchestrator.run()
    except KeyboardInterrupt:
        print("\n\nOrchestrator interrupted by user")
        print("State saved. Can be resumed by running again.")
        sys.exit(0)
    except Exception as e:
        print(f"\nOrchestrator error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
