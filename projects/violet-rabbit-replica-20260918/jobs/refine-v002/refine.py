"""Revise the exact saved v001 model after inspecting its actual renders."""
import json
import math
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

helpers=Path(__file__).parents[1]/'build-v001/geometry.py'
exec(compile(helpers.read_text().replace('n, rings = 64, 32','n, rings = 128, 96'),str(helpers),'exec'),globals())
scene=bpy.context.scene
ANCHOR=bpy.data.objects['REPLICA_coordinates_metres']
assert scene['project_id']=='violet-rabbit-replica-20260918'
purple=bpy.data.materials['01_Worn_muted_violet_short_nap']
pale=bpy.data.materials['02_Worn_grey_lilac_patches']
inner=bpy.data.materials['03_Dark_ear_velvet']
black=bpy.data.materials['05_Black_woven_bow']
lining=bpy.data.materials['06_Exposed_dark_worn_lining']
metal=bpy.data.materials['07_Old_dark_steel']
eye=bpy.data.materials['08_Black_recessed_glass']
teeth=bpy.data.materials['09_Aged_olive_ivory']
gum=bpy.data.materials['10_Dark_recessed_gums']
NEW=[];CHANGED=[]
def remove(name):
    ob=bpy.data.objects.get(name)
    if ob:
        while ob in CHANGED:CHANGED.remove(ob)
        bpy.data.objects.remove(ob,do_unlink=True)
def transform_world(ob, fn):
    inv=ob.matrix_world.inverted()
    for v in ob.data.vertices: v.co=inv@Vector(fn(ob.matrix_world@v.co))
    ob.data.update();CHANGED.append(ob)
def rounded_box(name,center,dimensions,radius,material):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center)
    ob=bpy.context.object;ob.name=name;ob.dimensions=dimensions
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.data.materials.append(material)
    m=ob.modifiers.new('Soft rounded corners','BEVEL');m.width=radius;m.segments=6
    apply(ob,m)
    for p in ob.data.polygons:p.use_smooth=True
    return ob

# Updated lossless-exemplar images are editable and packed by the bridge.
folder=Path(WORKSPACE_DIR)/'output/surfaces'
replaced=[]
for mat in [purple,pale,inner,bpy.data.materials['04_Head_shell_with_faded_eye_mask']]:
    nt=mat.node_tree;kind='pale' if mat==pale else 'inner' if mat==inner else 'purple'
    for nd in list(nt.nodes):
        if nd.type=='TEX_IMAGE' and nd.image:
            filename=Path(bpy.path.abspath(nd.image.filepath)).name
            newfile=folder/filename
            if nd.name.startswith('Reference projection '):
                view=nd.name.rsplit(' ',1)[-1]
                newfile=folder/('projection_'+('pale' if kind=='pale' else 'purple')+'_'+view+'.png')
                # Alpha masks stop unrelated reference materials leaking into this surface.
                for link in list(nd.outputs['Color'].links):
                    mix=link.to_node
                    if mix.type=='MIX_RGB':
                        old=mix.inputs[0].links[0].from_socket
                        factor=nt.nodes.new('ShaderNodeMath');factor.operation='MULTIPLY';factor.name='Reference material isolation '+view
                        nt.links.new(old,factor.inputs[0]);nt.links.new(nd.outputs['Alpha'],factor.inputs[1]);nt.links.new(factor.outputs[0],mix.inputs[0])
            if newfile.is_file():
                noncolor=filename.endswith(('_height.png','_roughness.png'))
                image=bpy.data.images.load(str(newfile),check_existing=True)
                if noncolor:image.colorspace_settings.name='Non-Color'
                nd.image=image;replaced.append(newfile.name)
        if nd.type=='BUMP': nd.inputs['Strength'].default_value=.12;nd.inputs['Distance'].default_value=.0012
        if nd.name.startswith('Photo strength '): nd.inputs[1].default_value *= .64
    bs=nt.nodes.get('Principled BSDF');bs.inputs['Specular IOR Level'].default_value=.09;bs.inputs['Sheen Weight'].default_value=.035
for p in ['Specular IOR Level']:
    eye.node_tree.nodes.get('Principled BSDF').inputs[p].default_value=.018
