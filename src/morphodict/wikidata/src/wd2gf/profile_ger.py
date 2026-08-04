"""Raw and interpreted German source profiles."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import tempfile
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
COMBINING_FORM = "Q107614077"
COMPOUND_PROPERTY = "P5238"
PARADIGM_CLASS_PROPERTY = "P5911"
SERIES_ORDINAL_PROPERTY = "P1545"
OBJECT_FORM_PROPERTY = "P5548"


class ProfileError(RuntimeError):
    """The profile cannot be derived from the source store."""


@dataclass(frozen=True)
class ReportArtifact:
    path: Path
    sha256: str
    size_bytes: int


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
    return {
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
        f"- `{COMBINING_FORM}` forms: {combining['forms']} across {combining['lexemes']} Lexemes",
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
        f"- `{OBJECT_FORM_PROPERTY}` qualifiers on compound statements: {compound['object_form_qualifiers']}",
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
