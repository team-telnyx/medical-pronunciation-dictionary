#!/usr/bin/env python3
"""
Generate before/after audio samples using Telnyx TTS REST API.

Creates pairs of audio files for 10 representative medical terms:
- Before: TTS without pronunciation dictionary (raw text)
- After: TTS with alias substitution applied manually (simulates dictionary)

Output: data/audio/before/ and data/audio/after/
"""
import json
import os
import sys
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

# 10 representative terms across categories
SAMPLE_TERMS = [
    "atorvastatin",
    "omeprazole",
    "amoxicillin",
    "metformin",
    "myocardial infarction",
    "cholecystectomy",
    "cholecystitis",
    "MI",
    "COPD",
    "epithelium",
]


def generate_speech(text, output_path):
    """Call Telnyx TTS REST API and save audio."""
    payload = json.dumps({
        "text": text,
        "voice": VOICE,
        "output_format": "mp3",
    }).encode()

    req = urllib.request.Request(
        f"{API_BASE}/text-to-speech/speech",
        data=payload,
        headers={
            "Authorization": f"Bearer {TELNYX_KEY}",
            "Content-Type": "application/json",
        }
    )

    try:
        resp = urllib.request.urlopen(req, timeout=30)
        audio_data = resp.read()
        with open(output_path, "wb") as f:
            f.write(audio_data)
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False


def main():
    if not TELNYX_KEY:
        print("ERROR: TELNYX_API_KEY not set")
        sys.exit(1)

    # Load pronunciations
    with open(INPUT_FILE) as f:
        all_prons = json.load(f)
    pron_map = {p["text"]: p["alias"] for p in all_prons}

    BEFORE_DIR.mkdir(parents=True, exist_ok=True)
    AFTER_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Generating {len(SAMPLE_TERMS)} before/after audio samples...")
    print(f"Voice: {VOICE}")
    print()

    results = []
    for term in SAMPLE_TERMS:
        alias = pron_map.get(term, term)
        safe_name = term.replace(" ", "_").replace("/", "_")

        before_path = BEFORE_DIR / f"{safe_name}_before.mp3"
        after_path = AFTER_DIR / f"{safe_name}_after.mp3"

        print(f"  {term} -> {alias}")

        # Before: raw term
        if generate_speech(f"Please take your {term} as prescribed.", before_path):
            print(f"    before: {before_path.name} OK")
        else:
            print(f"    before: FAILED")

        # After: term replaced with alias in the sentence
        if generate_speech(f"Please take your {alias} as prescribed.", after_path):
            print(f"    after:  {after_path.name} OK")
        else:
            print(f"    after:  FAILED")

        results.append({
            "term": term,
            "alias": alias,
            "before": str(before_path.relative_to(BASE)),
            "after": str(after_path.relative_to(BASE)),
        })

    # Save manifest
    manifest_path = AUDIO_DIR / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nManifest: {manifest_path}")
    print(f"Audio files: {BEFORE_DIR} and {AFTER_DIR}")


if __name__ == "__main__":
    main()
