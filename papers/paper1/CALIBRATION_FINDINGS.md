# Paper 1 — Calibration Findings

## EXP1 — Qwen2.5-7B temperature curve in the canonical *logprob* environment

We adopted the logprob serving environment as canonical for Paper 1's greedy (t=0.0)
baseline. In that environment Qwen2.5-7B scores **59.71%** greedy, versus **67.96%** in the
older base-run environment (a model-snapshot / vLLM-version difference; the other four models
agree across environments to <1pp). The original t=0.3 / t=0.7 numbers for Qwen2.5-7B came
from the *old* environment (66.44% / 57.67%), which made its temperature curve non-monotonic
relative to the new 59.71% greedy. We therefore re-ran **only Qwen2.5-7B at t=0.3 and t=0.7,
3 runs each, in the logprob environment** using the exact same model / vLLM / dtype /
seed-handling as the greedy logprob run (`run_qwen25_7b_logprobs_temp.sbatch`; jobs 18934–18939).

### Result (focused-1030 set, n=1030, k=3 runs per temperature)

| temp | run accuracies        | mean   | answer-instability¹ |
|------|-----------------------|--------|---------------------|
| 0.0  | 59.71 / 59.71 / 59.71 | 59.71% | 0.00%  (deterministic) |
| 0.3  | 56.41 / 57.86 / 59.22 | 57.83% | 29.22% |
| 0.7  | 50.19 / 53.59 / 54.17 | 52.65% | 58.45% |

- **Temperature drop (t=0.0 → t=0.7): 59.71% → 52.65% = −7.06 pp.**
- **Monotonic degradation now holds** in the canonical environment: 59.71 ≥ 57.83 ≥ 52.65.
  (It did not hold before, because the t=0.3/0.7 points were from the higher-scoring old
  environment.) Answer-instability rises monotonically with temperature (0% → 29.22% → 58.45%).

¹ Answer-instability = % of questions where the 3 independent runs do **not** all predict the
same letter (Paper 1, Table 5 definition). t=0.0 is exactly reproducible across the 3 runs.

### Provenance (reproducibility appendix)
- Served model: `Qwen/Qwen2.5-7B`, HF snapshot `d149729398750b98c0af14eb82c78cfe92750796`
- vLLM 0.14.1, transformers 4.57.6, torch 2.9.1+cu128, dtype bf16, TP=2, max-model-len 4096
- Fresh random seed per job launch (matches the base-run protocol that surfaces instability)
- Results: `results/base_runs_logprobs/qwen25_7b/temp{0.0,0.3,0.7}_run{1,2,3}_results.json`
