"""Geometry revision from the hash-verified form-v001 saved scene, not a rebuild of accepted parts."""
import bpy, bmesh, math, json, hashlib, shutil, ast
from pathlib import Path
from mathutils import Vector
from math import sin,cos,pi,sqrt
OUT=Path(OUTPUT_DIR);OUT.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
assert scene['project_id']=='rabbit-geometry-20260918'
assert scene['job_id']=='form-v001'
scene['job_id']=JOB['job_id']
scene['previous_job_id']='form-v001'
BASE=Path(WORKSPACE_DIR)/'resume'/'output'/'model'
source=(BASE/'geometry_source.py').read_text()
assert hashlib.sha256(source.encode()).hexdigest()=='4a81f39cf97f8990133e98de9f9c834e259b213a9699b25eab3020b53d554b5f'
COL={c.name:c for c in bpy.data.collections}
SHELL=bpy.data.materials['Clay | shell'];PANEL=bpy.data.materials['Clay | face and panel']
INNER=bpy.data.materials['Clay | inner ear'];DARK=bpy.data.materials['Inspection | internal']
EYE=bpy.data.materials['Inspection | eyes and nose'];CLOTH=bpy.data.materials['Inspection | bow tie']
TOOTH=bpy.data.materials['Clay | teeth'];METAL=bpy.data.materials['Inspection | connectors']
# Extract only geometry helper definitions. The v001 scene-generation statements are NOT re-executed.
names={'place','mesh','apply','ball','cylinder','interp','spow','loft','boolean','hollow','prism','tube','curve','fused','pillow'}
defs=[n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name in names]
assert {n.name for n in defs}==names
exec(compile(ast.Module(body=defs,type_ignores=[]),'<verified-v001-helpers>','exec'),globals())

def remove(name):
    o=bpy.data.objects.get(name)
    if o:bpy.data.objects.remove(o,do_unlink=True)

def soften(o,width=.002,segments=3):
    b=o.modifiers.new('Soft manufactured and fabric edge','BEVEL');b.width=width;b.segments=segments;b.limit_method='ANGLE';b.angle_limit=.45
    apply(o,b)
    for p in o.data.polygons:p.use_smooth=True

def relax(o,count=8,factor=.35):
    m=o.modifiers.new('Sculpt surface relaxation','SMOOTH');m.factor=factor;m.iterations=count;apply(o,m)

# Preserve fingerprint evidence for unmodified parts.
def fingerprint(o):
    if o.type=='MESH': values=[list(v.co) for v in o.data.vertices]
    elif o.type=='CURVE':
        values=[[{'co':list(p.co),'left':list(p.handle_left),'right':list(p.handle_right)} for p in s.bezier_points] if s.type=='BEZIER' else [list(p.co) for p in s.points] for s in o.data.splines]
    else: values=[]
    return hashlib.sha256(json.dumps({'vertices':values,'matrix':[list(r) for r in o.matrix_world]},sort_keys=True).encode()).hexdigest()
keep_names=['Tail','Neck connector','Shoulder axle R','Shoulder axle L','Elbow joint R','Elbow joint L','Wrist joint R','Wrist joint L','Ear spring R','Ear spring L']
kept_before={n:fingerprint(bpy.data.objects[n]) for n in keep_names}

# Replace the projecting orbital spheres and pipe-like jaw with a continuous facial casing.
for name in ['Head continuous casing','Lower jaw U shell','Mouth internal baffle']:remove(name)
hp=[(1.375,.135,-.122,.072),(1.388,.167,-.165,.105),(1.423,.190,-.192,.126),(1.470,.209,-.216,.139),(1.520,.224,-.246,.146),(1.566,.204,-.241,.147),(1.610,.183,-.241,.144),(1.655,.172,-.216,.128),(1.698,.143,-.174,.105),(1.730,.102,-.128,.074),(1.746,.046,-.070,.038),(1.750,.001,-.022,-.020)]
cranium=loft('_revised_cranium',hp,'02_HEAD',SHELL,2.12,128,density=8)
# Subtle sculpted smile rise, rather than separate cylindrical cheek bars.
for v in cranium.data.vertices:
    x,y,z=v.co
    if y<-.11:
        ridge=math.exp(-((abs(x)-.168)/.057)**2-((z-(1.505+.16*(abs(x)-.12)))/.012)**2)
        v.co.y-=.009*ridge
# A widening mandibular sweep joins the side cheek mass and recedes by ~50mm at the front.
ps=[];ry=[];rz=[]
for i in range(129):
    t=pi*i/128;s=sin(t)
    ps.append((.178*cos(t),-.097-.151*s**.8,1.500-.160*s))
    ry.append(.025+.027*cos(t)**2)
    rz.append(.029+.016*cos(t)**2)
