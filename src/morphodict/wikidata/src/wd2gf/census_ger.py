"""Deterministic, compile-free census of the full German noun population."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from enum import StrEnum
from itertools import chain
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from wd2gf.nouns_ger import (
    ADJECTIVAL_DECLENSION_QID,
    DEFAULT_NOUN_POLICY,
    Gender,
    NounArtifact,
    NounCandidate,
    NounError,
    NounPolicy,
    NumberRestriction,
    SourceCompleteness,
    StructuralEvidence,
    _connect,
    _write_bytes,
    iter_noun_candidates,
    load_noun_policy,
    proposal_blocker,
)
from wd2gf.profile_ger import (
    DEFAULT_FEATURE_POLICY,
    FeaturePolicy,
    load_feature_policy,
    load_store_metadata,
)
from wd2gf.store import DEFAULT_DATABASE, canonical_json


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_NOUN_CENSUS = PROJECT_ROOT / "languages/ger/noun-census.md"
DEFAULT_CENSUS_DETAILS = PROJECT_ROOT / ".work/census/noun-census.tsv"


class AcceptanceTier(StrEnum):
    AUTOMATIC_COMPLETE_WITH_CO = "automatic_complete_with_co"
    AUTOMATIC_COMPLETE = "automatic_complete"
    REVIEW_REQUIRED_PROVISIONAL = "review_required_provisional"
    EXCLUDED = "excluded"


class StructuralCohort(StrEnum):
    SOURCE_ANALYSED_COMPOSITION = "source_analysed_composition"
    LIKELY_COMPOSITION = "likely_composition"
    OPAQUE_ACCEPTED_LEXEME = "opaque_accepted_lexeme"
    OPAQUE_UNRESOLVED_LEXEME = "opaque_unresolved_lexeme"
    PHRASAL_OR_CATEGORY_MISMATCH = "phrasal_or_category_mismatch"
    STRUCTURALLY_REJECTED = "structurally_rejected"


class CompoundConfidence(StrEnum):
    SOURCE_ATOMIC_SINGLE = "source_atomic_single"
    SOURCE_ATOMIC_MULTIPLE = "source_atomic_multiple_ambiguous"
    CONSTRUCTION_SPECIFIC_ONLY = "construction_specific_p5548_only"
    PROVISIONAL_DERIVED = "provisional_unlisted_derived"


class GenderCorrelation(StrEnum):
    NOT_MULTIPLE = "not_multiple"
    NONE = "no_recorded_correlation"
    PARTIAL_SENSE = "partial_sense_correlation"
    INVALID_SENSE = "invalid_or_overlapping_sense_correlation"
    COMPLETE_SHARED_FORMS = "complete_sense_correlation_shared_forms"
    COMPLETE_GENDER_FORMS = "complete_sense_and_form_correlation"
    INCOMPLETE_GENDER_FORMS = "complete_sense_incomplete_form_correlation"
    FORM_ONLY = "form_gender_correlation_without_complete_senses"


@dataclass(frozen=True)
class CensusClassification:
    acceptance_tier: AcceptanceTier
    exclusion_reason: str
    compound_confidence: CompoundConfidence
    structural_cohort: StructuralCohort
    gender_correlation: GenderCorrelation


@dataclass(frozen=True)
class CensusRun:
    report: NounArtifact
    details: NounArtifact
    total_candidates: int
    tier_counts: dict[str, int]


_GENDER_QIDS = {
    Gender.MASCULINE: "Q499327",
    Gender.FEMININE: "Q1775415",
    Gender.NEUTER: "Q1775461",
}


def _sense_qualifiers(
    connection: sqlite3.Connection, property_id: str
) -> tuple[dict[int, tuple[str, ...]], dict[str, str]]:
    by_statement: dict[int, list[str]] = defaultdict(list)
    identifiers: set[str] = set()
    rows = connection.execute(
        "SELECT q.statement_rowid, q.value_json FROM qualifier q "
        "JOIN statement s USING(statement_rowid) "
        "WHERE s.subject_kind = 'lexeme' AND s.property_id = 'P5185' "
        "AND q.property_id = ? ORDER BY q.statement_rowid, q.position",
        (property_id,),
    )
    for statement_rowid, value_json in rows:
        value = json.loads(value_json) if value_json is not None else None
        sense_id = value.get("id") if isinstance(value, dict) else None
        if isinstance(sense_id, str):
            by_statement[int(statement_rowid)].append(sense_id)
            identifiers.add(sense_id)
    owners: dict[str, str] = {}
    ordered = sorted(identifiers)
    for offset in range(0, len(ordered), 500):
        batch = ordered[offset : offset + 500]
        placeholders = ",".join("?" for _ in batch)
        owners.update(
            connection.execute(
                f"SELECT sense_id, lexeme_id FROM sense "
                f"WHERE sense_id IN ({placeholders})",
                tuple(batch),
            ).fetchall()
        )
    return (
        {key: tuple(values) for key, values in by_statement.items()},
        owners,
    )


def _multi_gender_source_counts(
    connection: sqlite3.Connection,
    gender_property: str,
    noun_qid: str,
    sense_correlation_property: str,
    form_gender_features: Sequence[str],
) -> Counter[str]:
    connection.execute(
        "CREATE TEMP TABLE phase3_multi_gender "
        "(lexeme_id TEXT PRIMARY KEY) WITHOUT ROWID"
    )
    connection.execute(
        """
        INSERT INTO phase3_multi_gender
        WITH effective AS (
          SELECT s.subject_id, s.value_qid
          FROM statement s JOIN lexeme l ON l.lexeme_id = s.subject_id
          WHERE s.subject_kind = 'lexeme' AND l.lexical_category_qid = ?
            AND s.property_id = ? AND s.rank != 'deprecated'
            AND (s.rank = 'preferred' OR NOT EXISTS (
              SELECT 1 FROM statement p
              WHERE p.subject_kind = 'lexeme' AND p.subject_id = s.subject_id
                AND p.property_id = s.property_id AND p.rank = 'preferred'
            ))
        )
        SELECT subject_id FROM effective
        GROUP BY subject_id HAVING COUNT(DISTINCT value_qid) > 1
        """,
        (noun_qid, gender_property),
    )
    placeholders = ",".join("?" for _ in form_gender_features)
    counts = Counter()
    counts["effective_multi_gender_lexemes"] = int(
        connection.execute("SELECT COUNT(*) FROM phase3_multi_gender").fetchone()[0]
    )
    counts["with_gender_marked_forms"] = int(
        connection.execute(
            f"SELECT COUNT(DISTINCT f.lexeme_id) FROM form_feature ff "
            f"JOIN form f USING(form_id) JOIN phase3_multi_gender m "
            f"ON m.lexeme_id = f.lexeme_id "
            f"WHERE ff.feature_qid IN ({placeholders})",
            tuple(form_gender_features),
        ).fetchone()[0]
    )
    counts["with_form_level_gender_statements"] = int(
        connection.execute(
            "SELECT COUNT(DISTINCT f.lexeme_id) FROM statement s "
            "JOIN form f ON f.form_id = s.subject_id "
            "JOIN phase3_multi_gender m ON m.lexeme_id = f.lexeme_id "
            "WHERE s.subject_kind = 'form' AND s.property_id = ? "
            "AND s.rank != 'deprecated'",
            (gender_property,),
        ).fetchone()[0]
    )
    counts["with_sense_level_gender_statements"] = int(
        connection.execute(
            "SELECT COUNT(DISTINCT se.lexeme_id) FROM statement s "
            "JOIN sense se ON se.sense_id = s.subject_id "
            "JOIN phase3_multi_gender m ON m.lexeme_id = se.lexeme_id "
            "WHERE s.subject_kind = 'sense' AND s.property_id = ? "
            "AND s.rank != 'deprecated'",
            (gender_property,),
        ).fetchone()[0]
    )
    counts["with_gender_statement_sense_qualifiers"] = int(
        connection.execute(
            "SELECT COUNT(DISTINCT s.subject_id) FROM qualifier q "
            "JOIN statement s USING(statement_rowid) "
            "JOIN phase3_multi_gender m ON m.lexeme_id = s.subject_id "
            "WHERE s.subject_kind = 'lexeme' AND s.property_id = ? "
            "AND s.rank != 'deprecated' AND q.property_id = ?",
            (gender_property, sense_correlation_property),
        ).fetchone()[0]
    )
    return counts


def gender_correlation(
    candidate: NounCandidate,
    qualifiers: Mapping[int, Sequence[str]],
    sense_owners: Mapping[str, str],
    form_gender_features: Sequence[str],
) -> GenderCorrelation:
    if len(candidate.genders) <= 1:
        return GenderCorrelation.NOT_MULTIPLE
    claim_senses: dict[Gender, set[str]] = defaultdict(set)
    every_claim_correlated = True
    invalid_owner = False
    qid_to_gender = {value: key for key, value in _GENDER_QIDS.items()}
    for claim in candidate.gender_claims:
        gender = qid_to_gender.get(claim.value_id)
        if gender is None:
            continue
        senses = tuple(qualifiers.get(claim.statement_rowid, ()))
        if not senses:
            every_claim_correlated = False
        for sense_id in senses:
            if sense_owners.get(sense_id) != candidate.source_key:
                invalid_owner = True
            else:
                claim_senses[gender].add(sense_id)
    marked_form_genders = {
        feature
        for slot in candidate.slots
        for form in slot.forms
        for feature in form.features
        if feature in form_gender_features
    }
    any_sense = any(claim_senses.values())
    if invalid_owner:
        return GenderCorrelation.INVALID_SENSE
    complete_senses = every_claim_correlated and all(
        claim_senses.get(gender) for gender in candidate.genders
    )
    if complete_senses:
        sense_sets = [claim_senses[gender] for gender in candidate.genders]
        if any(
            left & right
            for index, left in enumerate(sense_sets)
            for right in sense_sets[index + 1 :]
        ):
            return GenderCorrelation.INVALID_SENSE
        expected_form_genders = {_GENDER_QIDS[gender] for gender in candidate.genders}
        if not marked_form_genders:
            return GenderCorrelation.COMPLETE_SHARED_FORMS
        if marked_form_genders == expected_form_genders:
            return GenderCorrelation.COMPLETE_GENDER_FORMS
        return GenderCorrelation.INCOMPLETE_GENDER_FORMS
    if any_sense:
        return GenderCorrelation.PARTIAL_SENSE
    if marked_form_genders:
        return GenderCorrelation.FORM_ONLY
    return GenderCorrelation.NONE


def _compound_confidence(candidate: NounCandidate) -> CompoundConfidence:
    values = {form.value for form in candidate.combining_forms}
    if len(values) == 1:
        return CompoundConfidence.SOURCE_ATOMIC_SINGLE
    if len(values) > 1:
        return CompoundConfidence.SOURCE_ATOMIC_MULTIPLE
    if candidate.object_form_evidence:
        return CompoundConfidence.CONSTRUCTION_SPECIFIC_ONLY
    return CompoundConfidence.PROVISIONAL_DERIVED


def _is_adjectival(candidate: NounCandidate) -> bool:
    return any(
        claim.value_id == ADJECTIVAL_DECLENSION_QID
        for claim in candidate.paradigm_claims
    )


def _acceptance(
    candidate: NounCandidate,
    correlation: GenderCorrelation,
    compound_confidence: CompoundConfidence,
) -> tuple[AcceptanceTier, str]:
    if _is_adjectival(candidate):
        return AcceptanceTier.EXCLUDED, "category_mismatch_adjectival_declension"
    blocker = proposal_blocker(candidate)
    if blocker is not None:
        if (
            blocker == "unresolved_multiple_gender_alternatives"
            and correlation
            in {
                GenderCorrelation.COMPLETE_SHARED_FORMS,
                GenderCorrelation.COMPLETE_GENDER_FORMS,
            }
        ):
            return AcceptanceTier.EXCLUDED, "correlated_split_requires_followup"
        return AcceptanceTier.EXCLUDED, blocker
    if candidate.source_completeness is SourceCompleteness.NONE:
        return AcceptanceTier.EXCLUDED, "source_evidence_gap_missing_required_forms"
    if (
        candidate.source_completeness is SourceCompleteness.COMPLETE
        and len(candidate.genders) == 1
    ):
        if compound_confidence is CompoundConfidence.SOURCE_ATOMIC_SINGLE:
            return AcceptanceTier.AUTOMATIC_COMPLETE_WITH_CO, ""
        return AcceptanceTier.AUTOMATIC_COMPLETE, ""
    return AcceptanceTier.REVIEW_REQUIRED_PROVISIONAL, ""


def _structural_cohort(
    candidate: NounCandidate,
    tier: AcceptanceTier,
    exclusion_reason: str,
) -> StructuralCohort:
    if exclusion_reason in {
        "category_mismatch_adjectival_declension",
        "multiword_outside_atomic_noun_pilot",
    }:
        return StructuralCohort.PHRASAL_OR_CATEGORY_MISMATCH
    if exclusion_reason in {
        "residual_api_gap_singular_only",
        "correlated_split_requires_followup",
    }:
        return StructuralCohort.OPAQUE_UNRESOLVED_LEXEME
    if tier is AcceptanceTier.EXCLUDED:
        return StructuralCohort.STRUCTURALLY_REJECTED
    if candidate.compound_statement_keys:
        return StructuralCohort.SOURCE_ANALYSED_COMPOSITION
    if "hyphen" in candidate.orthography:
        return StructuralCohort.LIKELY_COMPOSITION
    return StructuralCohort.OPAQUE_ACCEPTED_LEXEME


def classify_candidate(
    candidate: NounCandidate,
    qualifiers: Mapping[int, Sequence[str]],
    sense_owners: Mapping[str, str],
    noun_policy: NounPolicy,
) -> CensusClassification:
    correlation = gender_correlation(
        candidate,
        qualifiers,
        sense_owners,
        noun_policy.form_gender_features,
    )
    confidence = _compound_confidence(candidate)
    tier, exclusion_reason = _acceptance(candidate, correlation, confidence)
    cohort = _structural_cohort(candidate, tier, exclusion_reason)
    return CensusClassification(tier, exclusion_reason, confidence, cohort, correlation)


def _table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> list[str]:
    rendered = [[str(value).replace("|", "\\|") for value in row] for row in rows]
    return [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
        *("| " + " | ".join(row) + " |" for row in rendered),
    ]


def _counter_table(counter: Counter[str]) -> list[str]:
    return _table(
        ("Class", "Candidates"),
        ((key, counter[key]) for key in sorted(counter)),
    )


def _details_header() -> tuple[str, ...]:
    return (
        "internal_id",
        "source_key",
        "entity_sha256_json",
        "lemma_json",
        "acceptance_tier",
        "exclusion_reason",
        "source_completeness",
        "genders_json",
        "gender_correlation",
        "number_restriction",
        "paradigm_classes_json",
        "orthography_json",
        "compound_confidence",
        "structural_evidence",
        "structural_cohort",
        "diagnostics_json",
    )


def _detail_row(
    index: int,
    candidate: NounCandidate,
    classification: CensusClassification,
) -> tuple[str, ...]:
    return (
        f"wdc_{index:06d}_N",
        candidate.source_key,
        canonical_json(list(candidate.entity_sha256)),
        canonical_json(candidate.lemma),
        classification.acceptance_tier.value,
        classification.exclusion_reason,
        candidate.source_completeness.value,
        canonical_json([gender.value for gender in candidate.genders]),
        classification.gender_correlation.value,
        candidate.number_restriction.value,
        canonical_json(sorted({claim.value_id for claim in candidate.paradigm_claims})),
        canonical_json(list(candidate.orthography)),
        classification.compound_confidence.value,
        candidate.structural_evidence.value,
        classification.structural_cohort.value,
        canonical_json(list(candidate.diagnostics)),
    )


def _write_detail_stream(
    path: Path,
    rows: Iterable[Sequence[str]],
) -> NounArtifact:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    digest = hashlib.sha256()
    size = 0
    try:
        with os.fdopen(descriptor, "wb") as output:
            for row in chain((_details_header(),), rows):
                if any(character in field for field in row for character in "\t\r\n"):
                    raise NounError("noun census detail escaped its TSV cell")
                content = ("\t".join(row) + "\n").encode("utf-8")
                output.write(content)
                digest.update(content)
                size += len(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise
    return NounArtifact(path, digest.hexdigest(), size)


def _report_bytes(
    *,
    snapshot: Mapping[str, object],
    noun_policy: NounPolicy,
    total: int,
    counters: Mapping[str, Counter[str]],
    tier_cohort: Counter[tuple[str, str]],
    details: NounArtifact,
) -> bytes:
    lines = [
        "# German full-population noun census",
        "",
        "This deterministic census classifies the complete exact-`Q188` noun",
        "population without compiling GF. It projects eligibility under the frozen",
        "Phase 3 policy; it does not claim that an unprobed proposal fits.",
        "",
        f"- Snapshot dump date: `{snapshot.get('dump_date')}`",
        f"- Snapshot SHA-256: `{snapshot.get('sha256')}`",
        f"- Noun candidates: `{total}`",
        f"- Census detail SHA-256: `{details.sha256}` ({details.size_bytes} local bytes)",
        f"- Scale selection seed: `{noun_policy.scale_seed}`",
        "- GF compilations performed: `0`",
        "",
        "## Acceptance thresholds",
        "",
        *_table(
            ("Tier", "Frozen definition"),
            ((key, noun_policy.acceptance_tiers[key]) for key in sorted(noun_policy.acceptance_tiers)),
        ),
        "",
        "No implicit `ParadigmsGer.mkCompoundForm` rule is reviewed at this gate.",
        "Only a single `Q107614077` Form supplies unrestricted atomic `N.co`",
        "evidence; `P5548` remains construction-specific and unlisted derived values",
        "remain provisional.",
        "",
        "## Projected acceptance tiers",
        "",
        *_counter_table(counters["acceptance"]),
        "",
        "## Source completeness",
        "",
        *_counter_table(counters["source_completeness"]),
        "",
        "## Gender and number evidence",
        "",
        "Gender status:",
        "",
        *_counter_table(counters["gender_status"]),
        "",
        "Number restrictions:",
        "",
        *_counter_table(counters["number_restriction"]),
        "",
        "Multi-gender correlation evidence:",
        "",
        *_counter_table(counters["gender_correlation"]),
        "",
        "Available correlation sources:",
        "",
        *_counter_table(counters["gender_correlation_source"]),
        "",
        "The split policy requires complete, owned, non-overlapping sense",
        "correlations for every effective gender and assignable morphology. Partial",
        "or absent correlations remain unresolved; no Cartesian split is projected.",
        "",
        "## Ambiguity and quarantine",
        "",
        "Exclusive exclusion reasons:",
        "",
        *_counter_table(counters["exclusion_reason"]),
        "",
        "Overlapping ambiguity/diagnostic signals:",
        "",
        *_counter_table(counters["ambiguity"]),
        "",
        "## Compound-form confidence",
        "",
        *_counter_table(counters["compound_confidence"]),
        "",
        "## Placement-neutral structural evidence",
        "",
        "Exclusive structural cohorts:",
        "",
        *_counter_table(counters["structural_cohort"]),
        "",
        "Recorded source evidence (overlapping signals):",
        "",
        *_counter_table(counters["structural_signal"]),
        "",
        "Structural evidence record states:",
        "",
        *_counter_table(counters["structural_evidence"]),
        "",
        "Candidates without a usable source component analysis are counted as",
        "`internal_structure_unresolved`, never as atomic. Current `ger` and",
        "`ger-fixes` placement was not consulted.",
        "",
        "Acceptance tier by structural cohort:",
        "",
        *_table(
            ("Acceptance tier", "Structural cohort", "Candidates"),
            (
                (tier, cohort, count)
                for (tier, cohort), count in sorted(tier_cohort.items())
            ),
        ),
        "",
        "## Orthography and paradigm evidence",
        "",
        "Orthography flags are overlapping:",
        "",
        *_counter_table(counters["orthography"]),
        "",
        "Effective noun paradigm-class bundles:",
        "",
        *_counter_table(counters["paradigm_class"]),
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def generate_noun_census(
    *,
    database_path: Path = DEFAULT_DATABASE,
    noun_policy_path: Path = DEFAULT_NOUN_POLICY,
    feature_policy_path: Path = DEFAULT_FEATURE_POLICY,
    report_path: Path = DEFAULT_NOUN_CENSUS,
    details_path: Path = DEFAULT_CENSUS_DETAILS,
    expected_snapshot: Mapping[str, object] | None = None,
) -> CensusRun:
    noun_policy = load_noun_policy(noun_policy_path)
    if noun_policy.reviewed_productive_co_rules:
        raise NounError("reviewed productive co rules require an implemented matcher")
    feature_policy: FeaturePolicy = load_feature_policy(feature_policy_path)
    connection = _connect(database_path)
    try:
        metadata = load_store_metadata(connection)
        snapshot = metadata.get("snapshot")
        if not isinstance(snapshot, dict):
            raise NounError("source database has no snapshot metadata")
        if expected_snapshot is not None and snapshot != dict(expected_snapshot):
            raise NounError("source database snapshot does not match the verified lock")
        qualifiers, sense_owners = _sense_qualifiers(
            connection, noun_policy.sense_correlation_property
        )
        counters: dict[str, Counter[str]] = defaultdict(Counter)
        gender_property = next(
            key
            for key, value in feature_policy.properties.items()
            if value == "grammatical_gender"
        )
        noun_qid = next(
            key for key, value in feature_policy.lexical_categories.items() if value == "N"
        )
        counters["gender_correlation_source"].update(
            _multi_gender_source_counts(
                connection,
                gender_property,
                noun_qid,
                noun_policy.sense_correlation_property,
                noun_policy.form_gender_features,
            )
        )
        tier_cohort: Counter[tuple[str, str]] = Counter()
        total = 0

        def detail_rows():
            nonlocal total
            for index, candidate in enumerate(
                iter_noun_candidates(connection, feature_policy), start=1
            ):
                total = index
                classification = classify_candidate(
                    candidate, qualifiers, sense_owners, noun_policy
                )
                counters["acceptance"][classification.acceptance_tier.value] += 1
                counters["source_completeness"][candidate.source_completeness.value] += 1
                gender_status = (
                    "missing"
                    if not candidate.genders
                    else "single"
                    if len(candidate.genders) == 1
                    else "multiple"
                )
                counters["gender_status"][gender_status] += 1
                counters["number_restriction"][candidate.number_restriction.value] += 1
                counters["gender_correlation"][classification.gender_correlation.value] += 1
                counters["compound_confidence"][classification.compound_confidence.value] += 1
                counters["structural_cohort"][classification.structural_cohort.value] += 1
                counters["structural_evidence"][candidate.structural_evidence.value] += 1
                tier_cohort[
                    (
                        classification.acceptance_tier.value,
                        classification.structural_cohort.value,
                    )
                ] += 1
                if classification.exclusion_reason:
                    counters["exclusion_reason"][classification.exclusion_reason] += 1
                paradigm_values = sorted(
                    {claim.value_id for claim in candidate.paradigm_claims}
                )
                labels = [
                    feature_policy.statement_values.get(value, value)
                    for value in paradigm_values
                ]
                counters["paradigm_class"]["+".join(labels) or "none_recorded"] += 1
                for flag in candidate.orthography or ("none",):
                    counters["orthography"][flag] += 1
                ambiguity_signals = set(candidate.diagnostics)
                if len(candidate.genders) > 1:
                    ambiguity_signals.add("multiple_gender_alternatives")
                if len({form.value for form in candidate.combining_forms}) > 1:
                    ambiguity_signals.add("multiple_combining_forms")
                for signal in sorted(ambiguity_signals or {"none_recorded"}):
                    counters["ambiguity"][signal] += 1
                if candidate.compound_statement_keys:
                    counters["structural_signal"]["source_component_analysis"] += 1
                else:
                    counters["structural_signal"]["internal_structure_unresolved"] += 1
                if candidate.structural_evidence in {
                    StructuralEvidence.COMPONENT_TARGET,
                    StructuralEvidence.SOURCE_AND_TARGET,
                }:
                    counters["structural_signal"]["used_as_component_target"] += 1
                if candidate.combining_forms:
                    counters["structural_signal"]["atomic_combining_form"] += 1
                if candidate.object_form_evidence:
                    counters["structural_signal"]["construction_specific_p5548"] += 1
                if "hyphen" in candidate.orthography:
                    counters["structural_signal"]["hyphen_orthography"] += 1
                yield _detail_row(index, candidate, classification)

        details = _write_detail_stream(details_path, detail_rows())
        report = _write_bytes(
            report_path,
            _report_bytes(
                snapshot=snapshot,
                noun_policy=noun_policy,
                total=total,
                counters=counters,
                tier_cohort=tier_cohort,
                details=details,
            ),
        )
        return CensusRun(report, details, total, dict(counters["acceptance"]))
    finally:
        connection.close()
