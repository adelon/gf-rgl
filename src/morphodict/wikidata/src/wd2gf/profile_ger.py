"""Raw and interpreted German source profiles."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import tempfile
import tomllib
import unicodedata
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from wd2gf.store import DEFAULT_DATABASE, SCHEMA_VERSION, canonical_json


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RAW_REPORT_DIR = PROJECT_ROOT / ".work/reports/raw"
DEFAULT_FIXTURE_DIR = PROJECT_ROOT / "languages/ger/fixtures/pinned"
DEFAULT_FIXTURE_SELECTION = DEFAULT_FIXTURE_DIR / "selection.tsv"
DEFAULT_FEATURE_POLICY = PROJECT_ROOT / "languages/ger/features.toml"
DEFAULT_INTERPRETED_REPORT_DIR = PROJECT_ROOT / ".work/reports/interpreted"
COMBINING_FORM = "Q107614077"
COMPOUND_PROPERTY = "P5238"
PARADIGM_CLASS_PROPERTY = "P5911"
SERIES_ORDINAL_PROPERTY = "P1545"
OBJECT_FORM_PROPERTY = "P5548"
NOUN_CATEGORY = "Q1084"


class ProfileError(RuntimeError):
    """The profile cannot be derived from the source store."""


@dataclass(frozen=True)
class ReportArtifact:
    path: Path
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class FeaturePolicy:
    lexical_categories: dict[str, str]
    properties: dict[str, str]
    form_features: dict[str, str]
    statement_values: dict[str, str]
    entity_ids: dict[str, str]
    rejected_noun_form_features: dict[str, str]


def load_feature_policy(path: Path = DEFAULT_FEATURE_POLICY) -> FeaturePolicy:
    try:
        with path.open("rb") as policy_file:
            data = tomllib.load(policy_file)
    except FileNotFoundError as error:
        raise ProfileError(f"feature policy does not exist: {path}") from error
    expected = {
        "schema_version",
        "reference",
        "reference_url",
        "lexical_categories",
        "properties",
        "form_features",
        "statement_values",
        "entity_ids",
        "rejected_noun_form_features",
    }
    if set(data) != expected or data["schema_version"] != 1:
        raise ProfileError("unsupported feature policy schema")
    sections = {}
    for section in expected - {"schema_version", "reference", "reference_url"}:
        mapping = data[section]
        if not isinstance(mapping, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in mapping.items()
        ):
            raise ProfileError(f"feature policy section {section} must map IDs to strings")
        sections[section] = dict(mapping)
    overlap = set(sections["form_features"]) & set(
        sections["rejected_noun_form_features"]
    )
    if overlap:
        raise ProfileError(f"mapped and rejected noun features overlap: {sorted(overlap)}")
    return FeaturePolicy(**sections)


def _table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> list[str]:
    rendered_rows = [[str(value).replace("|", "\\|") for value in row] for row in rows]
    return [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
        *("| " + " | ".join(row) + " |" for row in rendered_rows),
    ]


def _write_bytes(path: Path, content: bytes) -> ReportArtifact:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(file_descriptor, "wb") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise
    return ReportArtifact(path, hashlib.sha256(content).hexdigest(), len(content))


def _tsv(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> bytes:
    lines = ["\t".join(headers)]
    for row in rows:
        fields = []
        for value in row:
            field = str(value)
            if any(character in field for character in "\t\r\n"):
                field = json.dumps(field, ensure_ascii=False)
            fields.append(field)
        lines.append("\t".join(fields))
    return ("\n".join(lines) + "\n").encode("utf-8")


def _connect(database_path: Path) -> sqlite3.Connection:
    if not database_path.is_file():
        raise ProfileError(f"source database does not exist: {database_path}")
    connection = sqlite3.connect(f"file:{database_path}?mode=ro", uri=True)
    user_version = connection.execute("PRAGMA user_version").fetchone()[0]
    if user_version != SCHEMA_VERSION:
        connection.close()
        raise ProfileError(
            f"incompatible source database schema {user_version}; expected {SCHEMA_VERSION}"
        )
    return connection


def load_store_metadata(connection: sqlite3.Connection) -> dict[str, Any]:
    rows = connection.execute(
        "SELECT key, value_json FROM metadata ORDER BY key"
    ).fetchall()
    if not rows:
        raise ProfileError("source database has no finalized metadata")
    return {key: json.loads(value_json) for key, value_json in rows}


def _check_snapshot(
    store_metadata: Mapping[str, Any], expected_snapshot: Mapping[str, object] | None
) -> None:
    if expected_snapshot is not None and store_metadata.get("snapshot") != dict(
        expected_snapshot
    ):
        raise ProfileError("source database snapshot does not match the verified lock")


def _count(connection: sqlite3.Connection, query: str, parameters: tuple = ()) -> int:
    return int(connection.execute(query, parameters).fetchone()[0])


def _inventory_rows(connection: sqlite3.Connection) -> list[tuple[str, str, str, int, int]]:
    rows: list[tuple[str, str, str, int, int]] = []
    queries = [
        (
            "qid",
            "entity_language",
            "SELECT language_qid, COUNT(*), COUNT(DISTINCT lexeme_id) "
            "FROM lexeme GROUP BY language_qid",
        ),
        (
            "qid",
            "lexical_category",
            "SELECT lexical_category_qid, COUNT(*), COUNT(DISTINCT lexeme_id) "
            "FROM lexeme GROUP BY lexical_category_qid",
        ),
        (
            "representation_tag",
            "lemma",
            "SELECT language_tag, COUNT(*), COUNT(DISTINCT lexeme_id) "
            "FROM lemma GROUP BY language_tag",
        ),
        (
            "representation_tag",
            "form",
            "SELECT r.language_tag, COUNT(*), COUNT(DISTINCT f.lexeme_id) "
            "FROM form_representation r JOIN form f USING(form_id) "
            "GROUP BY r.language_tag",
        ),
        (
            "qid",
            "form_feature",
            "SELECT ff.feature_qid, COUNT(*), COUNT(DISTINCT f.lexeme_id) "
            "FROM form_feature ff JOIN form f USING(form_id) GROUP BY ff.feature_qid",
        ),
        (
            "property",
            "statement",
            "SELECT property_id, COUNT(*), COUNT(DISTINCT subject_kind || ':' || subject_id) "
            "FROM statement GROUP BY property_id",
        ),
        (
            "property",
            "qualifier",
            "SELECT property_id, COUNT(*), COUNT(DISTINCT statement_rowid) "
            "FROM qualifier GROUP BY property_id",
        ),
        (
            "qid",
            "statement_value",
            "SELECT value_qid, COUNT(*), COUNT(DISTINCT subject_kind || ':' || subject_id) "
            "FROM statement WHERE value_qid IS NOT NULL GROUP BY value_qid",
        ),
        (
            "qid",
            "qualifier_value",
            "SELECT value_qid, COUNT(*), COUNT(DISTINCT statement_rowid) "
            "FROM qualifier WHERE value_qid IS NOT NULL GROUP BY value_qid",
        ),
    ]
    for kind, context, query in queries:
        rows.extend(
            (kind, context, identifier, int(count), int(subjects))
            for identifier, count, subjects in connection.execute(query)
        )
    return sorted(rows)


FEATURE_BUNDLE_QUERY = """
WITH ordered_features AS (
  SELECT form_id, feature_qid
  FROM form_feature
  ORDER BY form_id, feature_qid, position
),
bundles AS (
  SELECT form_id, group_concat(feature_qid, '|') AS feature_bundle
  FROM ordered_features
  GROUP BY form_id
),
form_bundles AS (
  SELECT f.form_id, f.lexeme_id, l.lexical_category_qid,
         COALESCE(b.feature_bundle, '') AS feature_bundle
  FROM form f
  JOIN lexeme l USING(lexeme_id)
  LEFT JOIN bundles b USING(form_id)
)
SELECT fb.lexical_category_qid, fb.feature_bundle,
       COUNT(DISTINCT fb.form_id) AS forms,
       COUNT(DISTINCT fb.lexeme_id) AS lexemes,
       COUNT(r.language_tag) AS representations,
       COUNT(DISTINCT r.value) AS distinct_values
