# Phase 1 reproducibility record

This record covers the clean repeated ingestion and profiling run for the
official 2026-07-29 Wikidata Lexeme JSON gzip snapshot.

## Locked source

- Filename: `wikidata-20260729-lexemes.json.gz`
- Size: `596452649` bytes
- Official SHA-1: `12af73de6faa212ae3273343755e271c240a1f7d`
- Local SHA-256: `ff02d6805f4b4d97d51091caa45ce12371b0ce543c33909c8c96a6b17c22b937`
- Selection: entity-level `language == Q188` exactly

## Clean-repeat commands

From `src/morphodict/wikidata`:

Commands that generate the committed output locations:

```sh
PYTHONPATH=src python3 -m wd2gf.cli profile raw --output-dir languages/ger/reports/raw
PYTHONPATH=src python3 -m wd2gf.cli profile interpreted --output-dir languages/ger
PYTHONPATH=src python3 -m wd2gf.cli fixture extract --output-dir languages/ger/fixtures/pinned
```

Commands that create the independent repeat store and repeat outputs:

```sh
PYTHONPATH=src python3 -m wd2gf.cli snapshot verify
PYTHONPATH=src python3 -m wd2gf.cli store ingest
PYTHONPATH=src python3 -m wd2gf.cli store ingest --database .work/repeat/german-lexemes.sqlite3
PYTHONPATH=src python3 -m wd2gf.cli store fingerprint
PYTHONPATH=src python3 -m wd2gf.cli store fingerprint --database .work/repeat/german-lexemes.sqlite3
PYTHONPATH=src python3 -m wd2gf.cli profile raw --database .work/repeat/german-lexemes.sqlite3 --output-dir .work/repeat/raw
PYTHONPATH=src python3 -m wd2gf.cli profile interpreted --database .work/repeat/german-lexemes.sqlite3 --output-dir .work/repeat/interpreted
PYTHONPATH=src python3 -m wd2gf.cli fixture extract --database .work/repeat/german-lexemes.sqlite3 --output-dir .work/repeat/pinned
```

Commands that compare every committed artifact with its repeat counterpart:

```sh
cmp languages/ger/reports/raw/raw-profile.md .work/repeat/raw/raw-profile.md
cmp languages/ger/reports/raw/raw-inventory.tsv .work/repeat/raw/raw-inventory.tsv
cmp languages/ger/reports/raw/raw-feature-bundles.tsv .work/repeat/raw/raw-feature-bundles.tsv
cmp languages/ger/profile.md .work/repeat/interpreted/profile.md
cmp languages/ger/unknown-features.tsv .work/repeat/interpreted/unknown-features.tsv
cmp languages/ger/fixtures/pinned/lexemes.json .work/repeat/pinned/lexemes.json
cmp languages/ger/fixtures/pinned/manifest.tsv .work/repeat/pinned/manifest.tsv
```

Both database paths were absent before their respective create-from-scratch
runs. The following fingerprints were identical:

- Metadata SHA-256: `caa3a8af3678131a9321435faca9ad06ad69b693a96c8430636cedc0c230b042`
- Ordered selected-entity-hash SHA-256: `f9fd213c8c3ae2cae5ee70fec28e25370ce63bd84f0d74353ef85304b3c4b0e6`

Projection counts in both stores:

| Table | Rows |
|---|---:|
| `lexeme` | 241967 |
| `lemma` | 242059 |
| `form` | 2024122 |
| `form_representation` | 2024719 |
| `form_feature` | 5532732 |
| `sense` | 19957 |
| `sense_gloss` | 23640 |
| `statement` | 1171782 |
| `qualifier` | 17497 |

Envelope and selection counts in both stores:

- Validated entities before selection: `1536601`
- Selected exact-`Q188` entities: `241967`
- Excluded by entity language: `1294634`

## Byte-identical outputs

The primary and repeated outputs compared byte-for-byte:

| Artifact | SHA-256 | Bytes |
|---|---|---:|
| `reports/raw/raw-profile.md` | `ee27b29b884ac58962d980b8f87a2e3fd386c2e73c61c749475eb9598ad1f89e` | 6028 |
| `reports/raw/raw-inventory.tsv` | `f6538cdddf05f4a68c655945f0e3710f55f39b13e064c3a8bc86782fe8ecb577` | 487903 |
| `reports/raw/raw-feature-bundles.tsv` | `6815758616a9e75928e921b3e8c99a3a921e6b24cb9e87faa6d87fa152789c95` | 36614 |
| `profile.md` | `29c1fec0f33b84b0ca596520b18e669213a70fde9e69d9e3f939eab828239214` | 8209 |
| `unknown-features.tsv` | `269177a37c45bdba94f093828dbcdf639dda3f5d324ee760efa1fee6780a17b2` | 2087 |
| `fixtures/pinned/lexemes.json` | `e00c36f54e169250190ad7f79f5b4cdcdc798ebea6b8a0dab529ac6d5cffa724` | 82490 |
| `fixtures/pinned/manifest.tsv` | `bbf47f856f9c1c8906272709beafa9340554334af5bf4fac629476b950675f89` | 1627 |

The compound-evidence validation update reused the two fingerprint-identical
stores above. It reran only the four raw/interpreted profile commands and the
`cmp` commands; it did not ingest the dump again.

The historical German dictionaries were not read as inventory inputs. No GF
entries, candidate names, placement rules, compatibility declarations, or
dictionary generators were produced. No RGL build was run because no RGL
source file changed in Phase 1.
