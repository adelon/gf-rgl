from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from wd2gf.store import (
    SourcePolicy,
    StoreError,
    canonical_entity,
    ingest_dump,
    iter_dump,
    source_store_fingerprint,
    validate_entity,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/synthetic"
SNAPSHOT = {"sha256": "f" * 64, "dump_date": "2026-07-29"}


class StoreTests(unittest.TestCase):
    def test_array_envelope_and_unicode_are_preserved(self) -> None:
        entities = list(iter_dump(FIXTURES / "valid-array.json"))
        self.assertEqual([entity["id"] for entity in entities], ["L1", "L2", "L3"])
        self.assertEqual(
            entities[0]["lemmas"]["de"]["value"], 'Straße \\"Nord\\"\\n😀'
        )
        for entity in entities:
            validate_entity(entity)

    def test_canonical_entity_is_key_order_independent(self) -> None:
        first = {"b": "ä", "a": [2, 1]}
        second = {"a": [2, 1], "b": "ä"}
        self.assertEqual(canonical_entity(first), canonical_entity(second))
        payload, digest = canonical_entity(first)
        self.assertEqual(payload, '{"a":[2,1],"b":"ä"}')
        self.assertEqual(len(digest), 64)

    def test_malformed_inputs_are_rejected(self) -> None:
        with self.assertRaisesRegex(StoreError, "malformed JSON"):
            list(iter_dump(FIXTURES / "malformed-json.json"))
        malformed_entity = list(iter_dump(FIXTURES / "malformed-entity.json"))[0]
        with self.assertRaisesRegex(StoreError, "missing required"):
            validate_entity(malformed_entity)
        with self.assertRaisesRegex(StoreError, "trailing comma"):
            list(iter_dump(FIXTURES / "trailing-comma.json"))

    def test_ingestion_selects_entity_language_exactly_and_is_lossless(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "source.sqlite3"
            stats = ingest_dump(
                dump_path=FIXTURES / "valid-array.json",
                database_path=database,
                source_policy=SourcePolicy("Q188", "exact"),
                snapshot_metadata=SNAPSHOT,
            )
            self.assertEqual(stats.entities_before_selection, 3)
            self.assertEqual(stats.lexemes_validated, 3)
            self.assertEqual(stats.entities_selected, 2)
            self.assertEqual(stats.entities_excluded_language, 1)
            with sqlite3.connect(database) as connection:
                self.assertEqual(
                    connection.execute(
                        "SELECT lexeme_id FROM lexeme ORDER BY lexeme_id"
                    ).fetchall(),
                    [("L1",), ("L3",)],
                )
                canonical = connection.execute(
                    "SELECT canonical_json FROM lexeme WHERE lexeme_id = 'L1'"
                ).fetchone()[0]
                original = list(iter_dump(FIXTURES / "valid-array.json"))[0]
                self.assertEqual(json.loads(canonical), original)
                self.assertEqual(
                    connection.execute(
                        "SELECT language_tag FROM lemma WHERE lexeme_id = 'L1' "
                        "ORDER BY language_tag"
                    ).fetchall(),
                    [("de",), ("de-ch",)],
                )
                self.assertEqual(
                    connection.execute(
                        "SELECT feature_qid FROM form_feature ORDER BY feature_qid"
                    ).fetchall(),
                    [
                        ("Q110786",),
                        ("Q131105",),
                        ("Q131105",),
                        ("Q146786",),
                        ("Q146786",),
                        ("Q146786",),
                    ],
                )
                self.assertEqual(
                    connection.execute(
                        "SELECT property_id, rank, value_qid FROM statement "
                        "ORDER BY property_id, value_qid"
                    ).fetchall(),
                    [
                        ("P5137", "normal", "Q1"),
                        ("P5185", "preferred", "Q1775415"),
                        ("P5185", "normal", "Q1775415"),
                        ("P5185", "normal", "Q1775461"),
                    ],
                )
                self.assertEqual(
                    connection.execute(
                        "SELECT property_id, value_json FROM qualifier"
                    ).fetchall(),
                    [("P1545", '"1"')],
                )
            with self.assertRaisesRegex(StoreError, "refusing to replace"):
                ingest_dump(
                    dump_path=FIXTURES / "valid-array.json",
                    database_path=database,
                    source_policy=SourcePolicy("Q188", "exact"),
                    snapshot_metadata=SNAPSHOT,
                )
            fingerprint = source_store_fingerprint(database)
            self.assertEqual(fingerprint["schema_version"], 1)
            self.assertEqual(fingerprint["table_counts"]["lexeme"], 2)
            self.assertEqual(fingerprint["table_counts"]["form"], 4)
            self.assertEqual(len(fingerprint["selected_entity_hashes_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