FROM form_bundles fb
LEFT JOIN form_representation r USING(form_id)
GROUP BY fb.lexical_category_qid, fb.feature_bundle
ORDER BY fb.lexical_category_qid, fb.feature_bundle
"""


SLOT_DUPLICATE_QUERY = """
WITH ordered_features AS (
  SELECT form_id, feature_qid
  FROM form_feature
  ORDER BY form_id, feature_qid, position
),
bundles AS (
  SELECT form_id, group_concat(feature_qid, '|') AS feature_bundle
  FROM ordered_features
  GROUP BY form_id
),
slots AS (
  SELECT f.lexeme_id, r.language_tag, COALESCE(b.feature_bundle, '') AS feature_bundle,
         COUNT(*) AS forms, COUNT(DISTINCT r.value) AS values_count
  FROM form f
  JOIN form_representation r USING(form_id)
  LEFT JOIN bundles b USING(form_id)
  GROUP BY f.lexeme_id, r.language_tag, COALESCE(b.feature_bundle, '')
)
SELECT COUNT(*),
       SUM(CASE WHEN forms > 1 AND values_count = 1 THEN 1 ELSE 0 END),
       SUM(CASE WHEN values_count > 1 THEN 1 ELSE 0 END)
FROM slots
"""


def _series_ordinal(value_json: str | None) -> int | None:
    value = json.loads(value_json) if value_json is not None else None
    if (
        not isinstance(value, str)
        or not value
        or not value.isascii()
        or not value.isdecimal()
    ):
        return None
    ordinal = int(value)
    return ordinal if ordinal > 0 and str(ordinal) == value else None


def _compound_order_metrics(connection: sqlite3.Connection) -> dict[str, int]:
    statements_by_source: dict[str, list[int]] = {}
    rows = connection.execute(
        "SELECT subject_id, statement_rowid FROM statement "
        "WHERE subject_kind = 'lexeme' AND property_id = ? "
        "ORDER BY subject_id, position, statement_rowid",
        (COMPOUND_PROPERTY,),
    )
    for source_id, statement_rowid in rows:
        statements_by_source.setdefault(source_id, []).append(statement_rowid)

    ordinal_values: dict[int, list[str | None]] = {}
    rows = connection.execute(
        "SELECT q.statement_rowid, q.value_json FROM qualifier q "
        "JOIN statement s USING(statement_rowid) "
        "WHERE s.subject_kind = 'lexeme' AND s.property_id = ? "
        "AND q.property_id = ? ORDER BY q.statement_rowid, q.position",
        (COMPOUND_PROPERTY, SERIES_ORDINAL_PROPERTY),
    )
    for statement_rowid, value_json in rows:
        ordinal_values.setdefault(statement_rowid, []).append(value_json)

    result = {
        "fully_ordered_analyses": 0,
        "partially_ordered_analyses": 0,
        "duplicate_ordinal_analyses": 0,
        "malformed_ordinal_analyses": 0,
    }
    for statement_ids in statements_by_source.values():
        if len(statement_ids) < 2:
            continue
        values_by_component = [
            ordinal_values.get(identifier, []) for identifier in statement_ids
        ]
        parsed_by_component = [
            [_series_ordinal(value_json) for value_json in values]
            for values in values_by_component
        ]
        if any(
            len(values) > 1 or any(ordinal is None for ordinal in parsed)
            for values, parsed in zip(
                values_by_component, parsed_by_component, strict=True
            )
        ):
            result["malformed_ordinal_analyses"] += 1
            continue
        assigned = [parsed[0] for parsed in parsed_by_component if parsed]
        if len(set(assigned)) != len(assigned):
            result["duplicate_ordinal_analyses"] += 1
        elif any(ordinal > len(statement_ids) for ordinal in assigned):
            result["malformed_ordinal_analyses"] += 1
        elif len(assigned) < len(statement_ids):
            result["partially_ordered_analyses"] += 1
        elif set(assigned) == set(range(1, len(statement_ids) + 1)):
            result["fully_ordered_analyses"] += 1
        else:
            result["malformed_ordinal_analyses"] += 1
    return result


def _compound_metrics(connection: sqlite3.Connection) -> dict[str, int]:
    known_lexemes = {
        lexeme_id for (lexeme_id,) in connection.execute("SELECT lexeme_id FROM lexeme")
    }
    targets: list[str | None] = []
    for (value_json,) in connection.execute(
        "SELECT value_json FROM statement WHERE property_id = ? ORDER BY statement_rowid",
        (COMPOUND_PROPERTY,),
    ):
        value = json.loads(value_json) if value_json is not None else None
        target = value.get("id") if isinstance(value, dict) else None
        targets.append(target if isinstance(target, str) else None)
    valid_targets = [target for target in targets if target is not None]
    result = {
        "statements": len(targets),
        "source_lexemes": _count(
            connection,
            "SELECT COUNT(DISTINCT subject_id) FROM statement "
            "WHERE subject_kind = 'lexeme' AND property_id = ?",
            (COMPOUND_PROPERTY,),
        ),
        "distinct_targets": len(set(valid_targets)),
        "resolved_targets": len({target for target in valid_targets if target in known_lexemes}),
        "unresolved_target_statements": sum(
            target is None or target not in known_lexemes for target in targets
        ),
        "series_ordinal_qualifiers": _count(
            connection,
            "SELECT COUNT(*) FROM qualifier q JOIN statement s USING(statement_rowid) "
            "WHERE s.property_id = ? AND q.property_id = ?",
            (COMPOUND_PROPERTY, SERIES_ORDINAL_PROPERTY),
        ),
        "object_form_qualifiers": _count(
            connection,
            "SELECT COUNT(*) FROM qualifier q JOIN statement s USING(statement_rowid) "
            "WHERE s.property_id = ? AND q.property_id = ?",
            (COMPOUND_PROPERTY, OBJECT_FORM_PROPERTY),
        ),
        "multi_component_sources": _count(
            connection,
            "SELECT COUNT(*) FROM (SELECT subject_id FROM statement "
            "WHERE subject_kind = 'lexeme' AND property_id = ? "
            "GROUP BY subject_id HAVING COUNT(*) > 1)",
            (COMPOUND_PROPERTY,),
        ),
    }
    result.update(_compound_order_metrics(connection))
    if sum(
        result[key]
        for key in (
            "fully_ordered_analyses",
            "partially_ordered_analyses",
            "duplicate_ordinal_analyses",
            "malformed_ordinal_analyses",
        )
    ) != result["multi_component_sources"]:
        raise ProfileError("compound-order classifications are not exhaustive")
    return result


def _raw_markdown(
    connection: sqlite3.Connection,
    store_metadata: Mapping[str, Any],
    inventory: Sequence[tuple[str, str, str, int, int]],
) -> bytes:
    counts = store_metadata["counts"]
    snapshot = store_metadata["snapshot"]
    categories = connection.execute(
        "SELECT lexical_category_qid, COUNT(*) FROM lexeme "
        "GROUP BY lexical_category_qid ORDER BY COUNT(*) DESC, lexical_category_qid"
    ).fetchall()
    lemma_tags = connection.execute(
        "SELECT language_tag, COUNT(*), COUNT(DISTINCT lexeme_id) FROM lemma "
        "GROUP BY language_tag ORDER BY COUNT(*) DESC, language_tag"
    ).fetchall()
    form_tags = connection.execute(
        "SELECT r.language_tag, COUNT(*), COUNT(DISTINCT f.lexeme_id) "
        "FROM form_representation r JOIN form f USING(form_id) "
        "GROUP BY r.language_tag ORDER BY COUNT(*) DESC, r.language_tag"
    ).fetchall()
    ranks = connection.execute(
        "SELECT subject_kind, rank, COUNT(*) FROM statement "
        "GROUP BY subject_kind, rank ORDER BY subject_kind, rank"
    ).fetchall()
    top_features = connection.execute(
        "SELECT feature_qid, COUNT(*), COUNT(DISTINCT form_id) FROM form_feature "
        "GROUP BY feature_qid ORDER BY COUNT(*) DESC, feature_qid LIMIT 40"
    ).fetchall()
    top_properties = connection.execute(
        "SELECT property_id, COUNT(*), COUNT(DISTINCT subject_kind || ':' || subject_id) "
        "FROM statement GROUP BY property_id "
        "ORDER BY COUNT(*) DESC, property_id LIMIT 40"
    ).fetchall()
    total_slots, exact_duplicate_slots, conflicting_slots = connection.execute(
        SLOT_DUPLICATE_QUERY
    ).fetchone()
    competing_statements = _count(
        connection,
        "SELECT COUNT(*) FROM (SELECT subject_kind, subject_id, property_id "
        "FROM statement GROUP BY subject_kind, subject_id, property_id "
        "HAVING COUNT(*) > 1)",
    )
    conflicting_statements = _count(
        connection,
        "SELECT COUNT(*) FROM (SELECT subject_kind, subject_id, property_id "
        "FROM statement GROUP BY subject_kind, subject_id, property_id "
        "HAVING COUNT(DISTINCT COALESCE(value_json, snaktype)) > 1)",
    )
    duplicate_lemma_groups = _count(
        connection,
        "SELECT COUNT(*) FROM (SELECT lexical_category_qid, language_tag, value "
        "FROM lexeme JOIN lemma USING(lexeme_id) "
        "GROUP BY lexical_category_qid, language_tag, value HAVING COUNT(*) > 1)",
    )
    combining = {
        "forms": _count(
            connection,
            "SELECT COUNT(DISTINCT form_id) FROM form_feature WHERE feature_qid = ?",
            (COMBINING_FORM,),
        ),
        "noun_forms": _count(
            connection,
            "SELECT COUNT(DISTINCT f.form_id) FROM form_feature ff "
            "JOIN form f USING(form_id) JOIN lexeme l USING(lexeme_id) "
            "WHERE ff.feature_qid = ? AND l.lexical_category_qid = ?",
            (COMBINING_FORM, NOUN_CATEGORY),
        ),
        "noun_lexemes": _count(
            connection,
            "SELECT COUNT(DISTINCT f.lexeme_id) FROM form_feature ff "
            "JOIN form f USING(form_id) JOIN lexeme l USING(lexeme_id) "
            "WHERE ff.feature_qid = ? AND l.lexical_category_qid = ?",
            (COMBINING_FORM, NOUN_CATEGORY),
        ),
        "lexemes": _count(
            connection,
            "SELECT COUNT(DISTINCT f.lexeme_id) FROM form_feature ff "
            "JOIN form f USING(form_id) WHERE ff.feature_qid = ?",
            (COMBINING_FORM,),
        ),
        "multiple_forms": _count(
            connection,
            "SELECT COUNT(*) FROM (SELECT f.lexeme_id FROM form_feature ff "
            "JOIN form f USING(form_id) WHERE ff.feature_qid = ? "
            "GROUP BY f.lexeme_id HAVING COUNT(DISTINCT f.form_id) > 1)",
            (COMBINING_FORM,),
        ),
    }
    paradigm = {
        "statements": _count(
            connection,
            "SELECT COUNT(*) FROM statement WHERE property_id = ?",
            (PARADIGM_CLASS_PROPERTY,),
        ),
        "lexemes": _count(
            connection,
            "SELECT COUNT(DISTINCT subject_id) FROM statement "
            "WHERE subject_kind = 'lexeme' AND property_id = ?",
            (PARADIGM_CLASS_PROPERTY,),
        ),
    }
    compound = _compound_metrics(connection)
    lines = [
        "# Raw German Wikidata Lexeme profile",
        "",
        "This report contains only source IDs and structural counts. Labels and",
        "linguistic interpretations are frozen separately after inventory review.",
        "",
        "## Provenance and selection",
        "",
        f"- Snapshot date: `{snapshot['dump_date']}`",
        f"- Snapshot SHA-256: `{snapshot['sha256']}`",
        f"- Entity-language policy: exact `{store_metadata['source_policy']['language_entity']}`",
        f"- Entities before selection: {counts['entities_before_selection']}",
        f"- Validated Lexemes: {counts['lexemes_validated']}",
        f"- Selected entities: {counts['entities_selected']}",
        f"- Excluded by entity language: {counts['entities_excluded_language']}",
        "",
        "## Lexical categories",
        "",
        *_table(["QID", "Lexemes"], categories),
        "",
        "## Representation tags",
        "",
        "Lemma tags:",
        "",
        *_table(["Tag", "Representations", "Lexemes"], lemma_tags),
        "",
        "Form tags:",
        "",
        *_table(["Tag", "Representations", "Lexemes"], form_tags),
        "",
        "## Stored projections",
        "",
        f"- Lemma representations: {counts['selected_lemmas']}",
        f"- Forms: {counts['selected_forms']}",
        f"- Form representations: {counts['selected_form_representations']}",
        f"- Form feature assignments: {counts['selected_form_features']}",
        f"- Senses: {counts['selected_senses']}",
        f"- Statements: {counts['selected_statements']}",
        f"- Qualifiers: {counts['selected_qualifiers']}",
        "",
        "Statement ranks:",
        "",
        *_table(["Subject", "Rank", "Statements"], ranks),
        "",
        "## Form evidence",
        "",
        f"- Distinct Lexeme/tag/feature-bundle slots: {total_slots}",
        f"- Exact duplicate slots: {exact_duplicate_slots or 0}",
        f"- Conflicting-value slots: {conflicting_slots or 0}",
        (
            f"- `{COMBINING_FORM}` forms (all categories): {combining['forms']} "
            f"across {combining['lexemes']} Lexemes"
        ),
        (
            f"- `{COMBINING_FORM}` noun forms (`{NOUN_CATEGORY}`): "
            f"{combining['noun_forms']} across {combining['noun_lexemes']} Lexemes"
        ),
        f"- Lexemes with multiple `{COMBINING_FORM}` forms: {combining['multiple_forms']}",
        "",
        "Most frequent raw grammatical features:",
        "",
        *_table(["QID", "Assignments", "Forms"], top_features),
        "",
        "## Statement evidence",
        "",
        f"- Subject/property groups with competing statements: {competing_statements}",
        f"- Subject/property groups with conflicting values: {conflicting_statements}",
        f"- Duplicate category/tag/lemma groups: {duplicate_lemma_groups}",
        f"- `{PARADIGM_CLASS_PROPERTY}`: {paradigm['statements']} statements on {paradigm['lexemes']} Lexemes",
        f"- `{COMPOUND_PROPERTY}`: {compound['statements']} statements on {compound['source_lexemes']} Lexemes",
        f"- `{COMPOUND_PROPERTY}` distinct target IDs: {compound['distinct_targets']}",
        f"- Targets resolved inside exact-Q188 store: {compound['resolved_targets']}",
        f"- Unresolved or malformed target statements: {compound['unresolved_target_statements']}",
        f"- Sources with multiple components: {compound['multi_component_sources']}",
        f"- `{SERIES_ORDINAL_PROPERTY}` qualifiers on compound statements: {compound['series_ordinal_qualifiers']}",
        f"- Fully ordered multi-component analyses: {compound['fully_ordered_analyses']}",
        f"- Partially ordered multi-component analyses: {compound['partially_ordered_analyses']}",
        f"- Duplicate-ordinal multi-component analyses: {compound['duplicate_ordinal_analyses']}",
        f"- Malformed-ordinal multi-component analyses: {compound['malformed_ordinal_analyses']}",
        f"- `{OBJECT_FORM_PROPERTY}` qualifiers on compound statements: {compound['object_form_qualifiers']}",
        "",
        "Ordering is classified once per source with multiple component statements.",
        "Fully ordered means exactly one canonical positive decimal ordinal per",
        "component and the complete sequence `1..N`; partially ordered means that",
        "some or all ordinals are absent but every present ordinal is valid and",
        "unique. Repeated ordinals form the duplicate bucket; invalid, ambiguous,",
        "or out-of-range ordinals form the malformed bucket.",
        "",
        "Most frequent raw statement properties:",
        "",
        *_table(["Property", "Statements", "Subjects"], top_properties),
        "",
        "## Companion inventories",
        "",
        f"The complete raw inventory contains {len(inventory)} deterministic rows in",
        "`raw-inventory.tsv`. All feature bundles are in `raw-feature-bundles.tsv`.",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def generate_raw_profile(
    *,
    database_path: Path = DEFAULT_DATABASE,
    output_dir: Path = DEFAULT_RAW_REPORT_DIR,
    expected_snapshot: Mapping[str, object] | None = None,
) -> list[ReportArtifact]:
    connection = _connect(database_path)
    try:
        store_metadata = load_store_metadata(connection)
        _check_snapshot(store_metadata, expected_snapshot)
        inventory = _inventory_rows(connection)
        bundles = connection.execute(FEATURE_BUNDLE_QUERY).fetchall()
        artifacts = [
            _write_bytes(
                output_dir / "raw-inventory.tsv",
                _tsv(("kind", "context", "id", "count", "subjects"), inventory),
            ),
            _write_bytes(
                output_dir / "raw-feature-bundles.tsv",
                _tsv(
                    (
                        "lexical_category_qid",
                        "feature_bundle",
                        "forms",
                        "lexemes",
                        "representations",
                        "distinct_values",
                    ),
                    bundles,
                ),
            ),
        ]
        artifacts.insert(
            0,
            _write_bytes(
                output_dir / "raw-profile.md",
                _raw_markdown(connection, store_metadata, inventory),
            ),
        )
        return artifacts
    finally:
        connection.close()


def _read_fixture_selection(path: Path) -> list[tuple[str, str]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as error:
        raise ProfileError(f"fixture selection does not exist: {path}") from error
    if not lines or lines[0] != "lexeme_id\treason":
        raise ProfileError("fixture selection must start with lexeme_id and reason columns")
    selections: list[tuple[str, str]] = []
    seen: set[str] = set()
    for line_number, line in enumerate(lines[1:], start=2):
        if not line:
            continue
        fields = line.split("\t")
        if len(fields) != 2 or not fields[0] or not fields[1]:
            raise ProfileError(f"invalid fixture selection row {line_number}")
        lexeme_id, reason = fields
        if lexeme_id in seen:
            raise ProfileError(f"duplicate fixture Lexeme ID: {lexeme_id}")
        seen.add(lexeme_id)
        selections.append((lexeme_id, reason))
    if not selections:
        raise ProfileError("fixture selection is empty")
    return sorted(selections)


def extract_pinned_fixture(
    *,
    database_path: Path = DEFAULT_DATABASE,
    selection_path: Path = DEFAULT_FIXTURE_SELECTION,
    output_dir: Path = DEFAULT_FIXTURE_DIR,
    expected_snapshot: Mapping[str, object] | None = None,
) -> list[ReportArtifact]:
    selections = _read_fixture_selection(selection_path)
    connection = _connect(database_path)
    try:
        store_metadata = load_store_metadata(connection)
        _check_snapshot(store_metadata, expected_snapshot)
        snapshot_sha256 = store_metadata["snapshot"]["sha256"]
        payloads: list[str] = []
        manifest_rows: list[tuple[object, ...]] = []
        for lexeme_id, reason in selections:
            row = connection.execute(
                "SELECT lexical_category_qid, entity_sha256, canonical_json "
                "FROM lexeme WHERE lexeme_id = ?",
                (lexeme_id,),
            ).fetchone()
            if row is None:
                raise ProfileError(f"selected fixture Lexeme is absent: {lexeme_id}")
            lexical_category, entity_sha256, payload = row
            payloads.append(payload)
            manifest_rows.append(
                (
                    snapshot_sha256,
                    lexeme_id,
                    entity_sha256,
                    lexical_category,
                    reason,
                )
            )
        fixture = ("[\n" + ",\n".join(payloads) + "\n]\n").encode("utf-8")
        manifest = _tsv(
            (
                "snapshot_sha256",
                "lexeme_id",
                "entity_sha256",
                "lexical_category_qid",
                "reason",
            ),
            manifest_rows,
        )
        return [
            _write_bytes(output_dir / "lexemes.json", fixture),
            _write_bytes(output_dir / "manifest.tsv", manifest),
        ]
    finally:
        connection.close()


def _inverse(mapping: Mapping[str, str], label: str) -> str:
    matches = [identifier for identifier, mapped_label in mapping.items() if mapped_label == label]
    if len(matches) != 1:
        raise ProfileError(f"feature policy must map exactly one ID to {label!r}")
    return matches[0]


def _claim_values(
    connection: sqlite3.Connection,
    *,
    lexical_category: str,
    property_id: str,
) -> dict[str, set[str]]:
    values: dict[str, set[str]] = {}
    rows = connection.execute(
        """
        SELECT s.subject_id, s.snaktype, s.value_qid, s.value_json
        FROM statement s
        JOIN lexeme l ON l.lexeme_id = s.subject_id
        WHERE s.subject_kind = 'lexeme' AND s.rank != 'deprecated'
          AND l.lexical_category_qid = ? AND s.property_id = ?
        ORDER BY s.subject_id, s.statement_rowid
        """,
        (lexical_category, property_id),
    )
    for lexeme_id, snaktype, value_qid, value_json in rows:
        identifier = value_qid
        if identifier is None and value_json is not None:
            value = json.loads(value_json)
            if isinstance(value, dict) and isinstance(value.get("id"), str):
                identifier = value["id"]
        if identifier is None:
            identifier = f"snaktype:{snaktype}"
        values.setdefault(lexeme_id, set()).add(identifier)
    return values


CATEGORY_FORM_BUNDLES_QUERY = """
WITH ordered_features AS (
  SELECT form_id, feature_qid
  FROM form_feature
  ORDER BY form_id, feature_qid, position
),
bundles AS (
  SELECT form_id, group_concat(feature_qid, '|') AS feature_bundle
  FROM ordered_features
  GROUP BY form_id
)
SELECT f.lexeme_id, f.form_id, r.value, COALESCE(b.feature_bundle, '')
FROM form f
JOIN lexeme l USING(lexeme_id)
JOIN form_representation r USING(form_id)
LEFT JOIN bundles b USING(form_id)
WHERE l.lexical_category_qid = ? AND r.language_tag = 'de'
ORDER BY f.lexeme_id, f.position, f.form_id
"""


def _iter_lexeme_forms(
    connection: sqlite3.Connection, lexical_category: str
) -> Iterable[tuple[str, list[tuple[str, str, frozenset[str]]]]]:
    current_id: str | None = None
    forms: list[tuple[str, str, frozenset[str]]] = []
    for lexeme_id, form_id, value, bundle in connection.execute(
        CATEGORY_FORM_BUNDLES_QUERY, (lexical_category,)
    ):
        if current_id is not None and lexeme_id != current_id:
            yield current_id, forms
            forms = []
        current_id = lexeme_id
        forms.append((form_id, value, frozenset(bundle.split("|") if bundle else ())))
    if current_id is not None:
        yield current_id, forms


def _lemma_ids(connection: sqlite3.Connection, category: str) -> set[str]:
    return {
        lexeme_id
        for (lexeme_id,) in connection.execute(
            "SELECT l.lexeme_id FROM lexeme l JOIN lemma m USING(lexeme_id) "
            "WHERE l.lexical_category_qid = ? AND m.language_tag = 'de'",
            (category,),
        )
    }


def _noun_profile(
    connection: sqlite3.Connection, policy: FeaturePolicy
) -> dict[str, Any]:
    noun = _inverse(policy.lexical_categories, "N")
    number_ids = {
        _inverse(policy.form_features, "singular"): "singular",
        _inverse(policy.form_features, "plural"): "plural",
    }
    case_ids = {
        _inverse(policy.form_features, "nominative"): "nominative",
        _inverse(policy.form_features, "genitive"): "genitive",
        _inverse(policy.form_features, "dative"): "dative",
        _inverse(policy.form_features, "accusative"): "accusative",
    }
    combining = _inverse(policy.form_features, "combining_form")
    plural_only = _inverse(policy.statement_values, "plurale_tantum")
    singular_only = _inverse(policy.statement_values, "singulare_tantum")
    gender_ids = {
        _inverse(policy.statement_values, "masculine"),
        _inverse(policy.statement_values, "feminine"),
        _inverse(policy.statement_values, "neuter"),
    }
    observed_features = {
        feature_qid
        for (feature_qid,) in connection.execute(
            "SELECT DISTINCT ff.feature_qid FROM form_feature ff "
            "JOIN form f USING(form_id) JOIN lexeme l USING(lexeme_id) "
            "WHERE l.lexical_category_qid = ?",
            (noun,),
        )
    }
    classified_features = set(policy.form_features) | set(
        policy.rejected_noun_form_features
    )
    unclassified = sorted(observed_features - classified_features)
    if unclassified:
        raise ProfileError(f"unclassified noun form features: {unclassified}")

    noun_ids = {
        lexeme_id
        for (lexeme_id,) in connection.execute(
            "SELECT lexeme_id FROM lexeme WHERE lexical_category_qid = ?", (noun,)
        )
    }
    lemmas = _lemma_ids(connection, noun)
    genders = _claim_values(
        connection,
        lexical_category=noun,
        property_id=_inverse(policy.properties, "grammatical_gender"),
    )
    instances = _claim_values(
        connection,
        lexical_category=noun,
        property_id=_inverse(policy.properties, "instance_of"),
    )
    metrics: Counter[str] = Counter()
    gender_status: Counter[str] = Counter()
    restriction_status: Counter[str] = Counter()
    for lexeme_id in noun_ids:
        raw_genders = genders.get(lexeme_id, set())
        known_genders = raw_genders & gender_ids
        if raw_genders - gender_ids:
            gender_status["unknown_or_novalue"] += 1
        elif not known_genders:
            gender_status["missing"] += 1
        elif len(known_genders) == 1:
            gender_status["single"] += 1
        else:
            gender_status["multiple"] += 1
        restrictions = instances.get(lexeme_id, set()) & {plural_only, singular_only}
        if restrictions == {plural_only}:
            restriction_status["plural_only"] += 1
        elif restrictions == {singular_only}:
            restriction_status["singular_only"] += 1
        elif restrictions == {plural_only, singular_only}:
            restriction_status["conflicting"] += 1
        else:
            restriction_status["ordinary"] += 1

    processed: set[str] = set()
    for lexeme_id, forms in _iter_lexeme_forms(connection, noun):
        processed.add(lexeme_id)
        slot_values: dict[tuple[str, str], set[str]] = {}
        slot_form_counts: Counter[tuple[str, str]] = Counter()
        rejected = False
        for _, value, features in forms:
            if features & set(policy.rejected_noun_form_features):
                rejected = True
            if combining in features:
                continue
            numbers = features & set(number_ids)
            cases = features & set(case_ids)
            if len(numbers) != 1 or len(cases) != 1:
                continue
            slot = (number_ids[next(iter(numbers))], case_ids[next(iter(cases))])
            slot_values.setdefault(slot, set()).add(value)
            slot_form_counts[slot] += 1
        restrictions = instances.get(lexeme_id, set()) & {plural_only, singular_only}
        if restrictions == {plural_only}:
            expected = {("plural", case) for case in case_ids.values()}
        elif restrictions == {singular_only}:
            expected = {("singular", case) for case in case_ids.values()}
        elif len(restrictions) > 1:
            expected = set()
            metrics["restriction_conflict"] += 1
        else:
            expected = {
                (number, case)
                for number in number_ids.values()
                for case in case_ids.values()
            }
        conflicting = any(len(values) > 1 for values in slot_values.values())
        exact_duplicates = any(
            slot_form_counts[slot] > 1 and len(values) == 1
            for slot, values in slot_values.items()
        )
        complete = bool(expected) and expected <= set(slot_values)
        if complete:
            metrics["complete_slots"] += 1
        elif slot_values:
            metrics["partial_slots"] += 1
        else:
            metrics["no_slots"] += 1
        if conflicting:
            metrics["conflicting_slots"] += 1
        if exact_duplicates:
            metrics["exact_duplicate_slots"] += 1
        if rejected:
            metrics["rejected_feature"] += 1
        raw_genders = genders.get(lexeme_id, set())
        known_genders = raw_genders & gender_ids
        common = (
            lexeme_id in lemmas
            and complete
            and not conflicting
            and not rejected
            and not (raw_genders - gender_ids)
        )
        if common and len(known_genders) == 1:
            metrics["source_usable_single_gender"] += 1
        elif common and len(known_genders) > 1:
            metrics["source_usable_split_gender"] += 1
    without_de_forms = len(noun_ids - processed)
    metrics["no_de_form_representations"] += without_de_forms
    metrics["no_slots"] += without_de_forms
    metrics["without_de_lemma"] += len(noun_ids - lemmas)
    metrics["total"] = len(noun_ids)
    return {
        "metrics": metrics,
        "gender": gender_status,
        "restriction": restriction_status,
    }


def _verb_profile(
    connection: sqlite3.Connection, policy: FeaturePolicy
) -> dict[str, Counter[str]]:
    verb = _inverse(policy.lexical_categories, "V")
    identifiers = {
        label: _inverse(policy.form_features, label)
        for label in (
            "infinitive",
            "past_participle",
            "present_tense",
            "preterite",
            "indicative",
            "singular",
            "third_person",
        )
    }
    lemmas = _lemma_ids(connection, verb)
    forms_metrics: Counter[str] = Counter(total=_count(
        connection, "SELECT COUNT(*) FROM lexeme WHERE lexical_category_qid = ?", (verb,)
    ))
    complete_ids: set[str] = set()
    for lexeme_id, forms in _iter_lexeme_forms(connection, verb):
        feature_sets = [features for _, _, features in forms]
        flags = {
            "infinitive": any(identifiers["infinitive"] in features for features in feature_sets),
            "past_participle": any(
                identifiers["past_participle"] in features for features in feature_sets
            ),
            "present_3sg": any(
                {
                    identifiers["present_tense"],
                    identifiers["indicative"],
                    identifiers["singular"],
                    identifiers["third_person"],
                }
                <= features
                for features in feature_sets
            ),
            "preterite_3sg": any(
                {
                    identifiers["preterite"],
                    identifiers["indicative"],
                    identifiers["singular"],
                    identifiers["third_person"],
                }
                <= features
                for features in feature_sets
            ),
        }
        for name, present in flags.items():
            forms_metrics[f"with_{name}"] += int(present)
        if all(flags.values()):
            forms_metrics["principal_parts_complete"] += 1
            complete_ids.add(lexeme_id)
    forms_metrics["with_de_lemma"] = len(lemmas)

    auxiliary_property = _inverse(policy.properties, "auxiliary_verb")
    auxiliaries = _claim_values(
        connection, lexical_category=verb, property_id=auxiliary_property
    )
    haben = _inverse(policy.entity_ids, "haben")
    sein = _inverse(policy.entity_ids, "sein")
    auxiliary_metrics: Counter[str] = Counter()
    recognized_auxiliary: set[str] = set()
    for lexeme_id in lemmas:
        values = auxiliaries.get(lexeme_id, set())
        recognized = values & {haben, sein}
        unknown = values - {haben, sein}
        if unknown:
            auxiliary_metrics["unknown_or_novalue"] += 1
        elif recognized == {haben, sein}:
            auxiliary_metrics["both"] += 1
            recognized_auxiliary.add(lexeme_id)
        elif recognized == {haben}:
            auxiliary_metrics["haben"] += 1
            recognized_auxiliary.add(lexeme_id)
        elif recognized == {sein}:
            auxiliary_metrics["sein"] += 1
            recognized_auxiliary.add(lexeme_id)
        else:
            auxiliary_metrics["missing"] += 1
    forms_metrics["source_usable_with_auxiliary"] = len(
        complete_ids & recognized_auxiliary & lemmas
    )

    instances = _claim_values(
        connection,
        lexical_category=verb,
        property_id=_inverse(policy.properties, "instance_of"),
    )
    separable = _inverse(policy.statement_values, "separable_verb")
    inseparable = _inverse(policy.statement_values, "inseparable_verb")
    separability: Counter[str] = Counter()
    for lexeme_id in lemmas:
        values = instances.get(lexeme_id, set()) & {separable, inseparable}
        if values == {separable}:
            separability["separable"] += 1
        elif values == {inseparable}:
            separability["inseparable"] += 1
        elif len(values) > 1:
            separability["conflicting"] += 1
        else:
            separability["unrecorded"] += 1
    return {"forms": forms_metrics, "auxiliary": auxiliary_metrics, "separability": separability}


def _adjective_profile(
    connection: sqlite3.Connection, policy: FeaturePolicy
) -> Counter[str]:
    adjective = _inverse(policy.lexical_categories, "A")
    predicative = _inverse(policy.form_features, "predicative")
    degrees = {
        label: _inverse(policy.form_features, label)
        for label in ("positive", "comparative", "superlative")
    }
    lemmas = _lemma_ids(connection, adjective)
    instances = _claim_values(
        connection,
        lexical_category=adjective,
        property_id=_inverse(policy.properties, "instance_of"),
    )
    absolute = _inverse(policy.statement_values, "absolute_adjective")
    indeclinable = _inverse(policy.statement_values, "indeclinable_adjective")
    metrics: Counter[str] = Counter(total=_count(
        connection, "SELECT COUNT(*) FROM lexeme WHERE lexical_category_qid = ?", (adjective,)
    ))
    usable: set[str] = set()
    for lexeme_id, forms in _iter_lexeme_forms(connection, adjective):
        feature_sets = [features for _, _, features in forms]
        flags = {
            degree: any(
                predicative in features and feature_qid in features
                for features in feature_sets
            )
            for degree, feature_qid in degrees.items()
        }
        for degree, present in flags.items():
            metrics[f"with_{degree}_predicative"] += int(present)
        if all(flags.values()):
            metrics["all_degrees_predicative"] += 1
            usable.add(lexeme_id)
        elif flags["positive"] and absolute in instances.get(lexeme_id, set()):
            metrics["absolute_positive_only"] += 1
            usable.add(lexeme_id)
    metrics["with_de_lemma"] = len(lemmas)
    metrics["absolute_statements"] = sum(
        absolute in values for values in instances.values()
    )
    metrics["indeclinable_statements"] = sum(
        indeclinable in values for values in instances.values()
    )
    metrics["source_usable"] = len(usable & lemmas)
    return metrics


def _adverb_profile(
    connection: sqlite3.Connection, policy: FeaturePolicy
) -> Counter[str]:
    adverb = _inverse(policy.lexical_categories, "Adv")
    lemmas = _lemma_ids(connection, adverb)
    with_forms = {
        lexeme_id
        for (lexeme_id,) in connection.execute(
            "SELECT DISTINCT f.lexeme_id FROM form f JOIN lexeme l USING(lexeme_id) "
            "JOIN form_representation r USING(form_id) "
            "WHERE l.lexical_category_qid = ? AND r.language_tag = 'de'",
            (adverb,),
        )
    }
    return Counter(
        total=_count(
            connection,
            "SELECT COUNT(*) FROM lexeme WHERE lexical_category_qid = ?",
            (adverb,),
        ),
        with_de_lemma=len(lemmas),
        with_de_form=len(with_forms),
        source_usable=len(lemmas),
    )


def _spelling_rows(
    connection: sqlite3.Connection, policy: FeaturePolicy
) -> list[tuple[str, int, int, int, int, int, int]]:
    category_labels = policy.lexical_categories
    counters: dict[str, Counter[str]] = {
        label: Counter() for label in category_labels.values()
    }
    rows = connection.execute(
        "SELECT l.lexical_category_qid, m.value FROM lexeme l JOIN lemma m USING(lexeme_id) "
        "WHERE m.language_tag = 'de' ORDER BY l.lexical_category_qid, l.lexeme_id"
    )
    hyphens = set("-‐‑‒–—")
    for category_qid, value in rows:
        label = category_labels.get(category_qid)
        if label is None:
            continue
        counter = counters[label]
        counter["lemmas"] += 1
        counter["whitespace"] += int(any(character.isspace() for character in value))
        counter["hyphen"] += int(any(character in hyphens for character in value))
        counter["digit"] += int(any(character.isdigit() for character in value))
        cased = any(character.isalpha() for character in value)
        counter["all_upper"] += int(cased and value.upper() == value)
        counter["non_nfc"] += int(not unicodedata.is_normalized("NFC", value))
    return [
        (
            label,
            counter["lemmas"],
            counter["whitespace"],
            counter["hyphen"],
            counter["digit"],
            counter["all_upper"],
            counter["non_nfc"],
        )
        for label, counter in sorted(counters.items())
    ]


def _unknown_feature_rows(
    connection: sqlite3.Connection, policy: FeaturePolicy
) -> list[tuple[str, str, str, str, int, int]]:
    rows: list[tuple[str, str, str, str, int, int]] = []
    query = """
    SELECT l.lexical_category_qid, ff.feature_qid, COUNT(*), COUNT(DISTINCT f.lexeme_id)
    FROM form_feature ff
    JOIN form f USING(form_id)
    JOIN lexeme l USING(lexeme_id)
    GROUP BY l.lexical_category_qid, ff.feature_qid
    ORDER BY l.lexical_category_qid, ff.feature_qid
    """
    noun_qid = _inverse(policy.lexical_categories, "N")
    for category_qid, feature_qid, assignments, lexemes in connection.execute(query):
        if feature_qid in policy.form_features:
            continue
        if category_qid == noun_qid and feature_qid in policy.rejected_noun_form_features:
            status = "rejected"
            reason = policy.rejected_noun_form_features[feature_qid]
        else:
            status = "deferred_unknown"
            reason = "category fitting is outside Phase 1"
        rows.append(
            (
                category_qid,
                feature_qid,
                status,
                reason,
                int(assignments),
                int(lexemes),
            )
        )
    return rows


def _counter_rows(counter: Counter[str]) -> list[tuple[str, int]]:
    return [(key, int(counter[key])) for key in sorted(counter)]


def _mapped_statement_distribution(
    connection: sqlite3.Connection,
    *,
    property_id: str,
    category_qid: str,
    mappings: Mapping[str, str],
) -> list[tuple[str, int, int]]:
    rows = connection.execute(
        """
        SELECT s.value_qid, COUNT(*), COUNT(DISTINCT s.subject_id)
        FROM statement s JOIN lexeme l ON l.lexeme_id = s.subject_id
        WHERE s.subject_kind = 'lexeme' AND s.rank != 'deprecated'
          AND s.property_id = ? AND l.lexical_category_qid = ?
        GROUP BY s.value_qid ORDER BY COUNT(*) DESC, s.value_qid
        """,
        (property_id, category_qid),
    )
    return [
        (mappings.get(identifier, identifier or "novalue/somevalue"), int(count), int(lexemes))
        for identifier, count, lexemes in rows
    ]


def _duplicate_lemma_rows(
    connection: sqlite3.Connection, policy: FeaturePolicy
) -> list[tuple[str, int, int]]:
    result = []
    for qid, label in sorted(policy.lexical_categories.items(), key=lambda item: item[1]):
        groups, lexemes = connection.execute(
            """
            SELECT COUNT(*), COALESCE(SUM(group_size), 0) FROM (
              SELECT COUNT(*) AS group_size
              FROM lexeme l JOIN lemma m USING(lexeme_id)
              WHERE l.lexical_category_qid = ? AND m.language_tag = 'de'
              GROUP BY m.value HAVING COUNT(*) > 1
            )
            """,
            (qid,),
        ).fetchone()
        result.append((label, int(groups), int(lexemes)))
    return result


def _object_form_metrics(connection: sqlite3.Connection) -> dict[str, int]:
    targets: list[tuple[str | None, str | None]] = []
    rows = connection.execute(
        "SELECT s.value_json, q.value_json FROM qualifier q "
        "JOIN statement s USING(statement_rowid) "
        "WHERE s.property_id = ? AND q.property_id = ? ORDER BY q.statement_rowid",
        (COMPOUND_PROPERTY, OBJECT_FORM_PROPERTY),
    )
    for target_json, form_json in rows:
        target_value = json.loads(target_json) if target_json is not None else None
        form_value = json.loads(form_json) if form_json is not None else None
        target_id = target_value.get("id") if isinstance(target_value, dict) else None
        form_id = form_value.get("id") if isinstance(form_value, dict) else None
        targets.append(
            (
                target_id if isinstance(target_id, str) else None,
                form_id if isinstance(form_id, str) else None,
            )
        )
    resolved = 0
    wrong_owner = 0
    unresolved = 0
    for target_id, form_id in targets:
        owner = (
            connection.execute(
                "SELECT lexeme_id FROM form WHERE form_id = ?", (form_id,)
            ).fetchone()
            if form_id is not None
            else None
        )
        if target_id is None or owner is None:
            unresolved += 1
        elif owner[0] == target_id:
            resolved += 1
        else:
            wrong_owner += 1
    return {
        "qualifiers": len(targets),
        "resolved_forms": resolved,
        "wrong_owner": wrong_owner,
        "unresolved_or_malformed": unresolved,
    }


def _interpreted_markdown(
    connection: sqlite3.Connection,
    store_metadata: Mapping[str, Any],
    policy: FeaturePolicy,
    noun_profile: Mapping[str, Any],
    verb_profile: Mapping[str, Counter[str]],
    adjective_profile: Counter[str],
    adverb_profile: Counter[str],
    unknown_features: Sequence[tuple[str, str, str, str, int, int]],
) -> bytes:
    snapshot = store_metadata["snapshot"]
    source_counts = store_metadata["counts"]
    noun_qid = _inverse(policy.lexical_categories, "N")
    noun_metrics: Counter[str] = noun_profile["metrics"]
    category_coverage = [
        (
            "N",
            noun_metrics["total"],
            noun_metrics["total"] - noun_metrics["without_de_lemma"],
            noun_metrics["source_usable_single_gender"]
            + noun_metrics["source_usable_split_gender"],
        ),
        (
            "V",
            verb_profile["forms"]["total"],
            verb_profile["forms"]["with_de_lemma"],
            verb_profile["forms"]["source_usable_with_auxiliary"],
        ),
        (
            "A",
            adjective_profile["total"],
            adjective_profile["with_de_lemma"],
            adjective_profile["source_usable"],
        ),
        (
            "Adv",
            adverb_profile["total"],
            adverb_profile["with_de_lemma"],
            adverb_profile["source_usable"],
        ),
    ]
    gender_rows = _mapped_statement_distribution(
        connection,
        property_id=_inverse(policy.properties, "grammatical_gender"),
        category_qid=noun_qid,
        mappings=policy.statement_values,
    )
    restriction_rows = _mapped_statement_distribution(
        connection,
        property_id=_inverse(policy.properties, "instance_of"),
        category_qid=noun_qid,
        mappings=policy.statement_values,
    )
    paradigm_rows = _mapped_statement_distribution(
        connection,
        property_id=_inverse(policy.properties, "paradigm_class"),
        category_qid=noun_qid,
        mappings=policy.statement_values,
    )
    combining_qid = _inverse(policy.form_features, "combining_form")
    combining_rows = connection.execute(
        """
        SELECT r.language_tag, COUNT(*), COUNT(DISTINCT f.form_id),
               COUNT(DISTINCT f.lexeme_id), COUNT(DISTINCT r.value)
        FROM form_feature ff JOIN form f USING(form_id)
        JOIN form_representation r USING(form_id)
        WHERE ff.feature_qid = ?
        GROUP BY r.language_tag ORDER BY r.language_tag
        """,
        (combining_qid,),
    ).fetchall()
    combining_totals = {
        "forms": _count(
            connection,
            "SELECT COUNT(DISTINCT form_id) FROM form_feature WHERE feature_qid = ?",
            (combining_qid,),
        ),
        "lexemes": _count(
            connection,
            "SELECT COUNT(DISTINCT f.lexeme_id) FROM form_feature ff "
            "JOIN form f USING(form_id) WHERE ff.feature_qid = ?",
            (combining_qid,),
        ),
        "noun_forms": _count(
            connection,
            "SELECT COUNT(DISTINCT f.form_id) FROM form_feature ff "
            "JOIN form f USING(form_id) JOIN lexeme l USING(lexeme_id) "
            "WHERE ff.feature_qid = ? AND l.lexical_category_qid = ?",
            (combining_qid, noun_qid),
        ),
        "noun_lexemes": _count(
            connection,
            "SELECT COUNT(DISTINCT f.lexeme_id) FROM form_feature ff "
            "JOIN form f USING(form_id) JOIN lexeme l USING(lexeme_id) "
            "WHERE ff.feature_qid = ? AND l.lexical_category_qid = ?",
            (combining_qid, noun_qid),
        ),
    }
    compound = _compound_metrics(connection)
    object_forms = _object_form_metrics(connection)
    relevant_properties = {
        _inverse(policy.properties, label)
        for label in (
            "instance_of",
            "grammatical_gender",
            "word_stem",
            "combines_lexemes",
            "auxiliary_verb",
            "paradigm_class",
        )
    }
    placeholders = ",".join("?" for _ in relevant_properties)
    rank_rows = connection.execute(
        f"SELECT property_id, rank, COUNT(*) FROM statement "
        f"WHERE property_id IN ({placeholders}) "
        "GROUP BY property_id, rank ORDER BY property_id, rank",
        tuple(sorted(relevant_properties)),
    ).fetchall()
    sense_rows = connection.execute(
        f"SELECT property_id, COUNT(*) FROM statement WHERE subject_kind = 'sense' "
        f"AND property_id IN ({placeholders}) GROUP BY property_id ORDER BY property_id",
        tuple(sorted(relevant_properties)),
    ).fetchall()
    duplicate_rows = _duplicate_lemma_rows(connection, policy)
    spelling_rows = _spelling_rows(connection, policy)
    total_slots, exact_duplicate_slots, conflicting_slots = connection.execute(
        SLOT_DUPLICATE_QUERY
    ).fetchone()
    unknown_assignments = sum(row[4] for row in unknown_features)
    rejected_noun_assignments = sum(
        row[4] for row in unknown_features if row[2] == "rejected"
    )
    lines = [
        "# Interpreted German Wikidata Lexeme profile",
        "",
        "This interpretation applies only the reviewed mappings in `features.toml`",
        "to the semantically lossless source store. Counts are source evidence, not",
        "claims of linguistic correctness or acceptance into a GF dictionary.",
        "",
        "## Provenance and deterministic boundary",
        "",
        f"- Snapshot date: `{snapshot['dump_date']}`",
        f"- Snapshot SHA-256: `{snapshot['sha256']}`",
        f"- Exact entity-language selector: `{store_metadata['source_policy']['language_entity']}`",
        f"- Selected Lexemes: {source_counts['entities_selected']}",
        "- Historical German dictionaries used as inventory inputs: no",
        "- Normalization of retained source strings: none",
        "",
        "## Initial category coverage",
        "",
        *_table(["Category", "Lexemes", "With `de` lemma", "Profile-usable evidence"], category_coverage),
        "",
        "Profile-usable is category-specific and deliberately stricter than merely",
        "having a form: nouns need complete expected case/number slots and reviewed",
        "gender evidence; verbs need four principal-part signals and a recognized",
        "auxiliary; adjectives need three predicative degrees or an explicitly",
        "absolute positive; adverbs need a `de` lemma.",
        "",
        "## Noun source coverage",
        "",
        *_table(["Metric", "Lexemes"], _counter_rows(noun_metrics)),
        "",
        "Gender evidence status:",
        "",
        *_table(["Status", "Lexemes"], _counter_rows(noun_profile["gender"])),
        "",
        "Number-restriction status:",
        "",
        *_table(["Status", "Lexemes"], _counter_rows(noun_profile["restriction"])),
        "",
        "Non-deprecated gender statement values:",
        "",
        *_table(["Value", "Statements", "Lexemes"], gender_rows),
        "",
        "Non-deprecated `instance of` values on nouns (mapped values name number restrictions):",
        "",
        *_table(["Value", "Statements", "Lexemes"], restriction_rows[:30]),
        "",
        "Noun paradigm-class evidence:",
        "",
        *_table(["Value", "Statements", "Lexemes"], paradigm_rows),
        "",
        "Across all categories, source slots contain:",
        "",
        f"- {total_slots} Lexeme/tag/feature-bundle slots",
        f"- {exact_duplicate_slots or 0} exact duplicate slots",
        f"- {conflicting_slots or 0} conflicting-value slots",
        "",
        "## Combining-form and compound evidence",
        "",
        "Combining-form representations:",
        "",
        *_table(
            ["Tag", "Representations", "Forms", "Lexemes", "Distinct strings"],
            combining_rows,
        ),
        "",
        (
            "- All-category combining-form total: "
            f"{combining_totals['forms']} forms across "
            f"{combining_totals['lexemes']} Lexemes"
        ),
        (
            f"- Noun combining-form total: {combining_totals['noun_forms']} forms "
            f"across {combining_totals['noun_lexemes']} Lexemes"
        ),
        f"- `{COMPOUND_PROPERTY}` statements: {compound['statements']}",
        f"- Source Lexemes with compound evidence: {compound['source_lexemes']}",
        f"- Sources with multiple component statements: {compound['multi_component_sources']}",
        f"- Distinct component targets: {compound['distinct_targets']}",
        f"- Targets resolved inside the exact-Q188 store: {compound['resolved_targets']}",
        f"- Unresolved or malformed target statements: {compound['unresolved_target_statements']}",
        f"- `{SERIES_ORDINAL_PROPERTY}` ordering qualifiers: {compound['series_ordinal_qualifiers']}",
        f"- Fully ordered multi-component analyses: {compound['fully_ordered_analyses']}",
        f"- Partially ordered multi-component analyses: {compound['partially_ordered_analyses']}",
        f"- Duplicate-ordinal multi-component analyses: {compound['duplicate_ordinal_analyses']}",
        f"- Malformed-ordinal multi-component analyses: {compound['malformed_ordinal_analyses']}",
        f"- `{OBJECT_FORM_PROPERTY}` qualifiers: {object_forms['qualifiers']}",
        (
            f"- `{OBJECT_FORM_PROPERTY}` targets resolved to owned stored Forms: "
            f"{object_forms['resolved_forms']}"
        ),
        (
            f"- Stored `{OBJECT_FORM_PROPERTY}` targets owned by another Lexeme: "
            f"{object_forms['wrong_owner']}"
        ),
        (
            f"- Unresolved/malformed `{OBJECT_FORM_PROPERTY}` targets: "
            f"{object_forms['unresolved_or_malformed']}"
        ),
        "",
        "Ordering is classified once per source with multiple component statements.",
        "Fully ordered means exactly one canonical positive decimal ordinal per",
        "component and the complete sequence `1..N`; partially ordered means that",
        "some or all ordinals are absent but every present ordinal is valid and",
        "unique. Repeated ordinals form the duplicate bucket; invalid, ambiguous,",
        "or out-of-range ordinals form the malformed bucket.",
        "",
        "Combining forms and construction-specific object-form qualifiers remain",
        "separate evidence. Missing statements are not interpreted as atomicity.",
        "",
        "## Verb evidence",
        "",
        "Form coverage:",
        "",
        *_table(["Metric", "Lexemes"], _counter_rows(verb_profile["forms"])),
        "",
        "Auxiliary evidence:",
        "",
        *_table(["Status", "Lexemes"], _counter_rows(verb_profile["auxiliary"])),
        "",
        "Separability evidence:",
        "",
        *_table(["Status", "Lexemes"], _counter_rows(verb_profile["separability"])),
        "",
        "## Adjective and adverb evidence",
        "",
        "Adjectives:",
        "",
        *_table(["Metric", "Lexemes"], _counter_rows(adjective_profile)),
        "",
        "Adverbs:",
        "",
        *_table(["Metric", "Lexemes"], _counter_rows(adverb_profile)),
        "",
        "These categories are profiled only; fitting remains deferred.",
        "",
        "## Spelling profiles",
        "",
        *_table(
            ["Category", "`de` lemmas", "Whitespace", "Hyphen", "Digit", "All uppercase", "Non-NFC"],
            spelling_rows,
        ),
        "",
        "Strings are counted without rewriting or filtering them.",
        "",
        "## Ranks, correlations, and duplicate signals",
        "",
        "Ranks on projected morphology and compound properties:",
        "",
        *_table(["Property", "Rank", "Statements"], rank_rows),
        "",
        "Sense-specific statements on those properties:",
        "",
        *(_table(["Property", "Sense statements"], sense_rows) if sense_rows else ["None recorded."]),
        "",
        "Duplicate `de` lemma signals (diagnostic only; no merge is performed):",
        "",
        *_table(["Category", "Duplicate groups", "Lexemes in groups"], duplicate_rows),
        "",
        "## Rejection and quarantine accounting",
        "",
        f"- Entities rejected as malformed during full ingestion: 0",
        f"- Entities excluded by exact language selection: {source_counts['entities_excluded_language']}",
        f"- Nouns without a `de` lemma: {noun_metrics['without_de_lemma']}",
        f"- Nouns with partial slots: {noun_metrics['partial_slots']}",
        f"- Nouns with no recognized standalone slots: {noun_metrics['no_slots']}",
        f"- Nouns with conflicting slots: {noun_metrics['conflicting_slots']}",
        f"- Nouns with rejected rare form features: {noun_metrics['rejected_feature']}",
        f"- Nouns with a number-restriction conflict: {noun_metrics['restriction_conflict']}",
        f"- Nouns missing gender evidence: {noun_profile['gender']['missing']}",
        f"- Nouns with multiple gender values: {noun_profile['gender']['multiple']}",
        f"- Nouns with unknown/novalue gender evidence: {noun_profile['gender']['unknown_or_novalue']}",
        f"- Rejected noun-feature assignments: {rejected_noun_assignments}",
        f"- Deferred unknown feature assignments outside noun fitting: {unknown_assignments - rejected_noun_assignments}",
        "",
        "Every noun-category form feature in this snapshot is either mapped or",
        "explicitly rejected in `features.toml`; an unclassified noun feature is a",
        "hard profile error. `unknown-features.tsv` retains the rejected/deferred",
        "inventory. No source record is silently repaired or accepted.",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def generate_interpreted_profile(
    *,
    database_path: Path = DEFAULT_DATABASE,
    feature_policy_path: Path = DEFAULT_FEATURE_POLICY,
    output_dir: Path = DEFAULT_INTERPRETED_REPORT_DIR,
    expected_snapshot: Mapping[str, object] | None = None,
) -> list[ReportArtifact]:
    policy = load_feature_policy(feature_policy_path)
    connection = _connect(database_path)
    try:
        store_metadata = load_store_metadata(connection)
        _check_snapshot(store_metadata, expected_snapshot)
        noun_profile = _noun_profile(connection, policy)
        verb_profile = _verb_profile(connection, policy)
        adjective_profile = _adjective_profile(connection, policy)
        adverb_profile = _adverb_profile(connection, policy)
        unknown_features = _unknown_feature_rows(connection, policy)
        profile = _interpreted_markdown(
            connection,
            store_metadata,
            policy,
            noun_profile,
            verb_profile,
            adjective_profile,
            adverb_profile,
            unknown_features,
        )
        return [
            _write_bytes(output_dir / "profile.md", profile),
            _write_bytes(
                output_dir / "unknown-features.tsv",
                _tsv(
                    (
                        "lexical_category_qid",
                        "feature_qid",
                        "status",
                        "reason",
                        "assignments",
                        "lexemes",
                    ),
                    unknown_features,
                ),
            ),
        ]
    finally:
        connection.close()
