"""Python/Blender script entry point for workspace jobs."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import traceback
import uuid


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bridge.adapters import input_path  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, filename = tempfile.mkstemp(prefix=".json-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(filename, path)
    finally:
        Path(filename).unlink(missing_ok=True)


def copy_outputs(source: Path, target: Path) -> list[dict]:
    """Copy editable results into an immutable checkpoint before exposing it."""
    records = []
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise ValueError("Checkpoint output must not contain symbolic links")
        if not path.is_file() or path.name.startswith("."):
            continue
        relative = path.relative_to(source)
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        digest = hashlib.sha256()
        with destination.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        records.append({"path": (Path("output") / relative).as_posix(),
                        "bytes": destination.stat().st_size, "sha256": digest.hexdigest()})
    return records


def save_blend(bpy, target: Path) -> None:
    """Pack resources and replace a snapshot only after Blender finishes writing."""
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.parent / f".saving-{uuid.uuid4().hex}.blend"
    bpy.context.preferences.filepaths.save_version = 0
    if bpy.data.libraries:
        bpy.ops.file.pack_libraries()
    bpy.ops.file.pack_all()
    try:
        bpy.ops.wm.save_as_mainfile(filepath=str(temporary), check_existing=False, copy=True, relative_remap=False)
        if not temporary.is_file() or temporary.stat().st_size == 0:
            raise RuntimeError("Blender did not produce a saved scene")
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def validate_blend(bpy, path: Path) -> dict:
    """Actually reopen the saved scene, with embedded Python disabled."""
    bpy.ops.wm.open_mainfile(filepath=str(path))
    missing = []
    for image in bpy.data.images:
        if image.source in {"GENERATED", "VIEWER"} or image.packed_file or image.packed_files or not image.filepath:
            continue
        resolved = Path(bpy.path.abspath(image.filepath))
        if not resolved.is_file():
            missing.append(str(resolved))
    for library in bpy.data.libraries:
        if not library.packed_file and not Path(bpy.path.abspath(library.filepath)).is_file():
            missing.append(library.filepath)
    result = {"reopened": True, "missing_external_files": sorted(set(missing)),
              "objects": len(bpy.context.scene.objects), "blender_version": bpy.app.version_string,
              "pass": not missing}
    if missing:
        raise RuntimeError("Saved scene has missing external resources: " + ", ".join(missing))
    return result


def arguments() -> argparse.Namespace:
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument("--tool", required=True, choices=["python", "blender"])
    parser.add_argument("--script", required=True)
    parser.add_argument("--step-json", required=True)
    parser.add_argument("--job")
    for name in ("input", "output", "workspace", "checkpoint"):
        parser.add_argument(f"--{name}-dir", required=True)
    return parser.parse_args(values)


def main() -> int:
    args = arguments()
    step = json.loads(args.step_json)
    step_id = step["id"]
    if not isinstance(step_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", step_id):
        raise ValueError("Invalid step id")
    script = Path(args.script).resolve(strict=True)
    job = json.loads(Path(args.job).read_text(encoding="utf-8")) if args.job else {}
    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    workspace_dir = Path(args.workspace_dir).resolve()
    checkpoint_dir = Path(args.checkpoint_dir).resolve() / step_id
    for path in (output_dir, workspace_dir, checkpoint_dir):
        path.mkdir(parents=True, exist_ok=True)
    output_blend = output_dir / "model.blend"
    bpy = None
    if args.tool == "blender":
        import bpy
        if step.get("source_blend"):
            source = input_path(step["source_blend"], {"input_dir": input_dir, "workspace_dir": workspace_dir})
            if source.suffix != ".blend":
                raise ValueError("source_blend must be a .blend file")
            bpy.ops.wm.open_mainfile(filepath=str(source))

    def checkpoint(stage: str, summary: str = "", evidence: list[str] | None = None) -> str:
        if not isinstance(stage, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", stage):
            raise ValueError("Checkpoint stage must be a short filename-safe identifier")
        identifier = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + stage
        staging = checkpoint_dir / ("." + identifier)
        destination = checkpoint_dir / identifier
        staging.mkdir()
        try:
            if bpy is not None:
                save_blend(bpy, output_blend)
            files = copy_outputs(output_dir, staging / "output")
            record = {"schema_version": 2, "job_id": job.get("job_id"), "step_id": step_id,
                      "tool": args.tool, "created_at": utc_now(), "stage": stage,
                      "summary": str(summary), "evidence": evidence or [], "files": files}
            if bpy is not None:
                # Alias at checkpoint root makes restoring a scene unambiguous.
                shutil.copyfile(staging / "output/model.blend", staging / "scene.blend")
                record["source_blend"] = "scene.blend"
            atomic_json(staging / "checkpoint.json", record)
            os.replace(staging, destination)
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise
        print("CHECKPOINT " + json.dumps({"path": str(destination), "stage": stage, "summary": summary}, ensure_ascii=False), flush=True)
        return str(destination)

    namespace = {"__name__": "__creative_job__", "__file__": str(script), "JOB": job,
                 "STEP": step, "PARAMS": step.get("params", {}), "INPUT_DIR": input_dir,
                 "OUTPUT_DIR": output_dir, "WORKSPACE_DIR": workspace_dir,
                 "CHECKPOINT_DIR": checkpoint_dir, "RUN_DIR": output_dir,
                 "OUTPUT_BLEND": output_blend, "checkpoint": checkpoint}
    if bpy is not None:
        namespace["bpy"] = bpy
    try:
        exec(compile(script.read_text(encoding="utf-8"), str(script), "exec"), namespace)
        previews, validation = [], None
        if bpy is not None:
            checkpoint("script-complete", "Editable Blender scene saved before previews")
            validation = validate_blend(bpy, output_blend)
            from bridge.blender_entry import render_previews
            preview = step.get("preview", {"views": ["front", "right", "back", "three_quarter"],
                                           "width": 512, "height": 512, "samples": 16})
            previews = render_previews(output_dir, preview)
            # Preview lighting/camera must not modify the editable deliverable.
            validate_blend(bpy, output_blend)
        report = {"schema_version": 2, "job_id": job.get("job_id"), "step_id": step_id,
                  "tool": args.tool, "state": "succeeded", "finished_at": utc_now(),
                  "previews": previews, "validation": validation}
        atomic_json(output_dir / "tool_report.json", report)
        checkpoint("complete", "Step complete; visual acceptance still requires review")
        return 0
    except Exception as error:
        atomic_json(output_dir / "tool_report.json", {"schema_version": 2, "step_id": step_id,
                    "tool": args.tool, "state": "failed", "finished_at": utc_now(), "error": str(error)})
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
