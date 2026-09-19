"""Folded-eared rabbit: geometry-only derivative of the verified form-v003 scene.
Current three user views, not the former standing-ear/T-pose reference, govern it.
Units metres, +Z up, -Y front. Neutral region materials; no image textures.
"""
import ast, bisect, bpy, bmesh, math, json, hashlib, shutil
from pathlib import Path
from mathutils import Vector, Matrix
from math import sin, cos, pi, sqrt
OUT=Path(OUTPUT_DIR);OUT.mkdir(parents=True,exist_ok=True)
BASE=Path(WORKSPACE_DIR)/'output'/'import'/'parent'
scene=bpy.context.scene
assert scene['project_id']=='rabbit-geometry-20260918' and scene['job_id']=='form-v003'
parent_hash=hashlib.sha256((BASE/'model.blend').read_bytes()).hexdigest()
assert parent_hash=='4a22745761274f797c9a8f10766d653cd1196ef249bd940b98ee60244a5e6c1f'
base=(BASE/'base_geometry_source.py').read_text();parent=(BASE/'geometry_source.py').read_text()
assert hashlib.sha256(base.encode()).hexdigest()=='4a81f39cf97f8990133e98de9f9c834e259b213a9699b25eab3020b53d554b5f'
COL={c.name:c for c in bpy.data.collections}
SHELL=bpy.data.materials['Clay | shell'];PANEL=bpy.data.materials['Clay | face and panel']
INNER=bpy.data.materials['Clay | inner ear'];DARK=bpy.data.materials['Inspection | internal']
EYE=bpy.data.materials['Inspection | eyes and nose'];CLOTH=bpy.data.materials['Inspection | bow tie']
TOOTH=bpy.data.materials['Clay | teeth'];METAL=bpy.data.materials['Inspection | connectors']
for text,names in [(base,{'place','mesh','apply','ball','cylinder','spow','loft','boolean','tube','curve','fused'}),(parent,{'spline','interp'})]:
    nodes=[n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes}==names
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<saved-parent-helper-definitions>','exec'),globals())
# Reuse the actual saved eye, nose and dental meshes, not a new placeholder scene.
reuse_names=['Nose','Eye R','Eye L']+[f'{row} tooth {i:02d}' for row in ['Lower','Upper'] for i in range(1,11)]
reuse={n:bpy.data.objects[n] for n in reuse_names}
for o in list(bpy.data.objects):
    if o.name not in reuse:bpy.data.objects.remove(o,do_unlink=True)
for image in list(bpy.data.images):
    if image.type not in {'RENDER_RESULT','COMPOSITING'}:bpy.data.images.remove(image)
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1.0
scene['project_id']=JOB['project_id'];scene['job_id']=JOB['job_id']
scene['parent_project']='rabbit-geometry-20260918';scene['parent_job']='form-v003'
scene['scope']='Geometry only. Current folded ears and lowered arms. No finished UV, textures or rig.'
scene['front_axis']='-Y';scene['height_target_m']=2.20
scene['reference_note']='Original 1086x1448 views inspected in chat; actual-pixel 300x400 WebP derivatives packed here.'

def fit(o,center,dimensions):
    pts=[o.matrix_world@v.co for v in o.data.vertices]
    lo=Vector([min(p[k] for p in pts) for k in range(3)]);hi=Vector([max(p[k] for p in pts) for k in range(3)])
    middle=(lo+hi)/2;scale=Vector([dimensions[k]/(hi[k]-lo[k]) for k in range(3)])
    o.matrix_world=Matrix.Identity(4)
    for v,p in zip(o.data.vertices,pts):v.co=Vector(center)+Vector([(p[k]-middle[k])*scale[k] for k in range(3)])
    o.hide_render=False;o.hide_set(False);o.data.update();o['inherited_from']='rabbit-geometry-20260918/form-v003'
    return o

def roundbox(name,center,dimensions,radius,col,mat=SHELL):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center);o=bpy.context.object;o.dimensions=dimensions
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    m=o.modifiers.new('Rounded manufactured edge','BEVEL');m.width=radius;m.segments=8;apply(o,m)
    m=o.modifiers.new('Continuous surface curvature','SUBSURF');m.levels=2;m.render_levels=2;apply(o,m)
    return place(o,name,col,mat)

