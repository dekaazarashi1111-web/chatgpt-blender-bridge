"""Publish a workspace after its files have finished writing."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bridge.artifacts import ArtifactError, publish_snapshot
from bridge.state import atomic_write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True, help="Temporary archive directory outside source")
    parser.add_argument("--record", type=Path, required=True, help="Write verified resume pointer here")
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY"), required=not os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--project", required=True)
    parser.add_argument("--job", required=True)
    parser.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID"), required=not os.environ.get("GITHUB_RUN_ID"))
    parser.add_argument("--attempt", type=int, default=int(os.environ.get("GITHUB_RUN_ATTEMPT", "1")))
    parser.add_argument("--sequence", type=int, required=True)
    parser.add_argument("--exclude-top-level", action="append", default=[], help="Omit a top-level directory from a final snapshot")
    parser.add_argument("--metadata", type=Path, help="Optional execution metadata JSON")
    args = parser.parse_args()
    try:
        metadata = json.loads(args.metadata.read_text()) if args.metadata else None
        record = publish_snapshot(args.source, repository=args.repository, project_id=args.project,
                                  job_id=args.job, run_id=args.run_id, attempt=args.attempt,
                                  sequence=args.sequence, output_dir=args.output_dir, metadata=metadata,
                                  exclude_top_level=tuple(args.exclude_top_level))
        atomic_write_json(args.record, record)
    except (ArtifactError, OSError, ValueError) as exc:
        print(f"Workspace publication failed: {exc}", file=sys.stderr)
        return 1
    print(f"Saved workspace: {record['release_url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
