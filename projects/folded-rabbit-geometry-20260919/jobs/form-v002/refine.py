"""Geometry revision driven by the actual v001 review, not a fresh project.
Open the same-project saved scene. Keep unchanged torso/tail/internal parts;
replace only reviewed components and retain all construction dependencies.
"""
import ast,bisect,bpy,bmesh,math,json,hashlib,shutil,struct
from pathlib import Path
from mathutils import Vector,Matrix
from math import sin,cos,pi,sqrt
OUT=Path(OUTPUT_DIR);OUT.mkdir(parents=True,exist_ok=True)
PREV=Path(WORKSPACE_DIR)/'resume'/'output'/'model';scene=bpy.context.scene
assert scene['project_id']==JOB['project_id'] and scene['job_id']=='form-v001'
assert hashlib.sha256((PREV/'model.blend').read_bytes()).hexdigest()=='76f7e0926c7ebdcc45b34e0f608ebe5b7de9c77d77999b859b0948b85dd6e3ef'
COL={c.name:c for c in bpy.data.collections}
SHELL=bpy.data.materials['Clay | shell'];PANEL=bpy.data.materials['Clay | face and panel'];INNER=bpy.data.materials['Clay | inner ear']
DARK=bpy.data.materials['Inspection | internal'];EYE=bpy.data.materials['Inspection | eyes and nose'];CLOTH=bpy.data.materials['Inspection | bow tie'];TOOTH=bpy.data.materials['Clay | teeth'];METAL=bpy.data.materials['Inspection | connectors']
base=(PREV/'base_geometry_source.py').read_text();old=(PREV/'parent_form-v003_source.py').read_text();v1=(PREV/'geometry_source.py').read_text()
assert hashlib.sha256(v1.encode()).hexdigest()=='5d1276e96ed77008f7d02b409644c6bf5656991ecfbcbce0d5f0f44e2cfa63f0'
for text,names in [(base,{'place','mesh','apply','ball','cylinder','spow','loft','boolean','tube','curve','fused'}),(old,{'spline','interp'}),(v1,{'fit','roundbox','orient','beam','smooth'})]:
    nodes=[n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes}==names
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<verified saved helper definitions>','exec'),globals())
def fingerprint(o):
    h=hashlib.sha256();h.update(str(o.type).encode())
    for row in o.matrix_world:
        for x in row:h.update(struct.pack('<d',float(x)))
    if o.type=='MESH':
        for v in o.data.vertices:
            for x in v.co:h.update(struct.pack('<d',float(x)))
        for p in o.data.polygons:
            for i in p.vertices:h.update(struct.pack('<I',i))
    return h.hexdigest()
before={o.name:fingerprint(o) for o in scene.objects if o.type in {'MESH','CURVE'}}
changed=set()
def delete(name):
    if name in bpy.data.objects:changed.add(name);bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
def mark(name):changed.add(name);return bpy.data.objects[name]
def casing(name,center,rx,ry,height,col,mat=SHELL,corner=.022,exponent=2.35,bulge=.035,taper=0,n=96):
    # Convex cross sections and smoothly rounded axial ends, not flat-front cubes.
    c=min(corner,height*.24,rx*.7,ry*.7);lo=-height/2;hi=height/2;sections=[]
    for i in range(17):
        a=(pi/2)*i/16;sections.append((lo+c*(1-cos(a)),-c+c*sin(a)))
    for i in range(1,49):sections.append((lo+c+(height-2*c)*i/49,0))
    for i in range(17):
        a=(pi/2)*i/16;sections.append((hi-c+c*sin(a),-c+c*cos(a)))
    v=[];f=[]
    for z,d in sections:
        t=(z-lo)/height;factor=1+bulge*sin(pi*t)**2+taper*(t-.5)
        a=(rx+d)*factor;b=(ry+d)*(1+bulge*.6*sin(pi*t)**2)
        for j in range(n):
            angle=2*pi*j/n;v.append((center[0]+a*spow(cos(angle),2/exponent),center[1]+b*spow(sin(angle),2/exponent),center[2]+z))
    for i in range(len(sections)-1):
        for j in range(n):a=i*n+j;b=i*n+(j+1)%n;f.append((a,b,b+n,a+n))
    f.extend([tuple(reversed(range(n))),tuple((len(sections)-1)*n+j for j in range(n))])
    o=mesh(name,v,f,col,mat);o.data.polygons[-1].use_smooth=False;o.data.polygons[-2].use_smooth=False
    return o

