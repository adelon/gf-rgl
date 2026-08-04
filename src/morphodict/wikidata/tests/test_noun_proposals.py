from __future__ import annotations

import unittest
from dataclasses import replace

from tests.noun_test_support import synthetic_nouns
from wd2gf.nouns_ger import (
    ADJECTIVAL_DECLENSION_QID,
    AbbrevN,
    ClaimEvidence,
    PROBE_FIELDS,
    PluralOnlyN,
    SourceCompleteness,
    proposal_blocker,
    proposals_for_candidate,
    render_proposal_modules,
    unfitted_candidate_reason,
)


class NounProposalTests(unittest.TestCase):
    def test_proposal_taxonomy_and_rendering_are_frozen(self) -> None:
        with synthetic_nouns() as fixture:
            sampled = fixture.sampled
            candidates = fixture.candidates
            plural = proposals_for_candidate(sampled["L2"], fixture.policy)
            self.assertTrue(any(isinstance(x.proposal, PluralOnlyN) for x in plural))
            self.assertEqual(
                proposal_blocker(candidates["L3"]),
                "residual_api_gap_singular_only",
            )
            self.assertEqual(
                proposal_blocker(candidates["L5"]),
                "unresolved_multiple_gender_alternatives",
            )
            adjectival = replace(
                candidates["L13"],
                paradigm_claims=(
                    ClaimEvidence(
                        1,
                        "L13$P5911-adjectival",
                        "normal",
                        ADJECTIVAL_DECLENSION_QID,
                    ),
                ),
            )
            self.assertEqual(
                unfitted_candidate_reason(adjectival),
                "category_mismatch_adjectival_declension",
            )
            self.assertEqual(
                unfitted_candidate_reason(
                    replace(candidates["L13"], genders=(), gender_claims=())
                ),
                "source_evidence_gap_missing_gender",
            )
            self.assertEqual(
                unfitted_candidate_reason(
                    replace(
                        candidates["L2"],
                        slots=(),
                        source_completeness=SourceCompleteness.NONE,
                    )
                ),
                "source_evidence_gap_missing_required_forms",
            )
            abbreviation = proposals_for_candidate(sampled["L12"], fixture.policy)
            self.assertTrue(abbreviation)
            self.assertTrue(all(isinstance(x.proposal, AbbrevN) for x in abbreviation))

            options, artifacts = render_proposal_modules(
                fixture.first, fixture.policy, fixture.root / "rendered"
            )
            self.assertTrue(options)
            self.assertEqual(len(artifacts), 3)
            concrete = (fixture.root / "rendered/WdnPilotGer.gf").read_text()
            self.assertIn("probe_record", concrete)
            for field in PROBE_FIELDS:
                self.assertIn(f"{field} : Str", concrete)
            first_render = [artifact.path.read_bytes() for artifact in artifacts]
            _, repeated = render_proposal_modules(
                fixture.first, fixture.policy, fixture.root / "repeated"
            )
            self.assertEqual(
                first_render, [artifact.path.read_bytes() for artifact in repeated]
            )


if __name__ == "__main__":
    unittest.main()
