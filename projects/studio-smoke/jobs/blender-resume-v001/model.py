"""Assert a real restored scene before making a small, observable continuation."""
import hashlib
import json
from pathlib import Path

import bpy

source = WORKSPACE_DIR / "resume/output/model/model.blend"
assert source.is_file(), "Pinned snapshot did not contain the original editable model"
assert Path(bpy.data.filepath).resolve() == source.resolve(), "Blender did not open the resumed model"
scene = bpy.context.scene
cube = bpy.data.objects.get("CreativeBridgeCheckpointCube")
assert cube is not None and cube.type == "MESH", "The named cube was not restored"
assert scene.unit_settings.system == "METRIC", "Metric units were not restored"
assert abs(scene.unit_settings.scale_length - 1.0) < 1e-6, "Scene scale changed during restoration"
assert len(cube.data.vertices) == 8 and len(cube.data.polygons) == 6, "The saved editable cube mesh was not restored"
assert len([obj for obj in scene.objects if obj.type == "MESH"]) == 1, "Unexpected mesh objects in restored scene"
bevel = cube.modifiers.get("Soft edges")
assert bevel is not None and bevel.type == "BEVEL", "The editable bevel modifier was not restored"
assert abs(bevel.width - 0.12) < 1e-6 and bevel.segments == 3, "The saved bevel settings were not restored"
assert len(cube.data.materials) == 1, "Original material assignment was not restored"
material = cube.data.materials[0]
original_color = tuple(material.diffuse_color)
assert material.name == "Studio blue", "Original material was not restored"
assert all(abs(actual - expected) < 1e-5 for actual, expected in zip(original_color, (0.07, 0.3, 0.65, 1.0))), "Original blue material color changed"

# These mutations only happen after all restored-state assertions pass. The
# script contains no mesh creation, so a fresh scene cannot pass this test.
source_name = cube.name
cube.name = "CreativeBridgeResumedCube"
cube["resume_verified"] = True
cube["resume_source_job"] = JOB["resume"]["job_id"]
material.name = "Studio copper resumed"
material.diffuse_color = (0.65, 0.18, 0.055, 1.0)
scene["creative_resume_verified"] = True
scene["creative_resume_job"] = JOB["job_id"]

source_digest = hashlib.sha256()
with source.open("rb") as stream:
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        source_digest.update(chunk)
evidence = {
    "schema_version": 1,
    "pass": True,
    "test_kind": "technical_workspace_resume",
    "project_id": JOB["project_id"],
    "job_id": JOB["job_id"],
    "source_job_id": JOB["resume"]["job_id"],
    "source_release_tag": JOB["resume"]["release_tag"],
    "source_archive_sha256": JOB["resume"]["archive_sha256"],
    "source_manifest_sha256": JOB["resume"]["manifest_sha256"],
    "source_blend": STEP["source_blend"],
    "source_blend_sha256": source_digest.hexdigest(),
    "checks": {
        "loaded_exact_source_blend": True,
        "original_named_cube_present": True,
        "metric_units_preserved": True,
        "unit_scale_preserved": True,
        "editable_cube_topology_preserved": True,
        "single_mesh_preserved": True,
        "bevel_modifier_preserved": True,
        "original_material_preserved": True
    },
    "before": {
        "object_name": source_name,
        "material_name": "Studio blue",
        "diffuse_color": list(original_color),
        "mesh_vertices": len(cube.data.vertices),
        "mesh_polygons": len(cube.data.polygons),
        "bevel_width": bevel.width,
        "bevel_segments": bevel.segments
    },
    "after": {
        "object_name": cube.name,
        "material_name": material.name,
        "diffuse_color": list(material.diffuse_color),
        "resume_verified": bool(cube["resume_verified"])
    }
}
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "resume_evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
checkpoint("resume-verified", "Restored Blender state asserted; cube renamed and recolored", ["resume_evidence.json"])

# Check that the continuation survived an actual save/reopen, not just memory.
bpy.ops.wm.open_mainfile(filepath=str(OUTPUT_BLEND), use_scripts=False)
reopened = bpy.data.objects.get("CreativeBridgeResumedCube")
assert reopened is not None and bpy.data.objects.get("CreativeBridgeCheckpointCube") is None
assert bool(reopened.get("resume_verified")) and reopened.get("resume_source_job") == JOB["resume"]["job_id"]
assert reopened.data.materials[0].name == "Studio copper resumed"
assert all(abs(actual - expected) < 1e-5 for actual, expected in zip(reopened.data.materials[0].diffuse_color, (0.65, 0.18, 0.055, 1.0)))
assert bool(bpy.context.scene.get("creative_resume_verified"))
evidence["checks"]["continued_edit_saved_and_reopened"] = True
(OUTPUT_DIR / "resume_evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
checkpoint("resume-reopened", "Continued edit survives save/reopen and retains verification tags", ["resume_evidence.json"])
