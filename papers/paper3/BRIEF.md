You are my senior PhD research advisor, biomedical AI collaborator, neuro-symbolic AI expert, and scientific writing partner. I am developing Paper 3 from my MedQA2026 research project.

Paper 1 is intended to be a benchmark and empirical evaluation paper focused on base language models, medical reasoning categories, model scale, temperature variation, and run-to-run stability.

Paper 2 is intended to focus on neuro-symbolic medical QA using UMLS grounding, symbolic verification, Chain-of-Verification, contradiction detection, grounding coverage, and the concept mismatch problem.

Paper 3 should be the most ambitious paper in the sequence. It should propose and evaluate an agentic neuro-symbolic differential diagnosis framework for MedQA-style medical reasoning. The core idea is to move beyond static multiple-choice answer selection and toward adaptive, executable, evidence-guided clinical reasoning.

This paper should be inspired by the attached Algorithm 2 Diagnosis concept, which frames diagnosis as a hierarchical coarse-to-fine reasoning process rather than flat classification. In that document, the system first estimates coarse contextual cues, narrows the hypothesis space, selectively evaluates biomarkers, maintains a belief state over competing diagnoses, accumulates probabilistic evidence, and produces interpretable evidence traces rather than opaque predictions. It also emphasizes adaptive selection of evidence functions, reasoning over supportive and contradictory evidence, uncertainty reduction, and minimum-redundancy maximum-relevance style evidence selection. :contentReference[oaicite:0]{index=0}

For Paper 3, translate that concept from human motion diagnosis to MedQA-style clinical reasoning.

The central thesis of Paper 3 should be:

Medical QA should not be treated as a single-pass answer-selection problem. A more faithful formulation is adaptive differential reasoning: the system should parse the clinical vignette, identify the reasoning task, generate candidate hypotheses, select the most informative evidence functions, ground and verify evidence using biomedical knowledge, update belief over candidates, and produce an interpretable evidence trace before selecting the final answer.

Repository context:
- Repository: https://github.com/tadsligar/MedQA2026
- Dataset: focused balanced MedQA-style dataset with approximately 1,030 questions across five reasoning categories:
  1. Clinical Findings
  2. Diagnosis
  3. Mechanism / Pathophysiology
  4. Next Step / Workup
  5. Treatment / Management
- Paper 1 evaluates base models across reasoning category, temperature, model family, and model scale.
- Paper 2 studies UMLS grounding, symbolic verification, concept mismatch, Chain-of-Verification, and hybrid neuro-symbolic scoring.
- Paper 3 should use those foundations to design an adaptive agentic reasoning system.

The framework should include:
- Coarse question understanding
- Reasoning category identification
- Clinical evidence extraction
- Candidate answer/hypothesis representation
- UMLS-grounded evidence graph
- Category-specific reasoning modules
- Adaptive function/tool selection
- Symbolic support and contradiction evaluation
- Belief-state update over answer choices or candidate diagnoses
- Redundancy-aware evidence selection
- Chain-of-Verification or contradiction auditing
- Final answer selection with explanation trace
- Error and uncertainty analysis

The paper should avoid claiming clinical deployment readiness. It should be framed as a controlled MedQA-style evaluation of agentic neuro-symbolic reasoning.

Your task:
Generate a complete research-paper plan for Paper 3, including title options, abstract, research questions, hypotheses, method design, algorithm specification, experiments, metrics, tables/figures, ablations, case studies, limitations, publication strategy, and skeleton paper draft.

The paper should answer questions such as:
1. Can adaptive evidence acquisition improve MedQA-style medical reasoning compared with static prompting?
2. Does category-specific reasoning improve over a one-size-fits-all LLM reasoning pipeline?
3. Can an agentic system select useful evidence functions based on the clinical context and current uncertainty?
4. Does neuro-symbolic belief updating improve answer accuracy, calibration, or explanation quality?
5. Can redundancy-aware evidence selection reduce unnecessary or misleading evidence accumulation?
6. Can symbolic contradiction detection improve final answer selection or at least identify likely errors?
7. Are adaptive agentic reasoning gains concentrated in certain categories, such as diagnosis, workup, or treatment?
8. What failure modes remain when LLM planning is combined with symbolic grounding?
9. How does this framework move MedQA from answer selection toward differential diagnosis?

Please produce the following:

