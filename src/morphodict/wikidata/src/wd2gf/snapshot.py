"""Dated Wikidata Lexeme snapshot lifecycle."""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
import tomllib
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date as calendar_date
from pathlib import Path
from typing import BinaryIO
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_NEXT = PROJECT_ROOT / "snapshot.next.toml"
DEFAULT_LOCK = PROJECT_ROOT / "languages/ger/snapshot.lock.toml"
DEFAULT_WORK_DIR = PROJECT_ROOT / ".work/snapshots"
SOURCE = "wikidata-lexemes-json"
LICENSE = "CC0-1.0"
BASE_URL = "https://dumps.wikimedia.org/wikidatawiki/entities"
USER_AGENT = "wd2gf-ger-profile/0.1 (https://github.com/GrammaticalFramework/gf-rgl)"
CHUNK_SIZE = 1024 * 1024
DATE_PATTERN = re.compile(r"^(\d{4})(\d{2})(\d{2})$")
SHA1_PATTERN = re.compile(r"^([0-9a-fA-F]{40})\s+\*?(\S+)$")

PLAN_KEYS = {
    "schema_version",
    "source",
    "dump_date",
    "filename",
    "url",
    "size_bytes",
    "official_checksum_algorithm",
    "official_checksum",
    "license",
}
LOCK_KEYS = PLAN_KEYS | {"sha256"}


class SnapshotError(RuntimeError):
    """A snapshot lifecycle invariant was violated."""


def _quoted(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _write_metadata(path: Path, metadata: dict[str, object], *, replace: bool) -> None:
    if path.exists() and not replace:
        raise SnapshotError(f"refusing to replace existing metadata: {path}")
    order = [
        "schema_version",
        "source",
        "dump_date",
        "filename",
        "url",
        "size_bytes",
        "official_checksum_algorithm",
        "official_checksum",
        "sha256",
        "license",
    ]
    lines: list[str] = []
    for key in order:
        if key not in metadata:
            continue
        value = metadata[key]
        rendered = str(value) if isinstance(value, int) else _quoted(str(value))
        lines.append(f"{key} = {rendered}")
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="\n") as output:
            output.write("\n".join(lines) + "\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def load_metadata(path: Path, *, finalized: bool) -> dict[str, object]:
    try:
        with path.open("rb") as metadata_file:
            metadata = tomllib.load(metadata_file)
    except FileNotFoundError as error:
        kind = "finalized lock" if finalized else "snapshot plan"
        raise SnapshotError(f"missing {kind}: {path}") from error
    expected = LOCK_KEYS if finalized else PLAN_KEYS
    if set(metadata) != expected:
        missing = sorted(expected - set(metadata))
        extra = sorted(set(metadata) - expected)
        raise SnapshotError(f"invalid metadata keys; missing={missing}, extra={extra}")
    if metadata["schema_version"] != 1 or metadata["source"] != SOURCE:
        raise SnapshotError("unsupported snapshot metadata schema or source")
    if metadata["official_checksum_algorithm"] != "sha1":
        raise SnapshotError("unsupported official checksum algorithm")
    if metadata["license"] != LICENSE:
        raise SnapshotError("unexpected source license identifier")
    string_keys = expected - {"schema_version", "size_bytes"}
    if any(not isinstance(metadata[key], str) for key in string_keys):
        raise SnapshotError("snapshot string metadata has an invalid type")
    if not isinstance(metadata["size_bytes"], int) or metadata["size_bytes"] <= 0:
        raise SnapshotError("size_bytes must be a positive integer")
    try:
        dump_date = calendar_date.fromisoformat(str(metadata["dump_date"]))
    except ValueError as error:
        raise SnapshotError("dump_date must be a valid ISO date") from error
    compact_date = dump_date.strftime("%Y%m%d")
    expected_filename = f"wikidata-{compact_date}-lexemes.json.gz"
    expected_url = f"{BASE_URL}/{compact_date}/{expected_filename}"
    if metadata["filename"] != expected_filename or metadata["url"] != expected_url:
        raise SnapshotError("filename or URL does not match the explicit dated gzip source")
    if re.fullmatch(r"[0-9a-f]{40}", str(metadata["official_checksum"])) is None:
        raise SnapshotError("official_checksum must be a lowercase SHA-1")
    if finalized and re.fullmatch(r"[0-9a-f]{64}", str(metadata["sha256"])) is None:
        raise SnapshotError("sha256 must be a lowercase SHA-256")
    return metadata


def _date_parts(date: str) -> tuple[str, str, str]:
    match = DATE_PATTERN.fullmatch(date)
    if match is None:
        raise SnapshotError("dump date must use YYYYMMDD")
    year, month, day = match.groups()
    try:
        calendar_date(int(year), int(month), int(day))
    except ValueError as error:
        raise SnapshotError(f"invalid calendar date: {date}") from error
    return year, month, day


def _read_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request) as response:
            return response.read().decode("utf-8")
    except (HTTPError, URLError, UnicodeDecodeError) as error:
        raise SnapshotError(f"could not read official manifest {url}: {error}") from error


