"""Structured PGF probing and complete German noun-record comparison."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Mapping, Sequence

from wd2gf.nouns_ger import (
    DEFAULT_NOUN_WORK,
    PROBE_FIELDS,
    SLOT_FIELDS,
    NumberRestriction,
    NounArtifact,
    NounCandidate,
    NounError,
    NounPolicy,
    ProposalOption,
    SampledCandidate,
    SourceCompleteness,
    _write_bytes,
    proposal_blocker,
    render_proposal_modules,
)
from wd2gf.store import canonical_json


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RGL_ROOT = Path(__file__).resolve().parents[5]
HASKELL_PROBE = PROJECT_ROOT / "probe/NounProbe.hs"


class FieldEvidence(StrEnum):
    SOURCE_EXACT = "source_exact"
    REVIEWED_INFERENCE = "reviewed_inference"
    PROVISIONAL_INFERENCE = "provisional_inference"
    UNAVAILABLE = "unavailable"


class GFFit(StrEnum):
    EXACT_SOURCE_EVIDENCE = "exact_source_evidence"
    COMPATIBLE_WITH_INFERENCE = "compatible_with_inference"
    CONFLICTING = "conflicting"
    UNREPRESENTABLE = "unrepresentable"


class InferenceConfidence(StrEnum):
    SOURCE_EXACT = "source_exact"
    REVIEWED = "reviewed"
    PROVISIONAL = "provisional"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class ProbeRecord:
    option_id: str
    variant_index: int
    values: tuple[tuple[str, str], ...]
    no_linearization: bool = False

    def as_dict(self) -> dict[str, str]:
        return dict(self.values)


@dataclass(frozen=True)
class RecordComparison:
    option: ProposalOption
    record: ProbeRecord
    gf_fit: GFFit
    field_evidence: tuple[tuple[str, FieldEvidence], ...]
    mismatches: tuple[str, ...]


@dataclass(frozen=True)
class CandidateFit:
    sampled: SampledCandidate
    accepted: RecordComparison | None
    rejection_reason: str | None
    compared_options: int
    fitting_variants: int


@dataclass(frozen=True)
class ProbeRun:
    pgf_path: Path
    pgf_sha256: str
    raw_probe: NounArtifact
    details: NounArtifact
    fits: tuple[CandidateFit, ...]


def _run(command: Sequence[str], *, cwd: Path) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            list(command),
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as error:
        raise NounError(f"required probe command is unavailable: {command[0]}") from error
    except subprocess.CalledProcessError as error:
        stderr = error.stderr.decode("utf-8", errors="replace").strip()
        raise NounError(
            f"probe command failed ({command[0]}): {stderr[-4000:]}"
        ) from error


def _gf_core(gf_path: Path) -> tuple[Path, str]:
    try:
        resolved = gf_path.resolve(strict=True)
    except FileNotFoundError as error:
        raise NounError(f"GF executable does not exist: {gf_path}") from error
    if not os.access(resolved, os.X_OK):
        raise NounError(f"GF executable is not executable: {resolved}")
    gf_core = next((parent for parent in resolved.parents if parent.name == "gf-core"), None)
    if gf_core is None:
        raise NounError(f"GF executable resolves outside the local gf-core tree: {resolved}")
    version = resolved.parent.parent.name
    if not version or not version[0].isdigit():
        raise NounError(f"cannot derive GHC version from GF executable: {resolved}")
    return gf_core, version


def compile_probe(
    *,
    gf_path: Path,
    work_dir: Path = DEFAULT_NOUN_WORK,
) -> tuple[Path, str, Path]:
    gf_core, ghc_version = _gf_core(gf_path)
    rgl_library = RGL_ROOT / "dist/present"
    if not (rgl_library / "ParadigmsGer.gfo").is_file():
        raise NounError(
            "narrow probe requires the existing dist/present German RGL build"
        )
    gfo_dir = work_dir / "gfo"
    pgf_dir = work_dir / "pgf"
    haskell_dir = work_dir / "haskell"
    for directory in (gfo_dir, pgf_dir, haskell_dir):
        directory.mkdir(parents=True, exist_ok=True)
    concrete = work_dir / "WdnPilotGer.gf"
    if not concrete.is_file():
        raise NounError(f"rendered noun probe module is absent: {concrete}")
    _run(
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
    )
    pgf_path = pgf_dir / "WdnPilotAbs.pgf"
    if not pgf_path.is_file():
        raise NounError("GF did not produce the expected WdnPilotAbs.pgf")
    pgf_sha256 = hashlib.sha256(pgf_path.read_bytes()).hexdigest()

    stack_yaml = gf_core / f"stack-ghc{ghc_version}.yaml"
    if not stack_yaml.is_file():
        raise NounError(f"GF Stack build plan is absent: {stack_yaml}")
    probe_binary = work_dir / "NounProbe"
    _run(
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
            f"-outputdir={haskell_dir}",
            "-o",
            str(probe_binary),
            str(HASKELL_PROBE),
        ),
        cwd=gf_core,
    )
    return pgf_path, pgf_sha256, probe_binary


def run_structured_probe(
    *,
    probe_binary: Path,
    pgf_path: Path,
    manifest_path: Path,
    output_path: Path,
) -> NounArtifact:
    result = _run(
        (str(probe_binary), str(pgf_path), str(manifest_path)), cwd=PROJECT_ROOT
    )
    return _write_bytes(output_path, result.stdout)


def decode_probe(
    content: bytes, options: Sequence[ProposalOption]
) -> dict[str, tuple[ProbeRecord, ...]]:
    try:
        lines = content.decode("utf-8").splitlines()
    except UnicodeDecodeError as error:
        raise NounError("Haskell probe output is not UTF-8") from error
    expected_header = (
        "candidate_id\toption_id\tfunction_id\tvariant_index\tfield\tvalue_json"
    )
    if not lines or lines[0] != expected_header:
        raise NounError("Haskell probe output header does not match the TSV schema")
    options_by_id = {option.option_id: option for option in options}
    rows: dict[tuple[str, int], dict[str, str]] = {}
    no_linearization: set[tuple[str, int]] = set()
    for line_number, line in enumerate(lines[1:], start=2):
        fields = line.split("\t")
        if len(fields) != 6:
            raise NounError(f"invalid Haskell probe row {line_number}")
        candidate_id, option_id, function_id, raw_variant, field, value_json = fields
        option = options_by_id.get(option_id)
        if option is None or (
            option.candidate_id != candidate_id or option.function_id != function_id
        ):
            raise NounError(f"probe row {line_number} does not match the proposal manifest")
        try:
            variant_index = int(raw_variant)
        except ValueError as error:
            raise NounError(f"invalid probe variant index on row {line_number}") from error
        key = (option_id, variant_index)
        if field == "__no_linearization__" and value_json == "null":
            no_linearization.add(key)
            continue
        if field not in PROBE_FIELDS:
            raise NounError(f"unknown probe field on row {line_number}: {field}")
        try:
            value = json.loads(value_json)
        except json.JSONDecodeError as error:
            raise NounError(f"invalid JSON value on probe row {line_number}") from error
        if not isinstance(value, str):
            raise NounError(f"probe value on row {line_number} is not a string")
        record = rows.setdefault(key, {})
        if field in record:
            raise NounError(f"duplicate probe field on row {line_number}: {field}")
        record[field] = value

    result: dict[str, list[ProbeRecord]] = {option.option_id: [] for option in options}
    for option in options:
        option_keys = sorted(
            key for key in set(rows) | no_linearization if key[0] == option.option_id
        )
        if not option_keys:
            raise NounError(f"probe emitted no outcome for {option.option_id}")
        for key in option_keys:
            if key in no_linearization:
                result[option.option_id].append(
                    ProbeRecord(option.option_id, key[1], (), no_linearization=True)
                )
                continue
            values = rows[key]
            missing = sorted(set(PROBE_FIELDS) - set(values))
            if missing:
                raise NounError(
                    f"probe record {option.option_id}/{key[1]} is missing fields: {missing}"
                )
            result[option.option_id].append(
                ProbeRecord(
                    option.option_id,
                    key[1],
                    tuple((field, values[field]) for field in PROBE_FIELDS),
                )
            )
    return {key: tuple(value) for key, value in result.items()}


def compare_record(
    candidate: NounCandidate,
    option: ProposalOption,
    record: ProbeRecord,
) -> RecordComparison:
    if record.no_linearization:
        return RecordComparison(
            option,
            record,
            GFFit.UNREPRESENTABLE,
            (),
            ("no_linearization",),
        )
    values = record.as_dict()
    source_slots = {slot.field: slot.values for slot in candidate.slots}
    evidence: dict[str, FieldEvidence] = {}
    mismatches: list[str] = []
    for field in SLOT_FIELDS:
        unavailable = (
            candidate.number_restriction is NumberRestriction.PLURAL_ONLY
            and field.startswith("s_sg_")
        )
        if unavailable:
            evidence[field] = FieldEvidence.UNAVAILABLE
            if values[field] != "":
                mismatches.append(f"{field}:expected_unavailable")
        elif field in source_slots:
            evidence[field] = FieldEvidence.SOURCE_EXACT
            if values[field] not in source_slots[field]:
                mismatches.append(f"{field}:source_mismatch")
        else:
            evidence[field] = FieldEvidence.PROVISIONAL_INFERENCE

    if len(candidate.genders) == 1:
        evidence["gender"] = FieldEvidence.SOURCE_EXACT
        if values["gender"] != candidate.genders[0].value:
            mismatches.append("gender:source_mismatch")
    else:
        evidence["gender"] = FieldEvidence.PROVISIONAL_INFERENCE

    combining_values = {form.value for form in candidate.combining_forms}
    if len(combining_values) == 1:
        evidence["co"] = FieldEvidence.SOURCE_EXACT
        if values["co"] not in combining_values:
            mismatches.append("co:source_mismatch")
    else:
        evidence["co"] = FieldEvidence.PROVISIONAL_INFERENCE

    for field in PROBE_FIELDS:
        if field.startswith("uncap_"):
            source_field = field.removeprefix("uncap_")
            if source_field in evidence and evidence[source_field] is FieldEvidence.UNAVAILABLE:
                evidence[field] = FieldEvidence.UNAVAILABLE
                if values[field] != "":
                    mismatches.append(f"{field}:expected_unavailable")
            else:
                evidence[field] = FieldEvidence.REVIEWED_INFERENCE
    evidence["csep"] = (
        FieldEvidence.REVIEWED_INFERENCE
        if {"hyphen", "abbreviation"} & set(candidate.orthography)
        else FieldEvidence.PROVISIONAL_INFERENCE
    )
    if evidence["csep"] is FieldEvidence.REVIEWED_INFERENCE and values["csep"] != "hyphen":
        mismatches.append("csep:orthography_mismatch")

    if mismatches:
        fit = GFFit.CONFLICTING
    elif (
        candidate.source_completeness is SourceCompleteness.COMPLETE
        and len(candidate.genders) == 1
    ):
        fit = GFFit.EXACT_SOURCE_EVIDENCE
    else:
        fit = GFFit.COMPATIBLE_WITH_INFERENCE
    return RecordComparison(
        option=option,
        record=record,
        gf_fit=fit,
        field_evidence=tuple((field, evidence[field]) for field in PROBE_FIELDS),
        mismatches=tuple(mismatches),
    )


def fit_candidates(
    sample: Sequence[SampledCandidate],
    options: Sequence[ProposalOption],
    records: Mapping[str, Sequence[ProbeRecord]],
) -> tuple[CandidateFit, ...]:
    options_by_candidate: dict[str, list[ProposalOption]] = {}
    for option in options:
        options_by_candidate.setdefault(option.candidate_id, []).append(option)
    fits: list[CandidateFit] = []
    for sampled in sample:
        candidate = sampled.candidate
        blocker = proposal_blocker(candidate)
        candidate_options = options_by_candidate.get(sampled.internal_id, [])
        if blocker is not None:
            fits.append(CandidateFit(sampled, None, blocker, 0, 0))
            continue
        accepted: RecordComparison | None = None
        ambiguous_options = 0
        compared = 0
        for option in candidate_options:
            compared += 1
            comparisons = [
                compare_record(candidate, option, record)
                for record in records[option.option_id]
            ]
            matching_by_record = {
                comparison.record.values: comparison
                for comparison in comparisons
                if not comparison.mismatches
            }
            matching = tuple(matching_by_record.values())
            if len(matching) == 1:
                accepted = matching[0]
                break
            if len(matching) > 1:
                ambiguous_options += 1
        if accepted is not None:
            fits.append(CandidateFit(sampled, accepted, None, compared, 1))
        else:
            reason = (
                "ambiguous_gf_record_variants"
                if ambiguous_options
                else "no_public_constructor_matches_source_evidence"
            )
            fits.append(CandidateFit(sampled, None, reason, compared, ambiguous_options))
    return tuple(fits)


def probe_details_bytes(fits: Sequence[CandidateFit], pgf_sha256: str) -> bytes:
    rows = []
    for fit in fits:
        accepted = fit.accepted
        rows.append(
            {
                "candidate_id": fit.sampled.internal_id,
                "source_key": fit.sampled.candidate.source_key,
                "pgf_sha256": pgf_sha256,
                "accepted": accepted is not None,
                "rejection_reason": fit.rejection_reason,
                "compared_options": fit.compared_options,
                "fitting_variants": fit.fitting_variants,
                "constructor": accepted.option.constructor if accepted else None,
                "expression": accepted.option.expression if accepted else None,
                "gf_fit": accepted.gf_fit.value if accepted else GFFit.UNREPRESENTABLE.value,
                "record": accepted.record.as_dict() if accepted else None,
                "field_evidence": (
                    {field: status.value for field, status in accepted.field_evidence}
                    if accepted
                    else None
                ),
            }
        )
    return (canonical_json(rows) + "\n").encode("utf-8")


def _inference_confidence(comparison: RecordComparison) -> InferenceConfidence:
    statuses = {status for _, status in comparison.field_evidence}
    if FieldEvidence.PROVISIONAL_INFERENCE in statuses:
        return InferenceConfidence.PROVISIONAL
    if FieldEvidence.REVIEWED_INFERENCE in statuses:
        return InferenceConfidence.REVIEWED
    return InferenceConfidence.SOURCE_EXACT


def _source_statement_ids(candidate: NounCandidate) -> list[str]:
    return sorted(
        {
            *(claim.statement_key for claim in candidate.gender_claims),
            *(claim.statement_key for claim in candidate.restriction_claims),
            *(claim.statement_key for claim in candidate.paradigm_claims),
            *candidate.compound_statement_keys,
            *candidate.sense_statement_keys,
        }
    )


def _source_form_ids(candidate: NounCandidate) -> dict[str, list[str]]:
    result = {
        slot.field: [form.form_id for form in slot.forms] for slot in candidate.slots
    }
    if candidate.combining_forms:
        result["co"] = [form.form_id for form in candidate.combining_forms]
    return result


def _tsv(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> bytes:
    lines = ["\t".join(headers)]
    for row in rows:
        if len(row) != len(headers):
            raise NounError("noun pilot report row does not match its header")
        if any(character in field for field in row for character in "\t\r\n"):
            raise NounError("noun pilot report field escaped its structured TSV cell")
        lines.append("\t".join(row))
    return ("\n".join(lines) + "\n").encode("utf-8")


def noun_fit_bytes(fits: Sequence[CandidateFit], pgf_sha256: str) -> bytes:
    headers = (
        "internal_id",
        "source_key",
        "lexeme_ids_json",
        "entity_sha256_json",
        "lemma_json",
        "stratum",
        "pinned",
        "proposal_option_id",
        "constructor",
        "expression",
        "explicit_form_arguments",
        "source_completeness",
        "gf_fit",
        "inference_confidence",
        "review_status",
        "structural_evidence",
        "source_statement_ids_json",
        "source_form_ids_json",
        "p5548_evidence_json",
        "field_evidence_json",
        "complete_record_comparison",
        "gf_record_sha256",
        "pgf_sha256",
        *(f"gf_{field}_json" for field in PROBE_FIELDS),
    )
    rows: list[tuple[str, ...]] = []
    for fit in fits:
        if fit.accepted is None:
            continue
        sampled = fit.sampled
        candidate = sampled.candidate
        comparison = fit.accepted
        record = comparison.record.as_dict()
        record_json = canonical_json(record)
        rows.append(
            (
                sampled.internal_id,
                candidate.source_key,
                canonical_json(list(candidate.lexeme_ids)),
                canonical_json(list(candidate.entity_sha256)),
                canonical_json(candidate.lemma),
                candidate.stratum,
                "yes" if sampled.pinned else "no",
                comparison.option.option_id,
                comparison.option.constructor,
                comparison.option.expression,
                str(comparison.option.explicit_form_arguments),
                candidate.source_completeness.value,
                comparison.gf_fit.value,
                _inference_confidence(comparison).value,
                "sampled",
                candidate.structural_evidence.value,
                canonical_json(_source_statement_ids(candidate)),
                canonical_json(_source_form_ids(candidate)),
                canonical_json(list(candidate.object_form_evidence)),
                canonical_json(
                    {
                        field: evidence.value
                        for field, evidence in comparison.field_evidence
                    }
                ),
                "yes",
                hashlib.sha256(record_json.encode("utf-8")).hexdigest(),
                pgf_sha256,
                *(canonical_json(record[field]) for field in PROBE_FIELDS),
            )
        )
    return _tsv(headers, rows)


def _residual_api_gap(reason: str | None) -> str:
    return {
        "residual_api_gap_singular_only": "missing_public_singular_only_noun_constructor",
        "no_public_constructor_matches_source_evidence": "public_noun_constructor_gap",
    }.get(reason or "", "")


def noun_rejections_bytes(fits: Sequence[CandidateFit]) -> bytes:
    headers = (
        "internal_id",
        "source_key",
        "lexeme_ids_json",
        "entity_sha256_json",
        "lemma_json",
        "stratum",
        "pinned",
        "source_completeness",
        "gf_fit",
        "inference_confidence",
        "review_status",
        "rejection_reason",
        "residual_api_gap",
        "structural_evidence",
        "genders_json",
        "number_restriction",
        "source_statement_ids_json",
        "source_form_ids_json",
        "combining_forms_json",
        "p5548_evidence_json",
        "diagnostics_json",
        "compared_options",
        "fitting_variants",
    )
    rows: list[tuple[str, ...]] = []
    for fit in fits:
        if fit.accepted is not None:
            continue
        sampled = fit.sampled
        candidate = sampled.candidate
        combining = [
            {"form_id": form.form_id, "value": form.value}
            for form in candidate.combining_forms
        ]
        rows.append(
            (
                sampled.internal_id,
                candidate.source_key,
                canonical_json(list(candidate.lexeme_ids)),
                canonical_json(list(candidate.entity_sha256)),
                canonical_json(candidate.lemma),
                candidate.stratum,
                "yes" if sampled.pinned else "no",
                candidate.source_completeness.value,
                GFFit.UNREPRESENTABLE.value,
                InferenceConfidence.UNAVAILABLE.value,
                "rejected",
                fit.rejection_reason or "unknown_rejection",
                _residual_api_gap(fit.rejection_reason),
                candidate.structural_evidence.value,
                canonical_json([gender.value for gender in candidate.genders]),
                candidate.number_restriction.value,
                canonical_json(_source_statement_ids(candidate)),
                canonical_json(_source_form_ids(candidate)),
                canonical_json(combining),
                canonical_json(list(candidate.object_form_evidence)),
                canonical_json(list(candidate.diagnostics)),
                str(fit.compared_options),
                str(fit.fitting_variants),
            )
        )
    return _tsv(headers, rows)


def write_pilot_reports(
    *,
    fits: Sequence[CandidateFit],
    pgf_sha256: str,
    output_dir: Path,
) -> tuple[NounArtifact, NounArtifact]:
    return (
        _write_bytes(output_dir / "noun-fit.tsv", noun_fit_bytes(fits, pgf_sha256)),
        _write_bytes(
            output_dir / "noun-rejections.tsv", noun_rejections_bytes(fits)
        ),
    )


def probe_nouns(
    *,
    sample: Sequence[SampledCandidate],
    noun_policy: NounPolicy,
    gf_path: Path,
    work_dir: Path = DEFAULT_NOUN_WORK,
) -> ProbeRun:
    work_dir = work_dir.resolve()
    options, _ = render_proposal_modules(sample, noun_policy, work_dir)
    pgf_path, pgf_sha256, probe_binary = compile_probe(
        gf_path=gf_path, work_dir=work_dir
    )
    raw_probe = run_structured_probe(
        probe_binary=probe_binary,
        pgf_path=pgf_path,
        manifest_path=work_dir / "proposal-manifest.tsv",
        output_path=work_dir / "probe-output.tsv",
    )
    records = decode_probe(raw_probe.path.read_bytes(), options)
    fits = fit_candidates(sample, options, records)
    details = _write_bytes(
        work_dir / "fit-details.json", probe_details_bytes(fits, pgf_sha256)
    )
    return ProbeRun(pgf_path, pgf_sha256, raw_probe, details, fits)
