# Paper 1 — New Experiment Prompts

Each file is a **self-contained prompt** you can hand to an agent (or follow yourself)
to run one experiment that strengthens Paper 1. They are ordered by impact-per-effort.
Every doc states: motivation, exact configuration, expected outputs, analysis plan, and
the `[TBD-EXP#]` placeholder(s) it fills in `../DRAFT.md`.

Shared context for all experiments:
- Repo: `MedQA2026`; focused dataset `data/datasets/medqa_focused_1030.json`
  (1,030 questions, 206/category, 4-option A–D, random baseline 25%).
- Serving: vLLM, base models use the **completions** endpoint (`use_chat_api: false`),
  `max_output_tokens: 800`, bfloat16, tensor-parallel 2, A100 80GB. Configs in `configs/`.
- Existing runner: `scripts/base_runs/test_base_model.py`; SLURM in `slurm/full_run/`.
- Existing result schema (per question):
  `{question_id, category, correct, predicted, is_correct, tokens, latency, response}`.
- Answer extraction rule: **first valid A–D letter** in the generation (validated: 0
  malformed outputs in 46,350 generations; Qwen base models run to the 800-token cap on
  ~75% of items but answer first).

| # | Experiment | Fills placeholder | New compute |
|---|---|---|---|
| 1 | Token log-probabilities → calibration | EXP1 | re-run inference, logprobs on |
| 2 | Instruction-tuned comparison | EXP2 | 5 instruct models |
| 3 | Prompt-format robustness ablation | EXP3 | 1 model × 3 prompts |
| 4 | Chain-of-thought vs direct | EXP4 | 1–2 models, CoT prompt |
| 5 | Self-consistency scaling (k samples) | EXP5 | 1 model, k=5/10/20 |
| 6 | Hard-core expert clinical review | EXP6 | manual, 144 items |
| 7 | Category-label validation / IAA | EXP7 | manual/LLM audit |

Recommended minimum for a conference submission: **EXP1 + EXP2**.
