"""Refine the saved v003 geometry; all ancestor sources are verified and retained."""
import ast,bpy,bmesh,math,json,hashlib,shutil,bisect
from pathlib import Path
from mathutils import Vector
from math import sin,cos,pi,sqrt
OUT=Path(OUTPUT_DIR);OUT.mkdir(parents=True,exist_ok=True)
BASE=Path(WORKSPACE_DIR)/'resume'/'output'/'model';scene=bpy.context.scene
assert scene['project_id']==JOB['project_id'] and scene['job_id']=='form-v003'
parent_hash='4a22745761274f797c9a8f10766d653cd1196ef249bd940b98ee60244a5e6c1f'
assert hashlib.sha256((BASE/'model.blend').read_bytes()).hexdigest()==parent_hash
base=(BASE/'base_geometry_source.py').read_text();v2=(BASE/'parent_form-v002_source.py').read_text();v3=(BASE/'geometry_source.py').read_text()
for text,h in [(base,'4a81f39cf97f8990133e98de9f9c834e259b213a9699b25eab3020b53d554b5f'),(v2,'249d267f46abed42e25abbd7a67fab78bf241684b381ef70f05afcb575004d84'),(v3,'ebcc13bb2adc28e9f331f2279137c81ba3d0fbb845e93e38735a65771d85765c')]:assert hashlib.sha256(text.encode()).hexdigest()==h
COL={c.name:c for c in bpy.data.collections}
SHELL=bpy.data.materials['Clay | shell'];PANEL=bpy.data.materials['Clay | face and panel'];INNER=bpy.data.materials['Clay | inner ear'];DARK=bpy.data.materials['Inspection | internal']
EYE=bpy.data.materials['Inspection | eyes and nose'];CLOTH=bpy.data.materials['Inspection | bow tie'];TOOTH=bpy.data.materials['Clay | teeth'];METAL=bpy.data.materials['Inspection | connectors']
for text,names in [(base,{'place','mesh','apply','ball','cylinder','spow','loft','boolean','hollow','prism','tube','curve','fused'}),(v2,{'remove','relax','fingerprint'}),(v3,{'spline','interp','remesh_round'})]:
    nodes=[n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name in names];assert {n.name for n in nodes}==names
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<verified-geometry-helpers>','exec'),globals())
# Copy dependencies and the correct job identity BEFORE the first checkpoint.
scene['job_id']=JOB['job_id'];scene['previous_job_id']='form-v003'
scene['scope']='Geometry only; no textures, final UV layout or articulated rig'
for name,text in [('base_geometry_source.py',base),('parent_form-v002_source.py',v2),('parent_form-v003_source.py',v3),('geometry_source.py',Path(__file__).read_text())]:(OUT/name).write_text(text)
ref=Path(INPUT_DIR)/'reference.webp';assert hashlib.sha256(ref.read_bytes()).hexdigest()=='c878b9f1522a412c8b1174333ac456939307f3e048aea2b86120ef388d5aeaf0';shutil.copy2(ref,OUT/'reference.webp')
text=bpy.data.texts.get('REFINE_form-v004.py') or bpy.data.texts.new('REFINE_form-v004.py');text.clear();text.write(Path(__file__).read_text())
keep=[o.name for o in scene.objects if o.name.startswith(('Eye ','Muzzle cushion ','Upper tooth ','Lower tooth ','Whisker ','Ear spring ','Ear stem ','Shoulder axle ','Elbow joint ','Wrist joint ','Hip connector ','Knee connector ','Ankle connector ','Ankle cuff '))]+['Tail','Neck connector','Nose','Muzzle center split']
kept_before={n:fingerprint(bpy.data.objects[n]) for n in keep}
# Read only literal profile data from the verified source, not its generation statements.
profile_data={n.targets[0].id:ast.literal_eval(n.value) for n in ast.parse(v3).body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in {'hp','mp'}}
remove('Head continuous casing');remove('Mouth internal baffle')
skull=loft('_smooth_skull',profile_data['hp'],'02_HEAD',SHELL,2.08,112,density=10)
boolean(skull,loft('_mouth_void',profile_data['mp'],'09_INTERNAL',None,2.35,96,lambda p:(p[0],p[2],p[1]),10),'Deep oral cavity behind muzzle')
# Both tube ends now terminate deeply INSIDE the skull, not as visible cheek fins.
half=[(.125,-.030,1.600,.030),(.157,-.115,1.557,.038),(.183,-.100,1.521,.040),(.188,-.066,1.479,.034),(.175,-.081,1.436,.032),(.153,-.145,1.385,.029),(.098,-.223,1.346,.027),(.042,-.251,1.339,.027),(0.,-.255,1.338,.027)]
path=spline(half+[(-x,y,z,r) for x,y,z,r in reversed(half[:-1])],193)
jaw=tube('_curved_mandible',[p[:3] for p in path],[p[3] for p in path],[p[3] for p in path],'02_HEAD',SHELL,40)
head=fused('Head continuous casing',[skull,jaw],'02_HEAD',SHELL,.0017)
for s,label in [(-1,'R'),(1,'L')]:boolean(head,ball('_orbital_cavity',(s*.065,-.264,1.592),(.0525,.076,.059),'09_INTERNAL',None,72,48),'Orbital recess '+label)
remesh_round(head,.0016,22)
head.data.materials.clear();head.data.materials.append(SHELL);head.data.materials.append(PANEL)
for face in head.data.polygons:
    c=face.center;brow=1.607+.053*math.exp(-((abs(c.x)-.065)/.068)**2)
    if c.y<-.146 and c.z<brow and (c.z>1.465 or c.y<-.180):face.material_index=1