def orient(o,a,b):
    # Front facing local -Y, longitudinal local Z. Used for shoulder segments/ears.
    a,b=Vector(a),Vector(b);axis=(b-a).normalized();u=Vector((0,1,0)).cross(axis).normalized();v=axis.cross(u).normalized()
    rot=Matrix((u,v,axis)).transposed().to_4x4();o.matrix_world=Matrix.Translation((a+b)/2)@rot
    return rot,(a+b)/2

def beam(name,a,b,width,depth,radius,col,mat=SHELL):
    length=(Vector(b)-Vector(a)).length
    o=roundbox(name,(0,0,0),(width,depth,length),radius,col,mat);orient(o,a,b)
    return o

def smooth(o,voxel=None,iters=6):
    if voxel:
        m=o.modifiers.new('Uniform editable sculpt topology','REMESH');m.mode='VOXEL';m.voxel_size=voxel;m.use_smooth_shade=True;apply(o,m)
    m=o.modifiers.new('Surface relaxation','SMOOTH');m.factor=.36;m.iterations=iters;apply(o,m)
    for face in o.data.polygons:face.use_smooth=True

# Broad, weighted belly and rounded box back, traced in both front and side views.
bp=[(.952,.001,-.03,.03),(.952,.216,-.210,.166),(.962,.258,-.240,.195),
    (1.012,.270,-.251,.205),(1.130,.265,-.251,.214),(1.266,.251,-.238,.208),
    (1.405,.232,-.206,.186),(1.510,.205,-.157,.150),(1.565,.157,-.100,.095),(1.585,.080,-.052,.056),(1.590,.001,.0,.002)]
body=loft('Torso outer casing',bp,'01_BODY',SHELL,2.65,96,density=12)
body['construction']='C2 front/back silhouette sections; low, broad belly and separate shoulder caps'
rows=interp(bp,28)
def body_at(z):
    for a,b in zip(rows,rows[1:]):
        if a[0]<=z<=b[0]:
            t=(z-a[0])/max(1e-9,b[0]-a[0]);return [a[j]*(1-t)+b[j]*t for j in range(1,4)]
    raise ValueError('Panel outside body '+str(z))
pp=[(.958,.004),(.963,.14),(.990,.198),(1.060,.220),(1.180,.219),(1.305,.184),(1.416,.120),(1.472,.055),(1.481,.004)]
v=[];f=[];nx=60
for z,w in interp(pp,12):
    rx,yf,yb=body_at(z);w=min(w,rx*.93)
    for j in range(nx+1):
        x=w*(2*j/nx-1);y=(yf+yb)/2-(yb-yf)/2*max(0,1-(abs(x)/rx)**2.65)**(1/2.65)-.002
        v.append((x,y,z))
nr=len(v)//(nx+1)
for i in range(nr-1):
    for j in range(nx):a=i*(nx+1)+j;f.append((a,a+1,a+nx+2,a+nx+1))
panel=mesh('Fitted belly panel',v,f,'01_BODY',PANEL)
m=panel.modifiers.new('Thin fitted panel backing','SOLIDIFY');m.thickness=.003;m.offset=0;apply(panel,m)
ball('Tail',(0,.215,1.010),(.074,.070,.074),'01_BODY',PANEL,64,40)
cylinder('Neck connector',(0,.008,1.51),(0,.008,1.625),.091)

# Pelvis bridge unites the two upper leg shells into the reference's U-shaped hip.
hip=roundbox('_pelvic_bridge',(0,.012,.906),(.479,.277,.139),.047,'06_LEGS')
parts=[hip]
for s,label in [(-1,'R'),(1,'L')]:
    tp=[(.610,.001,-.012,.015),(.610,.089,-.099,.107),(.621,.117,-.128,.144),(.695,.125,-.140,.160),(.826,.128,-.139,.158),(.930,.121,-.131,.151),(.972,.10,-.10,.12),(.975,.001,.01,.012)]
    parts.append(loft('_thigh '+label,tp,'06_LEGS',SHELL,2.8,72,lambda p,s=s:(p[0]+s*.145,p[1],p[2]),10))
    sp=[(.244,.001,-.01,.015),(.244,.085,-.095,.109),(.253,.117,-.123,.139),(.320,.126,-.131,.142),(.469,.125,-.128,.144),(.566,.12,-.119,.13),(.604,.087,-.09,.10),(.604,.001,.0,.002)]
    loft('Shin shell '+label,sp,'06_LEGS',SHELL,2.85,72,lambda p,s=s:(p[0]+s*.157,p[1],p[2]),10)
    cylinder('Knee joint '+label,(s*.154,0,.59),(s*.154,0,.64),.085)