1. A concise one-paragraph positioning statement.
   Include:
   - What Paper 3 is about
   - Why adaptive diagnostic reasoning matters
   - Why static multiple-choice answering is insufficient
   - How this builds on Papers 1 and 2
   - What the main contribution is

2. Seven strong paper-title options.
   Include:
   - One title focused on agentic neuro-symbolic reasoning
   - One title focused on differential diagnosis
   - One title focused on adaptive evidence acquisition
   - One title focused on executable diagnostic reasoning
   - One title focused on MedQA specifically
   - One title suitable for a biomedical informatics venue
   - One title suitable for a neuro-symbolic AI venue

Possible themes:
- Agentic Neuro-Symbolic Differential Diagnosis for Medical Question Answering
- Adaptive Evidence Acquisition for MedQA Reasoning
- Executable Diagnostic Reasoning with Biomedical Knowledge Graphs
- From Answer Selection to Differential Diagnosis in Medical QA
- Category-Aware Neuro-Symbolic Agents for Clinical Reasoning

3. A polished draft abstract of 250–350 words.
   The abstract should include:
   - Motivation: medical QA is commonly evaluated as static answer selection
   - Gap: static prompting does not model differential diagnosis or adaptive evidence gathering
   - Prior foundation: category-balanced MedQA evaluation and UMLS-grounded verification
   - Method: an agentic neuro-symbolic framework that selects evidence functions, grounds findings, evaluates support/contradiction, updates beliefs, and produces evidence traces
   - Dataset: balanced MedQA-style dataset across five reasoning categories
   - Experiments: compare static LLM prompting, category-specific prompting, UMLS-grounded verification, and adaptive agentic reasoning
   - Metrics: accuracy, category-level performance, evidence efficiency, contradiction detection, stability, explanation trace quality, and error prediction
   - Expected contribution: show whether adaptive evidence acquisition improves robustness and interpretability, and characterize where it fails
   - Careful caveat: this is not clinical decision support

4. Research questions and hypotheses.
   Format as:
   RQ1:
   H1:
   RQ2:
   H2:
   etc.

   Include at least 8 research questions.
   Include hypotheses about:
   - adaptive evidence acquisition outperforming static prompting
   - category-specific reasoning improving category-level performance
   - belief updates improving final answer selection
   - contradiction scores predicting wrong answers
   - evidence redundancy reduction improving efficiency
   - the agent helping diagnosis/workup more than clinical findings
   - symbolic grounding being helpful but limited by concept mismatch
   - agentic planning introducing new failure modes

5. Paper outline with section-by-section content:
   - Introduction
   - Related Work
   - Background and Motivation
   - Dataset
   - Agentic Neuro-Symbolic Framework
   - Algorithm
   - Experimental Design
   - Results
   - Ablation Studies
   - Case Studies
   - Discussion
   - Limitations
   - Future Work
   - Conclusion
   - Appendix / Reproducibility

For each section, give:
   - Purpose of the section
   - Key claims to make
   - Specific content to include
   - Tables or figures that belong there

6. Introduction draft structure.
   Provide a detailed paragraph-by-paragraph plan.
   Include:
   - Paragraph 1: LLMs perform well on medical QA but often reduce reasoning to answer selection
   - Paragraph 2: clinical reasoning is closer to differential diagnosis and adaptive evidence evaluation
   - Paragraph 3: MedQA-style questions contain heterogeneous reasoning tasks
   - Paragraph 4: Paper 1 showed category and temperature-dependent behavior
   - Paragraph 5: Paper 2 showed grounding and verification help but static symbolic scoring is limited
   - Paragraph 6: need for an adaptive agentic neuro-symbolic reasoning system
   - Paragraph 7: proposed framework
   - Paragraph 8: summary of experiments
   - Paragraph 9: contributions

Also write 4–6 polished contribution bullets suitable for the introduction.

7. Related work plan.
   Identify the major clusters of related work:
   - Medical question answering and MedQA benchmarks
   - Clinical reasoning and differential diagnosis
   - LLMs for medical reasoning
   - Agentic LLM systems
   - Neuro-symbolic AI
   - Biomedical knowledge graphs and UMLS
   - Chain-of-Verification and self-refinement
   - Tool-using LLMs
   - Adaptive computation and active feature selection
   - Probabilistic reasoning and belief updates
   - Explanation faithfulness and clinical AI interpretability

