"""Command-line entry point for the German Wikidata prototype."""

from __future__ import annotations

import argparse

from wd2gf import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wd2gf",
        description="Ingest and profile a pinned German Wikidata Lexeme dump.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def main(argv: list[str] | None = None) -> int:
    build_parser().parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