vg=head.vertex_groups.new(name='Mandible_region_for_later_rigging');vg.add([v.index for v in head.data.vertices if v.co.z<1.454 and v.co.y<-.072],1.,'REPLACE')
head['construction']='C-shaped mandible with buried terminations; actual eye and mouth cavities'
# A posterior half-ellipsoid forms a real oral roof, rear wall and ascending floor.
# It is open towards the mouth, not an opaque plane painted across the opening.
v=[];f=[];n=96;nr=48
for i in range(nr):
    t=pi/2*i/nr
    for j in range(n):
        a=2*pi*j/n;v.append((.169*cos(t)*cos(a),-.242+.170*sin(t),1.410+.043*sin(t)+.061*cos(t)*sin(a)))
for i in range(nr-1):
    for j in range(n):a=i*n+j;b=i*n+(j+1)%n;f.append((a,b,b+n,a+n))
v.append((0,-.072,1.453));pole=len(v)-1
for j in range(n):f.append(((nr-1)*n+j,(nr-1)*n+(j+1)%n,pole))
cup=mesh('Mouth internal baffle',v,f,'09_INTERNAL',DARK)
so=cup.modifiers.new('Real oral lining thickness','SOLIDIFY');so.thickness=.002;so.offset=0;apply(cup,so)
cup['construction']='Open hollow oral cup with floor and rear wall, not a screen or texture'
for label in ['R','L']:
    relax(bpy.data.objects['Ear outer '+label],20,.48)
    wing=bpy.data.objects['Bow wing '+label];m=wing.modifiers.new('Soften folded cloth curvature','SUBSURF');m.levels=1;m.render_levels=1;apply(wing,m)
checkpoint('closed-oral-lining','Buried jaw terminations, real hollow oral floor, polished ear rims and softer bow folds')
# Keep the successful finger profiles, remove the extra root ball that doubled the thumb.
start=v3.index('for s,label in [(-1,\'R\'),(1,\'L\')]:\n    remove(\'Hand continuous ')
end=v3.index('# Toe surfaces are analytic',start)
hand_code=v3[start:end].replace("ball('_thumb_root',(s*.787,-.048,1.232),(.042,.045,.035),'05_HANDS',SHELL,64,40),",'')
assert '_thumb_root' not in hand_code
exec(compile(hand_code,'<verified-v003-hands-with-single-thumb>','exec'),globals())
# Shorter forefoot casing exposes the complete broad toes, rather than hiding them as nails.
def toe_dome(name,cx,cy,width,height):
    n=80;nr=48;v=[];f=[]
    for i in range(nr):
        t=pi/2*i/nr;r=cos(t)**(2/2.4)
        for j in range(n):
            a=2*pi*j/n;v.append((cx+width*r*spow(cos(a),2/2.15),cy+.086*r*spow(sin(a),2/2.15),.003+height*sin(t)**(2/2.1)))
    for i in range(nr-1):
        for j in range(n):a=i*n+j;b=i*n+(j+1)%n;f.append((a,b,b+n,a+n))
    v.append((cx,cy,.003+height));pole=len(v)-1
    for j in range(n):f.append(((nr-1)*n+j,(nr-1)*n+(j+1)%n,pole))
    f.append(tuple(reversed(range(n))))
    o=mesh(name,v,f,'07_FEET',PANEL);o.data.polygons[-1].use_smooth=False;o['separate_future_material_zone']=True
    return o
