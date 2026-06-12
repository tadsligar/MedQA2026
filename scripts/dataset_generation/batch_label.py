#!/usr/bin/env python3
"""
Paper 4 labeling via the OpenAI **Batch API** (50% cheaper), with automatic chunking to respect
the per-org **enqueued-token limit** (e.g. 2,000,000 tokens for gpt-5.4-mini). The full 12,723-q
file is ~10M+ tokens, so it is split into sub-limit chunks submitted SEQUENTIALLY (the cap is on
concurrently enqueued tokens), each parsed and appended to one resumable op_labels.jsonl.

Reuses the rubric / 15-system schema / strict parser from operation_labeler.py (all 15 systems
required; no primary_system; no confidence). gpt-5-family reasoning params: reasoning_effort,
max_completion_tokens.

Typical use (one command after build):
  pip install openai
  export OPENAI_API_KEY=sk-...
  export CLASSIFIER_MODEL=gpt-5.4-mini
  python scripts/dataset_generation/batch_label.py build      # -> batch_input.jsonl
  python scripts/dataset_generation/batch_label.py auto       # split + submit/poll/append, looped

Manual/diagnostic steps also available: split, submit, poll, fetch (operate on a single chunk).
"""
import os, sys, json, time, argparse, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUTDIR = os.path.join(REPO, "results", "reasoning_ops")
CHUNKDIR = os.path.join(OUTDIR, "chunks")
INPUT_JSONL = os.path.join(OUTDIR, "batch_input.jsonl")
LABELS_JSONL = os.path.join(OUTDIR, "op_labels.jsonl")
STATE_FILE = os.path.join(OUTDIR, ".chunk_state.json")

_spec = importlib.util.spec_from_file_location("ol", os.path.join(HERE, "operation_labeler.py"))
ol = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(ol)

MODEL = os.environ.get("CLASSIFIER_MODEL", "gpt-5.4-mini")
REASONING_EFFORT = os.environ.get("REASONING_EFFORT", "minimal")
MAX_COMPLETION_TOKENS = int(os.environ.get("MAX_COMPLETION_TOKENS", "512"))
# stay safely under the org enqueued-token cap (2,000,000); count input + reserved output
ENQUEUE_BUDGET = int(os.environ.get("ENQUEUE_BUDGET", "1700000"))
POLL_SECONDS = int(os.environ.get("POLL_SECONDS", "30"))


def _opts_text(item):
    opts = item["options"]
    if isinstance(opts, dict):
        return "\n".join(f"{k}. {v}" for k, v in sorted(opts.items()))
    return "\n".join(f"{chr(65+j)}. {v}" for j, v in enumerate(opts))


def _est_tokens(line):
    """rough enqueued-token estimate for one request line = input chars/4 + reserved output."""
    body = json.loads(line)["body"]
    chars = sum(len(m["content"]) for m in body["messages"])
    return chars // 4 + MAX_COMPLETION_TOKENS


def build(dataset):
    data = json.load(open(dataset, encoding="utf-8"))
    os.makedirs(OUTDIR, exist_ok=True)
    n = 0
    with open(INPUT_JSONL, "w", encoding="utf-8") as f:
        for i, item in enumerate(data):
            qid = int(item.get("question_id", i))
            body = {"model": MODEL, "reasoning_effort": REASONING_EFFORT,
                    "max_completion_tokens": MAX_COMPLETION_TOKENS,
                    "messages": [{"role": "system", "content": ol.RUBRIC},
                                 {"role": "user", "content": f"Question: {item['question']}\n\nOptions:\n{_opts_text(item)}"}]}
            f.write(json.dumps({"custom_id": f"q-{qid}", "method": "POST",
                                "url": "/v1/chat/completions", "body": body}, ensure_ascii=False) + "\n")
            n += 1
    print(f"wrote {n} requests -> {INPUT_JSONL} ({os.path.getsize(INPUT_JSONL)/1e6:.1f} MB)")
    print(f"model={MODEL} reasoning_effort={REASONING_EFFORT} max_completion_tokens={MAX_COMPLETION_TOKENS}")


