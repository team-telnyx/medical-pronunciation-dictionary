#!/usr/bin/env python3
"""
Automated before/after pronunciation eval.

Replaces the manual "judge the pair blind" step in CONTRIBUTING.md with an
AI pipeline: render both clips on a real Telnyx voice, transcribe both
blind via STT, score similarity to the target pronunciation, then have an
LLM judge call HELPS / WASH / HURTS the way a human listener would.

Same methodology as the original telnyx_naturalhd_audit.csv:
- before: TTS with no pronunciation dictionary attached
- after:  TTS with a real Telnyx pronunciation_dict_id attached
- same carrier sentence for both
- transcription is blind: the transcriber never sees the target term

Usage:
  export TELNYX_API_KEY=...
  export LITELLM_KEY=...
  export LITELLM_BASE=...   # e.g. http://litellm-aiswe.query.prod.telnyx.io:4000/v1
  python3 src/eval_pronunciation.py --sample 25          # validation sample
  python3 src/eval_pronunciation.py --all                # full 966-term corpus
  python3 src/eval_pronunciation.py --all --workers 8    # more concurrency

Resumable: every completed term is appended to the checkpoint file
immediately. Re-running the same command skips terms already checkpointed.

Output: data/eval_checkpoint.jsonl (raw, resumable)
        data/telnyx_naturalhd_audit_ai.csv (final, same schema as the
        original audit) + a diff report against the stored verdicts.
"""
from __future__ import annotations

import argparse
import csv
import difflib
import json
import os
import random
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

TELNYX_KEY = os.environ.get("TELNYX_API_KEY", "")
LITELLM_KEY = os.environ.get("LITELLM_KEY", "")
LITELLM_BASE = os.environ.get("LITELLM_BASE", "")
JUDGE_MODEL = "MiniMax-M3-MXFP8-nothink"

# TTS is generously rate-limited (2000 req/s per the API's own response
# headers), so a small concurrency cap is just politeness.
TELNYX_TTS_CONCURRENCY = 4
_tts_gate = threading.Semaphore(TELNYX_TTS_CONCURRENCY)

# STT (Whisper) is rate-limited to 1 request/second ACCOUNT-WIDE (confirmed
# via x-ratelimit-limit: 1, 1;w=1 on the transcriptions endpoint). This is
# the real bottleneck: every call must be serialized with a minimum gap,
# not just capped in concurrency, or the API 429s/503s almost every call.
STT_MIN_INTERVAL = 1.05
_stt_lock = threading.Lock()
_stt_last_call = [0.0]


def _throttle_stt():
    with _stt_lock:
        now = time.monotonic()
        wait = _stt_last_call[0] + STT_MIN_INTERVAL - now
        if wait > 0:
            time.sleep(wait)
        _stt_last_call[0] = time.monotonic()

API_BASE = "https://api.telnyx.com/v2"
VOICE = "Telnyx.NaturalHD.astra"
# openai/whisper-large-v3-turbo (the model the telnyx-toolkit STT tool
# defaults to) is returning HTTP 500 on every call as of 2026-08-26,
# confirmed via isolated curl calls unrelated to rate limiting.
# distil-whisper/distil-large-v2 works but rejects an explicit `language`
# field, so the multipart body below omits it.
STT_MODEL = "distil-whisper/distil-large-v2"
DICT_BATCH_SIZE = 100  # Telnyx pronunciation dict cap

BASE = Path(__file__).parent.parent
INPUT_FILE = BASE / "data" / "terms_master.json"
STORED_AUDIT = BASE / "data" / "telnyx_naturalhd_audit.csv"
CHECKPOINT_FILE = BASE / "data" / "eval_checkpoint.jsonl"
CONFIRM_CHECKPOINT_FILE = BASE / "data" / "eval_checkpoint_confirm.jsonl"
AUDIO_TMP = BASE / "data" / "audio" / "_eval_tmp"

CARRIERS = {
    "drug": "Please take your {t} as prescribed.",
    "clinical": "The patient was diagnosed with {t}.",
    "anatomical": "The biopsy shows inflammation in the {t}.",
    "acronym": "The patient has a history of {t}.",
}

