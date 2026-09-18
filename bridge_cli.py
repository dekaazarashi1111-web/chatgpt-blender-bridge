#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from bridge.config import ROOT, ConfigError, load_config, locate_blender
from bridge.jobs import JobError, load_job
from bridge.worker import process_job, run_worker


def command_doctor(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config).resolve() if args.config else None)
    blender = locate_blender(config["blender_bin"])
    checks = []
    for name, command in (
        ("git", ["git", "--version"]),
        ("blender", [str(blender), "--version"]),
    ):
        completed = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        first_line = completed.stdout.splitlines()[0] if completed.stdout.splitlines() else ""
        checks.append((name, completed.returncode == 0, first_line))
    for name, passed, detail in checks:
        print(f"{name.upper()}={'PASS' if passed else 'FAIL'} {detail}")
    if not all(item[1] for item in checks):
        return 1
    print(f"DOCTOR=PASS repository={config['repository']} blender={blender}")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    descriptors = [ROOT / "examples" / "jobs" / "demo-cube" / "job.json"]
    descriptors.extend(sorted((ROOT / "queue" / "pending").glob("*/job.json")))
    passed = 0
    for descriptor in descriptors:
        try:
            data, _ = load_job(descriptor, allow_any_location=True)
            print(f"JOB_SCHEMA=PASS id={data['job_id']} path={descriptor.relative_to(ROOT)}")
            passed += 1
        except Exception as exc:
            print(f"JOB_SCHEMA=FAIL path={descriptor} error={exc}", file=sys.stderr)
            return 1
    print(f"VALIDATE=PASS jobs={passed}")
    return 0


def command_smoke(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config).resolve() if args.config else None)
    smoke_root = ROOT / ".worker" / "smoke"
    queue_root = smoke_root / "queue" / "pending" / "demo-cube"
    run_dir = smoke_root / "latest"
    if smoke_root.exists():
        shutil.rmtree(smoke_root)
    queue_root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "examples" / "jobs" / "demo-cube" / "job.json", queue_root / "job.json")
    shutil.copy2(ROOT / "examples" / "jobs" / "demo-cube" / "script.py", queue_root / "script.py")
    smoke_config = {**config, "git_sync": False, "git_publish": False}
    manifest = process_job(
        queue_root / "job.json",
        smoke_config,
        publish_updates=False,
        publish_results=False,
        run_dir_override=run_dir,
        status_path_override=smoke_root / "status" / "demo-cube.json",
    )
    passed = manifest.get("state") == "complete"
    print(f"SMOKE={'PASS' if passed else 'FAIL'} state={manifest.get('state')} output={run_dir}")
    return 0 if passed else 1


def command_submit_demo(args: argparse.Namespace) -> int:
    source = ROOT / "examples" / "jobs" / "demo-cube"
    target = ROOT / "queue" / "pending" / "demo-cube"
    if target.exists():
        raise RuntimeError(f"Refusing to overwrite existing job: {target}")
    target.mkdir(parents=True)
    shutil.copy2(source / "script.py", target / "script.py")
    shutil.copy2(source / "job.json", target / "job.json")
    print(f"SUBMIT_DEMO=PASS path={target.relative_to(ROOT)}")
    return 0


def command_worker(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config).resolve() if args.config else None)
    if args.no_sync:
        config["git_sync"] = False
    if args.no_publish:
        config["git_publish"] = False
    return run_worker(config, once=args.once)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="GitHub queue based Blender worker")
    root.add_argument("--config", help="config.json path")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor").set_defaults(function=command_doctor)
    commands.add_parser("validate").set_defaults(function=command_validate)
    commands.add_parser("smoke").set_defaults(function=command_smoke)
    commands.add_parser("submit-demo").set_defaults(function=command_submit_demo)
    worker = commands.add_parser("worker")
    worker.add_argument("--once", action="store_true")
    worker.add_argument("--no-sync", action="store_true")
    worker.add_argument("--no-publish", action="store_true")
    worker.set_defaults(function=command_worker)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        return args.function(args)
    except (ConfigError, JobError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
