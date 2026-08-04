"""Shared synthetic and pinned noun fixtures for focused Phase 2/3 tests."""

from __future__ import annotations

import json
import sqlite3
import tempfile
from contextlib import closing, contextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterator

from wd2gf.nouns_ger import (
    DEFAULT_NOUN_POLICY,
    NounPolicy,
    SampledCandidate,
    load_noun_policy,
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


@dataclass(frozen=True)
class SyntheticNouns:
    root: Path
    database: Path
    policy: NounPolicy
    first: tuple[SampledCandidate, ...]
    second: tuple[SampledCandidate, ...]

    @property
    def candidates(self):
        return {item.candidate.source_key: item.candidate for item in self.first}

    @property
    def sampled(self):
        return {item.candidate.source_key: item for item in self.first}


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


def write_fixture(path: Path) -> None:
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
        _lexeme("L8", "Rest", {"s_sg_nom": "Rest"}),
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
            {
                field: "Jeans"
                for field in (
                    "s_sg_nom",
                    "s_sg_acc",
                    "s_sg_dat",
                    "s_sg_gen",
                    "s_pl_nom",
                    "s_pl_acc",
                    "s_pl_dat",
                    "s_pl_gen",
                )
            },
            genders=(("feminine", "normal"),),
        ),
        _lexeme(
            "L15",
            "Auto",
            _complete("Auto", "Autos", "Autos", "Autos"),
            genders=(("neuter", "normal"),),
        ),
    ]
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


@contextmanager
def synthetic_nouns() -> Iterator[SyntheticNouns]:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        fixture = root / "nouns.json"
        database = root / "source.sqlite3"
        write_fixture(fixture)
        ingest_dump(
            dump_path=fixture,
            database_path=database,
            source_policy=SourcePolicy("Q188", "exact"),
            snapshot_metadata=SNAPSHOT,
        )
        policy = replace(load_noun_policy(), pinned_lexemes=())
        feature_policy = load_feature_policy(DEFAULT_FEATURE_POLICY)
        with closing(sqlite3.connect(database)) as connection:
            first = select_noun_sample(connection, policy, feature_policy)
            second = select_noun_sample(connection, policy, feature_policy)
        yield SyntheticNouns(root, database, policy, first, second)


def pinned_sample() -> tuple[NounPolicy, tuple[SampledCandidate, ...]]:
    with tempfile.TemporaryDirectory() as temporary:
        database = Path(temporary) / "source.sqlite3"
        ingest_dump(
            dump_path=PINNED,
            database_path=database,
            source_policy=SourcePolicy("Q188", "exact"),
            snapshot_metadata=SNAPSHOT,
        )
        policy = load_noun_policy(DEFAULT_NOUN_POLICY)
        with closing(sqlite3.connect(database)) as connection:
            sample = select_noun_sample(
                connection,
                policy,
                load_feature_policy(DEFAULT_FEATURE_POLICY),
            )
    return policy, sample