footp=[(-.207,.119,.020,.080),(-.192,.151,.003,.111),(-.130,.163,.003,.139),(-.045,.152,.003,.148),(.050,.127,.004,.134),(.107,.102,.006,.096),(.134,.067,.013,.065),(.139,.015,.033,.043)]
for label,cx in [('R',-.170),('L',.162)]:
    remove('Foot base '+label);loft('Foot base '+label,footp,'07_FEET',SHELL,2.55,96,lambda p,cx=cx:(p[0]+cx,p[2],p[1]),12)
    for j,dx in enumerate([-.105,0,.105]):
        name='Toe cap '+label+str(j+1);remove(name);toe_dome(name,cx+dx,-.225,.062 if j==1 else .059,.113 if j==1 else .107)
checkpoint('rounded-forefeet','Shortened foot casing with visible broad toe domes and single continuous thumbs')
# Refine the inspected casing contours only; preserve the skeleton, face details and pose.
remove('Torso outer casing');remove('Fitted belly panel')
body_profile=[(.749,.203,-.147,.165),(.756,.243,-.183,.194),(.802,.258,-.218,.211),(.918,.260,-.251,.212),(1.045,.250,-.241,.201),(1.172,.241,-.209,.174),(1.265,.237,-.171,.139),(1.319,.216,-.131,.108),(1.348,.168,-.105,.080),(1.360,.085,-.077,.063),(1.364,.001,-.016,-.014)]
body=loft('Torso outer casing',body_profile,'01_BODY',SHELL,2.55,112,density=12)
rows=interp(body_profile,20)
def body_at(z):
    for a,b in zip(rows,rows[1:]):
        if a[0]<=z<=b[0]:
            t=(z-a[0])/(b[0]-a[0]);return [a[j]*(1-t)+b[j]*t for j in range(1,4)]
    return rows[-1][1:] if z>rows[-1][0] else rows[0][1:]
pr=interp([(.766,.150),(.780,.179),(.86,.198),(1.01,.190),(1.15,.159),(1.25,.112),(1.318,.075)],12);v=[];f=[];nx=64
for z,w in pr:
    rx,yf,yb=body_at(z)
    for j in range(nx+1):
        x=w*(2*j/nx-1);y=(yf+yb)/2-(yb-yf)/2*max(0.,1-(abs(x)/rx)**2.55)**(1/2.55)-.0015;v.append((x,y,z))
for i in range(len(pr)-1):
    for j in range(nx):a=i*(nx+1)+j;f.append((a,a+1,a+nx+2,a+nx+1))
panel=mesh('Fitted belly panel',v,f,'01_BODY',PANEL);so=panel.modifiers.new('Thin fitted panel','SOLIDIFY');so.thickness=.0015;so.offset=0;apply(panel,so)
for i in [1,2]:o=bpy.data.objects['Button '+str(i)];o.location.y=body_at(o.location.z)[1]-.012
upper=[(.244,.060,-.067,.067),(.254,.081,-.082,.082),(.287,.090,-.088,.088),(.364,.090,-.087,.087),(.448,.079,-.079,.079),(.477,.074,-.071,.071),(.486,.058,-.057,.057)]
lower=[(.492,.060,-.062,.062),(.503,.078,-.079,.079),(.561,.078,-.079,.079),(.672,.076,-.077,.077),(.722,.070,-.071,.071),(.734,.056,-.058,.058)]
arms={};thighs={}
for s,label in [(-1,'R'),(1,'L')]:
    remove('Upper arm shell '+label);remove('Forearm shell '+label)
    trans=lambda p,s=s:(s*p[2],p[1],1.239+p[0])
    arms[label]=loft('Upper arm shell '+label,upper,'04_ARMS',SHELL,2.55,96,trans,12)
    loft('Forearm shell '+label,lower,'04_ARMS',SHELL,2.55,96,trans,12)
for label,cx,wide in [('R',-.128,1.03),('L',.122,1.)]:
    remove('Thigh shell '+label);remove('Shin shell '+label)
    thighp=[(.506,.075,-.074,.079),(.519,.097,-.094,.100),(.577,.103,-.101,.108),(.672,.108,-.106,.112),(.736,.105,-.103,.110),(.745,.092,-.090,.096)]
    thighs[label]=loft('Thigh shell '+label,thighp,'06_LEGS',SHELL,2.60,96,lambda p,cx=cx,wide=wide:(cx+p[0]*wide,p[1]+.007,p[2]),12)
    shinp=[(.154,.078,-.080,.085),(.163,.098,-.098,.105),(.189,.101,-.102,.111),(.286,.100,-.103,.113),(.416,.098,-.100,.110),(.489,.094,-.094,.103),(.501,.078,-.079,.087)]
    loft('Shin shell '+label,shinp,'06_LEGS',SHELL,2.60,96,lambda p,cx=cx:(p[0]+cx,p[1]+.008,p[2]),12)
