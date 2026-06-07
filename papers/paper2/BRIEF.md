You are my senior PhD research advisor, biomedical AI collaborator, and scientific writing partner. I am developing Paper 2 from my MedQA2026 research project.

Paper 1 is intended to be a benchmark and empirical evaluation paper focused on base language models, model scale, medical reasoning categories, temperature variation, and run-to-run stability.

Paper 2 should build on that foundation and focus on neuro-symbolic grounding for medical question answering. Specifically, this paper should investigate how structured biomedical knowledge, especially UMLS-based concept grounding and symbolic verification, can improve or explain medical QA performance, while also identifying where purely symbolic methods fail.

The central theme of Paper 2 should be:

Pure symbolic medical knowledge is useful but brittle; LLMs are flexible but ungrounded. A hybrid neuro-symbolic system can combine the semantic abstraction of language models with the constraint, traceability, and contradiction-detection capabilities of biomedical knowledge graphs.

Context:
- Repository: https://github.com/tadsligar/MedQA2026
- Dataset: focused balanced MedQA-style dataset with approximately 1,030 questions across five medical reasoning categories:
  1. Clinical Findings
  2. Diagnosis
  3. Mechanism / Pathophysiology
  4. Next Step / Workup
  5. Treatment / Management
- Paper 1 evaluates base LLMs across model families, model sizes, decoding temperatures, and reasoning categories.
- Paper 2 should focus on the neuro-symbolic components in the repo:
  - UMLS concept grounding
  - UMLS relationship indexing
  - semantic type filtering
  - category-specific symbolic scorers
  - Hybrid UMLS Verifier
  - Chain-of-Verification pipeline
  - symbolic contradiction detection
  - grounding coverage
  - explanation verification
  - concept mismatch problem

Important conceptual motivation:
The uploaded Algorithm 2 Diagnosis document frames diagnosis as a coarse-to-fine reasoning process with structured evidence acquisition, probabilistic belief updates, interpretable evidence traces, and adaptive evaluation of biomarkers. For Paper 2, translate this idea from motion biomarkers to clinical reasoning evidence: symptoms, signs, demographics, labs, disease mechanisms, treatments, contraindications, and diagnostic workup. However, do not make Paper 2 a full agentic diagnostic system yet. That is reserved for Paper 3. Paper 2 should focus on grounding, verification, and the strengths and limitations of symbolic medical knowledge. The attached concept emphasizes that diagnostic systems should not be opaque classifiers; they should produce interpretable evidence traces and reason over supportive, contradictory, missing, and inconclusive evidence. Use that as motivation for why UMLS grounding and symbolic verification matter. :contentReference[oaicite:0]{index=0}

The major research problem:
Large language models can answer medical QA questions, but their reasoning is often difficult to audit. Biomedical knowledge graphs such as UMLS provide structured concepts and relations, but exact symbolic matching can fail when clinically equivalent ideas are expressed differently. For example, a symbolic system may fail to connect “chest discomfort” with “chest pain,” or may miss a clinically relevant relation when the wording differs from the canonical UMLS concept. This is the concept mismatch problem.

Paper 2 should investigate this problem directly.

Your task:
Generate a complete research-paper plan for Paper 2, including title options, abstract, research questions, hypotheses, methodology, experiments, metrics, tables/figures, analysis plan, limitations, publication strategy, and a skeleton draft.

The paper should answer questions such as:
1. Can UMLS grounding improve interpretability and error detection in MedQA-style medical reasoning?
2. How well do pure symbolic UMLS methods perform compared with LLM-only methods?
3. Where do symbolic methods fail due to concept mismatch, sparse relations, or overly literal matching?
4. Does hybrid LLM + UMLS verification improve answer accuracy, explanation faithfulness, or error detection?
5. Are some medical reasoning categories more amenable to symbolic grounding than others?
6. Can symbolic verification identify contradictions, unsupported claims, or weakly grounded reasoning traces?
7. Can grounding coverage or symbolic violation scores predict whether an LLM answer is likely to be wrong?
8. What does this imply for future agentic neuro-symbolic diagnostic systems?

Please produce the following:

1. A concise one-paragraph positioning statement.
   Include:
   - What this paper is about
   - Why it matters
   - What gap it fills
   - Why UMLS grounding is useful but insufficient by itself
   - What the main contribution is

2. Five strong paper-title options.
   Include:
   - One title focused on the concept mismatch problem
   - One title focused on neuro-symbolic medical QA
   - One title focused on UMLS grounding
   - One title focused on verification
   - One title suitable for a biomedical informatics venue

