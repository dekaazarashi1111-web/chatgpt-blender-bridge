from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import traceback
from typing import Iterator

from .config import ROOT, locate_blender
from .git_queue import GitError, github_author, publish, sync
from .jobs import JobError, load_job
from .state import atomic_write_json, file_record, publish_artifacts, utc_now


TERMINAL_STATES = {"needs_review", "changes_requested", "complete", "failed", "blocked"}


@contextmanager
def worker_lock() -> Iterator[None]:
    lock_path = ROOT / ".worker" / "worker.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    stream = lock_path.open("a+b")
    try:
        if os.name == "nt":
            import msvcrt

            stream.seek(0)
            if stream.tell() == 0:
                stream.write(b"0")
                stream.flush()
            stream.seek(0)
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise RuntimeError("Another worker process already holds the lock") from exc
        else:
            import fcntl

            try:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise RuntimeError("Another worker process already holds the lock") from exc
        yield
    finally:
        if os.name == "nt":
            import msvcrt

            stream.seek(0)
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
        else:
            import fcntl

            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        stream.close()


def _status_path(job_id: str) -> Path:
    return ROOT / "queue" / "status" / f"{job_id}.json"


def _write_status(
    job_id: str,
    payload: dict,
    *,
    config: dict,
    publish_update: bool,
    path_override: Path | None = None,
) -> str | None:
    path = path_override or _status_path(job_id)
    atomic_write_json(path, payload)
    if publish_update:
        return publish(
            [path],
            f"worker({job_id}): {payload['state']}",
            config["branch"],
            push=config["git_publish"],
        )
    return None


def _run_process(command: list[str], log_path: Path, timeout: int) -> tuple[int, bool]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.setdefault("LIBGL_ALWAYS_SOFTWARE", "1")
    started = time.monotonic()
    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"COMMAND={' '.join(command)}\n")
        log.flush()
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )
        timed_out = False
        while process.poll() is None:
            if time.monotonic() - started > timeout:
                timed_out = True
                log.write(f"TIMEOUT after {timeout} seconds\n")
                log.flush()
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)
                break
            time.sleep(0.25)
        return process.returncode if process.returncode is not None else 1, timed_out


def _criteria(job: dict, checks: dict[str, bool]) -> list[dict]:
    records: list[dict] = []
    for criterion in job["acceptance_criteria"]:
        if criterion["kind"] == "automatic":
            passed = bool(checks.get(criterion["check"], False))
            status = "pass" if passed else "fail"
        else:
            status = "pending_review"
        records.append({**criterion, "status": status})
    return records


