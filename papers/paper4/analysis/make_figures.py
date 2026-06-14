#!/usr/bin/env python3
"""Paper 4 figures (no GPU): per-competency accuracy w/ Wilson CIs; MK-DX gap vs scale
(full vs held-out test); per-competency instability. Saves to papers/paper4/figures/."""
import os, json, glob, math
from collections import defaultdict
from statistics import mean
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
FIG = os.path.join(REPO, "papers/paper4/figures"); os.makedirs(FIG, exist_ok=True)
FULL = os.path.join(REPO, "results/base_runs_full")
MODELS = ["olmo3_7b", "olmo3_32b", "qwen25_7b", "qwen25_14b", "qwen25_32b"]
NAME = {"olmo3_7b": "OLMo-3 7B", "olmo3_32b": "OLMo-3 32B", "qwen25_7b": "Qwen2.5 7B",
        "qwen25_14b": "Qwen2.5 14B", "qwen25_32b": "Qwen2.5 32B"}
SIZE = {"OLMo-3 7B": 7, "OLMo-3 32B": 32, "Qwen2.5 7B": 7, "Qwen2.5 14B": 14, "Qwen2.5 32B": 32}
CLIN = ["MK", "DX", "MGMT"]; COL = {"MK": "#d1495b", "DX": "#1b6ca8", "MGMT": "#3f8f3f"}


def wilson(k, n, z=1.96):
    p = k/n; d = 1+z*z/n; c = (p+z*z/(2*n))/d; h = (z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)))/d
    return 100*(c-h), 100*(c+h)


def load_v2():
    d = {}
    for l in open(os.path.join(REPO, "results/reasoning_ops/op_labels_v2.jsonl")):
        o = json.loads(l)
        if o.get("competency"): d[int(o["qid"])] = o["competency"]
    return d


def runs(m, t):
    per = defaultdict(list)
    for f in glob.glob(os.path.join(FULL, m, f"temp{t}_run*_results.json")):
        for r in json.load(open(f)):
            ic = r["is_correct"]; ic = ic if isinstance(ic, bool) else str(ic).lower() == "true"
            per[int(r["question_id"])].append((ic, r.get("predicted")))
    return per


def maj(per): return {q: (1 if sum(i for i, _ in v)*2 >= len(v) else 0) for q, v in per.items()}


lab = load_v2()
split = {}
for i, q in enumerate(json.load(open(os.path.join(REPO, "data/datasets/medqa_full_combined.json")))):
    split[int(q.get("question_id", i))] = q.get("source_split", "?")
corr = {m: maj(runs(m, 0.0)) for m in MODELS}

# F1: per-competency accuracy + Wilson CI
fig, ax = plt.subplots(figsize=(9, 4.5)); x = range(len(MODELS)); w = 0.26
for j, c in enumerate(CLIN):
    ys, los, his = [], [], []
    for m in MODELS:
        v = [corr[m][q] for q in lab if lab[q] == c and q in corr[m]]; k = sum(v); n = len(v)
        a = 100*k/n; lo, hi = wilson(k, n); ys.append(a); los.append(a-lo); his.append(hi-a)
    ax.bar([i+(j-1)*w for i in x], ys, w, yerr=[los, his], capsize=2, label=c, color=COL[c])
ax.set_xticks(list(x)); ax.set_xticklabels([NAME[m] for m in MODELS], rotation=20, ha="right")
ax.set_ylabel("Accuracy (%)"); ax.set_title("Per-competency accuracy (t=0.0, full set) with Wilson 95% CIs")
ax.legend(title="Competency"); ax.set_ylim(30, 80); fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig1_competency_accuracy.png"), dpi=150); plt.close(fig)

# F2: MK-DX gap vs scale, full vs test
fig, ax = plt.subplots(figsize=(7.5, 4.5))
for subset, mk_marker, lbl in [("full", "o", "full set"), ("test", "s", "held-out test")]:
    xs, ys = [], []
    for m in MODELS:
        sel = (lambda q: True) if subset == "full" else (lambda q: split.get(q) == "test")
        mk = [corr[m][q] for q in lab if lab[q] == "MK" and q in corr[m] and sel(q)]
        dx = [corr[m][q] for q in lab if lab[q] == "DX" and q in corr[m] and sel(q)]
        xs.append(SIZE[NAME[m]]+ (0.3 if "Qwen" in NAME[m] else -0.3)); ys.append(100*mean(mk)-100*mean(dx))
    ax.scatter(xs, ys, marker=mk_marker, s=60, label=lbl)
ax.axhline(0, color="gray", lw=0.8, ls="--"); ax.set_xscale("log"); ax.set_xticks([7, 14, 32]); ax.set_xticklabels(["7B", "14B", "32B"])
ax.set_xlabel("Model size"); ax.set_ylabel("MK − DX accuracy gap (pp)")
ax.set_title("MK−DX gap (negative = diagnosis easier than applying science)")
ax.legend(); fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig2_mk_dx_gap.png"), dpi=150); plt.close(fig)

# F3: instability by competency (t=0.7)
fig, ax = plt.subplots(figsize=(9, 4.5))
for j, c in enumerate(CLIN):
    ys = []
    for m in MODELS:
        per = runs(m, 0.7); vals = []
        for q in lab:
            if lab[q] == c and q in per and len(per[q]) > 1:
                vals.append(0 if len({p for _, p in per[q]}) == 1 else 1)
        ys.append(100*mean(vals))
    ax.bar([i+(j-1)*w for i in range(len(MODELS))], ys, w, label=c, color=COL[c])
ax.set_xticks(list(range(len(MODELS)))); ax.set_xticklabels([NAME[m] for m in MODELS], rotation=20, ha="right")
ax.set_ylabel("Run-to-run instability (%)"); ax.set_title("Answer instability by competency (t=0.7)")
ax.legend(title="Competency"); fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig3_instability_by_competency.png"), dpi=150); plt.close(fig)
print("wrote fig1_competency_accuracy.png, fig2_mk_dx_gap.png, fig3_instability_by_competency.png")
