# German noun first scale gate

The authorized 5,000-candidate Phase 3 gate passed its frozen local
budgets twice. The 25,000 gate was not run. Proposal fitting and the
one-selected-constructor resulting module are measured separately.

- Snapshot dump date: `2026-07-29`
- Snapshot SHA-256: `ff02d6805f4b4d97d51091caa45ce12371b0ce543c33909c8c96a6b17c22b937`
- GF: `Grammatical Framework (GF) version 3.12.0`
- GF build: `Built on linux/x86_64 with ghc-9.6 at 2026-06-10 01:37:43`
- GF executable: `/home/aleph/code/gf-core/.stack-work/install/x86_64-linux/45f76329935f82047fd129672ce6eecf7484ab62efd519524a5fd6bcebc44f96/9.6.7/bin/gf`
- GF executable SHA-256: `a88bf62ab2b2fa90842894ff3be9b567d561ad8f395fc1d85b2eb5343b5244a0`
- Fitting chunk size: `500` candidates
- Deterministic artifacts compared: `117` files
- Semantic summary SHA-256: `b14f1bb1a42f7b031e44c1abec5fa3284fcdb400cd638268ec5c80943c61fe10`

## Deterministic populations and outcomes

The fitting sample contains `5000` candidates in
`22` source-completeness and
rejection strata. Its selection TSV SHA-256 is
`37cf131fda63d2fd741ae595faafa6fc86f5a52327352407c6e3137a5fbd5caa`.

| Projected tier | Candidates | GF fits | No fit |
|---|---|---|---|
| automatic_complete | 3283 | 3282 | 1 |
| automatic_complete_with_co | 9 | 9 | 0 |
| excluded | 1177 | 242 | 935 |
| review_required_provisional | 531 | 498 | 33 |

Those candidates generated `29116` competing
constructor proposals. A GF fit does not override an excluded source or
review classification; this is why some excluded candidates can still be
morphologically representable.

No-fit reasons in the fitting sample:

| Reason | Candidates |
|---|---|
| ambiguous_gf_record_variants | 7 |
| ambiguous_multiple_combining_forms | 1 |
| conflicting_source_slots | 860 |
| forms_conflict_with_number_restriction | 2 |
| multiword_outside_atomic_noun_pilot | 14 |
| residual_api_gap_singular_only | 12 |
| source_evidence_gap_missing_de_lemma | 1 |
| source_evidence_gap_missing_gender | 31 |
| source_evidence_gap_missing_required_forms | 1 |
| unclassified_constructor_mismatch | 3 |
| unresolved_multiple_gender_alternatives | 35 |
| unsupported_form_feature | 2 |

The deterministic accepted-entry pool contained
`5200` projected automatic candidates
and retained same-tier reserves before selecting exactly 5,000 successful
fits:

| Projected tier | Pool candidates | GF fits | No fit |
|---|---|---|---|
| automatic_complete | 5087 | 5085 | 2 |
| automatic_complete_with_co | 113 | 113 | 0 |

| Result acceptance tier | Entries |
|---|---|
| automatic_complete | 4987 |
| automatic_complete_with_co | 13 |

Selected constructor distribution:

| Constructor | Entries |
|---|---|
| abbrevN+invarN_one | 1 |
| abbrevN+invarN_two | 2 |
| changeCompoundN+mkN_lemma | 3 |
| changeCompoundN+mkN_lemma_gender | 1 |
| changeCompoundN+mkN_two | 2 |
| invarN_one | 13 |
| invarN_two | 330 |
| invarPlN_one | 4 |
| invarPlN_two | 307 |
| mkN_lemma | 2950 |
| mkN_lemma_gender | 635 |
| mkN_six | 42 |
| mkN_two | 710 |

All 5,000 result entries were probed across every case/number form, gender,
`co`, `uncap.s`, `uncap.co`, and `csep`; their complete records matched the
records selected during fitting.

## Automatic-projection misses

3 distinct projected `automatic_complete` Lexemes in the two
deterministic proposal samples had no matching public constructor. They are
review findings, not automatically labelled API gaps:

| Lexeme | Lemma | Fit reason | Source slots |
|---|---|---|---|
| L617760 | Tote | unclassified_constructor_mismatch | {"s_pl_acc":["Tote"],"s_pl_dat":["Toten"],"s_pl_gen":["Toten"],"s_pl_nom":["Tote"],"s_sg_acc":["Tote"],"s_sg_dat":["Toten"],"s_sg_gen":["Toten"],"s_sg_nom":["Tote"]} |
| L620155 | Kameruner | unclassified_constructor_mismatch | {"s_pl_acc":["Kameruner"],"s_pl_dat":["Kamerunern"],"s_pl_gen":["Kameruner"],"s_pl_nom":["Kamerunern"],"s_sg_acc":["Kameruner"],"s_sg_dat":["Kameruner"],"s_sg_gen":["Kameruner"],"s_sg_nom":["Kameruner"]} |
| L643955 | Geflüchtete | unclassified_constructor_mismatch | {"s_pl_acc":["Geflüchtete"],"s_pl_dat":["Geflüchteten"],"s_pl_gen":["Geflüchteter"],"s_pl_nom":["Geflüchtete"],"s_sg_acc":["Geflüchtete"],"s_sg_dat":["Geflüchteten"],"s_sg_gen":["Geflüchteten"],"s_sg_nom":["Geflüchtete"]} |

`Tote` and `Geflüchtete` show adjective-like inflection without the source
paradigm marker used by the census quarantine. `Kameruner` combines a
feminine claim with a form table requiring source review. The accepted-entry
module excluded all three via the fit requirement.

## Measurements

The fitting-gate row is the 5,000-candidate workload. Accepted-entry
selection is shown separately because it probes the reserve pool needed to
obtain exactly 5,000 fitted automatic entries; neither row is the resulting
dictionary approximation.

| Proposal workload | Primary wall s | Repeat wall s | Primary probe s | Repeat probe s | Peak RSS KiB (P/R) |
|---|---|---|---|---|---|
| 5,000-candidate fitting gate | 4.29 | 4.31 | 0.91 | 0.94 | 75764 / 79804 |
| 5,200-candidate accepted selection | 6.47 | 6.44 | 1.29 | 1.28 | 101840 / 102716 |

| 5,000-entry result stage | Primary | Repeat | Frozen limit |
|---|---|---|---|
| Clean GF build wall seconds | 0.63 | 0.62 | 600.0 |
| Structured probe wall seconds | 0.18 | 0.18 | 300.0 |
| Incremental GF build wall seconds | 0.09 | 0.09 | 90.0 |
| Peak RSS KiB | 102916 | 93876 | 2097152 |
| GF source bytes | 430220 | 430220 | 33554432 |
| .gfo bytes | 2231193 | 2231191 | 134217728 |
| .pgf bytes | 1137603 | 1137603 | 134217728 |

All frozen checks passed in both runs. The combined competing-proposal
workload used 10.76 / 10.75 seconds, at most
102716 KiB RSS, and at most
166870077 disposable bytes,
including accepted-entry selection.

## Repeat verification

The primary and repeat semantic summaries are byte-identical at `b14f1bb1a42f7b031e44c1abec5fa3284fcdb400cd638268ec5c80943c61fe10`.
Candidate and reserve selection, all generated GF source, proposal
manifests, structured probe TSVs, PGFs, fitted results, selected records,
and this compact semantic report match byte-for-byte. The result hashes are:

| Artifact | SHA-256 |
|---|---|
| Selected-entry TSV | b736552fb97b406588b69f5b5513b0b7bad10caaf44006ca1e34d28e56ef8ae1 |
| Result concrete GF | 01b3191729278a1ca74a66182feff2e87fee410b2b11a3239a00fcb67f1d9a2f |
| Result PGF | 31e3143560304b207e1fb2ccf05a05a022350b0250291ddc5b2973bf7380a561 |
| Result probe TSV | 4f738dce9dd5b1b74c2d998026c9483f5e154d633f098d83f3e22013f9e04efa |
| Complete result records | 03ddad4bfa785054970a17eeb482a226f9912b0cb768fb1d6160e7e69e088bd3 |

`.gfo` bytes embed their disposable run-directory paths, so their primary
and repeat sizes differ by two bytes; they are ignored intermediates, not a
semantic repeat artifact. Their downstream PGFs are byte-identical.

## Gate assessment

Proceeding to the 25,000 engineering scale point is justified by the wide
performance margins, deterministic selection and output, and successful
complete-record checks. It still requires explicit authorization and must
retain fit-based exclusion and review of projection misses. This gate does
not resolve the much larger linguistic risks recorded by the census:
source conflicts and incompleteness, unresolved multi-gender Lexemes, sparse
combining-form evidence, and overwhelmingly unresolved internal structure.
It is not a decision to generate or place a canonical dictionary.

The 25,000 gate was not run.
