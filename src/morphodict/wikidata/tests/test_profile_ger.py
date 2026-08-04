from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from wd2gf.profile_ger import (
    DEFAULT_FEATURE_POLICY,
    _compound_metrics,
    _object_form_metrics,
    extract_pinned_fixture,
    generate_interpreted_profile,
    generate_raw_profile,
)
from wd2gf.store import SourcePolicy, ingest_dump


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/synthetic/valid-array.json"
SNAPSHOT = {"sha256": "f" * 64, "dump_date": "2026-07-29"}


def _entity_value(identifier: str, entity_type: str) -> dict[str, object]:
    return {
        "snaktype": "value",
        "datatype": f"wikibase-{entity_type}",
        "datavalue": {
            "value": {"entity-type": entity_type, "id": identifier},
            "type": "wikibase-entityid",
        },
    }


def _qualifier_value(property_id: str, value: str) -> dict[str, object]:
    return {
        "snaktype": "value",
        "property": property_id,
        "datatype": "string",
        "datavalue": {"value": value, "type": "string"},
    }


def _compound_statement(
    target_id: str,
    *,
    ordinal: str | None = None,
    object_form_id: str | None = None,
) -> dict[str, object]:
    qualifiers: dict[str, list[dict[str, object]]] = {}
    if ordinal is not None:
        qualifiers["P1545"] = [_qualifier_value("P1545", ordinal)]
    if object_form_id is not None:
        qualifiers["P5548"] = [_entity_value(object_form_id, "form")]
    mainsnak = _entity_value(target_id, "lexeme")
    mainsnak["property"] = "P5238"
    return {
        "rank": "normal",
        "mainsnak": mainsnak,
        "qualifiers": qualifiers,
        "references": [],
    }


def _lexeme(
    lexeme_id: str,
    *,
    statements: list[dict[str, object]] | None = None,
    form_id: str | None = None,
) -> dict[str, object]:
    forms = []
    if form_id is not None:
        forms.append(
            {
                "id": form_id,
                "representations": {"de": {"language": "de", "value": form_id}},
                "grammaticalFeatures": [],
                "claims": {},
            }
        )
    return {
        "type": "lexeme",
        "id": lexeme_id,
        "lemmas": {"de": {"language": "de", "value": lexeme_id}},
        "lexicalCategory": "Q1084",
        "language": "Q188",
        "claims": {"P5238": statements} if statements is not None else {},
        "forms": forms,
        "senses": [],
    }


def _write_compound_fixture(path: Path) -> None:
    entities = [
        _lexeme("L10", form_id="L10-F1"),
        _lexeme("L20", form_id="L20-F1"),
        _lexeme(
            "L100",
            statements=[
                _compound_statement("L10", ordinal="1", object_form_id="L10-F1"),
                _compound_statement("L20", ordinal="2", object_form_id="L10-F1"),
            ],
        ),
        _lexeme(
            "L101",
            statements=[
                _compound_statement("L10", ordinal="1"),
                _compound_statement("L20", object_form_id="L20-F99"),
            ],
        ),
        _lexeme(
            "L102",
            statements=[
                _compound_statement("L10", ordinal="1"),
                _compound_statement("L20", ordinal="1"),
            ],
        ),
        _lexeme(
            "L103",
            statements=[
                _compound_statement("L10", ordinal="1"),
                _compound_statement("L20", ordinal="not-an-ordinal"),
            ],
        ),
        _lexeme(
            "L104",
            statements=[
                _compound_statement("L10"),
                _compound_statement("L20"),
            ],
        ),
        _lexeme(
            "L105",
            statements=[
                _compound_statement("L10", ordinal="3"),
                _compound_statement("L20"),
            ],
        ),
    ]
    path.write_text(
        "[\n" + ",\n".join(json.dumps(entity) for entity in entities) + "\n]\n",
        encoding="utf-8",
    )