Possible title themes:
- The Concept Mismatch Problem in Neuro-Symbolic Medical Question Answering
- UMLS-Grounded Verification for Medical QA
- Hybrid Neuro-Symbolic Reasoning for MedQA
- Grounding and Verifying LLM Medical Reasoning with Biomedical Knowledge Graphs

3. A polished draft abstract of 200–300 words.
   The abstract should include:
   - Motivation: LLMs perform well on medical QA but are difficult to audit
   - Gap: symbolic biomedical knowledge can ground reasoning but is brittle
   - Method: UMLS grounding, symbolic scoring, Chain-of-Verification, and hybrid LLM-symbolic verification
   - Dataset: balanced MedQA-style dataset across five reasoning categories
   - Experiments: compare LLM-only, symbolic-only, and hybrid neuro-symbolic systems
   - Analysis: accuracy, grounding coverage, contradiction detection, category-level effects, and concept mismatch errors
   - Expected contribution: characterize when and why symbolic grounding helps, fails, and motivates hybrid reasoning
   - Avoid overclaiming clinical utility

4. Research questions and hypotheses.
   Format as:
   RQ1:
   H1:
   RQ2:
   H2:
   etc.

   Include at least 7 research questions.
   Include hypotheses about:
   - symbolic-only underperformance
   - hybrid improvement over symbolic-only
   - category-dependent benefit
   - grounding coverage as a predictor of correctness
   - contradiction scores as a predictor of error
   - concept mismatch as a major failure mode
   - UMLS being stronger for diagnosis/mechanism than treatment/workup, or evaluate whether that assumption holds

5. Paper outline with section-by-section content:
   - Introduction
   - Related Work
   - Background on UMLS and Neuro-Symbolic Reasoning
   - Dataset
   - Methods
   - Experimental Design
   - Results
   - Concept Mismatch Analysis
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
   - Paragraph 1: why medical QA accuracy alone is insufficient
   - Paragraph 2: why grounding and verification matter in medical reasoning
   - Paragraph 3: why biomedical knowledge graphs such as UMLS are attractive
   - Paragraph 4: why purely symbolic UMLS reasoning is brittle
   - Paragraph 5: concept mismatch problem
   - Paragraph 6: proposed hybrid neuro-symbolic framework
   - Paragraph 7: summary of experiments
   - Paragraph 8: contributions

Also write 3–5 polished contribution bullets suitable for the introduction.

7. Related work plan.
   Identify the major clusters of related work:
   - Medical question answering benchmarks
   - LLMs for clinical reasoning
   - Biomedical knowledge graphs
   - UMLS, SNOMED CT, MeSH, and concept normalization
   - Neuro-symbolic AI
   - Retrieval-augmented and knowledge-grounded medical QA
   - Chain-of-verification and self-verification
   - Explanation faithfulness and hallucination detection
   - Clinical decision support and symbolic reasoning

For each cluster:
   - Explain what to cite
   - Explain how to position this paper
   - Identify the gap this paper addresses

8. Background section on UMLS and symbolic grounding.
   Explain, in paper-ready language:
   - What UMLS is
   - What concepts, CUIs, semantic types, and relations are
   - How UMLS can be used to ground medical text
   - Why UMLS grounding can support interpretability
   - Why UMLS grounding is not the same as clinical reasoning
   - Why concept normalization is difficult
   - Why exact symbolic matching can fail
   - Why LLMs can help bridge semantic gaps
   - Why unconstrained LLMs still need grounding and verification

9. Methodology.
   Design a complete neuro-symbolic pipeline.

   Include modules such as:
   A. Question parser
      - Extract stem
      - Extract answer choices
      - Identify reasoning category
      - Extract demographics, symptoms, signs, labs, medications, history, and temporal clues

   B. UMLS concept grounding
      - Map clinical mentions to UMLS concepts
      - Store concept IDs, semantic types, aliases, and confidence scores
      - Ground both question stem and answer choices
      - Handle negation and uncertainty

   C. Symbolic candidate scoring
      - Score each answer choice based on relation support
      - Use semantic type compatibility
      - Use category-specific relationship patterns
      - Penalize unsupported or contradictory relations

   D. LLM reasoning generation
      - Generate structured rationale
      - Require evidence table
      - Require support/contradiction list for each answer option

   E. Chain-of-Verification
      - Verify claims in the rationale
      - Ground claims to UMLS concepts
      - Detect contradictions
      - Detect demographic implausibility
      - Detect semantic-type mismatches
      - Detect weak grounding coverage
      - Detect internal inconsistency

   F. Hybrid decision module
      - Combine LLM answer likelihood with symbolic support
      - Use symbolic violations as warnings or penalties
      - Optionally revise final answer
      - Produce final answer, confidence proxy, and evidence trace

   G. Output explanation
      - Final answer
      - Supporting concepts
      - Contradictory concepts
      - Grounding coverage
      - Verification flags
      - Explanation trace

