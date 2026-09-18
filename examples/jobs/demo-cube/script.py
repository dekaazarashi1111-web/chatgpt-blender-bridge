import bpy
import math


bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

bpy.ops.mesh.primitive_cube_add(location=(0.0, 0.0, 0.75))
body = bpy.context.object
body.name = "BridgeDemoBody"
body.scale = (1.0, 0.72, 0.75)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bevel = body.modifiers.new(name="SoftEdges", type="BEVEL")
bevel.width = 0.16
bevel.segments = 4

material = bpy.data.materials.new(name="BridgePurple")
material.diffuse_color = (0.23, 0.06, 0.52, 1.0)
material.metallic = 0.15
material.roughness = 0.28
body.data.materials.append(material)

bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=(0.0, -0.56, 1.12), scale=(0.45, 0.22, 0.24))
detail = bpy.context.object
detail.name = "BridgeDemoDetail"
detail.rotation_euler.x = math.radians(8.0)
detail.data.materials.append(material)

checkpoint("geometry_ready", "demo形状とmaterialを作成", [body.name, detail.name])
