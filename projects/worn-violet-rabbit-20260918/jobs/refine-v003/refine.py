"""Partial sculpt revision of the reopened model, driven by the reviewed reference views."""
import bpy
import bmesh
import ast
import math
import json
import random
from pathlib import Path
from mathutils import Vector

random.seed(9183003)
OUT=Path(OUTPUT_DIR);OUT.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
COLS={c.name:c for c in bpy.data.collections}
materials={m.name:m for m in bpy.data.materials}
VIOLET=materials['01_Dusty_violet_worn_textile']
PALE=materials['02_Chalky_grey_lilac_wear']
INNER=materials['03_Recessed_dark_plum_ear']
DARK=materials['04_Deep_cavity_charcoal']
METAL=materials['05_Graphite_endoskeleton']
STEEL=materials['06_Tarnished_joint_edges']
EYES=materials['07_Black_glass_eyes']
BUTTON=materials['08_Black_bakelite']
TIE=materials['09_Black_cotton_bow']
TEETH=materials['10_Aged_dull_ivory']
THREAD=materials['11_Faded_frayed_edges']
base=Path(__file__).resolve().parents[1]/'build-v001'/'model.py'
parsed=ast.parse(base.read_text())
helper_nodes=[n for n in parsed.body if isinstance(n,ast.FunctionDef)]
exec(compile(ast.Module(body=helper_nodes,type_ignores=[]),str(base)+'::helpers','exec'),globals())
changed=[]

def remove(name):
    obj=bpy.data.objects.get(name)
    if obj is not None:bpy.data.objects.remove(obj,do_unlink=True)
    changed.append(name)

def active(ob):
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True)
    bpy.context.view_layer.objects.active=ob

# Fit the limbs to the shell instead of exposing large black shoulder cuffs.
for side in (-1,1):
    tag='R' if side<0 else 'L'
    for suffix in ('upper_arm_shell','upper_arm_inner'):
        ob=scene.objects[tag+'_'+suffix];ob.location.x-=side*.036;ob.scale.x*=.148/.144
        changed.append(ob.name)
    ob=scene.objects[tag+'_forearm_shell'];ob.location.x-=side*.032;ob.scale.x*=.143/.136
    scene.objects[tag+'_elbow'].location.x-=side*.033
    scene.objects[tag+'_shoulder_joint'].location.x-=side*.045
    scene.objects[tag+'_shoulder_joint'].scale.x*=.77
    scene.objects[tag+'_shoulder_axle'].location.x-=side*.032
    scene.objects[tag+'_wrist'].location.x-=side*.024
    scene.objects[tag+'_forearm_end'].location.x-=side*.025
    scene.objects[tag+'_palm'].location.x-=side*.024
    scene.objects[tag+'_thumb'].location.x-=side*.021
    scene.objects[tag+'_foot_housing'].location.x+=side*.011
    scene.objects[tag+'_foot_housing'].location.y+=.014
    scene.objects[tag+'_foot_housing'].scale.y*=.255/.229

# Bring the cranial back forward, then carve real eye sockets.
head=scene.objects['Head_cranial_shell'];head.location.y-=.050
changed.append(head.name)
for side in (-1,1):
    tag='R' if side<0 else 'L'
    for suffix in ('pale_orbital_surround','black_orbital_depth','black_eye','subtle_pupil'):
        remove(tag+'_'+suffix)
    cutter=ell('Temporary_eye_socket_cutter',(side*.076,-.240,1.884),(.058,.108,.065),DARK,n=64)
    active(head)
    mod=head.modifiers.new('Recessed_eye_socket_'+tag,'BOOLEAN');mod.operation='DIFFERENCE'
    mod.solver='EXACT';mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter,do_unlink=True)
    ell(tag+'_black_orbital_depth',(side*.076,-.173,1.884),(.057,.035,.064),DARK)
    eye=ell(tag+'_black_eye',(side*.076,-.211,1.884),(.050,.025,.055),EYES,n=64)
    eye['construction']='Black eye behind the facial rim, inside a real socket; no protruding pupil overlay'

# Continuous pale facial marking following the cranial surface, with open eye holes.
def cranial_front(x,z):
    r=max(.01,1-abs((z-1.837)/.229)**(2/.82))**(.82/2)
    xrel=min(.999,abs(x)/(.246*r))
    return -.023-.228*r*max(.001,1-xrel**(2/.90))**(.90/2)

