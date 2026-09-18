"""Restore a SHA-256-pinned same-project workspace before starting offline tools."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bridge.artifacts import ArtifactError, MAX_MANIFEST_BYTES, restore_snapshot
from bridge.state import atomic_write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", type=Path, required=True, help="Verified resume pointer JSON")
    parser.add_argument("--destination", type=Path, required=True, help="New or empty directory")
    parser.add_argument("--project", required=True)
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY"), required=not os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--manifest", type=Path, help="Optionally copy restored manifest here")
    args = parser.parse_args()
    try:
        if args.record.stat().st_size > MAX_MANIFEST_BYTES:
            raise ArtifactError("Resume pointer exceeds quota")
        record = json.loads(args.record.read_text())
        manifest = restore_snapshot(record, args.destination, repository=args.repository, project_id=args.project)
        if args.manifest:
            atomic_write_json(args.manifest, manifest)
    except (ArtifactError, OSError, ValueError) as exc:
        print(f"Workspace restore failed: {exc}", file=sys.stderr)
        return 1
    print(f"Restored {manifest['file_count']} files from {record['release_tag']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
