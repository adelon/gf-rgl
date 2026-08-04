"""Streaming source ingestion and semantically lossless SQLite storage."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import sqlite3
import tempfile
import tomllib
from collections.abc import Callable, Iterator, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, TextIO


SCHEMA_VERSION = 1
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE = PROJECT_ROOT / ".work/german-lexemes.sqlite3"
DEFAULT_SOURCE_POLICY = PROJECT_ROOT / "languages/ger/source.toml"
QID_PATTERN = re.compile(r"^Q[1-9]\d*$")
PID_PATTERN = re.compile(r"^P[1-9]\d*$")
LEXEME_ID_PATTERN = re.compile(r"^L[1-9]\d*$")
FORM_ID_PATTERN = re.compile(r"^L[1-9]\d*-F[1-9]\d*$")
SENSE_ID_PATTERN = re.compile(r"^L[1-9]\d*-S[1-9]\d*$")
RANKS = {"preferred", "normal", "deprecated"}


class StoreError(RuntimeError):
    """The dump or source-store contract was violated."""


@dataclass(frozen=True)
class SourcePolicy:
    language_entity: str
    selection: str


@dataclass
class IngestStats:
    entities_before_selection: int = 0
    lexemes_validated: int = 0
    entities_selected: int = 0
    entities_excluded_language: int = 0
    selected_lemmas: int = 0
    selected_forms: int = 0
    selected_form_representations: int = 0
    selected_form_features: int = 0
    selected_senses: int = 0
    selected_statements: int = 0
    selected_qualifiers: int = 0


def load_source_policy(path: Path = DEFAULT_SOURCE_POLICY) -> SourcePolicy:
    try:
        with path.open("rb") as policy_file:
            data = tomllib.load(policy_file)
    except FileNotFoundError as error:
        raise StoreError(f"missing source policy: {path}") from error
    expected = {"schema_version", "language_entity", "selection"}
    if set(data) != expected or data["schema_version"] != 1:
        raise StoreError("unsupported German source policy schema")
    if not isinstance(data["language_entity"], str) or not QID_PATTERN.fullmatch(
        data["language_entity"]
    ):
        raise StoreError("source policy language_entity must be a QID")
    if data["selection"] != "exact":
        raise StoreError("the only supported entity-language selection is exact")
    return SourcePolicy(data["language_entity"], data["selection"])


def _no_duplicate_object_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise StoreError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise StoreError(f"non-standard JSON number: {value}")


def decode_entity(source: str, *, line_number: int) -> dict[str, Any]:
    try:
        entity = json.loads(
            source,
            object_pairs_hook=_no_duplicate_object_keys,
            parse_constant=_reject_nonfinite,
        )
    except StoreError:
        raise
    except json.JSONDecodeError as error:
        raise StoreError(f"malformed JSON entity on line {line_number}: {error}") from error
    if not isinstance(entity, dict):
        raise StoreError(f"entity on line {line_number} is not a JSON object")
    return entity


def iter_json_array(stream: TextIO) -> Iterator[dict[str, Any]]:
    opened = False
    closed = False
    entity_count = 0
    previous_had_comma = False
    for line_number, raw_line in enumerate(stream, start=1):
        stripped = raw_line.strip()
        if not stripped:
            continue
        if not opened:
            if stripped != "[":
                raise StoreError("dump must begin with a standalone JSON-array opening bracket")
            opened = True
            continue
        if closed:
            raise StoreError(f"content after JSON-array closing bracket on line {line_number}")
        if stripped == "]":
            if entity_count and previous_had_comma:
                raise StoreError("JSON array has a trailing comma")
            closed = True
            continue
        if entity_count and not previous_had_comma:
            raise StoreError(f"missing inter-object comma before line {line_number}")
        previous_had_comma = stripped.endswith(",")
        entity_source = stripped[:-1].rstrip() if previous_had_comma else stripped
        if not entity_source:
            raise StoreError(f"missing entity object on line {line_number}")
        yield decode_entity(entity_source, line_number=line_number)
        entity_count += 1
    if not opened:
        raise StoreError("dump is empty and has no JSON-array envelope")
    if not closed:
        raise StoreError("dump has no JSON-array closing bracket")


def iter_dump(path: Path) -> Iterator[dict[str, Any]]:
    try:
        if path.suffix == ".gz":
            with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
                yield from iter_json_array(stream)
        else:
            with path.open("r", encoding="utf-8", newline="") as stream:
                yield from iter_json_array(stream)
    except (OSError, UnicodeDecodeError) as error:
        raise StoreError(f"could not stream dump {path}: {error}") from error


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as error:
        raise StoreError(f"value is not canonicalizable JSON: {error}") from error


def canonical_entity(entity: Mapping[str, Any]) -> tuple[str, str]:
    payload = canonical_json(entity)
    return payload, hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _require_mapping(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise StoreError(f"{context} must be an object")
    return value


def _require_list(value: Any, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise StoreError(f"{context} must be an array")
    return value


def _representations(value: Any, context: str) -> dict[str, dict[str, str]]:
    mapping = _require_mapping(value, context)
    result: dict[str, dict[str, str]] = {}
    for language_tag, raw_representation in mapping.items():
        if not isinstance(language_tag, str) or not language_tag:
            raise StoreError(f"{context} has an invalid representation tag")
        representation = _require_mapping(
            raw_representation, f"{context}[{language_tag!r}]"
        )
        if set(representation) != {"language", "value"}:
            raise StoreError(
                f"{context}[{language_tag!r}] must contain only language and value"
            )
        if not all(isinstance(representation[key], str) for key in representation):
            raise StoreError(f"{context}[{language_tag!r}] fields must be strings")
        result[language_tag] = representation
    return result


def _claims(value: Any, context: str) -> dict[str, list[dict[str, Any]]]:
    mapping = _require_mapping(value, context)
    result: dict[str, list[dict[str, Any]]] = {}
    for property_id, raw_statements in mapping.items():
        if not isinstance(property_id, str) or not PID_PATTERN.fullmatch(property_id):
            raise StoreError(f"{context} has invalid property ID {property_id!r}")
        statements = _require_list(raw_statements, f"{context}.{property_id}")
        result[property_id] = [
            _require_mapping(statement, f"{context}.{property_id}[{index}]")
            for index, statement in enumerate(statements)
        ]
    return result


def validate_entity(entity: dict[str, Any]) -> None:
    required = {
        "type",
        "id",
        "lemmas",
        "lexicalCategory",
        "language",
        "claims",
        "forms",
        "senses",
    }
    missing = sorted(required - set(entity))
    if missing:
        raise StoreError(f"Lexeme entity is missing required fields: {missing}")
    if entity["type"] != "lexeme":
        raise StoreError(f"unexpected entity type: {entity['type']!r}")
    if not isinstance(entity["id"], str) or not LEXEME_ID_PATTERN.fullmatch(entity["id"]):
        raise StoreError(f"invalid Lexeme ID: {entity['id']!r}")
    for field in ("language", "lexicalCategory"):
        if not isinstance(entity[field], str) or not QID_PATTERN.fullmatch(entity[field]):
            raise StoreError(f"invalid {field} QID on {entity['id']}")
    _representations(entity["lemmas"], f"{entity['id']}.lemmas")
    _claims(entity["claims"], f"{entity['id']}.claims")

    forms = _require_list(entity["forms"], f"{entity['id']}.forms")
    seen_forms: set[str] = set()
    for position, raw_form in enumerate(forms):
        form = _require_mapping(raw_form, f"{entity['id']}.forms[{position}]")
        required_form = {"id", "representations", "grammaticalFeatures", "claims"}
        missing_form = sorted(required_form - set(form))
        if missing_form:
            raise StoreError(f"form on {entity['id']} is missing fields: {missing_form}")
        form_id = form["id"]
        if not isinstance(form_id, str) or not FORM_ID_PATTERN.fullmatch(form_id):
            raise StoreError(f"invalid Form ID on {entity['id']}: {form_id!r}")
        if form_id.split("-F", 1)[0] != entity["id"]:
            raise StoreError(f"Form ID belongs to another Lexeme: {form_id}")
        if form_id in seen_forms:
            raise StoreError(f"duplicate Form ID on {entity['id']}: {form_id}")
        seen_forms.add(form_id)
        _representations(form["representations"], f"{form_id}.representations")
        features = _require_list(form["grammaticalFeatures"], f"{form_id}.features")
        if any(not isinstance(feature, str) or not QID_PATTERN.fullmatch(feature) for feature in features):
            raise StoreError(f"invalid grammatical feature on {form_id}")
        _claims(form["claims"], f"{form_id}.claims")

    senses = _require_list(entity["senses"], f"{entity['id']}.senses")
    seen_senses: set[str] = set()
    for position, raw_sense in enumerate(senses):
        sense = _require_mapping(raw_sense, f"{entity['id']}.senses[{position}]")
        required_sense = {"id", "glosses", "claims"}
        missing_sense = sorted(required_sense - set(sense))
        if missing_sense:
            raise StoreError(f"sense on {entity['id']} is missing fields: {missing_sense}")
        sense_id = sense["id"]
        if not isinstance(sense_id, str) or not SENSE_ID_PATTERN.fullmatch(sense_id):
            raise StoreError(f"invalid Sense ID on {entity['id']}: {sense_id!r}")
        if sense_id.split("-S", 1)[0] != entity["id"]:
            raise StoreError(f"Sense ID belongs to another Lexeme: {sense_id}")
        if sense_id in seen_senses:
            raise StoreError(f"duplicate Sense ID on {entity['id']}: {sense_id}")
        seen_senses.add(sense_id)
        _representations(sense["glosses"], f"{sense_id}.glosses")
        _claims(sense["claims"], f"{sense_id}.claims")


SCHEMA = """
PRAGMA user_version = 1;
PRAGMA foreign_keys = ON;
CREATE TABLE metadata (
  key TEXT PRIMARY KEY,
  value_json TEXT NOT NULL
) WITHOUT ROWID;
CREATE TABLE lexeme (
  lexeme_id TEXT PRIMARY KEY,
  language_qid TEXT NOT NULL,
  lexical_category_qid TEXT NOT NULL,
  revision_id INTEGER,
  modified TEXT,
  entity_sha256 TEXT NOT NULL UNIQUE,
  canonical_json TEXT NOT NULL
) WITHOUT ROWID;
CREATE TABLE lemma (
  lexeme_id TEXT NOT NULL REFERENCES lexeme(lexeme_id),
  language_tag TEXT NOT NULL,
  representation_language TEXT NOT NULL,
  value TEXT NOT NULL,
  PRIMARY KEY (lexeme_id, language_tag)
) WITHOUT ROWID;
CREATE TABLE form (
  form_id TEXT PRIMARY KEY,
  lexeme_id TEXT NOT NULL REFERENCES lexeme(lexeme_id),
  position INTEGER NOT NULL,
  UNIQUE (lexeme_id, position)
);
CREATE TABLE form_representation (
  form_id TEXT NOT NULL REFERENCES form(form_id),
  language_tag TEXT NOT NULL,
  representation_language TEXT NOT NULL,
  value TEXT NOT NULL,
  PRIMARY KEY (form_id, language_tag)
) WITHOUT ROWID;
CREATE TABLE form_feature (
  form_id TEXT NOT NULL REFERENCES form(form_id),
  position INTEGER NOT NULL,
  feature_qid TEXT NOT NULL,
  PRIMARY KEY (form_id, position)
) WITHOUT ROWID;
CREATE TABLE sense (
  sense_id TEXT PRIMARY KEY,
  lexeme_id TEXT NOT NULL REFERENCES lexeme(lexeme_id),
  position INTEGER NOT NULL,
  UNIQUE (lexeme_id, position)
);
CREATE TABLE sense_gloss (
  sense_id TEXT NOT NULL REFERENCES sense(sense_id),
  language_tag TEXT NOT NULL,
  representation_language TEXT NOT NULL,
  value TEXT NOT NULL,
  PRIMARY KEY (sense_id, language_tag)
) WITHOUT ROWID;
CREATE TABLE statement (
  statement_rowid INTEGER PRIMARY KEY,
  subject_kind TEXT NOT NULL CHECK (subject_kind IN ('lexeme', 'form', 'sense')),
  subject_id TEXT NOT NULL,
  property_id TEXT NOT NULL,
  position INTEGER NOT NULL,
  statement_id TEXT,
  rank TEXT NOT NULL CHECK (rank IN ('preferred', 'normal', 'deprecated')),
  snaktype TEXT NOT NULL,
  datatype TEXT,
  value_qid TEXT,
  value_json TEXT,
  qualifiers_json TEXT NOT NULL,
  references_json TEXT NOT NULL,
  statement_json TEXT NOT NULL,
  UNIQUE (subject_kind, subject_id, property_id, position)
);
CREATE TABLE qualifier (
  statement_rowid INTEGER NOT NULL REFERENCES statement(statement_rowid),
  property_id TEXT NOT NULL,
  position INTEGER NOT NULL,
  snaktype TEXT NOT NULL,
  datatype TEXT,
  value_qid TEXT,
  value_json TEXT,
  qualifier_json TEXT NOT NULL,
  PRIMARY KEY (statement_rowid, property_id, position)
) WITHOUT ROWID;
"""


INDEXES = """
CREATE INDEX lexeme_language_category ON lexeme(language_qid, lexical_category_qid);
CREATE INDEX lemma_language_tag ON lemma(language_tag);
CREATE INDEX form_representation_language_tag ON form_representation(language_tag);
CREATE INDEX form_feature_qid ON form_feature(feature_qid, form_id);
CREATE INDEX statement_property_rank ON statement(property_id, rank);
CREATE INDEX statement_value_qid ON statement(value_qid, property_id);
CREATE INDEX statement_subject ON statement(subject_kind, subject_id);
CREATE INDEX qualifier_property ON qualifier(property_id, statement_rowid);
CREATE INDEX qualifier_value_qid ON qualifier(value_qid, property_id);
"""


def _value_projection(snak: dict[str, Any]) -> tuple[str | None, str | None]:
    if "datavalue" not in snak:
        return None, None
    datavalue = _require_mapping(snak["datavalue"], "snak.datavalue")
    if "value" not in datavalue:
        raise StoreError("snak.datavalue is missing value")
    value = datavalue["value"]
    value_qid: str | None = None
    if isinstance(value, dict):
        candidate = value.get("id")
        if isinstance(candidate, str) and QID_PATTERN.fullmatch(candidate):
            value_qid = candidate
    return value_qid, canonical_json(value)


def _insert_representations(
    connection: sqlite3.Connection,
    *,
    table: str,
    owner_column: str,
    owner_id: str,
    representations: dict[str, dict[str, str]],
) -> int:
    rows = [
        (owner_id, language_tag, representation["language"], representation["value"])
        for language_tag, representation in sorted(representations.items())
    ]
    connection.executemany(
        f"INSERT INTO {table} ({owner_column}, language_tag, representation_language, value) "
        "VALUES (?, ?, ?, ?)",
        rows,
    )
    return len(rows)


def _insert_claims(
    connection: sqlite3.Connection,
    *,
    subject_kind: str,
    subject_id: str,
    claims: dict[str, list[dict[str, Any]]],
) -> tuple[int, int]:
    statement_count = 0
    qualifier_count = 0
    for property_id in sorted(claims):
        for position, statement in enumerate(claims[property_id]):
            rank = statement.get("rank")
            if rank not in RANKS:
                raise StoreError(f"invalid statement rank on {subject_id}: {rank!r}")
            mainsnak = _require_mapping(statement.get("mainsnak"), "statement.mainsnak")
            snaktype = mainsnak.get("snaktype")
            if not isinstance(snaktype, str):
                raise StoreError(f"invalid statement snaktype on {subject_id}")
            snak_property = mainsnak.get("property")
            if snak_property is not None and snak_property != property_id:
                raise StoreError(f"statement property mismatch on {subject_id}")
            datatype = mainsnak.get("datatype")
            if datatype is not None and not isinstance(datatype, str):
                raise StoreError(f"invalid statement datatype on {subject_id}")
            value_qid, value_json = _value_projection(mainsnak)
            qualifiers = _require_mapping(statement.get("qualifiers", {}), "qualifiers")
            references = _require_list(statement.get("references", []), "references")
            statement_id = statement.get("id")
            if statement_id is not None and not isinstance(statement_id, str):
                raise StoreError(f"invalid statement ID on {subject_id}")
            cursor = connection.execute(
                """
                INSERT INTO statement (
                  subject_kind, subject_id, property_id, position, statement_id,
                  rank, snaktype, datatype, value_qid, value_json,
                  qualifiers_json, references_json, statement_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    subject_kind,
                    subject_id,
                    property_id,
                    position,
                    statement_id,
                    rank,
                    snaktype,
                    datatype,
                    value_qid,
                    value_json,
                    canonical_json(qualifiers),
                    canonical_json(references),
                    canonical_json(statement),
                ),
            )
            statement_rowid = cursor.lastrowid
            if statement_rowid is None:
                raise StoreError("SQLite did not assign a statement row ID")
            statement_count += 1
            for qualifier_property in sorted(qualifiers):
                if not PID_PATTERN.fullmatch(qualifier_property):
                    raise StoreError(f"invalid qualifier property: {qualifier_property!r}")
                snaks = _require_list(
                    qualifiers[qualifier_property], f"qualifier {qualifier_property}"
                )
                for qualifier_position, raw_qualifier in enumerate(snaks):
                    qualifier = _require_mapping(raw_qualifier, "qualifier snak")
                    qualifier_snaktype = qualifier.get("snaktype")
                    if not isinstance(qualifier_snaktype, str):
                        raise StoreError("invalid qualifier snaktype")
                    qualifier_datatype = qualifier.get("datatype")
                    if qualifier_datatype is not None and not isinstance(
                        qualifier_datatype, str
                    ):
                        raise StoreError("invalid qualifier datatype")
                    qualifier_qid, qualifier_value = _value_projection(qualifier)
                    connection.execute(
                        """
                        INSERT INTO qualifier (
                          statement_rowid, property_id, position, snaktype, datatype,
                          value_qid, value_json, qualifier_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            statement_rowid,
                            qualifier_property,
                            qualifier_position,
                            qualifier_snaktype,
                            qualifier_datatype,
                            qualifier_qid,
                            qualifier_value,
                            canonical_json(qualifier),
                        ),
                    )
                    qualifier_count += 1
    return statement_count, qualifier_count


def _insert_entity(
    connection: sqlite3.Connection, entity: dict[str, Any], stats: IngestStats
) -> None:
    lexeme_id = entity["id"]
    payload, entity_sha256 = canonical_entity(entity)
    revision_id = entity.get("lastrevid")
    if revision_id is not None and not isinstance(revision_id, int):
        raise StoreError(f"lastrevid on {lexeme_id} must be an integer")
    modified = entity.get("modified")
    if modified is not None and not isinstance(modified, str):
        raise StoreError(f"modified on {lexeme_id} must be a string")
    connection.execute(
        """
        INSERT INTO lexeme (
          lexeme_id, language_qid, lexical_category_qid, revision_id, modified,
          entity_sha256, canonical_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            lexeme_id,
            entity["language"],
            entity["lexicalCategory"],
            revision_id,
            modified,
            entity_sha256,
            payload,
        ),
    )
    lemmas = _representations(entity["lemmas"], f"{lexeme_id}.lemmas")
    stats.selected_lemmas += _insert_representations(
        connection,
        table="lemma",
        owner_column="lexeme_id",
        owner_id=lexeme_id,
        representations=lemmas,
    )
    statement_count, qualifier_count = _insert_claims(
        connection,
        subject_kind="lexeme",
        subject_id=lexeme_id,
        claims=_claims(entity["claims"], f"{lexeme_id}.claims"),
    )
    stats.selected_statements += statement_count
    stats.selected_qualifiers += qualifier_count

    for form_position, raw_form in enumerate(entity["forms"]):
        form = _require_mapping(raw_form, f"{lexeme_id}.forms[{form_position}]")
        form_id = form["id"]
        connection.execute(
            "INSERT INTO form (form_id, lexeme_id, position) VALUES (?, ?, ?)",
            (form_id, lexeme_id, form_position),
        )
        stats.selected_forms += 1
        representations = _representations(
            form["representations"], f"{form_id}.representations"
        )
        stats.selected_form_representations += _insert_representations(
            connection,
            table="form_representation",
            owner_column="form_id",
            owner_id=form_id,
            representations=representations,
        )
        features = _require_list(form["grammaticalFeatures"], f"{form_id}.features")
        connection.executemany(
            "INSERT INTO form_feature (form_id, position, feature_qid) VALUES (?, ?, ?)",
            [(form_id, position, feature) for position, feature in enumerate(features)],
        )
        stats.selected_form_features += len(features)
        statement_count, qualifier_count = _insert_claims(
            connection,
            subject_kind="form",
            subject_id=form_id,
            claims=_claims(form["claims"], f"{form_id}.claims"),
        )
        stats.selected_statements += statement_count
        stats.selected_qualifiers += qualifier_count

    for sense_position, raw_sense in enumerate(entity["senses"]):
        sense = _require_mapping(raw_sense, f"{lexeme_id}.senses[{sense_position}]")
        sense_id = sense["id"]
        connection.execute(
            "INSERT INTO sense (sense_id, lexeme_id, position) VALUES (?, ?, ?)",
            (sense_id, lexeme_id, sense_position),
        )
        stats.selected_senses += 1
        _insert_representations(
            connection,
            table="sense_gloss",
            owner_column="sense_id",
            owner_id=sense_id,
            representations=_representations(sense["glosses"], f"{sense_id}.glosses"),
        )
        statement_count, qualifier_count = _insert_claims(
            connection,
            subject_kind="sense",
            subject_id=sense_id,
            claims=_claims(sense["claims"], f"{sense_id}.claims"),
        )
        stats.selected_statements += statement_count
        stats.selected_qualifiers += qualifier_count


