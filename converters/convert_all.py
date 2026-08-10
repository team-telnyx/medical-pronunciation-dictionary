#!/usr/bin/env python3
"""
Multi-provider format converters for the medical pronunciation dictionary.

Reads ../data/terms_master.json and emits provider-specific formats
under ../providers/<provider>/.

Each term produces BOTH an alias entry and an IPA phoneme entry where
the provider supports both. Providers that only support phoneme (Polly,
Retell) emit phoneme-only entries.

Providers:
  - telnyx:       chunked JSON, 100 entries per file (50 terms x 2 entries)
  - elevenlabs:   W3C PLS XML, 100 lexemes per file, alias + phoneme
  - vapi:         single JSON file, alias + <<ipa>> entries
  - amazon-polly: W3C PLS XML, 100 lexemes per file, phoneme only
  - retell:       single JSON file, IPA phoneme entries only
  - generic:      CSV (text, alias, ipa, category) + flat JSON

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
SOURCE_FILE = PROJECT_DIR / "data" / "terms_master.json"
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
        ipa = (entry.get("ipa") or "").strip()
        category = (entry.get("category") or "").strip()
        if not text or not alias or not ipa:
            skipped += 1
            continue
        if text in seen:
            skipped += 1
            continue
        seen.add(text)
        cleaned.append({"text": text, "alias": alias, "ipa": ipa, "category": category})

    if skipped:
        print(f"  [load] skipped {skipped} entries (missing fields or duplicates)")
    return cleaned


# ---------------------------------------------------------------------------
# Chunking helpers
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
    """One JSON file per CHUNK_SIZE entries. One phoneme entry per term
    (Telnyx API rejects duplicate text entries, and phoneme is more
    precise than alias for providers that support IPA)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    for idx, batch in enumerate(chunked(terms, CHUNK_SIZE), start=1):
        name = f"{DICT_PREFIX} {pad(idx)}"
        items = [
            {
                "text": item["text"],
                "type": "phoneme",
                "phoneme": item["ipa"],
                "alphabet": "ipa",
            }
            for item in batch
        ]
        payload = {"name": name, "items": items}
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


def build_pls_document(
    batch: list[dict],
    include_alias: bool,
    xml_lang: str = "en-US",
) -> ET.ElementTree:
    """Build a W3C PLS XML document for a batch of terms.

    When include_alias is True, each lexeme gets both <alias> and <phoneme>.
    When False, each lexeme gets only <phoneme> (for providers like Polly
    that don't support alias).

    xml_lang defaults to en-US (required by Amazon Polly, fine for others).
    No id attribute on lexemes (spaces in multi-word terms break xsd:ID).
    """
    lexicon = ET.Element(
        f"{{{PLS_NAMESPACE}}}lexicon",
        {
            "version": "1.0",
            f"{{{PLS_XSI}}}schemaLocation": PLS_SCHEMA,
            "alphabet": "ipa",
            "{http://www.w3.org/XML/1998/namespace}lang": xml_lang,
        },
    )
    for item in batch:
        lexeme = ET.SubElement(lexicon, f"{{{PLS_NAMESPACE}}}lexeme")
        grapheme = ET.SubElement(lexeme, f"{{{PLS_NAMESPACE}}}grapheme")
        grapheme.text = item["text"]
        if include_alias:
            alias_el = ET.SubElement(lexeme, f"{{{PLS_NAMESPACE}}}alias")
            alias_el.text = item["alias"]
        phoneme = ET.SubElement(lexeme, f"{{{PLS_NAMESPACE}}}phoneme")
        phoneme.text = item["ipa"]
    return ET.ElementTree(lexicon)


def write_pls(
    terms: list[dict],
    out_dir: Path,
    file_prefix: str,
    include_alias: bool,
) -> list[Path]:
    """Write W3C PLS XML files, one per CHUNK_SIZE lexemes."""
    out_dir.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    for idx, batch in enumerate(chunked(terms, CHUNK_SIZE), start=1):
        tree = build_pls_document(batch, include_alias=include_alias)
        path = out_dir / f"{file_prefix}-{pad(idx)}.pls"
        # xml_declaration=True with utf-8 encoding for a proper PLS header.
        tree.write(path, encoding="utf-8", xml_declaration=True)
        files.append(path)
    return files


