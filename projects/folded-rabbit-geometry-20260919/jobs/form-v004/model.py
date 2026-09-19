"""Refine the actual reviewed v003 scene; no base import, no textures, no surrogate images."""
import ast,bpy,bmesh,math,json,hashlib,shutil,struct
from pathlib import Path
from mathutils import Vector,Matrix
from math import sin,cos,pi,sqrt
OUT=Path(OUTPUT_DIR);OUT.mkdir(parents=True,exist_ok=True)
PREV=Path(WORKSPACE_DIR)/'resume'/'output'/'model';scene=bpy.context.scene
PARENT='7d3ca0c79a149f1377392b071444b4adbe8f94e2d71af4a2cfef3e5fa682f1bb'
assert scene['project_id']==JOB['project_id'] and scene['job_id']=='form-v003'
assert hashlib.sha256((PREV/'model.blend').read_bytes()).hexdigest()==PARENT
COL={c.name:c for c in bpy.data.collections}
SHELL=bpy.data.materials['Clay | shell'];PANEL=bpy.data.materials['Clay | face and panel'];INNER=bpy.data.materials['Clay | inner ear']
DARK=bpy.data.materials['Inspection | internal'];EYE=bpy.data.materials['Inspection | eyes and nose'];CLOTH=bpy.data.materials['Inspection | bow tie'];TOOTH=bpy.data.materials['Clay | teeth'];METAL=bpy.data.materials['Inspection | connectors']
sources=[('base_geometry_source.py','4a81f39cf97f8990133e98de9f9c834e259b213a9699b25eab3020b53d554b5f',{'place','mesh','apply','ball','spow','boolean','tube','curve','fused'}),('form-v001_source.py','5d1276e96ed77008f7d02b409644c6bf5656991ecfbcbce0d5f0f44e2cfa63f0',{'fit','roundbox','orient','smooth'}),('form-v002_source.py','023d673f457493a9e6385a900694ffdff02f09aabe4cfc983396335d58390a46',{'fingerprint','casing','closed_outline','cheek'}),('geometry_source.py','26a1c6b8d55d238c1ca0e9eafb2d15e93bb5d8a869a3e774331f068547bc5099',{'profiled','deform','smoothstep'})]
for filename,digest,names in sources:
    text=(PREV/filename).read_text();assert hashlib.sha256(text.encode()).hexdigest()==digest,filename
    nodes=[n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name in names];assert {n.name for n in nodes}==names
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<verified '+filename+'>','exec'),globals())
before={o.name:fingerprint(o) for o in scene.objects if o.type in {'MESH','CURVE'}};changed=set()
def delete(name):
    if name in bpy.data.objects:changed.add(name);bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
def mark(name):changed.add(name);return bpy.data.objects[name]
def actual_bounds(o):
    pts=[o.matrix_world@v.co for v in o.data.vertices]
    return Vector(tuple(min(p[k] for p in pts) for k in range(3))),Vector(tuple(max(p[k] for p in pts) for k in range(3)))
scene['job_id']=JOB['job_id'];scene['geometry_revision']='form-v004 / smooth facial depth field and continuous fingers'
scene['reference_scale_px_per_m']=1418/2.2
for n in ['Head casing','Mouth internal baffle','Pelvis and thigh casing']:delete(n)
for s,label in [(-1,'R'),(1,'L')]:
    delete('Cheek pad '+label);delete('Socket lining '+label)
    for j in range(1,4):delete('Finger '+label+str(j));delete('Toe cap '+label+str(j));delete('Whisker '+label+str(j))
for row in ['Lower','Upper']:
    for i in range(1,11):delete('%s tooth %02d'%(row,i))
# The muzzle is a smooth deformation of ONE shell, not intersecting raised oval bosses.
rows=[(1.600,.001,-.080,.050,0),(1.603,.112,-.248,.110,0),(1.613,.157,-.278,.132,0),(1.631,.183,-.290,.145,0),(1.663,.196,-.285,.151,0),(1.710,.201,-.266,.154,0),(1.775,.207,-.249,.153,0),(1.836,.204,-.238,.143,0)]
for i in range(51):
    a=(pi/2)*(1-i/51)
    rows.append((1.899+.106*cos(a),max(.0002,.188*sin(a)),-.025-.187*sin(a),-.025+.157*sin(a),0))
rows.append((2.005,.0002,-.0252,-.0248,0))
head=profiled('Head casing',rows,'02_HEAD',SHELL,2.26,160,7)
for v in head.data.vertices:
    x,y,z=v.co
    if y<-.075 and z<1.86:
        front_weight=smoothstep(-.080,-.215,y)
        lobes=sum(math.exp(-((x-s*.054)/.048)**2) for s in [-1,1])
        depth=.033*lobes*math.exp(-((z-1.648)/.092)**2)
        depth+=.018*math.exp(-(x/.064)**2-((z-1.717)/.090)**2)
        v.co.y-=front_weight*depth
        if z<1.633:v.co.z+=.007*math.exp(-(x/.012)**2)*smoothstep(1.633,1.603,z)*front_weight