def closed_outline(points,per=10):
    out=[];N=len(points)
    for i in range(N):
        p0,p1,p2,p3=[points[k%N] for k in [i-1,i,i+1,i+2]]
        for j in range(per):
            t=j/per
            out.append(tuple(.5*((2*p1[k])+(-p0[k]+p2[k])*t+(2*p0[k]-5*p1[k]+4*p2[k]-p3[k])*t*t+(-p0[k]+3*p1[k]-3*p2[k]+p3[k])*t*t*t) for k in range(2)))
    return out

def cheek(s,label):
    # Side-view pear outline with a shallow lenticular outward surface.
    edge=closed_outline([(-.162,1.740),(-.150,1.774),(-.116,1.794),(-.067,1.797),(-.018,1.774),(.002,1.741),(-.012,1.698),(-.045,1.657),(-.096,1.641),(-.144,1.647),(-.161,1.682)],8)
    cy=-.079;cz=1.722;n=len(edge);v=[];f=[]
    for i in range(49):
        lat=-pi/2+pi*(i+.25)/49.5;r=cos(lat);xx=s*(.191+(.054 if lat>=0 else .037)*sin(lat))
        for y,z in edge:v.append((xx,cy+(y-cy)*r,cz+(z-cz)*r))
    for i in range(48):
        for j in range(n):a=i*n+j;b=i*n+(j+1)%n;f.append((a,b,b+n,a+n))
    f.extend([tuple(reversed(range(n))),tuple(48*n+j for j in range(n))])
    o=mesh('Cheek pad '+label,v,f,'02_HEAD',PANEL);smooth(o,.0017,5);return o

# Inherit the original transform/geometry of parts unaffected by this review.
scene['job_id']=JOB['job_id'];scene['geometry_revision']='form-v002: reviewed curves, recessed eyes and continuous muzzle'
for name in ['Head casing','U shaped lower jaw','Mouth internal baffle']:
    delete(name)
for s,label in [(-1,'R'),(1,'L')]:
    for prefix in ['Cheek pad ','Muzzle cushion ','Socket lining ','Orbital rim ','Ear outer ','Ear recessed insert ','Ear folded cap ','Ear cap inset ','Palm and thumb ','Upper arm casing ','Forearm casing ','Shin shell ']:delete(prefix+label)
    for j in range(1,4):delete('Finger '+label+str(j));delete('Toe cap '+label+str(j))
for row in ['Lower','Upper']:
    for i in range(1,11):delete('%s tooth %02d'%(row,i))
for name in ['Pelvis and thigh casing','Bow wing R','Bow wing L','Bow knot']:delete(name)

# Continuous forehead-to-nose bridge. Mouth cutter no longer removes the bridge.
hp=[(1.601,.001,.005,.007),(1.601,.139,-.134,.115),(1.621,.183,-.260,.150),(1.660,.200,-.299,.158),(1.707,.207,-.281,.158),(1.760,.210,-.255,.155),(1.816,.204,-.251,.151),(1.876,.193,-.229,.140),(1.936,.173,-.195,.116),(1.985,.103,-.120,.081),(2.003,.035,-.057,.038),(2.003,.001,-.009,-.007)]
head=loft('Head casing',hp,'02_HEAD',SHELL,2.25,144,density=18)
boolean(head,ball('_mouth',(0,-.256,1.554),(.158,.183,.079),'09_INTERNAL',None,96,64),'Opening below muzzle, bridge retained')
for s,label in [(-1,'R'),(1,'L')]:
    boolean(head,ball('_orbit',(s*.069,-.249,1.824),(.047,.078,.058),'09_INTERNAL',None,96,64),'Deep rounded eye socket '+label)
