#!/usr/bin/env python3
"""
Fix IPA data quality issues in data/terms_master.json.

Steps:
1. Re-derive IPA for all 149 acronym entries from their alias text via LiteLLM
2. Normalize IPA transcription system (ɹ->r, g->ɡ, ʤ->dʒ, ensure stress)
3. Fix specific alias/IPA contradictions
4. Remove no-op entries
5. Add missing terms

Reads LITELLM_KEY from ~/.codex/.env.
"""
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
OUTPUT_FILE = REPO_ROOT / "data" / "terms_master.json"

API_URL = "http://litellm-aiswe.query.prod.telnyx.io:4000/v1/chat/completions"
MODEL = "MiniMax-M3-MXFP8-nothink"
BATCH_SIZE = 30

# Load LITELLM_KEY from ~/.codex/.env
ENV_FILE = Path.home() / ".codex" / ".env"
if ENV_FILE.exists():
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line.startswith("LITELLM_KEY="):
                os.environ["LITELLM_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")
                break

API_KEY = os.environ.get("LITELLM_KEY", "")
if not API_KEY:
    print("ERROR: LITELLM_KEY not found in ~/.codex/.env", file=sys.stderr)
    sys.exit(1)


def call_litellm(system_prompt, user_msg, max_tokens=4000):
    """Send a request to LiteLLM and return the content string."""
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ],
        "temperature": 0.1,
        "max_tokens": max_tokens
    }).encode()

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
    )

    for attempt in range(3):
        try:
            resp = urllib.request.urlopen(req, timeout=60)
            result = json.loads(resp.read())
            content = result["choices"][0]["message"]["content"]
            return content.strip()
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}", file=sys.stderr)
            if attempt < 2:
                time.sleep(3)
    return None


def parse_json_response(content):
    """Strip markdown fences and parse JSON."""
    if content is None:
        return None
    content = content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        if len(lines) > 1:
            content = "\n".join(lines[1:])
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
    if content.startswith("json"):
        content = content[4:].strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return None


# =============================================================================
# STEP 1: Re-derive IPA for acronyms from their alias text
# =============================================================================

IPA_SYSTEM_PROMPT = """You are a medical pronunciation expert. For each phrase, provide its IPA pronunciation using standard IPA notation. Use American English (rhotic). Include primary stress ˈ before the stressed syllable. Return ONLY a JSON array of objects with 'text' and 'ipa' fields. No slashes around IPA, no markdown."""


def rederive_acronym_ipa(acronyms):
    """Send acronyms to LiteLLM to get IPA from their alias text."""
    print(f"\n=== STEP 1: Re-derive IPA for {len(acronyms)} acronyms ===")
    results = {}
    total_batches = (len(acronyms) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(acronyms), BATCH_SIZE):
        batch = acronyms[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"  Batch {batch_num}/{total_batches}: {len(batch)} terms")

        terms_list = [(a["text"], a["alias"]) for a in batch]
        user_msg = "Provide IPA pronunciations for these medical phrases:\n\n" + "\n".join(
            f"{idx+1}. {alias}" for idx, (_, alias) in enumerate(terms_list)
        )

        content = call_litellm(IPA_SYSTEM_PROMPT, user_msg)
        parsed = parse_json_response(content)

        if parsed is None or not isinstance(parsed, list):
            print(f"    FAILED to parse response")
            continue

        # Match by alias text (since we sent aliases, not acronyms)
        alias_to_text = {a["alias"].lower().strip(): a["text"] for a in batch}
        for item in parsed:
            if not isinstance(item, dict):
                continue
            text = item.get("text", "").lower().strip()
            ipa = item.get("ipa", "").strip()
            if text in alias_to_text and ipa:
                results[alias_to_text[text]] = ipa

        # Fallback: positional matching
        if len(results) < i:
            for idx, (acronym_text, alias) in enumerate(terms_list):
                if acronym_text not in results and idx < len(parsed):
                    item = parsed[idx]
                    if isinstance(item, dict) and item.get("ipa"):
                        results[acronym_text] = item["ipa"].strip()

        print(f"    Got {len([k for k in results if k in [a['text'] for a in batch]])}/{len(batch)} IPAs")
        time.sleep(0.3)

    return results