# Lower head already ends above the jaw: do not let a mouth cutter eat the lip away.
for s,label in [(-1,'R'),(1,'L')]:
    boolean(head,ball('_orbital cutter',(s*.069,-.237,1.823),(.0445,.076,.052),'09_INTERNAL',None,112,72),'Recessed eye socket '+label)
smooth(head,.00125,20)
head.data.materials.append(PANEL);head.data.materials.append(DARK)
for p in head.data.polygons:
    x,y,z=p.center;brow=1.861+.054*math.exp(-((abs(x)-.069)/.068)**2)
    if y<-.116 and z<brow:p.material_index=1
    if y<-.140 and any(((x-s*.069)/.0445)**2+((z-1.823)/.052)**2<1.02**2 for s in [-1,1]):p.material_index=2
for s,label in [(-1,'R'),(1,'L')]:
    g=head.vertex_groups.new(name='Muzzle cushion '+label)
    ids=[v.index for v in head.data.vertices if .002<s*v.co.x<.123 and v.co.y<-.267 and 1.601<v.co.z<1.750]
    assert len(ids)>100;g.add(ids,1.0,'REPLACE')
    c=cheek(s,label);center=Vector((s*.191,-.079,1.722));rot=Matrix.Rotation(-s*math.radians(32),3,'Z')
    for v in c.data.vertices:v.co=center+rot@(v.co-center)
    fit(c,(s*.189,-.151,1.724),(.130,.181,.164));smooth(c,None,8)
    fit(mark('Eye '+label),(s*.069,-.212,1.830),(.069,.066,.072))
    ball('Socket lining '+label,(s*.069,-.174,1.820),(.043,.048,.051),'09_INTERNAL',DARK,96,64)
head['muzzle_construction']='Continuous analytic depth field; separately editable left/right vertex groups'
smooth(mark('Nose'),.0011,12)
ball('Mouth internal baffle',(0,-.163,1.585),(.144,.048,.062),'09_INTERNAL',DARK,96,64)
# Reference: six broad lower front teeth, side teeth turning into the mouth, two small upper tips.
angles=[-1.89,-1.51,-1.05,-.63,-.21,.21,.63,1.05,1.51,1.89]
for i,t in enumerate(angles,1):
    x=.108*sin(t);y=-.183-.092*cos(t);z=1.557+.026*sin(t)**2
    h=.040+(0.0015 if i in [3,6,8] else -.0005);rx=.0175 if 3<=i<=8 else .015
    o=casing('Lower tooth %02d'%i,(x,y,z),rx,.016,h,'02_HEAD',TOOTH,.013,2.7,.025,0,80)
    center=Vector((x,y,z));rot=Matrix.Rotation(-t*.72,3,'Z')@Matrix.Rotation((i%3-1)*.035,3,'Y')
    for v in o.data.vertices:v.co=center+rot@(v.co-center)
    # Rear upper teeth remain real editable parts but do not form an exposed piano-key row.
    ux=(-.023 if i==5 else .023) if i in [5,6] else x
    uz=1.612 if i in [5,6] else 1.643+.004*sin(t)**2
    uy=-.280 if i in [5,6] else y+.016
    casing('Upper tooth %02d'%i,(ux,uy,uz),.017 if i in [5,6] else .014,.014,.022,'02_HEAD',TOOTH,.009,2.8,.02,0,72)
for s,label in [(-1,'R'),(1,'L')]:
    for i,(z,end) in enumerate([(1.654,1.649),(1.639,1.627),(1.623,1.604)],1):
        curve('Whisker '+label+str(i),[(s*.115,-.303,z),(s*.151,-.290,z-.002),(s*.200,-.266,z+.003),(s*.225,-.247,end+.008),(s*.242,-.239,end)],.00058,'08_DETAILS',DARK)
checkpoint('facial-character','Continuous nose bridge, forward cheek covers, seated eyeballs and reference-like teeth saved')
# Narrow the upper shoulder silhouette while preserving the elbow/wrist and lower legs.
for s,label in [(-1,'R'),(1,'L')]:
    o=mark('Shoulder cap '+label);deform(o,lambda p,s=s:(p.x*.96,p.y,p.z-.006))
    o=mark('Upper arm casing '+label)
    deform(o,lambda p,s=s:(p.x-s*.008*smoothstep(1.23,1.49,p.z),p.y,p.z))
