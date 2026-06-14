# AIAU run prompt — Paper 4 second-annotator labeling (vLLM)

Paste the block below once the repo is synced on the cluster.

---

I'm on the AIAU HPC cluster in `/aiau010_scratch/tzs0128/projects/MedQA2026` (repo just `git pull`-ed,
conda env `medqa`). I need to run the Paper 4 labeling job: it serves an open instruct model with
vLLM and runs `scripts/dataset_generation/operation_labeler.py` against it to label all 12,723
MedQA questions with a reasoning operation (R/F/B/I/W) plus a Y/N for each of 15 organ systems.
This is an INDEPENDENT second annotator to a gpt-5.4-mini API pass; agreement between them is the
label-reliability metric.

Please:
1. Confirm the SLURM job exists: `slurm/reasoning_ops/run_label_vllm.sbatch` (and its README).
2. Make sure the model is available (in `$HF_HOME`/`/aiau010_scratch/tzs0128/hf_cache` or
   downloadable on the node): default is `Qwen/Qwen2.5-32B-Instruct` (2 GPUs, TP=2).
3. Submit the job:
   ```bash
   cd /aiau010_scratch/tzs0128/projects/MedQA2026
   sbatch slurm/reasoning_ops/run_label_vllm.sbatch
   ```
   For the stronger 72B annotator (needs 4 GPUs):
   ```bash
   sbatch --gres=gpu:4 --export=ALL,MODEL=Qwen/Qwen2.5-72B-Instruct,TP=4 slurm/reasoning_ops/run_label_vllm.sbatch
   ```
4. Monitor:
   ```bash
   squeue -u tzs0128
   tail -f logs/p4_label_vllm_*.out        # job progress
   tail -f logs/vllm_p4_label_*.log         # vLLM server (model load ~10-15 min)
   ```
5. Output lands at `results/reasoning_ops/op_labels_qwen25_32b.jsonl` (resumable; re-submit to
   continue). Each line: `{"qid","reasoning_operation","systems":{15 Y/N},"model"}`. Watch for any
   `"parse_fail":true` rows — if there are many, the model is omitting systems; rerun with the 72B
   variant.
6. When it finishes, sanity-check counts and (if the API file is present) the auto-printed
   agreement vs `op_labels.jsonl`. Then commit just the label file (not the scratch):
   ```bash
   git add results/reasoning_ops/op_labels_qwen25_32b.jsonl
   git commit -m "Paper 4: vLLM second-annotator operation+system labels (Qwen2.5-32B)"
   git push
   ```

Notes: the labeler is greedy (temp 0) and requires all 15 systems in the JSON; `CLASSIFIER_MODEL`
is set to the served model id automatically. Expected wall-clock after model load: roughly 1–3h
for the full 12,723 (serial requests to the local endpoint).
