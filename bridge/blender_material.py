"""Import verified Material Maker maps into a Blender Principled material."""
import hashlib
import json
from pathlib import Path


def load_material_maker(directory, name="Material Maker", height_distance=0.04):
    import bpy
    root = Path(directory).resolve()
    report = json.loads((root / "material_report.json").read_text())
    if report.get("state") != "succeeded" or not report.get("maps"):
        raise ValueError("Material Maker export is not verified")
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes.get("Principled BSDF")
    textures = {}
    for index, (kind, record) in enumerate(report["maps"].items()):
        path = (root / record["path"]).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("Missing or unsafe Material Maker map")
        if hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
            raise ValueError("Material Maker map SHA-256 mismatch: " + kind)
        image = bpy.data.images.load(str(path), check_existing=True)
        if tuple(image.size) != (record["width"], record["height"]):
            raise ValueError("Material Maker map failed image decode: " + kind)
        image.colorspace_settings.name = "sRGB" if kind in {"albedo", "emission"} else "Non-Color"
        node = nodes.new("ShaderNodeTexImage")
        node.name = "MM_" + kind
        node.label = kind
        node.image = image
        node.location = (-900, -index * 240)
        textures[kind] = node.outputs["Color"]
    color = textures.get("albedo")
    if color and "ao" in textures:
        multiply = nodes.new("ShaderNodeMixRGB")
        multiply.blend_type = "MULTIPLY"
        multiply.inputs[0].default_value = 1
        links.new(color, multiply.inputs[1])
        links.new(textures["ao"], multiply.inputs[2])
        color = multiply.outputs["Color"]
    if color:
        links.new(color, shader.inputs["Base Color"])
    for kind, socket in (("roughness", "Roughness"), ("metallic", "Metallic"), ("emission", "Emission Color")):
        if kind in textures:
            links.new(textures[kind], shader.inputs[socket])
            if kind == "emission":
                shader.inputs["Emission Strength"].default_value = 1
    normal = None
    if "normal" in textures:
        mapping = nodes.new("ShaderNodeNormalMap")
        links.new(textures["normal"], mapping.inputs["Color"])
        normal = mapping.outputs["Normal"]
    if "height" in textures:
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Distance"].default_value = height_distance
        links.new(textures["height"], bump.inputs["Height"])
        if normal:
            links.new(normal, bump.inputs["Normal"])
        normal = bump.outputs["Normal"]
    if normal:
        links.new(normal, shader.inputs["Normal"])
    material["material_maker_version"] = report["release"]["version"]
    material["material_maker_source_sha256"] = report["source_sha256"]
    return material
