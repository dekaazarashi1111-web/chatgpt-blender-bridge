"""Frustum-checked geometry views, without image-texture or lighting camouflage."""
import bpy,json,shutil
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
OUT=Path(OUTPUT_DIR);OUT.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
assert scene['job_id']==JOB['job_id']
scene.render.engine='BLENDER_WORKBENCH'
sh=scene.display.shading;sh.light='STUDIO';sh.studio_light='paint.sl';sh.color_type='MATERIAL'
sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH'
sh.curvature_ridge_factor=.70;sh.curvature_valley_factor=.80;sh.cavity_ridge_factor=.70;sh.cavity_valley_factor=.80
sh.show_specular_highlight=False;sh.show_object_outline=False;sh.background_type='WORLD'
scene.world.color=(.20,.20,.20)
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
scene.render.resolution_percentage=100;scene.render.film_transparent=True;scene.display.render_aa='16'
scene.view_settings.view_transform='Standard'
cd=bpy.data.cameras.new('Geometry inspection camera');cd.type='ORTHO'
cam=bpy.data.objects.new('Geometry inspection camera',cd);scene.collection.objects.link(cam);scene.camera=cam
geos=[o for o in scene.objects if o.type in {'MESH','CURVE'}]
original_hide={o.name:o.hide_render for o in geos}
head_names={o.name for o in bpy.data.collections['02_HEAD'].objects}|{o.name for o in geos if o.name.startswith('Whisker ') or o.name.startswith('Mouth internal')}
records=[]
def image(name,loc,target,scale,res=1200,isolated=None,single=False):
    for o in geos:o.hide_render=original_hide[o.name] or (isolated is not None and o.name not in isolated)
    sh.color_type='SINGLE' if single else 'MATERIAL';sh.single_color=(.57,.57,.57)
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=scale
    scene.render.resolution_x=res;scene.render.resolution_y=res;bpy.context.view_layer.update()
    clipped=[];bounds=[]
    for o in geos:
        if o.hide_render:continue
        for corner in o.bound_box:
            p=world_to_camera_view(scene,cam,o.matrix_world@Vector(corner));bounds.append((p.x,p.y))
            if not (.005<p.x<.995 and .005<p.y<.995):clipped.append(o.name)
    assert not clipped, 'Framing clips modeled parts: '+str(sorted(set(clipped)))
    scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
    records.append({'view':name,'file':name+'.png','camera':list(loc),'target':list(target),'ortho_scale':scale,'pixels':[res,res],'isolated':isolated is not None,'uniform_material':single,'frustum_pass':True,'frame_xy_min':[min(p[k] for p in bounds) for k in [0,1]],'frame_xy_max':[max(p[k] for p in bounds) for k in [0,1]]})
image('front',(0,-7,1.12),(0,0,1.12),2.40)
image('right',(7,0,1.12),(0,0,1.12),2.40)
image('back',(0,7,1.12),(0,0,1.12),2.40)
image('three_quarter',(4,-6,3.0),(0,0,1.12),2.45)
image('front_uniform_clay',(0,-7,1.12),(0,0,1.12),2.40,1200,None,True)
image('head_front',(0,-7,1.535),(0,-.10,1.535),.60,1400,head_names)
image('head_right',(7,-.10,1.535),(0,-.10,1.535),.62,1400,head_names)
image('head_three_quarter',(3,-6,2.6),(0,-.08,1.53),.68,1400,head_names)
image('head_uniform_clay',(3,-6,2.6),(0,-.08,1.53),.68,1400,head_names,True)
foot_names={o.name for o in bpy.data.collections['07_FEET'].objects}
image('feet_detail',(2,-4,2.2),(0,-.07,.072),.87,1100,foot_names)
image('feet_uniform_clay',(2,-4,2.2),(0,-.07,.072),.87,1100,foot_names,True)
hand_names={o.name for o in bpy.data.collections['05_HANDS'].objects if o.name.endswith('L')}
image('hand_detail',(2.2,-2.8,2.25),(.885,0,1.23),.45,1100,hand_names)
ear_names={o.name for o in bpy.data.collections['03_EARS'].objects}
image('ears_detail',(2,-5,2.60),(0,-.06,1.98),.67,1100,ear_names)
for o in geos:o.hide_render=original_hide[o.name]
sh.color_type='MATERIAL';bpy.data.objects.remove(cam,do_unlink=True)
(OUT/'render_manifest.json').write_text(json.dumps(records,indent=2))
for p in (Path(WORKSPACE_DIR)/'output'/'model').iterdir():
    if p.suffix in {'.py','.json','.webp'} and p.name not in {'tool_report.json','validation.json'}:shutil.copy2(p,OUT/p.name)
shutil.copy2(Path(__file__),OUT/'render_source.py')
checkpoint('geometry-review-views','13 frustum-checked orthographic, isolated and uniform-clay images from the saved geometry')
