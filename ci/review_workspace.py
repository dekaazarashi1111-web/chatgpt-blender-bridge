"""Apply explicit reviews pinned to the exact generated snapshot."""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bridge.workspace_store import WorkspaceStore


def apply_review(review, record):
    required = {"schema_version", "project_id", "job_id", "source_commit", "snapshot_sha256", "verdict", "criteria", "summary"}
    if set(review) != required or review["schema_version"] != 1:
        raise ValueError("Review schema mismatch")
    if review["verdict"] not in {"approved", "changes_requested"}:
        raise ValueError("Invalid review verdict")
    if not isinstance(review["summary"], str) or not 1 <= len(review["summary"]) <= 4000:
        raise ValueError("Review needs a meaningful summary")
    for key in ("project_id", "job_id", "source_commit"):
        if review[key] != record[key]:
            raise ValueError(f"Review {key} does not match generated output")
    if review["snapshot_sha256"] != record["latest_snapshot"]["archive_sha256"]:
        raise ValueError("Review refers to a different checkpoint")
    if not isinstance(review["criteria"], dict) or set(review["criteria"]) != set(record["acceptance_criteria"]):
        raise ValueError("Review must cover every acceptance criterion")
    if any(result not in {"pass", "fail"} for result in review["criteria"].values()):
        raise ValueError("Criterion values must be pass or fail")
    if review["verdict"] == "approved" and any(result != "pass" for result in review["criteria"].values()):
        raise ValueError("All criteria must pass before approval")
    if record["state"] != "needs_review":
        raise ValueError("Only technically successful output awaiting review can be reviewed")
    return {**record, "state": "complete" if review["verdict"] == "approved" else "changes_requested",
            "review": review, "next_action": "Finished." if review["verdict"] == "approved" else "Create a new revision using latest_snapshot."}


def main():
    store = WorkspaceStore(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_SHA"])
    for path in sorted((ROOT / "projects").glob("*/reviews/*.json")):
        review = json.loads(path.read_text())
        project, job = path.parent.parent.name, path.stem
        record = store.get_job(project, job)
        if not record:
            raise ValueError(f"No generated result for review {project}/{job}")
        if record.get("review") == review:
            continue
        store.save(apply_review(review, record), review_only=True)


if __name__ == "__main__":
    main()
