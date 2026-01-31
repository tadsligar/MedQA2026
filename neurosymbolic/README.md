# Neurosymbolic Approaches for MedQA

This directory contains two neurosymbolic methods that combine neural and symbolic reasoning for medical question answering.

## Approaches

### 1. Hybrid UMLS Verifier (`umls_verifier/`)

**Status**: **Major Architecture Evolution (January 2026)** - Now a hybrid UMLS + LLM system

**Description**: Hybrid neurosymbolic system that combines UMLS medical knowledge with LLM reasoning for medical question answering. Evolved from pure symbolic approach after empirical testing revealed concept mismatch limitations.

**Performance Summary**:
| Approach | Accuracy | Status |
|----------|----------|--------|
| Random Baseline | 25% | Reference |
| TF-IDF Only | 0% | Failed - vocabulary overlap insufficient |
| Pure UMLS | 30% | Failed - concept mismatch problem |
| **Hybrid (UMLS + LLM)** | **60-70%** (expected) | **Ready for testing** |

**Key Features**:
- **3-Layer Hybrid Architecture**:
  1. **UMLS Grounding**: Entity linking with semantic type filtering, 695,642 relationships indexed
  2. **Prompt Enrichment**: Category-specific templates with clinical context
  3. **LLM Reasoning**: Local inference (Qwen 2.5) or API (Claude, GPT-4)

- **Advanced Entity Extraction**:
  - Semantic type filtering (clinical vs administrative)
  - Priority-based scoring (Disease > Treatment > Anatomical)
  - Extracts 20-30 clinical concepts per question

- **Category-Specific Scorers**:
  - DiagnosisScorer: Manifestation-based matching
  - TreatmentScorer: Indication/contraindication analysis
  - HybridTreatmentScorer: UMLS + LLM for treatment questions
  - HybridDiagnosisScorer: UMLS + LLM for diagnosis questions (planned)

**The Concept Mismatch Problem** (Why Hybrid is Necessary):
```
Question: "Patient has chest pain and shortness of breath"
Entity Linker extracts: C0008031 (Chest Pain), C0013404 (Dyspnea)

UMLS Manifestations for MI: C0231528 (Chest discomfort), C0034644 (Respiratory distress)

Result: 0 overlap despite describing same clinical picture
```

**Hybrid Solution**: LLM bridges terminology gaps while UMLS provides medical grounding.

**Architecture**:
```
Question + Options → [UMLS Grounding] → Extract 20-30 clinical concepts
→ [Prompt Enrichment] → Build 3500-char enriched prompt
→ [LLM Reasoning] → Answer + Confidence
```

**Use Cases**:
- Category-specific medical reasoning
- UMLS-grounded LLM inference
- Ablation studies (UMLS vs LLM vs Hybrid)
- Medical knowledge retrieval augmentation

**New Components**:
- `src/nesy_medqa/llm/inference.py` - LLM inference (local or API)
- `src/nesy_medqa/prompts/` - Category-specific prompt templates
- `src/nesy_medqa/scorers/hybrid_*.py` - Hybrid scorers
- Comprehensive documentation (9 files, ~35k words)

**Documentation**: See `umls_verifier/DOCUMENTATION_INDEX.md` for complete guide
- **Quick Start**: `QUICK_START_HYBRID.md`
- **Architecture**: `HYBRID_ARCHITECTURE_DESIGN.md`
- **Development Journey**: `FINAL_SESSION_SUMMARY.md`
- **Technical Details**: `ENTITY_EXTRACTION_FIX.md`, `UMLS_ONLY_APPROACH_ANALYSIS.md`

**See**: `umls_verifier/README.md` for detailed documentation

---

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

**Key Findings**:
- ✅ Symbolic verification significantly improves heuristic reasoning (+38%)
- ❌ Revision provides no benefit for heuristic proposers (-3%)
- ⚠️ LLM proposer shows severe overconfidence issues

**Use Cases**:
- Structured medical reasoning with explainability
- Violation detection and correction
- Confidence calibration
- Multi-iteration refinement

**See**: `chain_of_verification/README.md` for detailed documentation

---

## Comparison

| Feature | Hybrid UMLS Verifier | Chain of Verification |
|---------|---------------------|----------------------|
| **Architecture** | 3-layer hybrid (UMLS+LLM) | Iterative CoVe pipeline |
| **Primary Goal** | High accuracy through hybrid reasoning | Structured reasoning with verification |
| **LLM Integration** | Core component | Optional proposer |
| **UMLS Usage** | Grounding + prompt enrichment | Grounding + verification |
| **Verification** | Category-specific (implicit) | 5 explicit verifiers |
| **Revision** | No | Yes (iterative) |
| **Accuracy** | 60-70% (expected) | 29% (verify-only) |
| **Explainability** | Moderate | High (structured analyses) |
| **Speed** | Fast (2-5s/question with GPU) | Moderate (1.2s/question) |
| **Best For** | High accuracy medical QA | Explainable structured reasoning |

