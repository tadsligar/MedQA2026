# Neurosymbolic Approaches for MedQA

This directory contains two neurosymbolic methods that combine neural and symbolic reasoning for medical question answering.

## Approaches

### 1. UMLS Verifier (`umls_verifier/`)

**Description**: NeuroSymbolic verifier that combines neural relevance scoring with symbolic verification using UMLS concepts.

**Key Features**:
- UMLS-grounded evidence linking
- Hybrid scoring (TF-IDF or LLM + symbolic rules)
- Modular verifiers:
  - Type Compatibility: Semantic type alignment
  - Demographic Plausibility: Age/sex/pregnancy contradiction detection
  - Grounding Coverage: Penalizes poorly-grounded options
- Works across heterogeneous medical tasks

**Architecture**:
```
Question/Option → Entity Linking → UMLS CUIs → Evidence Gathering
→ Neural Scoring (TF-IDF/LLM) + Symbolic Verification → Final Score
```

**Use Cases**:
- Grounding-based answer ranking
- Post-hoc verification of LLM outputs
- Symbolic constraint enforcement

**See**: `umls_verifier/README.md` for detailed documentation

### 2. Chain of Verification (`chain_of_verification/`)

**Description**: UMLS-grounded Chain-of-Verification (CoVe) pipeline that iteratively proposes, grounds, verifies, and revises medical analyses.

**Key Features**:
- Structured analysis generation (heuristic or LLM-based)
- UMLS concept grounding with CUI mapping
- 5 symbolic verifiers detecting violations:
  - Type incompatibility
  - Demographic implausibility
  - Low grounding coverage
  - Polarity conflicts
  - Internal contradictions
- Iterative refinement through revision
- Comprehensive metrics (accuracy, grounding, violations)

**Architecture**:
```
Question → Propose Analysis → Ground to UMLS → Verify
→ [Revise if violations] → Decide Final Answer
```

**Evaluation Results** (on MedQA subset):
- Heuristic baseline: 21.0%
- With verification only: 29.0% (+38% improvement)
- Full CoVe (with revision): 28.0%

**Use Cases**:
- Structured medical reasoning with explainability
- Violation detection and correction
- Confidence calibration

**See**: `chain_of_verification/README.md` for detailed documentation

## UMLS Data

Both approaches require UMLS (Unified Medical Language System) data:

### Required Files
- **MRCONSO.RRF**: Concepts and terms (~4GB)
- **MRSTY.RRF**: Semantic types (~100MB)
- **MRDEF.RRF**: Definitions (~200MB)

### Obtaining UMLS
1. Register for free UMLS license: https://uts.nlm.nih.gov/uts/signup-login
2. Download latest Metathesaurus Full Release
3. Extract META directory
4. Build index using scripts in respective approach directories

### UMLS Index Location
UMLS indices should be placed in `/aiau010_scratch/tzs0128/projects/MedQA2026/data/umls/`

Or reference existing indices from the neurosymbolic subdirectories.

## Comparison

| Feature | UMLS Verifier | Chain of Verification |
|---------|---------------|----------------------|
| **Primary Goal** | Post-hoc verification | Structured reasoning pipeline |
| **Proposer** | External (any LLM) | Built-in (heuristic or LLM) |
| **Grounding** | Evidence bundles | Structured analyses |
| **Verification** | 3 verifiers | 5 verifiers |
| **Revision** | No | Yes (iterative) |
| **Explainability** | Moderate | High (structured analyses) |
| **Speed** | Fast | Moderate (if revision enabled) |
| **Best For** | Ranking/filtering | Full reasoning pipeline |

## Integration with Base Runs

These neurosymbolic approaches can be used to:
1. **Augment base model predictions**: Use symbolic verification to filter/rank outputs
2. **Analyze base model errors**: Identify patterns in failures
3. **Compare with neural-only baselines**: Measure value of symbolic grounding

## Installation

Each approach is a standalone Python package. See individual READMEs for installation instructions.

## Citation

If you use these approaches, please acknowledge:

**UMLS Source**:
> Bodenreider O. The Unified Medical Language System (UMLS): integrating biomedical terminology.
> Nucleic Acids Research. 2004 Jan 1;32(Database issue):D267-70.

## License

Both approaches are provided for research and educational purposes. UMLS data is subject to UMLS license agreement.