def mask_inside(x,z):
    outer=any(((x-side*.076)/.091)**2+((z-1.884)/.089)**2<1 for side in (-1,1))
    outer=outer or (abs(x)<.062 and 1.790<z<1.955)
    hole=any(((x-side*.076)/.0545)**2+((z-1.884)/.0615)**2<1 for side in (-1,1))
    return outer and not hole

verts=[];faces=[];uvs=[]
nx,nz=180,116
for k in range(nz+1):
    z=1.787+.191*k/nz
    for j in range(nx+1):
        x=-.172+.344*j/nx
        verts.append((x,cranial_front(x,z)-.0045,z));uvs.append((j/nx,k/nz))
for k in range(nz):
    for j in range(nx):
        x=-.172+.344*(j+.5)/nx;z=1.787+.191*(k+.5)/nz
        if mask_inside(x,z):
            faces.append((k*(nx+1)+j,k*(nx+1)+j+1,(k+1)*(nx+1)+j+1,(k+1)*(nx+1)+j))
mask=mesh_obj('Continuous_conforming_pale_face_mask',verts,faces,PALE,'02_FACE',uvs)
bm=bmesh.new();bm.from_mesh(mask.data)
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
bm.to_mesh(mask.data);bm.free()
sub=mask.modifiers.new('Soft_mask_boundary','SUBSURF');sub.levels=1
sol=mask.modifiers.new('Flush_surface_marking','SOLIDIFY');sol.thickness=.0015
for side in (-1,1):
    verts=[];faces=[];uvs=[]
    for k in range(3):
        for j in range(128):
            a=2*math.pi*j/128
            x=side*.076+(.0545-.002*k)*math.cos(a)
            z=1.884+(.0615-.0015*k)*math.sin(a)
            y=cranial_front(x,z)-.006 if k==0 else (-.208 if k==1 else -.171)
            verts.append((x,y,z));uvs.append((j/128,k/2))
    for k in range(2):
        for j in range(128):faces.append((k*128+j,k*128+(j+1)%128,(k+1)*128+(j+1)%128,(k+1)*128+j))
    mesh_obj('Inset_orbital_wall_'+str(side),verts,faces,PALE,'02_FACE',uvs)
EYES.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.29
EYES.node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=.28

# Central muzzle and larger softly triangular nose, rather than a head-wide white bar.
for side in (-1,1):
    tag='R' if side<0 else 'L'
    remove(tag+'_muzzle_lobe');remove(tag+'_outer_muzzle_fold')
    rounded(tag+'_muzzle_lobe',(side*.069,-.279,1.759),(.082,.084,.063),PALE,'02_FACE',ez=.77,ex=.84,n=64,m=40)
    ell(tag+'_outer_muzzle_fold',(side*.194,-.154,1.769),(.055,.073,.067),PALE,n=64)
ell('Pale_nasal_bridge',(0,-.269,1.806),(.044,.070,.055),PALE,n=64)
remove('Soft_black_triangular_nose')
verts=[(-.059,-.330,1.801),(.059,-.330,1.801),(0,-.312,1.739),
       (-.053,-.377,1.797),(.053,-.377,1.797),(0,-.388,1.744)]
faces=[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)]
nose=mesh_obj('Soft_black_triangular_nose',verts,faces,BUTTON,'02_FACE')
be=nose.modifiers.new('Rounded_nose_edges','BEVEL');be.width=.008;be.segments=5
nose.modifiers.new('Nose_normals','WEIGHTED_NORMAL')
for ob in list(scene.objects):
    if ob.name.startswith(('Nose_to_muzzle_division','Muzzle_smile_','Cheek_crease_','Whisker_root_')):
        remove(ob.name)
curve('Nose_to_muzzle_division',[(0,-.337,1.745),(0,-.330,1.719),(0,-.329,1.697)],.0024,DARK,'02_FACE')
for side in (-1,1):
    curve('Muzzle_smile_'+str(side),[(0,-.329,1.698),(side*.08,-.353,1.699),(side*.146,-.269,1.729),(side*.207,-.223,1.779)],.0019,DARK,'02_FACE')
    for j in range(3):
        curve('Cheek_crease_%s_%s'%(side,j),[(side*.109,-.351,1.748+.016*j),
              (side*.180,-.270,1.725+.038*j),(side*(.238+.007*j),-.172,1.698+.052*j)],.00075,METAL,'02_FACE')
    for x,z in ((.105,1.776),(.120,1.753),(.096,1.738)):
        y=-.279-.084*math.sqrt(max(0,1-((x-.069)/.082)**2-((z-1.759)/.063)**2))-.001
        ell('Whisker_root_%s_%s'%(side,x),(side*x,y,z),(.0017,.001,.0017),METAL,n=16)

