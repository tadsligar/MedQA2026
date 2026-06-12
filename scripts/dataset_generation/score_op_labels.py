#!/usr/bin/env python3
"""
Validate operation_labeler.py output against a gold sample.

  reasoning_operation : single-label  -> accuracy + Cohen's kappa
  organ systems        : multi-label   -> micro/macro precision/recall/F1, mean Jaccard

Gold file (JSONL), same schema as the labeler:
  {"qid", "reasoning_operation":"R|F|B|I|W", "systems":{<15 systems>:"Y|N"}}
Usage:
  python scripts/dataset_generation/score_op_labels.py \
    --pred results/reasoning_ops/op_labels.jsonl \
    --gold results/reasoning_ops/gold_op_labels.jsonl
"""
import json, argparse
from collections import Counter

SYSTEMS = ["Cardiovascular", "Respiratory", "Gastrointestinal", "RenalUrinary", "Reproductive",
           "EndocrineMetabolic", "Nervous", "SpecialSenses", "Hematologic", "Immune",
           "Infectious", "Musculoskeletal", "Skin", "Behavioral", "Multisystem"]


def load(p):
    d = {}
    for line in open(p):
        try:
            o = json.loads(line); d[int(o["qid"])] = o
        except Exception:
            pass
    return d


def kappa(pairs):
    cats = sorted({a for a, _ in pairs} | {b for _, b in pairs})
    N = len(pairs)
    po = sum(1 for a, b in pairs if a == b) / N
    ga = Counter(a for a, _ in pairs); gb = Counter(b for _, b in pairs)
    pe = sum((ga[c]/N)*(gb[c]/N) for c in cats)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred", default="results/reasoning_ops/op_labels.jsonl")
    ap.add_argument("--gold", default="results/reasoning_ops/gold_op_labels.jsonl")
    args = ap.parse_args()
    import os
    if not os.path.exists(args.gold):
        print("No gold file yet:", args.gold); return
    pred, gold = load(args.pred), load(args.gold)
    qids = [q for q in gold if q in pred]
    print(f"scored on {len(qids)} overlapping qids")

    # --- reasoning operation: single-label ---
    pairs = [(gold[q]["reasoning_operation"], pred[q]["reasoning_operation"]) for q in qids]
    acc = sum(1 for a, b in pairs if a == b) / len(pairs)
    print(f"\nreasoning_operation  accuracy={100*acc:.1f}%  kappa={kappa(pairs):.3f}")
    conf = Counter(pairs)
    print("  confusion (gold->pred):", dict(sorted(conf.items())))

    # --- organ systems: multi-label ---
    tp = fp = fn = 0
    jac = []
    per = {s: [0, 0, 0] for s in SYSTEMS}  # tp, fp, fn
    for q in qids:
        g = {s for s in SYSTEMS if gold[q].get("systems", {}).get(s) == "Y"}
        p = {s for s in SYSTEMS if pred[q].get("systems", {}).get(s) == "Y"}
        tp += len(g & p); fp += len(p - g); fn += len(g - p)
        u = len(g | p); jac.append(len(g & p)/u if u else 1.0)
        for s in SYSTEMS:
            if s in g and s in p: per[s][0] += 1
            elif s in p: per[s][1] += 1
            elif s in g: per[s][2] += 1
    def prf(tp, fp, fn):
        pr = tp/(tp+fp) if tp+fp else 0; rc = tp/(tp+fn) if tp+fn else 0
        f1 = 2*pr*rc/(pr+rc) if pr+rc else 0; return pr, rc, f1
    mpr, mrc, mf1 = prf(tp, fp, fn)
    print(f"\norgan systems (multi-label)  micro P={mpr:.2f} R={mrc:.2f} F1={mf1:.2f}  meanJaccard={sum(jac)/len(jac):.2f}")
    macro = [prf(*per[s]) for s in SYSTEMS]
    print(f"  macro F1={sum(f for _,_,f in macro)/len(macro):.2f}")
    print("  per-system F1:")
    for s, (_, _, f1) in sorted(zip(SYSTEMS, macro), key=lambda x: -x[1][2]):
        n = per[s][0]+per[s][2]
        print(f"    {s:18} F1={f1:.2f}  (gold N={n})")


if __name__ == "__main__":
    main()