10. Experimental conditions.
   Define all comparison systems:
   - Random or majority baseline
   - Pure LLM baseline
   - Pure UMLS symbolic scorer
   - TF-IDF or lexical retrieval baseline, if available
   - UMLS concept-overlap scorer
   - UMLS relation-aware scorer
   - LLM with UMLS concepts appended to prompt
   - LLM with UMLS verifier reranking
   - Chain-of-Verification without answer revision
   - Chain-of-Verification with answer revision
   - Hybrid UMLS + LLM final decision model
   - Oracle or upper-bound analysis if useful

For each condition:
   - Define the system
   - Explain what it tests
   - Explain what result would support the paper’s thesis

11. Metrics.
   Define all metrics the paper should report:
   - Overall accuracy
   - Category-specific accuracy
   - Symbolic-only accuracy
   - Hybrid accuracy
   - Improvement over LLM baseline
   - Improvement over symbolic baseline
   - Grounding coverage
   - Answer-choice grounding rate
   - Evidence support score
   - Contradiction score
   - Semantic-type compatibility score
   - Concept mismatch rate
   - Verification precision
   - Verification recall, if manually labeled
   - Revision success rate
   - Revision harm rate
   - Explanation faithfulness proxy
   - Error prediction AUROC, if using verifier scores to predict correctness
   - Calibration proxy, if confidence scores are available

For each metric:
   - Define it
   - Explain why it matters
   - Explain how to compute it
   - Explain how to interpret it

12. Statistical analysis.
   Recommend appropriate statistical tests:
   - Bootstrap confidence intervals for accuracy
   - McNemar test for paired answer differences
   - Paired bootstrap for category-level comparisons
   - Logistic regression predicting correctness from grounding and violation features
   - AUROC/AUPRC for verifier-based error prediction
   - Correlation between grounding coverage and accuracy
   - Category-by-method interaction analysis
   - Ablation comparisons for symbolic features

Explain how to avoid overclaiming if improvements are small or mixed.

13. Tables and figures.
   Propose a full set of publication-quality tables and figures.

   Include at minimum:
   - Table 1: Dataset and category distribution
   - Table 2: System variants / experimental conditions
   - Table 3: Overall accuracy by method
   - Table 4: Category-specific accuracy by method
   - Table 5: Grounding and verification metrics
   - Table 6: Concept mismatch taxonomy with examples
   - Table 7: Ablation study of symbolic components
   - Figure 1: Neuro-symbolic pipeline diagram
   - Figure 2: UMLS grounding example for one MedQA question
   - Figure 3: Accuracy comparison across LLM-only, symbolic-only, and hybrid systems
   - Figure 4: Category-level heatmap of hybrid gains
   - Figure 5: Grounding coverage vs correctness
   - Figure 6: Verification violation score vs error probability
   - Figure 7: Concept mismatch failure examples

For each table/figure:
   - Describe what it should show
   - State the intended takeaway
   - Draft a possible caption

14. Concept mismatch analysis.
   This should be a major section of the paper.

   Build a taxonomy of concept mismatch errors, including:
   - lexical synonym mismatch
   - clinical paraphrase mismatch
   - granularity mismatch
   - symptom vs diagnosis mismatch
   - mechanism vs disease mismatch
   - treatment indication mismatch
   - lab value normalization mismatch
   - negation or uncertainty mismatch
   - temporal mismatch
   - relation sparsity
   - missing UMLS relation
   - overly broad semantic type
   - overly narrow concept mapping
   - answer-choice abstraction mismatch

For each category:
   - Define it
   - Give a MedQA-style example
   - Explain how it affects symbolic scoring
   - Explain how an LLM may help
   - Explain how an LLM may still fail

15. Error-analysis framework.
   Develop an error taxonomy for the hybrid system:
   - LLM correct, symbolic wrong
   - symbolic correct, LLM wrong
   - both wrong
   - both correct but for different reasons
   - symbolic verifier detects LLM error but revision fails
   - symbolic verifier incorrectly flags correct LLM reasoning
   - UMLS grounding failure
   - UMLS relation failure
   - category misclassification
   - answer extraction failure
   - contradiction detection false positive
   - contradiction detection false negative

