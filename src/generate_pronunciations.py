#!/usr/bin/env python3
"""
Generate phonetic alias pronunciations for medical terms using LiteLLM.

Sends batches of medical terms to a LiteLLM model (MiniMax-M3 or GLM-5.2)
and asks for plain-text phonetic respellings that work as TTS alias entries.

Output: data/terms_with_pronunciations.json
"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))
from terms import get_all_terms

# Load env
env_files = [os.path.expanduser("~/.codex/.env"), os.path.expanduser("~/.claude/.env")]
for f in env_files:
    if os.path.exists(f):
        with open(f) as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.replace("export ", "").strip()
                    v = v.strip().strip('"').strip("'")
                    os.environ.setdefault(k, v)

LITELLM_KEY = os.environ.get("LITELLM_KEY", "")
LITELLM_URL = "http://litellm-aiswe.query.prod.telnyx.io:4000/v1/chat/completions"
MODEL = "MiniMax-M3-MXFP8-nothink"
BATCH_SIZE = 30
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "terms_with_pronunciations.json"

SYSTEM_PROMPT = """You are a medical pronunciation expert. For each medical term, provide a plain-text phonetic respelling that a text-to-speech engine can read aloud to produce the correct pronunciation.

Rules:
1. Use ONLY standard English letters, hyphens, and spaces in the respelling.
2. Capitalize the stressed syllable (e.g., "oh-MEP-ra-zole" for omeprazole).
3. Keep it simple - the respelling should sound correct when read by a TTS engine.
4. For acronyms, spell out the full term (e.g., "MI" -> "myocardial infarction").
5. For multi-word terms, respell each word.
6. If the term is already pronounced as written, return it as-is.

Return ONLY a JSON array of objects with "text" and "alias" fields. No explanation, no markdown."""

def call_litellm(batch):
    """Send a batch of terms to LiteLLM and get pronunciations back."""
    terms_list = [t["text"] for t in batch]
    user_msg = f"Provide phonetic respellings for these medical terms:\n\n" + "\n".join(f"{i+1}. {t}" for i, t in enumerate(terms_list))

    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg}
        ],
        "temperature": 0.1,
        "max_tokens": 4000
    }).encode()

    req = urllib.request.Request(
        LITELLM_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {LITELLM_KEY}",
            "Content-Type": "application/json"
        }
    )

    for attempt in range(3):
        try:
            resp = urllib.request.urlopen(req, timeout=60)
            result = json.loads(resp.read())
            content = result["choices"][0]["message"]["content"]
            # Strip markdown code fences if present
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
            if content.startswith("json"):
                content = content[4:].strip()
            return json.loads(content)
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}", file=sys.stderr)
            if attempt < 2:
                time.sleep(3)
    return None


def main():
    all_terms = get_all_terms()
    print(f"Total terms to process: {len(all_terms)}")
    print(f"Model: {MODEL}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Estimated batches: {(len(all_terms) + BATCH_SIZE - 1) // BATCH_SIZE}")
    print()

    # Load existing results if any
    results = {}
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE) as f:
            existing = json.load(f)
            for item in existing:
                results[item["text"]] = item
        print(f"Loaded {len(results)} existing pronunciations, skipping those.")

    # Filter out already-processed terms
    todo = [t for t in all_terms if t["text"] not in results]
    print(f"Terms remaining: {len(todo)}")
    print()

    batch_num = 0
    total_batches = (len(todo) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(todo), BATCH_SIZE):
        batch = todo[i:i + BATCH_SIZE]
        batch_num += 1
        print(f"Batch {batch_num}/{total_batches}: terms {i+1}-{min(i+BATCH_SIZE, len(todo))}")

        pronunciations = call_litellm(batch)

        if pronunciations is None:
            print(f"  FAILED - skipping batch")
            # Save what we have with null aliases
            for t in batch:
                if t["text"] not in results:
                    results[t["text"]] = {"text": t["text"], "alias": t["text"], "category": t["category"]}
            continue

        # Match pronunciations back to terms
        if isinstance(pronunciations, list):
            # Handle both dict and string items in the list
            parsed = []
            for item in pronunciations:
                if isinstance(item, dict):
                    text = item.get("text", "")
                    alias = item.get("alias", text)
                    parsed.append((text, alias))
                elif isinstance(item, str):
                    # LLM returned just the alias, match by position
                    idx = len(parsed)
                    if idx < len(batch):
                        parsed.append((batch[idx]["text"], item))

            # If we didn't get positional matches, try matching by index to batch
            if len(parsed) < len(batch):
                for idx, t in enumerate(batch):
                    if idx < len(parsed):
                        continue
                    if idx < len(pronunciations) and isinstance(pronunciations[idx], str):
                        parsed.append((t["text"], pronunciations[idx]))

            for text, alias in parsed:
                cat = "unknown"
                for t in batch:
                    if t["text"].lower() == text.lower():
                        cat = t["category"]
                        break
                results[text] = {"text": text, "alias": alias, "category": cat}
        else:
            print(f"  Unexpected response format: {type(pronunciations)}")

        # Save after each batch
        with open(OUTPUT_FILE, "w") as f:
            json.dump(list(results.values()), f, indent=2)
        print(f"  Saved {len(results)} pronunciations")

        # Small delay between batches
        if batch_num < total_batches:
            time.sleep(0.5)

    print(f"\nDone! Total pronunciations: {len(results)}")
    print(f"Output: {OUTPUT_FILE}")

    # Print sample
    print("\nSample entries:")
    for t in list(results.values())[:10]:
        print(f"  {t['text']}: {t['alias']} ({t['category']})")


if __name__ == "__main__":
    main()
