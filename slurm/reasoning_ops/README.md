# Paper 4 — reasoning-operation + organ-system labeling (cluster, second annotator)

`run_label_vllm.sbatch` serves an open instruct model with vLLM and runs the SAME
`scripts/dataset_generation/operation_labeler.py` against the local OpenAI-compatible endpoint —
an INDEPENDENT second annotator to the gpt-5.4-mini API pass. Agreement between the two is a
label-reliability number for the paper (operation: accuracy/kappa; systems: F1/Jaccard). Free, no
data egress.

## Launch
```bash
cd /aiau010_scratch/tzs0128/repo/MedQA2026
sbatch slurm/reasoning_ops/run_label_vllm.sbatch                      # Qwen2.5-32B-Instruct, 2 GPU (default)
# stronger annotator (72B needs 4 GPUs):
sbatch --gres=gpu:4 --export=ALL,MODEL=Qwen/Qwen2.5-72B-Instruct,TP=4 slurm/reasoning_ops/run_label_vllm.sbatch
# focused 1,030 set instead of full:
sbatch --export=ALL,DATASET=data/datasets/medqa_focused_1030.json,OUTTAG=qwen32b_focused slurm/reasoning_ops/run_label_vllm.sbatch
```
Output: `results/reasoning_ops/op_labels_<OUTTAG>.jsonl` (kept separate from the API
`op_labels.jsonl`). The labeler is resumable — re-submitting continues where it stopped.

## Notes
- `CLASSIFIER_MODEL` is set to the served model id automatically (vLLM matches on it).
- The job auto-runs an agreement check vs `op_labels.jsonl` at the end if that API file exists.
- The labeler is greedy (temp 0) and requires all 15 systems in the JSON; a weaker model that
  omits keys yields `parse_fail` rows (flagged, excluded downstream). If the parse_fail rate is
  high, use the 72B variant.
