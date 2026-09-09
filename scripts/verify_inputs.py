"""Verify research snapshots without changing inputs or their manifest."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "data/reference/replication_input_manifest.json").read_text())
    failures = []
    for record in manifest["files"]:
        path = root / record["path"]
        if not path.exists():
            failures.append(f"Missing: {record['path']}")
            continue
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != record["sha256"] or path.stat().st_size != record["bytes"]:
            failures.append(f"Snapshot mismatch: {record['path']}")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"Verified {len(manifest['files'])} research inputs against SHA-256 manifest.")


if __name__ == "__main__":
    main()
