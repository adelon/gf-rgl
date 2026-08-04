# German Wikidata Lexeme profile prototype

This directory contains the Phase 1, German-only source ingestion and profile
experiment described in `~/scratch/rgl/import.md`. It consumes one finalized,
dated Wikidata Lexeme JSON dump, selects entities whose entity-level language
is exactly `Q188`, and retains each selected entity as canonical, semantically
lossless JSON in a local SQLite store.

Wikidata structured data is CC0. The committed snapshot lock identifies the
source bytes; the retained dump, SQLite databases, partial downloads, and
detailed generated reports remain ignored under `.work/`.

The historical `MorphoDictGer` and `DictGer` inventories are not inputs. Phase
1 does not generate GF entries or make naming, placement, curation, or
compatibility decisions.

## Requirements and local commands

Python 3.11 or newer is required. Runtime and tests use only the Python
standard library.

From this directory:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m wd2gf.cli --help
PYTHONPATH=src python3 -m wd2gf.cli snapshot resolve --date 20260729 --compression gz
PYTHONPATH=src python3 -m wd2gf.cli snapshot download
PYTHONPATH=src python3 -m wd2gf.cli snapshot verify
PYTHONPATH=src python3 -m wd2gf.cli store ingest
PYTHONPATH=src python3 -m wd2gf.cli profile raw
PYTHONPATH=src python3 -m wd2gf.cli fixture extract
```

Snapshot acquisition and profile commands are documented by the CLI itself.
Network access is needed only to resolve and download a snapshot. Verification,
ingestion, and profiling are offline once the finalized lock and retained dump
are present.

Accepted entities are serialized with UTF-8 characters unescaped, object keys
sorted, no optional whitespace, and standard JSON string/number semantics;
duplicate object keys and non-finite numbers are rejected. The SHA-256 stored
for each Lexeme identifies that canonical semantic payload, while the snapshot
lock identifies the exact compressed source bytes.
