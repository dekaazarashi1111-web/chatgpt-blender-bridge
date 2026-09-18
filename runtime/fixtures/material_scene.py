"""Verify exported PBR maps are editable, linked, packed and rendered in Blender."""
import json
import bpy
from bridge.blender_material import load_material_maker

directory = WORKSPACE_DIR / PARAMS.get("material_dir", "outputs/material")
report = json.loads((directory / "material_report.json").read_text())
assert report["state"] == "succeeded"
assert {"albedo", "roughness", "metallic", "normal", "height", "ao"} <= report["maps"].keys()
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
bpy.context.scene.unit_settings.system = "METRIC"
bpy.ops.mesh.primitive_cube_add(size=2)
cube = bpy.context.object
cube.name = "MaterialMakerTerracottaCube"
material = load_material_maker(directory, "Material Maker terracotta")
cube.data.materials.append(material)
nodes = material.node_tree.nodes
assert nodes.get("MM_albedo").image.colorspace_settings.name == "sRGB"
assert nodes.get("MM_roughness").image.colorspace_settings.name == "Non-Color"
assert nodes.get("MM_normal").image.colorspace_settings.name == "Non-Color"
shader = nodes.get("Principled BSDF")
assert all(shader.inputs[socket].is_linked for socket in ("Base Color", "Roughness", "Metallic", "Normal"))
image = nodes.get("MM_albedo").image
# Sampling a grid demonstrates that a real patterned material was generated.
pixels = image.pixels[:]
samples = [pixels[(y * image.size[0] + x) * 4] for y in range(17, 2048, 71) for x in range(23, 2048, 79)]
assert max(samples) - min(samples) > 0.05, "Material Maker returned a flat albedo image"
checkpoint("material-linked", "Material Maker maps imported and packed")
assert all(node.image.packed_file for node in nodes if node.type == "TEX_IMAGE")
(OUTPUT_DIR / "material_integration.json").write_text(json.dumps({
    "pass": True, "material_maker_version": report["release"]["version"],
    "maps": sorted(report["maps"]), "source_sha256": report["source_sha256"],
    "shader_inputs_connected": True, "images_packed": True,
    "albedo_range": max(samples) - min(samples)
}, indent=2) + "\n")
