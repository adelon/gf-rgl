from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from wd2gf.nouns_ger import (
    AbbrevN,
    DEFAULT_NOUN_POLICY,
    PROBE_FIELDS,
    PluralOnlyN,
    STRATA,
    load_noun_policy,
    noun_sample_bytes,
    proposal_blocker,
    proposals_for_candidate,
    render_proposal_modules,
    select_noun_sample,
)
from wd2gf.profile_ger import DEFAULT_FEATURE_POLICY, load_feature_policy
from wd2gf.probe_ger import (
    FieldEvidence,
    ProbeRecord,
    compare_record,
    decode_probe,
)
from wd2gf.store import SourcePolicy, ingest_dump


ROOT = Path(__file__).resolve().parents[1]
PINNED = ROOT / "languages/ger/fixtures/pinned/lexemes.json"
SNAPSHOT = {"sha256": "e" * 64, "dump_date": "2026-07-29"}

FEATURES = {
    "sg": "Q110786",
    "pl": "Q146786",
    "nom": "Q131105",
    "acc": "Q146078",
    "dat": "Q145599",
    "gen": "Q146233",
}
GENDERS = {
    "masculine": "Q499327",
    "feminine": "Q1775415",
    "neuter": "Q1775461",
}


def _entity_snak(property_id: str, identifier: str) -> dict[str, object]:
    return {
        "snaktype": "value",
        "property": property_id,
        "datatype": "wikibase-item",
        "datavalue": {
            "value": {"entity-type": "item", "id": identifier},
            "type": "wikibase-entityid",
        },
    }


def _statement(
    lexeme_id: str, property_id: str, identifier: str, rank: str = "normal"
) -> dict[str, object]:
    return {
        "id": f"{lexeme_id}${property_id}-{identifier}-{rank}",
        "rank": rank,
        "mainsnak": _entity_snak(property_id, identifier),
        "references": [],
    }


def _forms(
    lexeme_id: str,
    values: dict[str, str],
    *,
    combining: tuple[str, ...] = (),
    rejected: bool = False,
) -> list[dict[str, object]]:
    result = []
    for index, field in enumerate(
        (
            "s_sg_nom",
            "s_sg_acc",
            "s_sg_dat",
            "s_sg_gen",
            "s_pl_nom",
            "s_pl_acc",
            "s_pl_dat",
            "s_pl_gen",
        ),
        start=1,
    ):
        if field not in values:
            continue
        _, number, case = field.split("_")
        features = [FEATURES[number], FEATURES[case]]
        if rejected and index == 1:
            features.append("Q7977953")
        result.append(
            {
                "id": f"{lexeme_id}-F{index}",
                "representations": {
                    "de": {"language": "de", "value": values[field]}
                },
                "grammaticalFeatures": features,
                "claims": {},
            }
        )
    for offset, value in enumerate(combining, start=20):
        result.append(
            {
                "id": f"{lexeme_id}-F{offset}",
                "representations": {"de": {"language": "de", "value": value}},
                "grammaticalFeatures": ["Q107614077"],
                "claims": {},
            }
        )
    return result


def _lexeme(
    lexeme_id: str,
    lemma: str,
    values: dict[str, str],
    *,
    genders: tuple[tuple[str, str], ...] = (("masculine", "normal"),),
    restriction: str | None = None,
    combining: tuple[str, ...] = (),
    rejected: bool = False,
) -> dict[str, object]:
    claims: dict[str, list[dict[str, object]]] = {}
    if genders:
        claims["P5185"] = [
            _statement(lexeme_id, "P5185", GENDERS[gender], rank)
            for gender, rank in genders
        ]
    if restriction is not None:
        restriction_id = {
            "plural_only": "Q138246",
            "singular_only": "Q604984",
        }[restriction]
        claims["P31"] = [_statement(lexeme_id, "P31", restriction_id)]
    return {
        "type": "lexeme",
        "id": lexeme_id,
        "lemmas": {"de": {"language": "de", "value": lemma}},
        "lexicalCategory": "Q1084",
        "language": "Q188",
        "claims": claims,
        "forms": _forms(
            lexeme_id, values, combining=combining, rejected=rejected
        ),
        "senses": [],
    }


def _complete(sg: str, gen: str, pl: str, pl_dat: str) -> dict[str, str]:
    return {
        "s_sg_nom": sg,
        "s_sg_acc": sg,
        "s_sg_dat": sg,
        "s_sg_gen": gen,
        "s_pl_nom": pl,
        "s_pl_acc": pl,
        "s_pl_dat": pl_dat,
        "s_pl_gen": pl,
    }


