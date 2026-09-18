from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import traceback

import bpy
from mathutils import Vector


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def arguments() -> argparse.Namespace:
    values = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    parser.add_argument("--script", required=True)
    parser.add_argument("--run-dir", required=True)
    return parser.parse_args(values)


def scene_bounds() -> tuple[Vector, float]:
    points: list[Vector] = []
    for obj in bpy.context.scene.objects:
        if obj.type not in {"MESH", "CURVE", "SURFACE", "META", "FONT"} or obj.hide_render:
            continue
        points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    if not points:
        raise RuntimeError("Preview requires at least one renderable object")
    minimum = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    maximum = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    center = (minimum + maximum) * 0.5
    extent = maximum - minimum
    return center, max(extent.x, extent.y, extent.z, 0.1)


def add_area_light(name: str, location: Vector, energy: float, size: float, center: Vector) -> bpy.types.Object:
    data = bpy.data.lights.new(name=name, type="AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (center - location).to_track_quat("-Z", "Y").to_euler()
    return obj


def render_previews(run_dir: Path, preview: dict) -> list[dict]:
    scene = bpy.context.scene
    center, size = scene_bounds()
    camera_data = bpy.data.cameras.new("BridgePreviewCamera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = size * 1.45
    camera = bpy.data.objects.new("BridgePreviewCamera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    lights = [
        add_area_light("BridgeKey", center + Vector((-size * 2.0, -size * 2.5, size * 2.8)), 1100.0, size * 2.0, center),
        add_area_light("BridgeFill", center + Vector((size * 2.4, -size * 1.0, size * 1.4)), 650.0, size * 2.2, center),
        add_area_light("BridgeRim", center + Vector((0.0, size * 2.5, size * 2.1)), 850.0, size * 1.6, center),
    ]
    if scene.world is None:
        scene.world = bpy.data.worlds.new("BridgeWorld")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    if background:
        background.inputs["Color"].default_value = (0.035, 0.04, 0.05, 1.0)
        background.inputs["Strength"].default_value = 0.35
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"
    if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = preview["samples"]
    scene.render.resolution_x = preview["width"]
    scene.render.resolution_y = preview["height"]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    directions = {
        "front": Vector((0.0, -1.0, 0.08)),
        "right": Vector((1.0, 0.0, 0.08)),
        "back": Vector((0.0, 1.0, 0.08)),
        "left": Vector((-1.0, 0.0, 0.08)),
        "three_quarter": Vector((1.0, -1.0, 0.55)),
    }
    preview_dir = run_dir / "previews"
    preview_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    for view in preview["views"]:
        direction = directions[view].normalized()
        camera.location = center + direction * size * 3.2
        camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
        target = preview_dir / f"{view}.png"
        scene.render.filepath = str(target)
        bpy.ops.render.render(write_still=True)
        records.append({"view": view, "path": str(target), "bytes": target.stat().st_size})
    for obj in [camera, *lights]:
        bpy.data.objects.remove(obj, do_unlink=True)
    return records


def main() -> int:
    args = arguments()
    job_path = Path(args.job).resolve()
    script_path = Path(args.script).resolve()
    run_dir = Path(args.run_dir).resolve()
    output = run_dir / "output" / "model.blend"
    checkpoint_path = run_dir / "checkpoint.json"
    report_path = run_dir / "blender_report.json"
    run_dir.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    job = json.loads(job_path.read_text(encoding="utf-8"))

    def checkpoint(stage: str, summary: str = "", evidence: list[str] | None = None) -> None:
        atomic_json(
            checkpoint_path,
            {
                "schema_version": 1,
                "job_id": job["job_id"],
                "updated_at": utc_now(),
                "stage": stage,
                "summary": summary,
                "evidence": evidence or [],
            },
        )
        print(f"CHECKPOINT stage={stage} summary={summary}", flush=True)

    checkpoint("script_start", "Blender user scriptを開始")
    globals_dict = {
        "__name__": "__blender_job__",
        "__file__": str(script_path),
        "bpy": bpy,
        "JOB": job,
        "RUN_DIR": run_dir,
        "OUTPUT_BLEND": output,
        "checkpoint": checkpoint,
    }
    try:
        source = script_path.read_text(encoding="utf-8")
        exec(compile(source, str(script_path), "exec"), globals_dict)
        checkpoint("script_complete", "Blender user scriptが終了")
        bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)
        checkpoint("blend_saved", "編集可能なblendを保存", [str(output)])
        previews = render_previews(run_dir, job["preview"])
        checkpoint("previews_complete", "指定方向のpreviewを生成", [item["path"] for item in previews])
        report = {
            "schema_version": 1,
            "job_id": job["job_id"],
            "finished_at": utc_now(),
            "output_blend": str(output),
            "objects": [
                {"name": obj.name, "type": obj.type}
                for obj in sorted(bpy.context.scene.objects, key=lambda item: item.name)
                if not obj.name.startswith("BridgePreview")
            ],
            "previews": previews,
        }
        atomic_json(report_path, report)
        print(f"BLENDER_JOB=PASS output={output} previews={len(previews)} report={report_path}", flush=True)
        return 0
    except Exception:
        checkpoint("failed", "Blender job failed")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
