#!/usr/bin/env python3
"""
Paper 1 advanced analysis:
  A. Statistical rigor
     - Wilson 95% CIs for overall and per-category accuracy (t=0.0)
     - Exact McNemar tests for key model pairs (t=0.0, run 1)
     - Category x temperature interaction (chi-square on correct->incorrect flips)
  B. Behavioral analyses
     - Letter/positional bias (predicted vs gold answer-letter distribution)
     - Stability-as-confidence proxy (stable vs unstable question accuracy at t=0.7)
     - Temperature-rescue set (wrong at t=0.0, majority-correct at t=0.7)
     - Cross-model error overlap + hard-core set (all 5 models wrong at t=0.0)
  C. Data-quality audit (malformed predictions across all 45 files)

Outputs CSVs to papers/paper1/tables/ and prints a readable report.
"""
import json
import math
import os
from collections import Counter, defaultdict
from itertools import combinations
from statistics import mean

import pandas as pd
from scipy import stats

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # repo root from papers/<paper>/analysis/
REPO = _REPO
RESULTS_DIR = os.path.join(REPO, "results", "base_runs")
OUT = os.path.join(REPO, "papers", "paper1", "tables")

MODELS = ["olmo3_7b", "olmo3_32b", "qwen25_7b", "qwen25_14b", "qwen25_32b"]
NAME = {"olmo3_7b": "OLMo-3 7B", "olmo3_32b": "OLMo-3 32B", "qwen25_7b": "Qwen2.5 7B",
        "qwen25_14b": "Qwen2.5 14B", "qwen25_32b": "Qwen2.5 32B"}
TEMPS = [0.0, 0.3, 0.7]
RUNS = [1, 2, 3]
CATEGORIES = ["Clinical Findings", "Diagnosis", "Mechanism/Pathophysiology",
              "Next Step/Workup", "Treatment/Management"]
VALID = {"A", "B", "C", "D"}


def