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
- pls/medical-pronunciation-dict-01.pls ... medical-pronunciation-dict-10.pls
- txt/medical-pronunciation-dict-01.txt ... medical-pronunciation-dict-10.txt
- import_to_telnyx.py (helper to create dictionaries via API)
"""
import json
import os
import sys
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

BASE = Path(__file__).parent.parent
INPUT_FILE = BASE / "data" / "terms_with_pronunciations.json"
PLS_DIR = BASE / "pls"
TXT_DIR = BASE / "txt"

MAX_ITEMS_PER_DICT = 100


def load_terms():
    with open(INPUT_FILE) as f:
        return json.load(f)


def chunk_list(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def export_pls_xml(terms, filepath, dict_name):
    """Export terms as W3C PLS XML format."""
    root = Element("lexicon", {
        "version": "1.0",
        "xmlns": "http://www.w3.org/2005/01/pronunciation-lexicon",
        "alphabet": "ipa",
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


def export_import_script(all_chunks, dict_prefix="medical-pron"):
    """Generate a Python script that imports all dictionaries via Telnyx API."""
    lines = [
        '#!/usr/bin/env python3',
        '"""',
        'Import medical pronunciation dictionaries into Telnyx.',
        '',
        'Usage:',
        '  python3 import_to_telnyx.py  # creates all dictionaries',
        '  python3 import_to_telnyx.py --dry-run  # preview without creating',
        '',
        'Requires: TELNYX_API_KEY environment variable',
        '"""',
        'import json',
        'import os',
        'import sys',
        'import urllib.request',
        '',
        'API_BASE = "https://api.telnyx.com/v2"',
        '',
        '',
        'def create_dict(name, items):',
        '    key = os.environ.get("TELNYX_API_KEY", "")',
        '    if not key:',
        '        print("ERROR: TELNYX_API_KEY not set")',
        '        sys.exit(1)',
        '    payload = json.dumps({"name": name, "items": items}).encode()',
        '    req = urllib.request.Request(',
        '        f"{API_BASE}/pronunciation_dicts",',
        '        data=payload,',
        '        headers={',
        '            "Authorization": f"Bearer {key}",',
        '            "Content-Type": "application/json",',
        '        },',
        '    )',
        '    resp = urllib.request.urlopen(req)',
        '    return json.loads(resp.read())',
        '',
        '',
        'def main():',
        '    dry_run = "--dry-run" in sys.argv',
        f'    chunks = {json.dumps(all_chunks)}',
        '    print(f"Total dictionaries to create: {len(chunks)}")',
        '    for i, chunk in enumerate(chunks, 1):',
        '        name = f"Medical Pronunciation Dict {i:02d}"',
        '        items = [{"text": t["text"], "type": "alias", "alias": t["alias"]} for t in chunk if t["alias"] and t["alias"] != t["text"]]',
        f'        print(f"  Dict {{i}}/{{len(chunks)}}: {{name}} ({{len(items)}} items)")',
        '        if not dry_run:',
        '            result = create_dict(name, items)',
        f'            dict_id = result.get("data", {{}}).get("id", "unknown")',
        f'            print(f"    Created: {{dict_id}}")',
        '    if dry_run:',
        '        print("\\nDry run complete. Run without --dry-run to create dictionaries.")',
        '    else:',
        '        print("\\nAll dictionaries created!")',
        '        print("Next: assign dictionary IDs to your assistant in the Voice tab.")',
        '',
        '',
        'if __name__ == "__main__":',
        '    main()',
    ]
    output = "\n".join(lines) + "\n"
    filepath = BASE / "import_to_telnyx.py"
    with open(filepath, "w") as f:
        f.write(output)
    os.chmod(filepath, 0o755)


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
    for i, chunk in enumerate(all_chunks, 1):
        fname = f"medical-pronunciation-dict-{i:02d}.pls"
        export_pls_xml(chunk, PLS_DIR / fname, f"Medical Pronunciation Dict {i:02d}")
    print(f"Exported {len(all_chunks)} PLS XML files to {PLS_DIR}/")

    # Export plain text files
    TXT_DIR.mkdir(exist_ok=True)
    for i, chunk in enumerate(all_chunks, 1):
        fname = f"medical-pronunciation-dict-{i:02d}.txt"
        export_plain_text(chunk, TXT_DIR / fname)
    print(f"Exported {len(all_chunks)} plain text files to {TXT_DIR}/")

    # Export import script
    export_import_script(all_chunks)
    print(f"Exported import script to {BASE}/import_to_telnyx.py")

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
