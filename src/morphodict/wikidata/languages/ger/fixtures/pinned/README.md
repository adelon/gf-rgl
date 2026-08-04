# Pinned-dump fixtures

This directory contains a small, complete selection of German Lexeme entities
from the verified 2026-07-29 snapshot. `lexemes.json` uses the same canonical
serialization as the source store without projecting away forms, senses,
statements, qualifiers, references, or unusual strings. `manifest.tsv` records
the snapshot SHA-256, each canonical entity hash, raw category QID, and the
source-profile stratum that motivated selection.

`selection.tsv` is the reviewed source-only selection policy. Regenerate the
fixture after a verified full ingest with:

```sh
PYTHONPATH=src python3 -m wd2gf.cli fixture extract
```