def process_job(
    descriptor: Path,
    config: dict,
    *,
    check_author: bool = True,
    publish_updates: bool = True,
    publish_results: bool = True,
    run_dir_override: Path | None = None,
    status_path_override: Path | None = None,
) -> dict:
    job: dict | None = None
    try:
        job, files = load_job(descriptor)
        job_id = job["job_id"]
    except Exception as exc:
        fallback = descriptor.parent.name
        payload = {
            "schema_version": 1,
            "job_id": fallback,
            "state": "blocked",
            "updated_at": utc_now(),
            "reason_code": "invalid_job",
            "reason_detail": str(exc),
        }
        if fallback and all(character.isalnum() or character in "._-" for character in fallback):
            _write_status(
                fallback,
                payload,
                config=config,
                publish_update=publish_updates,
                path_override=status_path_override,
            )
        return payload

    author = "local-smoke"
    source_commit = "local"
    if check_author:
        author, source_commit = github_author(files.descriptor, config["repository"])
        if config["require_trusted_author"] and author not in config["trusted_authors"]:
            payload = {
                "schema_version": 1,
                "job_id": job_id,
                "state": "blocked",
                "updated_at": utc_now(),
                "reason_code": "untrusted_author",
                "reason_detail": f"GitHub author {author!r} is not trusted",
                "source_commit": source_commit,
                "author": author,
            }
            _write_status(
                job_id,
                payload,
                config=config,
                publish_update=publish_updates,
                path_override=status_path_override,
            )
            return payload

    run_dir = run_dir_override or (ROOT / ".worker" / "runs" / job_id / source_commit[:12])
    run_dir.mkdir(parents=True, exist_ok=True)
    running = {
        "schema_version": 1,
        "job_id": job_id,
        "title": job["title"],
        "state": "running",
        "updated_at": utc_now(),
        "source_commit": source_commit,
        "author": author,
        "checkpoint": ".worker runtime checkpoint",
    }
    _write_status(
        job_id,
        running,
        config=config,
        publish_update=publish_updates,
        path_override=status_path_override,
    )

    blender = locate_blender(config["blender_bin"])
    command = [str(blender), "--background", "--factory-startup", "--disable-autoexec"]
    source_blend = job.get("source_blend")
    if source_blend:
        command.append(str((ROOT / source_blend).resolve()))
    command.extend(
        [
            "--python-exit-code", "1",
            "--python", str(ROOT / "bridge" / "blender_entry.py"),
            "--",
            "--job", str(files.descriptor),
            "--script", str(files.script),
            "--run-dir", str(run_dir),
        ]
    )
    timeout = min(job["timeout_seconds"], config["max_job_seconds"])
    blender_code, timed_out = _run_process(command, run_dir / "blender.log", timeout)
    output_blend = run_dir / "output" / "model.blend"
    validation_path = run_dir / "validation.json"
    validation_code = 1
    if blender_code == 0 and output_blend.is_file():
        validation_command = [
            str(blender), "--background", "--disable-autoexec", str(output_blend),
            "--python-exit-code", "1",
            "--python", str(ROOT / "bridge" / "blender_validate.py"),
            "--", "--report", str(validation_path),
        ]
        validation_code, validation_timeout = _run_process(
            validation_command,
            run_dir / "blender.log",
            min(600, timeout),
        )
        timed_out = timed_out or validation_timeout
    validation = {}
    if validation_path.is_file():
        validation = json.loads(validation_path.read_text(encoding="utf-8"))
    checks: dict[str, bool] = {
        "script_exit": blender_code == 0 and not timed_out,
        "blend_exists": output_blend.is_file() and output_blend.stat().st_size > 0,
        "reopen_ok": validation_code == 0 and validation.get("pass") is True,
        "report_exists": (run_dir / "blender_report.json").is_file(),
    }
    for view in job["preview"]["views"]:
        preview_path = run_dir / "previews" / f"{view}.png"
        checks[f"preview:{view}"] = preview_path.is_file() and preview_path.stat().st_size > 0
    criteria = _criteria(job, checks)
    automatic_pass = all(item["status"] == "pass" for item in criteria if item["kind"] == "automatic")
    required_checks = ["script_exit", "blend_exists", "reopen_ok", "report_exists"] + [
        f"preview:{view}" for view in job["preview"]["views"]
    ]
    technical_pass = all(checks.get(name, False) for name in required_checks)
    if not automatic_pass or not technical_pass or blender_code != 0 or validation_code != 0 or timed_out:
        state = "failed"
    elif job["review_required"]:
        state = "needs_review"
    else:
        state = "complete"

    destination: Path | None = None
    published_artifacts: dict = {}
    if publish_results:
        destination, published_artifacts = publish_artifacts(job_id, run_dir, config["max_publish_bytes"])
    else:
        published_artifacts = {
            "model.blend": file_record(output_blend),
            **{
                f"previews/{view}.png": file_record(run_dir / "previews" / f"{view}.png")
                for view in job["preview"]["views"]
            },
        }
    manifest = {
        "schema_version": 1,
        "job_id": job_id,
        "title": job["title"],
        "state": state,
        "started_from_commit": source_commit,
        "author": author,
        "finished_at": utc_now(),
        "blender_exit_code": blender_code,
        "validation_exit_code": validation_code,
        "timed_out": timed_out,
        "checks": checks,
        "acceptance_criteria": criteria,
        "review_required": job["review_required"],
        "artifacts": published_artifacts,
        "checkpoint": json.loads((run_dir / "checkpoint.json").read_text(encoding="utf-8"))
        if (run_dir / "checkpoint.json").is_file() else None,
    }
    manifest_path = (destination / "manifest.json") if destination else (run_dir / "manifest.json")
    atomic_write_json(manifest_path, manifest)
    status = {
        "schema_version": 1,
        "job_id": job_id,
        "title": job["title"],
        "state": state,
        "updated_at": utc_now(),
        "source_commit": source_commit,
        "author": author,
        "reason_code": "timeout" if timed_out else ("verification_failed" if state == "failed" else None),
        "manifest": (Path("results") / job_id / "manifest.json").as_posix() if publish_results else str(manifest_path),
    }
    status_path = status_path_override or _status_path(job_id)
    atomic_write_json(status_path, status)
    if publish_updates:
        publish_paths = [status_path]
        if destination:
            publish_paths.append(destination)
        result_commit = publish(
            publish_paths,
            f"worker({job_id}): {state}",
            config["branch"],
            push=config["git_publish"],
        )
        status["result_commit"] = result_commit
        atomic_write_json(status_path, status)
        publish(
            [status_path],
            f"worker({job_id}): record result commit",
            config["branch"],
            push=config["git_publish"],
        )
    return manifest


