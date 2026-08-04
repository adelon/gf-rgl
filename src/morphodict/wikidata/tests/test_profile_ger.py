from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from wd2gf.profile_ger import extract_pinned_fixture, generate_raw_profile
from wd2gf.store import SourcePolicy, ingest_dump


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/synthetic/valid-array.json"
SNAPSHOT = {"sha256": "f" * 64, "dump_date": "2026-07-29"}


class RawProfileTests(unittest.TestCase):
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
            self.assertIn("`Q107614077` forms: 0", profile)
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


if __name__ == "__main__":
    unittest.main()