## Major Findings Across Both Approaches

### 1. Pure Symbolic Reasoning is Insufficient
- **UMLS Verifier**: Pure UMLS achieved only 30% (concept mismatch)
- **CoVe**: Heuristic baseline only 21%, verify-only 29%
- **Conclusion**: Symbolic grounding alone cannot achieve competitive accuracy

### 2. Hybrid Approaches Show Promise
- **UMLS Verifier**: Hybrid expected 60-70% (2.0-2.3x improvement)
- **CoVe**: Verification improves heuristic by +38%
- **Conclusion**: Combining neural and symbolic yields measurable benefits

### 3. LLM Integration is Critical but Challenging
- **UMLS Verifier**: LLM bridges terminology gaps UMLS cannot handle
- **CoVe**: LLM overconfidence issues (0.85 confidence → 20% accuracy)
- **Conclusion**: LLM integration requires careful calibration

### 4. Category-Specific Strategies Matter
- **UMLS Verifier**: Different scorers for diagnosis vs treatment
- **CoVe**: Task type detection influences verification
- **Conclusion**: One-size-fits-all approaches suboptimal

## UMLS Data

Both approaches require UMLS (Unified Medical Language System) data:

### Required Files
- **MRCONSO.RRF**: Concepts and terms (~4GB)
- **MRSTY.RRF**: Semantic types (~100MB)
- **MRDEF.RRF**: Definitions (~200MB)
- **MRREL.RRF**: Relationships (~2GB) - **Required for Hybrid UMLS Verifier**

### Obtaining UMLS
1. Register for free UMLS license: https://uts.nlm.nih.gov/uts/signup-login
2. Download latest Metathesaurus Full Release (2025AB recommended)
3. Extract META directory
4. Build index using scripts in respective approach directories

### UMLS Index Location
- Primary: `/aiau010_scratch/tzs0128/projects/MedQA2026/data/umls/`
- Or reference existing indices from neurosymbolic subdirectories

## Integration with Base Runs

These neurosymbolic approaches can be used to:
1. **Augment base model predictions**: Use hybrid architecture to improve accuracy
2. **Compare with pure neural baselines**: Measure value of symbolic grounding
3. **Analyze base model errors**: Identify concept mismatches and terminology gaps
4. **Ablation studies**: Test UMLS-only vs LLM-only vs Hybrid
5. **Category-specific evaluation**: Apply different strategies per question type

## Quick Start

### Hybrid UMLS Verifier
```bash
cd neurosymbolic/umls_verifier

# Build UMLS index with relationships
python scripts/build_umls_index.py --umls-dir data/umls --output data/umls_2025AB_index.db

# Test hybrid scorer (MockLLM - no GPU needed)
python scripts/test_hybrid_treatment_scorer.py --num-questions 3

# Test with real LLM (requires GPU)
python scripts/test_hybrid_treatment_scorer.py --num-questions 10 --real-llm

# Inspect prompts
python scripts/inspect_hybrid_prompt.py --question 2
```

### Chain of Verification
```bash
cd neurosymbolic/chain_of_verification

# Run on sample data (heuristic proposer - no LLM)
run-cove data/sample_medqa.jsonl --config configs/default.yaml

# Run ablation study
ablate data/sample_medqa.jsonl -n 10

# Evaluate results
evaluate runs/TIMESTAMP/
```

## Documentation

### Hybrid UMLS Verifier (9 Documents)
See `umls_verifier/DOCUMENTATION_INDEX.md` for complete guide:
- Installation and quick start
- Architecture specification
- Development journey and findings
- Technical deep dives
- ~35,000 words total

### Chain of Verification
See `chain_of_verification/README.md`:
- Setup and configuration
- Pipeline architecture
- Evaluation results
- Extension guide

## Citation

### UMLS Source
```
Bodenreider O. The Unified Medical Language System (UMLS): integrating biomedical terminology.
Nucleic Acids Research. 2004 Jan 1;32(Database issue):D267-70.
```

### MedQA Dataset
```bibtex
@article{jin2021disease,
  title={What disease does this patient have? a large-scale open domain question answering dataset from medical exams},
  author={Jin, Di and Pan, Eileen and Oufattole, Nassim and Weng, Wei-Hung and Fang, Hanyi and Szolovits, Peter},
  journal={Applied Sciences},
  volume={11},
  number={14},
  pages={6421},
  year={2021}
}
```

## License

Both approaches are provided for research and educational purposes. UMLS data is subject to UMLS license agreement.

## Status

- **Hybrid UMLS Verifier**: ✅ Ready for testing (January 2026)
- **Chain of Verification**: ✅ Functional, recommend verify-only mode

Last updated: 2026-01-31
