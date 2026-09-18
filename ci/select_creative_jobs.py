"""Select generic pending work; each project is serialized by Actions concurrency."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bridge.creative_jobs import load_creative_job
from bridge.workspace_store import WorkspaceStore


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", default="")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.job:
        descriptor = (ROOT / args.job).absolute()
        if not descriptor.is_relative_to(ROOT / "projects"):
            raise ValueError("Job path must be inside projects")
        descriptors = [descriptor]
    else:
        descriptors = sorted((ROOT / "projects").glob("*/jobs/*/job.json"))
    selected = []
    store = None if args.validate_only else WorkspaceStore(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_SHA"])
    for descriptor in descriptors:
        job, _ = load_creative_job(descriptor, repo_root=ROOT)
        previous = store.get_job(job["project_id"], job["job_id"]) if store else None
        if previous and previous.get("state") in {"complete", "needs_review", "changes_requested", "failed", "blocked", "timed_out"}:
            continue
        selected.append({"project": job["project_id"], "job": descriptor.relative_to(ROOT).as_posix()})
    if len(selected) > 32:
        raise RuntimeError("At most 32 pending jobs per run; submit remaining work in a later batch")
    matrix = json.dumps({"include": selected}, separators=(",", ":"))
    print(matrix)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as stream:
            stream.write(f"matrix={matrix}\nhas_jobs={'true' if selected else 'false'}\n")


if __name__ == "__main__":
    main()
