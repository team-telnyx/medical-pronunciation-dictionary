#!/usr/bin/env python3
"""
Export medical pronunciation dictionary to Telnyx-compatible formats.

Telnyx supports:
- PLS/XML (W3C Pronunciation Lexicon Specification)
- Plain text (word=alias or word:/phoneme/)

Constraints:
- Max 100 items per dictionary
- Max 50 dictionaries per organization
- Max 200 chars per text field
- Max 500 chars per alias/phoneme value

Output:
- pls/medical-pronunciation-dict-NN.pls
- txt/medical-pronunciation-dict-NN.txt
"""
import json
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

BASE = Path(__file__).parent.parent
INPUT_FILE = BASE / "data" / "terms_master.json"
PLS_DIR = BASE / "pls"
TXT_DIR = BASE / "txt"

MAX_ITEMS_PER_DICT = 100


def load_terms():
    with open(INPUT_FILE) as f:
        return json.load(f)


def chunk_list(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def prune(out_dir, pattern, keep):
    """Delete numbered chunk files left over from a previous, larger run."""
    kept = {p.resolve() for p in keep}
    for path in sorted(out_dir.glob(pattern)):
        if path.resolve() not in kept:
            path.unlink()
            print(f"  [prune] removed stale {path.relative_to(BASE)}")


def export_pls_xml(terms, filepath):
    """Export terms as W3C PLS XML format."""
    # These files carry <alias> only, so no alphabet attribute: alphabet
    # declares the phonetic alphabet used by <phoneme>, which is absent here.
    root = Element("lexicon", {
        "version": "1.0",
        "xmlns": "http://www.w3.org/2005/01/pronunciation-lexicon",
        "xml:lang": "en-US",
    })

    for item in terms:
        text = item["text"]
        alias = item["alias"]
        if not alias or alias == text:
            continue
        lexeme = SubElement(root, "lexeme")
        grapheme = SubElement(lexeme, "grapheme")
        grapheme.text = text
        alias_elem = SubElement(lexeme, "alias")
        alias_elem.text = alias

    raw = tostring(root, encoding="unicode")
    pretty = minidom.parseString(raw).toprettyxml(indent="  ", encoding="UTF-8")
    with open(filepath, "wb") as f:
        f.write(pretty)


def export_plain_text(terms, filepath):
    """Export terms as Telnyx plain text format."""
    lines = []
    for item in terms:
        text = item["text"]
        alias = item["alias"]
        if not alias or alias == text:
            continue
        lines.append(f"{text}={alias}")
    with open(filepath, "w") as f:
        f.write("\n".join(lines) + "\n")


def main():
    terms = load_terms()
    print(f"Total terms: {len(terms)}")

    # Group by category for logical dictionary organization
    categories = {}
    for t in terms:
        cat = t["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(t)

    # Build chunks of max 100 items, organized by category
    all_chunks = []
    dict_num = 1
    for cat in ["drug", "clinical", "anatomical", "acronym"]:
        items = categories.get(cat, [])
        for chunk in chunk_list(items, MAX_ITEMS_PER_DICT):
            all_chunks.append(chunk)
            print(f"  Dict {dict_num}: {cat} ({len(chunk)} items)")
            dict_num += 1

    print(f"\nTotal dictionaries needed: {len(all_chunks)}")

    # Export PLS XML files
    PLS_DIR.mkdir(exist_ok=True)
    written = []
    for i, chunk in enumerate(all_chunks, 1):
        fname = f"medical-pronunciation-dict-{i:02d}.pls"
        export_pls_xml(chunk, PLS_DIR / fname)
        written.append(PLS_DIR / fname)
    prune(PLS_DIR, "medical-pronunciation-dict-*.pls", written)
    print(f"Exported {len(all_chunks)} PLS XML files to {PLS_DIR}/")

    # Export plain text files
    TXT_DIR.mkdir(exist_ok=True)
    written = []
    for i, chunk in enumerate(all_chunks, 1):
        fname = f"medical-pronunciation-dict-{i:02d}.txt"
        export_plain_text(chunk, TXT_DIR / fname)
        written.append(TXT_DIR / fname)
    prune(TXT_DIR, "medical-pronunciation-dict-*.txt", written)
    print(f"Exported {len(all_chunks)} plain text files to {TXT_DIR}/")

    # Stats
    total_items = sum(len(c) for c in all_chunks)
    items_with_alias = sum(1 for c in all_chunks for t in c if t["alias"] and t["alias"] != t["text"])
    print(f"\nSummary:")
    print(f"  Total items: {total_items}")
    print(f"  Items with alias: {items_with_alias}")
    print(f"  Dictionaries: {len(all_chunks)}")
    print(f"  PLS files: {PLS_DIR}")
    print(f"  TXT files: {TXT_DIR}")


if __name__ == "__main__":
    main()
