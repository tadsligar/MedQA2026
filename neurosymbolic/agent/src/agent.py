"""
Paper 3 EXP4/EXP5/EXP8/EXP9 — agentic neuro-symbolic reasoner (Algorithm 1).

Maintains a belief over the four answer candidates and adaptively selects evidence functions
(policies A-G) under a budget, updates belief, stops on margin/budget, runs a final verifier
pass, and emits an interpretable evidence trace. Reuses Paper 2's grounding, candidate
analyses, verifiers, and (optionally) an LLM signal from the Paper 1 EXP1 logprob run.

Runs GPU-free when given --llm-logprobs (or none); the LLM-planner policy ('llm_planner')
needs a live vLLM server.

Key flags:
  --policy {fixed,category,uncertainty,utility,redundancy,llm_planner,hybrid}
  --belief {additive,weighted,bayesian}
  --budget N            evidence-function calls per question
  --ablation NAME       disable a component (see ABLATIONS)
Emits base-run schema + evidence_trace, belief_history, functions_called, n_steps, confidence.

CLI:
  python -m neurosymbolic.agent.src.agent --index data/umls/umls_2025AB_index.db \
     --llm-logprobs results/base_runs_logprobs/qwen25_32b/temp0.0_run1_results.json \
     --policy utility --belief weighted --budget 6 \
     --output results/agent/eval/full_utility_results.json
"""
import json, os, sys, math, argparse, random
from pathlib import Path

_HERE = os.path.dirname(__file__)
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "..", "..", "umls_verifier", "src"))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "chain_of_verification", "src"))
from umls_index import UMLSIndex            # noqa
from grounding import ground_question        # noqa
from verifiers import run_verifiers          # noqa
from llm_client import LLMClient             # noqa
from cove import build_candidate_analyses, parse_demographics  # noqa
import evidence_functions as EF              # noqa

random.seed(42)
LETTERS = ["A", "B", "C", "D"]
ABLATIONS = {
    "none", "no_umls", "no_category", "fixed_sequence", "no_belief_update",
    "no_contradiction", "no_redundancy", "no_semtype", "no_pathophys",
    "no_contraindication", "llm_only_functions", "symbolic_only_functions",
    "random_selection", "no_adaptivity", "no_final_verify",
}


def softmax(scores):
    m = max(scores.values())
    ex = {k: math.exp(v - m) for k, v in scores.items()}
    z = sum(ex.values()) or 1
    return {k: ex[k] / z for k in scores}


def entropy(belief):
    return -sum(p * math.log(p + 1e-12) for p in belief.values())


def margin(belief):
    s = sorted(belief.values(), reverse=True)
    return (s[0] - s[1]) if len(s) > 1 else s[0]


def init_belief(llm_probs, mode):
    if llm_probs:
        return softmax({l: math.log((llm_probs.get(l) or 0.01) + 1e-6) for l in LETTERS})
    return {l: 0.25 for l in LETTERS}


def candidate_function_pool(category, ablation):
    pool = EF.applicable_functions(category if ablation != "no_category" else "Other/Mixed")
    drop = {
        "no_contradiction": {"contradictions"},
        "no_semtype": {"answer_semantic_type"},
        "no_pathophys": {"pathophysiology_chain", "mechanism_consistency"},
        "no_contraindication": {"treatment_contraindication"},
    }.get(ablation, set())
    if ablation == "symbolic_only_functions":
        pool = [f for f in pool if f not in {"temporal_consistency"}]
    return [f for f in pool if f not in drop]


def pick_function(pool, used, belief, analyses, case, idx, policy, ablation):
    """Return the next evidence-function name per the selection policy."""
    remaining = [f for f in pool if f not in used]
    if not remaining:
        return None
    if ablation == "random_selection" or policy == "fixed":
        return remaining[0] if policy == "fixed" else random.choice(remaining)
    if policy == "category":
        return remaining[0]  # category-ordered (pool is already category-filtered)
    # uncertainty / utility / redundancy: estimate expected |belief change| of each fn
    def expected_delta(fname):
        fn = EF.LIBRARY[fname][0]
        deltas, _ = fn(case, analyses, idx)
        # relevance: how much would top-2 candidates separate
        top2 = sorted(belief, key=lambda l: -belief[l])[:2]
        rel = abs(deltas.get(top2[0], 0) - deltas.get(top2[1], 0)) if len(top2) == 2 else 0
        return rel
    scored = {f: expected_delta(f) for f in remaining}
    if policy == "redundancy" and ablation != "no_redundancy":
        # penalize functions similar to already-used ones (same family prefix)
        for f in scored:
            fam = f.split("_")[0]
            if any(u.split("_")[0] == fam for u in used):
                scored[f] *= 0.5
    return max(scored, key=scored.get)


def llm_plan_next(remaining, item, client):
    prompt = ("Which ONE check is most useful next to decide this medical question? "
              f"Options: {remaining}. Reply with just the name.\nQ: {item['question'][:300]}")
    out = client.generate(prompt, temperature=0.0, max_tokens=16)
    txt = (out.get("text") or "").strip().lower()
    for f in remaining:
        if f in txt:
            return f
    return remaining[0]