def split():
    """split INPUT_JSONL into chunk files each under ENQUEUE_BUDGET estimated tokens."""
    os.makedirs(CHUNKDIR, exist_ok=True)
    for old in os.listdir(CHUNKDIR):
        os.remove(os.path.join(CHUNKDIR, old))
    chunks, cur, tok, idx = [], [], 0, 0
    for line in open(INPUT_JSONL, encoding="utf-8"):
        t = _est_tokens(line)
        if cur and tok + t > ENQUEUE_BUDGET:
            p = os.path.join(CHUNKDIR, f"chunk_{idx:03d}.jsonl")
            open(p, "w", encoding="utf-8").writelines(cur)
            chunks.append((p, len(cur), tok)); cur, tok, idx = [], 0, idx + 1
        cur.append(line); tok += t
    if cur:
        p = os.path.join(CHUNKDIR, f"chunk_{idx:03d}.jsonl")
        open(p, "w", encoding="utf-8").writelines(cur)
        chunks.append((p, len(cur), tok))
    print(f"split into {len(chunks)} chunks (budget {ENQUEUE_BUDGET:,} tok/chunk):")
    for p, nreq, t in chunks:
        print(f"  {os.path.basename(p)}: {nreq} reqs, ~{t:,} tok")
    return [p for p, _, _ in chunks]


def _client():
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("pip install --upgrade openai  (need >=1.x)")
    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("export OPENAI_API_KEY=...  (do not hardcode)")
    return OpenAI()


def _retry(fn, tries=10, base=5, what="request"):
    """Run a network call, surviving transient connection/DNS/5xx blips with backoff."""
    for i in range(tries):
        try:
            return fn()
        except KeyboardInterrupt:
            raise
        except Exception as e:
            wait = min(base * (i + 1), 60)
            print(f"  (transient {what} error: {type(e).__name__}; retry {i+1}/{tries} in {wait}s)")
            time.sleep(wait)
    raise RuntimeError(f"{what} failed after {tries} retries")


def _load_state():
    return json.load(open(STATE_FILE)) if os.path.exists(STATE_FILE) else {}


def _save_state(s):
    json.dump(s, open(STATE_FILE, "w"), indent=2)


def _done_qids():
    done = set()
    if os.path.exists(LABELS_JSONL):
        for line in open(LABELS_JSONL):
            try: done.add(json.loads(line)["qid"])
            except Exception: pass
    return done


def _append_results(text):
    """parse a batch output file's text, append parsed rows to op_labels.jsonl (skip dupes)."""
    done = _done_qids(); ok = fail = 0
    with open(LABELS_JSONL, "a", encoding="utf-8") as out:
        for line in text.splitlines():
            if not line.strip(): continue
            row = json.loads(line)
            qid = int(row["custom_id"].split("-", 1)[1])
            if qid in done: continue
            try:
                content = row["response"]["body"]["choices"][0]["message"]["content"]
            except Exception:
                content = ""
            res = ol.parse(content) if content else None
            if res:
                ok += 1
                out.write(json.dumps({"qid": qid, **res, "model": MODEL}, ensure_ascii=False) + "\n")
            else:
                fail += 1
                out.write(json.dumps({"qid": qid, "reasoning_operation": None, "systems": {},
                                      "parse_fail": True, "model": MODEL}, ensure_ascii=False) + "\n")
    return ok, fail


def _submit_file(c, path):
    up = _retry(lambda: c.files.create(file=open(path, "rb"), purpose="batch"), what="file upload")
    b = _retry(lambda: c.batches.create(input_file_id=up.id, endpoint="/v1/chat/completions",
                                        completion_window="24h",
                                        metadata={"project": "MedQA2026", "task": "paper4_labels",
                                                  "chunk": os.path.basename(path)}), what="batch create")
    return b.id


