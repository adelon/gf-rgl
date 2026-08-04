"""Command-line entry point for the German Wikidata prototype."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from wd2gf import __version__
from wd2gf.census_ger import (
    DEFAULT_CENSUS_DETAILS,
    DEFAULT_NOUN_CENSUS,
    generate_noun_census,
)
from wd2gf.nouns_ger import (
    DEFAULT_NOUN_POLICY,
    DEFAULT_NOUN_SAMPLE,
    DEFAULT_NOUN_WORK,
    NounError,
    generate_noun_sample,
    load_noun_policy,
    render_proposal_modules,
)
from wd2gf.snapshot import (
    DEFAULT_LOCK,
    DEFAULT_NEXT,
    DEFAULT_WORK_DIR,
    SnapshotError,
    download_snapshot,
    resolve_snapshot,
    verify_snapshot,
)
from wd2gf.profile_ger import (
    DEFAULT_FIXTURE_DIR,
    DEFAULT_FIXTURE_SELECTION,
    DEFAULT_FEATURE_POLICY,
    DEFAULT_INTERPRETED_REPORT_DIR,
    DEFAULT_RAW_REPORT_DIR,
    ProfileError,
    extract_pinned_fixture,
    generate_interpreted_profile,
    generate_raw_profile,
)
from wd2gf.probe_ger import probe_nouns, write_pilot_reports
from wd2gf.scale_ger import (
    DEFAULT_SCALE_POLICY,
    DEFAULT_SCALE_RESULTS,
    DEFAULT_SCALE_WORK,
    run_scale_gate,
    write_scale_report,
)
from wd2gf.store import (
    DEFAULT_DATABASE,
    DEFAULT_SOURCE_POLICY,
    IngestStats,
    StoreError,
    ingest_dump,
    load_source_policy,
    source_store_fingerprint,
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


def _ingest(args: argparse.Namespace) -> int:
    dump_path, snapshot_metadata = verify_snapshot(
        lock_path=args.lock, work_dir=args.work_dir
    )
    source_policy = load_source_policy(args.source_policy)

    def report_progress(stats: IngestStats) -> None:
        print(
            f"parsed={stats.entities_before_selection} "
            f"selected={stats.entities_selected}",
            file=sys.stderr,
        )

    stats = ingest_dump(
        dump_path=dump_path,
        database_path=args.database,
        source_policy=source_policy,
        snapshot_metadata=snapshot_metadata,
        progress=report_progress,
    )
    print(_metadata_json(vars(stats)))
    return 0


def _raw_profile(args: argparse.Namespace) -> int:
    _, snapshot_metadata = verify_snapshot(lock_path=args.lock, work_dir=args.work_dir)
    artifacts = generate_raw_profile(
        database_path=args.database,
        output_dir=args.output_dir,
        expected_snapshot=snapshot_metadata,
    )
    for artifact in artifacts:
        print(f"{artifact.sha256}  {artifact.size_bytes}  {artifact.path}")
    return 0


def _store_fingerprint(args: argparse.Namespace) -> int:
    print(_metadata_json(source_store_fingerprint(args.database)))
    return 0


def _extract_fixture(args: argparse.Namespace) -> int:
    _, snapshot_metadata = verify_snapshot(lock_path=args.lock, work_dir=args.work_dir)
    artifacts = extract_pinned_fixture(
        database_path=args.database,
        selection_path=args.selection,
        output_dir=args.output_dir,
        expected_snapshot=snapshot_metadata,
    )
    for artifact in artifacts:
        print(f"{artifact.sha256}  {artifact.size_bytes}  {artifact.path}")
    return 0


def _interpreted_profile(args: argparse.Namespace) -> int:
    _, snapshot_metadata = verify_snapshot(lock_path=args.lock, work_dir=args.work_dir)
    artifacts = generate_interpreted_profile(
        database_path=args.database,
        feature_policy_path=args.feature_policy,
        output_dir=args.output_dir,
        expected_snapshot=snapshot_metadata,
    )
    for artifact in artifacts:
        print(f"{artifact.sha256}  {artifact.size_bytes}  {artifact.path}")
    return 0


def _noun_sample(args: argparse.Namespace) -> int:
    _, snapshot_metadata = verify_snapshot(lock_path=args.lock, work_dir=args.work_dir)
    sample, artifact = generate_noun_sample(
        database_path=args.database,
        noun_policy_path=args.noun_policy,
        feature_policy_path=args.feature_policy,
        output_path=args.output,
        expected_snapshot=snapshot_metadata,
    )
    print(f"{artifact.sha256}  {artifact.size_bytes}  {artifact.path}")
    print(f"sampled_nouns={len(sample)}")
    return 0


def _noun_render(args: argparse.Namespace) -> int:
    _, snapshot_metadata = verify_snapshot(lock_path=args.lock, work_dir=args.work_dir)
    sample, sample_artifact = generate_noun_sample(
        database_path=args.database,
        noun_policy_path=args.noun_policy,
        feature_policy_path=args.feature_policy,
        output_path=args.output_dir / "noun-sample.tsv",
        expected_snapshot=snapshot_metadata,
    )
    _, artifacts = render_proposal_modules(
        sample,
        load_noun_policy(args.noun_policy),
        args.output_dir,
    )
    for artifact in (sample_artifact, *artifacts):
        print(f"{artifact.sha256}  {artifact.size_bytes}  {artifact.path}")
    return 0


def _noun_probe(args: argparse.Namespace) -> int:
    _, snapshot_metadata = verify_snapshot(lock_path=args.lock, work_dir=args.work_dir)
    sample, sample_artifact = generate_noun_sample(
        database_path=args.database,
        noun_policy_path=args.noun_policy,
        feature_policy_path=args.feature_policy,
        output_path=args.output_dir / "noun-sample.tsv",
        expected_snapshot=snapshot_metadata,
    )
    run = probe_nouns(
        sample=sample,
        noun_policy=load_noun_policy(args.noun_policy),
        gf_path=args.gf,
        work_dir=args.output_dir,
    )
    accepted = sum(fit.accepted is not None for fit in run.fits)
    print(
        f"{sample_artifact.sha256}  {sample_artifact.size_bytes}  "
        f"{sample_artifact.path}"
    )
    print(f"{run.raw_probe.sha256}  {run.raw_probe.size_bytes}  {run.raw_probe.path}")
    print(f"{run.details.sha256}  {run.details.size_bytes}  {run.details.path}")
    print(f"pgf_sha256={run.pgf_sha256}")
    print(f"accepted={accepted} rejected={len(run.fits) - accepted}")
    return 0


def _noun_pilot(args: argparse.Namespace) -> int:
    _, snapshot_metadata = verify_snapshot(lock_path=args.lock, work_dir=args.work_dir)
    sample, sample_artifact = generate_noun_sample(
        database_path=args.database,
        noun_policy_path=args.noun_policy,
        feature_policy_path=args.feature_policy,
        output_path=args.report_dir / "noun-sample.tsv",
        expected_snapshot=snapshot_metadata,
    )
    run = probe_nouns(
        sample=sample,
        noun_policy=load_noun_policy(args.noun_policy),
        gf_path=args.gf,
        work_dir=args.output_dir,
    )
    report_artifacts = write_pilot_reports(
        fits=run.fits,
        pgf_sha256=run.pgf_sha256,
        output_dir=args.report_dir,
    )
    for artifact in (sample_artifact, *report_artifacts):
        print(f"{artifact.sha256}  {artifact.size_bytes}  {artifact.path}")
    accepted = sum(fit.accepted is not None for fit in run.fits)
    print(f"pgf_sha256={run.pgf_sha256}")
    print(f"accepted={accepted} rejected={len(run.fits) - accepted}")
    return 0


def _noun_census(args: argparse.Namespace) -> int:
    _, snapshot_metadata = verify_snapshot(lock_path=args.lock, work_dir=args.work_dir)
    run = generate_noun_census(
        database_path=args.database,
        noun_policy_path=args.noun_policy,
        feature_policy_path=args.feature_policy,
        report_path=args.output,
        details_path=args.details,
        expected_snapshot=snapshot_metadata,
    )
    for artifact in (run.report, run.details):
        print(f"{artifact.sha256}  {artifact.size_bytes}  {artifact.path}")
    print(f"noun_candidates={run.total_candidates}")
    print(_metadata_json(run.tier_counts))
    return 0


def _noun_scale_gate(args: argparse.Namespace) -> int:
    _, snapshot_metadata = verify_snapshot(lock_path=args.lock, work_dir=args.work_dir)
    run = run_scale_gate(
        gf_path=args.gf,
        database_path=args.database,
        noun_policy_path=args.noun_policy,
        feature_policy_path=args.feature_policy,
        scale_policy_path=args.scale_policy,
        work_dir=args.output_dir,
        expected_snapshot=snapshot_metadata,
    )
    for artifact in (run.semantic, run.measurements):
        print(f"{artifact.sha256}  {artifact.size_bytes}  {artifact.path}")
    print(
        f"fitting_candidates={run.fitting_candidates} "
        f"result_entries={run.result_entries} budget_passed={run.budget_passed}"
    )
    return 0


def _noun_scale_report(args: argparse.Namespace) -> int:
    artifact = write_scale_report(
        primary_dir=args.primary_dir,
        repeat_dir=args.repeat_dir,
        output_path=args.output,
    )
    print(f"{artifact.sha256}  {artifact.size_bytes}  {artifact.path}")
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

    store_parser = commands.add_parser("store", help="manage the lossless source store")
    store_commands = store_parser.add_subparsers(dest="store_command", required=True)
    ingest_parser = store_commands.add_parser(
        "ingest", help="verify and stream the pinned dump into a new SQLite store"
    )
    ingest_parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    ingest_parser.add_argument("--source-policy", type=Path, default=DEFAULT_SOURCE_POLICY)
    ingest_parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    ingest_parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    ingest_parser.set_defaults(handler=_ingest)
    fingerprint_parser = store_commands.add_parser(
        "fingerprint", help="hash selected entity hashes and report projection counts"
    )
    fingerprint_parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    fingerprint_parser.set_defaults(handler=_store_fingerprint)

    profile_parser = commands.add_parser("profile", help="profile the German source store")
    profile_commands = profile_parser.add_subparsers(dest="profile_command", required=True)
    raw_parser = profile_commands.add_parser(
        "raw", help="emit uninterpreted QID, property, and feature inventories"
    )
    raw_parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    raw_parser.add_argument("--output-dir", type=Path, default=DEFAULT_RAW_REPORT_DIR)
    raw_parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    raw_parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    raw_parser.set_defaults(handler=_raw_profile)
    interpreted_parser = profile_commands.add_parser(
        "interpreted", help="apply the reviewed German QID mappings"
    )
    interpreted_parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    interpreted_parser.add_argument(
        "--feature-policy", type=Path, default=DEFAULT_FEATURE_POLICY
    )
    interpreted_parser.add_argument(
        "--output-dir", type=Path, default=DEFAULT_INTERPRETED_REPORT_DIR
    )
    interpreted_parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    interpreted_parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    interpreted_parser.set_defaults(handler=_interpreted_profile)

    fixture_parser = commands.add_parser(
        "fixture", help="extract complete source entities for pinned tests"
    )
    fixture_commands = fixture_parser.add_subparsers(
        dest="fixture_command", required=True
    )
    extract_parser = fixture_commands.add_parser(
        "extract", help="extract the reviewed fixture selection from the source store"
    )
    extract_parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    extract_parser.add_argument("--selection", type=Path, default=DEFAULT_FIXTURE_SELECTION)
    extract_parser.add_argument("--output-dir", type=Path, default=DEFAULT_FIXTURE_DIR)
    extract_parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    extract_parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    extract_parser.set_defaults(handler=_extract_fixture)

    noun_parser = commands.add_parser("noun", help="run the German noun pilot")
    noun_commands = noun_parser.add_subparsers(dest="noun_command", required=True)
    noun_sample_parser = noun_commands.add_parser(
        "sample", help="select the deterministic stratified noun sample"
    )
    noun_sample_parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    noun_sample_parser.add_argument(
        "--noun-policy", type=Path, default=DEFAULT_NOUN_POLICY
    )
    noun_sample_parser.add_argument(
        "--feature-policy", type=Path, default=DEFAULT_FEATURE_POLICY
    )
    noun_sample_parser.add_argument("--output", type=Path, default=DEFAULT_NOUN_SAMPLE)
    noun_sample_parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    noun_sample_parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    noun_sample_parser.set_defaults(handler=_noun_sample)
    noun_render_parser = noun_commands.add_parser(
        "render", help="render disposable GF modules for the noun proposals"
    )
    noun_render_parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    noun_render_parser.add_argument(
        "--noun-policy", type=Path, default=DEFAULT_NOUN_POLICY
    )
    noun_render_parser.add_argument(
        "--feature-policy", type=Path, default=DEFAULT_FEATURE_POLICY
    )
    noun_render_parser.add_argument(
        "--output-dir", type=Path, default=DEFAULT_NOUN_WORK
    )
    noun_render_parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    noun_render_parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    noun_render_parser.set_defaults(handler=_noun_render)
    noun_probe_parser = noun_commands.add_parser(
        "probe", help="compile and structurally probe every noun proposal"
    )
    noun_probe_parser.add_argument("--gf", type=Path, required=True)
    noun_probe_parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    noun_probe_parser.add_argument(
        "--noun-policy", type=Path, default=DEFAULT_NOUN_POLICY
    )
    noun_probe_parser.add_argument(
        "--feature-policy", type=Path, default=DEFAULT_FEATURE_POLICY
    )
    noun_probe_parser.add_argument(
        "--output-dir", type=Path, default=DEFAULT_NOUN_WORK
    )
    noun_probe_parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    noun_probe_parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    noun_probe_parser.set_defaults(handler=_noun_probe)
    noun_pilot_parser = noun_commands.add_parser(
        "pilot", help="run the complete noun pilot and write decision reports"
    )
    noun_pilot_parser.add_argument("--gf", type=Path, required=True)
    noun_pilot_parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    noun_pilot_parser.add_argument(
        "--noun-policy", type=Path, default=DEFAULT_NOUN_POLICY
    )
    noun_pilot_parser.add_argument(
        "--feature-policy", type=Path, default=DEFAULT_FEATURE_POLICY
    )
    noun_pilot_parser.add_argument(
        "--output-dir", type=Path, default=DEFAULT_NOUN_WORK
    )
    noun_pilot_parser.add_argument(
        "--report-dir", type=Path, default=DEFAULT_NOUN_SAMPLE.parent
    )
    noun_pilot_parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    noun_pilot_parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    noun_pilot_parser.set_defaults(handler=_noun_pilot)
    noun_census_parser = noun_commands.add_parser(
        "census", help="classify the full noun population without compiling GF"
    )
    noun_census_parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    noun_census_parser.add_argument(
        "--noun-policy", type=Path, default=DEFAULT_NOUN_POLICY
    )
    noun_census_parser.add_argument(
        "--feature-policy", type=Path, default=DEFAULT_FEATURE_POLICY
    )
    noun_census_parser.add_argument("--output", type=Path, default=DEFAULT_NOUN_CENSUS)
    noun_census_parser.add_argument(
        "--details", type=Path, default=DEFAULT_CENSUS_DETAILS
    )
    noun_census_parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    noun_census_parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    noun_census_parser.set_defaults(handler=_noun_census)
    noun_scale_parser = noun_commands.add_parser(
        "scale-gate", help="run the authorized 5,000-candidate scale gate"
    )
    noun_scale_parser.add_argument("--gf", type=Path, required=True)
    noun_scale_parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    noun_scale_parser.add_argument(
        "--noun-policy", type=Path, default=DEFAULT_NOUN_POLICY
    )
    noun_scale_parser.add_argument(
        "--feature-policy", type=Path, default=DEFAULT_FEATURE_POLICY
    )
    noun_scale_parser.add_argument(
        "--scale-policy", type=Path, default=DEFAULT_SCALE_POLICY
    )
    noun_scale_parser.add_argument(
        "--output-dir", type=Path, default=DEFAULT_SCALE_WORK
    )
    noun_scale_parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    noun_scale_parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    noun_scale_parser.set_defaults(handler=_noun_scale_gate)
    noun_scale_report_parser = noun_commands.add_parser(
        "scale-report", help="verify repeated gate artifacts and write scale results"
    )
    noun_scale_report_parser.add_argument("--primary-dir", type=Path, required=True)
    noun_scale_report_parser.add_argument("--repeat-dir", type=Path, required=True)
    noun_scale_report_parser.add_argument(
        "--output", type=Path, default=DEFAULT_SCALE_RESULTS
    )
    noun_scale_report_parser.set_defaults(handler=_noun_scale_report)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except (SnapshotError, StoreError, ProfileError, NounError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
