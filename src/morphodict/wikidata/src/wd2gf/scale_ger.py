"""Deterministic first-gate scale measurements for German noun fitting."""

from __future__ import annotations

import hashlib
import os
import subprocess
import tomllib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence, TypeVar

from wd2gf.census_ger import (
    AcceptanceTier,
    CensusClassification,
    _sense_qualifiers,
    classify_candidate,
)
from wd2gf.nouns_ger import (
    DEFAULT_NOUN_POLICY,
    NounArtifact,
    NounCandidate,
    NounError,
    NounPolicy,
    ProposalOption,
    SampledCandidate,
    _connect,
    _write_bytes,
    iter_noun_candidates,
    load_noun_policy,
    render_option_modules,
    render_proposal_modules,
)
from wd2gf.probe_ger import (
    CandidateFit,
    ProbeRecord,
    _gf_core,
    decode_probe,
    fit_candidates,
)
from wd2gf.profile_ger import (
    DEFAULT_FEATURE_POLICY,
    FeaturePolicy,
    load_feature_policy,
    load_store_metadata,
)
from wd2gf.store import DEFAULT_DATABASE, canonical_json


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RGL_ROOT = Path(__file__).resolve().parents[5]
HASKELL_PROBE = PROJECT_ROOT / "probe/NounProbe.hs"
DEFAULT_SCALE_POLICY = PROJECT_ROOT / "languages/ger/scale-policy.toml"
DEFAULT_SCALE_WORK = PROJECT_ROOT / ".work/phase3/gate-5000"
T = TypeVar("T")


@dataclass(frozen=True)
class WorkloadBudget:
    values: dict[str, float | int]


@dataclass(frozen=True)
class ScalePolicy:
    reference: str
    selection_seed: str
    gate_candidates: int
    fitting_chunk_size: int
    result_entries: int
    result_selection_reserve_per_tier: int
    minimum_per_fitting_stratum: int
    fitting_budget: WorkloadBudget
    result_budget: WorkloadBudget
    authorized_scale_points: tuple[int, ...]
    next_scale_point: int
    next_scale_requires_review: bool
    stop_on_budget_failure: bool
    stop_on_nondeterminism: bool


@dataclass(frozen=True)
class SelectedCandidate:
    sampled: SampledCandidate
    classification: CensusClassification
    selection_stratum: str


@dataclass(frozen=True)
class PopulationSelection:
    fitting: tuple[SelectedCandidate, ...]
    result_pool: tuple[SelectedCandidate, ...]
    fitting_quotas: dict[str, int]
    result_quotas: dict[str, int]
    population_strata: dict[str, int]


@dataclass(frozen=True)
class CommandMeasurement:
    label: str
    wall_seconds: float
    peak_rss_kib: int


@dataclass(frozen=True)
class ChunkFitRun:
    fits: tuple[CandidateFit, ...]
    proposal_count: int
    measurements: tuple[CommandMeasurement, ...]
    source_artifacts: tuple[NounArtifact, ...]
    probe_artifacts: tuple[NounArtifact, ...]
    pgf_hashes: tuple[str, ...]


@dataclass(frozen=True)
class ScaleGateRun:
    semantic: NounArtifact
    measurements: NounArtifact
    budget_passed: bool
    fitting_candidates: int
    result_entries: int