JUDGE_SYSTEM = """You judge whether a TTS pronunciation dictionary entry helped, did nothing, \
or hurt. You are told what a listener transcribed hearing the SAME sentence \
rendered twice: once with no dictionary attached, once with the dictionary \
attached. Neither transcript was produced with knowledge of the target term.

Reply with exactly one line, pipe-separated, no other text:
VERDICT|one-sentence reason

VERDICT is exactly one of: HELPS, WASH, HURTS
- HELPS: the "with dictionary" transcript clearly recovers the correct term/expansion \
and the "without dictionary" transcript did not.
- HURTS: the "without dictionary" transcript already got it right (or close), and the \
"with dictionary" transcript is worse, garbled, or fragmented.
- WASH: no meaningful difference either way (both correct, both wrong, or both equally \
unclear)."""


def _http_json(url, payload=None, method=None, headers=None, timeout=60):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode() if payload is not None else None,
        method=method,
        headers=headers or {},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read()
    return json.loads(body) if body else {}


def telnyx_headers():
    return {"Authorization": f"Bearer {TELNYX_KEY}", "Content-Type": "application/json"}


def create_dict(name, items):
    data = _http_json(f"{API_BASE}/pronunciation_dicts", {"name": name, "items": items},
                       headers=telnyx_headers())["data"]
    return data["id"]


def delete_dict(dict_id):
    req = urllib.request.Request(f"{API_BASE}/pronunciation_dicts/{dict_id}",
                                  method="DELETE", headers=telnyx_headers())
    urllib.request.urlopen(req, timeout=30)


def _backoff_seconds(exc, attempt):
    if isinstance(exc, urllib.error.HTTPError):
        retry_after = exc.headers.get("Retry-After") if exc.headers else None
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
        if exc.code == 429:
            return min(30, 5 * (2 ** attempt))
    return min(20, 2 ** attempt)


