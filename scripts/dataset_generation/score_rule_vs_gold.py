import json
from collections import Counter, defaultdict

gold = {}
for l in open("results/category_relabel/gold_labels_opus.jsonl"):
    o=json.loads(l); gold[o["qid"]]=o["competency"]

rule={}
for l in open("results/category_relabel/competency_labels_rule.jsonl"):
    o=json.loads(l); rule[o["qid"]]=(o["competency"],o["confidence"])

CATS=["MK","PC_DX","PC_MGMT","COMM","PROF","SBP","PBL"]
n=agree=0
hi_n=hi_agree=0
conf=defaultdict(Counter)  # gold -> Counter(rule)
mism=[]
for qid,g in gold.items():
    if qid not in rule: continue
    r,c=rule[qid]; n+=1
    conf[g][r]+=1
    if r==g: agree+=1
    else: mism.append((qid,g,r,c))
    if c=="high":
        hi_n+=1
        if r==g: hi_agree+=1

print(f"Overall agreement: {agree}/{n} = {100*agree/n:.1f}%")
print(f"High-confidence agreement: {hi_agree}/{hi_n} = {100*hi_agree/hi_n:.1f}%")

# Cohen's kappa
def kappa(pairs):
    cats=set()
    for a,b in pairs: cats|={a,b}
    cats=list(cats)
    N=len(pairs)
    po=sum(1 for a,b in pairs if a==b)/N
    ga=Counter(a for a,b in pairs); gb=Counter(b for a,b in pairs)
    pe=sum((ga[c]/N)*(gb[c]/N) for c in cats)
    return (po-pe)/(1-pe)
pairs=[(gold[q],rule[q][0]) for q in gold if q in rule]
print(f"Cohen's kappa: {kappa(pairs):.3f}")

print("\nConfusion (rows=gold, cols=rule):")
print("gold\\rule  "+"  ".join(f"{c:>7}" for c in CATS))
for g in CATS:
    row=conf.get(g,Counter())
    print(f"{g:>9}  "+"  ".join(f"{row.get(c,0):>7}" for c in CATS)+f"   (n={sum(row.values())})")

print("\nMismatches:")
for qid,g,r,c in sorted(mism):
    print(f"  qid {qid}: gold={g} rule={r} ({c})")
