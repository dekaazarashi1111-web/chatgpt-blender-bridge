"""Orthographic reference-matched lookdev, separate from bridge thumbnails."""
import json
from pathlib import Path
import bpy
from mathutils import Vector

scene=bpy.context.scene
for ob in list(scene.objects):
    if ob.type in {'LIGHT','CAMERA'}: bpy.data.objects.remove(ob,do_unlink=True)
scene.render.engine='CYCLES'; scene.cycles.device='CPU'; scene.cycles.samples=int(PARAMS.get('samples',96))
scene.cycles.use_denoising=False; scene.cycles.use_adaptive_sampling=True; scene.cycles.adaptive_threshold=.035
scene.cycles.max_bounces=7; scene.cycles.diffuse_bounces=3; scene.cycles.glossy_bounces=4
scene.render.threads_mode='FIXED'; scene.render.threads=3
scene.view_settings.view_transform='Standard'
try: scene.view_settings.look='None'
except TypeError: pass
scene.view_settings.exposure=0; scene.view_settings.gamma=1
world=scene.world; world.use_nodes=True
nd=world.node_tree.nodes; lk=world.node_tree.links; nd.clear()
out=nd.new('ShaderNodeOutputWorld'); mix=nd.new('ShaderNodeMixShader')
lightpath=nd.new('ShaderNodeLightPath'); env=nd.new('ShaderNodeBackground'); bg=nd.new('ShaderNodeBackground')
env.inputs['Color'].default_value=(.42,.42,.42,1);env.inputs['Strength'].default_value=.25
bg.inputs['Color'].default_value=(.1144,.1144,.1144,1);bg.inputs['Strength'].default_value=1
lk.new(lightpath.outputs['Is Camera Ray'],mix.inputs[0]);lk.new(env.outputs[0],mix.inputs[1]);lk.new(bg.outputs[0],mix.inputs[2]);lk.new(mix.outputs[0],out.inputs[0])
for name,loc,power,size in [('Studio_key',(-3,-4,5),250,4),('Studio_fill',(4,-2,3),75,5),('Studio_back',(0,3,4),125,4)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.location=loc
    if hasattr(ob,'visible_glossy'): ob.visible_glossy=False
    ob.rotation_euler=(Vector((0,0,1.3))-ob.location).to_track_quat('-Z','Y').to_euler()
# Small source gives restrained eye pin reflections, never emissive eyes.
data=bpy.data.lights.new('Eye_pin_light','POINT');data.energy=2;data.shadow_soft_size=.018
ob=bpy.data.objects.new('Eye_pin_light',data);scene.collection.objects.link(ob);ob.location=(-.8,-2.0,2.7)
views=Path(OUTPUT_DIR)/'views';views.mkdir(parents=True,exist_ok=True)
size=int(PARAMS.get('resolution',896));scene.render.resolution_x=size;scene.render.resolution_y=size;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8'
scene.render.film_transparent=True
specs=[('front',(0,-6,1.303),(0,0,1.303),2.678),('right',(6,0,1.303),(0,0,1.303),2.678),
       ('back',(0,6,1.303),(0,0,1.303),2.678),('three_quarter',(4,-6,3.10),(0,0,1.3),2.92),
       ('face',(0,-6,1.823),(0,-.05,1.823),.655),('face_profile',(6,-.10,1.823),(0,-.10,1.823),.80),
       ('surface',(1.2,-6,1.68),(0,-.15,1.17),.72)]
records=[]
for name,loc,target,scale in specs:
    data=bpy.data.cameras.new('Camera_'+name);data.type='ORTHO';data.ortho_scale=scale
    camera=bpy.data.objects.new('Camera_'+name,data);scene.collection.objects.link(camera);camera.location=loc
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();scene.camera=camera
    scene.render.filepath=str(views/(name+'.png'))
    print('RENDER_START',name,flush=True);bpy.ops.render.render(write_still=True)
    records.append({'view':name,'resolution':[size,size],'samples':scene.cycles.samples,'denoising':False,'ortho_scale':scale})
scene.camera=bpy.data.objects['Camera_front'];scene.render.film_transparent=False
(Path(OUTPUT_DIR)/'render_settings.json').write_text(json.dumps({'renderer':bpy.app.version_string,'views':records,'lighting':'neutral soft studio at half v001 irradiance, matched to observed reference brightness','review':'not yet performed'},indent=2))
checkpoint('lookdev','Actual reference-aligned front/right/back and detail views rendered; no appearance acceptance inferred')
