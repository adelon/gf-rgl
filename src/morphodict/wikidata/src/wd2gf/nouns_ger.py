"""German noun candidates and deterministic Phase 2 sampling."""

from __future__ import annotations

import hashlib
import heapq
import json
import os
import sqlite3
import tempfile
import tomllib
import unicodedata
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

from wd2gf.profile_ger import (
    DEFAULT_FEATURE_POLICY,
    FeaturePolicy,
    load_feature_policy,
    load_store_metadata,
)
from wd2gf.store import DEFAULT_DATABASE, SCHEMA_VERSION, canonical_json


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_NOUN_POLICY = PROJECT_ROOT / "languages/ger/noun-policy.toml"
DEFAULT_NOUN_SAMPLE = PROJECT_ROOT / "languages/ger/noun-sample.tsv"
DEFAULT_NOUN_WORK = PROJECT_ROOT / ".work/nouns"


class NounError(RuntimeError):
    """The German noun pilot contract was violated."""


class Gender(StrEnum):
    MASCULINE = "masculine"
    FEMININE = "feminine"
    NEUTER = "neuter"


class NumberRestriction(StrEnum):
    ORDINARY = "ordinary"
    PLURAL_ONLY = "plural_only"
    SINGULAR_ONLY = "singular_only"
    CONFLICTING = "conflicting"