smooth(head,.0016,12)
# A subtle continuous lip belongs to the shell itself, not a floating flat torus.
for v in head.data.vertices:
    x,y,z=v.co
    if y<-.185:
        for s in [-1,1]:
            rr=sqrt(((x-s*.069)/.047)**2+((z-1.824)/.058)**2)
            if .97<rr<1.27:v.co.y-=.0025*math.exp(-((rr-1.10)/.095)**2)
head.data.update();head.data.materials.append(PANEL)
for p in head.data.polygons:
    c=p.center;brow=1.861+.057*math.exp(-((abs(c.x)-.069)/.068)**2)
    if c.y<-.125 and c.z<brow:p.material_index=1
for s,label in [(-1,'R'),(1,'L')]:
    cheek(s,label)
    mp=[(1.601,.002,-.252,-.244),(1.603,.040,-.293,-.216),(1.612,.056,-.321,-.204),(1.647,.064,-.325,-.201),(1.693,.065,-.305,-.205),(1.729,.047,-.274,-.209),(1.756,.017,-.240,-.223),(1.758,.001,-.23,-.229)]
    loft('Muzzle cushion '+label,mp,'02_HEAD',PANEL,2.45,96,lambda p,s=s:(p[0]+s*.059,p[1],p[2]),18)
    o=mark('Eye '+label);fit(o,(s*.069,-.209,1.822),(.073,.066,.080))
    ball('Socket lining '+label,(s*.069,-.185,1.824),(.045,.041,.054),'09_INTERNAL',DARK,80,56)
fit(mark('Nose'),(0,-.326,1.674),(.101,.031,.047))
half=[(.151,-.066,1.672,.035),(.171,-.070,1.632,.041),(.169,-.101,1.585,.042),(.136,-.177,1.535,.037),(.076,-.250,1.513,.032),(0,-.271,1.511,.030)]
path=spline(half+[(-x,y,z,r) for x,y,z,r in reversed(half[:-1])],181)
jaw=tube('U shaped lower jaw',[p[:3] for p in path],[p[3] for p in path],[p[3] for p in path],'02_HEAD',PANEL,48);smooth(jaw,.0016,6)
ball('Mouth internal baffle',(0,-.169,1.598),(.142,.044,.067),'09_INTERNAL',DARK,80,48)
angles=[-1.55,-1.18,-.82,-.49,-.16,.16,.49,.82,1.18,1.55]
for i,t in enumerate(angles,1):
    x=.111*sin(t);y=-.175-.093*cos(t);z=1.551+.028*sin(t)**2
    o=casing('Lower tooth %02d'%i,(x,y,z),.017,.016,.036,'02_HEAD',TOOTH,.010,2.8,.01,0,64)
    o.rotation_euler[2]=-t*.35
    # Upper teeth are partially buried in the continuous upper lip, as in the reference.
    o=casing('Upper tooth %02d'%i,(x,y+.010,1.612+.011*sin(t)**2),.015,.013,.022,'02_HEAD',TOOTH,.008,2.8,.01,0,64)
checkpoint('face-refinement','Floating eye rings removed; continuous nasal bridge, shaped cheek plates and supported dental arches saved')