hip=fused('Pelvis and thigh casing',parts,'06_LEGS',SHELL,.0025);smooth(hip,iters=5)
# Sole-flat domes: no flat front caps or rings on the toe surface.
def toe(name,cx,cy,rx,ry,h):
    n=72;nr=36;v=[];f=[]
    for i in range(nr):
        t=(pi/2)*i/nr
        for j in range(n):
            a=2*pi*j/n
            v.append((cx+rx*cos(t)*spow(cos(a),.78),cy+ry*cos(t)*spow(sin(a),.84),.005+h*sin(t)))
    for i in range(nr-1):
        for j in range(n):a=i*n+j;b=i*n+(j+1)%n;f.append((a,b,b+n,a+n))
    v.append((cx,cy,.005+h));pole=len(v)-1
    for j in range(n):f.append(((nr-1)*n+j,(nr-1)*n+(j+1)%n,pole))
    f.append(tuple(reversed(range(n))));o=mesh(name,v,f,'07_FEET',PANEL);o['sole_height_m']=.005
for s,label in [(-1,'R'),(1,'L')]:
    fp=[(.008,.001,-.04,.04),(.008,.126,-.191,.120),(.015,.157,-.248,.147),(.075,.169,-.260,.152),(.151,.151,-.198,.142),(.214,.122,-.110,.125),(.242,.103,-.09,.099),(.244,.001,.0,.002)]
    loft('Foot heel casing '+label,fp,'07_FEET',SHELL,2.65,80,lambda p,s=s:(p[0]+s*.176,p[1],p[2]),10)
    for i,(x,y,h) in enumerate([(.110,-.248,.160),(.235,-.248,.166),(.357,-.217,.149)],1):toe('Toe cap '+label+str(i),s*x,y,.074,.116,h)
    cylinder('Ankle joint '+label,(s*.157,0,.225),(s*.157,0,.276),.083)

# Lowered arms: explicit shoulder cap, upper-arm and forearm panels with joints.
for s,label in [(-1,'R'),(1,'L')]:
    ball('Shoulder cap '+label,(s*.246,.015,1.471),(.113,.132,.129),'04_ARMS',SHELL,64,40)
    a=(s*.283,-.001,1.454);b=(s*.347,-.004,1.230)
    beam('Upper arm casing '+label,a,b,.201,.218,.036,'04_ARMS')
    a=(s*.359,-.004,1.219);b=(s*.423,-.014,.974)
    beam('Forearm casing '+label,a,b,.190,.190,.030,'04_ARMS')
    ball('Elbow joint '+label,(s*.350,0,1.225),(.075,.077,.070),'09_INTERNAL',METAL)
    ball('Wrist joint '+label,(s*.426,-.006,.970),(.058,.063,.052),'09_INTERNAL',METAL)
    palm=roundbox('_palm',(s*.449,-.003,.886),(.120,.170,.160),.033,'05_HANDS')
    parts=[palm]
    thumbpath=spline([(s*.426,-.048,.929,.039),(s*.409,-.075,.904,.036),(s*.386,-.086,.866,.033),(s*.366,-.086,.824,.027),(s*.365,-.084,.808,.001)],48)
    parts.append(tube('_thumb',[p[:3] for p in thumbpath],[p[3] for p in thumbpath],[p[3] for p in thumbpath],'05_HANDS',SHELL,28))
    palm=fused('Palm and thumb '+label,parts,'05_HANDS',SHELL,.0019);smooth(palm,iters=8)
    for j,y in enumerate([-.061,0,.061],1):
        pts=[(s*.472,y,.838,.027),(s*.479,y,.810,.030),(s*.480,y,.775,.028),(s*.466,y,.744,.027),(s*.438,y,.716,.026),(s*.414,y,.715,.017),(s*.408,y,.720,.001)]
        path=spline(pts,70)
        o=tube('Finger '+label+str(j),[p[:3] for p in path],[p[3] for p in path],[p[3] for p in path],'05_HANDS',SHELL,32)
        o['construction']='Three individual curled digits arranged across palm depth, not a front-facing fan'
