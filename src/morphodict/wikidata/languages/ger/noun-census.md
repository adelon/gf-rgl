# German full-population noun census

This deterministic census classifies the complete exact-`Q188` noun
population without compiling GF. It projects eligibility under the frozen
Phase 3 policy; it does not claim that an unprobed proposal fits.

- Snapshot dump date: `2026-07-29`
- Snapshot SHA-256: `ff02d6805f4b4d97d51091caa45ce12371b0ce543c33909c8c96a6b17c22b937`
- Noun candidates: `188942`
- Census detail SHA-256: `526a34af000af0ef739d75e922f4accbe685205583e2023292dabaa5aaf4f688` (48113280 local bytes)
- Scale selection seed: `wikidata-20260729-german-noun-scale-v1`
- GF compilations performed: `0`

## Acceptance thresholds

| Tier | Frozen definition |
|---|---|
| automatic_complete | complete required case-number evidence; exactly one effective gender; no blocker; every available source field must still be reproduced by GF |
| automatic_complete_with_co | complete required case-number evidence; exactly one effective gender; no blocker; one Q107614077 combining value or a listed reviewed productive rule |
| excluded | source conflict, unsupported feature, unresolved alternative, category mismatch, phrasal item, or residual API gap |
| review_required_provisional | source-compatible proposal requiring missing inflectional, gender, or unlisted combining-form inference; GF probing remains mandatory |

No implicit `ParadigmsGer.mkCompoundForm` rule is reviewed at this gate.
Only a single `Q107614077` Form supplies unrestricted atomic `N.co`
evidence; `P5548` remains construction-specific and unlisted derived values
remain provisional.

## Projected acceptance tiers

| Class | Candidates |
|---|---|
| automatic_complete | 124563 |
| automatic_complete_with_co | 312 |
| excluded | 43996 |
| review_required_provisional | 20071 |

## Source completeness

| Class | Candidates |
|---|---|
| complete | 130474 |
| conflicting | 32609 |
| none | 10273 |
| partial | 15586 |

## Gender and number evidence

Gender status:

| Class | Candidates |
|---|---|
| missing | 6703 |
| multiple | 2445 |
| single | 179794 |

Number restrictions:

| Class | Candidates |
|---|---|
| ordinary | 187200 |
| plural_only | 1221 |
| singular_only | 521 |

Multi-gender correlation evidence:

| Class | Candidates |
|---|---|
| no_recorded_correlation | 2444 |
| not_multiple | 186497 |
| partial_sense_correlation | 1 |

Available correlation sources:

| Class | Candidates |
|---|---|
| effective_multi_gender_lexemes | 2445 |
| with_form_level_gender_statements | 0 |
| with_gender_marked_forms | 0 |
| with_gender_statement_sense_qualifiers | 1 |
| with_sense_level_gender_statements | 0 |

The split policy requires complete, owned, non-overlapping sense
correlations for every effective gender and assignable morphology. Partial
or absent correlations remain unresolved; no Cartesian split is projected.

## Ambiguity and quarantine

Exclusive exclusion reasons:

| Class | Candidates |
|---|---|
| ambiguous_multiple_combining_forms | 3 |
| category_mismatch_adjectival_declension | 28 |
| conflicting_source_slots | 32601 |
| forms_conflict_with_number_restriction | 22 |
| multiword_outside_atomic_noun_pilot | 437 |
| residual_api_gap_singular_only | 382 |
| source_evidence_gap_missing_de_lemma | 1 |
| source_evidence_gap_missing_required_forms | 9334 |
| unresolved_multiple_gender_alternatives | 1179 |
| unsupported_form_feature | 9 |

Overlapping ambiguity/diagnostic signals:

| Class | Candidates |
|---|---|
| conflicting_slots | 32609 |
| forms_conflict_with_number_restriction | 23 |
| missing_de_lemma | 1 |
| missing_gender | 6703 |
| multiple_combining_forms | 5 |
| multiple_gender_alternatives | 2445 |
| non_slot_form_bundle | 57 |
| none_recorded | 149394 |
| rejected_noun_form_feature | 10 |
| unknown_gender_claim | 2 |

## Compound-form confidence

| Class | Candidates |
|---|---|
| construction_specific_p5548_only | 19 |
| provisional_unlisted_derived | 188553 |
| source_atomic_multiple_ambiguous | 5 |
| source_atomic_single | 365 |

## Placement-neutral structural evidence

Exclusive structural cohorts:

| Class | Candidates |
|---|---|
| likely_composition | 2660 |
| opaque_accepted_lexeme | 136806 |
| opaque_unresolved_lexeme | 382 |
| phrasal_or_category_mismatch | 465 |
| source_analysed_composition | 5480 |
| structurally_rejected | 43149 |

Recorded source evidence (overlapping signals):

| Class | Candidates |
|---|---|
| atomic_combining_form | 370 |
| construction_specific_p5548 | 184 |
| hyphen_orthography | 3896 |
| internal_structure_unresolved | 182246 |
| source_component_analysis | 6696 |
| used_as_component_target | 3966 |

Structural evidence record states:

| Class | Candidates |
|---|---|
| component_target | 3530 |
| explicit_compound_analysis | 6260 |
| none_recorded | 178716 |
| source_and_target | 436 |

Candidates without a usable source component analysis are counted as
`internal_structure_unresolved`, never as atomic. Current `ger` and
`ger-fixes` placement was not consulted.

Acceptance tier by structural cohort:

| Acceptance tier | Structural cohort | Candidates |
|---|---|---|
| automatic_complete | likely_composition | 2269 |
| automatic_complete | opaque_accepted_lexeme | 117261 |
| automatic_complete | source_analysed_composition | 5033 |
| automatic_complete_with_co | likely_composition | 2 |
| automatic_complete_with_co | opaque_accepted_lexeme | 277 |
| automatic_complete_with_co | source_analysed_composition | 33 |
| excluded | opaque_unresolved_lexeme | 382 |
| excluded | phrasal_or_category_mismatch | 465 |
| excluded | structurally_rejected | 43149 |
| review_required_provisional | likely_composition | 389 |
| review_required_provisional | opaque_accepted_lexeme | 19268 |
| review_required_provisional | source_analysed_composition | 414 |

## Orthography and paradigm evidence

Orthography flags are overlapping:

| Class | Candidates |
|---|---|
| abbreviation | 273 |
| digit | 166 |
| hyphen | 3896 |
| none | 184331 |
| whitespace | 459 |

Effective noun paradigm-class bundles:

| Class | Candidates |
|---|---|
| Q124328315 | 5 |
| Q124328316 | 6 |
| Q124328317 | 16 |
| Q124328317+Q124328320 | 1 |
| Q124328318 | 23 |
| Q124328320 | 101 |
| Q124328321 | 49 |
| adjectival_declension | 28 |
| genitive_es_invariant_plural | 946 |
| genitive_es_plural_s | 194 |
| n_declension | 361 |
| n_declension_genitive_s | 46 |
| none_recorded | 186451 |
| plural_en | 611 |
| plural_en+plural_s | 1 |
| plural_s | 32 |
| plural_umlaut_e | 70 |
| plural_umlaut_e+Q124328321 | 1 |
