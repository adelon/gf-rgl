from __future__ import annotations

import unittest

from tests.noun_test_support import pinned_sample, synthetic_nouns
from wd2gf.nouns_ger import (
    DEFAULT_NOUN_POLICY,
    STRATA,
    load_noun_policy,
    noun_sample_bytes,
)


class NounSamplingTests(unittest.TestCase):
    def test_ranked_candidates_and_strata_are_deterministic(self) -> None:
        with synthetic_nouns() as fixture:
            self.assertEqual(fixture.first, fixture.second)
            candidates = fixture.candidates
            self.assertEqual(
                [gender.value for gender in candidates["L1"].genders], ["feminine"]
            )
            expected = {
                "L2": "plural_only",
                "L3": "singular_only",
                "L4": "explicit_combining",
                "L5": "multiple_gender",
                "L6": "conflicting_slots",
                "L7": "hyphenated",
                "L8": "partial_evidence",
                "L9": "rejected_feature",
                "L10": "ambiguous_combining",
                "L11": "multiword",
                "L12": "abbreviation",
                "L13": "irregular_full",
                "L14": "invariant",
                "L15": "invariant_plural",
            }
            self.assertEqual(
                {key: candidates[key].stratum for key in expected}, expected
            )
            self.assertEqual(
                noun_sample_bytes(fixture.first, fixture.policy),
                noun_sample_bytes(fixture.second, fixture.policy),
            )

    def test_pinned_dump_nouns_are_forced_into_the_sample(self) -> None:
        policy, sample = pinned_sample()
        self.assertEqual(
            {item.candidate.source_key for item in sample if item.pinned},
            set(policy.pinned_lexemes),
        )
        self.assertTrue(all(item.internal_id.startswith("wdn_") for item in sample))

    def test_policy_freezes_all_strata(self) -> None:
        policy = load_noun_policy(DEFAULT_NOUN_POLICY)
        self.assertEqual(set(policy.quotas), set(STRATA))
        self.assertEqual(policy.singular_only_policy, "residual-api-gap")
        self.assertIn("P5548", policy.combining_form_policy)
        self.assertEqual(
            set(policy.acceptance_tiers),
            {
                "automatic_complete_with_co",
                "automatic_complete",
                "review_required_provisional",
                "excluded",
            },
        )
        self.assertEqual(policy.reviewed_productive_co_rules, ())
        self.assertEqual(policy.unlisted_derived_co_policy, "provisional")
        self.assertEqual(
            policy.uncorrelated_multi_gender_policy, "reject-unresolved"
        )


if __name__ == "__main__":
    unittest.main()
