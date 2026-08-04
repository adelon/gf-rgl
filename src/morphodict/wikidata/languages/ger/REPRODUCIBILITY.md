# Phase 1 and Phase 2 reproducibility record

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

## Phase 2 German noun pilot

The noun pilot reused the verified primary Phase 1 store. It did not ingest the
dump again. From `src/morphodict/wikidata`, the committed report locations were
generated with the preflighted local GF executable:

```sh
PYTHONPATH=src python3 -m wd2gf.cli noun pilot --gf="$GF" --output-dir .work/phase2/pilot --report-dir languages/ger
```

An independent generation used distinct disposable and report directories:

```sh
PYTHONPATH=src python3 -m wd2gf.cli noun pilot --gf="$GF" --output-dir .work/phase2/repeat-pilot --report-dir .work/phase2/repeat-reports
cmp languages/ger/noun-sample.tsv .work/phase2/repeat-reports/noun-sample.tsv
cmp languages/ger/noun-fit.tsv .work/phase2/repeat-reports/noun-fit.tsv
cmp languages/ger/noun-rejections.tsv .work/phase2/repeat-reports/noun-rejections.tsv
```

The primary and repeat report bytes were identical:

| Artifact | SHA-256 | Bytes | Data rows |
|---|---|---:|---:|
| `noun-sample.tsv` | `a97a43ea48bb07140dffd34aa844bb6ae53b151c4195b9fa43cabbe9f2c443c7` | 273348 | 352 |
| `noun-fit.tsv` | `8370b5983c0575eb2ec336679f4a874e658328a9d4f1c60825b23a4c0c306385` | 412017 | 261 |
| `noun-rejections.tsv` | `c23cedc5d3480322adcf12181254f2aca689dbf6e4e9da228f07bae034a1d48c` | 47914 | 91 |

The disposable abstract module, concrete module, proposal manifest, structured
probe output, detailed fit JSON, and PGF were also byte-identical between the
two directories. Their respective SHA-256 hashes were
`8067f5e6413bda197a8005999bd5b116d9a94188a3ed4f9b2431ffc1b6dcc786`,
`8fbb70f723fea7728e166a1f6dc79a3552ae69c9e5d34a0bc023725f4fa4e77c`,
`bf7e26ecb84282eeb65b2dff8b0f08b15505fad18df30b5785f06e8545bb52d3`,
`78455ebf893a61c7520af520dd9ba11625a230ea959017663162c779d9fd05b1`,
`3ae14c0c7a37e75c294a3fa022081bf7986536016f8841203a980fc09c739799`,
and `537756d1f474dff804f2564fc787e3f6777d12b4b73dd31811dcf66f04d6bea4`.
The manifest contained 1967 proposals and the structured probe contained 42740
field rows.

Of 352 sampled nouns, 200 had exact source-evidence fits and 61 had fits
compatible with stated inference. Every one of the 261 accepted rows records
the complete 20-field GF noun record, per-field evidence status, source entity
hashes and Lexeme/Form/statement IDs, deterministic candidate and proposal
identities, structural evidence, and review status. All accepted records retain
at least provisional inference metadata because GF supplies fields not asserted
by Wikidata; these generated values are reported only in `gf_*` columns.

The 91 rejections were:

| Reason | Nouns |
|---|---:|
| singular-only residual API gap | 20 |
| unresolved multiple-gender alternatives | 20 |
| conflicting source slots | 20 |
| unsupported form feature | 10 |
| multiword outside the atomic pilot | 10 |
| missing gender evidence | 5 |
| missing required forms | 1 |
| adjectival-declension category mismatch | 1 |
| multiple unsupported combining forms | 3 |
| forms conflict with number restriction | 1 |

The only demonstrated residual public-API population is therefore the 20
singular-only nouns that need a public singular-only constructor. Five
previously unmatched records lacked gender evidence, one plural-only record
lacked forms, and the adjectivally declined `Verwandte` is a category/modelling
mismatch rather than an ordinary noun-constructor gap. Phase 2 does not add an
API. The sample also forces four pinned dump-derived Lexemes: `L3146`, `L10227`,
`L40399`, and `L295104`; all four obtained complete-record fits.

Report status terms have the following frozen meanings:

| Term | Meaning |
|---|---|
| `automatic` | Extracted and classified by frozen policy; no individual linguistic judgement is claimed. |
| `sampled` | Included in the deterministic pilot and structurally probed; not thereby individually reviewed. |
| `individually_reviewed` | A human reviewer has adjudicated the cited morphology or structural evidence. |
| `reviewed_inference` | Supplied by an explicitly frozen productive rule or recorded individual adjudication. |
| `provisional_inference` | Compatible GF output without source or frozen reviewed support. |
| `rejected` | Excluded under a recorded source-gap, ambiguity, category, or representation policy. |

The focused Python suite, warning-clean Haskell typecheck, disposable GF module
compile, structured PGF probe, and byte-repeat checks passed. No broad RGL build
was run because no RGL source changed. No canonical dictionary entries,
compounds, public names, placement rules, or generated GF artifacts were
committed.

## Phase 3 full-population noun census

The compile-free census was generated from the verified primary store with:

```sh
PYTHONPATH=src python3 -m wd2gf.cli noun census --output languages/ger/noun-census.md --details .work/phase3/census/noun-census.tsv
```

An independent repeat used separate output paths:

```sh
PYTHONPATH=src python3 -m wd2gf.cli noun census --output .work/phase3/census-repeat/noun-census.md --details .work/phase3/census-repeat/noun-census.tsv
cmp languages/ger/noun-census.md .work/phase3/census-repeat/noun-census.md
cmp .work/phase3/census/noun-census.tsv .work/phase3/census-repeat/noun-census.tsv
```

Both the compact report and the 188942-row local detail file were
byte-identical. `noun-census.md` is 6495 bytes with SHA-256
`2d822f22a682c49d748dc1d596e93ba8a88a6e91b82e4c33a11f799baa09152b`;
the local detail is 48113280 bytes with SHA-256
`526a34af000af0ef739d75e922f4accbe685205583e2023292dabaa5aaf4f688`.
The census compiled no GF and did not inspect `ger` or `ger-fixes` placement.
Candidates without a source component analysis remain structurally unresolved
rather than being counted as atomic. Counts, acceptance tiers, multi-gender
correlation findings, ambiguity and quarantine reasons, and placement-neutral
cohorts are recorded in `noun-census.md`.
