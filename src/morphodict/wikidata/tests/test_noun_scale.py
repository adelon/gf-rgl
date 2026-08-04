from __future__ import annotations

import os
import unittest
from dataclasses import replace
from pathlib import Path

from tests.noun_test_support import synthetic_nouns
from wd2gf.census_ger import (
    AcceptanceTier,
    CensusClassification,
    CompoundConfidence,
    GenderCorrelation,
    StructuralCohort,
)
from wd2gf.nouns_ger import NounError, proposals_for_candidate, render_option_modules
from wd2gf.scale_ger import (
    SelectedCandidate,
    _compile_bridge,
    _retain,
    _selected,
    fit_in_chunks,
    load_scale_policy,
    proportional_quotas,
    verify_scale_repeat,
)


class NounScaleTests(unittest.TestCase):
    def test_first_gate_policy_and_quota_allocation_are_frozen(self) -> None:
        policy = load_scale_policy()
        self.assertEqual(policy.authorized_scale_points, (5000,))
        self.assertEqual(policy.next_scale_point, 25000)
        self.assertEqual(policy.fitting_chunk_size, 500)
        quotas = proportional_quotas({"large": 90, "small": 10, "tiny": 1}, 20, 1)
        self.assertEqual(sum(quotas.values()), 20)
        self.assertEqual(quotas["tiny"], 1)
        self.assertGreaterEqual(quotas["small"], 1)
        self.assertLessEqual(quotas["large"], 90)

    def test_ranked_selection_is_order_independent(self) -> None:
        classification = CensusClassification(
            AcceptanceTier.AUTOMATIC_COMPLETE,
            "",
            CompoundConfidence.PROVISIONAL_DERIVED,
            StructuralCohort.OPAQUE_ACCEPTED_LEXEME,
            GenderCorrelation.NOT_MULTIPLE,
        )
        with synthetic_nouns() as fixture:
            candidates = tuple(item.candidate for item in fixture.first[:8])
            selections = []
            for values in (candidates, tuple(reversed(candidates))):
                heaps = {}
                for candidate in values:
                    _retain(
                        heaps,
                        stratum="eligible",
                        quota=4,
                        seed="scale-test",
                        candidate=candidate,
                        classification=classification,
                    )
                selections.append(
                    tuple(
                        item.sampled.candidate.source_key
                        for item in _selected(heaps, "scale-test", "wdf")
                    )
                )
            self.assertEqual(selections[0], selections[1])
            self.assertEqual(len(selections[0]), 4)

    def test_result_renderer_accepts_one_preselected_option(self) -> None:
        with synthetic_nouns() as fixture:
            options = proposals_for_candidate(fixture.first[0], fixture.policy)
            selected = options[-1:]
            artifacts = render_option_modules(selected, fixture.root / "selected")
            self.assertEqual(len(artifacts), 3)
            concrete = (fixture.root / "selected/WdnPilotGer.gf").read_text()
            self.assertIn(selected[0].expression, concrete)
            for unselected in options[:-1]:
                self.assertNotIn(f"  {unselected.function_id} =", concrete)
            manifest = (fixture.root / "selected/proposal-manifest.tsv").read_text()
            self.assertEqual(len(manifest.splitlines()), 2)

    def test_repeat_verifier_checks_only_semantic_scale_artifacts(self) -> None:
        with synthetic_nouns() as fixture:
            primary = fixture.root / "primary"
            repeated = fixture.root / "repeated"
            names = (
                "semantic-summary.json",
                "fitting-selection.tsv",
                "fitting-results.json",
                "result-selection-pool.tsv",
                "result-selection-results.json",
                "result-selection.tsv",
                "result-records.json",
            )
            for directory in (primary, repeated):
                directory.mkdir()
                for name in names:
                    (directory / name).write_text(f"{name}\n")
                (directory / "measurements.json").write_text(str(directory))
            self.assertEqual(len(verify_scale_repeat(primary, repeated)), len(names))
            (repeated / "result-records.json").write_text("changed\n")
            with self.assertRaisesRegex(NounError, "changed deterministic artifacts"):
                verify_scale_repeat(primary, repeated)

    @unittest.skipUnless(
        os.environ.get("GF_INTEGRATION"), "set GF_INTEGRATION for GF/Haskell check"
    )
    def test_chunked_fitter_uses_structured_haskell_bridge(self) -> None:
        classification = CensusClassification(
            AcceptanceTier.REVIEW_REQUIRED_PROVISIONAL,
            "",
            CompoundConfidence.PROVISIONAL_DERIVED,
            StructuralCohort.OPAQUE_ACCEPTED_LEXEME,
            GenderCorrelation.NOT_MULTIPLE,
        )
        with synthetic_nouns() as fixture:
            selected = tuple(
                SelectedCandidate(item, classification, "synthetic")
                for item in fixture.first
            )
            policy = replace(load_scale_policy(), fitting_chunk_size=5)
            gf_path = Path(os.environ["GF"])
            binary, _ = _compile_bridge(gf_path, fixture.root / "bridge")
            run = fit_in_chunks(
                selected=selected,
                noun_policy=fixture.policy,
                scale_policy=policy,
                gf_path=gf_path,
                probe_binary=binary,
                work_dir=fixture.root / "chunks",
                workload="synthetic",
            )
            self.assertEqual(len(run.fits), len(selected))
            self.assertEqual(len(run.probe_artifacts), 3)
            self.assertTrue(all(artifact.size_bytes > 0 for artifact in run.probe_artifacts))


if __name__ == "__main__":
    unittest.main()