class RawProfileTests(unittest.TestCase):
    def test_compound_ordering_and_object_form_ownership(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = root / "compound.json"
            database = root / "source.sqlite3"
            _write_compound_fixture(fixture)
            ingest_dump(
                dump_path=fixture,
                database_path=database,
                source_policy=SourcePolicy("Q188", "exact"),
                snapshot_metadata=SNAPSHOT,
            )
            with sqlite3.connect(database) as connection:
                compound = _compound_metrics(connection)
                object_forms = _object_form_metrics(connection)

            self.assertEqual(compound["multi_component_sources"], 6)
            self.assertEqual(compound["fully_ordered_analyses"], 1)
            self.assertEqual(compound["partially_ordered_analyses"], 2)
            self.assertEqual(compound["duplicate_ordinal_analyses"], 1)
            self.assertEqual(compound["malformed_ordinal_analyses"], 2)
            self.assertEqual(
                sum(
                    compound[key]
                    for key in (
                        "fully_ordered_analyses",
                        "partially_ordered_analyses",
                        "duplicate_ordinal_analyses",
                        "malformed_ordinal_analyses",
                    )
                ),
                compound["multi_component_sources"],
            )
            self.assertEqual(
                object_forms,
                {
                    "qualifiers": 3,
                    "resolved_forms": 1,
                    "wrong_owner": 1,
                    "unresolved_or_malformed": 1,
                },
            )
            generate_raw_profile(
                database_path=database,
                output_dir=root / "raw",
                expected_snapshot=SNAPSHOT,
            )
            generate_interpreted_profile(
                database_path=database,
                feature_policy_path=DEFAULT_FEATURE_POLICY,
                output_dir=root / "interpreted",
                expected_snapshot=SNAPSHOT,
            )
            raw_profile = (root / "raw/raw-profile.md").read_text(encoding="utf-8")
            self.assertIn("Fully ordered multi-component analyses: 1", raw_profile)
            self.assertIn("Partially ordered multi-component analyses: 2", raw_profile)
            self.assertIn("Duplicate-ordinal multi-component analyses: 1", raw_profile)
            self.assertIn("Malformed-ordinal multi-component analyses: 2", raw_profile)
            interpreted_profile = (root / "interpreted/profile.md").read_text(
                encoding="utf-8"
            )
            self.assertIn(
                "`P5548` targets resolved to owned stored Forms: 1",
                interpreted_profile,
            )
            self.assertIn(
                "Stored `P5548` targets owned by another Lexeme: 1",
                interpreted_profile,
            )
            self.assertIn(
                "Unresolved/malformed `P5548` targets: 1", interpreted_profile
            )

    def test_raw_reports_are_deterministic_and_source_id_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            database = root / "source.sqlite3"
            ingest_dump(
                dump_path=FIXTURE,
                database_path=database,
                source_policy=SourcePolicy("Q188", "exact"),
                snapshot_metadata=SNAPSHOT,
            )
            first = generate_raw_profile(
                database_path=database,
                output_dir=root / "first",
                expected_snapshot=SNAPSHOT,
            )
            second = generate_raw_profile(
                database_path=database,
                output_dir=root / "second",
                expected_snapshot=SNAPSHOT,
            )
            self.assertEqual(
                [(artifact.path.name, artifact.sha256, artifact.size_bytes) for artifact in first],
                [(artifact.path.name, artifact.sha256, artifact.size_bytes) for artifact in second],
            )
            for first_artifact, second_artifact in zip(first, second, strict=True):
                self.assertEqual(
                    first_artifact.path.read_bytes(), second_artifact.path.read_bytes()
                )
            profile = (root / "first/raw-profile.md").read_text(encoding="utf-8")
            self.assertIn("Selected entities: 2", profile)
            self.assertIn("`Q107614077` forms (all categories): 0", profile)
            inventory = (root / "first/raw-inventory.tsv").read_text(encoding="utf-8")
            self.assertIn("qid\tlexical_category\tQ1084\t2\t2", inventory)
            self.assertIn("property\tstatement\tP5185\t3\t2", inventory)

    def test_pinned_fixture_retains_complete_canonical_entities(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            database = root / "source.sqlite3"
            ingest_dump(
                dump_path=FIXTURE,
                database_path=database,
                source_policy=SourcePolicy("Q188", "exact"),
                snapshot_metadata=SNAPSHOT,
            )
            selection = root / "selection.tsv"
            selection.write_text(
                "lexeme_id\treason\nL3\tconflicting synthetic forms\nL1\tUnicode and qualifiers\n",
                encoding="utf-8",
            )
            first = extract_pinned_fixture(
                database_path=database,
                selection_path=selection,
                output_dir=root / "first",
                expected_snapshot=SNAPSHOT,
            )
            second = extract_pinned_fixture(
                database_path=database,
                selection_path=selection,
                output_dir=root / "second",
                expected_snapshot=SNAPSHOT,
            )
            self.assertEqual(
                [(artifact.path.name, artifact.sha256) for artifact in first],
                [(artifact.path.name, artifact.sha256) for artifact in second],
            )
            fixture = json.loads((root / "first/lexemes.json").read_text(encoding="utf-8"))
            self.assertEqual([entity["id"] for entity in fixture], ["L1", "L3"])
            self.assertIn("qualifiers", fixture[0]["claims"]["P5185"][0])

    def test_interpreted_profile_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            database = root / "source.sqlite3"
            ingest_dump(
                dump_path=FIXTURE,
                database_path=database,
                source_policy=SourcePolicy("Q188", "exact"),
                snapshot_metadata=SNAPSHOT,
            )
            first = generate_interpreted_profile(
                database_path=database,
                feature_policy_path=DEFAULT_FEATURE_POLICY,
                output_dir=root / "first",
                expected_snapshot=SNAPSHOT,
            )
            second = generate_interpreted_profile(
                database_path=database,
                feature_policy_path=DEFAULT_FEATURE_POLICY,
                output_dir=root / "second",
                expected_snapshot=SNAPSHOT,
            )
            self.assertEqual(
                [(artifact.path.name, artifact.sha256) for artifact in first],
                [(artifact.path.name, artifact.sha256) for artifact in second],
            )
            profile = (root / "first/profile.md").read_text(encoding="utf-8")
            self.assertIn("| N | 2 | 2 | 0 |", profile)
            self.assertIn("Historical German dictionaries used as inventory inputs: no", profile)
            self.assertEqual(
                (root / "first/unknown-features.tsv").read_text(encoding="utf-8"),
                "lexical_category_qid\tfeature_qid\tstatus\treason\tassignments\tlexemes\n",
            )


if __name__ == "__main__":
    unittest.main()