For each:
   - Define it
   - Explain how to detect it
   - Explain why it matters for future neuro-symbolic systems

16. Ablation studies.
   Propose ablations such as:
   - remove semantic type filtering
   - remove UMLS relations
   - use concepts only
   - use relations only
   - remove contradiction detector
   - remove demographic plausibility detector
   - remove grounding coverage score
   - remove category-specific scoring
   - use LLM without UMLS
   - use UMLS appended to prompt but no verifier
   - use verifier but no answer revision
   - use verifier with answer revision

For each ablation:
   - What it tests
   - Expected result
   - How it supports the paper’s argument

17. Case studies.
   Propose 3–5 qualitative case studies:
   - A case where UMLS grounding helps correct an LLM error
   - A case where UMLS symbolic scoring fails due to concept mismatch
   - A case where the verifier detects a contradiction
   - A case where answer revision harms performance
   - A case where hybrid reasoning produces a better evidence trace but not a better final answer

For each case study:
   - What to show
   - How to present the question, answer choices, LLM rationale, UMLS concepts, verifier output, and final decision
   - What lesson the reader should take away

18. Core contribution claims.
   Write 3–5 precise contribution bullets.
   They should be defensible and non-hypey.
   Avoid claiming clinical deployment readiness.
   Focus on empirical characterization, hybrid reasoning, grounding, verification, and concept mismatch.

19. Limitations section.
   Write a thoughtful limitations plan.
   Include:
   - MedQA is exam-style, not real clinical practice
   - UMLS is incomplete and not designed as a full reasoning engine
   - Concept extraction and entity linking errors propagate downstream
   - Symbolic relations may not encode causal or temporal reasoning well
   - LLM-generated rationales may not be faithful
   - Verification metrics may require manual validation
   - Hybrid improvements may be category-dependent
   - Answer revision can introduce harm
   - The system does not provide medical advice or clinical decision support

20. Future work section.
   Connect Paper 2 to Paper 3.
   Explain how this paper motivates:
   - agentic evidence acquisition
   - adaptive diagnostic programs
   - category-specific reasoning modules
   - probabilistic belief updates
   - symbolic contradiction-aware planning
   - differential diagnosis rather than answer selection
   - medical knowledge graph expansion
   - executable evidence traces

Make the future-work section sound like a coherent PhD research program.

21. Publication strategy.
   Recommend suitable venue types:
   - biomedical informatics conferences
   - medical AI workshops
   - ML for health venues
   - knowledge representation / neuro-symbolic AI workshops
   - arXiv-first strategy
   - possible journal extension

Also recommend what additional experiments would strengthen the paper before submission.

22. Concrete next steps from the repo.
   Give me a checklist of artifacts I should generate:
   - outputs from LLM-only baseline
   - outputs from pure UMLS scorer
   - outputs from hybrid verifier
   - Chain-of-Verification traces
   - concept grounding logs
   - contradiction flags
   - category-specific result CSVs
   - answer-level correctness labels
   - verifier score tables
   - ablation results
   - manually annotated sample of concept mismatch cases
   - manually annotated sample of verifier true/false positives
   - reproducibility README
   - environment/configuration table
   - prompt templates

23. Finally, produce a draft skeleton paper in this format:
   - Title
   - Abstract
   - 1. Introduction
   - 2. Related Work
   - 3. Background: UMLS and Neuro-Symbolic Medical Reasoning
   - 4. Dataset
   - 5. Methods
   - 6. Experimental Setup
   - 7. Results
   - 8. Concept Mismatch Analysis
   - 9. Discussion
   - 10. Limitations
   - 11. Future Work
   - 12. Conclusion

For each section:
   - Include starter prose
   - Include placeholders for exact results
   - Include notes about what tables/figures to insert
   - Maintain formal academic tone

Writing style:
Use rigorous academic language. Be ambitious but careful. Do not overclaim clinical utility. Avoid making the system sound ready for real patient diagnosis. Emphasize that this is a controlled MedQA-style evaluation of neuro-symbolic grounding, verification, and error characterization.

The main message should be:
UMLS grounding alone is not enough, and LLM reasoning alone is not trustworthy enough. The interesting research contribution is understanding how hybrid neuro-symbolic systems can use structured biomedical knowledge to audit, constrain, and explain medical reasoning while still relying on LLMs to bridge semantic and contextual gaps.