# Replace the upper hip ridge with matching-depth padded volumes, without a surface splice.
parts=[roundbox('_hip bridge',(0,.006,.921),(.461,.310,.118),.051,'06_LEGS',SHELL)]
for s,label in [(-1,'R'),(1,'L')]:
    rows=[(.610,.001,-.006,.010,s*.146),(.612,.084,-.095,.112,s*.146),(.625,.112,-.131,.148,s*.146),(.684,.125,-.147,.161,s*.147),(.818,.129,-.148,.162,s*.146),(.921,.127,-.147,.163,s*.141),(.963,.106,-.123,.142,s*.137),(.980,.001,.006,.014,s*.137)]
    parts.append(profiled('_thigh '+label,rows,'06_LEGS',SHELL,2.55))
hip=fused('Pelvis and thigh casing',parts,'06_LEGS',SHELL,.0019);smooth(hip,None,90)
# Interpolating Catmull-Rom path: includes the actual terminal points, unlike the old approximating spline.
def through(points,sub=12):
    out=[]
    for i in range(len(points)-1):
        p0=points[max(0,i-1)];p1=points[i];p2=points[i+1];p3=points[min(len(points)-1,i+2)]
        for j in range(sub):
            t=j/sub
            out.append(tuple(.5*(2*p1[k]+(-p0[k]+p2[k])*t+(2*p0[k]-5*p1[k]+4*p2[k]-p3[k])*t*t+(-p0[k]+3*p1[k]-3*p2[k]+p3[k])*t*t*t) for k in range(len(p1))))
    out.append(points[-1]);return out
for s,label in [(-1,'R'),(1,'L')]:
    p=mark('Palm and thumb '+label)
    # Raise the palm's knuckle edge gently; keep the wrist and thumb tip where they belong.
    deform(p,lambda v,s=s:(v.x,v.y,v.z+.018*math.exp(-((v.z-.810)/.040)**2)*smoothstep(.392,.440,s*v.x)))
    for j,y in enumerate([-.055,0,.055],1):
        controls=[(s*.450,y,.858,.013),(s*.467,y,.837,.027),(s*.484,y,.810,.028),(s*.489,y,.788,.027),(s*.488,y,.783,.025),(s*.487,y,.778,.027),(s*.476,y,.751,.028),(s*.452,y,.730,.027),(s*.433,y,.721,.021),(s*.425,y,.718,.008),(s*.424,y,.718,.0008)]
        pts=through(controls,10);r=[max(.0006,p[3]) for p in pts]
        o=tube('Finger '+label+str(j),[p[:3] for p in pts],r,r,'05_HANDS',SHELL,48);smooth(o,None,4)
        o['construction']='Continuous curled digit with a shallow circumferential phalange groove and a buried root'
# A softly squared dome lies between v002 flat plateaus and v003 egg-shaped toes.
for s,label in [(-1,'R'),(1,'L')]:
    for j,(cx,cy,h) in enumerate([(.110,-.248,.159),(.235,-.248,.166),(.357,-.217,.147)],1):
        n=96;nr=64;v=[];f=[]
        for i in range(nr):
            a=(pi/2)*i/nr;r=cos(a)**.70;z=.005+h*sin(a)**.70
            for k in range(n):
                t=2*pi*k/n;v.append((s*cx+.074*r*spow(cos(t),.77),cy+.116*r*spow(sin(t),.80),z))
        for i in range(nr-1):
            for k in range(n):a=i*n+k;b=i*n+(k+1)%n;f.append((a,b,b+n,a+n))
        v.append((s*cx,cy,.005+h));pole=len(v)-1
        for k in range(n):f.append(((nr-1)*n+k,(nr-1)*n+(k+1)%n,pole))
        f.append(tuple(reversed(range(n))));mesh('Toe cap '+label+str(j),v,f,'07_FEET',PANEL)
checkpoint('continuous-hands-and-hip','Continuous curved fingers, flush upper hip and softer squared toe caps saved')
# Preserve the accepted folded-ear silhouette; repair only the recess's thin open-ended rim.
for s,label in [(-1,'R'),(1,'L')]:
    old=bpy.data.objects['Ear outer '+label];oldlo,oldhi=actual_bounds(old);matrix=old.matrix_world.copy()
    delete('Ear outer '+label);delete('Ear recessed insert '+label)
    a=(s*.114,-.104,1.983);b=(s*.188,-.167,2.143);L=(Vector(b)-Vector(a)).length
    ear=casing('Ear outer '+label,(0,0,0),.076,.061,L+.015,'03_EARS',SHELL,.023,2.75,.045)
    cut=roundbox('_closed ear recess',(0,-.057,-.001),(.065,.078,L-.028),.023,'09_INTERNAL',None)
    boolean(ear,cut,'Closed rounded inner channel');smooth(ear,.0011,8)
    insert=roundbox('Ear recessed insert '+label,(0,-.019,-.001),(.055,.004,L-.047),.0018,'03_EARS',INNER)
    ear.matrix_world=matrix;insert.matrix_world=matrix.copy();bpy.context.view_layer.update();lo,hi=actual_bounds(ear)
    factors=Vector(tuple((oldhi[k]-oldlo[k])/(hi[k]-lo[k]) for k in range(3)))
    for o in [ear,insert]:deform(o,lambda p,lo=lo,oldlo=oldlo,factors=factors:tuple(oldlo[k]+(p[k]-lo[k])*factors[k] for k in range(3)))
