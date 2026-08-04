from __future__ import annotations

import hashlib
import tempfile
import tomllib
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from wd2gf.snapshot import (
    SnapshotError,
    checksum_for_filename,
    download_snapshot,
    load_metadata,
    resolve_snapshot,
    verify_snapshot,
)


class SnapshotTests(unittest.TestCase):
    def test_manifest_requires_one_exact_filename(self) -> None:
        filename = "wikidata-20260729-lexemes.json.gz"
        checksum = "a" * 40
        manifest = f"{checksum}  {filename}\n{'b' * 40}  other.json.gz\n"
        self.assertEqual(checksum_for_filename(manifest, filename), checksum)
        with self.assertRaisesRegex(SnapshotError, "found 0"):
            checksum_for_filename(manifest, "missing.json.gz")

    def test_resolve_writes_plan_without_local_sha256(self) -> None:
        filename = "wikidata-20260729-lexemes.json.gz"
        checksum = "a" * 40
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "snapshot.next.toml"
            with (
                patch(
                    "wd2gf.snapshot._read_text",
                    return_value=f"{checksum}  {filename}\n",
                ),
                patch("wd2gf.snapshot._content_length", return_value=123),
            ):
                metadata = resolve_snapshot(
                    date="20260729",
                    compression="gz",
                    next_path=plan_path,
                    lock_path=root / "snapshot.lock.toml",
                )
            self.assertNotIn("sha256", metadata)
            with plan_path.open("rb") as plan_file:
                persisted = tomllib.load(plan_file)
            self.assertEqual(persisted["dump_date"], "2026-07-29")
            self.assertEqual(persisted["size_bytes"], 123)

    def test_download_finalize_and_verify(self) -> None:
        payload = b"synthetic compressed bytes\n"
        sha1 = hashlib.sha1(payload).hexdigest()
        filename = "wikidata-20260729-lexemes.json.gz"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "snapshot.next.toml"
            lock_path = root / "snapshot.lock.toml"
            work_dir = root / "work"
            with (
                patch(
                    "wd2gf.snapshot._read_text", return_value=f"{sha1}  {filename}\n"
                ),
                patch("wd2gf.snapshot._content_length", return_value=len(payload)),
            ):
                resolve_snapshot(
                    date="20260729",
                    compression="gz",
                    next_path=plan_path,
                    lock_path=lock_path,
                )
            with patch("wd2gf.snapshot.urlopen", return_value=BytesIO(payload)):
                dump_path, lock = download_snapshot(
                    next_path=plan_path, lock_path=lock_path, work_dir=work_dir
                )
            self.assertEqual(dump_path.read_bytes(), payload)
            self.assertEqual(lock["sha256"], hashlib.sha256(payload).hexdigest())
            self.assertEqual(verify_snapshot(lock_path=lock_path, work_dir=work_dir)[0], dump_path)
            with self.assertRaisesRegex(SnapshotError, "refusing to replace"):
                download_snapshot(
                    next_path=plan_path, lock_path=lock_path, work_dir=work_dir
                )

    def test_verify_detects_changed_bytes(self) -> None:
        payload = b"original"
        sha1 = hashlib.sha1(payload).hexdigest()
        filename = "wikidata-20260729-lexemes.json.gz"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "snapshot.next.toml"
            lock_path = root / "snapshot.lock.toml"
            work_dir = root / "work"
            with (
                patch(
                    "wd2gf.snapshot._read_text", return_value=f"{sha1}  {filename}\n"
                ),
                patch("wd2gf.snapshot._content_length", return_value=len(payload)),
            ):
                resolve_snapshot(
                    date="20260729",
                    compression="gz",
                    next_path=plan_path,
                    lock_path=lock_path,
                )
            with patch("wd2gf.snapshot.urlopen", return_value=BytesIO(payload)):
                dump_path, _ = download_snapshot(
                    next_path=plan_path, lock_path=lock_path, work_dir=work_dir
                )
            dump_path.write_bytes(b"changed")
            with self.assertRaisesRegex(SnapshotError, "mismatch"):
                verify_snapshot(lock_path=lock_path, work_dir=work_dir)

    def test_rejects_invalid_date_and_compression(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(SnapshotError, "calendar"):
                resolve_snapshot(
                    date="20260230",
                    compression="gz",
                    next_path=root / "next",
                    lock_path=root / "lock",
                )
            with self.assertRaisesRegex(SnapshotError, "only supported"):
                resolve_snapshot(
                    date="20260729",
                    compression="bz2",
                    next_path=root / "next",
                    lock_path=root / "lock",
                )

    def test_rejects_filename_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plan_path = Path(temporary) / "snapshot.next.toml"
            plan_path.write_text(
                "\n".join(
                    [
                        "schema_version = 1",
                        'source = "wikidata-lexemes-json"',
                        'dump_date = "2026-07-29"',
                        'filename = "../../outside.gz"',
                        'url = "https://dumps.wikimedia.org/wikidatawiki/entities/20260729/wikidata-20260729-lexemes.json.gz"',
                        "size_bytes = 1",
                        'official_checksum_algorithm = "sha1"',
                        f'official_checksum = "{"a" * 40}"',
                        'license = "CC0-1.0"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SnapshotError, "filename or URL"):
                load_metadata(plan_path, finalized=False)


if __name__ == "__main__":
    unittest.main()