def run_agent_on_item(item, idx, args, client, llm_probs):
    cat = item.get("validated_category", "Other/Mixed")
    age, sex = parse_demographics(item["question"])
    grounded = ground_question(item, idx) if args.ablation != "no_umls" else \
        {"stem_concepts": [], "option_concepts": {l: [] for l in item["options"]},
         "grounding_coverage": 0.0}
    case = {"category": cat, "age": age, "sex": sex,
            "grounding_coverage": grounded["grounding_coverage"],
            "stem_concepts": grounded["stem_concepts"]}
    analyses = build_candidate_analyses(item, grounded, idx)

    belief = init_belief(llm_probs if args.ablation != "llm_only_functions" or True else None,
                         args.belief)
    pool = candidate_function_pool(cat, args.ablation)
    used, trace, history = [], [], [dict(belief)]

    budget = args.budget if args.ablation != "no_adaptivity" else len(pool)
    for t in range(budget):
        if args.ablation == "fixed_sequence":
            fname = pool[t] if t < len(pool) else None
        elif args.policy == "llm_planner" and client is not None:
            remaining = [f for f in pool if f not in used]
            fname = llm_plan_next(remaining, item, client) if remaining else None
        else:
            fname = pick_function(pool, used, belief, analyses, case, idx, args.policy, args.ablation)
        if fname is None:
            break
        used.append(fname)
        fn = EF.LIBRARY[fname][0]
        deltas, detail = fn(case, analyses, idx)
        if args.ablation != "no_belief_update":
            if args.belief == "additive":
                raw = {l: math.log(belief[l] + 1e-9) + deltas[l] for l in LETTERS}
                belief = softmax(raw)
            else:  # weighted / bayesian-ish: temperature-scaled additive in log space
                raw = {l: math.log(belief[l] + 1e-9) + args.alpha * deltas[l] for l in LETTERS}
                belief = softmax(raw)
        trace.append({"step": t + 1, "function": fname, "detail": detail,
                      "deltas": {l: round(deltas[l], 3) for l in LETTERS},
                      "belief": {l: round(belief[l], 3) for l in LETTERS}})
        history.append(dict(belief))
        # adaptive stopping
        if args.ablation != "no_adaptivity" and args.policy not in ("fixed",):
            if margin(belief) >= args.margin_threshold or entropy(belief) <= args.entropy_threshold:
                break

    # final verification pass
    flags = {}
    if args.ablation != "no_final_verify":
        for l in LETTERS:
            v, sev = run_verifiers(analyses[l], case, idx)
            flags[l] = v
            belief[l] = belief[l] * math.exp(-0.3 * sev)
        z = sum(belief.values()) or 1
        belief = {l: belief[l] / z for l in LETTERS}

    pick = max(belief, key=belief.get)
    return pick, belief, trace, history, used, flags, grounded["grounding_coverage"]


def main():
    ap = argparse.ArgumentParser(description="Agentic neuro-symbolic reasoner (Paper 3)")
    ap.add_argument("--index", required=True)
    ap.add_argument("--dataset", default="data/datasets/medqa_focused_1030.json")
    ap.add_argument("--llm-logprobs", default=None, help="Paper 1 EXP1 option_probs (GPU-free LLM signal)")
    ap.add_argument("--vllm-url", default=None, help="for --policy llm_planner")
    ap.add_argument("--policy", default="utility",
                    choices=["fixed", "category", "uncertainty", "utility", "redundancy",
                             "llm_planner", "hybrid"])
    ap.add_argument("--belief", default="weighted", choices=["additive", "weighted", "bayesian"])
    ap.add_argument("--budget", type=int, default=6)
    ap.add_argument("--alpha", type=float, default=1.0)
    ap.add_argument("--margin-threshold", type=float, default=0.6)
    ap.add_argument("--entropy-threshold", type=float, default=0.2)
    ap.add_argument("--ablation", default="none", choices=sorted(ABLATIONS))
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    idx = UMLSIndex(args.index)
    data = json.load(open(args.dataset, encoding="utf-8"))
    lp = None
    if args.llm_logprobs and os.path.exists(args.llm_logprobs):
        lp = json.load(open(args.llm_logprobs)); lp.sort(key=lambda x: x["question_id"])
    client = LLMClient(args.vllm_url) if (args.vllm_url and args.policy == "llm_planner") else None

    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    results = []
    for qid, item in enumerate(data):
        correct = next((l for l, t in item["options"].items() if t == item["answer"]), "A")
        llm_probs = (lp[qid].get("option_probs") if lp else None)
        pick, belief, trace, history, used, flags, cov = run_agent_on_item(
            item, idx, args, client, llm_probs)
        results.append({
            "question_id": qid, "category": item.get("validated_category", "Other/Mixed"),
            "correct": correct, "predicted": pick, "is_correct": pick == correct,
            "tokens": 0, "latency": 0.0, "response": f"{args.policy}/{args.belief}"[:200],
            "confidence": round(max(belief.values()), 3),
            "n_steps": len(used), "functions_called": used,
            "flags": {l: [v["verifier"] for v in flags.get(l, [])] for l in LETTERS},
            "grounding_coverage": cov, "evidence_trace": trace,
            "policy": args.policy, "belief_mode": args.belief, "ablation": args.ablation,
        })
        if (qid + 1) % 200 == 0:
            acc = sum(r["is_correct"] for r in results) / len(results) * 100
            steps = sum(r["n_steps"] for r in results) / len(results)
            print(f"  [{qid+1}/{len(data)}] {args.policy}/{args.belief} acc={acc:.2f}% avg_steps={steps:.1f}")

    acc = sum(r["is_correct"] for r in results) / len(results) * 100
    avg_steps = sum(r["n_steps"] for r in results) / len(results)
    json.dump(results, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"Agent {args.policy}/{args.belief} ablation={args.ablation}: "
          f"acc={acc:.2f}% avg_steps={avg_steps:.2f} -> {out}")
    idx.close()


if __name__ == "__main__":
    main()
