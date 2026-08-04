from __future__ import annotations

import json
import unittest
from dataclasses import replace

from tests.noun_test_support import synthetic_nouns
from wd2gf.nouns_ger import PROBE_FIELDS, proposals_for_candidate
from wd2gf.probe_ger import (
    FieldEvidence,
    ProbeRecord,
    compare_record,
    decode_probe,
    fit_candidates,
)


class NounProbeTests(unittest.TestCase):
    def test_structured_decode_and_complete_record_comparison(self) -> None:
        with synthetic_nouns() as fixture:
            plural_sample = fixture.sampled["L2"]
            plural_options = proposals_for_candidate(plural_sample, fixture.policy)
            first_option = plural_options[0]
            lines = [
                "candidate_id\toption_id\tfunction_id\tvariant_index\tfield\tvalue_json"
            ]
            lines.extend(
                "\t".join(
                    (
                        first_option.candidate_id,
                        first_option.option_id,
                        first_option.function_id,
                        "1",
                        field,
                        json.dumps(field),
                    )
                )
                for field in PROBE_FIELDS
            )
            decoded = decode_probe(
                ("\n".join(lines) + "\n").encode(), (first_option,)
            )
            self.assertEqual(len(decoded[first_option.option_id]), 1)

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
                first_option,
                ProbeRecord(
                    first_option.option_id,
                    1,
                    tuple((field, values[field]) for field in PROBE_FIELDS),
                ),
            )
            self.assertEqual(comparison.mismatches, ())
            evidence = dict(comparison.field_evidence)
            self.assertEqual(evidence["s_sg_nom"], FieldEvidence.UNAVAILABLE)
            self.assertEqual(
                evidence["uncap_s_sg_nom"], FieldEvidence.UNAVAILABLE
            )

    def test_least_explicit_fit_keeps_coherent_variants(self) -> None:
        with synthetic_nouns() as fixture:
            sample = fixture.sampled["L14"]
            options = proposals_for_candidate(sample, fixture.policy)
            self.assertEqual(
                [option.explicit_form_arguments for option in options],
                sorted(option.explicit_form_arguments for option in options),
            )
            values = {
                field: (
                    "feminine"
                    if field == "gender"
                    else "bind"
                    if field == "csep"
                    else "jeans"
                    if field.startswith("uncap_")
                    else "Jeans"
                )
                for field in PROBE_FIELDS
            }
            records = {
                option.option_id: (
                    ProbeRecord(
                        option.option_id,
                        1,
                        tuple((field, values[field]) for field in PROBE_FIELDS),
                    ),
                )
                for option in options
            }
            fit = fit_candidates((sample,), options, records)[0]
            self.assertEqual(fit.accepted.option.option_id, options[0].option_id)

            ambiguous = {
                option.option_id: (
                    outcome[0],
                    replace(
                        outcome[0],
                        variant_index=2,
                        values=tuple(
                            (field, "JEANS" if field == "co" else value)
                            for field, value in outcome[0].values
                        ),
                    ),
                )
                for option, outcome in (
                    (option, records[option.option_id]) for option in options
                )
            }
            fit = fit_candidates((sample,), options, ambiguous)[0]
            self.assertIsNone(fit.accepted)
            self.assertEqual(fit.rejection_reason, "ambiguous_gf_record_variants")


if __name__ == "__main__":
    unittest.main()