# Persist the complete dependency closure of this continuation.
for p in PREV.iterdir():
    if p.suffix in {'.py','.webp'}:shutil.copy2(p,OUT/('form-v003_source.py' if p.name=='geometry_source.py' else p.name))
for name in ['accepted_parent_import.json','parent_release_manifest.json']:shutil.copy2(PREV/name,OUT/name)
(OUT/'geometry_source.py').write_text(Path(__file__).read_text())
block=bpy.data.texts.get('BUILD_folded_form-v004.py') or bpy.data.texts.new('BUILD_folded_form-v004.py');block.clear();block.write(Path(__file__).read_text())
bpy.context.view_layer.update();preserved={n:h for n,h in before.items() if n not in changed}
for name,h in preserved.items():assert fingerprint(bpy.data.objects[name])==h,name+' changed unexpectedly'
geos=[o for o in scene.objects if o.type in {'MESH','CURVE'} and not o.hide_render]
required={'Head casing':1,'Cheek pad ':2,'Eye ':2,'Nose':1,'U shaped lower jaw':1,'Ear outer ':2,'Ear folded cap ':2,'Ear recessed insert ':2,'Lower tooth ':10,'Upper tooth ':10,'Whisker ':6,'Toe cap ':6,'Finger ':6,'Palm and thumb ':2,'Button ':2,'Bow wing ':2,'Shin shell ':2}
counts={k:sum(o.name.startswith(k) for o in geos) for k in required};closed={};bounds={};actual=[]
for o in geos:
    if o.type=='MESH':
        bm=bmesh.new();bm.from_mesh(o.data);closed[o.name]={'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'boundary_edges':sum(e.is_boundary for e in bm.edges)};bm.free()
        lo,hi=actual_bounds(o);actual.extend([lo,hi]);bounds[o.name]={'min':list(lo),'max':list(hi)}
lo=[min(p[k] for p in actual) for k in range(3)];hi=[max(p[k] for p in actual) for k in range(3)]
checks={'required_parts':counts==required,'finite_coordinates':all(math.isfinite(a) for o in geos if o.type=='MESH' for v in o.data.vertices for a in v.co),'closed_all_meshes':all(v['nonmanifold_edges']==0 for v in closed.values()),'height_range':2.18<hi[2]-lo[2]<2.22,'no_texture_nodes':not any(n.type=='TEX_IMAGE' for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes),'unchanged_parts_preserved':True,'continuous_muzzle_regions':all(head.vertex_groups.get('Muzzle cushion '+l) is not None for l in ['R','L'])}
audit={'job_id':JOB['job_id'],'pass':all(checks.values()),'checks':checks,'bounds_method':'actual transformed mesh vertices, not rotated object bounding-box corners','bounds_min':lo,'bounds_max':hi,'dimensions_m':[hi[k]-lo[k] for k in range(3)],'required_counts':counts,'closed_shell_checks':closed,'object_bounds':bounds,'objects':len(geos),'vertices':sum(len(o.data.vertices) for o in geos if o.type=='MESH'),'polygons':sum(len(o.data.polygons) for o in geos if o.type=='MESH'),'unchanged_object_fingerprints':preserved,'visual_review':'pending exact form-v004 images'}
(OUT/'geometry_audit.json').write_text(json.dumps(audit,indent=2));assert audit['pass'],json.dumps(checks)
(OUT/'lineage.json').write_text(json.dumps({'project_id':JOB['project_id'],'from_job':'form-v003','to_job':JOB['job_id'],'source_blend_sha256':PARENT,'preserved_objects':sorted(preserved),'modified_or_replaced_objects':sorted(changed),'scope':'Geometry only; accepted original import, torso, lower-leg shapes, tail, bow and folded caps not rebuilt'},indent=2))
bpy.ops.object.select_all(action='DESELECT');checkpoint('form-v004-ready','Saved editable form and exact parent lineage. Actual final-image comparison is still mandatory.')
