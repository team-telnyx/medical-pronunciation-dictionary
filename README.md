# Medical Pronunciation Dictionary

Prepackaged medical pronunciation dictionary for voice AI TTS engines. 962 drugs, clinical terms, anatomical terms, and medical acronyms with phonetic alias pronunciations that import into Telnyx, ElevenLabs, Vapi, and Amazon Polly.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Terms](https://img.shields.io/badge/terms-962-brightgreen)]()
[![Providers](https://img.shields.io/badge/providers-5-blue)]()
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue)]()
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](CONTRIBUTING.md)

## Quick start

### Telnyx API (30 seconds)

```bash
git clone https://github.com/team-telnyx/medical-pronunciation-dictionary.git
cd medical-pronunciation-dictionary
export TELNYX_API_KEY=your_key_here
python3 import_to_telnyx.py
```

Creates 10 pronunciation dictionaries in your Telnyx account, each containing up to 100 terms. Telnyx caps dictionaries at 100 items, so the pack splits automatically.

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

## Why aliases

Alias format uses plain-text phonetic respelling (`a-TOR-va-STAT-in` for atorvastatin). It works across every TTS provider without requiring IPA support. IPA is more precise but only some providers accept it, and the ones that do often need different IPA dialects. Aliases sidestep the entire problem.

## Provider support

| Provider | Format | Status | Files |
|----------|--------|--------|-------|
| Telnyx | JSON items + PLS XML | Supported | `providers/telnyx/` (10 JSON), `pls/` (11 PLS) |
| ElevenLabs | PLS XML | Supported | `providers/elevenlabs/` (10 PLS) |
| Vapi | JSON (no `type` field) | Supported | `providers/vapi/` (1 JSON, 962 items) |
| Amazon Polly | PLS XML | Supported | `providers/amazon-polly/` (10 PLS) |
| Retell | IPA phonemes | Roadmap | Needs IPA entries, not aliases |
| Generic | CSV + JSON | Supported | `providers/generic/` |

## Coverage

| Category | Count | Examples |
|----------|-------|---------|
| Drugs | 396 | atorvastatin, omeprazole, metformin, sertraline |
| Clinical terms | 265 | myocardial infarction, cholecystectomy, atrial fibrillation |
| Anatomical terms | 152 | epithelium, myocardium, synovium, choroid plexus |
| Medical acronyms | 149 | MI, COPD, CHF, UTI, HbA1c, SpO2 |
| **Total** | **962** | |

## File structure

```
medical-pronunciation-dictionary/
├── data/
│   ├── terms_with_pronunciations.json   # Source of truth: 962 terms with aliases
│   └── audio/
│       ├── before/                      # 10 MP3 samples without dictionary
│       ├── after/                       # 10 MP3 samples with alias applied
│       └── manifest.json                # Audio sample manifest
├── providers/
│   ├── telnyx/                          # 10 JSON files (100 items each)
│   ├── elevenlabs/                      # 10 PLS XML files
│   ├── vapi/                            # 1 JSON file (all 962 items)
│   ├── amazon-polly/                    # 10 PLS XML files
│   └── generic/                         # CSV + flat JSON for any provider
├── pls/                                 # 11 W3C PLS XML files (original export)
├── txt/                                 # 11 plain text files (word=alias format)
├── src/
│   ├── terms.py                         # Curated term lists (962 terms)
│   ├── generate_pronunciations.py       # LiteLLM pronunciation generator
│   ├── export_pls.py                    # PLS XML + plain text exporter
│   └── generate_audio_samples.py        # Before/after audio sample generator
├── converters/
│   └── convert_all.py                   # Multi-provider format converter
├── import_to_telnyx.py                  # One-command Telnyx API import
├── README.md
├── CONTRIBUTING.md
└── LICENSE
```

## Audio samples

10 before/after pairs generated with Telnyx NaturalHD voice (astra). Each pair shows the same sentence spoken with and without the alias applied.

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

1. Edit `src/terms.py` and add your term to the appropriate list
2. Run `python3 src/generate_pronunciations.py` (skips already-processed terms, generates aliases for new ones via LiteLLM)
3. Run `python3 converters/convert_all.py` to regenerate all provider formats
4. Run `python3 import_to_telnyx.py` to push to Telnyx

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow including how to add a new provider format.

## How pronunciations are generated

1. Term lists are curated from RxNorm (NLM), SNOMED CT subsets, and clinical knowledge
2. Each term is sent to MiniMax-M3-MXFP8 via LiteLLM with a medical pronunciation expert prompt
3. The model returns a plain-text phonetic respelling with the stressed syllable capitalized
4. Acronyms are expanded to their full form (MI -> myocardial infarction)
5. Output is validated and saved to `data/terms_with_pronunciations.json`

No external g2p library required. The LiteLLM proxy handles the grapheme-to-phoneme conversion with better accuracy for medical terms than generic g2p tools.

## Contributing

PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add terms, add provider format converters, and submit changes.

## License

MIT (c) Telnyx, Inc. See [LICENSE](LICENSE).
