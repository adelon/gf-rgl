# Interpreted German Wikidata Lexeme profile

This interpretation applies only the reviewed mappings in `features.toml`
to the semantically lossless source store. Counts are source evidence, not
claims of linguistic correctness or acceptance into a GF dictionary.

## Provenance and deterministic boundary

- Snapshot date: `2026-07-29`
- Snapshot SHA-256: `ff02d6805f4b4d97d51091caa45ce12371b0ce543c33909c8c96a6b17c22b937`
- Exact entity-language selector: `Q188`
- Selected Lexemes: 241967
- Historical German dictionaries used as inventory inputs: no
- Normalization of retained source strings: none

## Initial category coverage

| Category | Lexemes | With `de` lemma | Profile-usable evidence |
|---|---|---|---|
| N | 188942 | 188941 | 125859 |
| V | 20422 | 20422 | 1179 |
| A | 26862 | 26862 | 2054 |
| Adv | 2656 | 2656 | 2656 |

Profile-usable is category-specific and deliberately stricter than merely
having a form: nouns need complete expected case/number slots and reviewed
gender evidence; verbs need four principal-part signals and a recognized
auxiliary; adjectives need three predicative degrees or an explicitly
absolute positive; adverbs need a `de` lemma.

## Noun source coverage

| Metric | Lexemes |
|---|---|
| complete_slots | 160566 |
| conflicting_slots | 32609 |
| exact_duplicate_slots | 14 |
| no_de_form_representations | 10193 |
| no_slots | 10267 |
| partial_slots | 18109 |
| rejected_feature | 10 |
| source_usable_single_gender | 125319 |
| source_usable_split_gender | 540 |
| total | 188942 |
| without_de_lemma | 1 |

Gender evidence status:

| Status | Lexemes |
|---|---|
| missing | 6701 |
| multiple | 2448 |
| single | 179791 |
| unknown_or_novalue | 2 |

Number-restriction status:

| Status | Lexemes |
|---|---|
| ordinary | 187200 |
| plural_only | 1221 |
| singular_only | 521 |

Non-deprecated gender statement values:

| Value | Statements | Lexemes |
|---|---|---|
| feminine | 79671 | 79671 |
| masculine | 66107 | 66107 |
| neuter | 38977 | 38977 |
| novalue/somevalue | 1 | 1 |
| Q1305037 | 1 | 1 |

Non-deprecated `instance of` values on nouns (mapped values name number restrictions):

| Value | Statements | Lexemes |
|---|---|---|
| Q61366396 | 1451 | 1451 |
| plurale_tantum | 1221 | 1221 |
| singulare_tantum | 521 | 521 |
| Q63870920 | 58 | 58 |
| Q117448639 | 37 | 37 |
| Q3109261 | 37 | 37 |
| Q245423 | 25 | 25 |
| Q208674 | 23 | 23 |
| Q4455897 | 23 | 23 |
| Q107627504 | 18 | 18 |
| Q116003388 | 17 | 17 |
| Q3920971 | 16 | 16 |
| Q100552658 | 11 | 11 |
| Q12321 | 10 | 10 |
| Q217438 | 10 | 10 |
| Q54440109 | 10 | 10 |
| Q102786 | 8 | 8 |
| Q7189808 | 8 | 8 |
| Q7884789 | 7 | 7 |
| Q108709 | 5 | 5 |
| Q1520033 | 5 | 5 |
| Q489168 | 4 | 4 |
| Q103808 | 3 | 3 |
| Q9788 | 3 | 3 |
| Q101244 | 2 | 2 |
| Q111048186 | 2 | 2 |
| Q112263731 | 2 | 2 |
| Q1137656 | 2 | 2 |
| Q181970 | 2 | 2 |
| Q2253185 | 2 | 2 |

Noun paradigm-class evidence:

| Value | Statements | Lexemes |
|---|---|---|
| genitive_es_invariant_plural | 947 | 946 |
| plural_en | 613 | 612 |
| n_declension | 362 | 361 |
| genitive_es_plural_s | 194 | 194 |
| Q124328320 | 102 | 102 |
| plural_umlaut_e | 71 | 71 |
| Q124328321 | 50 | 50 |
| n_declension_genitive_s | 46 | 46 |
| plural_s | 34 | 33 |
| adjectival_declension | 28 | 28 |
| Q124328318 | 23 | 23 |
| Q124328317 | 17 | 17 |
| Q124328316 | 6 | 6 |
| Q124328315 | 5 | 5 |

Across all categories, source slots contain:

