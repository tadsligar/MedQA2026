# Reasoning-Category Relabeling Rubric (strong-LLM annotation)

Purpose: re-assign each of the 1,030 focused-MedQA questions to one of five reasoning
categories using a single strong annotator (Claude Opus), to replace/augment the original
rule+Qwen2.5 labels. The category is determined by **what the question asks you to produce**
(the final "ask" sentence) together with **what the answer options are** (diseases vs. tests
vs. treatments vs. findings vs. mechanisms).

## Categories & decision rules
1. **Clinical Findings** — asks what you would *observe/expect*: a sign, symptom, lab value,
   imaging result, expected complication, or physical-exam finding of a (usually already
   implied) condition. Options are findings/values/manifestations.
   Cues: "most likely to show", "expected finding", "serum/level most likely closest to",
   "most likely to reveal", "complication this patient is most at risk for", "most likely
   to be elevated/decreased".
2. **Diagnosis** — asks you to *name the disease/condition or the causal entity*. Options are
   diseases/conditions/organisms.
   Cues: "most likely diagnosis", "most likely cause of this patient's condition" (options =
   diseases), "which condition/organism".
3. **Mechanism/Pathophysiology** — asks *why/how*: drug mechanism of action, biological
   pathway, pathophysiologic process. Options are mechanisms/processes/molecules.
   Cues: "mechanism of action", "second messenger", "underlying mechanism", "responsible for",
   "pathophysiology", "how does … work".
4. **Next Step/Workup** — asks what to *do next to evaluate/diagnose*: next best step, initial
   step, best initial test/investigation, most appropriate diagnostic study. Options are
   tests/diagnostic actions.
   Cues: "next step in management/workup", "most appropriate next step", "best initial test".
5. **Treatment/Management** — asks *how to treat/manage*: best treatment, definitive
   management, which drug/therapy. Options are drugs/therapies/procedures.
   Cues: "best/most appropriate treatment", "first-line therapy", "which medication", "definitive treatment".

## Tie-breakers (decide by the OPTIONS)
- "next step in management" → if options are **tests/diagnostics** → Next Step/Workup; if
  options are **treatments** → Treatment/Management.
- "most likely cause" → options are **diseases/organisms** → Diagnosis; options are
  **mechanisms/processes** → Mechanism/Pathophysiology.
- "most appropriate response by the physician" / ethics / consent / disclosure / prognosis /
  pure epidemiology → does not fit the five; label **Other** (expected to be rare; reported
  separately, not forced into a clinical category).

## Output
Per question: `qid, category, confidence ∈ {high, med, low}, reason (≤12 words)`.
`category` ∈ {Clinical Findings, Diagnosis, Mechanism/Pathophysiology, Next Step/Workup,
Treatment/Management, Other}. Written to `results/category_relabel/opus_labels.jsonl`.

## Downstream
- Added to the dataset as `category` (primary); the prior label kept as `category_legacy`.
- Agreement between the two annotators is reported (confusion matrix); per-category counts
  will differ from the original 206/category and are reported as-is (Wilson CIs handle
  unequal n). No model re-runs needed — only CPU per-category analysis is recomputed.
