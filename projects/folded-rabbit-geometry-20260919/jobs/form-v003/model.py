"""Targeted form-v003 refinement of the verified same-project v002 .blend.
Geometry only. Reference PNG hashes are unchanged. No image-generated geometry.
"""
import ast,bisect,bpy,bmesh,math,json,hashlib,shutil,struct
from pathlib import Path
from mathutils import Vector,Matrix
from math import sin,cos,pi,sqrt
OUT=Path(OUTPUT_DIR);OUT.mkdir(parents=True,exist_ok=True)
PREV=Path(WORKSPACE_DIR)/'resume'/'output'/'model';scene=bpy.context.scene
assert scene['project_id']==JOB['project_id'] and scene['job_id']=='form-v002'
PARENT_SHA='adbb099ed8f76fc69a6c309064ad82b04c472c6e8d8457a3b4be49b73374d3f3'
assert hashlib.sha256((PREV/'model.blend').read_bytes()).hexdigest()==PARENT_SHA
COL={c.name:c for c in bpy.data.collections}
SHELL=bpy.data.materials['Clay | shell'];PANEL=bpy.data.materials['Clay | face and panel'];INNER=bpy.data.materials['Clay | inner ear']
DARK=bpy.data.materials['Inspection | internal'];EYE=bpy.data.materials['Inspection | eyes and nose'];CLOTH=bpy.data.materials['Inspection | bow tie'];TOOTH=bpy.data.materials['Clay | teeth'];METAL=bpy.data.materials['Inspection | connectors']
# Only function definitions are inherited; accepted construction/import is not rerun.
sources=[('base_geometry_source.py','4a81f39cf97f8990133e98de9f9c834e259b213a9699b25eab3020b53d554b5f',{'place','mesh','apply','ball','cylinder','spow','loft','boolean','tube','curve','fused'}),('parent_form-v003_source.py','ebcc13bb2adc28e9f331f2279137c81ba3d0fbb845e93e38735a65771d85765c',{'spline','interp'}),('form-v001_source.py','5d1276e96ed77008f7d02b409644c6bf5656991ecfbcbce0d5f0f44e2cfa63f0',{'fit','roundbox','orient','smooth'}),('geometry_source.py','023d673f457493a9e6385a900694ffdff02f09aabe4cfc983396335d58390a46',{'fingerprint','casing','closed_outline','cheek'})]
for filename,digest,names in sources:
    text=(PREV/filename).read_text();assert hashlib.sha256(text.encode()).hexdigest()==digest,filename
    nodes=[n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes}==names
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<verified '+filename+'>','exec'),globals())
before={o.name:fingerprint(o) for o in scene.objects if o.type in {'MESH','CURVE'}};changed=set()
def delete(name):
    if name in bpy.data.objects:changed.add(name);bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
def mark(name):changed.add(name);return bpy.data.objects[name]
def deform(o,fn):
    inv=o.matrix_world.inverted()
    for vertex in o.data.vertices:vertex.co=inv@Vector(fn(o.matrix_world@vertex.co))
    o.data.update()