checkpoint('body-and-lowered-limbs','Current-reference belly, hips, broad feet, lowered arms and curled fingers saved')

# Face: cranium, separate buccal pads and thick C-shaped mandibular shell.
hp=[(1.601,.001,.0,.002),(1.601,.137,-.135,.105),(1.610,.18,-.219,.144),
    (1.682,.208,-.235,.153),(1.753,.210,-.251,.156),(1.814,.204,-.251,.153),
    (1.876,.194,-.232,.139),(1.936,.173,-.195,.116),(1.985,.103,-.12,.081),(2.003,.035,-.057,.038),(2.003,.001,-.009,-.007)]
head=loft('Head casing',hp,'02_HEAD',SHELL,2.25,112,density=12)
boolean(head,ball('_oral_cutter',(0,-.260,1.585),(.155,.173,.087),'09_INTERNAL',None,80,48),'Actual mouth opening')
for s,label in [(-1,'R'),(1,'L')]:
    boolean(head,ball('_orbital_cutter',(s*.069,-.244,1.824),(.048,.068,.057),'09_INTERNAL',None,72,48),'Recessed eye socket '+label)
smooth(head,.0019,12)
head.data.materials.append(PANEL)
for face in head.data.polygons:
    c=face.center;brow=1.861+.057*math.exp(-((abs(c.x)-.069)/.068)**2)
    if c.y<-.13 and c.z<brow:face.material_index=1
for s,label in [(-1,'R'),(1,'L')]:
    cheek=ball('Cheek pad '+label,(s*.181,-.085,1.713),(.066,.088,.085),'02_HEAD',PANEL,80,56)
    for v in cheek.data.vertices:
        w=max(0.,min(1.,-v.co.z/.085));v.co.x-=s*.017*w*w
    cheek.rotation_euler[1]=s*math.radians(17)
    pad=roundbox('Muzzle cushion '+label,(s*.059,-.259,1.655),(.127,.124,.127),.047,'02_HEAD',PANEL)
    pad.rotation_euler[1]=s*math.radians(-5)
    fit(reuse['Eye '+label],(s*.069,-.238,1.820),(.071,.051,.078))
    ball('Socket lining '+label,(s*.069,-.215,1.823),(.044,.043,.052),'09_INTERNAL',DARK,64,40)
    v=[];f=[];n=80;k=12
    for i in range(n):
        a=2*pi*i/n
        for j in range(k):
            t=2*pi*j/k;r=.0035
            v.append((s*.069+(.046+r*cos(t))*cos(a),-.242+r*sin(t),1.824+(.055+r*cos(t))*sin(a)))
    for i in range(n):
        for j in range(k):f.append((i*k+j,i*k+(j+1)%k,((i+1)%n)*k+(j+1)%k,((i+1)%n)*k+j))
    mesh('Orbital rim '+label,v,f,'02_HEAD',INNER)
half=[(.150,-.072,1.664,.037),(.168,-.073,1.623,.038),(.161,-.110,1.578,.039),(.131,-.187,1.529,.035),(.070,-.254,1.511,.029),(0.,-.270,1.512,.029)]
path=spline(half+[(-x,y,z,r) for x,y,z,r in reversed(half[:-1])],161)
jaw=tube('U shaped lower jaw',[p[:3] for p in path],[p[3] for p in path],[p[3] for p in path],'02_HEAD',PANEL,40)
smooth(jaw,.0018,6)
ball('Mouth internal baffle',(0,-.141,1.604),(.136,.054,.079),'09_INTERNAL',DARK,64,40)
fit(reuse['Nose'],(0,-.326,1.670),(.100,.056,.050))
for i in range(10):
    t=-1.30+2.60*i/9;x=.122*sin(t);y=-.169-.105*cos(t)
    z=1.553+.029*sin(t)**2
    o=fit(reuse['Lower tooth %02d'%(i+1)],(x,y,z),(.031,.032,.036));o['row']='Lower dental arch'
    o=fit(reuse['Upper tooth %02d'%(i+1)],(x,y+.010,1.612+.011*sin(t)**2),(.029,.028,.026));o['row']='Upper dental arch'
