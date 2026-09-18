"""Trusted Actions host: isolate tools, publish checkpoints, then advance the index."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bridge.artifacts import publish_snapshot, restore_snapshot
from bridge.creative_jobs import load_creative_job
from bridge.workspace_store import WorkspaceStore, now

TERMINAL = {"complete", "needs_review", "changes_requested", "failed", "blocked", "timed_out"}


def docker_command(image, descriptor, step_id, work, inputs, name):
    if not re.fullmatch(r"ghcr\.io/[a-z0-9._/-]+@sha256:[0-9a-f]{64}", image):
        raise ValueError("Runtime must be a digest-pinned GHCR image")
    return ["docker", "run", "--rm", "--name", name, "--network", "none", "--read-only",
            "--cap-drop=ALL", "--security-opt=no-new-privileges", "--pids-limit=512",
            "--memory=10g", "--cpus=3", "--user", f"{os.getuid()}:{os.getgid()}",
            "--tmpfs", "/tmp:rw,nosuid,size=2147483648", "--workdir", "/work",
            "--env", "HOME=/tmp/creative-home", "--env", "PYTHONDONTWRITEBYTECODE=1",
            "--env", "LIBGL_ALWAYS_SOFTWARE=1", "--env", "OMP_NUM_THREADS=3",
            "--mount", f"type=bind,src={ROOT},dst=/repo,readonly",
            "--mount", f"type=bind,src={inputs},dst=/input,readonly",
            "--mount", f"type=bind,src={work},dst=/work",
            image, "xvfb-run", "-a", "python3", "/repo/ci/execute_step.py",
            "--job", descriptor.relative_to(ROOT).as_posix(), "--step", step_id]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--local", action="store_true", help="No GitHub writes; useful for container smoke tests")
    args = parser.parse_args()
    descriptor = (ROOT / args.job).absolute()
    job, files = load_creative_job(descriptor, repo_root=ROOT)
    project, job_id = job["project_id"], job["job_id"]
    run_id, attempt = os.environ.get("GITHUB_RUN_ID", "0"), os.environ.get("GITHUB_RUN_ATTEMPT", "1")
    source_commit = os.environ.get("GITHUB_SHA") or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    repository = os.environ.get("GITHUB_REPOSITORY", "dekaazarashi1111-web/chatgpt-blender-bridge")
    store = None if args.local else WorkspaceStore(repository, source_commit)
    previous = store.get_job(project, job_id) if store else None
    if previous and previous.get("state") in TERMINAL:
        print(f"ALREADY_PROCESSED {project}/{job_id}; create a new revision to continue")
        return 0
    if previous and previous.get("state") == "running":
        prior_run = store.api("/actions/runs/" + str(int(previous["run_id"])))
        new_attempt = str(previous.get("run_id")) == run_id and str(previous.get("run_attempt")) != attempt
        if prior_run["status"] != "completed" and not new_attempt:
            print("ALREADY_RUNNING: waiting for existing run is safer than duplicate execution")
            return 0
        store.save({**previous, "state": "blocked", "next_action": "Previous execution was interrupted. Create a new job ID using the preserved latest_snapshot or step_snapshots; it will not restart from scratch."})
        print("INTERRUPTED: preserved previous checkpoints; submit a new revision to resume")
        return 0
    root = ROOT / ".creative-runs" / f"{project}-{job_id}-{run_id}-{attempt}"
    if root.exists():
        raise RuntimeError("Local run directory already exists; refusing to overwrite work")
    work, inputs, trusted = root / "work", root / "inputs", root / "trusted"
    for path in (work, inputs, trusted):
        path.mkdir(parents=True)
    for item, source in zip(job["inputs"], files.inputs):
        if hashlib.sha256(source.read_bytes()).hexdigest() != item["sha256"]:
            raise RuntimeError("Input changed after validation")
        target = inputs / item["target"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    record = {"schema_version": 2, "project_id": project, "job_id": job_id,
              "state": "running", "source_commit": source_commit, "runtime_image": args.image,
              "run_id": run_id, "run_attempt": attempt,
              "run_url": f"https://github.com/{repository}/actions/runs/{run_id}",
              "started_at": now(), "steps": [], "latest_snapshot": None, "step_snapshots": {},
              "acceptance_criteria": job["acceptance_criteria"], "review_required": job["review_required"],
              "next_action": "Wait for the current Actions run; do not submit duplicate work."}
    if store:
        store.save(record)
    deadline = time.monotonic() + job["timeout_seconds"]
    sequence = 0
    seen = set()
    last_publish = 0.0
    periodic_count = 0
    checkpoint_interval = max(120, job["timeout_seconds"] / 10)
    publication_errors = []

    def snapshot(source, current_step, kind):
        nonlocal sequence, last_publish
        sequence += 1
        if args.local:
            return
        saved = publish_snapshot(source, repository=repository, project_id=project, job_id=job_id,
                                 run_id=run_id, attempt=attempt, sequence=sequence,
                                 output_dir=trusted / "snapshots" / str(sequence),
                                 exclude_top_level=("checkpoints", "resume") if source == work else (),
                                 metadata={"source_commit": source_commit, "current_step": current_step,
                                           "kind": kind, "runtime_image": args.image})
        record["latest_snapshot"] = saved
        if kind == "step_complete":
            record["step_snapshots"][current_step] = saved
        record["current_step"] = current_step
        store.save(record)
        last_publish = time.monotonic()
        # The Release is verified and the pointer durable; reclaim the local archive.
        shutil.rmtree(trusted / "snapshots" / str(sequence))

    failure = None
    active_name = None
    try:
        if job.get("resume"):
            restore_snapshot(job["resume"], work / "resume", repository=repository, project_id=project)
        for step in job["steps"]:
            if time.monotonic() >= deadline:
                raise TimeoutError("Creative time budget exhausted; resume from the last published snapshot")
            step_deadline = min(deadline, time.monotonic() + step.get("timeout_seconds", job["timeout_seconds"]))
            active_name = f"creative-{run_id}-{attempt}-{step['id']}".lower()
            command = docker_command(args.image, descriptor, step["id"], work, inputs, active_name)
            log_path = trusted / f"{step['id']}.log"
            with log_path.open("w") as log:
                process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
                while process.poll() is None:
                    if time.monotonic() >= step_deadline:
                        subprocess.run(["docker", "stop", "--time", "10", active_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
                        process.wait(timeout=30)
                        raise TimeoutError(f"Step {step['id']} reached its time budget")
                    # Only checkpoint directories finalized by tool_entry are candidates.
                    # A failure to publish is recorded; the last good pointer is preserved.
                    if periodic_count < 12 and time.monotonic() - last_publish >= checkpoint_interval:
                        for marker in sorted((work / "checkpoints" / step["id"]).glob("*/checkpoint.json"), reverse=True):
                            if marker.parent.name.startswith("."):
                                continue
                            if marker in seen:
                                break
                            try:
                                snapshot(marker.parent, step["id"], "checkpoint")
                                seen.add(marker)
                                periodic_count += 1
                            except Exception as exc:
                                publication_errors.append(str(exc))
                                print(f"CHECKPOINT_PUBLISH_FAILED: {exc}", flush=True)
                                last_publish = time.monotonic()
                            break
                    time.sleep(5)
                exit_code = process.returncode
            active_name = None
            record["steps"].append({"id": step["id"], "tool": step["tool"], "exit_code": exit_code})
            if exit_code:
                print(log_path.read_text(errors="replace")[-12000:], flush=True)
                raise RuntimeError(f"Step {step['id']} failed with exit code {exit_code}; inspect Actions logs")
            # User process is stopped, so this is a consistent full workspace snapshot.
            snapshot(work, step["id"], "step_complete")
        record["state"] = "needs_review" if job["review_required"] else "complete"
        record["next_action"] = ("Inspect real previews against references; submit a pinned review or a new revision."
                                 if job["review_required"] else "Technical job completed; artifacts are available.")
    except Exception as exc:
        failure = exc
        record["state"] = "timed_out" if isinstance(exc, TimeoutError) else "failed"
        record["error"] = str(exc)
        record["next_action"] = "Read logs and latest_snapshot; submit a new job ID with that resume record."
    finally:
        if active_name:
            subprocess.run(["docker", "rm", "--force", active_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        if failure:
            try:
                snapshot(work, record.get("current_step", "failed"), "interrupted")
            except Exception as exc:
                publication_errors.append(str(exc))
        record["finished_at"] = now()
        record["publication_errors"] = publication_errors
        if store:
            try:
                record["previews"] = store.publish_previews(project, job_id, work)
            except Exception as exc:
                record["preview_publication_error"] = str(exc)
            try:
                store.save(record)
            except Exception as exc:
                record["state_publication_error"] = str(exc)
                failure = failure or exc
        (trusted / "result.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps(record, indent=2, ensure_ascii=False))
    return 1 if failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
