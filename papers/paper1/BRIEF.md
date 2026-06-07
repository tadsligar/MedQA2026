You are my senior PhD research advisor, AI/ML research collaborator, and scientific writing partner. I am developing a publication from my GitHub repository MedQA2026, which evaluates base language models on a balanced subset of MedQA-style medical reasoning questions.

The goal is to spin off Paper 1 from this project. Paper 1 should be a rigorous benchmark and empirical evaluation paper, not yet the full neuro-symbolic agent paper. It should establish the dataset, experimental design, baseline results, and core empirical findings needed to support later papers on neuro-symbolic grounding, verification, and agentic differential diagnosis.

Context:
- Repository: https://github.com/tadsligar/MedQA2026
- Project theme: evaluating base LLM medical reasoning on MedQA using controlled decoding-temperature experiments and reasoning-category analysis.
- Dataset: a focused balanced MedQA dataset with approximately 1,030 questions, balanced across five reasoning categories:
  1. Clinical Findings
  2. Diagnosis
  3. Mechanism / Pathophysiology
  4. Next Step / Workup
  5. Treatment / Management
- Models evaluated include Qwen2.5 7B, Qwen2.5 14B, Qwen2.5 32B, OLMo 7B, and OLMo 32B.
- Temperatures evaluated include 0.0, 0.3, and 0.7.
- Experiments include repeated runs where applicable, enabling analysis of stochastic variability, answer instability, and category-level robustness.
- This paper should focus on base-model evaluation and should not overclaim clinical utility.
- Later papers will build on this with UMLS grounding, Chain-of-Verification, symbolic contradiction detection, and agentic neuro-symbolic diagnostic reasoning.

The uploaded conceptual reference document frames diagnosis as a coarse-to-fine evidence acquisition process rather than a flat classification task. It emphasizes adaptive reasoning, interpretable evidence traces, uncertainty reduction, and category-specific evidence selection. Use that only as strategic motivation for the broader research arc, but keep Paper 1 focused on benchmarking and empirical model behavior. The future work section can mention that later work will extend from static answer selection toward executable neuro-symbolic diagnostic reasoning. :contentReference[oaicite:0]{index=0}

Your task:
Generate a complete research-paper plan for Paper 1, including title options, abstract, research questions, hypotheses, paper structure, methodology, experiments, metrics, tables/figures, analysis plan, expected contributions, limitations, and publication strategy.

Important framing:
This should be positioned as a serious empirical benchmark paper for AI/ML, biomedical informatics, or medical AI venues. Avoid making it sound like a class project. Emphasize methodological rigor, controlled comparison, reproducibility, and insights into medical reasoning behavior of base language models.

The paper should answer questions such as:
1. How do base LLMs perform across distinct categories of medical reasoning?
2. Does model scale consistently improve performance across all medical reasoning categories?
3. Does decoding temperature improve or degrade accuracy, stability, and robustness?
4. Are some reasoning categories more sensitive to stochastic decoding than others?
5. Do base models exhibit consistent answer-selection behavior or high run-to-run variability?
6. Can category-balanced evaluation reveal weaknesses hidden by aggregate MedQA accuracy?
7. What empirical patterns motivate later neuro-symbolic verification and agentic reasoning methods?

Please produce the following:

1. A concise one-paragraph positioning statement:
   - What is this paper about?
   - Why does it matter?
   - What gap does it fill?
   - What is the main contribution?

2. Five strong paper-title options.
   Titles should sound publication-quality and should avoid hype.
   Include at least one title emphasizing temperature, one emphasizing category-balanced medical reasoning, and one emphasizing base-model evaluation.

3. A polished draft abstract of 200–300 words.
   The abstract should include:
   - Problem motivation
   - Gap in current MedQA evaluation
   - Dataset/design summary
   - Model and temperature comparison
   - Key analysis dimensions
   - Main expected findings, phrased cautiously if exact numbers are not yet known
   - Contribution and implications

4. Research questions and hypotheses.
   Format as:
   RQ1:
   H1:
   RQ2:
   H2:
   etc.
   Include at least 5 research questions.

5. A proposed paper outline with section-by-section content:
   - Introduction
   - Related Work
   - Dataset
   - Experimental Design
   - Results
   - Analysis
   - Discussion
   - Limitations
   - Conclusion
   - Appendix / Reproducibility

For each section, give:
   - Purpose of the section
   - Key claims to make
   - Specific content to include
   - Tables or figures that belong there

6. Introduction draft structure:
   Provide a detailed paragraph-by-paragraph plan for the introduction.
   Include:
   - Opening problem
   - Why MedQA matters
   - Why aggregate accuracy is insufficient
   - Why category-balanced reasoning analysis matters
   - Why temperature and stochasticity matter
   - What this paper contributes
   - Summary of findings
   - Contributions list

7. Related work plan:
   Identify the major clusters of related work:
   - Medical question answering benchmarks
   - LLMs for clinical reasoning
   - Base vs instruction-tuned medical reasoning models
   - Temperature, sampling, and stochastic decoding
   - Evaluation beyond aggregate accuracy
   - Reliability, uncertainty, and calibration in medical AI

For each cluster:
   - Explain what to cite
   - Explain how to position this paper relative to prior work
   - Identify the gap this paper addresses