class SourceCompleteness(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    NONE = "none"
    CONFLICTING = "conflicting"


class StructuralEvidence(StrEnum):
    NONE_RECORDED = "none_recorded"
    COMPONENT_TARGET = "component_target"
    EXPLICIT_COMPOUND_ANALYSIS = "explicit_compound_analysis"
    SOURCE_AND_TARGET = "source_and_target"


SLOT_FIELDS = (
    "s_sg_nom",
    "s_sg_acc",
    "s_sg_dat",
    "s_sg_gen",
    "s_pl_nom",
    "s_pl_acc",
    "s_pl_dat",
    "s_pl_gen",
)

STRATA = (
    "regular_masculine",
    "regular_feminine",
    "regular_neuter",
    "invariant",
    "invariant_plural",
    "plural_only",
    "singular_only",
    "abbreviation",
    "hyphenated",
    "explicit_combining",
    "ambiguous_combining",
    "irregular_full",
    "partial_evidence",
    "multiple_gender",
    "conflicting_slots",
    "rejected_feature",
    "restriction_conflict",
    "multiword",
    "unknown_gender",
)

CONSTRUCTOR_ORDER = (
    "mkN_lemma",
    "mkN_lemma_gender",
    "invarN_one",
    "invarPlN_one",
    "invarN_two",
    "invarPlN_two",
    "mkN_two",
    "changeCompoundN",
    "mkN_three",
    "mkN_six",
    "pluralOnlyN",
    "abbrevN",
)

PROBE_FIELDS = (
    *SLOT_FIELDS,
    "gender",
    "co",
    "uncap_s_sg_nom",
    "uncap_s_sg_acc",
    "uncap_s_sg_dat",
    "uncap_s_sg_gen",
    "uncap_s_pl_nom",
    "uncap_s_pl_acc",
    "uncap_s_pl_dat",
    "uncap_s_pl_gen",
    "uncap_co",
    "csep",
)

ADJECTIVAL_DECLENSION_QID = "Q103383087"


@dataclass(frozen=True)
class ClaimEvidence:
    statement_rowid: int
    statement_key: str
    rank: str
    value_id: str


@dataclass(frozen=True)
class FormEvidence:
    form_id: str
    value: str
    features: tuple[str, ...]


@dataclass(frozen=True)
class SlotEvidence:
    field: str
    forms: tuple[FormEvidence, ...]

    @property
    def values(self) -> tuple[str, ...]:
        return tuple(sorted({form.value for form in self.forms}))


@dataclass(frozen=True)
class NounCandidate:
    source_key: str
    lexeme_ids: tuple[str, ...]
    entity_sha256: tuple[str, ...]
    lemma: str | None
    genders: tuple[Gender, ...]
    gender_claims: tuple[ClaimEvidence, ...]
    number_restriction: NumberRestriction
    restriction_claims: tuple[ClaimEvidence, ...]
    paradigm_claims: tuple[ClaimEvidence, ...]
    slots: tuple[SlotEvidence, ...]
    combining_forms: tuple[FormEvidence, ...]
    object_form_evidence: tuple[str, ...]
    compound_statement_keys: tuple[str, ...]
    sense_statement_keys: tuple[str, ...]
    source_completeness: SourceCompleteness
    structural_evidence: StructuralEvidence
    orthography: tuple[str, ...]
    diagnostics: tuple[str, ...]
    stratum: str


@dataclass(frozen=True)
class SampledCandidate:
    internal_id: str
    score: str
    pinned: bool
    candidate: NounCandidate


@dataclass(frozen=True)
class NounPolicy:
    reference: str
    sample_seed: str
    scale_seed: str
    rank_policy: str
    review_status: str
    singular_only_policy: str
    combining_form_policy: str
    constructor_order: tuple[str, ...]
    pinned_lexemes: tuple[str, ...]
    quotas: dict[str, int]
    acceptance_tiers: dict[str, str]
    atomic_co_feature: str
    construction_specific_co_property: str
    reviewed_productive_co_rules: tuple[str, ...]
    unlisted_derived_co_policy: str
    co_inference_rationale: str
    sense_correlation_property: str
    form_gender_features: tuple[str, ...]
    multi_gender_split_requirements: tuple[str, ...]
    uncorrelated_multi_gender_policy: str


@dataclass(frozen=True)
class NounArtifact:
    path: Path
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class MkNLemma:
    lemma: str


@dataclass(frozen=True)
class MkNLemmaGender:
    lemma: str
    gender: Gender


@dataclass(frozen=True)
class InvarNOne:
    form: str
    gender: Gender


@dataclass(frozen=True)
class InvarNTwo:
    singular: str
    plural: str
    gender: Gender


@dataclass(frozen=True)
class InvarPlNOne:
    form: str
    gender: Gender


@dataclass(frozen=True)
class InvarPlNTwo:
    singular: str
    plural: str
    gender: Gender


@dataclass(frozen=True)
class MkNTwo:
    singular: str
    plural: str
    gender: Gender


@dataclass(frozen=True)
class MkNThree:
    singular: str
    plural: str
    combining: str
    gender: Gender


@dataclass(frozen=True)
class MkNSix:
    singular_nom: str
    singular_acc: str
    singular_dat: str
    singular_gen: str
    plural_nom: str
    plural_dat: str
    gender: Gender


@dataclass(frozen=True)
class PluralOnlyN:
    plural: str


BaseProposal = (
    MkNLemma
    | MkNLemmaGender
    | InvarNOne
    | InvarNTwo
    | InvarPlNOne
    | InvarPlNTwo
    | MkNTwo
    | MkNThree
    | MkNSix
    | PluralOnlyN
)


@dataclass(frozen=True)
class ChangeCompoundN:
    combining: str
    base: BaseProposal


@dataclass(frozen=True)
class AbbrevN:
    base: BaseProposal | ChangeCompoundN


NounProposal = BaseProposal | ChangeCompoundN | AbbrevN


@dataclass(frozen=True)
class ProposalOption:
    candidate_id: str
    option_id: str
    function_id: str
    constructor: str
    explicit_form_arguments: int
    expression: str
    proposal: NounProposal


@dataclass(frozen=True)
class _CandidateIds:
    gender_property: str
    instance_property: str
    paradigm_property: str
    compound_property: str
    gender_ids: dict[str, Gender]
    plural_only_id: str
    singular_only_id: str
    number_ids: dict[str, str]
    case_ids: dict[str, str]
    form_gender_ids: frozenset[str]
    combining_id: str
    rejected_features: frozenset[str]


def _candidate_ids(policy: FeaturePolicy) -> _CandidateIds:
    return _CandidateIds(
        gender_property=_one_id(policy.properties, "grammatical_gender"),
        instance_property=_one_id(policy.properties, "instance_of"),
        paradigm_property=_one_id(policy.properties, "paradigm_class"),
        compound_property=_one_id(policy.properties, "combines_lexemes"),
        gender_ids={
            _one_id(policy.statement_values, "masculine"): Gender.MASCULINE,
            _one_id(policy.statement_values, "feminine"): Gender.FEMININE,
            _one_id(policy.statement_values, "neuter"): Gender.NEUTER,
        },
        plural_only_id=_one_id(policy.statement_values, "plurale_tantum"),
        singular_only_id=_one_id(policy.statement_values, "singulare_tantum"),
        number_ids={
            _one_id(policy.form_features, "singular"): "sg",
            _one_id(policy.form_features, "plural"): "pl",
        },
        case_ids={
            _one_id(policy.form_features, "nominative"): "nom",
            _one_id(policy.form_features, "accusative"): "acc",
            _one_id(policy.form_features, "dative"): "dat",
            _one_id(policy.form_features, "genitive"): "gen",
        },
        form_gender_ids=frozenset(
            {
                _one_id(policy.form_features, "masculine"),
                _one_id(policy.form_features, "feminine"),
                _one_id(policy.form_features, "neuter"),
            }
        ),
        combining_id=_one_id(policy.form_features, "combining_form"),
        rejected_features=frozenset(policy.rejected_noun_form_features),
    )


def load_noun_policy(path: Path = DEFAULT_NOUN_POLICY) -> NounPolicy:
    try:
        with path.open("rb") as policy_file:
            data = tomllib.load(policy_file)
    except FileNotFoundError as error:
        raise NounError(f"noun policy does not exist: {path}") from error
    expected = {
        "schema_version",
        "reference",
        "sample_seed",
        "scale_seed",
        "rank_policy",
        "review_status",
        "singular_only_policy",
        "combining_form_policy",
        "constructor_order",
        "pinned_lexemes",
        "quotas",
        "acceptance_tiers",
        "compound_form_inference",
        "multi_gender",
    }
    if set(data) != expected or data["schema_version"] != 2:
        raise NounError("unsupported noun policy schema")
    if data["rank_policy"] != "preferred-over-normal; deprecated excluded":
        raise NounError("unsupported noun statement-rank policy")
    if data["review_status"] != "automatic":
        raise NounError("initial noun review status must be automatic")
    if data["singular_only_policy"] != "residual-api-gap":
        raise NounError("singular-only policy must preserve the public-API gap")
    constructor_order = data["constructor_order"]
    if constructor_order != list(CONSTRUCTOR_ORDER):
        raise NounError("noun constructor order does not match the closed proposal set")
    pinned = data["pinned_lexemes"]
    if not isinstance(pinned, list) or any(
        not isinstance(identifier, str) or not identifier.startswith("L")
        for identifier in pinned
    ):
        raise NounError("pinned_lexemes must be a list of Lexeme IDs")
    if len(set(pinned)) != len(pinned):
        raise NounError("pinned_lexemes contains duplicates")
    quotas = data["quotas"]
    if not isinstance(quotas, dict) or set(quotas) != set(STRATA):
        raise NounError("noun quotas must name the complete frozen stratum set")
    if any(not isinstance(value, int) or value < 0 for value in quotas.values()):
        raise NounError("noun quotas must be nonnegative integers")
    scalar_fields = (
        "reference",
        "sample_seed",
        "scale_seed",
        "rank_policy",
        "review_status",
        "singular_only_policy",
        "combining_form_policy",
    )
    if any(not isinstance(data[field], str) or not data[field] for field in scalar_fields):
        raise NounError("noun policy scalar fields must be nonempty strings")
    acceptance_tiers = data["acceptance_tiers"]
    expected_tiers = {
        "automatic_complete_with_co",
        "automatic_complete",
        "review_required_provisional",
        "excluded",
    }
    if (
        not isinstance(acceptance_tiers, dict)
        or set(acceptance_tiers) != expected_tiers
        or any(
            not isinstance(value, str) or not value
            for value in acceptance_tiers.values()
        )
    ):
        raise NounError("acceptance_tiers must define the four frozen thresholds")
    co_policy = data["compound_form_inference"]
    if set(co_policy) != {
        "atomic_source_feature",
        "construction_specific_property",
        "reviewed_productive_rules",
        "unlisted_derived_value",
        "rationale",
    }:
        raise NounError("compound_form_inference does not match its frozen schema")
    reviewed_rules = co_policy["reviewed_productive_rules"]
    if not isinstance(reviewed_rules, list) or any(
        not isinstance(rule, str) or not rule for rule in reviewed_rules
    ):
        raise NounError("reviewed_productive_rules must be a list of rule names")
    if co_policy["unlisted_derived_value"] != "provisional":
        raise NounError("unlisted derived compound forms must remain provisional")
    multi_gender = data["multi_gender"]
    if set(multi_gender) != {
        "sense_correlation_property",
        "form_gender_features",
        "split_requirements",
        "uncorrelated_policy",
    }:
        raise NounError("multi_gender does not match its frozen schema")
    form_gender_features = multi_gender["form_gender_features"]
    split_requirements = multi_gender["split_requirements"]
    if not isinstance(form_gender_features, list) or any(
        not isinstance(value, str) or not value for value in form_gender_features
    ):
        raise NounError("form_gender_features must be a list of QIDs")
    if not isinstance(split_requirements, list) or any(
        not isinstance(value, str) or not value for value in split_requirements
    ):
        raise NounError("multi-gender split requirements must be nonempty strings")
    if multi_gender["uncorrelated_policy"] != "reject-unresolved":
        raise NounError("uncorrelated multi-gender candidates must remain unresolved")
    return NounPolicy(
        reference=data["reference"],
        sample_seed=data["sample_seed"],
        scale_seed=data["scale_seed"],
        rank_policy=data["rank_policy"],
        review_status=data["review_status"],
        singular_only_policy=data["singular_only_policy"],
        combining_form_policy=data["combining_form_policy"],
        constructor_order=tuple(constructor_order),
        pinned_lexemes=tuple(pinned),
        quotas=dict(quotas),
        acceptance_tiers=dict(acceptance_tiers),
        atomic_co_feature=co_policy["atomic_source_feature"],
        construction_specific_co_property=co_policy[
            "construction_specific_property"
        ],
        reviewed_productive_co_rules=tuple(reviewed_rules),
        unlisted_derived_co_policy=co_policy["unlisted_derived_value"],
        co_inference_rationale=co_policy["rationale"],
        sense_correlation_property=multi_gender["sense_correlation_property"],
        form_gender_features=tuple(form_gender_features),
        multi_gender_split_requirements=tuple(split_requirements),
        uncorrelated_multi_gender_policy=multi_gender["uncorrelated_policy"],
    )


def _one_id(mapping: Mapping[str, str], label: str) -> str:
    matches = [identifier for identifier, value in mapping.items() if value == label]
    if len(matches) != 1:
        raise NounError(f"feature policy must map exactly one ID to {label!r}")
    return matches[0]


def _connect(database_path: Path) -> sqlite3.Connection:
    if not database_path.is_file():
        raise NounError(f"source database does not exist: {database_path}")
    connection = sqlite3.connect(f"file:{database_path}?mode=ro", uri=True)
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    if version != SCHEMA_VERSION:
        connection.close()
        raise NounError(
            f"incompatible source database schema {version}; expected {SCHEMA_VERSION}"
        )
    return connection


def _value_identifier(value_qid: str | None, value_json: str | None, snaktype: str) -> str:
    if value_qid is not None:
        return value_qid
    value = json.loads(value_json) if value_json is not None else None
    if isinstance(value, dict) and isinstance(value.get("id"), str):
        return value["id"]
    return f"snaktype:{snaktype}"


def _claim_maps(
    connection: sqlite3.Connection,
    noun_qid: str,
    properties: Sequence[str],
) -> dict[str, dict[str, list[ClaimEvidence]]]:
    placeholders = ",".join("?" for _ in properties)
    result: dict[str, dict[str, list[ClaimEvidence]]] = {}
    rows = connection.execute(
        f"""
        SELECT s.subject_id, s.property_id, s.statement_rowid, s.position,
               s.statement_id, s.rank, s.snaktype, s.value_qid, s.value_json
        FROM statement s JOIN lexeme l ON l.lexeme_id = s.subject_id
        WHERE s.subject_kind = 'lexeme' AND l.lexical_category_qid = ?
          AND s.property_id IN ({placeholders})
        ORDER BY s.subject_id, s.property_id, s.position, s.statement_rowid
        """,
        (noun_qid, *properties),
    )
    for (
        lexeme_id,
        property_id,
        statement_rowid,
        position,
        statement_id,
        rank,
        snaktype,
        value_qid,
        value_json,
    ) in rows:
        statement_key = statement_id or f"{lexeme_id}:{property_id}:{position}"
        evidence = ClaimEvidence(
            statement_rowid=int(statement_rowid),
            statement_key=statement_key,
            rank=rank,
            value_id=_value_identifier(value_qid, value_json, snaktype),
        )
        result.setdefault(lexeme_id, {}).setdefault(property_id, []).append(evidence)
    return result


def _effective_claims(claims: Iterable[ClaimEvidence]) -> tuple[ClaimEvidence, ...]:
    current = tuple(claim for claim in claims if claim.rank != "deprecated")
    preferred = tuple(claim for claim in current if claim.rank == "preferred")
    return preferred or tuple(claim for claim in current if claim.rank == "normal")


FORM_QUERY = """
WITH ordered_features AS (
  SELECT form_id, feature_qid
  FROM form_feature
  ORDER BY form_id, position, feature_qid
),
bundles AS (
  SELECT form_id, group_concat(feature_qid, '|') AS feature_bundle
  FROM ordered_features
  GROUP BY form_id
)
SELECT f.lexeme_id, f.form_id, r.value, COALESCE(b.feature_bundle, '')
FROM form f JOIN lexeme l USING(lexeme_id)
JOIN form_representation r USING(form_id)
LEFT JOIN bundles b USING(form_id)
WHERE l.lexical_category_qid = ? AND r.language_tag = 'de'
ORDER BY f.lexeme_id, f.position, f.form_id
"""


def _iter_forms(
    connection: sqlite3.Connection, noun_qid: str
) -> Iterator[tuple[str, tuple[FormEvidence, ...]]]:
    current_id: str | None = None
    forms: list[FormEvidence] = []
    for lexeme_id, form_id, value, feature_bundle in connection.execute(
        FORM_QUERY, (noun_qid,)
    ):
        if current_id is not None and lexeme_id != current_id:
            yield current_id, tuple(forms)
            forms = []
        current_id = lexeme_id
        features = tuple(feature_bundle.split("|")) if feature_bundle else ()
        forms.append(FormEvidence(form_id, value, features))
    if current_id is not None:
        yield current_id, tuple(forms)


def _sense_statement_map(
    connection: sqlite3.Connection, properties: Sequence[str]
) -> dict[str, tuple[str, ...]]:
    placeholders = ",".join("?" for _ in properties)
    result: dict[str, list[str]] = {}
    rows = connection.execute(
        f"""
        SELECT se.lexeme_id, s.subject_id, s.property_id, s.position, s.statement_id
        FROM statement s JOIN sense se ON se.sense_id = s.subject_id
        WHERE s.subject_kind = 'sense' AND s.property_id IN ({placeholders})
          AND s.rank != 'deprecated'
        ORDER BY se.lexeme_id, s.subject_id, s.property_id, s.position
        """,
        tuple(properties),
    )
    for lexeme_id, subject_id, property_id, position, statement_id in rows:
        result.setdefault(lexeme_id, []).append(
            statement_id or f"{subject_id}:{property_id}:{position}"
        )
    return {key: tuple(values) for key, values in result.items()}


def _compound_indexes(
    connection: sqlite3.Connection,
    compound_property: str,
    object_form_property: str,
) -> tuple[dict[str, tuple[str, ...]], dict[str, tuple[str, ...]]]:
    claims_by_source: dict[str, list[ClaimEvidence]] = {}
    rows = connection.execute(
        """
        SELECT subject_id, statement_rowid, position, statement_id, rank,
               snaktype, value_qid, value_json
        FROM statement
        WHERE subject_kind = 'lexeme' AND property_id = ?
        ORDER BY subject_id, position, statement_rowid
        """,
        (compound_property,),
    )
    for (
        subject_id,
        statement_rowid,
        position,
        statement_id,
        rank,
        snaktype,
        value_qid,
        value_json,
    ) in rows:
        claims_by_source.setdefault(subject_id, []).append(
            ClaimEvidence(
                statement_rowid=int(statement_rowid),
                statement_key=statement_id
                or f"{subject_id}:{compound_property}:{position}",
                rank=rank,
                value_id=_value_identifier(value_qid, value_json, snaktype),
            )
        )
    effective_by_rowid: dict[int, ClaimEvidence] = {}
    targets: dict[str, list[str]] = {}
    for claims in claims_by_source.values():
        for claim in _effective_claims(claims):
            effective_by_rowid[claim.statement_rowid] = claim
            if claim.value_id.startswith("L"):
                targets.setdefault(claim.value_id, []).append(claim.statement_key)

    object_forms: dict[str, list[str]] = {}
    rows = connection.execute(
        "SELECT q.statement_rowid, q.value_json FROM qualifier q "
        "WHERE q.property_id = ? ORDER BY q.statement_rowid, q.position",
        (object_form_property,),
    )
    pending: list[tuple[ClaimEvidence, str]] = []
    form_ids: set[str] = set()
    for statement_rowid, value_json in rows:
        claim = effective_by_rowid.get(statement_rowid)
        value = json.loads(value_json) if value_json is not None else None
        form_id = value.get("id") if isinstance(value, dict) else None
        if claim is not None and isinstance(form_id, str):
            pending.append((claim, form_id))
            form_ids.add(form_id)
    owners: dict[str, str] = {}
    if form_ids:
        identifiers = sorted(form_ids)
        for offset in range(0, len(identifiers), 500):
            batch = identifiers[offset : offset + 500]
            placeholders = ",".join("?" for _ in batch)
            owners.update(
                connection.execute(
                    f"SELECT form_id, lexeme_id FROM form WHERE form_id IN ({placeholders})",
                    tuple(batch),
                ).fetchall()
            )
    for claim, form_id in pending:
        target_id = claim.value_id
        if owners.get(form_id) == target_id:
            object_forms.setdefault(target_id, []).append(
                f"{claim.statement_key}>{form_id}"
            )
    return (
        {key: tuple(sorted(values)) for key, values in targets.items()},
        {key: tuple(sorted(values)) for key, values in object_forms.items()},
    )


def _orthography(value: str | None) -> tuple[str, ...]:
    if value is None:
        return ()
    flags: list[str] = []
    if any(character.isspace() for character in value):
        flags.append("whitespace")
    if any(character in "-‐‑‒–—" for character in value):
        flags.append("hyphen")
    if any(character.isdigit() for character in value):
        flags.append("digit")
    cased = [character for character in value if character.lower() != character.upper()]
    if len(cased) >= 2 and all(character == character.upper() for character in cased):
        flags.append("abbreviation")
    if unicodedata.normalize("NFC", value) != value:
        flags.append("non_nfc")
    return tuple(flags)


def _slot_field(number: str, case: str) -> str:
    return f"s_{number}_{case}"


def _source_completeness(
    restriction: NumberRestriction,
    slots: Mapping[str, SlotEvidence],
) -> tuple[SourceCompleteness, tuple[str, ...]]:
    diagnostics: list[str] = []
    if restriction is NumberRestriction.CONFLICTING:
        return SourceCompleteness.CONFLICTING, ("conflicting_number_restrictions",)
    if restriction is NumberRestriction.PLURAL_ONLY:
        expected = {field for field in SLOT_FIELDS if field.startswith("s_pl_")}
        forbidden = {field for field in slots if field.startswith("s_sg_")}
    elif restriction is NumberRestriction.SINGULAR_ONLY:
        expected = {field for field in SLOT_FIELDS if field.startswith("s_sg_")}
        forbidden = {field for field in slots if field.startswith("s_pl_")}
    else:
        expected = set(SLOT_FIELDS)
        forbidden = set()
    if forbidden:
        diagnostics.append("forms_conflict_with_number_restriction")
    if any(len(evidence.values) > 1 for evidence in slots.values()):
        return SourceCompleteness.CONFLICTING, tuple(diagnostics + ["conflicting_slots"])
    present = set(slots)
    if expected <= present and not forbidden:
        return SourceCompleteness.COMPLETE, tuple(diagnostics)
    if expected & present:
        return SourceCompleteness.PARTIAL, tuple(diagnostics)
    return SourceCompleteness.NONE, tuple(diagnostics)


def _single_slot_values(slots: Sequence[SlotEvidence]) -> dict[str, str]:
    return {
        slot.field: slot.values[0]
        for slot in slots
        if len(slot.values) == 1
    }


def _stratum(candidate: NounCandidate) -> str:
    diagnostics = set(candidate.diagnostics)
    if diagnostics & {
        "rejected_noun_form_feature",
        "unclassified_noun_form_feature",
    }:
        return "rejected_feature"
    if candidate.number_restriction is NumberRestriction.CONFLICTING:
        return "restriction_conflict"
    if candidate.source_completeness is SourceCompleteness.CONFLICTING:
        return "conflicting_slots"
    if len(candidate.genders) > 1:
        return "multiple_gender"
    if "whitespace" in candidate.orthography:
        return "multiword"
    if candidate.number_restriction is NumberRestriction.SINGULAR_ONLY:
        return "singular_only"
    if candidate.number_restriction is NumberRestriction.PLURAL_ONLY:
        return "plural_only"
    combining_values = {form.value for form in candidate.combining_forms}
    if len(combining_values) > 1:
        return "ambiguous_combining"
    if combining_values:
        return "explicit_combining"
    if "abbreviation" in candidate.orthography:
        return "abbreviation"
    if "hyphen" in candidate.orthography:
        return "hyphenated"
    if candidate.source_completeness is not SourceCompleteness.COMPLETE:
        return "partial_evidence"
    values = _single_slot_values(candidate.slots)
    singular = [values.get(f"s_sg_{case}") for case in ("nom", "acc", "dat", "gen")]
    plural = [values.get(f"s_pl_{case}") for case in ("nom", "acc", "dat", "gen")]
    if len(set(singular)) == 1 and len(set(plural)) == 1:
        return "invariant"
    if len(set(singular[:3])) == 1 and len(set(plural)) == 1:
        return "invariant_plural"
    if singular[1] != singular[0] or singular[2] != singular[0]:
        return "irregular_full"
    if plural[1] != plural[0] or plural[3] != plural[0]:
        return "irregular_full"
    if len(candidate.genders) != 1:
        return "unknown_gender"
    return f"regular_{candidate.genders[0].value}"


def _candidate(
    *,
    lexeme_id: str,
    entity_sha256: str,
    lemma: str | None,
    forms: Sequence[FormEvidence],
    claims: Mapping[str, list[ClaimEvidence]],
    sense_statement_keys: tuple[str, ...],
    component_statement_keys: tuple[str, ...],
    object_form_evidence: tuple[str, ...],
    ids: _CandidateIds,
) -> NounCandidate:
    diagnostics: list[str] = []
    gender_claims = _effective_claims(claims.get(ids.gender_property, []))
    genders = tuple(
        sorted(
            {
                ids.gender_ids[claim.value_id]
                for claim in gender_claims
                if claim.value_id in ids.gender_ids
            },
            key=lambda gender: gender.value,
        )
    )
    if any(claim.value_id not in ids.gender_ids for claim in gender_claims):
        diagnostics.append("unknown_gender_claim")

    instance_claims = _effective_claims(claims.get(ids.instance_property, []))
    restriction_claims = tuple(
        claim
        for claim in instance_claims
        if claim.value_id in {ids.plural_only_id, ids.singular_only_id}
    )
    restriction_values = {claim.value_id for claim in restriction_claims}
    if restriction_values == {ids.plural_only_id}:
        restriction = NumberRestriction.PLURAL_ONLY
    elif restriction_values == {ids.singular_only_id}:
        restriction = NumberRestriction.SINGULAR_ONLY
    elif restriction_values == {ids.plural_only_id, ids.singular_only_id}:
        restriction = NumberRestriction.CONFLICTING
    else:
        restriction = NumberRestriction.ORDINARY

    slot_forms: dict[str, list[FormEvidence]] = {}
    combining_forms: list[FormEvidence] = []
    known_features = (
        set(ids.number_ids)
        | set(ids.case_ids)
        | set(ids.form_gender_ids)
        | {ids.combining_id}
    )
    for form in forms:
        features = set(form.features)
        if features & ids.rejected_features:
            diagnostics.append("rejected_noun_form_feature")
        if features - known_features - ids.rejected_features:
            diagnostics.append("unclassified_noun_form_feature")
        if ids.combining_id in features:
            combining_forms.append(form)
            continue
        numbers = features & set(ids.number_ids)
        cases = features & set(ids.case_ids)
        if len(numbers) == 1 and len(cases) == 1:
            field = _slot_field(
                ids.number_ids[next(iter(numbers))],
                ids.case_ids[next(iter(cases))],
            )
            slot_forms.setdefault(field, []).append(form)
        elif features:
            diagnostics.append("non_slot_form_bundle")
    slots = tuple(
        SlotEvidence(field, tuple(sorted(slot_forms[field], key=lambda form: form.form_id)))
        for field in SLOT_FIELDS
        if field in slot_forms
    )
    completeness, completeness_diagnostics = _source_completeness(
        restriction, {slot.field: slot for slot in slots}
    )
    diagnostics.extend(completeness_diagnostics)
    if lemma is None:
        diagnostics.append("missing_de_lemma")
    if not genders:
        diagnostics.append("missing_gender")
    if len({form.value for form in combining_forms}) > 1:
        diagnostics.append("multiple_combining_forms")

    own_compounds = _effective_claims(claims.get(ids.compound_property, []))
    if own_compounds and component_statement_keys:
        structural = StructuralEvidence.SOURCE_AND_TARGET
    elif own_compounds:
        structural = StructuralEvidence.EXPLICIT_COMPOUND_ANALYSIS
    elif component_statement_keys:
        structural = StructuralEvidence.COMPONENT_TARGET
    else:
        structural = StructuralEvidence.NONE_RECORDED

    draft = NounCandidate(
        source_key=lexeme_id,
        lexeme_ids=(lexeme_id,),
        entity_sha256=(entity_sha256,),
        lemma=lemma,
        genders=genders,
        gender_claims=gender_claims,
        number_restriction=restriction,
        restriction_claims=restriction_claims,
        paradigm_claims=_effective_claims(claims.get(ids.paradigm_property, [])),
        slots=slots,
        combining_forms=tuple(sorted(combining_forms, key=lambda form: form.form_id)),
        object_form_evidence=object_form_evidence,
        compound_statement_keys=tuple(claim.statement_key for claim in own_compounds),
        sense_statement_keys=sense_statement_keys,
        source_completeness=completeness,
        structural_evidence=structural,
        orthography=_orthography(lemma),
        diagnostics=tuple(sorted(set(diagnostics))),
        stratum="",
    )
    return replace(draft, stratum=_stratum(draft))


def _score(seed: str, source_key: str) -> tuple[int, str]:
    digest = hashlib.sha256(f"{seed}\0{source_key}".encode("utf-8")).hexdigest()
    return int(digest, 16), digest


def _lexeme_sort_key(candidate: NounCandidate) -> tuple[int, str]:
    identifier = candidate.lexeme_ids[0]
    numeric = identifier[1:]
    return (int(numeric) if numeric.isdecimal() else 0, candidate.source_key)


def select_noun_sample(
    connection: sqlite3.Connection,
    noun_policy: NounPolicy,
    feature_policy: FeaturePolicy,
) -> tuple[SampledCandidate, ...]:
    noun_qid = _one_id(feature_policy.lexical_categories, "N")
    ids = _candidate_ids(feature_policy)
    properties = tuple(
        _one_id(feature_policy.properties, label)
        for label in (
            "grammatical_gender",
            "instance_of",
            "paradigm_class",
            "combines_lexemes",
        )
    )
    claim_maps = _claim_maps(connection, noun_qid, properties)
    sense_statements = _sense_statement_map(connection, properties)
    component_targets, object_forms = _compound_indexes(
        connection,
        ids.compound_property,
        _one_id(feature_policy.properties, "object_form"),
    )
    forms_iterator = iter(_iter_forms(connection, noun_qid))
    current_forms = next(forms_iterator, None)
    heaps: dict[str, list[tuple[int, str, NounCandidate]]] = {
        stratum: [] for stratum in STRATA
    }
    pinned_candidates: dict[str, NounCandidate] = {}
    rows = connection.execute(
        "SELECT l.lexeme_id, l.entity_sha256, m.value FROM lexeme l "
        "LEFT JOIN lemma m ON m.lexeme_id = l.lexeme_id AND m.language_tag = 'de' "
        "WHERE l.lexical_category_qid = ? ORDER BY l.lexeme_id",
        (noun_qid,),
    )
    for lexeme_id, entity_sha256, lemma in rows:
        forms: tuple[FormEvidence, ...] = ()
        if current_forms is not None and current_forms[0] == lexeme_id:
            forms = current_forms[1]
            current_forms = next(forms_iterator, None)
        candidate = _candidate(
            lexeme_id=lexeme_id,
            entity_sha256=entity_sha256,
            lemma=lemma,
            forms=forms,
            claims=claim_maps.get(lexeme_id, {}),
            sense_statement_keys=sense_statements.get(lexeme_id, ()),
            component_statement_keys=component_targets.get(lexeme_id, ()),
            object_form_evidence=object_forms.get(lexeme_id, ()),
            ids=ids,
        )
        if lexeme_id in noun_policy.pinned_lexemes:
            pinned_candidates[lexeme_id] = candidate
        quota = noun_policy.quotas[candidate.stratum]
        if quota == 0:
            continue
        numeric_score, _ = _score(noun_policy.sample_seed, candidate.source_key)
        heap = heaps[candidate.stratum]
        item = (-numeric_score, candidate.source_key, candidate)
        if len(heap) < quota:
            heapq.heappush(heap, item)
        elif numeric_score < -heap[0][0]:
            heapq.heapreplace(heap, item)

    missing_pinned = sorted(set(noun_policy.pinned_lexemes) - set(pinned_candidates))
    if missing_pinned:
        raise NounError(f"pinned noun Lexemes are absent: {missing_pinned}")
    selected = {
        item[2].source_key: item[2]
        for heap in heaps.values()
        for item in heap
    }
    selected.update((key, value) for key, value in pinned_candidates.items())
    ordered = sorted(selected.values(), key=_lexeme_sort_key)
    return tuple(
        SampledCandidate(
            internal_id=f"wdn_{index:06d}_N",
            score=_score(noun_policy.sample_seed, candidate.source_key)[1],
            pinned=candidate.source_key in noun_policy.pinned_lexemes,
            candidate=candidate,
        )
        for index, candidate in enumerate(ordered, start=1)
    )


def proposal_blocker(candidate: NounCandidate) -> str | None:
    diagnostics = set(candidate.diagnostics)
    if candidate.lemma is None:
        return "source_evidence_gap_missing_de_lemma"
    if diagnostics & {
        "rejected_noun_form_feature",
        "unclassified_noun_form_feature",
    }:
        return "unsupported_form_feature"
    if candidate.number_restriction is NumberRestriction.CONFLICTING:
        return "conflicting_number_restrictions"
    if candidate.source_completeness is SourceCompleteness.CONFLICTING:
        return "conflicting_source_slots"
    if "forms_conflict_with_number_restriction" in diagnostics:
        return "forms_conflict_with_number_restriction"
    if len(candidate.genders) > 1:
        return "unresolved_multiple_gender_alternatives"
    if "whitespace" in candidate.orthography:
        return "multiword_outside_atomic_noun_pilot"
    if candidate.number_restriction is NumberRestriction.SINGULAR_ONLY:
        return "residual_api_gap_singular_only"
    if len({form.value for form in candidate.combining_forms}) > 1:
        return "ambiguous_multiple_combining_forms"
    return None


def unfitted_candidate_reason(candidate: NounCandidate) -> str:
    """Classify an otherwise unblocked candidate after no proposal fits."""
    if any(
        claim.value_id == ADJECTIVAL_DECLENSION_QID
        for claim in candidate.paradigm_claims
    ):
        return "category_mismatch_adjectival_declension"
    if candidate.source_completeness is SourceCompleteness.NONE:
        return "source_evidence_gap_missing_required_forms"
    if not candidate.genders:
        return "source_evidence_gap_missing_gender"
    return "unclassified_constructor_mismatch"


def _gf_quote(value: str) -> str:
    replacements = {
        "\\": "\\\\",
        '"': '\\"',
        "\n": "\\n",
        "\r": "\\r",
        "\t": "\\t",
    }
    return '"' + "".join(replacements.get(character, character) for character in value) + '"'


def _gf_gender(gender: Gender) -> str:
    return {
        Gender.MASCULINE: "P.masculine",
        Gender.FEMININE: "P.feminine",
        Gender.NEUTER: "P.neuter",
    }[gender]


def proposal_constructor(proposal: NounProposal) -> str:
    match proposal:
        case MkNLemma():
            return "mkN_lemma"
        case MkNLemmaGender():
            return "mkN_lemma_gender"
        case InvarNOne():
            return "invarN_one"
        case InvarNTwo():
            return "invarN_two"
        case InvarPlNOne():
            return "invarPlN_one"
        case InvarPlNTwo():
            return "invarPlN_two"
        case MkNTwo():
            return "mkN_two"
        case MkNThree():
            return "mkN_three"
        case MkNSix():
            return "mkN_six"
        case PluralOnlyN():
            return "pluralOnlyN"
        case ChangeCompoundN(base=base):
            return f"changeCompoundN+{proposal_constructor(base)}"
        case AbbrevN(base=base):
            return f"abbrevN+{proposal_constructor(base)}"
    raise NounError(f"unsupported noun proposal: {proposal!r}")


def proposal_form_arguments(proposal: NounProposal) -> int:
    match proposal:
        case MkNLemma() | MkNLemmaGender() | InvarNOne() | InvarPlNOne() | PluralOnlyN():
            return 1
        case InvarNTwo() | InvarPlNTwo() | MkNTwo():
            return 2
        case MkNThree():
            return 3
        case MkNSix():
            return 6
        case ChangeCompoundN(base=base):
            return 1 + proposal_form_arguments(base)
        case AbbrevN(base=base):
            return proposal_form_arguments(base)
    raise NounError(f"unsupported noun proposal: {proposal!r}")


def render_proposal(proposal: NounProposal) -> str:
    match proposal:
        case MkNLemma(lemma=lemma):
            return f"P.mkN {_gf_quote(lemma)}"
        case MkNLemmaGender(lemma=lemma, gender=gender):
            return f"P.mkN {_gf_quote(lemma)} {_gf_gender(gender)}"
        case InvarNOne(form=form, gender=gender):
            return f"P.invarN {_gf_quote(form)} {_gf_gender(gender)}"
        case InvarNTwo(singular=singular, plural=plural, gender=gender):
            return (
                f"P.invarN {_gf_quote(singular)} {_gf_quote(plural)} "
                f"{_gf_gender(gender)}"
            )
        case InvarPlNOne(form=form, gender=gender):
            return f"P.invarPlN {_gf_quote(form)} {_gf_gender(gender)}"
        case InvarPlNTwo(singular=singular, plural=plural, gender=gender):
            return (
                f"P.invarPlN {_gf_quote(singular)} {_gf_quote(plural)} "
                f"{_gf_gender(gender)}"
            )
        case MkNTwo(singular=singular, plural=plural, gender=gender):
            return (
                f"P.mkN {_gf_quote(singular)} {_gf_quote(plural)} "
                f"{_gf_gender(gender)}"
            )
        case MkNThree(
            singular=singular,
            plural=plural,
            combining=combining,
            gender=gender,
        ):
            return (
                f"P.mkN {_gf_quote(singular)} {_gf_quote(plural)} "
                f"{_gf_quote(combining)} {_gf_gender(gender)}"
            )
        case MkNSix(
            singular_nom=singular_nom,
            singular_acc=singular_acc,
            singular_dat=singular_dat,
            singular_gen=singular_gen,
            plural_nom=plural_nom,
            plural_dat=plural_dat,
            gender=gender,
        ):
            forms = (
                singular_nom,
                singular_acc,
                singular_dat,
                singular_gen,
                plural_nom,
                plural_dat,
            )
            return "P.mkN " + " ".join(
                [*(_gf_quote(form) for form in forms), _gf_gender(gender)]
            )
        case PluralOnlyN(plural=plural):
            return f"P.pluralOnlyN {_gf_quote(plural)}"
        case ChangeCompoundN(combining=combining, base=base):
            return f"P.changeCompoundN {_gf_quote(combining)} ({render_proposal(base)})"
        case AbbrevN(base=base):
            return f"P.abbrevN ({render_proposal(base)})"
    raise NounError(f"unsupported noun proposal: {proposal!r}")


def _base_constructor(proposal: NounProposal) -> str:
    match proposal:
        case ChangeCompoundN(base=base) | AbbrevN(base=base):
            return _base_constructor(base)
        case _:
            return proposal_constructor(proposal)


def _proposal_sort_key(
    proposal: NounProposal, noun_policy: NounPolicy
) -> tuple[int, int, int, str]:
    base = _base_constructor(proposal)
    outer = proposal_constructor(proposal).split("+", 1)[0]
    return (
        proposal_form_arguments(proposal),
        noun_policy.constructor_order.index(base),
        noun_policy.constructor_order.index(outer),
        render_proposal(proposal),
    )


def proposals_for_candidate(
    sampled: SampledCandidate, noun_policy: NounPolicy
) -> tuple[ProposalOption, ...]:
    candidate = sampled.candidate
    if proposal_blocker(candidate) is not None or candidate.lemma is None:
        return ()
    values = _single_slot_values(candidate.slots)
    gender = candidate.genders[0] if len(candidate.genders) == 1 else None
    bases: list[BaseProposal] = []
    if candidate.number_restriction is NumberRestriction.PLURAL_ONLY:
        if "s_pl_nom" in values:
            bases.append(PluralOnlyN(values["s_pl_nom"]))
    else:
        bases.append(MkNLemma(candidate.lemma))
        if gender is not None:
            bases.extend(
                (
                    MkNLemmaGender(candidate.lemma, gender),
                    InvarNOne(candidate.lemma, gender),
                    InvarPlNOne(candidate.lemma, gender),
                )
            )
            if "s_sg_nom" in values and "s_pl_nom" in values:
                singular = values["s_sg_nom"]
                plural = values["s_pl_nom"]
                bases.extend(
                    (
                        InvarNTwo(singular, plural, gender),
                        InvarPlNTwo(singular, plural, gender),
                        MkNTwo(singular, plural, gender),
                    )
                )
            required_six = (
                "s_sg_nom",
                "s_sg_acc",
                "s_sg_dat",
                "s_sg_gen",
                "s_pl_nom",
                "s_pl_dat",
            )
            if all(field in values for field in required_six):
                bases.append(MkNSix(*(values[field] for field in required_six), gender))

    proposals: list[NounProposal] = list(bases)
    combining_values = sorted({form.value for form in candidate.combining_forms})
    if len(combining_values) == 1:
        combining = combining_values[0]
        proposals.extend(ChangeCompoundN(combining, base) for base in bases)
        if (
            gender is not None
            and "s_sg_nom" in values
            and "s_pl_nom" in values
        ):
            proposals.append(
                MkNThree(values["s_sg_nom"], values["s_pl_nom"], combining, gender)
            )
    if "abbreviation" in candidate.orthography:
        proposals = [AbbrevN(proposal) for proposal in proposals]

    unique = {render_proposal(proposal): proposal for proposal in proposals}
    ordered = sorted(unique.values(), key=lambda proposal: _proposal_sort_key(proposal, noun_policy))
    stem = sampled.internal_id.removesuffix("_N")
    return tuple(
        ProposalOption(
            candidate_id=sampled.internal_id,
            option_id=f"{stem}_p{index:03d}",
            function_id=f"{stem}_p{index:03d}_N",
            constructor=proposal_constructor(proposal),
            explicit_form_arguments=proposal_form_arguments(proposal),
            expression=render_proposal(proposal),
            proposal=proposal,
        )
        for index, proposal in enumerate(ordered, start=1)
    )


def proposal_options(
    sample: Sequence[SampledCandidate], noun_policy: NounPolicy
) -> tuple[ProposalOption, ...]:
    return tuple(
        option
        for sampled in sample
        for option in proposals_for_candidate(sampled, noun_policy)
    )


def _probe_expression(field: str) -> str:
    if field.startswith("s_"):
        _, number, case = field.split("_")
        return f"n.s ! R.{number.capitalize()} ! R.{case.capitalize()}"
    if field.startswith("uncap_s_"):
        _, _, number, case = field.split("_")
        return f"n.uncap.s ! R.{number.capitalize()} ! R.{case.capitalize()}"
    if field == "co":
        return "n.co"
    if field == "uncap_co":
        return "n.uncap.co"
    if field == "gender":
        return (
            "case n.g of {R.Masc => \"masculine\" ; "
            "R.Fem => \"feminine\" ; R.Neutr => \"neuter\"}"
        )
    if field == "csep":
        return (
            "case n.csep of {R.BindSep => \"bind\" ; "
            "R.HyphenSep => \"hyphen\"}"
        )
    raise NounError(f"unknown noun probe field: {field}")


def _abstract_module(options: Sequence[ProposalOption]) -> bytes:
    functions = [f"  {option.function_id} : Entry ;" for option in options]
    source = [
        "abstract WdnPilotAbs = {",
        "flags startcat=Entry ;",
        "cat Entry ; Probe ;",
        "fun",
        *functions,
        "  probe_record : Entry -> Probe ;",
        "}",
        "",
    ]
    return "\n".join(source).encode("utf-8")


def _concrete_module(options: Sequence[ProposalOption]) -> bytes:
    entries = [
        f"  {option.function_id} = {option.expression} ;" for option in options
    ]
    probe_type = " ; ".join(f"{field} : Str" for field in PROBE_FIELDS)
    probe_values = " ;\n    ".join(
        f"{field} = {_probe_expression(field)}" for field in PROBE_FIELDS
    )
    source = [
        "concrete WdnPilotGer of WdnPilotAbs =",
        "  open Prelude, (R=ResGer), (P=ParadigmsGer) in {",
        "flags coding=utf8 ;",
        f"lincat Entry = R.Noun ; Probe = {{{probe_type}}} ;",
        "lin",
        *entries,
        "  probe_record n = {",
        f"    {probe_values}",
        "    } ;",
        "}",
        "",
    ]
    return "\n".join(source).encode("utf-8")


def proposal_manifest_bytes(options: Sequence[ProposalOption]) -> bytes:
    lines = [
        "candidate_id\toption_id\tfunction_id\tconstructor\t"
        "explicit_form_arguments\texpression"
    ]
    for option in options:
        fields = (
            option.candidate_id,
            option.option_id,
            option.function_id,
            option.constructor,
            str(option.explicit_form_arguments),
            option.expression,
        )
        if any(character in field for field in fields for character in "\t\r\n"):
            raise NounError("proposal manifest field escaped its structured TSV cell")
        lines.append("\t".join(fields))
    return ("\n".join(lines) + "\n").encode("utf-8")


def render_proposal_modules(
    sample: Sequence[SampledCandidate],
    noun_policy: NounPolicy,
    output_dir: Path = DEFAULT_NOUN_WORK,
) -> tuple[tuple[ProposalOption, ...], tuple[NounArtifact, ...]]:
    options = proposal_options(sample, noun_policy)
    if not options:
        raise NounError("noun sample produced no renderable proposals")
    artifacts = (
        _write_bytes(output_dir / "WdnPilotAbs.gf", _abstract_module(options)),
        _write_bytes(output_dir / "WdnPilotGer.gf", _concrete_module(options)),
        _write_bytes(
            output_dir / "proposal-manifest.tsv", proposal_manifest_bytes(options)
        ),
    )
    return options, artifacts


def _claim_json(claims: Sequence[ClaimEvidence]) -> str:
    return canonical_json(
        [
            {
                "statement": claim.statement_key,
                "rank": claim.rank,
                "value": claim.value_id,
            }
            for claim in claims
        ]
    )


def noun_sample_bytes(
    sample: Sequence[SampledCandidate], noun_policy: NounPolicy
) -> bytes:
    headers = (
        "internal_id",
        "source_key",
        "lexeme_ids",
        "entity_sha256",
        "lemma_json",
        "stratum",
        "sample_score_sha256",
        "pinned",
        "genders",
        "gender_claims_json",
        "number_restriction",
        "restriction_claims_json",
        "paradigm_claims_json",
        "source_completeness",
        "slot_values_json",
        "slot_form_ids_json",
        "combining_forms_json",
        "object_form_evidence_json",
        "compound_statement_ids_json",
        "sense_statement_ids_json",
        "structural_evidence",
        "orthography",
        "diagnostics_json",
        "review_status",
    )
    lines = ["\t".join(headers)]
    for sampled in sample:
        candidate = sampled.candidate
        slot_values = {slot.field: list(slot.values) for slot in candidate.slots}
        slot_forms = {
            slot.field: [form.form_id for form in slot.forms] for slot in candidate.slots
        }
        combining = [
            {
                "form_id": form.form_id,
                "value": form.value,
                "features": list(form.features),
            }
            for form in candidate.combining_forms
        ]
        fields = (
            sampled.internal_id,
            candidate.source_key,
            canonical_json(list(candidate.lexeme_ids)),
            canonical_json(list(candidate.entity_sha256)),
            canonical_json(candidate.lemma),
            candidate.stratum,
            sampled.score,
            "yes" if sampled.pinned else "no",
            canonical_json([gender.value for gender in candidate.genders]),
            _claim_json(candidate.gender_claims),
            candidate.number_restriction.value,
            _claim_json(candidate.restriction_claims),
            _claim_json(candidate.paradigm_claims),
            candidate.source_completeness.value,
            canonical_json(slot_values),
            canonical_json(slot_forms),
            canonical_json(combining),
            canonical_json(list(candidate.object_form_evidence)),
            canonical_json(list(candidate.compound_statement_keys)),
            canonical_json(list(candidate.sense_statement_keys)),
            candidate.structural_evidence.value,
            canonical_json(list(candidate.orthography)),
            canonical_json(list(candidate.diagnostics)),
            noun_policy.review_status,
        )
        if any("\t" in field or "\n" in field or "\r" in field for field in fields):
            raise NounError("noun sample field escaped its structured TSV cell")
        lines.append("\t".join(fields))
    return ("\n".join(lines) + "\n").encode("utf-8")


def _write_bytes(path: Path, content: bytes) -> NounArtifact:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise
    return NounArtifact(path, hashlib.sha256(content).hexdigest(), len(content))


def generate_noun_sample(
    *,
    database_path: Path = DEFAULT_DATABASE,
    noun_policy_path: Path = DEFAULT_NOUN_POLICY,
    feature_policy_path: Path = DEFAULT_FEATURE_POLICY,
    output_path: Path = DEFAULT_NOUN_SAMPLE,
    expected_snapshot: Mapping[str, object] | None = None,
) -> tuple[tuple[SampledCandidate, ...], NounArtifact]:
    noun_policy = load_noun_policy(noun_policy_path)
    feature_policy = load_feature_policy(feature_policy_path)
    connection = _connect(database_path)
    try:
        metadata = load_store_metadata(connection)
        if expected_snapshot is not None and metadata.get("snapshot") != dict(
            expected_snapshot
        ):
            raise NounError("source database snapshot does not match the verified lock")
        sample = select_noun_sample(connection, noun_policy, feature_policy)
        artifact = _write_bytes(output_path, noun_sample_bytes(sample, noun_policy))
        return sample, artifact
    finally:
        connection.close()