# Deeper cheek / lower-jaw sweep, matching the volume visible from the side.
remove('Separate_pale_lower_jaw')
verts=[];faces=[];uvs=[]
for i in range(129):
    t=math.pi*i/128;st=math.sin(t)
    center=Vector((-.202*math.cos(t),-.104-.190*st,1.758-.181*st))
    radial=Vector((-math.cos(t),0,-math.sin(t)))
    thickness=.024+.027*(1-st)**2;depth=.043+.036*(1-st)**2
    for j in range(32):
        a=2*math.pi*j/32
        p=center+radial*(thickness*math.cos(a))+Vector((0,depth*math.sin(a),0))
        verts.append(tuple(p));uvs.append((i/128,j/32))
for i in range(128):
    for j in range(32):faces.append((i*32+j,i*32+(j+1)%32,(i+1)*32+(j+1)%32,(i+1)*32+j))
faces.extend([tuple(reversed(range(32))),tuple(128*32+j for j in range(32))])
mesh_obj('Separate_pale_lower_jaw',verts,faces,PALE,'02_FACE',uvs)
for ob in [o for o in scene.objects if '_tooth_' in o.name]:
    idx=int(ob.name.rsplit('_',1)[-1]);upper=ob.name.startswith('Upper')
    ob.scale.x=.89+.11*random.random();ob.scale.z=.92+.17*random.random()
    ob.rotation_euler.y=math.radians((idx-4)*.7+random.uniform(-2,2))
    if upper:
        ob.location.y+=.012;ob.scale.z*=.86
    else:
        ob.location.y+=.040;ob.location.z-=.007
    changed.append(ob.name)

# Padded ears with curved back volume, a restrained worn rim and a recessed well.
for side in (-1,1):
    tag='R' if side<0 else 'L';remove(tag+'_sculpted_recessed_ear')
    cx=side*.112;cz=2.338
    rings=[(.087,.263,.006),(.081,.258,-.022),(.066,.239,-.043),
           (.050,.218,-.047),(.043,.204,-.026),(.042,.199,.013)]
    verts=[];faces=[];uvs=[];material_ids=[]
    def layer(w,h,y):
        for j in range(128):
            a=2*math.pi*j/128;nz=spow(math.sin(a),.58)
            x=w*spow(math.cos(a),.69)*(.89+.11*(nz+1)/2)
            lean=-.043*max(0,(h*nz/.263-.30)/.70)**2
            verts.append((cx+x,y+lean,cz+h*nz));uvs.append((.5+x/.18,.5+nz/2))
    for w,h,y in rings:layer(w,h,y)
    for k in range(5):
        for j in range(128):
            faces.append((k*128+j,k*128+(j+1)%128,(k+1)*128+(j+1)%128,(k+1)*128+j))
            material_ids.append(0 if k<2 else (1 if k==2 else 2))
    faces.append(tuple(5*128+j for j in range(128)));material_ids.append(2)
    previous=0
    for scale,depth in ((.96,.042),(.80,.061),(.56,.070),(.26,.074)):
        current=len(verts);layer(.087*scale,.263*scale,depth)
        for j in range(128):
            faces.append((previous+j,current+j,current+(j+1)%128,previous+(j+1)%128));material_ids.append(0)
        previous=current
    center=len(verts);verts.append((cx,.075,cz));uvs.append((.5,.5))
    for j in range(128):faces.append((previous+j,center,previous+(j+1)%128));material_ids.append(0)
    ear=mesh_obj(tag+'_sculpted_recessed_ear',verts,faces,VIOLET,'03_EARS',uvs)
    ear.data.materials.append(PALE);ear.data.materials.append(INNER)
    for poly,index in zip(ear.data.polygons,material_ids):poly.material_index=index
    ear['construction']='Volumetric padded back, curved tip, recessed inner ear and restrained worn rim'

