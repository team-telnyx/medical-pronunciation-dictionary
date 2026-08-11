# Medical Pronunciation Dictionary

Prepackaged medical pronunciation dictionary for voice AI TTS engines. 966 drugs, clinical terms, anatomical terms, and medical acronyms with both phonetic alias and IPA pronunciations. Imports into Telnyx, ElevenLabs, Vapi, Retell, and Amazon Polly.

Every alias was tested against a real TTS engine. The alias packs ship only the 271 entries that measurably improve pronunciation, because 309 of the other 695 made it **worse**. See [Which entries ship](#which-entries-ship).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Terms](https://img.shields.io/badge/terms-966-brightgreen)]()
[![Verified aliases](https://img.shields.io/badge/verified%20aliases-271-brightgreen)]()
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

Reads `providers/telnyx/` and creates 3 pronunciation dictionaries in your Telnyx account, 271 alias entries total. Telnyx caps dictionaries at 100 items and rejects duplicate `text` entries, so the pack uses one alias entry per term.

There are two Telnyx packs. The default is alias, because alias works on every Telnyx voice. IPA phonemes only work on **Telnyx Ultra, MiniMax and Inworld**, and on any other voice they make pronunciation worse rather than being ignored. If you are on one of those three engines:

```bash
python3 import_to_telnyx.py --ipa
```

See [Which format each provider gets](#which-format-each-provider-gets).

### Telnyx Portal

1. Log in to [portal.telnyx.com](https://portal.telnyx.com)
2. Go to **AI Suite -> Pronunciation Dictionaries**
3. Click **Create Dictionary**
4. Upload each of the 6 PLS XML files from `pls/` or plain text files from `txt/`

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

`data/terms_master.json` carries both for every term, and the converter emits whichever format the provider actually applies.

### Which format each provider gets

| Provider | Emitted | Why |
|----------|---------|-----|
| Telnyx (default) | alias | Alias is the only entry type that works on every Telnyx voice, so it is the safe default for a pack you hand to someone else. |
| Telnyx Ultra / MiniMax / Inworld | phoneme (`providers/telnyx-ipa/`) | These three engines support IPA. Opt in with `import_to_telnyx.py --ipa`. On any other voice a phoneme entry is not ignored, it is destructive: verified on `Telnyx.NaturalHD.astra`, where mapping `tomato` to `/təˈmeɪtoʊ/` renders as "tee me me to ours", and on `Telnyx.KokoroTTS.af`, which speaks the literal Unicode character names. The same dictionary on `Telnyx.Ultra` renders `tomato` correctly. |
| ElevenLabs | alias + phoneme | PLS supports both per lexeme |
| Amazon Polly | phoneme | Polly lexicons are IPA-based |
| Vapi | phoneme (`<<ipa>>`) | Vapi's documented syntax. Not independently verified. |
| Retell | phoneme | Retell's documented word/phoneme format. Not independently verified. |
| Generic | both | the consumer decides |

Telnyx, Vapi, and Retell reject duplicate entries for the same word, so those get one rule per term rather than a competing alias and phoneme pair.

The Telnyx TTS request field is `pronunciation_dict_id`, singular, a string. The plural spellings are accepted with HTTP 200 and silently ignored.

The audio samples below were generated on `Telnyx.NaturalHD.astra`, so they show the alias pack.

## Which entries ship

All 966 terms were rendered twice on `Telnyx.NaturalHD.astra`, with and without their alias entry, using an identical carrier sentence. Both clips were transcribed blind, with no indication of which was which and no mention of the target term.

| Verdict | Terms | Meaning |
|---------|-------|---------|
| HELPS | 271 | the alias fixes a real mispronunciation |
| WASH | 386 | no audible improvement |
| HURTS | 309 | the alias makes a correctly-pronounced word worse |

It splits almost entirely by category:

| Category | Helps | Hurts |
|----------|-------|-------|
| acronym (149) | **91%** | 1% |
| drug (398) | 26% | 30% |
| anatomical (150) | 9% | 38% |
| clinical (269) | 7% | **48%** |

Acronym aliases are spoken expansions (`MI` -> "myocardial infarction") that the engine reads fluently. The other categories use hyphenated respellings, and the engine reads those syllable by syllable: `encephalopathy` becomes "un say fa lop a v" on a word it already said correctly.

So the alias-based outputs ship the 271 that help. Phoneme-based outputs still carry all 966, because the fragmentation is an alias-tokenisation problem and no phoneme engine has been measured.

| Output | Terms | Filtered? |
|--------|-------|-----------|
| `providers/telnyx/` | 271 | yes, alias |
| `pls/`, `txt/` | 271 | yes, alias-only exports |
| `providers/elevenlabs/` | 966 lexemes | phoneme on all, `<alias>` on 271 |
| `providers/telnyx-ipa/`, `amazon-polly/`, `vapi/`, `retell/` | 966 (911 for Retell) | no, phoneme |
| `providers/generic/` | 966 | no, verdict exposed as a column |

`data/terms_master.json` keeps all 966 with a `telnyx_naturalhd_verdict` field. Nothing is deleted. Per-term evidence, including both transcriptions, is in [`data/telnyx_naturalhd_audit.csv`](data/telnyx_naturalhd_audit.csv).

**Caveat:** measured on one voice. A different engine may tokenise hyphenated aliases differently, so the specific 271 is Telnyx-NaturalHD-specific. The method is not.

## Provider support

| Provider | Format | Alias | IPA | Files |
|----------|--------|-------|-----|-------|
| Telnyx | JSON items | Yes | No | `providers/telnyx/` (3 JSON, 271 verified alias entries) |
| Telnyx Ultra / MiniMax / Inworld | JSON items | No | Yes | `providers/telnyx-ipa/` (10 JSON, 100 phoneme entries each) |
| Telnyx | PLS XML | Yes | No | `pls/` (6 PLS, 271 verified aliases) |
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
│   ├── terms_master.json                # Source of truth: 966 terms, alias + IPA + verdict
│   ├── telnyx_naturalhd_audit.csv       # Per-term audit evidence (966 rows)
│   └── audio/
│       ├── before/                      # 6 MP3 samples, no dictionary attached
│       ├── after/                       # 6 MP3 samples, dictionary attached
│       └── manifest.json                # Audio sample manifest
├── providers/
│   ├── telnyx/                          # 3 JSON files (271 verified alias entries)
│   ├── telnyx-ipa/                      # 10 JSON files, IPA (Ultra/MiniMax/Inworld only)
│   ├── elevenlabs/                      # 10 PLS XML files (alias + IPA per lexeme)
│   ├── vapi/                            # 1 JSON file (<<ipa>> per term)
│   ├── amazon-polly/                    # 10 PLS XML files (IPA only, en-US)
│   ├── retell/                          # 1 JSON file (IPA only, word-level, 911 entries)
│   ├── stt/                             # keyterms.txt (comma-separated, 966 terms)
│   └── generic/                         # CSV (text, alias, ipa, category) + nested JSON
├── pls/                                 # 6 W3C PLS XML files (271 verified aliases)
├── txt/                                 # 6 plain text files (word=alias format)
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

6 before/after pairs generated with the Telnyx NaturalHD voice (astra) by `src/generate_audio_samples.py`.

Both clips in a pair use the **identical sentence text**. The only difference is whether a real Telnyx pronunciation dictionary is attached to the request via `pronunciation_dict_id`. Clone the repo and open the MP3s from `data/audio/before/` and `data/audio/after/`.

These six are terms where attaching the dictionary makes an audible difference. Plenty of medical terms are already pronounced correctly by the engine, and a before/after pair that sounds identical demonstrates nothing, so they are not included here.

| Term | Without dictionary | Alias applied | Files |
|------|--------------------|---------------|-------|
| MI | heard as "me" | `myocardial infarction` | [before](data/audio/before/MI_before.mp3) / [after](data/audio/after/MI_after.mp3) |
| CHF | clipped mid-word | `congestive heart failure` | [before](data/audio/before/CHF_before.mp3) / [after](data/audio/after/CHF_after.mp3) |
| COPD | dropped entirely | `chronic obstructive pulmonary disease` | [before](data/audio/before/COPD_before.mp3) / [after](data/audio/after/COPD_after.mp3) |
| DVT | spelled out letter by letter | `deep vein thrombosis` | [before](data/audio/before/DVT_before.mp3) / [after](data/audio/after/DVT_after.mp3) |
| ceftriaxone | heard as "sef-CHAX-one" | `sef-try-AX-one` | [before](data/audio/before/ceftriaxone_before.mp3) / [after](data/audio/after/ceftriaxone_after.mp3) |
| furosemide | heard as "FOR-us my-dis" | `fur-OH-se-mide` | [before](data/audio/before/furosemide_before.mp3) / [after](data/audio/after/furosemide_after.mp3) |

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