for s,label in [(-1,'R'),(1,'L')]:
    for i,(dz,ez) in enumerate([(.012,.004),(.0,-.013),(-.013,-.038)],1):
        curve('Whisker '+label+str(i),[(s*.113,-.298,1.632+dz),(s*.148,-.284,1.626+dz),(s*.204,-.254,1.632+ez),(s*.231,-.243,1.624+ez)],.00065,'08_DETAILS',DARK)
checkpoint('face-and-mouth','True orbital/oral recesses, separate cheek pads, split muzzle and thick curved mandible')

# Ear pairs: bent upper phalanges, not merely tilted straight rabbit ears.
for s,label in [(-1,'R'),(1,'L')]:
    a=(s*.108,-.104,1.981);b=(s*.188,-.169,2.163)
    length=(Vector(b)-Vector(a)).length
    ear=roundbox('Ear outer '+label,(0,0,0),(.130,.084,length+.012),.023,'03_EARS',SHELL)
    cut=roundbox('_channel',(0,-.042,-.008),(.066,.051,length+.008),.021,'09_INTERNAL',None)
    boolean(ear,cut,'Deep open-bottom inner ear channel')
    back=roundbox('Ear recessed insert '+label,(0,-.018,-.008),(.058,.005,length-.010),.002,'03_EARS',INNER)
    rot,center=orient(ear,a,b)
    back.matrix_world=Matrix.Translation(center)@rot@back.matrix_world
    cap_a=(s*.171,-.169,2.164);cap_b=(s*.288,-.291,2.110)
    cap=beam('Ear folded cap '+label,cap_a,cap_b,.127,.099,.027,'03_EARS',SHELL)
    rot,center=orient(cap,cap_a,cap_b)
    cap_len=(Vector(cap_b)-Vector(cap_a)).length
    pad=roundbox('Ear cap inset '+label,(0,-.049,cap_len*.12),(.114,.012,cap_len*.83),.005,'03_EARS',PANEL)
    pad.matrix_world=Matrix.Translation(center)@rot@pad.matrix_world
    ball('Ear hinge '+label,a,(.031,.026,.028),'09_INTERNAL',METAL)
    ear['construction']='Thick lower segment with recessed channel and separate forward/outward folded cap'

# Broad pleated bow: shaped volume and folds, not crossed flat ellipses.
def bow_wing(s,label):
    outline=[(.021,1.466),(.089,1.491),(.168,1.520),(.156,1.444),(.134,1.337),(.073,1.386),(.025,1.416)]
    edge=[]
    for i,p in enumerate(outline):
        prev=outline[(i-1)%len(outline)];nxt=outline[(i+1)%len(outline)]
        a=[p[k]*.9+prev[k]*.1 for k in range(2)];b=[p[k]*.9+nxt[k]*.1 for k in range(2)]
        for j in range(8):
            t=j/8;edge.append([(1-t)**2*a[k]+2*t*(1-t)*p[k]+t*t*b[k] for k in range(2)])
    cx=.085;cz=1.440;v=[];f=[];n=len(edge)
    for r in [1.,.96,.82,.6,.33,.08]:
        for x,z in edge:
            xx=cx+(x-cx)*r;zz=cz+(z-cz)*r
            dy=.026*(1-r*r)+.011*sin(3*math.atan2(zz-cz,xx-cx))*r*(1-r)
            v.append((s*xx,-.214-dy,zz))
    for k in range(5):
        for j in range(n):a=k*n+j;b=k*n+(j+1)%n;f.append((a,b,b+n,a+n))
    v.append((s*cx,-.24,cz));pole=len(v)-1
    for j in range(n):f.append((5*n+j,5*n+(j+1)%n,pole))
    f.append(tuple(reversed(range(n))));mesh('Bow wing '+label,v,f,'08_DETAILS',CLOTH)
for s,label in [(-1,'R'),(1,'L')]:bow_wing(s,label)
roundbox('Bow knot',(0,-.245,1.437),(.058,.047,.059),.014,'08_DETAILS',CLOTH)
for i,z in enumerate([1.348,1.284],1):
    rx,yf,yb=body_at(z);ball('Button '+str(i),(0,yf-.012,z),(.018,.014,.019),'08_DETAILS',EYE,48,32)