# Tapered, nearly rectangular belly facing rather than a large oval badge.
remove('Conforming_pale_belly_panel')
profiles=[(.895,.263,.224,.227),(.911,.289,.249,.241),(1.00,.300,.269,.245),
          (1.17,.288,.266,.239),(1.34,.270,.230,.230),(1.48,.252,.183,.213),
          (1.545,.216,.157,.187),(1.566,.168,.144,.155)]
widths=[(.916,.191),(.926,.217),(.952,.233),(1.10,.238),(1.26,.226),(1.40,.207),(1.52,.174),(1.538,.156)]
def width_at(z):
    for a,b in zip(widths[:-1],widths[1:]):
        if z<=b[0]:
            f=max(0,min(1,(z-a[0])/(b[0]-a[0])));return a[1]*(1-f)+b[1]*f
    return widths[-1][1]
verts=[];faces=[];uvs=[]
for k in range(97):
    z=.916+(.622*k/96);width=width_at(z);rx,front,back=torso_r(z)
    for j in range(81):
        x=width*(2*j/80-1);c=min(.99999,abs(x)/rx)**(1/.72)
        y=-front*max(0,1-c*c)**(.86/2)-.0055
        verts.append((x,y,z));uvs.append((j/80,k/96))
for k in range(96):
    for j in range(80):faces.append((k*81+j,k*81+j+1,(k+1)*81+j+1,(k+1)*81+j))
patch=mesh_obj('Conforming_pale_belly_panel',verts,faces,PALE,'01_HOUSING',uvs)
sol=patch.modifiers.new('Thin_inset_textile','SOLIDIFY');sol.thickness=.002
be=patch.modifiers.new('Soft_panel_edges','BEVEL');be.width=.004;be.segments=3

# Irregular tears open into an outer shell edge, not a rectangular access panel.
def inside_polygon(x,z,polygon):
    inside=False;j=len(polygon)-1
    for i,(xi,zi) in enumerate(polygon):
        xj,zj=polygon[j]
        if (zi>z)!=(zj>z) and x<(xj-xi)*(z-zi)/(zj-zi)+xi:inside=not inside
        j=i
    return inside
leg_poly=[(-.183,.925),(-.004,.925),(-.004,.801),(-.046,.795),(-.052,.752),(-.111,.758),(-.128,.777),(-.169,.773),(-.166,.812),(-.188,.808)]
arm_poly=[(x+.036,z) for x,z in [(-.511,1.577),(-.296,1.577),(-.296,1.477),(-.363,1.478),(-.401,1.489),(-.424,1.505),(-.472,1.501),(-.501,1.529)]]
tear_leg=lambda p:p.y<-.025 and inside_polygon(p.x,p.z,leg_poly)
tear_arm=lambda p:p.y<.035 and inside_polygon(p.x,p.z,arm_poly)
for name,loc,scale,ez,ex,damage in [
    ('R_upper_leg_shell',(-.146,0,.743),(.119,.104,.151),.36,.68,tear_leg),
    ('R_upper_arm_shell',(-.427,0,1.455),(.148,.096,.097),.55,.36,tear_arm)]:
    remove(name)
    ob=rounded(name,loc,scale,VIOLET,ez=ez,ex=ex,n=96,m=52,damage=damage)
    bm=bmesh.new();bm.from_mesh(ob.data)
    kill=[f for f in bm.faces if damage(f.calc_center_median())]
    bmesh.ops.delete(bm,geom=kill,context='FACES_ONLY')
    boundary=[e for e in bm.edges if len(e.link_faces)==1]
    for i,e in enumerate(boundary):
        if i%3:continue
        mid=(e.verts[0].co+e.verts[1].co)/2
        if mid.y>-.025:continue
        delta=Vector((random.uniform(-.002,.002),-.002,random.uniform(-.004,.001)))
        curve(name+'_edge_fray_%03d'%i,[tuple(mid),tuple(mid+delta)],.00042,THREAD,'06_DAMAGE')
    bm.to_mesh(ob.data);bm.free()
for ob in list(scene.objects):
    if ob.name.startswith('Thigh_fray_'):remove(ob.name)
for side in (-1,1):
    tag='R' if side<0 else 'L'
    for k in range(3):
        name=tag+'_pale_toe_'+str(k+1);remove(name)
        rounded(name,(side*.191+(k-1)*.125,-.249,.079),(.061,.095,.070),PALE,'04_HANDS_FEET',ez=.93,ex=.98)