def _cleanup_sqlite(path: Path) -> None:
    path.unlink(missing_ok=True)
    Path(f"{path}-journal").unlink(missing_ok=True)
    Path(f"{path}-shm").unlink(missing_ok=True)
    Path(f"{path}-wal").unlink(missing_ok=True)


def ingest_dump(
    *,
    dump_path: Path,
    database_path: Path = DEFAULT_DATABASE,
    source_policy: SourcePolicy,
    snapshot_metadata: Mapping[str, object],
    progress: Callable[[IngestStats], None] | None = None,
    progress_every: int = 100_000,
) -> IngestStats:
    if database_path.exists():
        raise StoreError(f"refusing to replace existing database: {database_path}")
    if progress_every <= 0:
        raise StoreError("progress_every must be positive")
    database_path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        dir=database_path.parent, prefix=f".{database_path.name}.", suffix=".part"
    )
    os.close(file_descriptor)
    temporary_path = Path(temporary_name)
    temporary_path.unlink()
    connection: sqlite3.Connection | None = None
    stats = IngestStats()
    try:
        connection = sqlite3.connect(temporary_path)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = DELETE")
        connection.execute("PRAGMA synchronous = FULL")
        connection.executescript(SCHEMA)
        for entity in iter_dump(dump_path):
            stats.entities_before_selection += 1
            validate_entity(entity)
            stats.lexemes_validated += 1
            if entity["language"] != source_policy.language_entity:
                stats.entities_excluded_language += 1
            else:
                _insert_entity(connection, entity, stats)
                stats.entities_selected += 1
                if stats.entities_selected % 10_000 == 0:
                    connection.commit()
            if progress is not None and stats.entities_before_selection % progress_every == 0:
                progress(stats)
        metadata = {
            "schema_version": SCHEMA_VERSION,
            "source_policy": asdict(source_policy),
            "snapshot": dict(snapshot_metadata),
            "counts": asdict(stats),
        }
        connection.executemany(
            "INSERT INTO metadata (key, value_json) VALUES (?, ?)",
            [(key, canonical_json(value)) for key, value in sorted(metadata.items())],
        )
        connection.executescript(INDEXES)
        connection.execute("ANALYZE")
        connection.commit()
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        if integrity != ("ok",):
            raise StoreError(f"SQLite integrity check failed: {integrity}")
        connection.close()
        connection = None
        os.replace(temporary_path, database_path)
    except BaseException:
        if connection is not None:
            connection.close()
        _cleanup_sqlite(temporary_path)
        raise
    return stats


