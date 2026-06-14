#!/usr/bin/env python3
"""
Paper 4 v2 labeling — official USMLE competency (MK/DX/MGMT/COMM/PROF/SBP/PBL) via OpenAI Batch API.

Matches the VALIDATED setup (κ=0.829 on the 100 gold): sends the LEAD-IN (final question sentence)
+ options under the v2 rubric (rules ON), reasoning_effort=none. Same chunked auto-runner as
batch_label.py (respects the org enqueued-token cap), independent output so it won't touch the
operation labels.

Output: results/reasoning_ops/op_labels_v2.jsonl  {qid, competency, model}
(Organ-system tags already exist in op_labels.jsonl and can be joined by qid; not re-requested.)

Steps (one command after build):
  pip install --upgrade openai
  export OPENAI_API_KEY=sk-...  ; export CLASSIFIER_MODEL=gpt-5.4-mini
  python3 scripts/dataset_generation/batch_label_v2.py test     # 8-q smoke (own file, no state)
  python3 scripts/dataset_generation/batch_label_v2.py build
  python3 scripts/dataset_generation/batch_label_v2.py auto      # split + submit/poll/append, looped
"""
import os, sys, json, time, re, argparse

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTDIR = os.path.join(REPO, "results", "reasoning_ops")
CHUNKDIR = os.path.join(OUTDIR, "chunks_v2")
INPUT_JSONL = os.path.join(OUTDIR, "batch_input_v2.jsonl")
LABELS_JSONL = os.path.join(OUTDIR, "op_labels_v2.jsonl")
STATE_FILE = os.path.join(OUTDIR, ".chunk_state_v2.json")

MODEL = os.environ.get("CLASSIFIER_MODEL", "gpt-5.4-mini")
REASONING_EFFORT = os.environ.get("REASONING_EFFORT", "none")
MAX_COMPLETION_TOKENS = int(os.environ.get("MAX_COMPLETION_TOKENS", "400"))
ENQUEUE_BUDGET = int(os.environ.get("ENQUEUE_BUDGET", "1700000"))
POLL_SECONDS = int(os.environ.get("POLL_SECONDS", "30"))
CODES = ["MK", "DX", "MGMT", "COMM", "PROF", "SBP", "PBL"]

RUBRIC = """You classify a USMLE multiple-choice question into ONE official USMLE Physician
Tasks/Competency, deciding from the LEAD-IN (final question sentence) + the answer-option types.

Codes (use the OFFICIAL boundaries — note the counterintuitive rules):
- MK  Medical Knowledge / foundational science: "given an effect, DETERMINE THE CAUSE",
      cause/infectious agent/predisposing factor, underlying process/pathway/MECHANISM, drug
      mechanism of action, GENETIC mechanism/INHERITANCE, identify the underlying ANATOMIC
      STRUCTURE/location from findings, nutritional basis. (Options are processes/mechanisms/
      structures/agents.)
- DX  Patient Care: Diagnosis: selects the most likely DIAGNOSIS (names a disorder); PREDICTS the
      most likely additional physical finding or lab/study RESULT; SELECTS/INTERPRETS a study to
      confirm dx (workup); PROGNOSIS/complications/natural history.
- MGMT Patient Care: Management: pharmacotherapy, treatment/clinical intervention, prevention/health
      maintenance/screening, mixed-management choice.
- COMM what to say to patient/family.   - PROF consent/confidentiality/autonomy/minors/reporting/ethics.
- SBP quality improvement / patient safety / care systems.   - PBL biostatistics/epidemiology/study design.

Deterministic rules:
- "most likely cause / underlying mechanism" with PROCESS/MECHANISM options -> MK; with NAMED-DISEASE
  options -> DX. "most likely diagnosis" -> DX. "predict the finding/lab result" -> DX.
- "which anatomic structure/muscle/location" -> MK. "inheritance / mechanism of action" -> MK.
- "next step": study options -> DX(workup); treatment options -> MGMT.
- ethics->PROF ; what-to-say->COMM ; statistics/study-design->PBL.

Respond with ONLY a JSON object: {"competency":"<MK|DX|MGMT|COMM|PROF|SBP|PBL>"}"""


def leadin(question):
    parts = re.split(r'(?<=[.?!])\s+', question.strip())
    qs = [p for p in parts if p.strip().endswith('?')]
    s = qs[-1] if qs else (parts[-1] if parts else question)
    return s if len(s) >= 12 else " ".join(parts[-2:])  # fall back to last 2 sentences if too short