def load_scale_policy(path: Path = DEFAULT_SCALE_POLICY) -> ScalePolicy:
    try:
        with path.open("rb") as policy_file:
            data = tomllib.load(policy_file)
    except FileNotFoundError as error:
        raise NounError(f"scale policy does not exist: {path}") from error
    expected = {
        "schema_version",
        "reference",
        "selection_seed",
        "gate_candidates",
        "fitting_chunk_size",
        "result_entries",
        "result_selection_reserve_per_tier",
        "minimum_per_fitting_stratum",
        "budgets",
        "gate",
    }
    if set(data) != expected or data["schema_version"] != 1:
        raise NounError("unsupported noun scale policy schema")
    integer_fields = (
        "gate_candidates",
        "fitting_chunk_size",
        "result_entries",
        "result_selection_reserve_per_tier",
        "minimum_per_fitting_stratum",
    )
    if any(not isinstance(data[key], int) or data[key] <= 0 for key in integer_fields):
        raise NounError("scale sizes, chunks, reserves, and minima must be positive integers")
    if data["gate_candidates"] != 5000 or data["result_entries"] != 5000:
        raise NounError("the first Phase 3 gate is frozen at 5,000 candidates and entries")
    budgets = data["budgets"]
    if not isinstance(budgets, dict) or set(budgets) != {"fitting", "result"}:
        raise NounError("scale budgets must separate fitting and result workloads")
    fitting_keys = {
        "total_wall_seconds",
        "chunk_wall_seconds",
        "probe_wall_seconds",
        "peak_rss_kib",
        "disposable_artifact_bytes",
    }
    result_keys = {
        "clean_build_wall_seconds",
        "probe_wall_seconds",
        "incremental_build_wall_seconds",
        "peak_rss_kib",
        "gf_source_bytes",
        "gfo_bytes",
        "pgf_bytes",
    }
    if set(budgets["fitting"]) != fitting_keys or set(budgets["result"]) != result_keys:
        raise NounError("scale budget fields do not match the frozen schema")
    for workload in budgets.values():
        if any(
            isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0
            for value in workload.values()
        ):
            raise NounError("every scale budget must be a positive number")
    gate = data["gate"]
    gate_keys = {
        "authorized_scale_points",
        "next_scale_point",
        "next_scale_requires_review",
        "stop_on_budget_failure",
        "stop_on_nondeterminism",
    }
    if set(gate) != gate_keys:
        raise NounError("scale gate controls do not match the frozen schema")
    authorized = gate["authorized_scale_points"]
    if authorized != [5000] or gate["next_scale_point"] != 25000:
        raise NounError("only the 5,000 gate may be authorized in this policy")
    booleans = (
        "next_scale_requires_review",
        "stop_on_budget_failure",
        "stop_on_nondeterminism",
    )
    if any(not isinstance(gate[key], bool) or not gate[key] for key in booleans):
        raise NounError("first-gate stop and review controls must be true")
    if not isinstance(data["reference"], str) or not data["reference"]:
        raise NounError("scale policy reference must be nonempty")
    if not isinstance(data["selection_seed"], str) or not data["selection_seed"]:
        raise NounError("scale selection seed must be nonempty")
    return ScalePolicy(
        reference=data["reference"],
        selection_seed=data["selection_seed"],
        gate_candidates=data["gate_candidates"],
        fitting_chunk_size=data["fitting_chunk_size"],
        result_entries=data["result_entries"],
        result_selection_reserve_per_tier=data[
            "result_selection_reserve_per_tier"
        ],
        minimum_per_fitting_stratum=data["minimum_per_fitting_stratum"],
        fitting_budget=WorkloadBudget(dict(budgets["fitting"])),
        result_budget=WorkloadBudget(dict(budgets["result"])),
        authorized_scale_points=tuple(authorized),
        next_scale_point=gate["next_scale_point"],
        next_scale_requires_review=gate["next_scale_requires_review"],
        stop_on_budget_failure=gate["stop_on_budget_failure"],
        stop_on_nondeterminism=gate["stop_on_nondeterminism"],
    )


def proportional_quotas(
    counts: Mapping[str, int], target: int, minimum_per_stratum: int
) -> dict[str, int]:
    """Allocate an exact stratified target with a frozen minimum and remainders."""
    active = {key: count for key, count in counts.items() if count > 0}
    if target > sum(active.values()):
        raise NounError("scale target exceeds the available population")
    minima = {
        key: min(count, minimum_per_stratum) for key, count in active.items()
    }
    if sum(minima.values()) > target:
        raise NounError("scale target cannot preserve the configured stratum minimum")
    quotas = dict(minima)
    remaining = target - sum(quotas.values())
    capacity = {key: active[key] - quotas[key] for key in active}
    capacity_total = sum(capacity.values())
    if remaining and not capacity_total:
        raise NounError("scale quota allocation has no remaining capacity")
    exact = {
        key: (remaining * capacity[key] / capacity_total if capacity_total else 0.0)
        for key in active
    }
    for key in active:
        addition = min(capacity[key], int(exact[key]))
        quotas[key] += addition
    remainder = target - sum(quotas.values())
    order = sorted(
        active,
        key=lambda key: (-(exact[key] - int(exact[key])), key),
    )
    while remainder:
        progressed = False
        for key in order:
            if quotas[key] < active[key]:
                quotas[key] += 1
                remainder -= 1
                progressed = True
                if not remainder:
                    break
        if not progressed:
            raise NounError("scale quota allocation exhausted its capacity")
    return dict(sorted(quotas.items()))


def _fitting_stratum(
    candidate: NounCandidate, classification: CensusClassification
) -> str:
    return "|".join(
        (
            classification.acceptance_tier.value,
            candidate.source_completeness.value,
            classification.exclusion_reason or "eligible",
        )
    )