# =============================================================================
# STEP 2: Normalize IPA transcription system
# =============================================================================

def normalize_ipa(data):
    """Normalize IPA across all entries."""
    print(f"\n=== STEP 2: Normalize IPA transcription ===")
    normalized_count = 0
    no_stress_entries = []

    for entry in data:
        ipa = entry.get("ipa", "")
        if not ipa:
            continue

        original = ipa

        # 1. Replace ɹ with r (American English rhotic)
        ipa = ipa.replace("ɹ", "r")

        # 2. Replace ASCII g with IPA ɡ (U+0261) - only in IPA field
        ipa = ipa.replace("g", "ɡ")

        # 3. Replace ʤ ligature with dʒ
        ipa = ipa.replace("ʤ", "dʒ")

        # 4. Ensure at least one primary stress mark ˈ
        if "ˈ" not in ipa and "ˌ" not in ipa:
            no_stress_entries.append(entry["text"])
            # Try to add stress before the first vowel cluster
            # Simple heuristic: add ˈ before the first vowel
            match = re.search(r"[aeiouæɛɪɔʊʌə]", ipa)
            if match:
                ipa = ipa[:match.start()] + "ˈ" + ipa[match.start():]

        if ipa != original:
            entry["ipa"] = ipa
            normalized_count += 1

    # Special case: INR is non-rhotic British -> make it rhotic American
    for entry in data:
        if entry["text"] == "INR":
            # "nɔːrməlaɪzd" -> "nɔrməlaɪzd" (remove the length mark before r)
            entry["ipa"] = entry["ipa"].replace("nɔːrm", "nɔrm")
            print(f"  Fixed INR to rhotic American: {entry['ipa']}")

    print(f"  Normalized {normalized_count} entries")
    if no_stress_entries:
        print(f"  Entries without stress mark (auto-added): {no_stress_entries}")
    return normalized_count, no_stress_entries


# =============================================================================
# STEP 3: Fix alias/IPA contradictions
# =============================================================================

CONTRADICTION_FIXES = {
    "vancomycin": "væŋkoʊˈmaɪsɪn",
    "lisinopril": "laɪˈsɪnoʊprɪl",
    "furosemide": "fʊˈroʊsəmaɪd",
    "dyspnea": "ˈdɪspniə",
}


def fix_contradictions(data):
    """Fix specific alias/IPA contradictions."""
    print(f"\n=== STEP 3: Fix alias/IPA contradictions ===")
    fixed = []
    for entry in data:
        if entry["text"] in CONTRADICTION_FIXES:
            old_ipa = entry["ipa"]
            entry["ipa"] = CONTRADICTION_FIXES[entry["text"]]
            fixed.append((entry["text"], old_ipa, entry["ipa"]))
            print(f"  {entry['text']}: {old_ipa} -> {entry['ipa']}")
    return fixed


# =============================================================================
# STEP 4: Remove no-op entries
# =============================================================================

NO_OP_ENTRIES = ["valve", "cusp"]  # alias makes it worse
CONDITIONAL_NO_OPS = ["plaque", "scale", "crust", "lobe", "space of Disse"]


def remove_no_ops(data):
    """Remove entries where alias is same as text or makes it worse."""
    print(f"\n=== STEP 4: Remove no-op entries ===")
    removed = []
    filtered = []
    for entry in data:
        text = entry["text"]
        alias = entry.get("alias", "")
        if text in NO_OP_ENTRIES:
            removed.append(text)
            print(f"  Removed: {text} (alias: {alias})")
            continue
        if text in CONDITIONAL_NO_OPS and alias.lower().strip() == text.lower().strip():
            removed.append(text)
            print(f"  Removed: {text} (alias same as text)")
            continue
        filtered.append(entry)
    print(f"  Removed {len(removed)} entries")
    return filtered, removed


# =============================================================================
# STEP 5: Add missing terms
# =============================================================================

MISSING_TERMS = [
    {"text": "angina", "category": "clinical"},
    {"text": "epinephrine", "category": "drug"},
    {"text": "naloxone", "category": "drug"},
    {"text": "hyperlipidemia", "category": "clinical"},
    {"text": "osteoarthritis", "category": "clinical"},
    {"text": "diabetes mellitus", "category": "clinical"},
]