def opts_text(item):
    o = item["options"]
    if isinstance(o, dict):
        return "\n".join(f"{k}. {v}" for k, v in sorted(o.items()))
    return "\n".join(f"{chr(65+j)}. {v}" for j, v in enumerate(o))


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m: return None
    try: o = json.loads(m.group(0))
    except Exception: return None
    return o.get("competency") if o.get("competency") in CODES else None


def _body(item):
    user = f"Question (final sentence only): {leadin(item['question'])}\n\nOptions:\n{opts_text(item)}"
    return {"model": MODEL, "reasoning_effort": REASONING_EFFORT,
            "max_completion_tokens": MAX_COMPLETION_TOKENS,
            "messages": [{"role": "system", "content": RUBRIC}, {"role": "user", "content": user}]}


def build(dataset):
    data = json.load(open(dataset, encoding="utf-8"))
    os.makedirs(OUTDIR, exist_ok=True)
    with open(INPUT_JSONL, "w", encoding="utf-8") as f:
        for i, item in enumerate(data):
            qid = int(item.get("question_id", i))
            f.write(json.dumps({"custom_id": f"q-{qid}", "method": "POST",
                                "url": "/v1/chat/completions", "body": _body(item)}, ensure_ascii=False) + "\n")
    print(f"wrote {len(data)} requests -> {INPUT_JSONL} ({os.path.getsize(INPUT_JSONL)/1e6:.1f} MB); "
          f"model={MODEL} reasoning_effort={REASONING_EFFORT}")


def _est(line):
    b = json.loads(line)["body"]; chars = sum(len(m["content"]) for m in b["messages"])
    return chars//4 + MAX_COMPLETION_TOKENS


def split():
    os.makedirs(CHUNKDIR, exist_ok=True)
    for old in os.listdir(CHUNKDIR): os.remove(os.path.join(CHUNKDIR, old))
    cur, tok, idx, paths = [], 0, 0, []
    for line in open(INPUT_JSONL, encoding="utf-8"):
        t = _est(line)
        if cur and tok + t > ENQUEUE_BUDGET:
            p = os.path.join(CHUNKDIR, f"chunk_{idx:03d}.jsonl"); open(p, "w").writelines(cur)
            paths.append(p); cur, tok, idx = [], 0, idx+1
        cur.append(line); tok += t
    if cur:
        p = os.path.join(CHUNKDIR, f"chunk_{idx:03d}.jsonl"); open(p, "w").writelines(cur); paths.append(p)
    print(f"split into {len(paths)} chunks (budget {ENQUEUE_BUDGET:,} tok)")
    return paths


def _client():
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("pip install --upgrade openai")
    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("export OPENAI_API_KEY=...")
    return OpenAI()


def _retry(fn, tries=10, base=5, what="request"):
    for i in range(tries):
        try: return fn()
        except KeyboardInterrupt: raise
        except Exception as e:
            w = min(base*(i+1), 60)
            print(f"  (transient {what} error: {type(e).__name__}; retry {i+1}/{tries} in {w}s)")
            time.sleep(w)
    raise RuntimeError(f"{what} failed after {tries} retries")


def _load_state(): return json.load(open(STATE_FILE)) if os.path.exists(STATE_FILE) else {}
def _save_state(s): json.dump(s, open(STATE_FILE, "w"), indent=2)


def _done_qids():
    d = set()
    if os.path.exists(LABELS_JSONL):
        for l in open(LABELS_JSONL):
            try: d.add(json.loads(l)["qid"])
            except Exception: pass
    return d


def _append(text):
    done = _done_qids(); ok = fail = 0
    from collections import Counter
    dist = Counter()
    with open(LABELS_JSONL, "a", encoding="utf-8") as out:
        for line in text.splitlines():
            if not line.strip(): continue
            row = json.loads(line); qid = int(row["custom_id"].split("-", 1)[1])
            if qid in done: continue
            try: content = row["response"]["body"]["choices"][0]["message"]["content"]
            except Exception: content = ""
            comp = parse(content) if content else None
            if comp:
                ok += 1; dist[comp] += 1
                out.write(json.dumps({"qid": qid, "competency": comp, "model": MODEL}, ensure_ascii=False)+"\n")
            else:
                fail += 1
                out.write(json.dumps({"qid": qid, "competency": None, "parse_fail": True, "model": MODEL}, ensure_ascii=False)+"\n")
    return ok, fail, dict(dist)


def _submit(c, path):
    up = _retry(lambda: c.files.create(file=open(path, "rb"), purpose="batch"), what="upload")
    b = _retry(lambda: c.batches.create(input_file_id=up.id, endpoint="/v1/chat/completions",
               completion_window="24h", metadata={"project": "MedQA2026", "task": "paper4_v2",
               "chunk": os.path.basename(path)}), what="batch create")
    return b.id