def _score(seed: str, source_key: str) -> tuple[int, str]:
    digest = hashlib.sha256(f"{seed}\0{source_key}".encode("utf-8")).hexdigest()
    return int(digest, 16), digest


def _lexeme_key(source_key: str) -> tuple[int, str]:
    try:
        return int(source_key.removeprefix("L")), source_key
    except ValueError:
        return 2**63, source_key


def _retain(
    heaps: dict[str, list[tuple[int, str, NounCandidate, CensusClassification]]],
    *,
    stratum: str,
    quota: int,
    seed: str,
    candidate: NounCandidate,
    classification: CensusClassification,
) -> None:
    import heapq

    if quota <= 0:
        return
    numeric, _ = _score(seed, candidate.source_key)
    item = (-numeric, candidate.source_key, candidate, classification)
    heap = heaps.setdefault(stratum, [])
    if len(heap) < quota:
        heapq.heappush(heap, item)
    elif numeric < -heap[0][0]:
        heapq.heapreplace(heap, item)


def _selected(
    heaps: Mapping[
        str, Sequence[tuple[int, str, NounCandidate, CensusClassification]]
    ],
    seed: str,
    prefix: str,
) -> tuple[SelectedCandidate, ...]:
    entries = [
        (stratum, candidate, classification)
        for stratum, heap in heaps.items()
        for _, _, candidate, classification in heap
    ]
    entries.sort(key=lambda item: _lexeme_key(item[1].source_key))
    return tuple(
        SelectedCandidate(
            sampled=SampledCandidate(
                internal_id=f"{prefix}_{index:06d}_N",
                score=_score(seed, candidate.source_key)[1],
                pinned=False,
                candidate=candidate,
            ),
            classification=classification,
            selection_stratum=stratum,
        )
        for index, (stratum, candidate, classification) in enumerate(entries, start=1)
    )


def select_scale_population(
    *,
    database_path: Path = DEFAULT_DATABASE,
    noun_policy_path: Path = DEFAULT_NOUN_POLICY,
    feature_policy_path: Path = DEFAULT_FEATURE_POLICY,
    scale_policy_path: Path = DEFAULT_SCALE_POLICY,
    expected_snapshot: Mapping[str, object] | None = None,
) -> PopulationSelection:
    noun_policy = load_noun_policy(noun_policy_path)
    scale_policy = load_scale_policy(scale_policy_path)
    if scale_policy.selection_seed != noun_policy.scale_seed:
        raise NounError("noun and scale policies disagree on the selection seed")
    feature_policy: FeaturePolicy = load_feature_policy(feature_policy_path)
    connection = _connect(database_path)
    try:
        metadata = load_store_metadata(connection)
        snapshot = metadata.get("snapshot")
        if not isinstance(snapshot, dict):
            raise NounError("source database has no snapshot metadata")
        if expected_snapshot is not None and snapshot != dict(expected_snapshot):
            raise NounError("source database snapshot does not match the verified lock")
        qualifiers, sense_owners = _sense_qualifiers(
            connection, noun_policy.sense_correlation_property
        )
        fitting_counts: Counter[str] = Counter()
        automatic_counts: Counter[str] = Counter()
        for candidate in iter_noun_candidates(connection, feature_policy):
            classification = classify_candidate(
                candidate, qualifiers, sense_owners, noun_policy
            )
            fitting_counts[_fitting_stratum(candidate, classification)] += 1
            if classification.acceptance_tier in {
                AcceptanceTier.AUTOMATIC_COMPLETE,
                AcceptanceTier.AUTOMATIC_COMPLETE_WITH_CO,
            }:
                automatic_counts[classification.acceptance_tier.value] += 1
        fitting_quotas = proportional_quotas(
            fitting_counts,
            scale_policy.gate_candidates,
            scale_policy.minimum_per_fitting_stratum,
        )
        result_quotas = proportional_quotas(
            automatic_counts, scale_policy.result_entries, 1
        )
        result_pool_quotas = {
            key: min(
                automatic_counts[key],
                quota + scale_policy.result_selection_reserve_per_tier,
            )
            for key, quota in result_quotas.items()
        }
        fitting_heaps: dict[
            str, list[tuple[int, str, NounCandidate, CensusClassification]]
        ] = {}
        result_heaps: dict[
            str, list[tuple[int, str, NounCandidate, CensusClassification]]
        ] = {}
        fitting_seed = f"{scale_policy.selection_seed}:fitting"
        result_seed = f"{scale_policy.selection_seed}:result"
        for candidate in iter_noun_candidates(connection, feature_policy):
            classification = classify_candidate(
                candidate, qualifiers, sense_owners, noun_policy
            )
            stratum = _fitting_stratum(candidate, classification)
            _retain(
                fitting_heaps,
                stratum=stratum,
                quota=fitting_quotas[stratum],
                seed=fitting_seed,
                candidate=candidate,
                classification=classification,
            )
            tier = classification.acceptance_tier.value
            if tier in result_pool_quotas:
                _retain(
                    result_heaps,
                    stratum=tier,
                    quota=result_pool_quotas[tier],
                    seed=result_seed,
                    candidate=candidate,
                    classification=classification,
                )
        fitting = _selected(fitting_heaps, fitting_seed, "wdf")
        result_pool = _selected(result_heaps, result_seed, "wdr")
        if len(fitting) != scale_policy.gate_candidates:
            raise NounError("fitting selection did not reach the frozen gate size")
        if any(
            sum(item.selection_stratum == key for item in result_pool) < quota
            for key, quota in result_quotas.items()
        ):
            raise NounError("result selection pool does not cover its target quotas")
        return PopulationSelection(
            fitting=fitting,
            result_pool=result_pool,
            fitting_quotas=fitting_quotas,
            result_quotas=result_quotas,
            population_strata=dict(sorted(fitting_counts.items())),
        )
    finally:
        connection.close()