def source_store_fingerprint(database_path: Path = DEFAULT_DATABASE) -> dict[str, object]:
    if not database_path.is_file():
        raise StoreError(f"source database does not exist: {database_path}")
    connection = sqlite3.connect(f"file:{database_path}?mode=ro", uri=True)
    try:
        user_version = connection.execute("PRAGMA user_version").fetchone()[0]
        if user_version != SCHEMA_VERSION:
            raise StoreError(
                f"incompatible source database schema {user_version}; expected {SCHEMA_VERSION}"
            )
        table_counts = {
            table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table in (
                "lexeme",
                "lemma",
                "form",
                "form_representation",
                "form_feature",
                "sense",
                "sense_gloss",
                "statement",
                "qualifier",
            )
        }
        entity_hashes = hashlib.sha256()
        for lexeme_id, entity_sha256 in connection.execute(
            "SELECT lexeme_id, entity_sha256 FROM lexeme ORDER BY lexeme_id"
        ):
            entity_hashes.update(lexeme_id.encode("ascii"))
            entity_hashes.update(b"\t")
            entity_hashes.update(entity_sha256.encode("ascii"))
            entity_hashes.update(b"\n")
        metadata = {
            key: json.loads(value_json)
            for key, value_json in connection.execute(
                "SELECT key, value_json FROM metadata ORDER BY key"
            )
        }
        return {
            "schema_version": user_version,
            "table_counts": table_counts,
            "selected_entity_hashes_sha256": entity_hashes.hexdigest(),
            "metadata_sha256": hashlib.sha256(
                canonical_json(metadata).encode("utf-8")
            ).hexdigest(),
        }
    finally:
        connection.close()
