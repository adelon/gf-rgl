"""Command-line entry point for the German Wikidata prototype."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from wd2gf import __version__
from wd2gf.snapshot import (
    DEFAULT_LOCK,
    DEFAULT_NEXT,
    DEFAULT_WORK_DIR,
    SnapshotError,
    download_snapshot,
    resolve_snapshot,
    verify_snapshot,
)


def _metadata_json(metadata: dict[str, object]) -> str:
    return json.dumps(metadata, ensure_ascii=False, sort_keys=True)


def _resolve(args: argparse.Namespace) -> int:
    metadata = resolve_snapshot(
        date=args.date,
        compression=args.compression,
        next_path=args.plan,
        lock_path=args.lock,
        replace_plan=args.replace_plan,
    )
    print(_metadata_json(metadata))
    return 0


def _download(args: argparse.Namespace) -> int:
    dump_path, metadata = download_snapshot(
        next_path=args.plan,
        lock_path=args.lock,
        work_dir=args.work_dir,
        replace=args.replace,
    )
    print(f"verified download: {dump_path}")
    print(_metadata_json(metadata))
    return 0


def _verify(args: argparse.Namespace) -> int:
    dump_path, metadata = verify_snapshot(lock_path=args.lock, work_dir=args.work_dir)
    print(f"verified snapshot: {dump_path}")
    print(_metadata_json(metadata))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wd2gf",
        description="Ingest and profile a pinned German Wikidata Lexeme dump.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    snapshot_parser = commands.add_parser("snapshot", help="manage the dated dump lock")
    snapshot_commands = snapshot_parser.add_subparsers(
        dest="snapshot_command", required=True
    )

    resolve_parser = snapshot_commands.add_parser(
        "resolve", help="resolve explicit dated official metadata"
    )
    resolve_parser.add_argument("--date", required=True, help="dump date as YYYYMMDD")
    resolve_parser.add_argument("--compression", required=True, choices=["gz"])
    resolve_parser.add_argument("--plan", type=Path, default=DEFAULT_NEXT)
    resolve_parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    resolve_parser.add_argument("--replace-plan", action="store_true")
    resolve_parser.set_defaults(handler=_resolve)

    download_parser = snapshot_commands.add_parser(
        "download", help="download, verify, and finalize the snapshot lock"
    )
    download_parser.add_argument("--plan", type=Path, default=DEFAULT_NEXT)
    download_parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    download_parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    download_parser.add_argument(
        "--replace",
        action="store_true",
        help="explicitly replace an existing lock or dump after verifying new bytes",
    )
    download_parser.set_defaults(handler=_download)

    verify_parser = snapshot_commands.add_parser(
        "verify", help="verify retained bytes against a finalized lock"
    )
    verify_parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    verify_parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    verify_parser.set_defaults(handler=_verify)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except SnapshotError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
