#!/usr/bin/env python3
"""
Multi-provider format converters for the medical pronunciation dictionary.

Reads ../data/terms_with_pronunciations.json and emits provider-specific
formats under ../providers/<provider>/.

Providers:
  - telnyx:      chunked JSON, 100 items per file, with "type": "alias"
  - elevenlabs:  W3C PLS XML, 100 items per file
  - vapi:        single JSON file, no "type" field
  - amazon-polly: W3C PLS XML, 100 items per file
  - generic:     CSV (text, alias, category) + flat JSON (text -> alias)

Run from the project root:
    python3 converters/convert_all.py
"""

from __future__ import annotations

import csv
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent          # .../converters
PROJECT_DIR = SCRIPT_DIR.parent                       # .../medical-pronunciation-dictionary
SOURCE_FILE = PROJECT_DIR / "data" / "terms_with_pronunciations.json"
PROVIDERS_DIR = PROJECT_DIR / "providers"

CHUNK_SIZE = 100
DICT_PREFIX = "Medical Pronunciations"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_terms(path: Path) -> list[dict]:
    """Load and validate the source terms JSON."""
    if not path.exists():
        sys.exit(f"Source file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        sys.exit(f"Expected a JSON array in {path}, got {type(data).__name__}")

    cleaned: list[dict] = []
    seen: set[str] = set()
    skipped = 0
    for entry in data:
        text = (entry.get("text") or "").strip()
        alias = (entry.get("alias") or "").strip()
        category = (entry.get("category") or "").strip()
        if not text or not alias:
            skipped += 1
            continue
        if text in seen:
            skipped += 1
            continue
        seen.add(text)
        cleaned.append({"text": text, "alias": alias, "category": category})

    if skipped:
        print(f"  [load] skipped {skipped} entries (missing fields or duplicates)")
    return cleaned


# ---------------------------------------------------------------------------
# Chunking helper
# ---------------------------------------------------------------------------

def chunked(seq: list, size: int) -> Iterable[list]:
    """Yield successive chunks of `size` from `seq`."""
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def pad(n: int) -> str:
    """Zero-pad an integer to two digits: 1 -> '01', 12 -> '12'."""
    return f"{n:02d}"


# ---------------------------------------------------------------------------
# Telnyx JSON
# ---------------------------------------------------------------------------

def write_telnyx(terms: list[dict], out_dir: Path) -> list[Path]:
    """One JSON file per CHUNK_SIZE items, with 'type': 'alias' on each item."""
    out_dir.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    for idx, batch in enumerate(chunked(terms, CHUNK_SIZE), start=1):
        name = f"{DICT_PREFIX} {pad(idx)}"
        payload = {
            "name": name,
            "items": [
                {"text": item["text"], "type": "alias", "alias": item["alias"]}
                for item in batch
            ],
        }
        path = out_dir / f"medical-pronunciations-{pad(idx)}.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.write("\n")
        files.append(path)
    return files


# ---------------------------------------------------------------------------
# W3C PLS XML (ElevenLabs + Amazon Polly)
# ---------------------------------------------------------------------------

PLS_NAMESPACE = "http://www.w3.org/2005/01/pronunciation-lexicon"
PLS_XSI = "http://www.w3.org/2001/XMLSchema-instance"
PLS_SCHEMA = (
    "http://www.w3.org/2005/01/pronunciation-lexicon "
    "http://www.w3.org/TR/2007/CR-pronunciation-lexicon-20071212/pls.xsd"
)

# Register the default namespace so ElementTree emits xmlns="..." not ns0:...
ET.register_namespace("", PLS_NAMESPACE)


def build_pls_document(batch: list[dict]) -> ET.ElementTree:
    """Build a W3C PLS XML document for a batch of terms."""
    lexicon = ET.Element(
        f"{{{PLS_NAMESPACE}}}lexicon",
        {
            "version": "1.0",
            f"{{{PLS_XSI}}}schemaLocation": PLS_SCHEMA,
            "alphabet": "ipa",
            "{http://www.w3.org/XML/1998/namespace}lang": "en",
        },
    )
    for item in batch:
        lexeme = ET.SubElement(lexicon, f"{{{PLS_NAMESPACE}}}lexeme")
        lexeme.set("id", item["text"])
        grapheme = ET.SubElement(lexeme, f"{{{PLS_NAMESPACE}}}grapheme")
        grapheme.text = item["text"]
        phoneme = ET.SubElement(lexeme, f"{{{PLS_NAMESPACE}}}phoneme")
        phoneme.text = item["alias"]
    return ET.ElementTree(lexicon)


def write_pls(terms: list[dict], out_dir: Path, file_prefix: str) -> list[Path]:
    """Write W3C PLS XML files, one per CHUNK_SIZE items."""
    out_dir.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    for idx, batch in enumerate(chunked(terms, CHUNK_SIZE), start=1):
        tree = build_pls_document(batch)
        path = out_dir / f"{file_prefix}-{pad(idx)}.pls"
        # xml_declaration=True with utf-8 encoding for a proper PLS header.
        tree.write(path, encoding="utf-8", xml_declaration=True)
        files.append(path)
    return files


# ---------------------------------------------------------------------------
# Vapi JSON
# ---------------------------------------------------------------------------

def write_vapi(terms: list[dict], out_dir: Path) -> list[Path]:
    """Single JSON file with all items, no 'type' field."""
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "name": "Medical Pronunciation Dictionary",
        "items": [{"text": item["text"], "alias": item["alias"]} for item in terms],
    }
    path = out_dir / "medical-pronunciations.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return [path]


