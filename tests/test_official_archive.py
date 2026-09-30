"""Frozen official snapshots must be verified before restoration."""
from __future__ import annotations

import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from scripts.replicate_official import restore_frozen_official_inputs


class OfficialArchiveTest(unittest.TestCase):
    def test_downloads_and_checks_deposit_before_restoring_missing_cache(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache = root / "data/reference/frozen_official"
            cache.mkdir(parents=True)
            blob = b"frozen data"
            (cache.parent / "replication_input_manifest.json").write_text(json.dumps({"files": [{
                "path": "data/raw/statbank_pris01.csv", "bytes": len(blob),
                "sha256": hashlib.sha256(blob).hexdigest(),
            }]}), encoding="utf-8")
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w") as archive:
                archive.writestr("statbank_pris01.csv", blob)
            payload = buffer.getvalue()
            (cache / "archive_manifest.json").write_text(json.dumps({
                "url": "https://example.test/frozen.zip", "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }), encoding="utf-8")
            with patch("scripts.replicate_official.urllib.request.urlopen", return_value=io.BytesIO(payload)):
                restore_frozen_official_inputs(root)
            self.assertEqual((cache / "statbank_pris01.csv").read_bytes(), blob)
            self.assertEqual((root / "data/raw/statbank_pris01.csv").read_bytes(), blob)

    def test_restores_missing_raw_file_without_overwriting_existing_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "data/reference/frozen_official"
            archive.mkdir(parents=True)
            source = archive / "statbank_pris01.csv"
            source.write_bytes(b"frozen data")
            manifest = root / "data/reference/replication_input_manifest.json"
            manifest.write_text(json.dumps({"files": [{
                "path": "data/raw/statbank_pris01.csv",
                "bytes": source.stat().st_size,
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            }]}), encoding="utf-8")
            restore_frozen_official_inputs(root)
            target = root / "data/raw/statbank_pris01.csv"
            self.assertEqual(target.read_bytes(), b"frozen data")
            target.write_bytes(b"different data")
            restore_frozen_official_inputs(root)
            self.assertEqual(target.read_bytes(), b"different data")
            source.write_bytes(b"broken data")
            with self.assertRaisesRegex(RuntimeError, "hash mismatch"):
                restore_frozen_official_inputs(root)


if __name__ == "__main__":
    unittest.main()