# Curved upper-arm shells overlap the shoulder more deeply; no flat square fronts.
for s,label in [(-1,'R'),(1,'L')]:
    a=(s*.283,-.004,1.489);b=(s*.347,-.004,1.228);L=(Vector(b)-Vector(a)).length
    o=casing('Upper arm casing '+label,(0,0,0),.104,.123,L,'04_ARMS',SHELL,.025,2.35,.045,-.09);orient(o,a,b)
    a=(s*.359,-.004,1.219);b=(s*.423,-.014,.974);L=(Vector(b)-Vector(a)).length
    o=casing('Forearm casing '+label,(0,0,0),.094,.105,L,'04_ARMS',SHELL,.019,2.55,.035,-.015);orient(o,a,b)
    palm=casing('_palm '+label,(s*.449,-.003,.881),.063,.087,.166,'05_HANDS',SHELL,.027,2.25,.02,-.04)
    pts=spline([(s*.431,-.048,.927,.032),(s*.410,-.072,.900,.036),(s*.386,-.084,.863,.031),(s*.367,-.085,.823,.027),(s*.366,-.084,.807,.001)],60)
    thumb=tube('_thumb '+label,[p[:3] for p in pts],[p[3] for p in pts],[p[3] for p in pts],'05_HANDS',SHELL,40)
    palm=fused('Palm and thumb '+label,[palm,thumb],'05_HANDS',SHELL,.0016);smooth(palm,iters=8)
    for j,y in enumerate([-.060,0,.060],1):
        pts=spline([(s*.463,y,.862,.023),(s*.478,y,.831,.028),(s*.483,y,.795,.029),(s*.477,y,.767,.028),(s*.458,y,.740,.026),(s*.434,y,.724,.025)],80)
        stem=tube('_digit', [p[:3] for p in pts],[p[3] for p in pts],[p[3] for p in pts],'05_HANDS',SHELL,36)
        tip=ball('_round digit end',(s*.434,y,.724),(.025,.025,.025),'05_HANDS',SHELL,56,40)
        o=fused('Finger '+label+str(j),[stem,tip],'05_HANDS',SHELL,.0015);smooth(o,iters=4)
        o['root']='Inside the palm; no exposed flat root cap'
# Broad, nearly flat knee ends with soft perimeter fillets, and a continuous pelvis.
parts=[roundbox('_hip bridge',(0,.010,.914),(.474,.281,.119),.028,'06_LEGS')]
for s,label in [(-1,'R'),(1,'L')]:
    parts.append(casing('_thigh '+label,(s*.145,.012,(.608+.972)/2),.123,.146,.972-.608,'06_LEGS',SHELL,.018,2.65,.028,.01))
    casing('Shin shell '+label,(s*.157,.007,(.246+.602)/2),.123,.132,.602-.246,'06_LEGS',SHELL,.017,2.8,.035,-.015)
hip=fused('Pelvis and thigh casing',parts,'06_LEGS',SHELL,.0022)
# Remove the primitive-union ridge without changing the crotch or lower thigh shape.
for v in hip.data.vertices:
    p=hip.matrix_world@v.co;x,y,z=p
    if z>.867 and abs(y-.010)>.02:
        u=max(0,min(1,(z-.867)/.046));u=u*u*(3-2*u)
        ry=.149;rx=.273;ideal=.010+math.copysign(ry*max(0,1-(abs(x)/rx)**2.65)**(1/2.65),y-.010)
        p.y=y+(ideal-y)*u
        v.co=hip.matrix_world.inverted()@p
smooth(hip,iters=6)
# Rounded-square toe domes instead of tall egg-shaped cones.
for s,label in [(-1,'R'),(1,'L')]:
    for j,(cx,cy,h) in enumerate([(.110,-.248,.157),(.235,-.248,.163),(.357,-.217,.147)],1):
        n=96;nr=56;v=[];f=[];e=.56
        for i in range(nr):
            a=(pi/2)*i/nr;r=cos(a)**e;z=.005+h*sin(a)**e
            for k in range(n):
                t=2*pi*k/n;v.append((s*cx+.074*r*spow(cos(t),.75),cy+.116*r*spow(sin(t),.75),z))
        for i in range(nr-1):
            for k in range(n):a=i*n+k;b=i*n+(k+1)%n;f.append((a,b,b+n,a+n))
        v.append((s*cx,cy,.005+h));pole=len(v)-1
        for k in range(n):f.append(((nr-1)*n+k,(nr-1)*n+(k+1)%n,pole))
        f.append(tuple(reversed(range(n))));mesh('Toe cap '+label+str(j),v,f,'07_FEET',PANEL)
checkpoint('curved-limb-shells','Convex arm shells, continuous hip, nearly flush knees, palm-rooted fingers and fuller toes saved')

