from __future__ import annotations

import unittest

from tests.noun_test_support import synthetic_nouns
from wd2gf.nouns_ger import PROBE_FIELDS, proposals_for_candidate
from wd2gf.probe_ger import (
    CandidateFit,
    ProbeRecord,
    compare_record,
    noun_fit_bytes,
    noun_rejections_bytes,
)


class NounReportingTests(unittest.TestCase):
    def test_fit_and_rejection_reports_keep_quality_axes_separate(self) -> None:
        with synthetic_nouns() as fixture:
            plural_sample = fixture.sampled["L2"]
            plural_option = proposals_for_candidate(plural_sample, fixture.policy)[0]
            values = {field: "" for field in PROBE_FIELDS}
            for field in ("s_pl_nom", "s_pl_acc", "s_pl_dat", "s_pl_gen"):
                values[field] = "Kosten"
            for field in (
                "uncap_s_pl_nom",
                "uncap_s_pl_acc",
                "uncap_s_pl_dat",
                "uncap_s_pl_gen",
            ):
                values[field] = "kosten"
            values.update(
                {
                    "gender": "masculine",
                    "co": "Kosten",
                    "uncap_co": "kosten",
                    "csep": "bind",
                }
            )
            comparison = compare_record(
                plural_sample.candidate,
                plural_option,
                ProbeRecord(
                    plural_option.option_id,
                    1,
                    tuple((field, values[field]) for field in PROBE_FIELDS),
                ),
            )
            fit_report = noun_fit_bytes(
                (CandidateFit(plural_sample, comparison, None, 1, 1),), "a" * 64
            ).decode()
            fit_header, fit_row = fit_report.splitlines()
            self.assertIn("gf_s_sg_nom_json", fit_header.split("\t"))
            self.assertIn("complete_record_comparison", fit_header.split("\t"))
            self.assertIn('"s_sg_nom":"unavailable"', fit_row)
            self.assertIn('\t""\t', fit_row)

            rejection_report = noun_rejections_bytes(
                (
                    CandidateFit(
                        fixture.sampled["L3"],
                        None,
                        "residual_api_gap_singular_only",
                        0,
                        0,
                    ),
                )
            ).decode()
            rejection_header, rejection_row = rejection_report.splitlines()
            self.assertIn("residual_api_gap", rejection_header.split("\t"))
            self.assertIn(
                "missing_public_singular_only_noun_constructor", rejection_row
            )


if __name__ == "__main__":
    unittest.main()