def tts(text, dict_id=None, retries=6):
    payload = {"text": text, "voice": VOICE, "output_format": "mp3"}
    if dict_id:
        payload["pronunciation_dict_id"] = dict_id
    for attempt in range(retries):
        try:
            with _tts_gate:
                req = urllib.request.Request(
                    f"{API_BASE}/text-to-speech/speech",
                    data=json.dumps(payload).encode(),
                    headers=telnyx_headers(),
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return resp.read()
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            if attempt == retries - 1:
                raise
            time.sleep(_backoff_seconds(exc, attempt))


def stt(audio_bytes, retries=6):
    filename = f"{uuid.uuid4().hex}.mp3"
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex[:16]}"
    body = []
    body.append(f"--{boundary}".encode())
    body.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode())
    body.append(b"Content-Type: audio/mpeg")
    body.append(b"")
    body.append(audio_bytes)
    body.append(f"--{boundary}".encode())
    body.append(b'Content-Disposition: form-data; name="model"')
    body.append(b"")
    body.append(STT_MODEL.encode())
    body.append(f"--{boundary}--".encode())
    body.append(b"")
    body_bytes = b"\r\n".join(body)

    for attempt in range(retries):
        try:
            _throttle_stt()
            req = urllib.request.Request(
                f"{API_BASE}/ai/audio/transcriptions",
                data=body_bytes,
                headers={
                    "Authorization": f"Bearer {TELNYX_KEY}",
                    "Content-Type": f"multipart/form-data; boundary={boundary}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("text", "").strip()
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            if attempt == retries - 1:
                raise
            time.sleep(_backoff_seconds(exc, attempt))


def similarity(a, b):
    return difflib.SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def compute_gain(target, heard_without, heard_with):
    before_sim = similarity(target, heard_without)
    after_sim = similarity(target, heard_with)
    return round(after_sim - before_sim, 3)


def judge(text, category, target, heard_without, heard_with, gain, retries=3):
    user = (
        f"Category: {category}\n"
        f"Term: {text}\n"
        f"Target pronunciation goal: {target}\n"
        f"Heard WITHOUT dictionary: {heard_without or '(silence/no clear words)'}\n"
        f"Heard WITH dictionary: {heard_with or '(silence/no clear words)'}\n"
        f"Similarity gain (after - before, -1 to 1): {gain}"
    )
    payload = {
        "model": JUDGE_MODEL,
        "messages": [
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": user},
        ],
        "max_tokens": 100,
        "temperature": 0,
    }
    for attempt in range(retries):
        try:
            resp = _http_json(
                f"{LITELLM_BASE}/chat/completions", payload, method="POST",
                headers={"Authorization": f"Bearer {LITELLM_KEY}", "Content-Type": "application/json"},
                timeout=30,
            )
            content = resp["choices"][0]["message"]["content"].strip()
            verdict, _, reason = content.partition("|")
            verdict = verdict.strip().upper()
            if verdict not in ("HELPS", "WASH", "HURTS"):
                verdict = "WASH"
                reason = f"unparsed judge output: {content!r}"
            return verdict, reason.strip()
        except Exception as exc:
            if attempt == retries - 1:
                return "WASH", f"judge call failed: {exc}"
            time.sleep(2 ** attempt)


def eval_one_term(term, dict_id):
    text, category, alias = term["text"], term["category"], term["alias"]
    target = alias if category == "acronym" else text
    sentence = CARRIERS[category].format(t=text)

    audio_before = tts(sentence, dict_id=None)
    audio_after = tts(sentence, dict_id=dict_id)
    heard_without = stt(audio_before)
    heard_with = stt(audio_after)
    gain = compute_gain(target, heard_without, heard_with)
    verdict, reason = judge(text, category, target, heard_without, heard_with, gain)

    return {
        "text": text,
        "category": category,
        "alias": alias,
        "verdict": verdict,
        "gain": gain,
        "heard_without_dict": heard_without,
        "heard_with_dict": heard_with,
        "sentence": sentence,
        "judge_reason": reason,
        "stored_verdict": term.get("telnyx_naturalhd_verdict", ""),
        "stt_model": STT_MODEL,
    }


def load_terms():
    with open(INPUT_FILE, encoding="utf-8") as f:
        return json.load(f)


def load_checkpoint(path=CHECKPOINT_FILE):
    done = {}
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                done[row["text"]] = row
    return done


def append_checkpoint(row, path=CHECKPOINT_FILE):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def chunked(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def run_batch(batch, worker_count, batch_idx, total_batches, checkpoint_path=CHECKPOINT_FILE, label="batch"):
    items = [{"text": t["text"], "type": "alias", "alias": t["alias"]}
              for t in batch if t["alias"] and t["alias"] != t["text"]]
    dict_name = f"eval-pronunciation-{label}-{uuid.uuid4().hex[:8]}"
    dict_id = create_dict(dict_name, items)
    print(f"[{label} {batch_idx}/{total_batches}] dict {dict_id}, {len(batch)} terms", flush=True)
    try:
        with ThreadPoolExecutor(max_workers=worker_count) as pool:
            futures = {pool.submit(eval_one_term, term, dict_id): term for term in batch}
            for fut in as_completed(futures):
                term = futures[fut]
                try:
                    row = fut.result()
                except Exception as exc:
                    row = {
                        "text": term["text"], "category": term["category"], "alias": term["alias"],
                        "verdict": "ERROR", "gain": 0.0, "heard_without_dict": "", "heard_with_dict": "",
                        "sentence": "", "judge_reason": f"pipeline error: {exc}",
                        "stored_verdict": term.get("telnyx_naturalhd_verdict", ""),
                    }
                append_checkpoint(row, path=checkpoint_path)
                match = "match" if row["verdict"] == row["stored_verdict"] else "DIFF"
                print(f"  {row['text']:30s} {row['verdict']:6s} (stored: {row['stored_verdict']:6s}, {match}) gain={row['gain']}", flush=True)
    finally:
        delete_dict(dict_id)


def run_pass(terms_to_run, worker_count, checkpoint_path, label, max_retry_rounds=2):
    for round_num in range(max_retry_rounds + 1):
        done = load_checkpoint(checkpoint_path)
        # ERROR rows don't count as done: a later successful line for the
        # same term overwrites them on reload, so it's safe to retry.
        pending = [t for t in terms_to_run
                   if t["text"] not in done or done[t["text"]]["verdict"] == "ERROR"]
        if not pending:
            break
        if round_num > 0:
            print(f"[{label}] retry round {round_num}: {len(pending)} term(s) still ERROR", flush=True)
        total_batches = (len(pending) + DICT_BATCH_SIZE - 1) // DICT_BATCH_SIZE
        for batch_idx, batch in enumerate(chunked(pending, DICT_BATCH_SIZE), start=1):
            run_batch(batch, worker_count, batch_idx, total_batches, checkpoint_path=checkpoint_path, label=label)
    done = load_checkpoint(checkpoint_path)
    return {t["text"]: done[t["text"]] for t in terms_to_run if t["text"] in done}


def write_outputs(rows, confirm_rows):
    out_csv = BASE / "data" / "telnyx_naturalhd_audit_ai.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "text", "category", "alias", "verdict", "gain",
            "heard_without_dict", "heard_with_dict", "sentence", "judge_reason", "stored_verdict",
            "stt_model",
        ])
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in writer.fieldnames})

    agree = sum(1 for r in rows if r["verdict"] == r["stored_verdict"])
    diffs = [r for r in rows if r["verdict"] != r["stored_verdict"] and r["stored_verdict"]]
    errors = [r for r in rows if r["verdict"] == "ERROR"]

    print(f"\n=== Pass 1 summary ===")
    print(f"Total evaluated: {len(rows)}")
    print(f"Agree with stored verdict: {agree}/{len(rows)} ({100*agree/len(rows):.1f}%)")
    print(f"Disagreements: {len(diffs)}")
    print(f"Errors: {len(errors)}")
    print(f"Output: {out_csv.relative_to(BASE)}")

    if not diffs:
        return

    confirmed_change, noisy = [], []
    for r in diffs:
        c = confirm_rows.get(r["text"])
        if not c:
            continue
        if c["verdict"] == r["verdict"]:
            confirmed_change.append((r, c))
        else:
            noisy.append((r, c))

    diff_path = BASE / "data" / "eval_diff_report.csv"
    with open(diff_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "text", "category", "stored_verdict", "run1_verdict", "run2_verdict", "status", "judge_reason",
        ])
        writer.writeheader()
        for r in diffs:
            c = confirm_rows.get(r["text"])
            if not c:
                status = "UNCONFIRMED (confirmation pass did not complete)"
                run2 = ""
            elif c["verdict"] == r["verdict"]:
                status = "CONFIRMED_CHANGE"
                run2 = c["verdict"]
            else:
                status = "NOISY (unstable across re-render, not a reliable regression)"
                run2 = c["verdict"]
            writer.writerow({
                "text": r["text"], "category": r["category"], "stored_verdict": r["stored_verdict"],
                "run1_verdict": r["verdict"], "run2_verdict": run2, "status": status,
                "judge_reason": r["judge_reason"],
            })

    print(f"\n=== Confirmation pass ===")
    print(f"Disagreements re-rendered and re-judged: {len(confirm_rows)}/{len(diffs)}")
    print(f"Confirmed changes (stable across 2 independent renders, disagree with stored): {len(confirmed_change)}")
    print(f"Noisy (unstable across re-render, not a reliable regression): {len(noisy)}")
    print(f"Diff report: {diff_path.relative_to(BASE)}")

    if confirmed_change:
        print(f"\nConfirmed changes:")
        for r, c in confirmed_change:
            print(f"  {r['text']:25s} stored={r['stored_verdict']:6s} -> run1={r['verdict']:6s} run2={c['verdict']:6s}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0, help="Run on N random terms across all categories")
    ap.add_argument("--all", action="store_true", help="Run on the full 966-term corpus")
    ap.add_argument("--workers", type=int, default=6, help="Concurrent worker threads per batch")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    if not TELNYX_KEY:
        sys.exit("ERROR: TELNYX_API_KEY not set")
    if not LITELLM_KEY or not LITELLM_BASE:
        sys.exit("ERROR: LITELLM_KEY / LITELLM_BASE not set")
    if not args.sample and not args.all:
        sys.exit("ERROR: pass --sample N or --all")

    terms = load_terms()

    if args.sample:
        random.seed(args.seed)
        by_cat = {}
        for t in terms:
            by_cat.setdefault(t["category"], []).append(t)
        per_cat = max(1, args.sample // len(by_cat))
        selected = []
        for cat, cat_terms in by_cat.items():
            selected.extend(random.sample(cat_terms, min(per_cat, len(cat_terms))))
        random.shuffle(selected)
        selected = selected[:args.sample]
    else:
        selected = terms

    already = load_checkpoint()
    n_pending = len([t for t in selected if t["text"] not in already])
    print(f"{len(selected)} terms selected, {len(selected) - n_pending} already checkpointed, {n_pending} to run")

    result_map = run_pass(selected, args.workers, CHECKPOINT_FILE, label="batch")
    rows = [result_map[t["text"]] for t in selected if t["text"] in result_map]

    diff_terms = [t for t in selected
                  if t["text"] in result_map
                  and result_map[t["text"]]["verdict"] != result_map[t["text"]]["stored_verdict"]
                  and result_map[t["text"]]["stored_verdict"]
                  and result_map[t["text"]]["verdict"] != "ERROR"]
    confirm_rows = {}
    if diff_terms:
        print(f"\n{len(diff_terms)} disagreements found. Re-rendering each once more to confirm before flagging as a real change.")
        confirm_rows = run_pass(diff_terms, args.workers, CONFIRM_CHECKPOINT_FILE, label="confirm")

    write_outputs(rows, confirm_rows)


if __name__ == "__main__":
    raise SystemExit(main())