- 1943161 Lexeme/tag/feature-bundle slots
- 346 exact duplicate slots
- 79341 conflicting-value slots

## Combining-form and compound evidence

Combining-form representations:

| Tag | Representations | Forms | Lexemes | Distinct strings |
|---|---|---|---|---|
| de | 378 | 378 | 372 | 376 |

- `P5238` statements: 15026
- Source Lexemes with compound evidence: 7717
- Sources with multiple component statements: 6896
- Distinct component targets: 4987
- Targets resolved inside the exact-Q188 store: 4971
- Unresolved or malformed target statements: 24
- `P1545` ordering qualifiers: 6147
- `P5548` qualifiers: 526
- `P5548` targets resolved to stored Forms: 526
- Unresolved/malformed `P5548` targets: 0

Combining forms and construction-specific object-form qualifiers remain
separate evidence. Missing statements are not interpreted as atomicity.

## Verb evidence

Form coverage:

| Metric | Lexemes |
|---|---|
| principal_parts_complete | 18664 |
| source_usable_with_auxiliary | 1179 |
| total | 20422 |
| with_de_lemma | 20422 |
| with_infinitive | 19116 |
| with_past_participle | 18669 |
| with_present_3sg | 18784 |
| with_preterite_3sg | 18832 |

Auxiliary evidence:

| Status | Lexemes |
|---|---|
| both | 108 |
| haben | 1176 |
| missing | 19027 |
| sein | 111 |

Separability evidence:

| Status | Lexemes |
|---|---|
| inseparable | 664 |
| separable | 639 |
| unrecorded | 19119 |

## Adjective and adverb evidence

Adjectives:

| Metric | Lexemes |
|---|---|
| absolute_positive_only | 38 |
| absolute_statements | 47 |
| all_degrees_predicative | 2016 |
| indeclinable_statements | 200 |
| source_usable | 2054 |
| total | 26862 |
| with_comparative_predicative | 2043 |
| with_de_lemma | 26862 |
| with_positive_predicative | 24225 |
| with_superlative_predicative | 2026 |

Adverbs:

| Metric | Lexemes |
|---|---|
| source_usable | 2656 |
| total | 2656 |
| with_de_form | 2656 |
| with_de_lemma | 2656 |

These categories are profiled only; fitting remains deferred.

## Spelling profiles

| Category | `de` lemmas | Whitespace | Hyphen | Digit | All uppercase | Non-NFC |
|---|---|---|---|---|---|---|
| A | 26862 | 810 | 247 | 90 | 1 | 0 |
| Adv | 2656 | 109 | 15 | 4 | 0 | 0 |
| N | 188941 | 459 | 3896 | 166 | 289 | 0 |
| V | 20422 | 421 | 14 | 0 | 0 | 0 |

Strings are counted without rewriting or filtering them.

## Ranks, correlations, and duplicate signals

Ranks on projected morphology and compound properties:

| Property | Rank | Statements |
|---|---|---|
| P31 | normal | 11459 |
| P5185 | deprecated | 1 |
| P5185 | normal | 185880 |
| P5185 | preferred | 4 |
| P5187 | normal | 2167 |
| P5238 | deprecated | 2 |
| P5238 | normal | 15018 |
| P5238 | preferred | 6 |
| P5401 | normal | 1521 |
| P5911 | normal | 2503 |

Sense-specific statements on those properties:

| Property | Sense statements |
|---|---|
| P31 | 35 |
| P5401 | 17 |

Duplicate `de` lemma signals (diagnostic only; no merge is performed):

| Category | Duplicate groups | Lexemes in groups |
|---|---|---|
| A | 4 | 8 |
| Adv | 4 | 8 |
| N | 281 | 586 |
| V | 53 | 108 |

## Rejection and quarantine accounting

- Entities rejected as malformed during full ingestion: 0
- Entities excluded by exact language selection: 1294634
- Nouns without a `de` lemma: 1
- Nouns with partial slots: 18109
- Nouns with no recognized standalone slots: 10267
- Nouns with conflicting slots: 32609
- Nouns with rejected rare form features: 10
- Nouns with a number-restriction conflict: 0
- Nouns missing gender evidence: 6701
- Nouns with multiple gender values: 2448
- Nouns with unknown/novalue gender evidence: 2
- Rejected noun-feature assignments: 50
- Deferred unknown feature assignments outside noun fitting: 2084

Every noun-category form feature in this snapshot is either mapped or
explicitly rejected in `features.toml`; an unclassified noun feature is a
hard profile error. `unknown-features.tsv` retains the rejected/deferred
inventory. No source record is silently repaired or accepted.