def _write_fixture(path: Path) -> None:
    singular = {
        "s_sg_nom": "Milch",
        "s_sg_acc": "Milch",
        "s_sg_dat": "Milch",
        "s_sg_gen": "Milch",
    }
    plural = {
        "s_pl_nom": "Kosten",
        "s_pl_acc": "Kosten",
        "s_pl_dat": "Kosten",
        "s_pl_gen": "Kosten",
    }
    conflict = _complete("Band", "Bands", "Bänder", "Bändern")
    entities = [
        _lexeme(
            "L1",
            "Stufe",
            _complete("Stufe", "Stufe", "Stufen", "Stufen"),
            genders=(("masculine", "normal"), ("feminine", "preferred")),
        ),
        _lexeme("L2", "Kosten", plural, genders=(), restriction="plural_only"),
        _lexeme("L3", "Milch", singular, restriction="singular_only"),
        _lexeme(
            "L4",
            "Tisch",
            _complete("Tisch", "Tisches", "Tische", "Tischen"),
            combining=("Tisch",),
        ),
        _lexeme(
            "L5",
            "Band",
            _complete("Band", "Bands", "Bänder", "Bändern"),
            genders=(("masculine", "normal"), ("neuter", "normal")),
        ),
        _lexeme("L6", "AG", _complete("AG", "AG", "AGs", "AGs")),
        _lexeme(
            "L7",
            "E-Mail",
            _complete("E-Mail", "E-Mail", "E-Mails", "E-Mails"),
            genders=(("feminine", "normal"),),
        ),
        _lexeme(
            "L8",
            "Rest",
            {"s_sg_nom": "Rest"},
            genders=(("masculine", "normal"),),
        ),
        _lexeme(
            "L9",
            "Signal",
            _complete("Signal", "Signals", "Signale", "Signalen"),
            rejected=True,
        ),
        _lexeme(
            "L10",
            "Doppel",
            _complete("Doppel", "Doppels", "Doppel", "Doppeln"),
            combining=("Doppel", "Doppels"),
        ),
        _lexeme(
            "L11",
            "mehr Wort",
            _complete("mehr Wort", "mehr Worts", "mehr Worte", "mehr Worten"),
        ),
        _lexeme(
            "L12",
            "USA",
            _complete("USA", "USA", "USAs", "USAs"),
            genders=(("neuter", "normal"),),
        ),
        _lexeme(
            "L13",
            "Herz",
            {
                "s_sg_nom": "Herz",
                "s_sg_acc": "Herz",
                "s_sg_dat": "Herzen",
                "s_sg_gen": "Herzens",
                "s_pl_nom": "Herzen",
                "s_pl_acc": "Herzen",
                "s_pl_dat": "Herzen",
                "s_pl_gen": "Herzen",
            },
            genders=(("neuter", "normal"),),
        ),
        _lexeme(
            "L14",
            "Jeans",
            {field: "Jeans" for field in (
                "s_sg_nom", "s_sg_acc", "s_sg_dat", "s_sg_gen",
                "s_pl_nom", "s_pl_acc", "s_pl_dat", "s_pl_gen",
            )},
            genders=(("feminine", "normal"),),
        ),
        _lexeme(
            "L15",
            "Auto",
            _complete("Auto", "Autos", "Autos", "Autos"),
            genders=(("neuter", "normal"),),
        ),
    ]
    # A second distinct value for one L6 slot exercises conflict detection.
    entities[5]["forms"].append(
        {
            "id": "L6-F30",
            "representations": {"de": {"language": "de", "value": "AGen"}},
            "grammaticalFeatures": [FEATURES["sg"], FEATURES["nom"]],
            "claims": {},
        }
    )
    path.write_text(
        "[\n" + ",\n".join(json.dumps(entity) for entity in entities) + "\n]\n",
        encoding="utf-8",
    )


