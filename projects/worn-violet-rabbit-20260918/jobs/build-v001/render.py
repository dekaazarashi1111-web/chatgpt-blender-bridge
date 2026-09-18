"""Render fixed-axis comparison views from the saved/reopened editable scene."""
import bpy
import json
import hashlib
from pathlib import Path
from mathutils import Vector

OUT=Path(OUTPUT_DIR);OUT.mkdir(parents=True,exist_ok=True)
views=OUT/'views';views.mkdir(exist_ok=True)
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.device='CPU'
scene.cycles.samples=48;scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.035
scene.cycles.use_denoising=True;scene.cycles.max_bounces=6
scene.render.threads_mode='FIXED';scene.render.threads=3
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.render.image_settings.color_depth='8';scene.render.film_transparent=False
scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
scene.view_settings.exposure=0;scene.view_settings.gamma=1
cam=scene.objects.get('Reference_orthographic_camera')
assert cam is not None
scene.camera=cam
specs=[
 ('front',(0,-7,1.303),(0,0,1.303),2.678,1024,1024),
 ('right',(7,0,1.303),(0,0,1.303),2.678,1024,1024),
 ('back',(0,7,1.303),(0,0,1.303),2.678,1024,1024),
 ('three_quarter',(4.8,-7,3.05),(0,0,1.28),2.90,1024,1024),
 ('face',(0,-5,1.82),(0,-.06,1.82),.80,1024,1024),
 ('face_profile',(5,-.12,1.83),(0,-.09,1.83),.80,1024,1024),
 ('surface',(2.8,-5,1.25),(0,-.02,1.25),.84,1024,1024)
]
checkpoint('before-fixed-view-renders','Packed model ready for exact horizontal orthographic comparison renders')
records=[]
for name,loc,target,scale,w,h in specs:
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.type='ORTHO';cam.data.ortho_scale=scale
    scene.render.resolution_x=w;scene.render.resolution_y=h
    path=views/(name+'.png');scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True)
    assert path.stat().st_size>10000
    records.append({'view':name,'relative_path':'views/'+path.name,'dimensions':[w,h],
                    'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                    'camera_position':list(loc),'target':list(target),'ortho_scale':scale})
    print('REFERENCE_RENDER_COMPLETE '+name,flush=True)
cam.location=(0,-7,1.303);cam.rotation_euler=(Vector((0,0,1.303))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.ortho_scale=2.678;scene.render.resolution_x=1024;scene.render.resolution_y=1024
scene.render.filepath='//front.png'
(OUT/'render_validation.json').write_text(json.dumps({'pass':True,'source_step':'model','revision':'build-v001',
    'engine':'CYCLES','device':'CPU','samples':48,'color_management':'Standard, None, exposure 0, gamma 1',
    'reference_comparison':'same horizontal camera and gray background; final fidelity requires human/image review',
    'renders':records},indent=2)+'\n')
checkpoint('fixed-views-complete','Seven actual reference comparison and surface-detail images saved')
