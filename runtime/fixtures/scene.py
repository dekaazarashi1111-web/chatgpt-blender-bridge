"""Exercises legal Blender .system/.remove APIs and packed external textures."""
import bpy

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
bpy.context.scene.unit_settings.system = "METRIC"
bpy.ops.mesh.primitive_cube_add(size=2)
cube = bpy.context.object
cube.name = "RuntimeSmokeCube"
material = bpy.data.materials.new("CheckerMaterial")
material.use_nodes = True
texture = material.node_tree.nodes.new("ShaderNodeTexImage")
texture.image = bpy.data.images.load(str(INPUT_DIR / "checker.png"))
material.node_tree.links.new(texture.outputs["Color"], material.node_tree.nodes.get("Principled BSDF").inputs["Base Color"])
cube.data.materials.append(material)
checkpoint("geometry", "Cube and packed texture are ready")
