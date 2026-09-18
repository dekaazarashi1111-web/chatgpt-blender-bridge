import bpy

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0
bpy.ops.mesh.primitive_cube_add(size=2)
cube = bpy.context.object
cube.name = "CreativeBridgeCheckpointCube"
bevel = cube.modifiers.new("Soft edges", "BEVEL")
bevel.width = 0.12
bevel.segments = 3
material = bpy.data.materials.new("Studio blue")
material.diffuse_color = (0.07, 0.3, 0.65, 1)
cube.data.materials.append(material)
checkpoint("shape-ready", "Metric unit setting and editable beveled cube saved")
