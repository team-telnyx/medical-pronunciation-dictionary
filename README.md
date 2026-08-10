# Medical Pronunciation Dictionary

Prepackaged medical pronunciation dictionary for voice AI TTS engines. 966 drugs, clinical terms, anatomical terms, and medical acronyms with both phonetic alias and IPA pronunciations. Imports into Telnyx, ElevenLabs, Vapi, Retell, and Amazon Polly.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Terms](https://img.shields.io/badge/terms-966-brightgreen)]()
[![Providers](https://img.shields.io/badge/providers-5-blue)]()
[![Formats](https://img.shields.io/badge/formats-alias%20%2B%20IPA-orange)]()
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue)]()
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](CONTRIBUTING.md)

## Quick start

### Telnyx API (30 seconds)

```bash
git clone https://github.com/team-telnyx/medical-pronunciation-dictionary.git
cd medical-pronunciation-dictionary
export TELNYX_API_KEY=your_key_here
python3 import_to_telnyx.py --dry-run   # preview
python3 import_to_telnyx.py             # create
```

Reads `providers/telnyx/` and creates 10 pronunciation dictionaries in your Telnyx account, 966 IPA phoneme entries total. Telnyx caps dictionaries at 100 items and rejects duplicate text entries, so the pack uses one phoneme entry per term.

### Telnyx Portal

1. Log in to [portal.telnyx.com](https://portal.telnyx.com)
2. Go to **AI Suite -> Pronunciation Dictionaries**
3. Click **Create Dictionary**
4. Upload each of the 11 PLS XML files from `pls/` or plain text files from `txt/`

### ElevenLabs

```python
import os, requests

with open("providers/elevenlabs/medical-pronunciations-01.pls", "rb") as f:
    response = requests.post(
        "https://api.elevenlabs.io/v1/pronunciation-dictionaries/add-from-file",
        headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]},
        files={"file": ("medical.pls", f, "application/xml")},
        data={"name": "medical-pronunciations-01"},
    )
```

Repeat for files 02 through 10.

### Vapi

```python
import os, json, requests

with open("providers/vapi/medical-pronunciations.json") as f:
    payload = json.load(f)

response = requests.post(
    "https://api.vapi.ai/pronunciation-dictionary",
    headers={"Authorization": f"Bearer {os.environ['VAPI_API_KEY']}"},
    json=payload,
)
```

### Amazon Polly

```bash
aws polly put-lexicon \
  --name medical-pronunciations-01 \
  --content file://providers/amazon-polly/medical-pronunciations-01.pls
```

Repeat for files 02 through 10.

## Why both alias and IPA

**Alias** (plain-text phonetic respelling like `a-TOR-va-STAT-in`) works across every TTS provider. **IPA** (like `əˌtɔr.vəˈstæ.tɪn`) is more precise but only supported by some providers.

`data/terms_master.json` carries both for every term. The converter then emits whichever the provider actually supports: phoneme entries for Telnyx, Vapi, Polly, and Retell, alias plus phoneme for ElevenLabs, alias only for the legacy `pls/` and `txt/` exports, and both columns for `providers/generic/`.

Telnyx, Vapi, and Retell reject duplicate entries for the same word, so those get one rule per term rather than a competing alias and phoneme pair.

## Provider support

| Provider | Format | Alias | IPA | Files |
|----------|--------|-------|-----|-------|
| Telnyx | JSON items | No | Yes | `providers/telnyx/` (10 JSON, 100 phoneme entries each) |
| Telnyx | PLS XML | Yes | Yes | `pls/` (11 PLS, alias-only legacy format) |
| ElevenLabs | PLS XML | Yes | Yes | `providers/elevenlabs/` (10 PLS, alias + phoneme per lexeme) |
| Vapi | JSON | No | Yes | `providers/vapi/` (1 JSON, 966 `<<ipa>>` entries) |
| Amazon Polly | PLS XML | No | Yes | `providers/amazon-polly/` (10 PLS, phoneme only, en-US) |
| Retell | JSON | No | Yes | `providers/retell/` (1 JSON, 911 word-level entries) |
| STT | Keyterms | N/A | N/A | `providers/stt/keyterms.txt` (comma-separated, 966 terms) |
| Generic | CSV + JSON | Yes | Yes | `providers/generic/` |

## Coverage

| Category | Count | Examples |
|----------|-------|---------|
| Drugs | 398 | atorvastatin, omeprazole, metformin, sertraline |
| Clinical terms | 267 | myocardial infarction, cholecystectomy, atrial fibrillation |
| Anatomical terms | 152 | epithelium, myocardium, synovium, choroid plexus |
| Medical acronyms | 149 | MI, COPD, CHF, UTI, HbA1c, SpO2 |
| **Total** | **966** | |

## File structure

```
medical-pronunciation-dictionary/
├── data/
│   ├── terms_master.json                # Source of truth: 966 terms with alias + IPA
│   └── audio/
│       ├── before/                      # 10 MP3 samples without dictionary
│       ├── after/                       # 10 MP3 samples with alias applied
│       └── manifest.json                # Audio sample manifest
├── providers/
│   ├── telnyx/                          # 10 JSON files (100 phoneme entries each)
│   ├── elevenlabs/                      # 10 PLS XML files (alias + IPA per lexeme)
│   ├── vapi/                            # 1 JSON file (<<ipa>> per term)
│   ├── amazon-polly/                    # 10 PLS XML files (IPA only, en-US)
│   ├── retell/                          # 1 JSON file (IPA only, word-level, 911 entries)
│   ├── stt/                             # keyterms.txt (comma-separated, 966 terms)
│   └── generic/                         # CSV (text, alias, ipa, category) + nested JSON
├── pls/                                 # 11 W3C PLS XML files (legacy export, alias only)
├── txt/                                 # 11 plain text files (word=alias format)
├── src/
│   ├── terms.py                         # Curated term lists (966 terms)
│   ├── generate_pronunciations.py       # Alias pronunciation generator
│   ├── export_pls.py                    # PLS XML + plain text exporter
│   └── generate_audio_samples.py        # Before/after audio sample generator
├── converters/
│   └── convert_all.py                   # Multi-provider format converter (alias + IPA)
├── import_to_telnyx.py                  # One-command Telnyx API import
├── README.md
├── CONTRIBUTING.md
└── LICENSE
```

## Audio samples

10 before/after pairs generated with Telnyx NaturalHD voice (astra). Each pair shows the same sentence spoken with and without the alias applied. Clone the repo and open the MP3s from `data/audio/before/` and `data/audio/after/`.

| Term | Alias | Before | After |
|------|-------|--------|-------|
| atorvastatin | a-TOR-va-STAT-in | `data/audio/before/atorvastatin_before.mp3` | `data/audio/after/atorvastatin_after.mp3` |
| omeprazole | oh-MEP-rah-zole | `data/audio/before/omeprazole_before.mp3` | `data/audio/after/omeprazole_after.mp3` |
| amoxicillin | ah-MOX-i-sil-in | `data/audio/before/amoxicillin_before.mp3` | `data/audio/after/amoxicillin_after.mp3` |
| metformin | met-FOR-min | `data/audio/before/metformin_before.mp3` | `data/audio/after/metformin_after.mp3` |
| myocardial infarction | my-oh-KAR-dee-al in-FARK-shun | `data/audio/before/myocardial_infarction_before.mp3` | `data/audio/after/myocardial_infarction_after.mp3` |
| cholecystectomy | koh-leh-sis-TEK-toh-mee | `data/audio/before/cholecystectomy_before.mp3` | `data/audio/after/cholecystectomy_after.mp3` |
| cholecystitis | ko-luh-sis-TYE-tis | `data/audio/before/cholecystitis_before.mp3` | `data/audio/after/cholecystitis_after.mp3` |
| MI | myocardial infarction | `data/audio/before/MI_before.mp3` | `data/audio/after/MI_after.mp3` |
| COPD | chronic obstructive pulmonary disease | `data/audio/before/COPD_before.mp3` | `data/audio/after/COPD_after.mp3` |
| epithelium | eh-pih-THEE-lee-um | `data/audio/before/epithelium_before.mp3` | `data/audio/after/epithelium_after.mp3` |

## Adding custom terms

1. Edit `data/terms_master.json` and add your entry: `{"text": "your_term", "alias": "your-A-li-as", "ipa": "jɔːr ˈeɪliəs", "category": "drug"}`. All four fields are required; entries missing `ipa` are skipped by the converter.
2. Run `python3 converters/convert_all.py` to regenerate all provider formats
3. Run `python3 src/export_pls.py` to regenerate `pls/` and `txt/`
4. Re-import to your TTS provider

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow including how to add a new provider format.

## How pronunciations are generated

Pronunciations use plain-text phonetic respelling (alias format) with the stressed syllable capitalized. For example, `atorvastatin` becomes `a-TOR-va-STAT-in`.

This format is chosen over IPA because:
- Works with every TTS provider, not just those that support IPA
- Human-readable and easy to audit
- Simple to edit without phonetic expertise

The initial 966 aliases and IPA entries were generated using an LLM with a medical pronunciation prompt. Pronunciations have not been reviewed by a clinician or pharmacist. Both alias and IPA are known to contain errors in some entries. If you find a wrong pronunciation, open a PR with the correction in `data/terms_master.json`.

For production healthcare deployments, have a clinician or pharmacist review at least the top 100 most common drug pronunciations before shipping.

## Telnyx dictionary quota

This pack creates 10 dictionaries (one per 100 terms). Telnyx allows 50 dictionaries per organization, so this pack uses 20% of the quota. If you need to import additional pronunciation dictionaries for other domains, you have 40 slots remaining.

## Contributing

PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add terms, add provider format converters, and submit changes.

## License

MIT (c) Telnyx, Inc. See [LICENSE](LICENSE).