jaw=tube('_revised_mandible',ps,ry,rz,'02_HEAD',SHELL,32)
head=fused('Head continuous casing',[cranium,jaw],'02_HEAD',SHELL,.0018)
relax(head,12,.38)
# Mouth void has an ascending floor toward the cheek hinges; it is not a flat through-hole.
mp=[(-.65,.192,1.344,1.481),(-.34,.177,1.348,1.483),(-.28,.170,1.360,1.486),(-.22,.164,1.380,1.496),(-.17,.155,1.412,1.513),(-.13,.141,1.426,1.509),(-.116,.082,1.446,1.493),(-.109,.001,1.466,1.469)]
cutter=loft('_revised_mouth_volume',mp,'09_INTERNAL',DARK,2.5,96,lambda p:(p[0],p[2],p[1]),8)
head.data.materials.append(DARK)
cutter.data.materials.clear();cutter.data.materials.append(SHELL);cutter.data.materials.append(DARK)
for p in cutter.data.polygons:p.material_index=1
boolean(head,cutter,'Deep shaped mouth opening')
for s,label in [(-1,'R'),(1,'L')]:
    boolean(head,ball('_flush_socket',(s*.065,-.265,1.592),(.052,.076,.058),'09_INTERNAL',None,64,40),'Integrated recessed socket '+label)
soften(head,.0018,3)
# Preserve a selectable mandibular region; no rig or animation is claimed.
vg=head.vertex_groups.new(name='Mandible_region_for_later_rigging')
ids=[v.index for v in head.data.vertices if v.co.z<1.455 and v.co.y<-.075]
vg.add(ids,1.0,'REPLACE')
head['construction']='Continuous skull-cheek-mandible casing with true eye and mouth cavities'
head['rigging_note']='Fixed open-mouth modeling pose; mandibular vertices grouped, not a completed articulated rig'
ball('Mouth internal baffle',(0,-.055,1.453),(.142,.066,.060),'09_INTERNAL',DARK,48,28)
# Muzzle and teeth were already correctly counted; reposition and reshape the saved meshes in place.
for label in ['R','L']:
    bpy.data.objects['Muzzle cushion '+label].location.y+=.010
nose=bpy.data.objects['Nose'];nose.location.y+=.025
m=nose.modifiers.new('Rounded nose contour','SUBSURF');m.levels=2;m.render_levels=2;apply(nose,m)
# Compensate subdivision's shrinkage while retaining rounded corners.
center=Vector((0,-.315,1.514))
for v in nose.data.vertices:
    v.co.x*=1.13
    v.co.z=1.514+(v.co.z-1.514)*1.12
bpy.data.objects['Muzzle center split'].location.y+=.010
for o in bpy.data.objects:
    if o.name.startswith('Whisker '):o.location.y+=.010
    if o.name.startswith('Lower tooth '):
        o.location.y+=.044;o.location.z+=.006
        peak=max(v.co.z for v in o.data.vertices)
        for v in o.data.vertices:
            if v.co.z>0:v.co.z=peak*(v.co.z/peak)**.77
    if o.name.startswith('Upper tooth '):o.location.y+=.016;o.location.z+=.008

# Thick, softly bent ears: independently measured X-width and side thickness profiles.
ep=[(1.755,.050,.047),(1.773,.057,.052),(1.870,.067,.056),(1.980,.075,.060),(2.100,.074,.057),(2.150,.068,.053),(2.180,.052,.044),(2.201,.027,.026),(2.208,.001,.001)]
def ecy(z):
    t=max(0.,min(1.,(z-1.755)/.453));return -.022-.056*t**2.7
edata=interp(ep,8)
def eradius(z):
    for a,b in zip(edata,edata[1:]):
        if a[0]<=z<=b[0]:
            t=(z-a[0])/(b[0]-a[0]);return a[2]*(1-t)+b[2]*t
    return edata[0][2]
for s,label in [(-1,'R'),(1,'L')]:
    remove('Ear outer '+label);remove('Ear recessed insert '+label)
    cx=s*.096
    ear=loft('Ear outer '+label,[(z,w,ecy(z)-d,ecy(z)+d) for z,w,d in ep],'03_EARS',SHELL,2.5,96,lambda p,cx=cx:(p[0]+cx,p[1],p[2]),8)
    inner=[(1.766,.025),(1.780,.028),(1.910,.034),(2.044,.036),(2.078,.032),(2.096,.020),(2.104,.001)]
    cut=loft('_round_ear_channel',[(z,w,ecy(z)-.18,ecy(z)+eradius(z)*.35) for z,w in inner],'09_INTERNAL',None,2.15,72,lambda p,cx=cx:(p[0]+cx,p[1],p[2]),7)
    boolean(ear,cut,'Long rounded ear recess')
    soften(ear,.003,4)
    # The insert is IN FRONT of the cavity floor, not hidden behind it as in v001.
    ip=[(z,w*.985,ecy(z)+eradius(z)*.35-.0025,ecy(z)+eradius(z)*.35-.0006) for z,w in inner]
    insert=loft('Ear recessed insert '+label,ip,'03_EARS',INNER,2.15,72,lambda p,cx=cx:(p[0]+cx,p[1],p[2]),7)
    ear['source_side_profile']='x995..1040 at upper/middle, with rounded cap and a delayed forward bend'
