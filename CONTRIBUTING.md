# Contributing

PRs welcome. This guide covers how to add terms, add provider format converters, and submit changes.

## Adding new terms

The source of truth is `data/terms_with_pronunciations.json`. Each entry has `text`, `alias`, and `category` fields.

1. Edit `data/terms_with_pronunciations.json` and add your term to the appropriate category:

```json
[
  {
    "text": "atorvastatin",
    "alias": "a-TOR-va-STAT-in",
    "category": "drug"
  },
  {
    "text": "your-new-drug-name",
    "alias": "your-PHON-et-ic-AL-ias",
    "category": "drug"
  }
]
```

Categories: `drug`, `clinical`, `anatomical`, `acronym`.

2. Run the converter to regenerate all provider formats:

```bash
python converters/run_all.py
```

3. Verify the output by checking `providers/telnyx/`, `providers/elevenlabs/`, `providers/vapi/`, and `providers/amazon-polly/`.

4. Run the Telnyx import to push the updated dictionaries:

```bash
python import_to_telnyx.py
```

5. Add a before/after audio sample to `data/audio/<term>/` if the term is commonly mispronounced.

## Adding a new provider format converter

Each provider has its own quirks. To add a new provider:

1. Create a new converter module in `converters/`:

```python
# converters/newprovider.py
import json
from xml.etree import ElementTree as ET


def convert(terms: list[dict]) -> str:
    """Convert terms to NewProvider format."""
    root = ET.Element("pronunciations")
    for term in terms:
        entry = ET.SubElement(root, "phoneme")
        entry.set("word", term["text"])
        entry.set("pronunciation", term["alias"])
    return ET.tostring(root, encoding="unicode")
```

2. Add the output directory to `providers/`:

```
providers/
└── newprovider/
    └── medical-pronunciations.xml
```

3. Wire it into `converters/run_all.py`:

```python
from converters import newprovider

def run_all(terms: list[dict]) -> None:
    telnyx.convert(terms)
    elevenlabs.convert(terms)
    vapi.convert(terms)
    polly.convert(terms)
    newprovider.convert(terms)  # new
```

4. Add a usage example to `README.md` under the Usage section.

5. Update the provider support table in `README.md`.

## PR checklist

Before submitting a PR, confirm:

- [ ] `python converters/run_all.py` runs without errors
- [ ] All output files in `providers/` are regenerated
- [ ] Term count in `README.md` coverage table matches `data/terms_with_pronunciations.json`
- [ ] Provider support table in `README.md` reflects any new providers
- [ ] Before/after audio samples added for commonly mispronounced terms
- [ ] No secrets, API keys, or credentials in the diff
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
