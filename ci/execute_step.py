"""Runs inside a disposable, token-free, network-disabled container."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bridge.adapters import build_command
from bridge.creative_jobs import load_creative_job


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    parser.add_argument("--step", required=True)
    args = parser.parse_args()
    job, files = load_creative_job(ROOT / args.job, repo_root=ROOT)
    step = next(dict(item) for item in job["steps"] if item["id"] == args.step)
    if "script" in step:
        step["script"] = files.scripts[step["id"]].relative_to(ROOT).as_posix()
    output = Path("/work/output") / step["id"]
    output.mkdir(parents=True, exist_ok=True)
    context = {"repo_root": ROOT, "input_dir": Path("/input"), "output_dir": output,
               "workspace_dir": Path("/work"), "checkpoint_dir": Path("/work/checkpoints"),
               "job_file": ROOT / args.job}
    command = build_command(step, context)
    result = subprocess.run(command, check=False)
    if result.returncode:
        return result.returncode
    if step["tool"] == "blender":
        blend = output / "model.blend"
        if not blend.is_file() or blend.stat().st_size == 0:
            raise RuntimeError("Blender did not produce model.blend")
        report = output / "validation.json"
        check = subprocess.run(["blender", "--background", "--disable-autoexec", str(blend),
                                "--python-exit-code", "1", "--python", str(ROOT / "bridge/blender_validate.py"),
                                "--", "--report", str(report)], check=False)
        if check.returncode or not json.loads(report.read_text()).get("pass"):
            raise RuntimeError("Saved Blender file failed the reopen check")
    if not any(path.is_file() and not path.is_symlink() and path.stat().st_size > 0 for path in output.rglob("*")):
        raise RuntimeError("Step produced no non-empty output files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
