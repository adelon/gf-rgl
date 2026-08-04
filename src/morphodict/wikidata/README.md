# German Wikidata Lexeme profile prototype

This directory contains the German-only source ingestion, profile, and Phase 2
noun-fitting experiment described in `~/scratch/rgl/import.md`. It consumes one
finalized, dated Wikidata Lexeme JSON dump, selects entities whose entity-level
language is exactly `Q188`, and retains each selected entity as canonical,
semantically lossless JSON in a local SQLite store.

Wikidata structured data is CC0. The committed snapshot lock identifies the
source bytes; the retained dump, SQLite databases, partial downloads, and
detailed generated reports remain ignored under `.work/`.

The historical `MorphoDictGer` and `DictGer` inventories are not inputs. The
noun pilot generates only disposable probe entries with deterministic internal
identifiers; it makes no naming, placement, curation, compatibility, or
compound-generation decision.

## Requirements and local commands

Python 3.11 or newer is required. Python runtime and tests use only the standard
library. The noun probe additionally uses the repository's preflighted local GF
executable and the matching GF Stack environment to compile a small Haskell/PGF
bridge.

From this directory:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m wd2gf.cli --help
PYTHONPATH=src python3 -m wd2gf.cli snapshot resolve --date 20260729 --compression gz
PYTHONPATH=src python3 -m wd2gf.cli snapshot download
PYTHONPATH=src python3 -m wd2gf.cli snapshot verify
PYTHONPATH=src python3 -m wd2gf.cli store ingest
PYTHONPATH=src python3 -m wd2gf.cli store fingerprint
PYTHONPATH=src python3 -m wd2gf.cli profile raw
PYTHONPATH=src python3 -m wd2gf.cli profile interpreted
PYTHONPATH=src python3 -m wd2gf.cli fixture extract
PYTHONPATH=src python3 -m wd2gf.cli noun sample
PYTHONPATH=src python3 -m wd2gf.cli noun render
PYTHONPATH=src python3 -m wd2gf.cli noun probe --gf="$GF"
PYTHONPATH=src python3 -m wd2gf.cli noun pilot --gf="$GF"
```

Snapshot acquisition and profile commands are documented by the CLI itself.
Network access is needed only to resolve and download a snapshot. Verification,
ingestion, and profiling are offline once the finalized lock and retained dump
are present.

Selected full-snapshot results are committed under `languages/ger`: the raw
source-ID inventories, complete pinned entities, the reviewed feature policy,
the interpreted `profile.md`, `unknown-features.tsv`, and the clean-repeat
fingerprints in `REPRODUCIBILITY.md`. Phase 2 also commits the frozen noun
policy, stratified source sample, accepted complete-record fits, and explicit
rejections. Generated GF, GFO, PGF, Haskell build products, detailed fit JSON,
databases, and repeat outputs stay under ignored `.work/` paths.

The probe considers only the closed set of public `ParadigmsGer` noun
constructors recorded in `noun-policy.toml`, from least to most explicit. Its
Haskell bridge emits structured TSV from coherent PGF linearization variants;
Python never parses human-oriented GF shell output. The fit report records all
case/number forms, gender, `co`, `uncap.s`, `uncap.co`, and `csep`, and labels
those values as GF output separately from the source Form and statement IDs.
`Q107614077` Forms are atomic combining-form evidence. `P5548` evidence remains
construction-specific and is not promoted to unrestricted `N.co` evidence.

Accepted entities are serialized with UTF-8 characters unescaped, object keys
sorted, no optional whitespace, and standard JSON string/number semantics;
duplicate object keys and non-finite numbers are rejected. The SHA-256 stored
for each Lexeme identifies that canonical semantic payload, while the snapshot
lock identifies the exact compressed source bytes.