For each cluster:
   - Explain what to cite
   - Explain how to position this paper
   - Identify the gap this paper addresses

8. Conceptual framing.
   Explain how to translate the attached Algorithm 2 Diagnosis framework into MedQA.

   Create a mapping table:

   Motion diagnosis framework:
   - video segment
   - subject/body-region visibility
   - motion biomarker
   - gait asymmetry
   - tremor marker
   - latent neurological factor
   - diagnostic graph
   - adaptive biomarker selection
   - probabilistic evidence accumulation
   - mRMR feature selection
   - clip diagnostic score
   - interpretable evidence trace

   MedQA framework:
   - clinical vignette
   - available evidence type
   - clinical finding or relation
   - asymmetric symptom pattern / focal deficit
   - lab abnormality / symptom pattern / mechanism
   - candidate diagnosis, mechanism, workup, or treatment
   - UMLS-grounded clinical reasoning graph
   - adaptive evidence-function selection
   - answer-choice belief update
   - redundancy-aware evidence selection
   - candidate answer posterior
   - structured rationale with support/contradiction trace

9. Methodology: full framework design.
   Design the complete agentic neuro-symbolic framework.

   Include the following modules:

   A. Case parser
      - Extract clinical vignette
      - Extract answer choices
      - Extract age, sex, chief complaint, symptoms, signs, labs, imaging, medications, risk factors, timing, and negation
      - Identify what evidence is present and what evidence is missing

   B. Reasoning category classifier
      - Classify question as Clinical Findings, Diagnosis, Mechanism/Pathophysiology, Next Step/Workup, or Treatment/Management
      - Optionally allow multi-label category assignment
      - Use category to select reasoning policy

   C. Candidate hypothesis generator
      - Convert answer choices into candidate hypotheses
      - For diagnosis questions, candidates are diseases
      - For mechanism questions, candidates are causal mechanisms
      - For treatment questions, candidates are interventions
      - For workup questions, candidates are diagnostic next steps
      - For clinical findings questions, candidates are expected manifestations

   D. UMLS grounding module
      - Ground stem findings and answer choices to UMLS concepts
      - Capture CUIs, semantic types, aliases, relation candidates, and mapping confidence
      - Detect unmapped or weakly mapped concepts
      - Preserve negation and uncertainty

   E. Evidence-function library
      Define callable functions such as:
      - check_demographic_plausibility()
      - check_symptom_support()
      - check_lab_support()
      - check_temporal_consistency()
      - check_pathophysiology_chain()
      - check_disease_finding_relation()
      - check_treatment_indication()
      - check_treatment_contraindication()
      - check_next_best_test()
      - check_mechanism_consistency()
      - check_answer_semantic_type()
      - check_contradictions()
      - check_distractor_similarity()
      - estimate_grounding_coverage()
      - estimate_evidence_redundancy()
      - summarize_supporting_evidence()
      - summarize_contradictory_evidence()

   F. Agent controller / planner
      - Maintains current belief over candidate answers
      - Selects next evidence function based on uncertainty, category, expected information gain, grounding availability, and redundancy
      - Stops when confidence threshold, evidence budget, or maximum iterations are reached
      - Records each step in an evidence trace

   G. Belief-state update module
      - Initialize prior over answer choices
      - Update scores based on evidence support, contradiction, semantic compatibility, and LLM judgment
      - Use a transparent scoring equation or probabilistic approximation
      - Track uncertainty and margin between candidates
      - Allow symbolic evidence to penalize or boost candidates

   H. Redundancy-aware evidence selection
      - Use a minimum-redundancy maximum-relevance style strategy
      - Prioritize evidence functions that distinguish top competing candidates
      - Avoid repeated evidence that supports all options equally
      - Penalize redundant evidence already considered

   I. Verification and contradiction auditor
      - Verify generated claims against grounded evidence
      - Detect internal contradictions
      - Detect answer-choice incompatibilities
      - Detect unsupported rationale claims
      - Detect conflicts with negated findings
      - Produce warning flags

   J. Final decision module
      - Select final answer
      - Produce confidence proxy
      - Produce ranked candidate list
      - Produce support/contradiction table
      - Produce concise final rationale
      - Produce evidence trace

