# MedQA2026 — Execution Plan (dependency-ordered)

One checklist to run every experiment across Papers 1–3. Each step lists **where it runs**
(AIAU GPU / CPU / local 4090), its **prerequisites**, the **command**, and the **outputs +
paper placeholders** it fills. Steps marked ✅ are already done.

Conventions
- AIAU project dir: `/aiau010_scratch/tzs0128/projects/MedQA2026`; conda env `medqa`;
  partition `general`. Run all commands from the **repo root**.
- 32B models need `--gres=gpu:2` (AIAU). 7B fits a 24 GB 4090; 14B needs ~28 GB bf16
  (AIAU or quantized locally). Pure-symbolic / analysis steps are **CPU-only**.
- Analysis scripts are GPU-free, self-validate, and skip missing inputs — safe to re-run anytime.

---

## Stage 0 — Already done ✅
- **Paper 1 base runs** (5 models × 3 temps × 3 runs) → `results/base_runs/`. Verified.
- **Paper 1 analysis** → `papers/paper1/{tables,figures}` + `RESULTS.md`. Verified.
- **Paper 2 EXP1–EXP3 symbolic core** (you ran locally) → UMLS index built (9.1M terms,
  2.06M relations), grounding (coverage 0.195), symbolic scorers (overlap 25.6 / relation
  23.2 / tfidf 24.5 %). → `papers/paper2/tables/exp3_symbolic_*.csv`. **Fills EXP2/EXP3.**

---

## Stage 1 — Paper 1 EXP1 logprobs  ⟶ unlocks calibration AND the agent's LLM signal
**Run:** AIAU GPU (32B needs gpu:2) · **Prereq:** base runs (done).
This is the highest-leverage next step: its `option_probs` feed Paper 1 calibration, Paper 2
EXP5/EXP7, and the Paper 3 agent.
```bash
for m in qwen25_7b qwen25_14b qwen25_32b olmo3_7b olmo3_32b; do
  sbatch slurm/logprobs/run_${m}_logprobs.sbatch
done
python papers/paper1/analysis/compute_calibration.py     # GPU-free, after jobs finish
```
**Outputs:** `results/base_runs_logprobs/<model>/temp0.0_run1_results.json`;
`papers/paper1/tables/calib_*.csv`; `figures/fig7_reliability.png`.
**Fills:** Paper 1 `[TBD-EXP1]` (ECE, reliability, confidence–stability r). **Check**
`calib_selfcheck.csv`: re-run acc must match verified numbers.

## Stage 2 — Paper 1 EXP2–EXP5 (independent; run anytime after base runs)
**Run:** AIAU GPU.
```bash
# EXP2 instruct (confirm -Instruct HF IDs first!)
for m in qwen25_7b qwen25_14b qwen25_32b olmo3_7b olmo3_32b; do
  sbatch slurm/instruct/run_${m}_instruct.sbatch; done
python papers/paper1/analysis/compute_instruct_comparison.py
# EXP3/4/5 variants
sbatch slurm/variants/exp3_promptablation_qwen25_14b.sbatch
sbatch slurm/variants/exp3_promptablation_olmo3_32b.sbatch
sbatch slurm/variants/exp4_cotvsdirect_qwen25_14b.sbatch
sbatch slurm/variants/exp5_selfconsistency_qwen25_14b.sbatch
python papers/paper1/analysis/compute_variants.py
```
**Fills:** Paper 1 `[TBD-EXP2..EXP5]`. → **Paper 1 complete.**

---

## Stage 3 — Paper 2 hybrid/verification layer  (needs Stage 1 logprobs + UMLS index)
### 3a. GPU-free (CoVe heuristic, rerank, hybrid, aggregate)
**Run:** AIAU CPU or local.
```bash
sbatch slurm/hybrid/run_hybrid_cpu.sbatch        # uses index + Stage-1 logprobs
```
**Outputs:** `results/ns/{cove,verifier_rerank,hybrid}/*`;
`papers/paper2/tables/table3_method_comparison.csv`. **Fills EXP5, EXP6(heuristic), EXP7.**

### 3b. LLM parts (UMLS-in-prompt, CoVe LLM proposer)
**Run:** AIAU GPU (or local 4090 for 7B/14B).
```bash
sbatch slurm/hybrid/run_hybrid_llm.sbatch                         # Qwen2.5-14B
MODEL=Qwen/Qwen2.5-32B KEY=qwen25_32b TP=2 sbatch slurm/hybrid/run_hybrid_llm.sbatch
python papers/paper2/analysis/compute_hybrid.py
```
**Fills EXP4, EXP6(LLM).** → **Paper 2 core complete** (EXP8 concept-mismatch + EXP10
verifier-label review are manual/clinical, optional for first submission).

---

## Stage 4 — Paper 3 agent  (needs UMLS index + Stage 1 logprobs; Paper 2 modules reused)
### 4a. GPU-free (policies, belief variants, 14 ablations, budget sweep)
**Run:** AIAU CPU or local.
```bash
sbatch slurm/agent/run_agent_cpu.sbatch
```
**Outputs:** `results/agent/{eval,ablations,budget}/*`;
`papers/paper3/tables/agent_*.csv` (vs LLM 73.4% / oracle 86.0%). **Fills EXP4,5,8,9.**

### 4b. LLM-planner policy
**Run:** AIAU GPU (or local 4090).
```bash
sbatch slurm/agent/run_agent_llm.sbatch
python papers/paper3/analysis/compute_agent.py
```
**Fills EXP4 (llm_planner).** EXP1 (category-classifier eval), EXP2 (candidate grounding
rate), EXP7 (error-prediction AUROC), and EXP10 (case studies + failure annotation) draw from
the same agent traces / Paper 2 grounding — add as needed for the full paper.

---

## Stage 5 — Rebuild the manuscripts with real numbers
After each paper's tables are populated, refresh prose placeholders and regenerate PDFs:
```bash
python papers/paper1/analysis/build_pdf.py
python papers/paper2/analysis/build_pdf.py
python papers/paper3/analysis/build_pdf.py
```
(Replace the `[TBD-EXP#]` markers in each `DRAFT.md` with the computed values from
`papers/paper*/tables/` — every placeholder names the table/CSV that fills it.)

---

## Dependency graph (what blocks what)
```
base runs ✅
   ├── Paper 1 analysis ✅
   ├── Stage 1: logprobs ─────────────┐
   ├── Stage 2: instruct, variants    │ (Paper 1 done)
   │                                   │
UMLS index ✅ (Stage 0)                │
   ├── Stage 3a hybrid-CPU  ← needs ───┤ (logprobs)
   ├── Stage 3b hybrid-LLM             │
   └── Stage 4a agent-CPU   ← needs ───┘ (logprobs)
        └── Stage 4b agent-LLM
```
Critical path to "all three papers have real numbers": **Stage 1 → Stage 3a → Stage 4a**
(everything else is parallelizable). Stage 1 alone completes nothing less than the agent's and
hybrid's LLM signal, so run it first.

## Compute cheat-sheet
| Step | Node | Notes |
|---|---|---|
| logprobs, instruct, variants, hybrid-LLM, agent-LLM | AIAU GPU | 32B → gpu:2 |
| UMLS index, grounding, symbolic, CoVe-heuristic, rerank, hybrid(logprobs), agent-CPU, all analysis | CPU | local 4090 box or AIAU CPU |
| 7B / 14B LLM steps | local 4090 ok | `vllm serve ...` then `--vllm-url` |
| 32B LLM steps | AIAU only | 24 GB VRAM insufficient |