def _print_errors(b):
    errs = getattr(b, "errors", None)
    if errs is None: return
    data = getattr(errs, "data", None) or errs
    try:
        for e in data:
            g = lambda k: getattr(e, k, None) or (e.get(k) if isinstance(e, dict) else None)
            print(f"   [{g('code')}] line={g('line')}: {g('message')}")
    except TypeError:
        print("  ", errs)


def auto():
    c = _client(); paths = split(); state = _load_state()
    for path in paths:
        name = os.path.basename(path); st = state.get(name, {})
        if st.get("status") == "appended":
            print(f"[{name}] done, skip"); continue
        bid = st.get("batch_id")
        if not bid:
            bid = _submit(c, path); state[name] = {"batch_id": bid, "status": "submitted"}; _save_state(state)
            print(f"[{name}] submitted {bid}")
        while True:
            b = _retry(lambda: c.batches.retrieve(bid), what="poll")
            print(f"[{name}] {b.status} {getattr(b,'request_counts',None)}")
            if b.status == "completed":
                text = _retry(lambda: c.files.content(b.output_file_id).text, what="download")
                ok, fail, dist = _append(text)
                state[name] = {"batch_id": bid, "status": "appended", "ok": ok, "fail": fail}; _save_state(state)
                print(f"[{name}] appended ok={ok} fail={fail} dist={dist}")
                break
            if b.status in ("failed", "expired", "cancelled"):
                _print_errors(b); state[name] = {"batch_id": bid, "status": b.status}; _save_state(state)
                sys.exit(f"[{name}] {b.status} — fix and re-run auto (resumes).")
            time.sleep(POLL_SECONDS)
    print(f"\nALL CHUNKS DONE. {len(_done_qids())} labels in {LABELS_JSONL}")


def status():
    c = _client(); state = _load_state()
    if not state: print("no state; run auto."); return
    for name in sorted(state):
        st = state[name]; bid = st.get("batch_id")
        if st.get("status") == "appended": print(f"{name}: appended ok={st.get('ok')} fail={st.get('fail')}"); continue
        if bid:
            b = _retry(lambda: c.batches.retrieve(bid), what="poll")
            print(f"{name}: {b.status} {getattr(b,'request_counts',None)}")
    print(f"labels so far: {len(_done_qids())}")


def test(dataset):
    c = _client(); n = int(os.environ.get("TEST_N", "8"))
    data = json.load(open(dataset, encoding="utf-8"))[:n]
    path = os.path.join(OUTDIR, "batch_test_v2_input.jsonl"); os.makedirs(OUTDIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for i, item in enumerate(data):
            qid = int(item.get("question_id", i))
            f.write(json.dumps({"custom_id": f"q-{qid}", "method": "POST",
                                "url": "/v1/chat/completions", "body": _body(item)}, ensure_ascii=False)+"\n")
    print(f"TEST: {n} reqs, model={MODEL}, reasoning_effort={REASONING_EFFORT}")
    bid = _submit(c, path); print(f"submitted {bid}; polling...")
    while True:
        b = _retry(lambda: c.batches.retrieve(bid), what="poll")
        print(" ", b.status, getattr(b, "request_counts", None))
        if b.status in ("completed", "failed", "expired", "cancelled"): break
        time.sleep(15)
    if getattr(b, "error_file_id", None):
        print("ERRORS:"); print(c.files.content(b.error_file_id).text[:1500])
    if getattr(b, "output_file_id", None):
        ok = fail = 0
        for line in c.files.content(b.output_file_id).text.splitlines():
            if not line.strip(): continue
            row = json.loads(line)
            try: content = row["response"]["body"]["choices"][0]["message"]["content"]
            except Exception: content = ""
            comp = parse(content); print(f"  {row['custom_id']}: {comp or ('PARSE_FAIL '+content[:120])}")
            ok += bool(comp); fail += (not comp)
        print(f"\nparsed OK={ok} fail={fail}  " + ("✓ safe to run auto" if ok and not fail else "✗ check above"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["build", "split", "auto", "status", "test"])
    ap.add_argument("--dataset", default=os.path.join(REPO, "data/datasets/medqa_full_combined.json"))
    a = ap.parse_args()
    if a.step == "build": build(a.dataset)
    elif a.step == "test": test(a.dataset)
    elif a.step == "split": split()
    elif a.step == "auto": auto()
    elif a.step == "status": status()


if __name__ == "__main__":
    main()
