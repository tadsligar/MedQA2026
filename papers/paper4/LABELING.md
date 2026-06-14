# Paper 4 — labeling run guide

Two axes, one call per question, **no confidence field** (verbalized LLM confidence is poorly
calibrated; reliability is measured externally against a gold sample):
- `reasoning_operation` — single-label R/F/B/I/W (Paper 4 headline axis).
- `systems` — the model adjudicates **each of the 15 systems independently and returns a Y/N
  for every one** (multi-label ROS axis). No `primary_system`. The parser requires all 15 to be
  present (a response missing any is retried, never auto-filled), so skipped systems can't hide.

Schema per line of `results/reasoning_ops/op_labels.jsonl`:
```json
{"qid":0,"reasoning_operation":"B",
 "systems":{"Cardiovascular":"N","Respiratory":"N", "...":"...", "Infectious":"Y"},"model":"..."}
```
(Rows with `"parse_fail":true` failed after retries and should be excluded from analysis.)

## Option A — free, on AIAU/local (recommended; no data egress)
vLLM serves an OpenAI-compatible endpoint, so the same script works:
```bash
python -m vllm.entrypoints.openai.api_server --model Qwen2.5-72B-Instruct --port 8000 &
export OPENAI_BASE_URL=http://localhost:8000/v1
export OPENAI_API_KEY=EMPTY
export CLASSIFIER_MODEL=Qwen2.5-72B-Instruct
python scripts/dataset_generation/operation_labeler.py \
  --dataset data/datasets/medqa_full_combined.json \
  --output results/reasoning_ops/op_labels.jsonl
# resumable: safe to interrupt/re-run. Test first with --limit 50.
```

## Option B — hosted API (cheapest sane: gpt-4o-mini, ~$1–2 for all 12,723)
```bash
export OPENAI_API_KEY=...            # do NOT hardcode/commit
export OPENAI_BASE_URL=https://api.openai.com/v1
export CLASSIFIER_MODEL=gpt-4o-mini
python scripts/dataset_generation/operation_labeler.py
```

## Option C — gpt-5.4-mini via Batch API (chosen; ~$8, 50% off)
Batch only runs on the hosted OpenAI API (not vLLM). GPT-5 reasoning params are preset
(`reasoning_effort=none` — gpt-5.4-mini does NOT accept 'minimal'; valid: none/low/medium/high/xhigh —
and `max_completion_tokens=512`). The org has a **2,000,000 enqueued-token
cap**, and the full set is ~10M tokens, so it is auto-split into ~11 chunks submitted SEQUENTIALLY.
```bash
pip install --upgrade openai                 # need >=1.x (modern client + Batch support)
export OPENAI_API_KEY=sk-...                  # your env only — never hardcoded/committed
export CLASSIFIER_MODEL=gpt-5.4-mini          # confirm exact id in your account's model list

python scripts/dataset_generation/batch_label.py build   # -> batch_input.jsonl (no key needed)
python scripts/dataset_generation/batch_label.py auto     # split + submit/poll/append, looped
```
`auto` submits chunk_000, polls every 30s until it completes, appends parsed rows to
`op_labels.jsonl`, then does chunk_001, etc. — never exceeding the enqueue cap.
- **Keep the terminal open** while it runs (or use `nohup ... &`). It's resumable: if interrupted,
  re-run `auto` and it skips finished chunks and continues (state in `.chunk_state.json`).
- Requires a positive **prepaid credit balance** AND project/org spend limits above the cost
  (a "billing hard limit reached" error means add credits, not just raise the limit).
- `parse_fail` rows (model omitted a system / bad JSON) are flagged; re-run those with
  `operation_labeler.py` (resumes) afterward.
- Tunables via env: `ENQUEUE_BUDGET` (default 1.7M, keep < your cap), `MAX_COMPLETION_TOKENS`,
  `REASONING_EFFORT`, `POLL_SECONDS`. `build`/`split`/`submit`/`poll`/`fetch` remain available for
  manual/diagnostic single-chunk use.

## Validate (always do this)
Hand-label ~150 stratified items (oversample B vs F — the headline contrast) into the same
schema at `results/reasoning_ops/gold_op_labels.jsonl`, then:
```bash
python scripts/dataset_generation/score_op_labels.py \
  --pred results/reasoning_ops/op_labels.jsonl \
  --gold results/reasoning_ops/gold_op_labels.jsonl
# reasoning_operation -> accuracy + Cohen's kappa
# organ systems       -> micro/macro P/R/F1 + mean Jaccard (multi-label)
```

## Then (no GPU)
- `analysis/op_accuracy.py` — per-operation accuracy + Wilson CIs from existing `results/base_runs_full/`.
- `analysis/asymmetry_mixed_model.py` — forward(F)-vs-backward(B) contrast (the headline test).
These run on data already in the repo; see `PLAN.md` §6 and §8.