for s,label in [(-1,'R'),(1,'L')]:
    a=(s*.114,-.104,1.983);b=(s*.190,-.172,2.142);L=(Vector(b)-Vector(a)).length
    ear=casing('Ear outer '+label,(0,0,0),.069,.053,L+.014,'03_EARS',SHELL,.018,2.65,.025)
    cutter=roundbox('_ear groove',(0,-.049,-.008),(.067,.067,L+.011),.018,'09_INTERNAL',None)
    boolean(ear,cutter,'Deep rounded open-bottom ear groove')
    insert=roundbox('Ear recessed insert '+label,(0,-.016,-.008),(.056,.004,L-.008),.0018,'03_EARS',INNER)
    rot,center=orient(ear,a,b);insert.matrix_world=Matrix.Translation(center)@rot@insert.matrix_world
    cap_a=(s*.174,-.169,2.145);cap_b=(s*.276,-.356,2.091);L=(Vector(cap_b)-Vector(cap_a)).length
    cap=casing('Ear folded cap '+label,(0,0,0),.063,.050,L,'03_EARS',SHELL,.027,2.65,.025)
    cap.data.materials.append(PANEL)
    for p in cap.data.polygons:
        if p.center.y<-.022 and p.center.z>-.075:p.material_index=1
    orient(cap,cap_a,cap_b)
    # Normalize just the changed ears' top to the reference's metric 2.20m target.
    changed.add('Ear hinge '+label)
    bpy.data.objects['Ear hinge '+label].location=a
bpy.context.view_layer.update()
ear_objects=[o for o in bpy.data.collections['03_EARS'].objects]
top=max((o.matrix_world@Vector(c)).z for o in ear_objects for c in o.bound_box)
factor=(2.20-1.983)/(top-1.983)
for o in ear_objects:
    inv=o.matrix_world.inverted()
    for v in o.data.vertices:
        p=o.matrix_world@v.co;p.z=1.983+(p.z-1.983)*factor;v.co=inv@p
    o.data.update()
# Curved cloth volumes seated on the chest, with broad pleats rather than flat triangles.
bp=[(.952,.001,-.03,.03),(.952,.216,-.210,.166),(.962,.258,-.240,.195),(1.012,.270,-.251,.205),(1.130,.265,-.251,.214),(1.266,.251,-.238,.208),(1.405,.232,-.206,.186),(1.510,.205,-.157,.150),(1.565,.157,-.100,.095),(1.585,.080,-.052,.056),(1.590,.001,0,.002)]
rows=interp(bp,30)
def front_at(z):
    for a,b in zip(rows,rows[1:]):
        if a[0]<=z<=b[0]:
            t=(z-a[0])/max(1e-9,b[0]-a[0]);return a[2]*(1-t)+b[2]*t
    return -.20
for s,label in [(-1,'R'),(1,'L')]:
    edge=closed_outline([(.026,1.461),(.086,1.486),(.166,1.511),(.159,1.459),(.145,1.357),(.086,1.392),(.024,1.418)],12)
    cx=.084;cz=1.439;n=len(edge);v=[];f=[]
    for i in range(49):
        lat=-pi/2+pi*(i+.25)/49.5;r=cos(lat)
        for x,z in edge:
            xx=cx+(x-cx)*r;zz=cz+(z-cz)*r
            relief=(.021 if lat>=0 else .006)*sin(lat)
            if lat>=0:relief+=.012*sin(4*math.atan2(zz-cz,xx-cx))*r*(1-r)*sin(lat)
            yy=front_at(zz)-.009-relief;v.append((s*xx,yy,zz))
    for i in range(48):
        for j in range(n):a=i*n+j;b=i*n+(j+1)%n;f.append((a,b,b+n,a+n))
    f.extend([tuple(reversed(range(n))),tuple(48*n+j for j in range(n))])
    mesh('Bow wing '+label,v,f,'08_DETAILS',CLOTH)
roundbox('Bow knot',(0,front_at(1.437)-.024,1.437),(.058,.043,.059),.015,'08_DETAILS',CLOTH)

# Persist exact sources and reference resources independently of excluded resume/.
for p in PREV.iterdir():
    if p.suffix in {'.py','.webp'}:
        name='form-v001_source.py' if p.name=='geometry_source.py' else p.name
        shutil.copy2(p,OUT/name)
