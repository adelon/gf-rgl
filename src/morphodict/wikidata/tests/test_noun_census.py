from __future__ import annotations

import unittest

from tests.noun_test_support import SNAPSHOT, synthetic_nouns
from wd2gf.census_ger import generate_noun_census


class NounCensusTests(unittest.TestCase):
    def test_compile_free_census_is_deterministic_and_placement_neutral(self) -> None:
        with synthetic_nouns() as fixture:
            first = generate_noun_census(
                database_path=fixture.database,
                report_path=fixture.root / "census.md",
                details_path=fixture.root / "census.tsv",
                expected_snapshot=SNAPSHOT,
            )
            second = generate_noun_census(
                database_path=fixture.database,
                report_path=fixture.root / "repeat.md",
                details_path=fixture.root / "repeat.tsv",
                expected_snapshot=SNAPSHOT,
            )
            self.assertEqual(first.total_candidates, 15)
            self.assertEqual(first.report.sha256, second.report.sha256)
            self.assertEqual(first.details.sha256, second.details.sha256)
            self.assertEqual(first.report.path.read_bytes(), second.report.path.read_bytes())
            self.assertEqual(
                first.details.path.read_bytes(), second.details.path.read_bytes()
            )
            report = first.report.path.read_text(encoding="utf-8")
            self.assertIn("GF compilations performed: `0`", report)
            self.assertIn("internal_structure_unresolved", report)
            self.assertIn("unresolved_multiple_gender_alternatives", report)
            self.assertNotIn("estimated atomic", report)


if __name__ == "__main__":
    unittest.main()
