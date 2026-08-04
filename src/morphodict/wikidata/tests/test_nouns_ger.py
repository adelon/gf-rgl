from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from wd2gf.nouns_ger import (
    DEFAULT_NOUN_POLICY,
    STRATA,
    load_noun_policy,
    noun_sample_bytes,
    select_noun_sample,
)
from wd2gf.profile_ger import DEFAULT_FEATURE_POLICY, load_feature_policy
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
            self.assertEqual(
                noun_sample_bytes(first, noun_policy),
                noun_sample_bytes(second, noun_policy),
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
