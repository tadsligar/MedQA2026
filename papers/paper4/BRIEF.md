You are my senior PhD research advisor, AI/ML research collaborator, and scientific writing partner. I am developing a publication from my GitHub repository MedQA2026, which evaluates base language models on MedQA-style medical reasoning questions.

The goal is to spin off Paper 4 from this project. Paper 4 is a **conceptual + empirical** paper that reframes the "reasoning categories" of Paper 1 in a principled way: instead of surface buckets, we partition questions by the **type of inference they demand over a causal model of disease**. The central observation is that the standard MedQA categories are not all the same *kind* of reasoning, and that the difference matters.

Context:
- Repository: https://github.com/tadsligar/MedQA2026
- Project theme: evaluating and extending base-LLM medical reasoning on MedQA.
- Prior work in this repo: Paper 1 (category-balanced benchmark, decoding-temperature, run-to-run stability, scaling — empirically complete on real runs), Paper 2 (UMLS neuro-symbolic grounding & verification — design + seeds), Paper 3 (agentic differential diagnosis — design + seeds).
- Data already in hand and reusable for this paper: the full 12,723-question MedQA runs and the focused 1,030-question balanced runs, for five base models (Qwen2.5 7B/14B/32B, OLMo-3 7B/32B) at three temperatures (0.0/0.3/0.7), three runs each — i.e., per-question correctness is already available; **most of Paper 4 needs no new GPU runs.**
- A local UMLS 2025AB index (SQLite) and an organ-system gazetteer exist in the repo and can be reused for the question-structure probes.

The core idea (the thing to test and analyze):
- **Mechanism / pathophysiology** questions are *forward* reasoning over the causal model: cause → effect, applied deductively from known physiology ("how the body works"). Close to deduction / recall-and-apply.
- **Diagnosis** questions are *backward* reasoning: effect → cause. This is **abduction** (inference to the best explanation) and is harder in a specific way — it requires inverting the causal model and weighing base rates among competing explanations. (Classic medical-AI: INTERNIST/CADUCEUS modeled diagnosis as abduction.)
- **Treatment / management** questions are *interventional* reasoning (Pearl's "doing" rung): predict the effect of an action and choose the best one.
- **Clinical findings** recognition is largely *associative* (Pearl's "seeing" rung): recognize/recall an expected sign.
- Hypothesis: base LLMs are **differentially competent** across these inference types, and the asymmetry is consistent across models and interpretable — which both explains *why* aggregate accuracy hides structure and prescribes *which* symbolic scaffold should target *which* reasoning type in later neuro-symbolic work.

This paper should:
- Be honest about the central confound: in a multiple-choice format, an "abductive" question can sometimes be solved by surface pattern recognition rather than genuine inference. The paper must try to *separate reasoning from retrieval*, not assume it.
- Reuse Paper 1's verified infrastructure and statistics (Wilson intervals, McNemar/bootstrap, Holm), and Paper 1's run files, rather than re-collecting data.
- Position cleanly in the four-paper arc: Paper 4 refines Paper 1's category axis into a reasoning-operation axis and produces the *diagnostic* that motivates the targeted symbolic methods of Papers 2 and 3.

Your task:
Generate a complete research-paper plan for Paper 4, including: positioning statement; title options; draft abstract; research questions and hypotheses; the reasoning-operation taxonomy with its grounding in Peirce's inference triad and Pearl's ladder of causation; how each operation maps to an observable feature of the question (the "ask" sentence and answer-option types) so it can be labeled reproducibly; the methodology and statistical design for testing a *directional asymmetry* across inference types; the probes that separate genuine reasoning from pattern recall (differential breadth, integration depth, cue strength); metrics; tables/figures; what is computable from existing runs vs what (if anything) needs new experiments; expected contributions; limitations; and publication strategy.

Important framing:
This is a serious AI/ML + biomedical-informatics paper, not a class project. Emphasize the conceptual contribution (a principled, causal-inference-grounded taxonomy of medical-reasoning questions), methodological rigor (reproducible labeling + appropriate cross-category statistics), and the honest reasoning-vs-recall analysis. Make no claims of clinical utility.