# Broken edges have a few irregular soft turns, not a repeated sawtooth pattern.
def rounded_outline(poly,fraction=.06):
    result=[]
    for i,p in enumerate(poly):
        a=poly[(i-1)%len(poly)];b=poly[(i+1)%len(poly)]
        left=[(1-fraction)*p[k]+fraction*a[k] for k in range(2)];right=[(1-fraction)*p[k]+fraction*b[k] for k in range(2)]
        for j in range(5):
            t=j/5;result.append([(1-t)**2*left[k]+2*t*(1-t)*p[k]+t*t*right[k] for k in range(2)])
    return result
hollow(arms['R'],.006)
a=[(-.383,1.365),(-.233,1.365),(-.233,1.279),(-.273,1.275),(-.311,1.285),(-.340,1.305),(-.354,1.335)]
boolean(arms['R'],prism('_arm_break',rounded_outline(a),-.2,.016),'Reference shoulder-side shell break');remesh_round(arms['R'],.0014,6)
# These are separate breaks because the reference front/back drawings differ.
hollow(thighs['R'],.007)
a=[(-.152,.777),(-.020,.777),(-.020,.630),(-.067,.632),(-.099,.641),(-.139,.638),(-.165,.649),(-.183,.660),(-.171,.704),(-.150,.735)]
boolean(thighs['R'],prism('_thigh_front_break',rounded_outline(a),-.25,.025),'Reference front inner-thigh break');remesh_round(thighs['R'],.0015,6)
hollow(thighs['L'],.007)
a=[(.014,.777),(.249,.777),(.249,.598),(.204,.603),(.174,.622),(.126,.659),(.095,.666),(.058,.635),(.014,.612)]
boolean(thighs['L'],prism('_thigh_back_break',rounded_outline(a),.045,.25),'Reference rear thigh break');remesh_round(thighs['L'],.0015,6)
checkpoint('casing-contours','Rounded casing profiles, fitted belly and reference-shaped shell defects; unchanged joint chain retained')
bpy.context.view_layer.update()
geos=[o for o in scene.objects if o.type in {'MESH','CURVE'} and not o.hide_render]
points=[o.matrix_world@Vector(c) for o in geos for c in o.bound_box];lo=[min(v[k] for v in points) for k in range(3)];hi=[max(v[k] for v in points) for k in range(3)]
required={'Head continuous casing':1,'Hand continuous ':2,'Ear outer ':2,'Eye ':2,'Lower tooth ':10,'Upper tooth ':10,'Whisker ':6,'Toe cap ':6,'Button ':2,'Bow wing ':2,'Thigh shell ':2,'Shin shell ':2}
counts={k:sum(o.name.startswith(k) for o in geos) for k in required};kept={n:fingerprint(bpy.data.objects[n])==h for n,h in kept_before.items()}
closed={}
for name in ['Head continuous casing','Mouth internal baffle','Hand continuous R','Hand continuous L','Ear outer R','Ear outer L','Upper arm shell R','Thigh shell R','Thigh shell L']:
    bm=bmesh.new();bm.from_mesh(bpy.data.objects[name].data);closed[name]={'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges)};bm.free()
checks={'finite_coordinates':all(math.isfinite(a) for o in geos if o.type=='MESH' for v in o.data.vertices for a in v.co),'required_parts':counts==required,'closed_revised_shells':all(v['nonmanifold_edges']==0 for v in closed.values()),'preserved_unaffected_parts':all(kept.values()),'height_range':2.17<hi[2]-lo[2]<2.25,'span_range':2.05<hi[0]-lo[0]<2.18,'no_texture_nodes':not any(n.type=='TEX_IMAGE' for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes)}
audit={'job_id':JOB['job_id'],'pass':all(checks.values()),'checks':checks,'bounds_min':lo,'bounds_max':hi,'dimensions_m':[hi[k]-lo[k] for k in range(3)],'required_counts':counts,'closed_shell_checks':closed,'preserved_parts':kept,'objects':len(geos),'vertices':sum(len(o.data.vertices) for o in geos if o.type=='MESH'),'polygons':sum(len(o.data.polygons) for o in geos if o.type=='MESH'),'visual_review':'pending exact new images','limitations':['2D reconstruction, not original topology','No finished texture/UV/rig','Unseen internal geometry is inferred']}
(OUT/'geometry_audit.json').write_text(json.dumps(audit,indent=2));(OUT/'lineage.json').write_text(json.dumps({'parent_job':'form-v003','parent_blend_sha256':parent_hash,'preserved_parts':kept,'changes':'Buried jaw ends, real hollow oral lining, broad visible toes, single thumb, casing and defect contours, polished ear and bow surfaces'},indent=2))
assert audit['pass'],json.dumps(audit)
bpy.ops.object.select_all(action='DESELECT');checkpoint('geometry-v004','Geometry audit passed; exact-image review still required')