checkpoint('face-ear-correction','Continuous recessed face, thick ascending jaw walls and corrected 3D ear profile')

# Locally broaden only the upper shoulder contour; the main torso, belly height and depth stay fixed.
zfactor=[(1.20,1.),(1.24,1.),(1.27,1.07),(1.30,1.12),(1.325,1.22),(1.340,1.35),(1.350,1.45),(1.365,1.)]
factors=interp(zfactor,8)
def factor(z):
    if z<1.20:return 1.
    for a,b in zip(factors,factors[1:]):
        if a[0]<=z<=b[0]:return a[1]+(b[1]-a[1])*(z-a[0])/(b[0]-a[0])
    return 1.
for v in bpy.data.objects['Torso outer casing'].data.vertices:v.co.x*=factor(v.co.z)
# Refit the existing thin belly panel to the changed upper cross sections.
bp=next(ast.literal_eval(n.value) for n in ast.parse(source).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='body_profile' for t in n.targets))
br=interp(bp,12)
for v in bpy.data.objects['Fitted belly panel'].data.vertices:
    x,y,z=v.co
    for a,b in zip(br,br[1:]):
        if a[0]<=z<=b[0]:
            t=(z-a[0])/(b[0]-a[0]);rx,yf,yb=[a[j]*(1-t)+b[j]*t for j in range(1,4)]
            def surface(rad):return (yf+yb)/2-(yb-yf)/2*max(0.,1-(abs(x)/rad)**2.55)**(1/2.55)
            v.co.y+=surface(rx*factor(z))-surface(rx)
            break
# Preserve the actual damage cuts; only remove razor-sharp edge artifacts.
for n in ['Upper arm shell R','Thigh shell R','Thigh shell L']:soften(bpy.data.objects[n],.0013,3)
for label,s in [('R',-1),('L',1)]:
    cx=s*.128
    for prefix in ['Thigh shell ','Shin shell ','Ankle cuff ']:
        o=bpy.data.objects[prefix+label]
        for v in o.data.vertices:
            v.co.x=cx+(v.co.x-cx)*1.035
            if label=='L':v.co.x-=.006
            if prefix=='Shin shell ' and v.co.z>.45:
                u=min(1.,(v.co.z-.45)/.042);v.co.z+=.009*u*u*(3-2*u)
    # Join the existing palm/fingers/thumb into a soft glove-like surface with the grooves retained.
    parts=[bpy.data.objects['Palm '+label]]+[bpy.data.objects['Finger '+label+str(j)] for j in range(1,4)]+[bpy.data.objects['Thumb '+label]]
    for o in parts:
        if o.name.startswith('Finger '):
            for v in o.data.vertices:
                u=max(0.,min(1.,(abs(v.co.x)-.881)/.169));v.co.z-=.010*u*u
    hand=fused('Hand continuous '+label,parts,'05_HANDS',SHELL,.0016);relax(hand,7,.35)
    for j,yy in enumerate([-.056,0,.055]):
        group=hand.vertex_groups.new(name='Finger_'+str(j+1))
        ids=[v.index for v in hand.data.vertices if abs((hand.matrix_world@v.co).x)>.87 and abs((hand.matrix_world@v.co).y-yy)<.032]
        if ids:group.add(ids,1.,'REPLACE')
    hand['digits']='3 fingers plus thumb, contiguous geometry with selectable finger regions'
    # Broaden the heel/base without enlarging the already measured forward/back reach.
    foot=bpy.data.objects['Foot base '+label]
    newcx=-.170 if label=='R' else .162
    oldcx=s*.155
    for v in foot.data.vertices:v.co.x=newcx+(v.co.x-oldcx)*1.028
    for j,dx in enumerate([-.105,0,.105]):
        remove('Toe cap '+label+str(j+1))
        tp=[(-.307,.027,.011,.043),(-.297,.050,.004,.084),(-.278,.056,.003,.112),(-.229,.055,.003,.131),(-.181,.051,.004,.127),(-.145,.034,.020,.103),(-.137,.005,.045,.077)]
        toe=loft('Toe cap '+label+str(j+1),tp,'07_FEET',PANEL,2.7,64,lambda p,cx=newcx,dx=dx:(p[0]+cx+dx,p[2],p[1]),7)
        toe['separate_future_material_zone']=True
