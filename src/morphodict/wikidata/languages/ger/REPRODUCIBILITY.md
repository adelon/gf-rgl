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
| `reports/raw/raw-profile.md` | `5f46c081cb95956bcf97282c9a67523233d50617f1c7d283c56824e2563a57ef` | 5340 |
| `reports/raw/raw-inventory.tsv` | `f6538cdddf05f4a68c655945f0e3710f55f39b13e064c3a8bc86782fe8ecb577` | 487903 |
| `reports/raw/raw-feature-bundles.tsv` | `6815758616a9e75928e921b3e8c99a3a921e6b24cb9e87faa6d87fa152789c95` | 36614 |
| `profile.md` | `a07b5ce1d8e560bd296dc3694dea20ab23b66e19685d5ed48c9d15e8fb5673ff` | 7416 |
| `unknown-features.tsv` | `269177a37c45bdba94f093828dbcdf639dda3f5d324ee760efa1fee6780a17b2` | 2087 |
| `fixtures/pinned/lexemes.json` | `e00c36f54e169250190ad7f79f5b4cdcdc798ebea6b8a0dab529ac6d5cffa724` | 82490 |
| `fixtures/pinned/manifest.tsv` | `bbf47f856f9c1c8906272709beafa9340554334af5bf4fac629476b950675f89` | 1627 |

The historical German dictionaries were not read as inventory inputs. No GF
entries, candidate names, placement rules, compatibility declarations, or
dictionary generators were produced. No RGL build was run because no RGL
source file changed in Phase 1.