def selection_bytes(items: Sequence[SelectedCandidate]) -> bytes:
    lines = [
        "internal_id\tsource_key\tscore_sha256\tselection_stratum\t"
        "acceptance_tier\tsource_completeness\texclusion_reason"
    ]
    for item in items:
        candidate = item.sampled.candidate
        fields = (
            item.sampled.internal_id,
            candidate.source_key,
            item.sampled.score,
            item.selection_stratum,
            item.classification.acceptance_tier.value,
            candidate.source_completeness.value,
            item.classification.exclusion_reason,
        )
        if any(character in field for field in fields for character in "\t\r\n"):
            raise NounError("scale selection escaped its TSV schema")
        lines.append("\t".join(fields))
    return ("\n".join(lines) + "\n").encode("utf-8")


def _measured_run(
    command: Sequence[str],
    *,
    cwd: Path,
    metrics_path: Path,
    label: str,
) -> tuple[bytes, CommandMeasurement]:
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ)
    environment["LC_ALL"] = "C"
    timed = (
        "/usr/bin/time",
        "--quiet",
        "--format=%e\t%M",
        f"--output={metrics_path}",
        *command,
    )
    try:
        result = subprocess.run(
            timed,
            cwd=cwd,
            env=environment,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as error:
        raise NounError(f"required scale command is unavailable: {error.filename}") from error
    if result.returncode:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise NounError(f"scale command failed ({command[0]}): {stderr[-4000:]}")
    try:
        raw_wall, raw_rss = metrics_path.read_text(encoding="utf-8").strip().split("\t")
        measurement = CommandMeasurement(label, float(raw_wall), int(raw_rss))
    except (OSError, ValueError) as error:
        raise NounError(f"invalid GNU time measurement for {label}") from error
    return result.stdout, measurement


def _compile_bridge(
    gf_path: Path, work_dir: Path
) -> tuple[Path, CommandMeasurement]:
    gf_core, ghc_version = _gf_core(gf_path)
    stack_yaml = gf_core / f"stack-ghc{ghc_version}.yaml"
    if not stack_yaml.is_file():
        raise NounError(f"GF Stack build plan is absent: {stack_yaml}")
    build_dir = work_dir / "haskell"
    build_dir.mkdir(parents=True, exist_ok=True)
    binary = work_dir / "NounProbe"
    _, measurement = _measured_run(
        (
            "stack",
            "--stack-yaml",
            str(stack_yaml),
            "exec",
            "--",
            "ghc",
            "-O1",
            "-package",
            "gf",
            f"-outputdir={build_dir}",
            "-o",
            str(binary),
            str(HASKELL_PROBE),
        ),
        cwd=gf_core,
        metrics_path=work_dir / "bridge.time.tsv",
        label="haskell_bridge",
    )
    if not binary.is_file():
        raise NounError("Haskell build did not produce the noun probe bridge")
    return binary, measurement


def _compile_gf(
    *,
    gf_path: Path,
    work_dir: Path,
    label: str,
) -> tuple[Path, str, CommandMeasurement]:
    rgl_library = RGL_ROOT / "dist/present"
    if not (rgl_library / "ParadigmsGer.gfo").is_file():
        raise NounError("scale gate requires the existing dist/present German RGL build")
    concrete = work_dir / "WdnPilotGer.gf"
    if not concrete.is_file():
        raise NounError(f"rendered scale module is absent: {concrete}")
    gfo_dir = work_dir / "gfo"
    pgf_dir = work_dir / "pgf"
    gfo_dir.mkdir(parents=True, exist_ok=True)
    pgf_dir.mkdir(parents=True, exist_ok=True)
    _, measurement = _measured_run(
        (
            str(gf_path),
            "--batch",
            "--quiet",
            f"--gf-lib-path={rgl_library}",
            f"--gfo-dir={gfo_dir}",
            f"--output-dir={pgf_dir}",
            "--make",
            str(concrete),
        ),
        cwd=PROJECT_ROOT,
        metrics_path=work_dir / f"{label}.time.tsv",
        label=label,
    )
    pgf_path = pgf_dir / "WdnPilotAbs.pgf"
    if not pgf_path.is_file():
        raise NounError("GF did not produce the expected scale PGF")
    return pgf_path, hashlib.sha256(pgf_path.read_bytes()).hexdigest(), measurement


def _run_probe(
    *,
    probe_binary: Path,
    pgf_path: Path,
    manifest_path: Path,
    output_path: Path,
    label: str,
) -> tuple[NounArtifact, CommandMeasurement]:
    output, measurement = _measured_run(
        (str(probe_binary), str(pgf_path), str(manifest_path)),
        cwd=PROJECT_ROOT,
        metrics_path=output_path.with_suffix(".time.tsv"),
        label=label,
    )
    return _write_bytes(output_path, output), measurement


def _chunks(values: Sequence[T], size: int) -> Iterable[Sequence[T]]:
    for offset in range(0, len(values), size):
        yield values[offset : offset + size]


def fit_in_chunks(
    *,
    selected: Sequence[SelectedCandidate],
    noun_policy: NounPolicy,
    scale_policy: ScalePolicy,
    gf_path: Path,
    probe_binary: Path,
    work_dir: Path,
    workload: str,
) -> ChunkFitRun:
    all_fits: list[CandidateFit] = []
    measurements: list[CommandMeasurement] = []
    sources: list[NounArtifact] = []
    probes: list[NounArtifact] = []
    pgf_hashes: list[str] = []
    proposal_count = 0
    for index, chunk in enumerate(
        _chunks(tuple(selected), scale_policy.fitting_chunk_size), start=1
    ):
        chunk_dir = work_dir / f"chunk-{index:03d}"
        sample = tuple(item.sampled for item in chunk)
        options, artifacts = render_proposal_modules(sample, noun_policy, chunk_dir)
        proposal_count += len(options)
        sources.extend(artifacts)
        pgf_path, pgf_hash, gf_measurement = _compile_gf(
            gf_path=gf_path,
            work_dir=chunk_dir,
            label=f"{workload}_gf_{index:03d}",
        )
        raw_probe, probe_measurement = _run_probe(
            probe_binary=probe_binary,
            pgf_path=pgf_path,
            manifest_path=chunk_dir / "proposal-manifest.tsv",
            output_path=chunk_dir / "probe-output.tsv",
            label=f"{workload}_probe_{index:03d}",
        )
        records = decode_probe(raw_probe.path.read_bytes(), options)
        all_fits.extend(fit_candidates(sample, options, records))
        probes.append(raw_probe)
        measurements.extend((gf_measurement, probe_measurement))
        pgf_hashes.append(pgf_hash)
    if len(all_fits) != len(selected):
        raise NounError("chunked fitter did not return one outcome per candidate")
    return ChunkFitRun(
        fits=tuple(all_fits),
        proposal_count=proposal_count,
        measurements=tuple(measurements),
        source_artifacts=tuple(sources),
        probe_artifacts=tuple(probes),
        pgf_hashes=tuple(pgf_hashes),
    )


def fit_results_bytes(
    selected: Sequence[SelectedCandidate], fits: Sequence[CandidateFit]
) -> bytes:
    classifications = {
        item.sampled.internal_id: item.classification for item in selected
    }
    rows = []
    for fit in fits:
        accepted = fit.accepted
        classification = classifications[fit.sampled.internal_id]
        rows.append(
            {
                "internal_id": fit.sampled.internal_id,
                "source_key": fit.sampled.candidate.source_key,
                "acceptance_tier": classification.acceptance_tier.value,
                "accepted": accepted is not None,
                "rejection_reason": fit.rejection_reason,
                "compared_options": fit.compared_options,
                "constructor": accepted.option.constructor if accepted else None,
                "expression": accepted.option.expression if accepted else None,
                "gf_fit": accepted.gf_fit.value if accepted else None,
                "record": accepted.record.as_dict() if accepted else None,
                "field_evidence": (
                    {field: status.value for field, status in accepted.field_evidence}
                    if accepted
                    else None
                ),
            }
        )
    return (canonical_json(rows) + "\n").encode("utf-8")


def select_result_entries(
    selected: Sequence[SelectedCandidate],
    fits: Sequence[CandidateFit],
    quotas: Mapping[str, int],
) -> tuple[tuple[SelectedCandidate, CandidateFit], ...]:
    by_id = {item.sampled.internal_id: item for item in selected}
    accepted_by_tier: dict[str, list[tuple[SelectedCandidate, CandidateFit]]] = {
        key: [] for key in quotas
    }
    for fit in fits:
        item = by_id[fit.sampled.internal_id]
        tier = item.classification.acceptance_tier.value
        if fit.accepted is not None and tier in accepted_by_tier:
            accepted_by_tier[tier].append((item, fit))
    chosen: list[tuple[SelectedCandidate, CandidateFit]] = []
    for tier, quota in sorted(quotas.items()):
        ranked = sorted(
            accepted_by_tier[tier],
            key=lambda pair: (pair[0].sampled.score, pair[0].sampled.candidate.source_key),
        )
        if len(ranked) < quota:
            raise NounError(
                f"result selection has {len(ranked)} accepted {tier} candidates; "
                f"{quota} required"
            )
        chosen.extend(ranked[:quota])
    chosen.sort(key=lambda pair: _lexeme_key(pair[0].sampled.candidate.source_key))
    return tuple(chosen)


def _directory_size(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def _artifact_map(artifacts: Sequence[NounArtifact]) -> list[dict[str, object]]:
    return [
        {"name": artifact.path.name, "sha256": artifact.sha256, "bytes": artifact.size_bytes}
        for artifact in artifacts
    ]


def _measurement_map(measurements: Sequence[CommandMeasurement]) -> list[dict[str, object]]:
    return [
        {
            "label": measurement.label,
            "wall_seconds": measurement.wall_seconds,
            "peak_rss_kib": measurement.peak_rss_kib,
        }
        for measurement in measurements
    ]


def _budget_checks(
    policy: ScalePolicy,
    *,
    proposal_measurements: Sequence[CommandMeasurement],
    fitting_artifact_bytes: int,
    result_clean: CommandMeasurement,
    result_probe: CommandMeasurement,
    result_incremental: CommandMeasurement,
    result_source_bytes: int,
    result_gfo_bytes: int,
    result_pgf_bytes: int,
) -> dict[str, dict[str, object]]:
    fitting = policy.fitting_budget.values
    result = policy.result_budget.values
    fitting_total = sum(item.wall_seconds for item in proposal_measurements)
    fitting_probe = sum(
        item.wall_seconds for item in proposal_measurements if "_probe_" in item.label
    )
    chunk_totals: Counter[str] = Counter()
    for item in proposal_measurements:
        if item.label.rsplit("_", 1)[-1].isdigit():
            chunk_totals[item.label.rsplit("_", 2)[0] + item.label.rsplit("_", 1)[-1]] += item.wall_seconds
    observed = {
        "fitting.total_wall_seconds": fitting_total,
        "fitting.chunk_wall_seconds": max(chunk_totals.values(), default=0.0),
        "fitting.probe_wall_seconds": fitting_probe,
        "fitting.peak_rss_kib": max(
            (item.peak_rss_kib for item in proposal_measurements), default=0
        ),
        "fitting.disposable_artifact_bytes": fitting_artifact_bytes,
        "result.clean_build_wall_seconds": result_clean.wall_seconds,
        "result.probe_wall_seconds": result_probe.wall_seconds,
        "result.incremental_build_wall_seconds": result_incremental.wall_seconds,
        "result.peak_rss_kib": max(
            result_clean.peak_rss_kib,
            result_probe.peak_rss_kib,
            result_incremental.peak_rss_kib,
        ),
        "result.gf_source_bytes": result_source_bytes,
        "result.gfo_bytes": result_gfo_bytes,
        "result.pgf_bytes": result_pgf_bytes,
    }
    limits = {
        **{f"fitting.{key}": value for key, value in fitting.items()},
        **{f"result.{key}": value for key, value in result.items()},
    }
    return {
        key: {
            "observed": observed[key],
            "limit": limits[key],
            "passed": observed[key] <= limits[key],
        }
        for key in sorted(observed)
    }


def run_scale_gate(
    *,
    gf_path: Path,
    database_path: Path = DEFAULT_DATABASE,
    noun_policy_path: Path = DEFAULT_NOUN_POLICY,
    feature_policy_path: Path = DEFAULT_FEATURE_POLICY,
    scale_policy_path: Path = DEFAULT_SCALE_POLICY,
    work_dir: Path = DEFAULT_SCALE_WORK,
    expected_snapshot: Mapping[str, object] | None = None,
) -> ScaleGateRun:
    policy = load_scale_policy(scale_policy_path)
    noun_policy = load_noun_policy(noun_policy_path)
    work_dir = work_dir.resolve()
    if work_dir.exists() and any(work_dir.iterdir()):
        raise NounError(f"scale work directory is not empty: {work_dir}")
    work_dir.mkdir(parents=True, exist_ok=True)
    selection = select_scale_population(
        database_path=database_path,
        noun_policy_path=noun_policy_path,
        feature_policy_path=feature_policy_path,
        scale_policy_path=scale_policy_path,
        expected_snapshot=expected_snapshot,
    )
    fitting_selection = _write_bytes(
        work_dir / "fitting-selection.tsv", selection_bytes(selection.fitting)
    )
    result_pool = _write_bytes(
        work_dir / "result-selection-pool.tsv", selection_bytes(selection.result_pool)
    )
    probe_binary, bridge_measurement = _compile_bridge(gf_path, work_dir / "bridge")
    fitting_run = fit_in_chunks(
        selected=selection.fitting,
        noun_policy=noun_policy,
        scale_policy=policy,
        gf_path=gf_path,
        probe_binary=probe_binary,
        work_dir=work_dir / "fitting",
        workload="fitting",
    )
    fitting_results = _write_bytes(
        work_dir / "fitting-results.json",
        fit_results_bytes(selection.fitting, fitting_run.fits),
    )
    result_fit_run = fit_in_chunks(
        selected=selection.result_pool,
        noun_policy=noun_policy,
        scale_policy=policy,
        gf_path=gf_path,
        probe_binary=probe_binary,
        work_dir=work_dir / "result-selection",
        workload="result_selection",
    )
    result_pool_results = _write_bytes(
        work_dir / "result-selection-results.json",
        fit_results_bytes(selection.result_pool, result_fit_run.fits),
    )
    chosen = select_result_entries(
        selection.result_pool, result_fit_run.fits, selection.result_quotas
    )
    chosen_items = tuple(item for item, _ in chosen)
    chosen_fits = tuple(fit for _, fit in chosen)
    chosen_selection = _write_bytes(
        work_dir / "result-selection.tsv", selection_bytes(chosen_items)
    )
    chosen_options = tuple(
        fit.accepted.option for fit in chosen_fits if fit.accepted is not None
    )
    if len(chosen_options) != policy.result_entries:
        raise NounError("resulting module did not receive one constructor per entry")
    result_dir = work_dir / "result"
    result_sources = render_option_modules(chosen_options, result_dir)
    result_pgf, result_pgf_hash, result_clean = _compile_gf(
        gf_path=gf_path, work_dir=result_dir, label="result_clean"
    )
    result_probe_artifact, result_probe = _run_probe(
        probe_binary=probe_binary,
        pgf_path=result_pgf,
        manifest_path=result_dir / "proposal-manifest.tsv",
        output_path=result_dir / "probe-output.tsv",
        label="result_probe",
    )
    result_records = decode_probe(result_probe_artifact.path.read_bytes(), chosen_options)
    result_fits = fit_candidates(
        tuple(item.sampled for item in chosen_items), chosen_options, result_records
    )
    original_records: dict[str, ProbeRecord] = {
        fit.sampled.internal_id: fit.accepted.record
        for fit in chosen_fits
        if fit.accepted is not None
    }
    for fit in result_fits:
        if fit.accepted is None:
            raise NounError(
                f"result module no longer reproduces accepted candidate {fit.sampled.internal_id}"
            )
        if fit.accepted.record != original_records[fit.sampled.internal_id]:
            raise NounError(
                f"result module changed complete record {fit.sampled.internal_id}"
            )
    _, incremental_pgf_hash, result_incremental = _compile_gf(
        gf_path=gf_path, work_dir=result_dir, label="result_incremental"
    )
    if incremental_pgf_hash != result_pgf_hash:
        raise NounError("incremental result build changed the PGF bytes")
    result_records_artifact = _write_bytes(
        work_dir / "result-records.json",
        fit_results_bytes(chosen_items, result_fits),
    )
    proposal_measurements = (
        *fitting_run.measurements,
        *result_fit_run.measurements,
    )
    fitting_artifact_bytes = (
        _directory_size(work_dir / "fitting")
        + _directory_size(work_dir / "result-selection")
    )
    result_source_bytes = sum(
        artifact.size_bytes for artifact in result_sources if artifact.path.suffix == ".gf"
    )
    result_gfo_bytes = _directory_size(result_dir / "gfo")
    result_pgf_bytes = result_pgf.stat().st_size
    budget_checks = _budget_checks(
        policy,
        proposal_measurements=proposal_measurements,
        fitting_artifact_bytes=fitting_artifact_bytes,
        result_clean=result_clean,
        result_probe=result_probe,
        result_incremental=result_incremental,
        result_source_bytes=result_source_bytes,
        result_gfo_bytes=result_gfo_bytes,
        result_pgf_bytes=result_pgf_bytes,
    )
    budget_passed = all(bool(check["passed"]) for check in budget_checks.values())
    constructor_counts = Counter(
        fit.accepted.option.constructor for fit in result_fits if fit.accepted is not None
    )
    tier_counts = Counter(
        item.classification.acceptance_tier.value for item in chosen_items
    )
    semantic_data = {
        "schema_version": 1,
        "gate_candidates": len(selection.fitting),
        "fitting_selection": {
            "sha256": fitting_selection.sha256,
            "bytes": fitting_selection.size_bytes,
            "strata": selection.fitting_quotas,
            "population_strata": selection.population_strata,
        },
        "fitting": {
            "proposals": fitting_run.proposal_count,
            "accepted": sum(fit.accepted is not None for fit in fitting_run.fits),
            "rejected": sum(fit.accepted is None for fit in fitting_run.fits),
            "results_sha256": fitting_results.sha256,
            "source_artifacts": _artifact_map(fitting_run.source_artifacts),
            "probe_artifacts": _artifact_map(fitting_run.probe_artifacts),
            "pgf_sha256": list(fitting_run.pgf_hashes),
        },
        "result_selection": {
            "pool_candidates": len(selection.result_pool),
            "pool_sha256": result_pool.sha256,
            "pool_results_sha256": result_pool_results.sha256,
            "target_quotas": selection.result_quotas,
            "selected_entries": len(chosen),
            "selected_sha256": chosen_selection.sha256,
        },
        "result": {
            "acceptance_tiers": dict(sorted(tier_counts.items())),
            "constructors": dict(sorted(constructor_counts.items())),
            "source_artifacts": _artifact_map(result_sources),
            "pgf_sha256": result_pgf_hash,
            "probe_sha256": result_probe_artifact.sha256,
            "records_sha256": result_records_artifact.sha256,
            "complete_records_compared": len(result_fits),
        },
    }
    semantic = _write_bytes(
        work_dir / "semantic-summary.json",
        (canonical_json(semantic_data) + "\n").encode("utf-8"),
    )
    measurement_data = {
        "schema_version": 1,
        "bridge": _measurement_map((bridge_measurement,)),
        "proposal_commands": _measurement_map(proposal_measurements),
        "result_commands": _measurement_map(
            (result_clean, result_probe, result_incremental)
        ),
        "artifact_bytes": {
            "fitting_disposable": fitting_artifact_bytes,
            "result_gf_source": result_source_bytes,
            "result_gfo": result_gfo_bytes,
            "result_pgf": result_pgf_bytes,
        },
        "budget_checks": budget_checks,
        "budget_passed": budget_passed,
    }
    measurements = _write_bytes(
        work_dir / "measurements.json",
        (canonical_json(measurement_data) + "\n").encode("utf-8"),
    )
    if policy.stop_on_budget_failure and not budget_passed:
        raise NounError(
            f"5,000 gate exceeded a frozen budget; measurements retained at {measurements.path}"
        )
    return ScaleGateRun(
        semantic=semantic,
        measurements=measurements,
        budget_passed=budget_passed,
        fitting_candidates=len(selection.fitting),
        result_entries=len(chosen),
    )
