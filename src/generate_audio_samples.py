#!/usr/bin/env python3
"""
Generate before/after audio samples using the Telnyx TTS REST API.

Both clips use the SAME sentence text. The only difference is whether a real
Telnyx pronunciation dictionary is attached to the request:

- before: TTS with no dictionary
- after:  TTS with `pronunciation_dict_id` set to a dictionary built from
          data/terms_master.json

An earlier version faked the "after" clip by substituting the alias into the
sentence text ("Please take your a-TOR-va-STAT-in as prescribed"). That is not
what a dictionary does. It produced identical clips for terms the engine
already says correctly, and worse-sounding clips for terms whose alias the
engine read syllable by syllable.

Note: the request field is `pronunciation_dict_id`, singular, a string. The
plural forms are accepted with HTTP 200 and silently ignored.

Usage:
  export TELNYX_API_KEY=...
  python3 src/generate_audio_samples.py            # create dict, render, clean up
  python3 src/generate_audio_samples.py --keep     # leave the dictionary in place

Output: data/audio/before/, data/audio/after/, data/audio/manifest.json
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

TELNYX_KEY = os.environ.get("TELNYX_API_KEY", "")
API_BASE = "https://api.telnyx.com/v2"

BASE = Path(__file__).parent.parent
AUDIO_DIR = BASE / "data" / "audio"
BEFORE_DIR = AUDIO_DIR / "before"
AFTER_DIR = AUDIO_DIR / "after"
INPUT_FILE = BASE / "data" / "terms_master.json"

# Use a Telnyx NaturalHD voice (no BYOK needed)
VOICE = "Telnyx.NaturalHD.astra"
DICT_NAME = "medical-pronunciation-audio-samples"

# Terms where attaching the dictionary makes an audible difference. Terms the
# engine already pronounces correctly are deliberately excluded: a before/after
# pair that sounds identical demonstrates nothing.
SAMPLE_TERMS = [
    "MI",
    "CHF",
    "COPD",
    "DVT",
    "ceftriaxone",
    "furosemide",
]

# The carrier sentence has to make sense for the category, and must be
# identical across the before and after clip.
CARRIERS = {
    "drug": "Please take your {t} as prescribed.",
    "clinical": "The patient was diagnosed with {t}.",
    "anatomical": "The biopsy shows inflammation in the {t}.",
    "acronym": "The patient has a history of {t}.",
}


def api(path, payload=None, method=None):
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        data=json.dumps(payload).encode() if payload is not None else None,
        method=method,
        headers={
            "Authorization": f"Bearer {TELNYX_KEY}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read()
    return json.loads(body) if body else {}


def create_dictionary(terms):
    """Build a real pronunciation dictionary from the sample terms.

    Alias entries, not phoneme: Telnyx TTS does not interpret IPA phonemes,
    it reads the characters. One entry per term, since the API rejects
    duplicate `text` values inside a dictionary.
    """
    items = [
        {"text": t["text"], "type": "alias", "alias": t["alias"]}
        for t in terms
        if t["alias"] and t["alias"] != t["text"]
    ]
    data = api("/pronunciation_dicts", {"name": DICT_NAME, "items": items})["data"]
    return data["id"], len(items)


def generate_speech(text, output_path, dict_id=None):
    """Call Telnyx TTS and save the audio. Attaches a dictionary when given."""
    payload = {"text": text, "voice": VOICE, "output_format": "mp3"}
    if dict_id:
        payload["pronunciation_dict_id"] = dict_id
    req = urllib.request.Request(
        f"{API_BASE}/text-to-speech/speech",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {TELNYX_KEY}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            output_path.write_bytes(resp.read())
        return True
    except urllib.error.HTTPError as exc:
        print(f"  Error {exc.code}: {exc.read().decode()[:200]}")
        return False


def main():
    if not TELNYX_KEY:
        print("ERROR: TELNYX_API_KEY not set", file=sys.stderr)
        return 1

    with open(INPUT_FILE, encoding="utf-8") as f:
        by_text = {t["text"]: t for t in json.load(f)}

    missing = [t for t in SAMPLE_TERMS if t not in by_text]
    if missing:
        print(f"ERROR: not in {INPUT_FILE.name}: {missing}", file=sys.stderr)
        return 1

    selected = [by_text[t] for t in SAMPLE_TERMS]
    dict_id, count = create_dictionary(selected)
    print(f"Created dictionary {dict_id} with {count} alias entries")

    BEFORE_DIR.mkdir(parents=True, exist_ok=True)
    AFTER_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Voice: {VOICE}\n")

    results = []
    try:
        for term in selected:
            text = term["text"]
            sentence = CARRIERS[term["category"]].format(t=text)
            safe = text.replace(" ", "_").replace("/", "_")
            before = BEFORE_DIR / f"{safe}_before.mp3"
            after = AFTER_DIR / f"{safe}_after.mp3"

            print(f"  {text}: {sentence}")
            ok_b = generate_speech(sentence, before)
            ok_a = generate_speech(sentence, after, dict_id=dict_id)
            print(f"    before (no dict):   {'OK' if ok_b else 'FAILED'}")
            print(f"    after  (with dict): {'OK' if ok_a else 'FAILED'}")

            results.append({
                "term": text,
                "alias": term["alias"],
                "sentence": sentence,
                "before": str(before.relative_to(BASE)),
                "after": str(after.relative_to(BASE)),
            })
    finally:
        if "--keep" in sys.argv:
            print(f"\nDictionary kept: {dict_id}")
        else:
            api(f"/pronunciation_dicts/{dict_id}", method="DELETE")
            print(f"\nDeleted dictionary {dict_id}")

    manifest_path = AUDIO_DIR / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Manifest: {manifest_path.relative_to(BASE)}")
    print(f"Audio: {BEFORE_DIR.relative_to(BASE)} and {AFTER_DIR.relative_to(BASE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