def _print_errors(b):
    errs = getattr(b, "errors", None)
    if errs is None: return
    data = getattr(errs, "data", None) or errs
    try:
        for e in data:
            g = (lambda k: getattr(e, k, None) or (e.get(k) if isinstance(e, dict) else None))
            print(f"   [{g('code')}] line={g('line')}: {g('message')}")
    except TypeError:
        print("  ", errs)


def auto():
    """Split, then for each chunk: submit -> poll to completion -> append -> next. Resumable."""
    c = _client()
    chunk_paths = split()
    state = _load_state()
    for path in chunk_paths:
        name = os.path.basename(path)
        st = state.get(name, {})
        if st.get("status") == "appended":
            print(f"[{name}] already done, skipping"); continue
        bid = st.get("batch_id")
        if not bid:
            bid = _submit_file(c, path)
            state[name] = {"batch_id": bid, "status": "submitted"}; _save_state(state)
            print(f"[{name}] submitted batch {bid}")
        while True:
            b = _retry(lambda: c.batches.retrieve(bid), what="poll")
            rc = getattr(b, "request_counts", None)
            print(f"[{name}] {b.status} {rc}")
            if b.status == "completed":
                text = _retry(lambda: c.files.content(b.output_file_id).text, what="download")
                ok, fail = _append_results(text)
                state[name] = {"batch_id": bid, "status": "appended", "ok": ok, "fail": fail}; _save_state(state)
                print(f"[{name}] appended ok={ok} fail={fail}")
                break
            if b.status in ("failed", "expired", "cancelled"):
                _print_errors(b)
                state[name] = {"batch_id": bid, "status": b.status}; _save_state(state)
                sys.exit(f"[{name}] {b.status} — fix and re-run `auto` (it resumes).")
            time.sleep(POLL_SECONDS)
    total = len(_done_qids())
    print(f"\nALL CHUNKS DONE. {total} labels in {LABELS_JSONL}")


# ---- single-chunk manual helpers (diagnostics) ----
def submit():
    c = _client(); bid = _submit_file(c, INPUT_JSONL)
    json.dump({"single": {"batch_id": bid}}, open(STATE_FILE, "w"))
    print(f"submitted batch {bid}")


def poll():
    c = _client(); bid = _load_state().get("single", {}).get("batch_id")
    b = c.batches.retrieve(bid)
    print(f"batch {bid}: status={b.status} counts={getattr(b,'request_counts',None)}")
    if b.status in ("failed", "expired", "cancelled"): _print_errors(b)


def fetch():
    c = _client(); bid = _load_state().get("single", {}).get("batch_id")
    b = c.batches.retrieve(bid)
    if b.status != "completed": sys.exit(f"not complete (status={b.status})")
    ok, fail = _append_results(c.files.content(b.output_file_id).text)
    print(f"appended ok={ok} fail={fail} -> {LABELS_JSONL}")


def status():
    """Read-only progress check across all chunks (does not submit or advance anything)."""
    c = _client(); state = _load_state()
    if not state:
        print("no chunk state yet — run `auto`."); return
    for name in sorted(k for k in state if k != "single"):
        st = state[name]; bid = st.get("batch_id")
        if st.get("status") == "appended":
            print(f"{name}: appended (ok={st.get('ok')} fail={st.get('fail')})"); continue
        if bid:
            b = _retry(lambda: c.batches.retrieve(bid), what="poll")
            print(f"{name}: {b.status} {getattr(b,'request_counts',None)}  ({bid})")
        else:
            print(f"{name}: {st.get('status')}")
    print(f"\nlabels so far in op_labels.jsonl: {len(_done_qids())}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["build", "split", "auto", "status", "submit", "poll", "fetch"])
    ap.add_argument("--dataset", default=os.path.join(REPO, "data/datasets/medqa_full_combined.json"))
    a = ap.parse_args()
    {"build": lambda: build(a.dataset), "split": split, "auto": auto, "status": status,
     "submit": submit, "poll": poll, "fetch": fetch}[a.step]()


if __name__ == "__main__":
    main()
