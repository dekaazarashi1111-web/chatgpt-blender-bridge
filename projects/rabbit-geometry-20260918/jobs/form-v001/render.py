"""Actual Blender orthographic/clay reviews; no image-generation substitutes."""
import bpy, json, shutil, math
from pathlib import Path
from mathutils import Vector
OUT=Path(OUTPUT_DIR);OUT.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
# Reopened input .blend has no persistent render setup. Use workbench for unbiased form review.
scene.render.engine='BLENDER_WORKBENCH'
sh=scene.display.shading
sh.light='STUDIO';sh.studio_light='paint.sl';sh.color_type='MATERIAL'
sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH'
sh.curvature_ridge_factor=1.05;sh.curvature_valley_factor=1.10
sh.cavity_ridge_factor=1.0;sh.cavity_valley_factor=1.0
sh.show_specular_highlight=True;sh.show_object_outline=False
sh.background_type='WORLD'
scene.world.color=(.20,.20,.20)
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
scene.render.resolution_percentage=100;scene.render.film_transparent=True
scene.display.render_aa='32'
scene.view_settings.view_transform='Standard'
scene.view_settings.look='Medium High Contrast' if 'Medium High Contrast' in [x.identifier for x in scene.view_settings.bl_rna.properties['look'].enum_items] else scene.view_settings.look
camera_data=bpy.data.cameras.new('Inspection orthographic camera');camera_data.type='ORTHO'
camera=bpy.data.objects.new('Inspection orthographic camera',camera_data);scene.collection.objects.link(camera);scene.camera=camera
specs=[('front',(0,-7,1.12),(0,0,1.12),2.40,1200),('right',(7,0,1.12),(0,0,1.12),2.40,1200),('back',(0,7,1.12),(0,0,1.12),2.40,1200),('three_quarter',(4,-6,3.0),(0,0,1.12),2.42,1200),('head_front',(0,-7,1.525),(0,0,1.525),.64,1400),('head_right',(7,-.015,1.525),(0,-.015,1.525),.64,1400),('head_three_quarter',(3,-6,2.4),(0,-.09,1.525),.66,1400),('hands_feet',(3,-5,1.9),(0,0,.45),1.24,1000)]
records=[]
for name,loc,target,scale,res in specs:
    camera.location=loc;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera_data.ortho_scale=scale
    scene.render.resolution_x=res;scene.render.resolution_y=res
    scene.render.filepath=str(OUT/(name+'.png'))
    bpy.ops.render.render(write_still=True)
    records.append({'view':name,'file':name+'.png','camera':loc,'target':target,'ortho_scale':scale,'pixels':[res,res]})
# A uniform-clay head exposes form without pale/dark zones.
sh.color_type='SINGLE';sh.single_color=(.57,.57,.57)
camera.location=(3,-6,2.4);camera.rotation_euler=(Vector((0,-.09,1.525))-camera.location).to_track_quat('-Z','Y').to_euler();camera_data.ortho_scale=.66
scene.render.resolution_x=1400;scene.render.resolution_y=1400;scene.render.filepath=str(OUT/'head_uniform_clay.png');bpy.ops.render.render(write_still=True)
records.append({'view':'head_uniform_clay','file':'head_uniform_clay.png','uniform_material':True})
sh.color_type='MATERIAL'
(OUT/'render_manifest.json').write_text(json.dumps(records,indent=2))
# Carry self-contained dependencies and model-stage audit into this snapshot.
root=Path(WORKSPACE_DIR)/'output'/'model'
for name in ['reference.webp','geometry_audit.json','geometry_source.py']:
    shutil.copy2(root/name,OUT/name)
shutil.copy2(Path(__file__),OUT/'render_source.py')
# Delete the temporary camera so automatic technical previews do not change scene bounds.
bpy.data.objects.remove(camera,do_unlink=True)
checkpoint('orthographic-review','Exact front/right/back plus close-up and uniform-clay images rendered by Blender')