def add_missing_terms(data):
    """Generate alias and IPA for missing terms."""
    print(f"\n=== STEP 5: Add missing terms ===")
    existing_texts = {e["text"].lower() for e in data}
    to_add = [t for t in MISSING_TERMS if t["text"].lower() not in existing_texts]

    if not to_add:
        print("  All terms already present")
        return []

    # Generate alias and IPA in one call
    ALIAS_SYSTEM = """You are a medical pronunciation expert. For each medical term, provide a plain-text phonetic respelling that a text-to-speech engine can read aloud. Use ONLY standard English letters, hyphens, and spaces. Capitalize the stressed syllable. Return ONLY a JSON array of objects with 'text' and 'alias' fields. No markdown."""

    IPA_SYSTEM = """You are a medical pronunciation expert. For each phrase, provide its IPA pronunciation using standard IPA notation. Use American English (rhotic). Include primary stress ˈ before the stressed syllable. Return ONLY a JSON array of objects with 'text' and 'ipa' fields. No slashes around IPA, no markdown."""

    terms_list = [t["text"] for t in to_add]
    alias_msg = "Provide phonetic respellings for these medical terms:\n\n" + "\n".join(
        f"{i+1}. {t}" for i, t in enumerate(terms_list)
    )
    ipa_msg = "Provide IPA pronunciations for these medical terms:\n\n" + "\n".join(
        f"{i+1}. {t}" for i, t in enumerate(terms_list)
    )

    alias_content = call_litellm(ALIAS_SYSTEM, alias_msg)
    ipa_content = call_litellm(IPA_SYSTEM, ipa_msg)

    alias_parsed = parse_json_response(alias_content) or []
    ipa_parsed = parse_json_response(ipa_content) or []

    aliases = {}
    for item in alias_parsed:
        if isinstance(item, dict):
            aliases[item.get("text", "").lower().strip()] = item.get("alias", "").strip()

    ipas = {}
    for item in ipa_parsed:
        if isinstance(item, dict):
            ipas[item.get("text", "").lower().strip()] = item.get("ipa", "").strip()

    added = []
    for term in to_add:
        text = term["text"]
        alias = aliases.get(text.lower(), text)
        ipa = ipas.get(text.lower(), "")
        new_entry = {
            "text": text,
            "alias": alias,
            "ipa": ipa,
            "category": term["category"]
        }
        data.append(new_entry)
        added.append(new_entry)
        print(f"  Added: {text} -> alias={alias}, ipa={ipa}")

    return added


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("Loading data/terms_master.json...")
    with open(OUTPUT_FILE, encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded {len(data)} entries")

    issues = []

    # STEP 1: Re-derive acronym IPA
    acronyms = [e for e in data if e.get("category") == "acronym"]
    acronym_ipas = rederive_acronym_ipa(acronyms)
    acronyms_fixed = 0
    for entry in data:
        if entry["text"] in acronym_ipas:
            old_ipa = entry["ipa"]
            entry["ipa"] = acronym_ipas[entry["text"]]
            if old_ipa != entry["ipa"]:
                acronyms_fixed += 1
    print(f"  Updated {acronyms_fixed} acronym IPAs")

    # STEP 2: Normalize IPA
    normalized_count, no_stress = normalize_ipa(data)
    if no_stress:
        issues.append(f"Entries without stress mark (auto-added): {no_stress}")

    # STEP 3: Fix contradictions
    contradictions_fixed = fix_contradictions(data)

    # STEP 4: Remove no-ops
    data, removed = remove_no_ops(data)

    # STEP 5: Add missing terms
    added = add_missing_terms(data)

    # Save
    print(f"\n=== Saving {len(data)} entries to {OUTPUT_FILE} ===")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Report
    result = {
        "status": "done",
        "total_terms": len(data),
        "acronyms_fixed": acronyms_fixed,
        "ipa_normalized": normalized_count,
        "no_ops_removed": len(removed),
        "terms_added": len(added),
        "issues": issues,
    }
    print(f"\n{json.dumps(result, indent=2)}")
    return result


if __name__ == "__main__":
    main()
