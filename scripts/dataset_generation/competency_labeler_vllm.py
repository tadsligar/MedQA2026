#!/usr/bin/env python3
"""
v2 COMPETENCY labeler for a LOCAL vLLM OpenAI-compatible endpoint (second annotator = Qwen).

Matches the VALIDATED gpt-5.4-mini setup exactly: same v2 rubric (rules-ON), same LEAD-IN + options
input, same competency parse — imported from batch_label_v2.py so the two annotators are identical
except for the model. Synchronous, resumable. NO reasoning_effort (Qwen is not a reasoning model;
plain temperature=0).

Output (resumable JSONL): results/reasoning_ops/op_labels_v2_qwen.jsonl  {qid, competency, model}
Agreement vs the gpt-5.4-mini labels (results/reasoning_ops/op_labels_v2.jsonl) is the full-set
inter-annotator reliability number for Paper 4 (score with score_competency_agreement.py).

Env (set by the SLURM job against the local vLLM server):
  OPENAI_BASE_URL=http://localhost:8000/v1  OPENAI_API_KEY=EMPTY  CLASSIFIER_MODEL=<served id>
"""
import os, sys, json, time, argparse, urllib.request, urllib.error, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
# reuse the EXACT v2 rubric + lead-in extraction + parser from the batch path
_spec = importlib.util.spec_from_file_location("bl2", os.path.join(HERE, "batch_label_v2.py"))
bl2 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(bl2)


def chat(base_url, api_key, model, item, timeout=60):
    user = f"Question (final sentence only): {bl2.leadin(item['question'])}\n\nOptions:\n{bl2.opts_text(item)}"
    payload = {"model": model, "temperature": 0, "max_tokens": 120,
               "messages": [{"role": "system", "content": bl2.RUBRIC}, {"role": "user", "content": user}]}
    req = urllib.request.Request(base_url.rstrip("/") + "/chat/completions",
                                 data=json.dumps(payload).encode(),
                                 headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default=os.path.join(REPO, "data/datasets/medqa_full_combined.json"))
    ap.add_argument("--output", default=os.path.join(REPO, "results/reasoning_ops/op_labels_v2_qwen.jsonl"))
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    api_key = os.environ.get("OPENAI_API_KEY", "EMPTY")
    base = os.environ.get("OPENAI_BASE_URL", "http://localhost:8000/v1")
    model = os.environ.get("CLASSIFIER_MODEL")
    if not model:
        sys.exit("set CLASSIFIER_MODEL to the served vLLM model id")
    data = json.load(open(a.dataset, encoding="utf-8"))
    os.makedirs(os.path.dirname(a.output), exist_ok=True)
    done = set()
    if os.path.exists(a.output):
        for l in open(a.output):
            try: done.add(json.loads(l)["qid"])
            except Exception: pass
    print(f"{len(data)} questions; {len(done)} done; model={model} via {base}")
    out = open(a.output, "a", encoding="utf-8"); n = 0
    for i, item in enumerate(data):
        if a.limit and i >= a.limit: break
        qid = int(item.get("question_id", i))
        if qid in done: continue
        comp = None
        for attempt in range(5):
            try:
                comp = bl2.parse(chat(base, api_key, model, item))
                if comp: break
            except Exception:
                time.sleep(2 ** attempt)
        rec = {"qid": qid, "competency": comp, "model": model} if comp else \
              {"qid": qid, "competency": None, "parse_fail": True, "model": model}
        out.write(json.dumps(rec, ensure_ascii=False) + "\n"); out.flush(); n += 1
        if n % 500 == 0: print(f"  labeled {n} (total ~{len(done)+n})")
    out.close(); print(f"Done. Newly labeled {n}. Output: {a.output}")


if __name__ == "__main__":
    main()
