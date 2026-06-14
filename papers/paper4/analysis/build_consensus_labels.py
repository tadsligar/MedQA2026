#!/usr/bin/env python3
"""
Paper 4 — high-confidence CONSENSUS labels: keep only questions where two independent annotators
(gpt-5.4-mini and an open model, e.g. Qwen2.5) AGREE on the reasoning operation. This strips the
label-noise that confounds the F-vs-B asymmetry (the R/F/B boundary is the unreliable one;
restricting to agreed items yields a clean subset for the salvage test).

Inputs (JSONL, schema {qid, reasoning_operation, systems{15 Y/N}}):
  --a  results/reasoning_ops/op_labels.jsonl              (gpt-5.4-mini)
  --b  results/reasoning_ops/op_labels_qwen25_32b.jsonl   (Qwen second annotator)
Output:
  results/reasoning_ops/op_labels_consensus.jsonl
    {qid, reasoning_operation (agreed), systems (intersection of Y), n_systems_agree, model:"consensus"}

Also prints the full-set inter-annotator agreement + Cohen's kappa on the operation (a
paper-grade reliability number), per-operation retention, and multi-label system agreement
(mean Jaccard). Self-skips with a clear message if the second-annotator file is absent.

Then run the salvage test, e.g.:
  python papers/paper4/analysis/asymmetry_mixed_model.py --labels results/reasoning_ops/op_labels_consensus.jsonl
  python papers/paper4/analysis/op_accuracy.py            --labels results/reasoning_ops/op_labels_consensus.jsonl
"""
import os, json, argparse
from collections import Counter

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OPS = ["R", "F", "B", "I", "W"]
SYSTEMS = ["Cardiovascular", "Respiratory", "Gastrointestinal", "RenalUrinary", "Reproductive",
           "EndocrineMetabolic", "Nervous", "SpecialSenses", "Hematologic", "Immune",
           "Infectious", "Musculoskeletal", "Skin", "Behavioral", "Multisystem"]


def load(path):
    d = {}
    for line in open(path):
        try:
            o = json.loads(line)
        except Exception:
            continue
        if o.get("parse_fail") or not o.get("reasoning_operation"):
            continue
        d[int(o["qid"])] = o
    return d


def kappa(pairs):
    N = len(pairs)
    po = sum(1 for a, b in pairs if a == b) / N
    ga = Counter(a for a, _ in pairs); gb = Counter(b for _, b in pairs)
    pe = sum((ga[c]/N)*(gb[c]/N) for c in set(list(ga)+list(gb)))
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", default=os.path.join(REPO, "results/reasoning_ops/op_labels.jsonl"))
    ap.add_argument("--b", default=os.path.join(REPO, "results/reasoning_ops/op_labels_qwen25_32b.jsonl"))
    ap.add_argument("--out", default=os.path.join(REPO, "results/reasoning_ops/op_labels_consensus.jsonl"))
    args = ap.parse_args()
    if not os.path.exists(args.b):
        print(f"Second-annotator file not found:\n  {args.b}\n"
              f"Waiting on the cluster Qwen labeling job (slurm/reasoning_ops/run_label_vllm.sbatch).")
        return
    A, B = load(args.a), load(args.b)
    both = sorted(set(A) & set(B))
    print(f"annotator A (gpt): {len(A)}   annotator B (qwen): {len(B)}   overlap: {len(both)}")

    pairs = [(A[q]["reasoning_operation"], B[q]["reasoning_operation"]) for q in both]
    agree = [q for q in both if A[q]["reasoning_operation"] == B[q]["reasoning_operation"]]
    print(f"\nOperation agreement: {len(agree)}/{len(both)} = {100*len(agree)/len(both):.1f}%  "
          f"(kappa={kappa(pairs):.3f}) — full-set inter-annotator reliability")
    print("Confusion (A=gpt rows, B=qwen cols):")
    print("   "+"  ".join(f"{c:>5}" for c in OPS))
    for a in OPS:
        row = Counter(B[q]["reasoning_operation"] for q in both if A[q]["reasoning_operation"] == a)
        print(f"{a:>2} "+"  ".join(f"{row.get(c,0):>5}" for c in OPS))

    # write consensus subset
    jac = []
    dist = Counter()
    with open(args.out, "w", encoding="utf-8") as f:
        for q in agree:
            op = A[q]["reasoning_operation"]; dist[op] += 1
            ya = {s for s in SYSTEMS if (A[q].get("systems") or {}).get(s) == "Y"}
            yb = {s for s in SYSTEMS if (B[q].get("systems") or {}).get(s) == "Y"}
            inter = ya & yb; uni = ya | yb
            jac.append(len(inter)/len(uni) if uni else 1.0)
            systems = {s: ("Y" if s in inter else "N") for s in SYSTEMS}
            f.write(json.dumps({"qid": q, "reasoning_operation": op, "systems": systems,
                                "n_systems_agree": len(inter), "model": "consensus"},
                               ensure_ascii=False) + "\n")
    print(f"\nConsensus subset: {len(agree)} questions -> {args.out}")
    print("operation retention (of agreed set):", dict(dist.most_common()))
    # how many of each annotator-A operation survived
    a_dist = Counter(A[q]["reasoning_operation"] for q in both)
    print("retention rate by operation (agreed / overlap):")
    for op in OPS:
        kept = dist.get(op, 0); tot = a_dist.get(op, 0)
        print(f"  {op}: {kept}/{tot}" + (f" = {100*kept/tot:.0f}%" if tot else ""))
    print(f"system multi-label mean Jaccard (on agreed-operation items): {sum(jac)/len(jac):.2f}" if jac else "")


if __name__ == "__main__":
    main()