10. Algorithm specification.
   Write a clear algorithm for the method.

   Include:
   - Inputs
   - Outputs
   - Initialization
   - Candidate generation
   - Evidence-function selection loop
   - Belief update
   - Redundancy penalty
   - Stopping criteria
   - Verification pass
   - Final answer selection

   Provide pseudocode suitable for a research paper.

   The pseudocode should look like:

   Algorithm 1: Agentic Neuro-Symbolic Medical Reasoning
   Input: clinical vignette x, answer choices A, evidence budget B, knowledge graph K
   Output: final answer a*, ranked candidates, evidence trace T

   Steps:
   1. Parse case
   2. Classify reasoning category
   3. Ground concepts
   4. Initialize candidate beliefs
   5. For t = 1 to B:
       a. Estimate uncertainty
       b. Select evidence function using expected utility
       c. Execute function
       d. Update belief
       e. Append to trace
       f. Stop if confidence or margin threshold met
   6. Run verifier
   7. Adjust beliefs or flag contradictions
   8. Return final answer and trace

   Also provide a mathematical scoring formulation:
   - support score
   - contradiction score
   - grounding confidence
   - redundancy penalty
   - belief update
   - expected utility for next evidence function
   - final candidate score

11. Experimental conditions.
   Define all systems to compare:

   Baselines:
   - Random baseline
   - Static base LLM zero-shot
   - Static base LLM chain-of-thought
   - Static instruction-following prompt if available
   - Self-consistency or repeated sampling
   - Category-specific prompt only
   - UMLS symbolic-only scorer
   - UMLS-grounded LLM prompt
   - Chain-of-Verification system from Paper 2

   Agentic systems:
   - Agent without UMLS
   - Agent with UMLS grounding but no belief update
   - Agent with belief update but no contradiction auditor
   - Agent with contradiction auditor but no adaptive selection
   - Full adaptive neuro-symbolic agent
   - Full agent with fixed evidence budget
   - Full agent with dynamic stopping
   - Oracle upper-bound evidence selector, if feasible

For each condition:
   - Define the system
   - Explain what it tests
   - Explain what outcome would support or weaken the paper’s thesis

12. Metrics.
   Define all metrics the paper should report:

   Performance:
   - Overall accuracy
   - Category-specific accuracy
   - Accuracy by model
   - Accuracy by evidence budget
   - Accuracy by reasoning depth
   - Majority-vote accuracy if repeated runs are used

   Agentic reasoning:
   - Average number of evidence functions called
   - Evidence efficiency
   - Stopping depth
   - Function selection distribution
   - Adaptive vs fixed-policy improvement
   - Information gain per step
   - Candidate margin improvement

   Neuro-symbolic grounding:
   - Grounding coverage
   - Answer-choice grounding rate
   - UMLS relation support
   - Semantic-type compatibility
   - Concept mismatch rate
   - Unmapped concept rate

   Verification:
   - Contradiction score
   - Unsupported-claim rate
   - Verification flags per question
   - Verifier precision/recall if manually labeled
   - Error prediction AUROC
   - Revision success and harm rates

   Explanation quality:
   - Evidence trace completeness
   - Support/contradiction trace quality
   - Rationale faithfulness proxy
   - Human-rated interpretability if feasible
   - Trace length and redundancy

   Robustness:
   - Run-to-run answer stability
   - Sensitivity to temperature
   - Sensitivity to evidence budget
   - Sensitivity to category misclassification

For each metric:
   - Define it
   - Explain why it matters
   - Explain how to compute it
   - Explain how to interpret it

13. Statistical analysis plan.
   Recommend appropriate analyses:
   - Bootstrap confidence intervals for accuracy
   - McNemar tests for paired comparisons
   - Paired bootstrap for category-level improvements
   - Logistic regression predicting correctness from grounding, contradiction, and belief-margin features
   - AUROC/AUPRC for verifier-based error prediction
   - ANOVA or mixed-effects modeling for method/category interactions
   - Correlation between evidence budget and accuracy
   - Analysis of diminishing returns from additional evidence calls
   - Ablation significance testing
   - Multiple-comparison correction where appropriate

Explain how to avoid overclaiming if improvements are modest, category-specific, or limited to interpretability rather than accuracy.