eye.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.12
bs=metal.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.009,.010,.009,1);bs.inputs['Roughness'].default_value=.67;bs.inputs['Metallic'].default_value=.60

# Keep the accepted front dimensions, but correct profile depth and ear alignment.
head=bpy.data.objects['Head_sculpted_continuous_shell']
def head_warp(p):
    x,y,z=p
    y=.91*y-.052
    cheek=max(0,1-abs(z-1.79)/.095)*max(0,min(1,(abs(x)-.14)/.08))
    if y<-.17:y+=.018*cheek
    return x,y,z
transform_world(head,head_warp)
for label in ['L','R']:
    ob=bpy.data.objects[label+'_recessed_black_eye'];ob.location.y=.91*ob.location.y-.052;ob.scale.y*=.91;CHANGED.append(ob)
muzzle=bpy.data.objects['Muzzle_continuous_bilobed']
transform_world(muzzle,lambda p:(p.x*.96,p.y,1.757+(p.z-1.757)*.96))
remove('Muzzle_central_split')
bpy.context.view_layer.update()
muzzle_bvh=BVHTree.FromObject(muzzle,bpy.context.evaluated_depsgraph_get())
pts=[]
for z in [1.766,1.750,1.738,1.727]:
    origin=muzzle.matrix_world.inverted()@Vector((0,-1,z))
    hit=muzzle_bvh.ray_cast(origin,Vector((0,1,0)),2)[0]
    if hit:
        p=muzzle.matrix_world@hit;pts.append((p.x,p.y-.001,p.z))
assert len(pts)>=2
tube_curve('Muzzle_fitted_central_split',pts,.0013,lining)
remove('Nose_soft_triangle')
verts=[]
for y in [-.343,-.400]:
    for x,z in [(-.058,1.806),(.058,1.806),(0,1.752)]:verts.append((x,y,z))
nose=mesh_object('Nose_embedded_rounded_triangle',verts,[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],eye)
m=nose.modifiers.new('Soft nose edge','BEVEL');m.width=.010;m.segments=6;apply(nose,m);NEW.append(nose)
remove('Mouth_deep_black_interior')
interior=rounded_box('Mouth_interior_within_head',(0,-.026,1.677),(.342,.029,.123),.009,lining);NEW.append(interior)
remove('Jaw_continuous_deep_horseshoe')
# Thick swept side blades form the C-shaped profile; the old single U-tube collapsed to a diagonal bar in side view.
outline=[(-.211,1.799),(-.145,1.807),(-.088,1.781),(-.059,1.739),(-.069,1.687),(-.119,1.635),(-.207,1.594),(-.311,1.561),(-.358,1.561),(-.376,1.586),(-.334,1.616),(-.264,1.644),(-.192,1.681),(-.166,1.717),(-.180,1.747),(-.217,1.755)]
parts=[]
for s in [-1,1]:
    vs=[];fs=[];n=len(outline)
    for layer in [-1,1]:
        for y,z in outline:
            cx=.214-.32*(1.80-z)-.14*max(0,-y-.22)
            vs.append((s*cx+layer*.025,y,z))
    fs=[tuple(reversed(range(n))),tuple(n+j for j in range(n))]
    for j in range(n):fs.append((j,(j+1)%n,n+(j+1)%n,n+j))
    ob=mesh_object('Jaw_side_blade_'+str(s),vs,fs,pale)
    m=ob.modifiers.new('Soft shell perimeter','BEVEL');m.width=.009;m.segments=5;apply(ob,m);parts.append(ob)
front=tube_curve('Jaw_front_chin_union',[(-.146,-.324,1.605),(-.112,-.357,1.578),(0,-.374,1.568),(.112,-.357,1.578),(.146,-.324,1.605)],.022,pale)
active(front);bpy.ops.object.convert(target='MESH');parts.append(bpy.context.object)
jaw=fuse('Jaw_deep_curved_mandible',parts,pale,.0026,4);NEW.append(jaw)
for name in ['lower_gum_recess','upper_gum_recess']:remove(name)
for ob in list(scene.objects):
    if '_tooth_' in ob.name:remove(ob.name)