# Persist real inputs and all source dependencies for future sessions, not resume/ links.
refs={}
for name in ['front','side','back']:
    src=Path(INPUT_DIR)/'references'/(name+'.webp');dest=OUT/(name+'.webp');shutil.copy2(src,dest)
    refs[name]=hashlib.sha256(src.read_bytes()).hexdigest();image=bpy.data.images.load(str(dest));image.name='Reference current '+name;image.pack()
shutil.copy2(BASE/'base_geometry_source.py',OUT/'base_geometry_source.py')
(OUT/'parent_form-v003_source.py').write_text(parent)
current=Path(__file__).read_text();(OUT/'geometry_source.py').write_text(current)
for name,text in [('BUILD_folded_form-v001.py',current),('PARENT_form-v003.py',parent)]:
    block=bpy.data.texts.get(name) or bpy.data.texts.new(name);block.clear();block.write(text)
scene['reference_sha256']=json.dumps(refs,sort_keys=True)
bpy.context.view_layer.update()
geos=[o for o in scene.objects if o.type in {'MESH','CURVE'} and not o.hide_render]
points=[o.matrix_world@Vector(c) for o in geos for c in o.bound_box]
lo=[min(v[k] for v in points) for k in range(3)];hi=[max(v[k] for v in points) for k in range(3)]
required={'Head casing':1,'Cheek pad ':2,'Muzzle cushion ':2,'Eye ':2,'Nose':1,'U shaped lower jaw':1,'Ear outer ':2,'Ear folded cap ':2,'Ear recessed insert ':2,'Lower tooth ':10,'Upper tooth ':10,'Whisker ':6,'Toe cap ':6,'Finger ':6,'Palm and thumb ':2,'Button ':2,'Bow wing ':2,'Shin shell ':2}
counts={k:sum(o.name.startswith(k) for o in geos) for k in required}
closed={}
for name in ['Head casing','U shaped lower jaw','Ear outer R','Ear outer L','Pelvis and thigh casing','Palm and thumb R','Palm and thumb L']:
    bm=bmesh.new();bm.from_mesh(bpy.data.objects[name].data)
    closed[name]={'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'boundary_edges':sum(e.is_boundary for e in bm.edges)};bm.free()
checks={'required_parts':counts==required,'finite_coordinates':all(math.isfinite(a) for o in geos if o.type=='MESH' for v in o.data.vertices for a in v.co),
    'closed_revised_shells':all(v['nonmanifold_edges']==0 for v in closed.values()),'height_range':2.15<hi[2]-lo[2]<2.27,
    'lowered_arm_span':.95<hi[0]-lo[0]<1.14,'no_texture_nodes':not any(n.type=='TEX_IMAGE' for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes),
    'current_reference_count':len(refs)==3}
audit={'job_id':JOB['job_id'],'pass':all(checks.values()),'checks':checks,'bounds_min':lo,'bounds_max':hi,'dimensions_m':[hi[k]-lo[k] for k in range(3)],'required_counts':counts,'closed_shell_checks':closed,'objects':len(geos),'vertices':sum(len(o.data.vertices) for o in geos if o.type=='MESH'),'polygons':sum(len(o.data.polygons) for o in geos if o.type=='MESH'),'visual_review':'pending exact current-reference images','limitations':['2D reference reconstruction, not recovered original topology','No texture, finished UV or rig','Original full-resolution PNGs are not the packed downsampled WebPs']}
(OUT/'geometry_audit.json').write_text(json.dumps(audit,indent=2))
(OUT/'lineage.json').write_text(json.dumps({'parent_project':'rabbit-geometry-20260918','parent_job':'form-v003','parent_blend_sha256':parent_hash,'reused_saved_meshes':reuse_names,'parent_source_sha256':hashlib.sha256(parent.encode()).hexdigest(),'changes':'New folded ears, lowered arms, broad rounded torso/limbs, separate cheek pads and jaw, curled fingers, splayed three-toed feet. Current three references supersede old T-pose.'},indent=2))
assert audit['pass'],json.dumps(audit)
bpy.ops.object.select_all(action='DESELECT')
checkpoint('geometry-current-reference','Geometry audit passed; current-version visual review is still required')