# ---------------------------------------------------------------------------
# Vapi JSON
# ---------------------------------------------------------------------------

def write_vapi(terms: list[dict], out_dir: Path) -> list[Path]:
    """Single JSON file. One entry per term using IPA in Vapi's
    <<ipa>> phoneme syntax (more precise than alias)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    items = [
        {"text": item["text"], "alias": f"<<{item['ipa']}>>"}
        for item in terms
    ]
    payload = {"name": "Medical Pronunciation Dictionary", "items": items}
    path = out_dir / "medical-pronunciations.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return [path]


# ---------------------------------------------------------------------------
# Retell JSON
# ---------------------------------------------------------------------------

def write_retell(terms: list[dict], out_dir: Path) -> list[Path]:
    """Single JSON file with IPA phoneme entries only.
    Retell uses 'word' (not 'text') and requires 'alphabet' + 'phoneme'.
    Multi-word terms are filtered out (Retell is word-level)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    filtered = []
    skipped = 0
    for item in terms:
        if " " in item["text"]:
            skipped += 1
            continue
        filtered.append(
            {"word": item["text"], "alphabet": "ipa", "phoneme": item["ipa"]}
        )
    if skipped:
        print(f"  [retell] skipped {skipped} multi-word entries (word-level only)")
    payload = {"name": "Medical Pronunciation Dictionary", "items": filtered}
    path = out_dir / "medical-pronunciations.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return [path]


# ---------------------------------------------------------------------------
# STT keyterms (Deepgram keyterm boosting)
# ---------------------------------------------------------------------------

def write_keyterms(terms: list[dict], out_dir: Path) -> list[Path]:
    """Single comma-separated keyterms file for STT keyterm boosting
    (e.g., Deepgram transcription.settings.keyterm)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    keyterms = [item["text"] for item in terms]
    path = out_dir / "keyterms.txt"
    with path.open("w", encoding="utf-8") as f:
        f.write(",".join(keyterms) + "\n")
    return [path]


# ---------------------------------------------------------------------------
# Generic CSV + flat JSON
# ---------------------------------------------------------------------------

def write_generic_csv(terms: list[dict], out_dir: Path) -> list[Path]:
    """Single CSV with columns: text, alias, ipa, category."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "medical-pronunciations.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "alias", "ipa", "category"])
        for item in terms:
            writer.writerow([item["text"], item["alias"], item["ipa"], item["category"]])
    return [path]


def write_generic_json(terms: list[dict], out_dir: Path) -> list[Path]:
    """Flat JSON: {text: {alias, ipa}, ...} for simple lookups."""
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        item["text"]: {"alias": item["alias"], "ipa": item["ipa"]}
        for item in terms
    }
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

    print("[1/8] Telnyx JSON (chunked, 100 phoneme entries/file) ...")
    summary.append(("telnyx", write_telnyx(terms, PROVIDERS_DIR / "telnyx")))

    print("[2/8] ElevenLabs PLS (chunked, 100 lexemes/file, alias + phoneme) ...")
    summary.append((
        "elevenlabs",
        write_pls(
            terms,
            PROVIDERS_DIR / "elevenlabs",
            "medical-pronunciations",
            include_alias=True,
        ),
    ))

    print("[3/8] Vapi JSON (single file, <<ipa>> phoneme entries) ...")
    summary.append(("vapi", write_vapi(terms, PROVIDERS_DIR / "vapi")))

    print("[4/8] Amazon Polly PLS (chunked, 100 lexemes/file, phoneme only) ...")
    summary.append((
        "amazon-polly",
        write_pls(
            terms,
            PROVIDERS_DIR / "amazon-polly",
            "medical-pronunciations",
            include_alias=False,
        ),
    ))

    print("[5/8] Retell JSON (single file, IPA phoneme only, word-level) ...")
    summary.append(("retell", write_retell(terms, PROVIDERS_DIR / "retell")))

    print("[6/8] STT keyterms (comma-separated for Deepgram keyterm boosting) ...")
    summary.append(("keyterms", write_keyterms(terms, PROVIDERS_DIR / "stt")))

    print("[7/8] Generic CSV ...")
    summary.append(("generic-csv", write_generic_csv(terms, PROVIDERS_DIR / "generic")))

    print("[8/8] Generic JSON (flat) ...")
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
