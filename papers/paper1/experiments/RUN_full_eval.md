# AIAU prompt — re-run EXP1–5 on the FULL combined dataset

> ⚠️ BLOCKING PREREQUISITE — the EXP1–5 runners are hardcoded to 4 options (A–D) and assume
> `item['options']` is a dict. The full/test datasets are **5-option, stored as a LIST**. Running
> as-is will crash on `.items()` or silently drop option **E** (never selecting E, marking every
> E-answer question wrong, calibrating over the wrong letter set). FIX THE RUNNERS FIRST:
> `test_base_model_variants.py` (`VALID=['A','B','C','D']`, `options.items()`),
> `test_base_model_logprobs.py` (softmax over "four letters A–D"), `test_instruct_model.py`
> ("first valid A–D letter"). Make them derive the option letters per question (handle dict OR
> list), render all present options (A–E when 5), set the valid-answer set dynamically, and take
> logprobs over all present letters. (`slurm/full_run/` already handles 5 options — copy its
> approach.) Do NOT launch the jobs below until this is done and a quick 5-option smoke test shows
> 'E' is selectable.

Paste the block below to your AIAU code assistant.

---

In the MedQA2026 repo on the cluster (`/aiau010_scratch/tzs0128/repo/MedQA2026`, conda env `medqa`),
re-run Paper 1 experiments EXP1–EXP5 on the **full combined dataset**
(`data/datasets/medqa_full_combined.json`, 12,723 questions, 5-option) instead of the focused-1,030
set. We're standardizing the category-free analyses on the full 5-option set for power and
comparability.

Hard requirements:
- Write all outputs to NEW `*_full` result directories so the existing focused-1,030 results are
  NOT overwritten. Reuse the existing runner scripts unchanged — they already accept `--dataset`
  and `--output-dir`. Only create new sbatch wrappers (put them in `slurm/full_eval/`), mirroring
  the conventions in the existing jobs (partition `general`, `gpu:2`/TP=2 for ≤32B, conda `medqa`,
  HF cache exports, `vllm serve` + health-check loop, kill vLLM at end).
- Do NOT disturb the running Paper 4 labeling job; all these jobs bind port 8000, so don't
  co-schedule two vLLM servers on one node — sequence them (gate with `--dependency=afterany:`)
  or land them on separate nodes.
- Keep each experiment's model set and decoding config identical to the focused runs (below); only
  the dataset and output dir change.

Experiments (runner → config → output dir):

1. EXP1 calibration (base models, logprobs):
   `scripts/base_runs/test_base_model_logprobs.py`
   models: Qwen2.5 7B/14B/32B, OLMo-3 7B/32B (base) ; `--temperatures 0.0,0.3,0.7 --n-runs 3`
   → `results/base_runs_logprobs_full/<model>`
   (If GPU time is tight, `--temperatures 0.0 --n-runs 1` is enough for ECE; confirm with me.)

2. EXP2 instruct comparison:
   `scripts/instruct_runs/test_instruct_model.py`
   the 5 instruct counterparts (same IDs as the focused EXP2 sbatch) ; `--temperatures 0.0,0.3,0.7 --n-runs 3`
   → `results/instruct_runs_full/<model>_instruct`

3. EXP3 prompt ablation (base):
   `scripts/base_runs/test_base_model_variants.py --prompt-variant v0|v1|v2|v3 --temperatures 0.0 --n-runs 1`
   same models as focused (olmo3_32b, qwen25_14b) → `results/prompt_ablation_full/<model>`

4. EXP4 CoT vs direct (base):
   `scripts/base_runs/test_base_model_variants.py --mode direct --max-tokens 800` and
   `--mode cot --max-tokens 1024`, `--temperatures 0.0,0.7 --n-runs 1`
   same model as focused (qwen25_14b) → `results/cot_vs_direct_full/<model>/{direct,cot}`

5. EXP5 self-consistency (base):
   `scripts/base_runs/test_base_model_variants.py --temperatures 0.7 --n-runs 1 --n-samples 20`
   same model as focused (qwen25_14b) → `results/self_consistency_full/<model>`

Cost/sequencing: this is ~12× the focused inference. Run the cheap, high-value ones first
(EXP1 calibration, EXP2 instruct, EXP3 ablation), then EXP4 CoT and EXP5 self-consistency (k=20 is
the most expensive — long queue). Submit per-model jobs; don't block the whole set on one.

After the runs:
- Re-run the analyses pointed at the `*_full` dirs to regenerate the **category-free** tables only
  (`compute_calibration.py`, `compute_instruct_comparison.py`, and the EXP3/4/5 analyses): overall
  accuracy, base-vs-instruct delta + McNemar, temperature degradation, CoT delta, self-consistency
  curve, ECE/reliability. Update the analysis scripts to read the `*_full` dirs (add a path arg or
  a `--full` flag; don't hardcode-overwrite the focused paths).
- Do NOT recompute any per-category breakdowns yet — the category labels are under revision
  (Paper 4 relabeling). Leave per-category tables out of the full-set run.
- Also report the held-out **test split** (`medqa_full_test.json`, 1,273 qids) as a clean,
  contamination-free slice by filtering the full results to those question_ids, alongside the
  full-12,723 numbers.
- Commit the new `*_full` results + regenerated tables and push, with a message noting "EXP1–5 on
  full combined (5-option), category-free metrics; test-split slice."

Report back: per-experiment overall accuracy on full vs the focused-1,030 numbers, so we can see
whether the findings (base>instruct for small models, instruct temp-robustness, CoT hurts,
self-consistency gains, calibration/ECE) hold at full scale and on the held-out test split.