class NounCandidateTests(unittest.TestCase):
    def test_ranked_candidates_and_strata_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = root / "nouns.json"
            database = root / "source.sqlite3"
            _write_fixture(fixture)
            ingest_dump(
                dump_path=fixture,
                database_path=database,
                source_policy=SourcePolicy("Q188", "exact"),
                snapshot_metadata=SNAPSHOT,
            )
            noun_policy = replace(load_noun_policy(), pinned_lexemes=())
            feature_policy = load_feature_policy(DEFAULT_FEATURE_POLICY)
            with sqlite3.connect(database) as connection:
                first = select_noun_sample(connection, noun_policy, feature_policy)
                second = select_noun_sample(connection, noun_policy, feature_policy)

            self.assertEqual(first, second)
            by_source = {sample.candidate.source_key: sample.candidate for sample in first}
            self.assertEqual(
                [gender.value for gender in by_source["L1"].genders], ["feminine"]
            )
            self.assertEqual(by_source["L2"].stratum, "plural_only")
            self.assertEqual(by_source["L3"].stratum, "singular_only")
            self.assertEqual(by_source["L4"].stratum, "explicit_combining")
            self.assertEqual(by_source["L5"].stratum, "multiple_gender")
            self.assertEqual(by_source["L6"].stratum, "conflicting_slots")
            self.assertEqual(by_source["L7"].stratum, "hyphenated")
            self.assertEqual(by_source["L8"].stratum, "partial_evidence")
            self.assertEqual(by_source["L9"].stratum, "rejected_feature")
            self.assertEqual(by_source["L10"].stratum, "ambiguous_combining")
            self.assertEqual(by_source["L11"].stratum, "multiword")
            self.assertEqual(by_source["L12"].stratum, "abbreviation")
            self.assertEqual(by_source["L13"].stratum, "irregular_full")
            self.assertEqual(by_source["L14"].stratum, "invariant")
            self.assertEqual(by_source["L15"].stratum, "invariant_plural")
            self.assertEqual(
                noun_sample_bytes(first, noun_policy),
                noun_sample_bytes(second, noun_policy),
            )

            sampled_by_source = {
                sampled.candidate.source_key: sampled for sampled in first
            }
            plural_options = proposals_for_candidate(
                sampled_by_source["L2"], noun_policy
            )
            self.assertTrue(
                any(isinstance(option.proposal, PluralOnlyN) for option in plural_options)
            )
            self.assertEqual(
                proposal_blocker(by_source["L3"]),
                "residual_api_gap_singular_only",
            )
            self.assertEqual(
                proposal_blocker(by_source["L5"]),
                "uncorrelated_multiple_genders",
            )
            abbreviation_options = proposals_for_candidate(
                sampled_by_source["L12"], noun_policy
            )
            self.assertTrue(abbreviation_options)
            self.assertTrue(
                all(isinstance(option.proposal, AbbrevN) for option in abbreviation_options)
            )
            options, artifacts = render_proposal_modules(
                first, noun_policy, root / "rendered"
            )
            self.assertTrue(options)
            self.assertEqual(len(artifacts), 3)
            concrete = (root / "rendered/WdnPilotGer.gf").read_text(
                encoding="utf-8"
            )
            self.assertIn("probe_record", concrete)
            for field in PROBE_FIELDS:
                self.assertIn(f"{field} : Str", concrete)
            first_render = [artifact.path.read_bytes() for artifact in artifacts]
            _, repeated_artifacts = render_proposal_modules(
                first, noun_policy, root / "repeated"
            )
            self.assertEqual(
                first_render,
                [artifact.path.read_bytes() for artifact in repeated_artifacts],
            )

            first_option = options[0]
            probe_lines = [
                "candidate_id\toption_id\tfunction_id\tvariant_index\tfield\tvalue_json"
            ]
            probe_lines.extend(
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
                ("\n".join(probe_lines) + "\n").encode("utf-8"),
                (first_option,),
            )
            self.assertEqual(len(decoded[first_option.option_id]), 1)

            plural_candidate = sampled_by_source["L2"].candidate
            plural_record_values = {field: "" for field in PROBE_FIELDS}
            for field in ("s_pl_nom", "s_pl_acc", "s_pl_dat", "s_pl_gen"):
                plural_record_values[field] = "Kosten"
            for field in (
                "uncap_s_pl_nom",
                "uncap_s_pl_acc",
                "uncap_s_pl_dat",
                "uncap_s_pl_gen",
            ):
                plural_record_values[field] = "kosten"
            plural_record_values.update(
                {
                    "gender": "masculine",
                    "co": "Kosten",
                    "uncap_co": "kosten",
                    "csep": "bind",
                }
            )
            plural_comparison = compare_record(
                plural_candidate,
                plural_options[0],
                ProbeRecord(
                    plural_options[0].option_id,
                    1,
                    tuple(
                        (field, plural_record_values[field]) for field in PROBE_FIELDS
                    ),
                ),
            )
            self.assertEqual(plural_comparison.mismatches, ())
            evidence = dict(plural_comparison.field_evidence)
            self.assertEqual(evidence["s_sg_nom"], FieldEvidence.UNAVAILABLE)
            self.assertEqual(
                evidence["uncap_s_sg_nom"], FieldEvidence.UNAVAILABLE
            )

    def test_pinned_dump_nouns_are_forced_into_the_sample(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            database = root / "source.sqlite3"
            ingest_dump(
                dump_path=PINNED,
                database_path=database,
                source_policy=SourcePolicy("Q188", "exact"),
                snapshot_metadata=SNAPSHOT,
            )
            noun_policy = load_noun_policy(DEFAULT_NOUN_POLICY)
            with sqlite3.connect(database) as connection:
                sample = select_noun_sample(
                    connection,
                    noun_policy,
                    load_feature_policy(DEFAULT_FEATURE_POLICY),
                )
            pinned = {
                item.candidate.source_key for item in sample if item.pinned
            }
            self.assertEqual(pinned, set(noun_policy.pinned_lexemes))
            self.assertTrue(
                all(item.internal_id.startswith("wdn_") for item in sample)
            )


class NounPolicyTests(unittest.TestCase):
    def test_policy_freezes_all_strata(self) -> None:
        policy = load_noun_policy(DEFAULT_NOUN_POLICY)
        self.assertEqual(set(policy.quotas), set(STRATA))
        self.assertEqual(policy.singular_only_policy, "residual-api-gap")
        self.assertIn("P5548", policy.combining_form_policy)


if __name__ == "__main__":
    unittest.main()
