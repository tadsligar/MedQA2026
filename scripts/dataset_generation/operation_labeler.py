#!/usr/bin/env python3
"""
Paper 4 labeler — reasoning OPERATION (single-label) + ORGAN-SYSTEM involvement (multi-label Y/N).

One OpenAI-compatible Chat Completions call per question. The SAME code path works for:
  - a hosted API   (OPENAI_BASE_URL=https://api.openai.com/v1 , model gpt-4o-mini, etc.)
  - a local/cluster vLLM server (vLLM exposes /v1/chat/completions):
        python -m vllm.entrypoints.openai.api_server --model Qwen2.5-72B-Instruct --port 8000
        export OPENAI_BASE_URL=http://localhost:8000/v1 ; export OPENAI_API_KEY=EMPTY
        export CLASSIFIER_MODEL=Qwen2.5-72B-Instruct
  -> $0, no data egress (preferred for Boeing/AIAU).

Output (resumable JSONL): results/reasoning_ops/op_labels.jsonl
  {"qid", "reasoning_operation"∈{R,F,B,I,W}, "systems": {<all 15>: "Y"/"N"}, "model"}

The model must return an explicit Y/N for EVERY one of the 15 systems (it is instructed to
adjudicate each independently). The parser does NOT auto-fill: a response missing any of the 15
is treated as a parse failure and retried, so we never silently mask skipped systems.

NO confidence field by design: verbalized LLM self-confidence is poorly calibrated against
correctness (and Paper 1 shows run-to-run stability is the signal that works). Reliability is
quantified externally against a gold sample (score_op_labels.py), not self-reported.
"""
import os, sys, json, time, argparse, urllib.request, urllib.error

OPS = {"R", "F", "B", "I", "W"}
SYSTEMS = ["Cardiovascular", "Respiratory", "Gastrointestinal", "RenalUrinary", "Reproductive",
           "EndocrineMetabolic", "Nervous", "SpecialSenses", "Hematologic", "Immune",
           "Infectious", "Musculoskeletal", "Skin", "Behavioral", "Multisystem"]

RUBRIC = """You are an expert USMLE item analyst. For the multiple-choice question, output TWO things.

(1) reasoning_operation — the TYPE OF INFERENCE the question demands, decided from the ASK
(final question sentence) and the ANSWER-OPTION types. Pick exactly ONE:
  R  Recognition  : recall/identify an expected finding or fact (options are findings/signs/labs).
  F  Mechanistic  : forward reasoning, cause->effect; mechanism/pathophysiology (options are processes/mechanisms).
  B  Diagnostic   : backward reasoning, effect->cause; "most likely diagnosis / underlying cause" (options are diseases/organisms).
  I  Interventional: treatment/management; effect of an action (options are therapies/procedures/drugs).
  W  Workup       : choosing a diagnostic test to reduce uncertainty (options are studies/tests).
Tie-breakers: "next step in management" + treatment options -> I ; + test options -> W.
  "most likely cause" + disease/organism options -> B ; + mechanism/process options -> F.

(2) organ-system involvement — go through the 15 systems below ONE AT A TIME and decide each
INDEPENDENTLY. You MUST output a Y or N for ALL 15 (do not omit any, do not group them).
Answer "Y" ONLY if understanding or answering the question REQUIRES that system's
anatomy/physiology/pathology. Answer "N" if the system appears only as incidental past history,
comorbidity, social history, or a distractor answer option, or is absent. Judge each system on
its own merits — several may be "Y" for a genuinely cross-system question, or only one.
  1. Cardiovascular        2. Respiratory          3. Gastrointestinal
  4. RenalUrinary          5. Reproductive         6. EndocrineMetabolic
  7. Nervous               8. SpecialSenses        9. Hematologic
 10. Immune               11. Infectious          12. Musculoskeletal
 13. Skin                 14. Behavioral          15. Multisystem
(Use Multisystem for biostatistics/genetics/general-principles or a truly systemic process.)

Respond with ONLY this JSON object (all 15 system keys REQUIRED), no prose:
{"reasoning_operation":"<R|F|B|I|W>",
 "systems":{"Cardiovascular":"Y|N","Respiratory":"Y|N","Gastrointestinal":"Y|N",
 "RenalUrinary":"Y|N","Reproductive":"Y|N","EndocrineMetabolic":"Y|N","Nervous":"Y|N",
 "SpecialSenses":"Y|N","Hematologic":"Y|N","Immune":"Y|N","Infectious":"Y|N",
 "Musculoskeletal":"Y|N","Skin":"Y|N","Behavioral":"Y|N","Multisystem":"Y|N"}}"""


def chat(base_url, api_key, model, question, options_text, timeout=60):
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {"model": model, "temperature": 0, "max_tokens": 260,
               "messages": [{"role": "system", "content": RUBRIC},
                            {"role": "user", "content": f"Question: {question}\n\nOptions:\n{options_text}"}]}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]


def parse(text):
    import re
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        o = json.loads(m.group(0))
    except Exception:
        return None
    if o.get("reasoning_operation") not in OPS:
        return None
    sys_in = o.get("systems", {}) or {}
    # require an explicit, valid Y/N for ALL 15 — do NOT auto-fill missing ones (retry instead)
    systems = {}
    for s in SYSTEMS:
        v = str(sys_in.get(s, "")).strip().upper()
        if v.startswith("Y"):
            systems[s] = "Y"
        elif v.startswith("N"):
            systems[s] = "N"
        else:
            return None   # missing/invalid -> parse failure -> retry
    return {"reasoning_operation": o["reasoning_operation"], "systems": systems}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="data/datasets/medqa_full_combined.json")
    ap.add_argument("--output", default="results/reasoning_ops/op_labels.jsonl")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        sys.exit("Set OPENAI_API_KEY (use EMPTY for a local vLLM server). Do not hardcode.")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.environ.get("CLASSIFIER_MODEL", "gpt-4o-mini")

    data = json.load(open(args.dataset, encoding="utf-8"))
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    done = set()
    if os.path.exists(args.output):
        for line in open(args.output):
            try: done.add(json.loads(line)["qid"])
            except Exception: pass
    print(f"{len(data)} questions; {len(done)} already labeled; model={model} via {base_url}")

    out = open(args.output, "a", encoding="utf-8"); n = 0
    for i, item in enumerate(data):
        if args.limit and i >= args.limit: break
        qid = int(item.get("question_id", i))
        if qid in done: continue
        opts = item["options"]
        opts_text = "\n".join(f"{k}. {v}" for k, v in sorted(opts.items())) if isinstance(opts, dict) \
            else "\n".join(f"{chr(65+j)}. {v}" for j, v in enumerate(opts))
        res = None
        for attempt in range(5):
            try:
                res = parse(chat(base_url, api_key, model, item["question"], opts_text))
                if res: break
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503): time.sleep(2 ** attempt); continue
                print("HTTP", e.code, e.reason); time.sleep(2 ** attempt)
            except Exception:
                time.sleep(2 ** attempt)
        if not res:
            # flagged failure (not a real all-N) so downstream analysis can EXCLUDE it
            res = {"reasoning_operation": None, "systems": {}, "parse_fail": True}
        out.write(json.dumps({"qid": qid, **res, "model": model}, ensure_ascii=False) + "\n"); out.flush()
        n += 1
        if n % 200 == 0: print(f"  labeled {n} (total ~{len(done)+n})")
    out.close()
    print(f"Done. Newly labeled {n}. Output: {args.output}")


if __name__ == "__main__":
    main()
