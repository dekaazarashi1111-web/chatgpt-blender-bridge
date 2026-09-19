"""Render only the saved current model. Frustum checked neutral geometry review."""
import bpy,json,shutil,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
OUT=Path(OUTPUT_DIR);OUT.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene;assert scene['project_id']==JOB['project_id'] and scene['job_id']==JOB['job_id']
scene.render.engine='BLENDER_WORKBENCH'
sh=scene.display.shading;sh.light='STUDIO';sh.studio_light='paint.sl';sh.color_type='MATERIAL'
sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH'
sh.curvature_ridge_factor=.5;sh.curvature_valley_factor=.65;sh.cavity_ridge_factor=.5;sh.cavity_valley_factor=.65
sh.show_specular_highlight=False;sh.show_object_outline=False;sh.background_type='WORLD'
scene.world.color=(.20,.20,.20);scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
scene.render.resolution_percentage=100;scene.render.film_transparent=True;scene.display.render_aa='16'
scene.view_settings.view_transform='Standard'
cd=bpy.data.cameras.new('Current geometry review camera');cd.type='ORTHO'
cam=bpy.data.objects.new('Current geometry review camera',cd);scene.collection.objects.link(cam);scene.camera=cam
geos=[o for o in scene.objects if o.type in {'MESH','CURVE'}];orig={o.name:o.hide_render for o in geos}
head_names={o.name for o in bpy.data.collections['02_HEAD'].objects}
head_names|={o.name for o in geos if o.name.startswith(('Whisker ','Socket lining ','Mouth internal'))}
records=[]
def image(name,loc,target,scale,res=(960,1280),isolated=None,single=False):
    for o in geos:o.hide_render=orig[o.name] or (isolated is not None and o.name not in isolated)
    sh.color_type='SINGLE' if single else 'MATERIAL';sh.single_color=(.57,.57,.57)
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.resolution_x=res[0];scene.render.resolution_y=res[1]
    for attempt in range(16):
        cd.ortho_scale=scale;bpy.context.view_layer.update();bounds=[]
        for o in geos:
            if o.hide_render:continue
            for corner in o.bound_box:
                p=world_to_camera_view(scene,cam,o.matrix_world@Vector(corner));bounds.append((p.x,p.y))
        if all(.012<x<.988 and .012<y<.988 for x,y in bounds):break
        scale*=1.035
    assert bounds and all(.012<x<.988 and .012<y<.988 for x,y in bounds),name+' is clipped'
    scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
    records.append({'view':name,'file':name+'.png','camera':list(loc),'target':list(target),'ortho_scale':scale,'pixels':list(res),'isolated':isolated is not None,'uniform_material':single,'frustum_pass':True,'frame_xy_min':[min(p[k] for p in bounds) for k in [0,1]],'frame_xy_max':[max(p[k] for p in bounds) for k in [0,1]]})
image('front',(0,-7,1.10),(0,0,1.10),2.36)
image('right',(7,0,1.10),(0,0,1.10),2.36)
image('back',(0,7,1.10),(0,0,1.10),2.36)
image('three_quarter',(3.4,-6,2.65),(0,0,1.10),2.40)
image('front_uniform_clay',(0,-7,1.10),(0,0,1.10),2.36,single=True)
image('head_front',(0,-7,1.742),(0,-.10,1.742),.62,(1200,1200),head_names)
image('head_right',(7,-.105,1.742),(0,-.105,1.742),.62,(1200,1200),head_names)
image('head_three_quarter',(3,-6,2.6),(0,-.10,1.742),.68,(1200,1200),head_names)
image('head_uniform_clay',(3,-6,2.6),(0,-.10,1.742),.68,(1200,1200),head_names,True)
feet={o.name for o in bpy.data.collections['07_FEET'].objects}
image('feet_detail',(2,-4,2.4),(0,-.08,.11),1.01,(1200,1000),feet)
image('feet_uniform_clay',(2,-4,2.4),(0,-.08,.11),1.01,(1200,1000),feet,True)
hand={o.name for o in bpy.data.collections['05_HANDS'].objects if o.name.endswith('L') or o.name.startswith('Finger L')}
image('hand_detail',(3,-4,1.7),(.444,0,.858),.41,(1000,1000),hand)
ears={o.name for o in bpy.data.collections['03_EARS'].objects}
image('ears_detail',(2,-5,3.1),(0,-.17,2.09),.88,(1200,1000),ears)
for o in geos:o.hide_render=orig[o.name]
sh.color_type='MATERIAL';cam.location=(3.4,-6,2.65);cam.rotation_euler=(Vector((0,0,1.10))-cam.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=2.4
scene.render.resolution_x=960;scene.render.resolution_y=1280
(OUT/'render_manifest.json').write_text(json.dumps(records,indent=2))
for p in (Path(WORKSPACE_DIR)/'output'/'model').iterdir():
    if p.suffix in {'.py','.json','.webp'} and p.name not in {'tool_report.json','validation.json'}:shutil.copy2(p,OUT/p.name)
shutil.copy2(Path(__file__),OUT/'render_source.py')
checkpoint('current-geometry-review-views','13 checked orthographic, clay and detailed views rendered from the saved model')