# Actual-reference-derived colour; microrelief is restrained and separately editable.
texture_root=Path(WORKSPACE_DIR)/'output'/'surfaces'
assert json.loads((texture_root/'surface_provenance.json').read_text())['pass']
for mat,prefix,repeat in ((VIOLET,'violet',.36),(PALE,'pale',.27),(INNER,'ear',.36)):
    for node in mat.node_tree.nodes:
        if node.type=='VECT_MATH' and node.operation=='SCALE':node.inputs[3].default_value=1/repeat
        if node.type=='TEX_IMAGE':
            old=node.image.name.lower()
            suffix='height16' if 'height' in old else ('roughness' if 'roughness' in old else 'albedo')
            image=bpy.data.images.load(str(texture_root/(prefix+'_reference_'+suffix+'.png')),check_existing=True)
            if suffix!='albedo':image.colorspace_settings.name='Non-Color'
            node.image=image
        if node.type=='BUMP':node.inputs['Distance'].default_value=.0015;node.inputs['Strength'].default_value=.30
    principled=mat.node_tree.nodes.get('Principled BSDF')
    principled.inputs['Specular IOR Level'].default_value=.14
    principled.inputs['Sheen Weight'].default_value=.06
    mat['reference_derived_surface']='Source crop coordinates and reconstruction in surface_provenance.json; not recovered original UV maps'
scene.objects['Studio_soft_key'].data.energy=300
scene.objects['Studio_soft_fill'].data.energy=140
scene.objects['Studio_rear_softbox'].data.energy=200
scene.world.node_tree.nodes['Ambient_illumination'].inputs['Strength'].default_value=.33
p=TIE.node_tree.nodes.get('Principled BSDF')
p.inputs['Specular IOR Level'].default_value=.055;p.inputs['Sheen Weight'].default_value=.035
TEETH.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.20,.223,.122,1)
STEEL.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.045,.050,.046,1)
STEEL.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.56

for ob in scene.objects:
    if ob.type=='MESH' and ob.location.length<1e-9 and ob.rotation_euler.to_matrix().is_identity:
        if not ob.data.vertices:continue
        center=sum((v.co.copy() for v in ob.data.vertices),Vector())/len(ob.data.vertices)
        for v in ob.data.vertices:v.co-=center
        ob.location=center
if scene.objects.get('Rear_cranial_join'):scene.objects['Rear_cranial_join'].location.y-=.050
scene.cycles.use_denoising=False
for layer in scene.view_layers:
    if hasattr(layer,'cycles') and hasattr(layer.cycles,'use_denoising'):layer.cycles.use_denoising=False
scene['revision']=JOB['job_id'];scene['geometry_revision']=JOB['job_id']
scene['review_status']='unreviewed revised geometry; real comparison renders required'
if bpy.data.texts.get('READ_ME_project.txt'):
    bpy.data.texts['READ_ME_project.txt'].write('\nRevision refine-v003: partially edited restored geometry; traceable reference-derived albedo and separate microrelief. See surface_provenance.json and exact-version review.\n')
bpy.context.view_layer.update()
objects=[o for o in scene.objects if o.type in {'MESH','CURVE'} and not o.hide_render]
points=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box]
lo=[min(v[i] for v in points) for i in range(3)];hi=[max(v[i] for v in points) for i in range(3)]
size=[hi[i]-lo[i] for i in range(3)]
finite=all(math.isfinite(c) for o in objects if o.type=='MESH' for v in o.data.vertices for c in v.co)
missing=[o.name for o in objects if not o.data.materials]
report={'pass':finite and not missing and 2.55<size[2]<2.67 and 2.40<size[0]<2.60,
        'revision':JOB['job_id'],'project_id':JOB['project_id'],'bounds_min':lo,'bounds_max':hi,'dimensions':size,
        'finite_vertices':finite,'renderable_objects':len(objects),'mesh_vertices':sum(len(o.data.vertices) for o in objects if o.type=='MESH'),
        'missing_materials':missing,'changed_parts':changed,'unverified':['visual acceptance','rigging','printable manifold topology'],
        'method':'Partial editing of restored model; unmodified limb shells, mechanisms, reference and material sources retained'}
(OUT/'geometry_validation.json').write_text(json.dumps(report,indent=2)+'\n')
assert report['pass'],report
checkpoint('refined-reference-geometry','Recessed eyes, conforming face, deeper jaw, padded ears, tapered belly and irregular tears saved')
