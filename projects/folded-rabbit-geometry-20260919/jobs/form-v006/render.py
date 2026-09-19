import hashlib
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

def reuse_view(name,names,digest):
    parent=Path(WORKSPACE_DIR)/'output'/'model'/'reference_render_cache'
    preserved=json.loads((Path(WORKSPACE_DIR)/'output'/'model'/'lineage.json').read_text())['preserved_objects']
    assert names and set(names).issubset(preserved), 'Cannot reuse a view of modified geometry'
    source=parent/(name+'.png');assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
    old=next(r for r in json.loads((parent/'render_manifest.json').read_text()) if r['view']==name)
    assert old['frustum_pass'];shutil.copy2(source,OUT/source.name)
    records.append({**old,'reused_from_job':'form-v005','image_sha256':digest,'unchanged_geometry_confirmed':True})

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
image('head_front',(0,-7,1.742),(0,-.10,1.742),.62,(1200,1200),head_names)
image('head_right',(7,-.105,1.742),(0,-.105,1.742),.62,(1200,1200),head_names)
image('head_three_quarter',(3,-6,2.6),(0,-.10,1.742),.68,(1200,1200),head_names)
image('head_uniform_clay',(3,-6,2.6),(0,-.10,1.742),.68,(1200,1200),head_names,True)
for o in geos:o.hide_render=orig[o.name]
(OUT/'partial_render_manifest.json').write_text(json.dumps(records,indent=2))
checkpoint('face-views', 'Four actual face views saved before remaining full-body inspection')
image('front',(0,-7,1.10),(0,0,1.10),2.36)
image('right',(7,0,1.10),(0,0,1.10),2.36)
image('back',(0,7,1.10),(0,0,1.10),2.36)
image('three_quarter',(3.4,-6,2.65),(0,0,1.10),2.40)
image('front_uniform_clay',(0,-7,1.10),(0,0,1.10),2.36,single=True)
feet={o.name for o in bpy.data.collections['07_FEET'].objects}
reuse_view('feet_detail',feet,'1990751c17c277c3704dc579e1717897ee515007928370488cf4e71b93450c18')
reuse_view('feet_uniform_clay',feet,'961a4d09436f722c91174e4364cb649773e3c9a0638dea2148d65f969e04e588')
hand={o.name for o in bpy.data.collections['05_HANDS'].objects if o.name.endswith('L') or o.name.startswith('Finger L')}
reuse_view('hand_detail',hand,'465e7632bed1391e3a002088558ac4dce8be2507657182eea0eb4455fc9e5476')
ears={o.name for o in bpy.data.collections['03_EARS'].objects}
reuse_view('ears_detail',ears,'bbc183d980a33648bb6e7ded6bbfd1f2693eba48508cf93cb62e4540b9379ca9')
for o in geos:o.hide_render=orig[o.name]
sh.color_type='MATERIAL';cam.location=(3.4,-6,2.65);cam.rotation_euler=(Vector((0,0,1.10))-cam.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=2.4
scene.render.resolution_x=960;scene.render.resolution_y=1280
(OUT/'render_manifest.json').write_text(json.dumps(records,indent=2))
for p in (Path(WORKSPACE_DIR)/'output'/'model').iterdir():
    if p.suffix in {'.py','.json','.webp'} and p.name not in {'tool_report.json','validation.json'}:shutil.copy2(p,OUT/p.name)
shutil.copy2(Path(__file__),OUT/'render_source.py')
checkpoint('current-geometry-review-views','Nine affected views rendered; four unchanged isolated views inherited with hashes and fingerprints')