# Round bow corners and form broad soft folded wings instead of sharp triangles.
for label in ['R','L']:
    o=bpy.data.objects['Bow wing '+label]
    mod=o.modifiers.new('Soft bow folds','SUBSURF');mod.levels=2;mod.render_levels=2;apply(o,mod)
    s=-1 if label=='R' else 1
    for v in o.data.vertices:
        v.co.x*=1.13
        v.co.z=1.229+(v.co.z-1.229)*1.12
        if v.co.y<-.200:v.co.y-=.005*math.exp(-((v.co.z-(1.229-.20*(abs(v.co.x)-.02)))/.012)**2)

# Update provenance, preserve the original generator, and carry every dependency to current output.
scene['job_id']=JOB['job_id'];scene['previous_job_id']='form-v001'
scene['scope']='Geometry only; no texture maps, no finished rig/UV layout'
for fn in ['reference.webp']:
    shutil.copy2(BASE/fn,OUT/fn)
assert hashlib.sha256((OUT/'reference.webp').read_bytes()).hexdigest()=='c878b9f1522a412c8b1174333ac456939307f3e048aea2b86120ef388d5aeaf0'
(OUT/'base_geometry_source.py').write_text(source)
current=Path(__file__).read_text();(OUT/'geometry_source.py').write_text(current)
t=bpy.data.texts.get('REFINE_form-v002.py') or bpy.data.texts.new('REFINE_form-v002.py');t.clear();t.write(current)
# Explicitly retain vertex-region editability after merging the connected mask and gloves.
scene['editing_note']='Mandible region and three finger regions per hand are vertex groups; no articulated rig has been made.'
bpy.context.view_layer.update()
geos=[o for o in scene.objects if o.type in {'MESH','CURVE'} and not o.hide_render]
points=[o.matrix_world@Vector(c) for o in geos for c in o.bound_box]
lo=[min(v[k] for v in points) for k in range(3)];hi=[max(v[k] for v in points) for k in range(3)]
required={'Head continuous casing':1,'Hand continuous ':2,'Ear outer ':2,'Eye ':2,'Lower tooth ':10,'Upper tooth ':10,'Whisker ':6,'Toe cap ':6,'Button ':2,'Bow wing ':2}
counts={k:sum(o.name.startswith(k) for o in geos) for k in required}
finite=all(math.isfinite(a) for o in geos if o.type=='MESH' for v in o.data.vertices for a in v.co)
closed={}
for name in ['Head continuous casing','Hand continuous R','Hand continuous L']:
    bm=bmesh.new();bm.from_mesh(bpy.data.objects[name].data)
    closed[name]={'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges)};bm.free()
kept={n:fingerprint(bpy.data.objects[n])==h for n,h in kept_before.items()}
checks={'finite_coordinates':finite,'required_parts':counts==required,'closed_revised_shells':all(v['nonmanifold_edges']==0 for v in closed.values()),'preserved_unaffected_parts':all(kept.values()),'height_range':2.17<hi[2]-lo[2]<2.25,'span_range':2.05<hi[0]-lo[0]<2.18,'no_texture_nodes':not any(n.type=='TEX_IMAGE' for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes)}
audit={'job_id':JOB['job_id'],'pass':all(checks.values()),'checks':checks,'bounds_min':lo,'bounds_max':hi,'dimensions_m':[hi[k]-lo[k] for k in range(3)],'required_counts':counts,'closed_shell_checks':closed,'preserved_parts':kept,'objects':len(geos),'vertices':sum(len(o.data.vertices) for o in geos if o.type=='MESH'),'polygons':sum(len(o.data.polygons) for o in geos if o.type=='MESH'),'visual_review':'pending exact new images','limitations':['2D reference reconstruction, not original topology','Geometry only: no finished textures, UVs or rig','Mandible and finger regions are selectable vertex groups']}
(OUT/'geometry_audit.json').write_text(json.dumps(audit,indent=2))
(OUT/'lineage.json').write_text(json.dumps({'parent_job':'form-v001','parent_blend_sha256':'289754f38674d6fa6f430beef20cffdbecee62030eceabc8bc0f2a8a930a7c92','parent_source_sha256':hashlib.sha256(source.encode()).hexdigest(),'preserved_parts':kept,'changes':'Recessed continuous face, shorter thick jaw, thick bent ears, integrated glove surfaces, low broad toes, local shoulder/knee edits, rounded bow/nose'},indent=2))
assert audit['pass'],json.dumps(audit)
bpy.ops.object.select_all(action='DESELECT')
checkpoint('geometry-refined','Revised geometry passes actual mesh checks; visual acceptance remains pending')