def smoothstep(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def profiled(name,rows,col,mat=SHELL,exponent=2.5,n=96,sub=8):
    """Monotone Hermite sections, so measured knots are hit without spline shrinkage.
    Rows: z, half-width, front, back, x-centre. Closed end disks.
    """
    count=len(rows);xs=[r[0] for r in rows];assert all(a<b for a,b in zip(xs,xs[1:]))
    slopes=[]
    for k in range(1,5):
        sec=[(rows[i+1][k]-rows[i][k])/(xs[i+1]-xs[i]) for i in range(count-1)];m=[sec[0]]
        for i in range(1,count-1):
            if sec[i-1]*sec[i]<=0:m.append(0.)
            else:
                h0=xs[i]-xs[i-1];h1=xs[i+1]-xs[i];w1=2*h1+h0;w2=h1+2*h0
                m.append((w1+w2)/(w1/sec[i-1]+w2/sec[i]))
        m.append(sec[-1]);slopes.append(m)
    rings=[]
    for i in range(count-1):
        h=xs[i+1]-xs[i]
        for j in range(sub):
            t=j/sub;row=[xs[i]+h*t]
            for k in range(1,5):row.append((2*t**3-3*t*t+1)*rows[i][k]+(t**3-2*t*t+t)*h*slopes[k-1][i]+(-2*t**3+3*t*t)*rows[i+1][k]+(t**3-t*t)*h*slopes[k-1][i+1])
            rings.append(row)
    rings.append(rows[-1]);v=[];f=[]
    for z,rx,yf,yb,cx in rings:
        assert rx>0 and yf<yb,(name,z,rx,yf,yb)
        for j in range(n):
            t=2*pi*j/n;v.append((cx+rx*spow(cos(t),2/exponent),(yf+yb)/2+(yb-yf)/2*spow(sin(t),2/exponent),z))
    for i in range(len(rings)-1):
        for j in range(n):a=i*n+j;b=i*n+(j+1)%n;f.append((a,b,b+n,a+n))
    f.extend([tuple(reversed(range(n))),tuple((len(rings)-1)*n+j for j in range(n))])
    return mesh(name,v,f,col,mat)
scene['job_id']=JOB['job_id'];scene['geometry_revision']='form-v003 / continuous muzzle and shaped padded shells'
for name in ['Head casing','Mouth internal baffle','Pelvis and thigh casing']:delete(name)
for s,label in [(-1,'R'),(1,'L')]:
    for p in ['Muzzle cushion ','Cheek pad ','Socket lining ','Shoulder cap ','Upper arm casing ','Forearm casing ','Shin shell ','Ear outer ','Ear recessed insert ','Ear folded cap ']:delete(p+label)
    for j in range(1,4):delete('Toe cap '+label+str(j));delete('Finger '+label+str(j))
# Continuous nasal bridge: union real lobe volumes before cutting the mouth/eyes.
hp=[(1.597,.001,-.01,.01),(1.600,.137,-.258,.115),(1.624,.187,-.282,.151),(1.672,.213,-.295,.162),(1.722,.221,-.276,.164),(1.777,.216,-.249,.158),(1.834,.205,-.238,.148),(1.900,.189,-.215,.132),(1.954,.160,-.177,.112),(1.992,.085,-.096,.068),(2.005,.001,-.008,.008)]
parts=[loft('_cranial shell',hp,'02_HEAD',SHELL,2.30,128,density=20)]
for s,label in [(-1,'R'),(1,'L')]:
    mp=[(1.602,.002,-.265,-.245),(1.606,.043,-.311,-.216),(1.623,.061,-.331,-.205),(1.658,.067,-.329,-.202),(1.704,.061,-.301,-.204),(1.745,.032,-.258,-.218),(1.756,.001,-.233,-.231)]
    parts.append(loft('_continuous muzzle '+label,mp,'02_HEAD',PANEL,2.5,96,lambda p,s=s:(p[0]+s*.057,p[1],p[2]),18))
head=fused('Head casing',parts,'02_HEAD',SHELL,.00135)
boolean(head,ball('_mouth cutter',(0,-.251,1.550),(.155,.181,.079),'09_INTERNAL',None,96,64),'Open mouth below retained snout')
# Very narrow central cleft remains a geometric feature, not painted shading.
boolean(head,roundbox('_muzzle cleft',(0,-.336,1.626),(.003,.047,.067),.0013,'09_INTERNAL',None),'Muzzle centre cleft below nose')
for s,label in [(-1,'R'),(1,'L')]:
    boolean(head,ball('_orbit',(s*.069,-.252,1.824),(.046,.065,.0515),'09_INTERNAL',None,96,64),'Quiet recessed socket '+label)
smooth(head,.0012,10)
head.data.materials.append(PANEL)
for p in head.data.polygons:
    c=p.center;brow=1.861+.054*math.exp(-((abs(c.x)-.069)/.068)**2)
    if c.y<-.123 and c.z<brow:p.material_index=1
for s,label in [(-1,'R'),(1,'L')]:
    group=head.vertex_groups.new(name='Muzzle cushion '+label)
    ids=[v.index for v in head.data.vertices if .004<s*v.co.x<.128 and v.co.y<-.259 and 1.601<v.co.z<1.739]
    assert len(ids)>100;group.add(ids,1.0,'REPLACE')
    o=cheek(s,label)
    # The reference cheek is a broad, rounded pad, not a small side ball.
    deform(o,lambda p,s=s:(p.x+s*.005,p.y-.006,p.z+(p.z-1.721)*.07))
    fit(mark('Eye '+label),(s*.069,-.224,1.824),(.081,.077,.089))
    ball('Socket lining '+label,(s*.069,-.199,1.824),(.044,.043,.050),'09_INTERNAL',DARK,80,56)
head['muzzle_construction']='Two sculptable vertex groups in the continuous head; no dummy muzzle objects'
# Keep the reviewed U jaw, but soften its slight sampling striations locally.
smooth(mark('U shaped lower jaw'),None,4)
ball('Mouth internal baffle',(0,-.173,1.598),(.144,.048,.067),'09_INTERNAL',DARK,80,48)
for row in ['Lower','Upper']:
    for i in range(1,11):
        o=mark('%s tooth %02d'%(row,i));pts=[o.matrix_world@v.co for v in o.data.vertices];cz=(min(p.z for p in pts)+max(p.z for p in pts))/2
        deform(o,lambda p,cz=cz,row=row:(p.x,p.y,p.z if row=='Upper' else cz+(p.z-cz)*.92-.002))
checkpoint('continuous-face','Continuous muzzle lobes, fuller recessed eyes and larger cheek pads saved; no texture work')
# Sloping shoulder covers and changing arm sections, instead of exposed spheres/cylinders.
for s,label in [(-1,'R'),(1,'L')]:
    rows=[(1.387,.002,-.01,.012,s*.309),(1.401,.059,-.080,.087,s*.310),(1.432,.081,-.115,.123,s*.301),(1.476,.095,-.128,.133,s*.278),(1.521,.088,-.115,.120,s*.247),(1.560,.048,-.073,.080,s*.211),(1.575,.001,-.008,.009,s*.190)]
    profiled('Shoulder cap '+label,rows,'04_ARMS',SHELL,2.25)
    a=Vector((s*.349,-.003,1.229));b=Vector((s*.291,-.006,1.494));L=(b-a).length
    raw=[(0,.002,.006),(.003,.072,.085),(.014,.094,.111),(.055,.107,.123),(.125,.108,.132),(.193,.096,.129),(.240,.079,.114),(L-.008,.052,.080),(L,.001,.006)]
    rows=[(z-L/2,rx,-ry,ry,0) for z,rx,ry in raw]
    o=profiled('Upper arm casing '+label,rows,'04_ARMS',SHELL,2.25);orient(o,a,b)
    a=Vector((s*.424,-.016,.976));b=Vector((s*.360,-.004,1.218));L=(b-a).length
    raw=[(0,.001,.004),(.003,.059,.068),(.012,.084,.091),(.058,.094,.105),(.133,.095,.109),(.207,.093,.103),(L-.012,.084,.091),(L-.003,.060,.070),(L,.001,.004)]
    o=profiled('Forearm casing '+label,[(z-L/2,rx,-ry,ry,0) for z,rx,ry in raw],'04_ARMS',SHELL,2.55);orient(o,a,b)
# Round thighs with a deeper arched crotch; the union is relaxed before inspection.
parts=[roundbox('_hip bridge',(0,.012,.911),(.467,.286,.139),.056,'06_LEGS')]
for s,label in [(-1,'R'),(1,'L')]:
    rows=[(.610,.001,-.006,.010,s*.146),(.612,.084,-.095,.112,s*.146),(.625,.112,-.131,.148,s*.146),(.684,.125,-.147,.161,s*.147),(.818,.129,-.147,.163,s*.146),(.921,.127,-.133,.155,s*.141),(.966,.105,-.103,.128,s*.137),(.980,.001,.006,.014,s*.137)]
    parts.append(profiled('_thigh '+label,rows,'06_LEGS',SHELL,2.55))
    rows=[(.245,.001,-.004,.010,s*.157),(.247,.083,-.086,.104,s*.157),(.260,.115,-.119,.139,s*.157),(.328,.126,-.135,.151,s*.157),(.459,.125,-.132,.150,s*.156),(.554,.120,-.120,.138,s*.153),(.590,.109,-.103,.122,s*.151),(.602,.076,-.078,.095,s*.150),(.605,.001,.004,.012,s*.150)]
    profiled('Shin shell '+label,rows,'06_LEGS',SHELL,2.65)
hip=fused('Pelvis and thigh casing',parts,'06_LEGS',SHELL,.0018);smooth(hip,None,32)
# Fair the combined upper hip, avoiding the former primitive-union horizontal ridge.
for v in hip.data.vertices:
    p=hip.matrix_world@v.co;x,y,z=p
    if z>.858 and abs(y-.012)>.025:
        w=smoothstep(.858,.919,z);ideal=.012+math.copysign(.153*max(0,1-(abs(x)/.271)**2.6)**(1/2.6),y-.012)
        p.y=y+(ideal-y)*w;v.co=hip.matrix_world.inverted()@p
smooth(hip,None,12)
# Fingers have two closed articulated segments, joined as one editable digit object.
for s,label in [(-1,'R'),(1,'L')]:
    palm=mark('Palm and thumb '+label)
    deform(palm,lambda p,s=s:(p.x+s*.004*sin(pi*max(0,min(1,(p.z-.797)/.17))),p.y,p.z))
    for j,y in enumerate([-.055,0,.055],1):
        def segment(name,controls):
            pts=spline(controls,56);o=tube(name,[p[:3] for p in pts],[p[3] for p in pts],[p[3] for p in pts],'05_HANDS',SHELL,40)
            smooth(o,None,3);return o
        upper=segment('_proximal',[(s*.449,y,.842,.010),(s*.464,y,.833,.025),(s*.482,y,.806,.028),(s*.482,y,.782,.026),(s*.477,y,.773,.018)])
        lower=segment('_distal',[(s*.476,y,.770,.018),(s*.472,y,.756,.028),(s*.454,y,.735,.028),(s*.433,y,.721,.024),(s*.424,y,.719,.005)])
        bpy.ops.object.select_all(action='DESELECT');upper.select_set(True);lower.select_set(True);bpy.context.view_layer.objects.active=upper;bpy.ops.object.join();place(upper,'Finger '+label+str(j),'05_HANDS',SHELL)
        upper['construction']='Two closed phalanges with a narrow articulation seam; roots buried in palm'
# Fuller rounded toe domes: no planar plateau, no added nails.
for s,label in [(-1,'R'),(1,'L')]:
    for j,(cx,cy,h) in enumerate([(.110,-.248,.159),(.235,-.248,.166),(.357,-.217,.147)],1):
        n=96;nr=64;v=[];f=[]
        for i in range(nr):
            a=(pi/2)*i/nr;r=cos(a)**.88;z=.005+h*sin(a)**.88
            for k in range(n):
                t=2*pi*k/n;v.append((s*cx+.074*r*spow(cos(t),.80),cy+.116*r*spow(sin(t),.82),z))
        for i in range(nr-1):
            for k in range(n):a=i*n+k;b=i*n+(k+1)%n;f.append((a,b,b+n,a+n))
        v.append((s*cx,cy,.005+h));pole=len(v)-1
        for k in range(n):f.append(((nr-1)*n+k,(nr-1)*n+(k+1)%n,pole))
        f.append(tuple(reversed(range(n))));mesh('Toe cap '+label+str(j),v,f,'07_FEET',PANEL)
checkpoint('padded-limbs','Sloping shoulders, profiled limb shells, fair hip, articulated fingers and rounded toes saved')
# Thick folded ears: keep the reference's frontward/outward bend and actual recess.
for s,label in [(-1,'R'),(1,'L')]:
    a=(s*.114,-.104,1.983);b=(s*.188,-.167,2.143);L=(Vector(b)-Vector(a)).length
    ear=casing('Ear outer '+label,(0,0,0),.076,.061,L+.015,'03_EARS',SHELL,.023,2.75,.045)
    cutter=roundbox('_ear channel',(0,-.057,-.006),(.077,.078,L+.005),.024,'09_INTERNAL',None);boolean(ear,cutter,'Rounded inner-ear channel')
    insert=roundbox('Ear recessed insert '+label,(0,-.019,-.006),(.064,.004,L-.014),.0018,'03_EARS',INNER)
    rot,center=orient(ear,a,b);insert.matrix_world=Matrix.Translation(center)@rot@insert.matrix_world
    cap_a=(s*.173,-.168,2.145);cap_b=(s*.275,-.345,2.092);L=(Vector(cap_b)-Vector(cap_a)).length
    cap=casing('Ear folded cap '+label,(0,0,0),.071,.059,L,'03_EARS',SHELL,.030,2.75,.045)
    cap.data.materials.append(PANEL)
    for p in cap.data.polygons:
        if p.center.y<-.025 and p.center.z>-.075:p.material_index=1
    orient(cap,cap_a,cap_b);mark('Ear hinge '+label).location=a
bpy.context.view_layer.update();ear_objects=list(bpy.data.collections['03_EARS'].objects)
top=max((o.matrix_world@v.co).z for o in ear_objects if o.type=='MESH' for v in o.data.vertices);factor=(2.20-1.983)/(top-1.983)
for o in ear_objects:
    if o.type=='MESH':deform(o,lambda p:(p.x,p.y,1.983+(p.z-1.983)*factor))
for label in ['R','L']:
    o=mark('Bow wing '+label)
    deform(o,lambda p:(p.x,p.y-.004*smoothstep(1.50,1.36,p.z),1.437+(p.z-1.437)*(1.35 if p.z<1.437 else 1)))
# Carry required dependencies forward: excluded resume directories are never relied on.
for p in PREV.iterdir():
    if p.suffix in {'.py','.webp'}:shutil.copy2(p,OUT/('form-v002_source.py' if p.name=='geometry_source.py' else p.name))
for name in ['accepted_parent_import.json','parent_release_manifest.json']:shutil.copy2(PREV/name,OUT/name)
(OUT/'geometry_source.py').write_text(Path(__file__).read_text())
block=bpy.data.texts.get('BUILD_folded_form-v003.py') or bpy.data.texts.new('BUILD_folded_form-v003.py');block.clear();block.write(Path(__file__).read_text())
bpy.context.view_layer.update();preserved={n:h for n,h in before.items() if n not in changed}
for name,h in preserved.items():assert name in bpy.data.objects and fingerprint(bpy.data.objects[name])==h,name+' unexpectedly changed'
geos=[o for o in scene.objects if o.type in {'MESH','CURVE'} and not o.hide_render]
pts=[o.matrix_world@Vector(c) for o in geos for c in o.bound_box];lo=[min(p[k] for p in pts) for k in range(3)];hi=[max(p[k] for p in pts) for k in range(3)]
required={'Head casing':1,'Cheek pad ':2,'Eye ':2,'Nose':1,'U shaped lower jaw':1,'Ear outer ':2,'Ear folded cap ':2,'Ear recessed insert ':2,'Lower tooth ':10,'Upper tooth ':10,'Whisker ':6,'Toe cap ':6,'Finger ':6,'Palm and thumb ':2,'Button ':2,'Bow wing ':2,'Shin shell ':2}
counts={k:sum(o.name.startswith(k) for o in geos) for k in required};closed={};bounds={}
for o in geos:
    if o.type=='MESH':
        bm=bmesh.new();bm.from_mesh(o.data);closed[o.name]={'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'boundary_edges':sum(e.is_boundary for e in bm.edges)};bm.free()
    p=[o.matrix_world@Vector(c) for c in o.bound_box];bounds[o.name]={'min':[min(v[k] for v in p) for k in range(3)],'max':[max(v[k] for v in p) for k in range(3)]}
checks={'required_parts':counts==required,'finite_coordinates':all(math.isfinite(a) for o in geos if o.type=='MESH' for v in o.data.vertices for a in v.co),'closed_all_meshes':all(v['nonmanifold_edges']==0 for v in closed.values()),'height_range':2.18<hi[2]-lo[2]<2.23,'no_texture_nodes':not any(n.type=='TEX_IMAGE' for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes),'unchanged_parts_preserved':True,'continuous_muzzle_regions':all(head.vertex_groups.get('Muzzle cushion '+l) is not None for l in ['R','L'])}
audit={'job_id':JOB['job_id'],'pass':all(checks.values()),'checks':checks,'bounds_min':lo,'bounds_max':hi,'dimensions_m':[hi[k]-lo[k] for k in range(3)],'required_counts':counts,'closed_shell_checks':closed,'object_bounds':bounds,'objects':len(geos),'vertices':sum(len(o.data.vertices) for o in geos if o.type=='MESH'),'polygons':sum(len(o.data.polygons) for o in geos if o.type=='MESH'),'unchanged_object_fingerprints':preserved,'visual_review':'pending exact form-v003 images'}
(OUT/'geometry_audit.json').write_text(json.dumps(audit,indent=2));assert audit['pass'],json.dumps(checks)
(OUT/'lineage.json').write_text(json.dumps({'project_id':JOB['project_id'],'from_job':'form-v002','to_job':JOB['job_id'],'source_blend_sha256':PARENT_SHA,'preserved_objects':sorted(preserved),'modified_or_replaced_objects':sorted(changed),'scope':'Geometry only; accepted import not rerun; prior snapshot restored by runner'},indent=2))
bpy.ops.object.select_all(action='DESELECT');checkpoint('form-v003-ready','Editable shape refinement and exact parent lineage saved; actual image review remains mandatory')
