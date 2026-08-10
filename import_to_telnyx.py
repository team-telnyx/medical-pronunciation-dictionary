#!/usr/bin/env python3
"""
Import medical pronunciation dictionaries into Telnyx.

Reads the generated dictionaries in providers/telnyx/ and creates one Telnyx
pronunciation dictionary per file. Each file holds up to 100 items: an alias
entry and an IPA phoneme entry per term.

Usage:
  python3 import_to_telnyx.py            # create all dictionaries
  python3 import_to_telnyx.py --dry-run  # preview without creating

Requires: TELNYX_API_KEY environment variable
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API_BASE = "https://api.telnyx.com/v2"
DICTS_DIR = Path(__file__).parent / "providers" / "telnyx"


def load_dicts() -> list[dict]:
    """Load every generated Telnyx dictionary payload, in file order."""
    paths = sorted(DICTS_DIR.glob("medical-pronunciations-*.json"))
    if not paths:
        sys.exit(
            f"No dictionaries found in {DICTS_DIR}. "
            "Run `python3 converters/convert_all.py` first."
        )
    payloads = []
    for path in paths:
        with path.open(encoding="utf-8") as f:
            payloads.append(json.load(f))
    return payloads


def create_dict(key: str, name: str, items: list[dict]) -> str:
    payload = json.dumps({"name": name, "items": items}).encode()
    req = urllib.request.Request(
        f"{API_BASE}/pronunciation_dicts",
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as resp:
        body = json.loads(resp.read())
    return body.get("data", {}).get("id", "unknown")


def main() -> int:
    dry_run = "--dry-run" in sys.argv

    key = os.environ.get("TELNYX_API_KEY", "")
    if not key and not dry_run:
        print("ERROR: TELNYX_API_KEY not set", file=sys.stderr)
        return 1

    dicts = load_dicts()
    total_items = sum(len(d["items"]) for d in dicts)
    print(f"Dictionaries to create: {len(dicts)} ({total_items} items total)")

    for i, payload in enumerate(dicts, 1):
        name = payload["name"]
        items = payload["items"]
        print(f"  {i}/{len(dicts)}: {name} ({len(items)} items)")
        if dry_run:
            continue
        try:
            dict_id = create_dict(key, name, items)
        except urllib.error.HTTPError as exc:
            print(f"    FAILED ({exc.code}): {exc.read().decode()}", file=sys.stderr)
            return 1
        print(f"    created: {dict_id}")

    if dry_run:
        print("\nDry run complete. Run without --dry-run to create dictionaries.")
    else:
        print("\nAll dictionaries created.")
        print("Next: assign the dictionary IDs to your assistant in the Voice tab.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
