#!/usr/bin/env python3
"""
Classify every MedQA question into the official USMLE Physician Competencies (7-way) + a
finer sub-task, using a strong LLM via an OpenAI-compatible Chat Completions API.

Authoritative rubric: docs/medical_review/USMLE_COMPETENCY_RUBRIC.md
Output (resumable JSONL): results/category_relabel/competency_labels.jsonl
  one line: {"qid", "competency", "subtask", "confidence", "reason", "model"}

Configuration via environment (so you choose the model/provider):
  OPENAI_API_KEY   - required
  OPENAI_BASE_URL  - default https://api.openai.com/v1  (point at any OpenAI-compatible endpoint)
  CLASSIFIER_MODEL - default gpt-4o (use the strongest model you have access to)

Usage:
  export OPENAI_API_KEY=...            # do NOT hardcode
  export CLASSIFIER_MODEL=gpt-4o       # or claude-*, etc. via a compatible proxy
  python scripts/dataset_generation/classify_competencies.py \
      --dataset data/datasets/medqa_full_combined.json \
      --output results/category_relabel/competency_labels.jsonl

Notes:
- Idempotent/resumable: skips qids already in the output file. Safe to re-run / interrupt.
- Sends the full question + options (the option *type* is needed for tie-breaks).
- Greedy (temperature=0) for reproducibility. Retries with backoff.
- question_id is taken from the record's 'question_id' if present, else the array index, so the
  labels align to BOTH the dataset and results/base_runs_full/* (which carry question_id).
"""
import os, sys, json, time, argparse, urllib.request, urllib.error

VALID = {"MK", "PC_DX", "PC_MGMT", "COMM", "PROF", "SBP", "PBL"}

RUBRIC = """You are an expert USMLE item writer. Classify the multiple-choice question into ONE official
USMLE Physician Competency, using the answer OPTIONS to break ties.

Competency codes:
- MK  = Medical Knowledge/Scientific Concepts: mechanisms, pathways, drug mechanism of action,
        genetics, anatomic/physiologic basis, "given an effect determine the cause" (options are processes/mechanisms).
- PC_DX = Patient Care: Diagnosis. Subtasks: hx_pe (predict a physical finding/sign),
        labs_dx_studies (SELECT a study to confirm dx, or PREDICT/INTERPRET a lab/study result),
        formulate_dx (most likely diagnosis / identify disorder or organism),
        prognosis (complications, natural history, prognostic factors).
- PC_MGMT = Patient Care: Management. Subtasks: pharmacotherapy, clinical_interventions
        (treatment/procedure/acute mgmt), health_maint_prevention (screening/prevention/vaccines),
        mixed_management.
- COMM = Communication: most appropriate response/statement by the physician, counseling, breaking news.
- PROF = Professionalism/Legal/Ethical: consent, confidentiality, autonomy/refusal, reporting, minors.
- SBP  = Systems-based Practice & Patient Safety: quality improvement, error analysis, care settings.
- PBL  = Practice-based Learning: biostatistics/epidemiology, study design, screening-test math, literature interpretation.

Tie-breakers:
- "next step in management": options are diagnostic studies -> PC_DX/labs_dx_studies; options are treatments -> PC_MGMT.
- "most likely cause": options are diseases/organisms -> PC_DX/formulate_dx; options are mechanisms -> MK.
- predict a lab/finding result -> PC_DX (not MK). "what to say to patient" -> COMM. statistics/study -> PBL.

Respond with ONLY a JSON object, no prose:
{"competency":"<code>","subtask":"<string>","confidence":"high|med|low","reason":"<=15 words"}"""


def chat(base_url, api_key, model, question, options_text, timeout=60):
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model, "temperature": 0,
        "messages": [
            {"role": "system", "content": RUBRIC},
            {"role": "user", "content": f"Question: {question}\n\nOptions:\n{options_text}"},
        ],
        "max_tokens": 120,
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                headers={"Authorization": f"Bearer {api_key}",
                                         "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read())
    return data["choices"][0]["message"]["content"]


def parse(text):
    import re
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        o = json.loads(m.group(0))
    except Exception:
        return None
    if o.get("competency") not in VALID:
        return None
    return o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="data/datasets/medqa_full_combined.json")
    ap.add_argument("--output", default="results/category_relabel/competency_labels.jsonl")
    ap.add_argument("--limit", type=int, default=None, help="classify only first N (testing)")
    args = ap.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        sys.exit("Set OPENAI_API_KEY (do not hardcode).")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.environ.get("CLASSIFIER_MODEL", "gpt-4o")

    data = json.load(open(args.dataset, encoding="utf-8"))
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    done = set()
    if os.path.exists(args.output):
        for line in open(args.output):
            try: done.add(json.loads(line)["qid"])
            except Exception: pass
    print(f"{len(data)} questions; {len(done)} already labeled; model={model} via {base_url}")

    out = open(args.output, "a", encoding="utf-8")
    n = 0
    for i, item in enumerate(data):
        if args.limit and i >= args.limit:
            break
        qid = int(item.get("question_id", i))
        if qid in done:
            continue
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
            except Exception as e:
                time.sleep(2 ** attempt)
        if not res:
            res = {"competency": "PC_DX", "subtask": "PARSE_FAIL", "confidence": "low", "reason": "fallback"}
        rec = {"qid": qid, "competency": res["competency"], "subtask": res.get("subtask", ""),
               "confidence": res.get("confidence", "med"), "reason": res.get("reason", ""), "model": model}
        out.write(json.dumps(rec, ensure_ascii=False) + "\n"); out.flush()
        n += 1
        if n % 100 == 0:
            print(f"  labeled {n} (total done ~{len(done)+n})")
    out.close()
    print(f"Done. Newly labeled {n}. Output: {args.output}")


if __name__ == "__main__":
    main()