for row in ['lower','upper']:
    pts=[]
    for i in range(9):
        a=-1.07+2.14*i/8;x=.151*math.sin(a)
        if row=='lower':
            y=-.332+.089*(1-math.cos(a));z=1.619+.042*abs(math.sin(a))**1.6
            dims=(.0345,.032,.039);rad=.012
        else:
            y=-.307+.077*(1-math.cos(a));z=1.718+.019*abs(math.sin(a))
            dims=(.030,.028,.027);rad=.010
        ob=rounded_box(row+'_tooth_'+str(i+1),(x,y,z),dims,rad,teeth)
        ob.rotation_euler.z=-a*.35;NEW.append(ob)
        pts.append((x,y+.010,z+(-.017 if row=='lower' else .014)))
    tube_curve(row+'_gum_recess',pts,.010,gum)

# Recessed, softly squared ears with rounded crowns and depth/lean in profile.
for s,label in [(-1,'L'),(1,'R')]:
    remove(label+'_thick_ear_shell');remove(label+'_recessed_inner_ear')
    profiles=[]
    for z,rx,thick in [(2.074,.057,.052),(2.080,.064,.061),(2.12,.069,.066),(2.30,.079,.070),(2.44,.083,.073),(2.51,.079,.071),(2.555,.063,.060),(2.585,.035,.035),(2.599,.005,.006)]:
        t=(z-2.074)/.525;profiles.append((z,rx,thick,thick,-.035-.070*t**2.4))
    ear=shell(label+'_thick_rounded_ear',profiles,purple,.47,80,2);ear.location.x=s*.113
    cutprofiles=[];insetprofiles=[]
    for z,rx in [(2.083,.020),(2.092,.035),(2.14,.041),(2.36,.044),(2.441,.043),(2.475,.030),(2.489,.003)]:
        t=(z-2.074)/.525;cy=-.060-.070*t**2.4
        cutprofiles.append((z,rx,.200,.026,cy))
        insetprofiles.append((z+.001,max(.002,rx-.002),.004,.004,cy+.021))
    cut=shell(label+'_ear_slot_cutter',cutprofiles,lining,.60,64,2);cut.location.x=s*.113
    boolean_cut(ear,cut)
    ear.data.materials.append(pale)
    for p in ear.data.polygons:
        if 2.438<p.center.z<2.572 and p.normal.y<-.15:p.material_index=1
    inset=shell(label+'_dark_recessed_ear_pad',insetprofiles,inner,.64,64,2);inset.location.x=s*.113
    NEW.extend([ear,inset])
    bpy.data.objects[label+'_ear_pin'].location.y-=.025
    bpy.data.objects[label+'_ear_coil_spring'].location.y-=.025

# Fit the patch to the actual subdivided body, not its unsmoothed analytic approximation.
bpy.context.view_layer.update();body=bpy.data.objects['Torso_continuous_tapered_shell']
bvh=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
def fitted_y(x,z,clearance):
    hit=bvh.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),2)[0]
    assert hit is not None,(x,z)
    return hit.y-clearance
bib=bpy.data.objects['Belly_fitted_flat_bottom_patch']
transform_world(bib,lambda p:(p.x,fitted_y(p.x,p.z,.0045),p.z))
for label in ['L','R']:
    wing=bpy.data.objects[label+'_bow_wing_with_folds']
    transform_world(wing,lambda p:(p.x,fitted_y(p.x,p.z,.025)+.006*math.cos(p.z*125),p.z))
knot=bpy.data.objects['Bow_central_knot'];knot.location.y=fitted_y(0,knot.location.z,.040)
# Bring cuff edges close to the torso and to one another; darken the exposed pins.
for label,s in [('L',-1),('R',1)]:
    for suffix,a,b,aa,bb in [('_upper_arm_shell',.306,.574,.282,.578),('_forearm_shell',.591,.862,.584,.866)]:
        for ending in ['', '_dark_inner_lining']:
            ob=bpy.data.objects[label+suffix+ending]
            transform_world(ob,lambda p,s=s,a=a,b=b,aa=aa,bb=bb:(s*(aa+(s*p.x-a)*(bb-aa)/(b-a)),p.y,p.z))