14. Tables and figures.
   Propose a full set of publication-quality tables and figures.

   Include at minimum:

   - Table 1: Dataset category distribution
   - Table 2: Evidence-function library
   - Table 3: Experimental system variants
   - Table 4: Overall accuracy by method
   - Table 5: Category-specific accuracy by method
   - Table 6: Agentic efficiency metrics
   - Table 7: Ablation study
   - Table 8: Verification and grounding metrics
   - Table 9: Failure mode taxonomy

   - Figure 1: Overall framework diagram
   - Figure 2: Mapping from clinical vignette to evidence trace
   - Figure 3: Agent control loop
   - Figure 4: Belief update over candidate answers for one example
   - Figure 5: Accuracy vs evidence budget
   - Figure 6: Category-level heatmap of agentic gains
   - Figure 7: Function selection distribution by reasoning category
   - Figure 8: Contradiction score vs error probability
   - Figure 9: Example evidence trace for a diagnosis question
   - Figure 10: Ablation performance chart

For each table/figure:
   - Describe what it should show
   - State the intended takeaway
   - Draft a possible caption

15. Ablation studies.
   Propose detailed ablations:

   - Remove UMLS grounding
   - Remove category classifier
   - Replace adaptive evidence selection with fixed evidence sequence
   - Remove belief updates
   - Remove contradiction auditor
   - Remove redundancy penalty
   - Remove semantic-type compatibility
   - Remove pathophysiology checker
   - Remove treatment contraindication checker
   - Use LLM-only evidence functions
   - Use symbolic-only evidence functions
   - Use random evidence-function selection
   - Use full evidence evaluation with no adaptivity
   - Use adaptive selection but no final verification
   - Use verification but no answer revision
   - Vary evidence budget from 1 to N

For each ablation:
   - What it tests
   - Expected result
   - How it supports the paper’s argument
   - What interpretation to make if the result is negative

16. Agent policies.
   Define several possible evidence-selection policies:

   A. Fixed policy
      - Always run the same evidence functions in the same order

   B. Category policy
      - Select functions based only on question category

   C. Uncertainty policy
      - Select functions based on top-candidate margin or entropy

   D. Expected utility policy
      - Select function based on expected information gain and grounding availability

   E. Redundancy-aware policy
      - Select function based on relevance to top candidates minus redundancy with prior evidence

   F. LLM planner policy
      - Ask the LLM controller to choose the next function with structured justification

   G. Hybrid policy
      - Combine symbolic utility score with LLM planner recommendation

For each policy:
   - Define it
   - Explain how to implement it
   - Explain what hypothesis it tests
   - Explain how to evaluate it

17. Belief update design.
   Provide several candidate formulations:

   A. Simple additive score
      score(candidate) += support - contradiction

   B. Weighted neuro-symbolic score
      score(candidate) = LLM_score + alpha * symbolic_support - beta * contradiction + gamma * grounding_confidence

   C. Bayesian-style update
      prior over candidates updated by likelihood of evidence under each candidate

   D. Learning-to-rank model
      train a lightweight model over evidence features to rank answer choices

   E. Calibration-aware score
      combine belief margin, grounding coverage, and contradiction flags into confidence proxy

For each:
   - Define the formulation
   - State pros and cons
   - Recommend which version to use first for Paper 3
   - Explain what can be saved for future work

18. Evidence-function library detail.
   Write detailed descriptions for each evidence function.

   Include:
   - Function name
   - Input
   - Output
   - Applies to which reasoning categories
   - Uses UMLS or LLM or both
   - Example
   - Potential failure modes

Include at least these functions:
   - demographic plausibility
   - symptom support
   - lab support
   - temporal consistency
   - mechanism consistency
   - diagnosis-finding relation
   - treatment indication
   - treatment contraindication
   - next-best-test
   - expected clinical finding
   - answer semantic type compatibility
   - negation conflict
   - distractor similarity
   - grounding coverage
   - contradiction audit
   - evidence redundancy

19. Case studies.
   Propose 5 qualitative case studies:

   - Diagnosis case where adaptive evidence selection improves answer
   - Treatment case where contraindication checking prevents wrong answer
   - Workup case where next-best-test reasoning helps
   - Mechanism case where pathophysiology chain reasoning helps
   - Failure case where the agent selects misleading evidence or UMLS grounding fails

For each case study:
   - What to show
   - How to display the vignette, choices, evidence calls, belief updates, contradiction flags, and final answer
   - What lesson the reader should take away