# ---------------------------------------------------------------------------
# Generic CSV + flat JSON
# ---------------------------------------------------------------------------

def write_generic_csv(terms: list[dict], out_dir: Path) -> list[Path]:
    """Single CSV with columns: text, alias, category."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "medical-pronunciations.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "alias", "category"])
        for item in terms:
            writer.writerow([item["text"], item["alias"], item["category"]])
    return [path]


def write_generic_json(terms: list[dict], out_dir: Path) -> list[Path]:
    """Flat JSON: {text: alias, ...} for simple lookups."""
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {item["text"]: item["alias"] for item in terms}
    path = out_dir / "medical-pronunciations.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return [path]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print(f"Source: {SOURCE_FILE}")
    print(f"Output root: {PROVIDERS_DIR}")
    print()

    terms = load_terms(SOURCE_FILE)
    print(f"Loaded {len(terms)} terms")
    print()

    summary: list[tuple[str, list[Path]]] = []

    print("[1/6] Telnyx JSON (chunked, 100/file) ...")
    summary.append(("telnyx", write_telnyx(terms, PROVIDERS_DIR / "telnyx")))

    print("[2/6] ElevenLabs PLS (chunked, 100/file) ...")
    summary.append((
        "elevenlabs",
        write_pls(terms, PROVIDERS_DIR / "elevenlabs", "medical-pronunciations"),
    ))

    print("[3/6] Vapi JSON (single file) ...")
    summary.append(("vapi", write_vapi(terms, PROVIDERS_DIR / "vapi")))

    print("[4/6] Amazon Polly PLS (chunked, 100/file) ...")
    summary.append((
        "amazon-polly",
        write_pls(terms, PROVIDERS_DIR / "amazon-polly", "medical-pronunciations"),
    ))

    print("[5/6] Generic CSV ...")
    summary.append(("generic-csv", write_generic_csv(terms, PROVIDERS_DIR / "generic")))

    print("[6/6] Generic JSON (flat) ...")
    summary.append(("generic-json", write_generic_json(terms, PROVIDERS_DIR / "generic")))

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    total_files = 0
    for provider, files in summary:
        rel = [str(f.relative_to(PROJECT_DIR)) for f in files]
        print(f"  {provider:<14} {len(files):>3} file(s)")
        for r in rel:
            print(f"    - {r}")
        total_files += len(files)
    print("-" * 60)
    print(f"  Total: {total_files} file(s) across {len(summary)} provider(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
