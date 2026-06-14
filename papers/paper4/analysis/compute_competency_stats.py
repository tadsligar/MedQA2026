#!/usr/bin/env python3
"""
Paper 4 — confirmatory stats + robustness on the v2 competency labels (no GPU).
(A) Pooled model-adjusted competency effect (GLM logit, ref=DX) + Holm; LRT omnibus.
(B) Held-out test-split (source_split=='test', 1,273) replication of per-competency accuracy + MK-DX.
(C) Temperature: MK-DX gap at t=0.0/0.3/0.7; per-competency run-to-run instability (stability).
Inputs: results/reasoning_ops/op_labels_v2.jsonl, results/base_runs_full/<m>/temp*_run*_results.json,
data/datasets/medqa_full_combined.json (source_split).
"""
import os, json, glob, math
from collections import defaultdict, Counter
from statistics import mean
import pandas as pd, numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
FULL = os.path.join(REPO, "results/base_runs_full")
MODELS = ["olmo3_7b", "olmo3_32b", "qwen25_7b", "qwen25_14b", "qwen25_32b"]
NAME = {"olmo3_7b": "OLMo-3 7B", "olmo3_32b": "OLMo-3 32B", "qwen25_7b": "Qwen2.5 7B",
        "qwen25_14b": "Qwen2.5 14B", "qwen25_32b": "Qwen2.5 32B"}
CLIN = ["MK", "DX", "MGMT"]


def load_v2():
    d = {}
    for l in open(os.path.join(REPO, "results/reasoning_ops/op_labels_v2.jsonl")):
        o = json.loads(l)
        if o.get("competency"): d[int(o["qid"])] = o["competency"]
    return d


def runs(model, temp):
    per = defaultdict(list)
    for f in glob.glob(os.path.join(FULL, model, f"temp{temp}_run*_results.json")):
        for r in json.load(open(f)):
            ic = r["is_correct"]; ic = ic if isinstance(ic, bool) else str(ic).lower() == "true"
            per[int(r["question_id"])].append((ic, r.get("predicted")))
    return per


def majority(per):
    return {q: (1 if sum(ic for ic, _ in v)*2 >= len(v) else 0) for q, v in per.items()}


def ztest(pa, na, pb, nb):
    p = (pa*na+pb*nb)/(na+nb); se = math.sqrt(p*(1-p)*(1/na+1/nb))
    z = (pa-pb)/se if se else 0; return z, math.erfc(abs(z)/math.sqrt(2))


def main():
    lab = load_v2()
    split = {}
    for i, q in enumerate(json.load(open(os.path.join(REPO, "data/datasets/medqa_full_combined.json")))):
        split[int(q.get("question_id", i))] = q.get("source_split", "?")
    print("split sizes:", Counter(split.values()))

    # item-level frame at t=0.0 (majority)
    rows = []
    corr = {m: majority(runs(m, 0.0)) for m in MODELS}
    for m in MODELS:
        for q, c in lab.items():
            if q in corr[m]:
                rows.append({"model": m, "comp": c, "correct": corr[m][q], "test": split.get(q) == "test"})
    df = pd.DataFrame(rows)

    # (A) pooled GLM logit, competency ref=DX, + model fixed effects
    import statsmodels.formula.api as smf, statsmodels.api as sm
    dcl = df[df.comp.isin(CLIN)].copy()
    dcl["comp"] = pd.Categorical(dcl["comp"], categories=["DX", "MK", "MGMT"])
    glm = smf.glm("correct ~ C(comp) + C(model)", data=dcl, family=sm.families.Binomial()).fit()
    print("\n=== (A) pooled competency effect (logit, ref=DX, model-adjusted) ===")
    for term in ["C(comp)[T.MK]", "C(comp)[T.MGMT]"]:
        b = glm.params[term]; ci = glm.conf_int().loc[term]; p = glm.pvalues[term]
        print(f"  {term:16} OR={math.exp(b):.3f}  log-odds={b:+.3f} [{ci[0]:+.3f},{ci[1]:+.3f}]  p={p:.2e}")
    # Holm over the two contrasts
    ps = {t: glm.pvalues[t] for t in ["C(comp)[T.MK]", "C(comp)[T.MGMT]"]}
    sp = sorted(ps.items(), key=lambda kv: kv[1])
    print("  Holm:", [(t, f"{p:.2e}", "sig" if p <= 0.05/(2-i) else "ns") for i, (t, p) in enumerate(sp)])
    # LRT omnibus: competency factor
    red = smf.glm("correct ~ C(model)", data=dcl, family=sm.families.Binomial()).fit()
    lr = 2*(glm.llf - red.llf); from scipy import stats; p890 = stats.chi2.sf(lr, 2)
    print(f"  LRT competency factor: chi2(2)={lr:.1f}  p={p890:.2e}")

    # (B) held-out test split
    print("\n=== (B) held-out TEST split (n_test by competency below) ===")
    print(f"{'model':12} {'MK':>6}{'DX':>6}{'MGMT':>7}   MK-DX  z(MK,DX) p")
    for m in MODELS:
        acc = {}
        nt = {}
        for c in CLIN:
            v = [corr[m][q] for q in lab if lab[q] == c and split.get(q) == "test" and q in corr[m]]
            acc[c] = 100*mean(v) if v else float('nan'); nt[c] = len(v)
        z, p = ztest(acc["MK"]/100, nt["MK"], acc["DX"]/100, nt["DX"])
        print(f"{NAME[m]:12} {acc['MK']:6.1f}{acc['DX']:6.1f}{acc['MGMT']:7.1f}   {acc['MK']-acc['DX']:+5.1f}  z={z:+.2f} p={p:.3f}")
    print("  (test n per competency:", {c: sum(1 for q in lab if lab[q] == c and split.get(q) == 'test') for c in CLIN}, ")")

    # (C) temperature: MK-DX gap by temp
    print("\n=== (C) MK-DX gap (pp) by temperature ===")
    print(f"{'model':12} {'t=0.0':>7}{'t=0.3':>7}{'t=0.7':>7}")
    for m in MODELS:
        line = f"{NAME[m]:12}"
        for t in (0.0, 0.3, 0.7):
            cm = majority(runs(m, t))
            mk = [cm[q] for q in lab if lab[q] == "MK" and q in cm]
            dx = [cm[q] for q in lab if lab[q] == "DX" and q in cm]
            line += f"{(100*mean(mk)-100*mean(dx)):+7.1f}" if mk and dx else f"{'-':>7}"
        print(line)

    # stability by competency (t=0.7, fraction of qs where all runs agree on predicted)
    print("\n=== per-competency answer instability at t=0.7 (lower=more stable) ===")
    print(f"{'model':12} " + "".join(f"{c:>7}" for c in CLIN))
    for m in MODELS:
        per = runs(m, 0.7)
        inst = {}
        for c in CLIN:
            vals = []
            for q in lab:
                if lab[q] == c and q in per and len(per[q]) > 1:
                    preds = [p for _, p in per[q]]
                    vals.append(0 if len(set(preds)) == 1 else 1)
            inst[c] = 100*mean(vals) if vals else float('nan')
        print(f"{NAME[m]:12} " + "".join(f"{inst[c]:7.1f}" for c in CLIN))


if __name__ == "__main__":
    main()