shutil.copy2(Path(WORKSPACE_DIR)/'resume'/'output'/'import'/'import_evidence.json',OUT/'accepted_parent_import.json')
shutil.copy2(Path(WORKSPACE_DIR)/'resume'/'output'/'import'/'parent_release_manifest.json',OUT/'parent_release_manifest.json')
current=Path(__file__).read_text();(OUT/'geometry_source.py').write_text(current)
block=bpy.data.texts.get('BUILD_folded_form-v002.py') or bpy.data.texts.new('BUILD_folded_form-v002.py');block.clear();block.write(current)
bpy.context.view_layer.update()
# Parts deliberately not touched must match the exact saved geometry and transform.
preserved={name:h for name,h in before.items() if name not in changed}
for name,h in preserved.items():assert name in bpy.data.objects and fingerprint(bpy.data.objects[name])==h,name+' changed unexpectedly'
geos=[o for o in scene.objects if o.type in {'MESH','CURVE'} and not o.hide_render]
pts=[o.matrix_world@Vector(c) for o in geos for c in o.bound_box];lo=[min(p[k] for p in pts) for k in range(3)];hi=[max(p[k] for p in pts) for k in range(3)]
required={'Head casing':1,'Cheek pad ':2,'Muzzle cushion ':2,'Eye ':2,'Nose':1,'U shaped lower jaw':1,'Ear outer ':2,'Ear folded cap ':2,'Ear recessed insert ':2,'Lower tooth ':10,'Upper tooth ':10,'Whisker ':6,'Toe cap ':6,'Finger ':6,'Palm and thumb ':2,'Button ':2,'Bow wing ':2,'Shin shell ':2}
counts={k:sum(o.name.startswith(k) for o in geos) for k in required};closed={}
for name in ['Head casing','U shaped lower jaw','Ear outer R','Ear outer L','Pelvis and thigh casing','Palm and thumb R','Palm and thumb L']:
    bm=bmesh.new();bm.from_mesh(bpy.data.objects[name].data);closed[name]={'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'boundary_edges':sum(e.is_boundary for e in bm.edges)};bm.free()
checks={'required_parts':counts==required,'finite_coordinates':all(math.isfinite(a) for o in geos if o.type=='MESH' for v in o.data.vertices for a in v.co),'closed_revised_shells':all(v['nonmanifold_edges']==0 for v in closed.values()),'height_range':2.15<hi[2]-lo[2]<2.23,'no_texture_nodes':not any(n.type=='TEX_IMAGE' for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes),'unchanged_parts_preserved':True,'floating_ear_plaques_removed':not any(o.name.startswith('Ear cap inset') for o in geos),'floating_eye_rings_removed':not any(o.name.startswith('Orbital rim') for o in geos)}
audit={'job_id':JOB['job_id'],'pass':all(checks.values()),'checks':checks,'bounds_min':lo,'bounds_max':hi,'dimensions_m':[hi[k]-lo[k] for k in range(3)],'required_counts':counts,'closed_shell_checks':closed,'objects':len(geos),'vertices':sum(len(o.data.vertices) for o in geos if o.type=='MESH'),'polygons':sum(len(o.data.polygons) for o in geos if o.type=='MESH'),'unchanged_object_fingerprints':preserved,'visual_review':'pending exact v002 images'}
(OUT/'geometry_audit.json').write_text(json.dumps(audit,indent=2));assert audit['pass'],json.dumps(audit)
(OUT/'lineage.json').write_text(json.dumps({'project_id':JOB['project_id'],'from_job':'form-v001','to_job':JOB['job_id'],'source_blend_sha256':'76f7e0926c7ebdcc45b34e0f608ebe5b7de9c77d77999b859b0948b85dd6e3ef','preserved_objects':sorted(preserved),'modified_or_replaced_objects':sorted(changed),'scope':'Geometry only; import already accepted and not rerun'},indent=2))
bpy.ops.object.select_all(action='DESELECT')
checkpoint('reviewed-geometry-refinement','Reviewed component changes saved, unchanged parts fingerprint-verified; actual v002 visual review remains pending')