# Replace only the two visibly stair-stepped torn surfaces at higher edge resolution.
for name in ['L_upper_arm_shell','L_upper_arm_shell_dark_inner_lining','L_thigh_shell','L_thigh_shell_dark_inner_lining']:remove(name)
def arm_damage(t,a):return .08<t<.63+.042*math.sin(a*7)+.012*math.sin(a*19) and .14+.075*math.sin(t*25)<a<1.69
arm=cuff('L_upper_arm_shell',(-.282,0,1.465),(-.578,0,1.465),.104,.097,purple,arm_damage,lining)
def thigh_damage(t,a):return t>.56+.06*math.sin(a*5)+.018*math.sin(a*19) and .27<a<2.15
thigh=cuff('L_thigh_shell',(-.148,0,.596),(-.148,0,.884),.119,.105,purple,thigh_damage,lining)
NEW.extend([arm,thigh,bpy.data.objects['L_upper_arm_shell_dark_inner_lining'],bpy.data.objects['L_thigh_shell_dark_inner_lining']])
# Continuous wide shoes with rounded-box toe caps rather than exposed spherical pods.
for s,label in [(-1,'L'),(1,'R')]:
    remove(label+'_continuous_three_toed_foot')
    pieces=[ellipsoid(label+'_heel_union',(s*.148,.038,.088),(.146,.163,.083),purple),ellipsoid(label+'_forefoot_union',(s*.190,-.111,.081),(.185,.204,.077),purple)]
    for i,dx in enumerate([-.121,0,.121]):
        pieces.append(rounded_box(label+'_toe_union_'+str(i),(s*.190+dx,-.266,.079),(.130,.180,.148),.046,purple))
    foot=fuse(label+'_continuous_three_toed_foot',pieces,purple,.0033,3)
    transform_world(foot,lambda p:(p.x,p.y,max(.006,p.z)))
    foot.data.materials.append(pale)
    for p in foot.data.polygons:
        c=foot.matrix_world@p.center;p.material_index=1 if c.y<-.221 else 0
    NEW.append(foot)

# Preserve existing genuine UV layouts. Refresh only calibrated source projections for modified meshes.
bpy.context.view_layer.update()
for ob in set(CHANGED):
    if ob.name not in scene.objects or ob.type!='MESH':continue
    old=[tuple(v.uv) for v in ob.data.uv_layers['UVMap'].data] if ob.data.uv_layers.get('UVMap') else None
    project_uvs(ob)
    if old:
        for v,uv in zip(ob.data.uv_layers['UVMap'].data,old):v.uv=uv
for ob in NEW:project_uvs(ob);ob['asset']='violet-rabbit-replica-20260918'
bpy.ops.object.select_all(action='DESELECT')
for ob in NEW:ob.select_set(True)
bpy.context.view_layer.objects.active=jaw
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15192,island_margin=.008);bpy.ops.object.mode_set(mode='OBJECT')
# Remove unused old packed versions, but preserve the genuine reference image.
for image in list(bpy.data.images):
    if image.users==0:bpy.data.images.remove(image)
points=[];missing=[]
for ob in scene.objects:
    if ob.type=='MESH':
        if not ob.data.uv_layers or not ob.data.materials:missing.append(ob.name)
        for v in ob.data.vertices:
            p=ob.matrix_world@v.co;assert all(math.isfinite(x) for x in p);points.append(p)
assert not missing
lo=[min(p[k] for p in points) for k in range(3)];hi=[max(p[k] for p in points) for k in range(3)]
report={'project_id':JOB['project_id'],'job_id':JOB['job_id'],'source_snapshot':'build-v001 sequence 4',
        'blender':bpy.app.version_string,'mesh_vertices':len(points),'bounds_min':lo,'bounds_max':hi,'dimensions':[hi[k]-lo[k] for k in range(3)],
        'missing_uvs_or_materials':missing,'teeth':len([o for o in scene.objects if '_tooth_' in o.name]),
        'new_meshes_unwrapped':len(NEW),'prior_uv_layouts_preserved':True,'replacement_images':sorted(set(replaced)),
        'review':'pending actual render; do not infer approval from these checks'}
assert report['teeth']==18
(Path(OUTPUT_DIR)/'geometry_validation.json').write_text(json.dumps(report,indent=2))
checkpoint('refined','Profile jaw, ears, head depth, attached nose, patch fit, seams and feet corrected from actual v001 review')