20. Failure-mode taxonomy.
   Develop a taxonomy for agentic neuro-symbolic failures:

   - Incorrect category classification
   - Bad initial candidate representation
   - UMLS concept grounding error
   - Concept mismatch
   - Missing knowledge graph relation
   - Overweighting symbolic evidence
   - Overweighting LLM judgment
   - Redundant evidence loop
   - Misleading evidence function
   - Contradiction false positive
   - Contradiction false negative
   - Belief update instability
   - Premature stopping
   - Excessive evidence gathering
   - Correct answer harmed by revision
   - Incorrect final answer despite good evidence trace
   - Correct final answer with unfaithful evidence trace

For each:
   - Define it
   - Explain how to detect it
   - Explain why it matters
   - Explain possible mitigation

21. Core contribution claims.
   Write 4–6 precise contribution bullets.
   They should be defensible and non-hypey.
   Avoid clinical deployment claims.
   Focus on:
   - adaptive evidence acquisition
   - category-aware reasoning
   - neuro-symbolic belief updates
   - interpretable evidence traces
   - empirical evaluation against static baselines
   - characterization of agentic failure modes

22. Limitations section.
   Write a thoughtful limitations plan.
   Include:
   - MedQA is exam-style and not equivalent to real clinical practice
   - Multiple-choice answer choices simplify candidate generation
   - Agentic tool calls may increase computational cost
   - UMLS is incomplete and not a full causal reasoning engine
   - LLM-generated rationales may not be faithful
   - Belief update weights may require tuning
   - Evidence-function outputs may be noisy
   - Adaptive policies may overfit to dataset structure
   - Concept mismatch remains unresolved
   - No patient-safety or clinical deployment claims

23. Future work section.
   Extend beyond Paper 3:
   - Open-ended differential diagnosis without answer choices
   - Retrieval-augmented medical literature grounding
   - integration with SNOMED CT, RxNorm, MeSH, and clinical guidelines
   - learning evidence-selection policies
   - expert clinician evaluation of evidence traces
   - application to real clinical notes
   - uncertainty-aware abstention
   - causal medical knowledge graphs
   - multi-agent specialist reasoning
   - patient-safety evaluation

24. Publication strategy.
   Recommend suitable venue types:
   - ML for Health
   - biomedical informatics conferences
   - medical AI workshops
   - neuro-symbolic AI workshops
   - knowledge representation venues
   - arXiv-first release
   - later journal extension

Also recommend:
   - minimum experiment package needed for a workshop paper
   - stronger experiment package needed for a full conference paper
   - additions needed for a journal paper

25. Concrete next steps from the repo.
   Give me a checklist of artifacts to generate:

   - finalized Paper 1 benchmark results
   - finalized Paper 2 UMLS verifier results
   - category labels
   - question-level outputs from baselines
   - LLM rationale traces
   - UMLS grounding logs
   - evidence-function outputs
   - agent trace logs
   - belief-update logs
   - contradiction flags
   - function selection logs
   - evidence budget experiments
   - ablation results
   - manually reviewed case studies
   - failure-mode annotations
   - prompt templates
   - config files
   - reproducibility scripts
   - result aggregation notebooks
   - figure-generation scripts

26. Finally, produce a draft skeleton paper in this format:

   Title
   Abstract

   1. Introduction
   2. Related Work
   3. Background and Motivation
   4. Dataset
   5. Agentic Neuro-Symbolic Framework
   6. Algorithm
   7. Experimental Design
   8. Results
   9. Ablation Studies
   10. Case Studies
   11. Discussion
   12. Limitations
   13. Future Work
   14. Conclusion

For each section:
   - Include starter prose
   - Include placeholders for exact results
   - Include notes about what tables and figures to insert
   - Maintain formal academic tone

Writing style:
Use rigorous academic language. Be ambitious but careful. Do not overclaim clinical utility. Do not describe the system as ready for real diagnosis. Frame it as a controlled MedQA-style evaluation of adaptive neuro-symbolic medical reasoning.

The main message should be:
Medical QA systems should move beyond static answer selection. By treating each question as an adaptive evidence-acquisition problem, an agentic neuro-symbolic system can produce more interpretable, category-aware, and uncertainty-sensitive reasoning traces. The key research question is not merely whether the agent improves accuracy, but whether adaptive evidence selection, symbolic grounding, contradiction auditing, and belief updates reveal a more reliable path toward differential diagnostic reasoning.