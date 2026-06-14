#!/usr/bin/env python3
"""Full-set inter-annotator agreement between two v2 competency-label files (gpt-5.4-mini vs Qwen).
Cohen's kappa + accuracy + confusion + MK-vs-DX agreement. Usage:
  python3 score_competency_agreement.py --a op_labels_v2.jsonl --b op_labels_v2_qwen.jsonl
"""
import json, argparse
from collections import Counter
CODES = ["MK", "DX", "MGMT", "COMM", "PROF", "SBP", "PBL"]


def load(p):
    d = {}
    for l in open(p):
        try:
            o = json.loads(l)
        except Exception:
            continue
        if o.get("competency"):
            d[int(o["qid"])] = o["competency"]
    return d


def kappa(pairs):
    N = len(pairs); po = sum(1 for a, b in pairs if a == b)/N
    ga = Counter(a for a, _ in pairs); gb = Counter(b for _, b in pairs)
    pe = sum((ga[c]/N)*(gb[c]/N) for c in set(list(ga)+list(gb)))
    return (po-pe)/(1-pe) if pe < 1 else 1.0


def main():
    import os
    ap = argparse.ArgumentParser()
    base = os.path.join(os.path.dirname(__file__), "..", "..", "results", "reasoning_ops")
    ap.add_argument("--a", default=os.path.join(base, "op_labels_v2.jsonl"))
    ap.add_argument("--b", default=os.path.join(base, "op_labels_v2_qwen.jsonl"))
    args = ap.parse_args()
    if not os.path.exists(args.b):
        print("second-annotator file not found:", args.b); return
    A, B = load(args.a), load(args.b)
    q = sorted(set(A) & set(B)); pairs = [(A[x], B[x]) for x in q]
    agree = sum(1 for a, b in pairs if a == b)
    print(f"overlap {len(q)}; agreement {agree}/{len(q)} = {100*agree/len(q):.1f}%; kappa={kappa(pairs):.3f}")
    print("confusion (A=gpt rows, B=qwen cols):")
    cs = [c for c in CODES if any(a == c for a, _ in pairs) or any(b == c for _, b in pairs)]
    print("     " + "  ".join(f"{c:>4}" for c in cs))
    for a in cs:
        row = Counter(b for x, b in pairs if x == a)
        print(f"{a:>4} " + "  ".join(f"{row.get(c,0):>4}" for c in cs))
    mkdx = [(a, b) for a, b in pairs if a in ("MK", "DX") and b in ("MK", "DX")]
    if mkdx:
        ag = sum(1 for a, b in mkdx if a == b)
        print(f"MK-vs-DX: {ag}/{len(mkdx)} = {100*ag/len(mkdx):.1f}%  kappa={kappa(mkdx):.3f}")


if __name__ == "__main__":
    main()
