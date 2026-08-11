# Contributing

PRs welcome. This guide covers how to add terms, add provider format converters, and submit changes.

## Adding new terms

The source of truth is `data/terms_master.json`. Each entry has `text`, `alias`, `ipa`, and `category` fields. **All four are required.** `converters/convert_all.py` skips any entry missing `text`, `alias`, or `ipa`, so an entry without IPA silently disappears from every provider output.

1. Edit `data/terms_master.json` and add your term:

```json
[
  {
    "text": "atorvastatin",
    "alias": "a-TOR-va-STAT-in",
    "ipa": "əˌtɔr.vəˈstæ.tɪn",
    "category": "drug"
  },
  {
    "text": "your-new-drug-name",
    "alias": "your-PHON-et-ic-AL-ias",
    "ipa": "jɔːr ˈfoʊnɛtɪk ˈeɪliəs",
    "category": "drug"
  }
]
```

Categories: `drug`, `clinical`, `anatomical`, `acronym`.

Conventions:

- `alias` is a plain-text respelling, hyphen-separated, with the stressed syllable in caps: `oh-MEP-rah-zole`.
- `ipa` is American English IPA with a primary stress mark. Use `ɡ` (U+0261) not ASCII `g`, and keep the rhotic/non-rhotic choice consistent with the rest of the file.
- `alias` and `ipa` must describe the **same** pronunciation. Different providers get different formats, so a disagreement produces different speech depending on where the pack is loaded.
- Keep aliases pronounceable as a unit. A respelling with too many hyphens can be read syllable by syllable: `amoxicillin` -> `a-mox-i-sil-in` comes out worse than leaving the word alone. If the engine already says a term correctly, a bad alias is a regression, not a no-op.
- For acronyms, `alias` is the spoken expansion (`MI` -> `myocardial infarction`) and `ipa` transcribes that expansion.

2. Regenerate every provider format:

```bash
python3 converters/convert_all.py
```

3. Regenerate the legacy alias-only PLS and plain-text exports:

```bash
python3 src/export_pls.py
```

4. Verify the output under `providers/` and commit the regenerated files along with your data change.

5. Optionally push the updated dictionaries to your own Telnyx account:

```bash
export TELNYX_API_KEY=your_key_here
python3 import_to_telnyx.py --dry-run   # preview
python3 import_to_telnyx.py             # create
```

6. To add a before/after audio sample, add the term to `SAMPLE_TERMS` in `src/generate_audio_samples.py` and run it. The script builds a real Telnyx dictionary, renders the same sentence with and without it, and deletes the dictionary afterwards. Output lands in `data/audio/before/` and `data/audio/after/`, and it rewrites `data/audio/manifest.json` with repo-relative paths.

   Only add a term if the pair actually differs. Compare the two MP3s before committing; a pair that sounds identical means the engine already handled the term and the sample demonstrates nothing.

## Adding a new provider format

`converters/convert_all.py` is a single module with one writer function per provider. To add a provider:

1. Add a writer that takes the loaded terms and an output directory, and returns the paths it wrote:

```python
def write_newprovider(terms: list[dict], out_dir: Path) -> list[Path]:
    """Single JSON file in NewProvider's schema."""
    out_dir.mkdir(parents=True, exist_ok=True)
    items = [
        {"word": item["text"], "pronunciation": item["alias"]}
        for item in terms
    ]
    path = out_dir / "medical-pronunciations.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump({"items": items}, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return [path]
```

2. Call it from `main()` and append the result to `summary`:

```python
print("[8/8] NewProvider JSON ...")
summary.append(("newprovider", write_newprovider(terms, PROVIDERS_DIR / "newprovider")))
```

3. Renumber the existing `[n/7]` progress labels.

4. Add a usage example to `README.md` under Quick start, and a row to the provider support table.

## PR checklist

Before submitting a PR, confirm:

- [ ] `python3 converters/convert_all.py` runs without errors and reports 0 skipped entries
- [ ] `python3 src/export_pls.py` runs without errors
- [ ] All regenerated files under `providers/`, `pls/`, and `txt/` are committed
- [ ] Term count in the `README.md` coverage table matches `data/terms_master.json`
- [ ] Provider support table in `README.md` reflects any new providers
- [ ] `alias` and `ipa` agree on stress and syllables for every term you touched
- [ ] No secrets, API keys, absolute local paths, or internal hostnames in the diff
- [ ] No comments added unless they explain non-obvious behavior

## Code style

- Python 3.9+
- PEP 8
- No comments unless they explain non-obvious behavior
- Type hints on public functions
- One responsibility per module
- No backwards-compat hacks; change the code

## Questions

Open an issue or reach out in the PR thread.