def reconcile_reviews(config: dict, *, publish_updates: bool = True, check_author: bool = True) -> int:
    changed = 0
    for review_path in sorted((ROOT / "queue" / "reviews").glob("*.json")):
        try:
            review = json.loads(review_path.read_text(encoding="utf-8"))
            if set(review) != {"schema_version", "job_id", "verdict", "reviewed_at", "summary", "criteria"}:
                raise JobError("Review keys are invalid")
            if review["schema_version"] != 1 or review["verdict"] not in {"approved", "changes_requested"}:
                raise JobError("Review schema or verdict is invalid")
            job_id = review["job_id"]
            status_path = _status_path(job_id)
            manifest_path = ROOT / "results" / job_id / "manifest.json"
            if not status_path.is_file() or not manifest_path.is_file():
                continue
            status = json.loads(status_path.read_text(encoding="utf-8"))
            if status.get("state") != "needs_review":
                continue
            author = "local"
            if check_author:
                author, _ = github_author(review_path, config["repository"])
                if config["require_trusted_author"] and author not in config["trusted_authors"]:
                    raise JobError(f"Review author {author!r} is not trusted")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            review_ids = {item["id"] for item in manifest["acceptance_criteria"] if item["kind"] == "review"}
            supplied = review["criteria"]
            if set(supplied) != review_ids or any(value not in {"pass", "fail"} for value in supplied.values()):
                raise JobError("Review criteria must exactly cover review criterion IDs")
            if review["verdict"] == "approved" and any(value != "pass" for value in supplied.values()):
                raise JobError("approved review requires every review criterion to pass")
            for item in manifest["acceptance_criteria"]:
                if item["id"] in supplied:
                    item["status"] = supplied[item["id"]]
            new_state = "complete" if review["verdict"] == "approved" else "changes_requested"
            manifest["state"] = new_state
            manifest["review"] = {**review, "author": author}
            status["state"] = new_state
            status["updated_at"] = utc_now()
            status["review"] = {"verdict": review["verdict"], "author": author, "summary": review["summary"]}
            atomic_write_json(manifest_path, manifest)
            atomic_write_json(status_path, status)
            if publish_updates:
                publish(
                    [manifest_path, status_path],
                    f"worker({job_id}): review {new_state}",
                    config["branch"],
                    push=config["git_publish"],
                )
            changed += 1
        except Exception as exc:
            print(f"REVIEW_ERROR path={review_path} error={exc}", flush=True)
    return changed


def cycle(config: dict, *, once: bool = False) -> int:
    processed = 0
    if config["git_sync"]:
        sync(config["branch"])
    reconcile_reviews(config)
    for descriptor in sorted((ROOT / "queue" / "pending").glob("*/job.json")):
        status_path = _status_path(descriptor.parent.name)
        if status_path.is_file():
            status = json.loads(status_path.read_text(encoding="utf-8"))
            if status.get("state") in TERMINAL_STATES or status.get("state") == "running":
                continue
        process_job(descriptor, config)
        processed += 1
        if once:
            break
    return processed


def run_worker(config: dict, *, once: bool) -> int:
    with worker_lock():
        while True:
            try:
                processed = cycle(config, once=once)
                print(f"WORKER_CYCLE=PASS processed={processed} at={utc_now()}", flush=True)
            except (GitError, JobError, RuntimeError) as exc:
                print(f"WORKER_CYCLE=FAIL error={exc}", flush=True)
                if once:
                    return 1
            except Exception:
                traceback.print_exc()
                if once:
                    return 1
            if once:
                return 0
            time.sleep(max(5, int(config["poll_seconds"])))