def _content_length(url: str) -> int:
    request = Request(url, headers={"User-Agent": USER_AGENT}, method="HEAD")
    try:
        with urlopen(request) as response:
            value = response.headers.get("Content-Length")
    except (HTTPError, URLError) as error:
        raise SnapshotError(f"could not read published size for {url}: {error}") from error
    if value is None or not value.isascii() or not value.isdigit():
        raise SnapshotError(f"official response has no valid Content-Length for {url}")
    return int(value)


def checksum_for_filename(manifest: str, filename: str) -> str:
    matches: list[str] = []
    for line in manifest.splitlines():
        match = SHA1_PATTERN.fullmatch(line.strip())
        if match is not None and match.group(2) == filename:
            matches.append(match.group(1).lower())
    if len(matches) != 1:
        raise SnapshotError(
            f"expected exactly one {filename!r} entry in official SHA-1 manifest; "
            f"found {len(matches)}"
        )
    return matches[0]


def resolve_snapshot(
    *,
    date: str,
    compression: str,
    next_path: Path = DEFAULT_NEXT,
    lock_path: Path = DEFAULT_LOCK,
    replace_plan: bool = False,
) -> dict[str, object]:
    year, month, day = _date_parts(date)
    if compression != "gz":
        raise SnapshotError("the only supported compression is gz")
    if lock_path.exists():
        raise SnapshotError(
            f"a finalized lock already exists at {lock_path}; use an explicit replacement workflow"
        )
    filename = f"wikidata-{date}-lexemes.json.{compression}"
    directory = f"{BASE_URL}/{date}"
    manifest_url = f"{directory}/wikidata-{date}-sha1sums.txt"
    url = f"{directory}/{filename}"
    checksum = checksum_for_filename(_read_text(manifest_url), filename)
    metadata: dict[str, object] = {
        "schema_version": 1,
        "source": SOURCE,
        "dump_date": f"{year}-{month}-{day}",
        "filename": filename,
        "url": url,
        "size_bytes": _content_length(url),
        "official_checksum_algorithm": "sha1",
        "official_checksum": checksum,
        "license": LICENSE,
    }
    _write_metadata(next_path, metadata, replace=replace_plan)
    return metadata


@contextmanager
def _download_stream(url: str) -> Iterator[BinaryIO]:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request) as response:
            yield response
    except (HTTPError, URLError) as error:
        raise SnapshotError(f"download failed for {url}: {error}") from error


def _hash_file(path: Path) -> tuple[int, str, str]:
    size = 0
    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(CHUNK_SIZE):
            size += len(chunk)
            sha1.update(chunk)
            sha256.update(chunk)
    return size, sha1.hexdigest(), sha256.hexdigest()


def _validate_hashes(
    metadata: dict[str, object], *, size: int, sha1: str, sha256: str | None
) -> None:
    if size != metadata["size_bytes"]:
        raise SnapshotError(
            f"size mismatch: expected {metadata['size_bytes']}, computed {size}"
        )
    if sha1 != metadata["official_checksum"]:
        raise SnapshotError(
            f"official SHA-1 mismatch: expected {metadata['official_checksum']}, computed {sha1}"
        )
    expected_sha256 = metadata.get("sha256")
    if expected_sha256 is not None and sha256 != expected_sha256:
        raise SnapshotError(
            f"local SHA-256 mismatch: expected {expected_sha256}, computed {sha256}"
        )


def download_snapshot(
    *,
    next_path: Path = DEFAULT_NEXT,
    lock_path: Path = DEFAULT_LOCK,
    work_dir: Path = DEFAULT_WORK_DIR,
    replace: bool = False,
) -> tuple[Path, dict[str, object]]:
    plan = load_metadata(next_path, finalized=False)
    dump_path = work_dir / str(plan["filename"])
    if (lock_path.exists() or dump_path.exists()) and not replace:
        raise SnapshotError(
            "refusing to replace an existing finalized lock or dump; pass --replace explicitly"
        )
    work_dir.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        dir=work_dir, prefix=f".{dump_path.name}.", suffix=".part"
    )
    temporary_path = Path(temporary_name)
    size = 0
    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()
    try:
        with os.fdopen(file_descriptor, "wb") as output, _download_stream(
            str(plan["url"])
        ) as source:
            while chunk := source.read(CHUNK_SIZE):
                output.write(chunk)
                size += len(chunk)
                sha1.update(chunk)
                sha256.update(chunk)
            output.flush()
            os.fsync(output.fileno())
        _validate_hashes(
            plan, size=size, sha1=sha1.hexdigest(), sha256=sha256.hexdigest()
        )
        finalized = dict(plan)
        finalized["sha256"] = sha256.hexdigest()
        os.replace(temporary_path, dump_path)
        _write_metadata(lock_path, finalized, replace=replace)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise
    return dump_path, finalized


def verify_snapshot(
    *,
    lock_path: Path = DEFAULT_LOCK,
    work_dir: Path = DEFAULT_WORK_DIR,
) -> tuple[Path, dict[str, object]]:
    lock = load_metadata(lock_path, finalized=True)
    dump_path = work_dir / str(lock["filename"])
    try:
        size, sha1, sha256 = _hash_file(dump_path)
    except FileNotFoundError as error:
        raise SnapshotError(f"verified dump is not retained at {dump_path}") from error
    _validate_hashes(lock, size=size, sha1=sha1, sha256=sha256)
    return dump_path, lock