8. Dataset section plan:
   Describe how to present the 1,030-question balanced dataset.
   Include:
   - Source and filtering strategy
   - Category definitions
   - Category counts
   - Why balancing matters
   - Possible annotation or classification method
   - Any quality-control checks needed
   - Example question types for each category
   - Limitations of using MedQA-style exam questions

Also propose a dataset summary table.

9. Experimental design:
   Provide a detailed experimental setup:
   - Models
   - Parameter sizes
   - Base vs instruction-tuned distinction
   - Hardware/software environment if relevant
   - Prompt format
   - Decoding parameters
   - Number of repeated runs
   - Answer extraction method
   - Accuracy calculation
   - Handling malformed outputs
   - Statistical comparison method
   - Reproducibility artifacts

Include recommended statistical tests:
   - Confidence intervals for accuracy
   - McNemar or paired bootstrap tests for model comparisons
   - Variance analysis across repeated runs
   - Category-level error analysis
   - Temperature sensitivity metrics

10. Metrics:
   Define all metrics the paper should report:
   - Overall accuracy
   - Category-specific accuracy
   - Per-model accuracy
   - Per-temperature accuracy
   - Run-to-run variance
   - Answer instability
   - Majority-vote accuracy, if repeated samples exist
   - Calibration proxy, if confidence or logits are available
   - Error concentration by category
   - Relative improvement from scale
   - Temperature sensitivity index

For each metric:
   - Define it
   - Explain why it matters
   - Explain how to compute it
   - Explain how to interpret it

11. Results tables and figures:
   Propose a full set of publication-quality tables and figures.
   Include at minimum:
   - Table 1: Dataset category distribution
   - Table 2: Model list and experimental settings
   - Table 3: Overall accuracy by model and temperature
   - Table 4: Category-specific accuracy by model
   - Table 5: Run-to-run variability by model and temperature
   - Figure 1: Study design overview
   - Figure 2: Accuracy by model scale and temperature
   - Figure 3: Category-level heatmap
   - Figure 4: Stability or answer-variance plot
   - Figure 5: Error distribution by reasoning category

For each table/figure:
   - Describe what it should show
   - Explain the main takeaway
   - Explain what kind of caption it should have

12. Analysis plan:
   Provide a detailed analysis strategy.
   Include:
   - How to analyze scale effects
   - How to analyze temperature effects
   - How to analyze interaction between category and temperature
   - How to analyze model family differences
   - How to analyze repeated-run stability
   - How to identify questions that are consistently easy, consistently hard, or unstable
   - How to interpret cases where higher temperature improves performance
   - How to interpret cases where higher temperature causes degradation

13. Error-analysis framework:
   Develop an error taxonomy for wrong answers.
   Include categories such as:
   - Misread clinical finding
   - Incorrect diagnosis
   - Mechanism/pathophysiology confusion
   - Treatment guideline confusion
   - Next-step/workup sequencing error
   - Distractor attraction
   - Overgeneralization
   - Failure to use age/sex/risk factors
   - Temporal reasoning error
   - Pharmacology confusion
   - Malformed answer / extraction failure

For each:
   - Define it
   - Give an example pattern
   - Explain whether it can be detected automatically, manually, or semi-automatically

14. Core contribution claims:
   Write 3–5 contribution bullets suitable for the introduction.
   Make them precise, defensible, and non-hypey.
   Avoid claims that require neuro-symbolic methods, since those are for later papers.

15. Limitations:
   Write a thoughtful limitations section.
   Include:
   - MedQA is exam-style, not real clinical practice
   - Multiple-choice format may overestimate reasoning ability
   - Base models may not reflect deployed medical chatbots
   - Category labels may introduce classification assumptions
   - Accuracy does not fully capture reasoning quality
   - Temperature effects may depend on prompt format and answer extraction
   - No patient-safety claims should be made

16. Future work:
   Connect Paper 1 to later papers:
   - UMLS-grounded symbolic verification
   - Chain-of-Verification
   - Concept mismatch problem in symbolic medical QA
   - Agentic adaptive evidence acquisition
   - Differential diagnosis rather than answer selection
   - Explanation faithfulness and contradiction detection

Make this future-work section sound like a coherent research program.

17. Publication strategy:
   Recommend suitable venues or venue types:
   - ML/AI workshops
   - biomedical informatics conferences
   - medical AI workshops
   - arXiv-first strategy
   - possible journal extension
   - what additional experiments would strengthen acceptance

18. Concrete next steps:
   Give me a checklist of what I need to generate from the repo before drafting:
   - result CSVs
   - aggregate tables
   - confidence intervals
   - category labels
   - prompt templates
   - model configuration table
   - error samples
   - ablation tables
   - reproducibility README

19. Finally, produce a draft “skeleton paper” in this format:
   - Title
   - Abstract
   - 1. Introduction
   - 2. Related Work
   - 3. Dataset
   - 4. Experimental Setup
   - 5. Results
   - 6. Analysis
   - 7. Discussion
   - 8. Limitations
   - 9. Conclusion

For each section, include starter prose and placeholders where exact results should be inserted.

Tone:
Use formal academic writing. Be ambitious but careful. Do not overclaim clinical utility. Emphasize benchmark design, empirical characterization, reproducibility, and the need to move beyond aggregate accuracy in medical reasoning evaluation.