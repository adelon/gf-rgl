from __future__ import annotations

import sys
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PolicyTests(unittest.TestCase):
    def test_python_version(self) -> None:
        self.assertGreaterEqual(sys.version_info, (3, 11))

    def test_exact_german_source_policy(self) -> None:
        with (ROOT / "languages/ger/source.toml").open("rb") as source_file:
            policy = tomllib.load(source_file)
        self.assertEqual(
            policy,
            {"schema_version": 1, "language_entity": "Q188", "selection": "exact"},
        )

    def test_features_policy_freezes_reviewed_german_core(self) -> None:
        with (ROOT / "languages/ger/features.toml").open("rb") as features_file:
            policy = tomllib.load(features_file)
        self.assertEqual(policy["schema_version"], 1)
        self.assertEqual(
            policy["lexical_categories"],
            {"Q1084": "N", "Q24905": "V", "Q34698": "A", "Q380057": "Adv"},
        )
        self.assertEqual(policy["form_features"]["Q107614077"], "combining_form")
        self.assertEqual(policy["properties"]["P5238"], "combines_lexemes")
        self.assertEqual(policy["properties"]["P5911"], "paradigm_class")
        self.assertEqual(policy["rejected_noun_form_features"]["Q56352306"], "outside reviewed noun form model")


if __name__ == "__main__":
    unittest.main()
