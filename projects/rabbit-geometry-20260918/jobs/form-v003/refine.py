"""Continue form-v002: curved mandibular walls, rounded recesses and continuous digits.
The reference scale is 300 px/m; front -Y. This is geometry, not texture camouflage.
"""
import ast,bpy,bmesh,math,json,hashlib,shutil,bisect
from pathlib import Path
from mathutils import Vector
from math import sin,cos,pi,sqrt
OUT=Path(OUTPUT_DIR);OUT.mkdir(parents=True,exist_ok=True)
BASE=Path(WORKSPACE_DIR)/'resume'/'output'/'model'
scene=bpy.context.scene
assert scene['project_id']=='rabbit-geometry-20260918' and scene['job_id']=='form-v002'
assert hashlib.sha256((BASE/'model.blend').read_bytes()).hexdigest()=='f028acd02a8dd1ddd57f64d260e75fb50382151c72668cb1ea0fec39bc8f1f4f'
base=(BASE/'base_geometry_source.py').read_text();parent=(BASE/'geometry_source.py').read_text()
assert hashlib.sha256(base.encode()).hexdigest()=='4a81f39cf97f8990133e98de9f9c834e259b213a9699b25eab3020b53d554b5f'
assert hashlib.sha256(parent.encode()).hexdigest()=='249d267f46abed42e25abbd7a67fab78bf241684b381ef70f05afcb575004d84'
COL={c.name:c for c in bpy.data.collections}
SHELL=bpy.data.materials['Clay | shell'];PANEL=bpy.data.materials['Clay | face and panel']
INNER=bpy.data.materials['Clay | inner ear'];DARK=bpy.data.materials['Inspection | internal']
EYE=bpy.data.materials['Inspection | eyes and nose'];CLOTH=bpy.data.materials['Inspection | bow tie']
TOOTH=bpy.data.materials['Clay | teeth'];METAL=bpy.data.materials['Inspection | connectors']
for text,names in [(base,{'place','mesh','apply','ball','cylinder','interp','spow','loft','boolean','tube','curve','fused'}),(parent,{'remove','relax','fingerprint'})]:
    nodes=[n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes}==names
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<verified-helper-definitions>','exec'),globals())
keep_names=['Tail','Neck connector','Shoulder axle R','Shoulder axle L','Elbow joint R','Elbow joint L','Wrist joint R','Wrist joint L','Ear spring R','Ear spring L','Torso outer casing','Fitted belly panel','Thigh shell R','Thigh shell L','Shin shell R','Shin shell L']
kept_before={n:fingerprint(bpy.data.objects[n]) for n in keep_names}

# Open-uniform cubic B-splines have continuous second derivatives. They replace the
# previous C1 section interpolation whose local extrema produced highlight bands.
def spline(points,count):
    n=len(points);p=min(3,n-1)
    knots=[0.]*(p+1)+[i/(n-p) for i in range(1,n-p)]+[1.]*(p+1)
    out=[]
    for step in range(count):
        t=step/(count-1)
        if step==count-1:out.append(list(points[-1]));continue
        k=min(n-1,max(p,bisect.bisect_right(knots,t)-1))
        d=[list(points[k-p+j]) for j in range(p+1)]
        for r in range(1,p+1):
            for j in range(p,r-1,-1):
                i=k-p+j;den=knots[i+p-r+1]-knots[i]
                a=(t-knots[i])/den if den else 0.
                d[j]=[(1-a)*x+a*y for x,y in zip(d[j-1],d[j])]
        out.append(d[p])
    return out

def interp(profile,density=8):return spline(profile,max(32,(len(profile)-1)*density+1))

def remesh_round(o,voxel=.0016,iterations=14):
    m=o.modifiers.new('Uniform sculpt topology','REMESH');m.mode='VOXEL';m.voxel_size=voxel;m.use_smooth_shade=True;apply(o,m)
    relax(o,iterations,.40)
    for face in o.data.polygons:face.use_smooth=True

# Carve the skull FIRST, then unite a genuinely curved C-shaped mandible. Carving
# the jaw with the same enormous cutter was the cause of the previous diagonal bar.
remove('Head continuous casing');remove('Mouth internal baffle')
hp=[(1.379,.132,-.106,.070),(1.393,.164,-.155,.110),(1.436,.191,-.189,.131),(1.487,.217,-.223,.144),(1.522,.225,-.243,.149),(1.563,.205,-.249,.147),(1.611,.182,-.249,.143),(1.657,.172,-.218,.127),(1.699,.145,-.175,.103),(1.729,.105,-.132,.076),(1.749,.045,-.066,.033),(1.750,.001,-.018,-.016)]
skull=loft('_smooth_skull',hp,'02_HEAD',SHELL,2.08,112,density=10)
mp=[(-.60,.195,1.29,1.481),(-.34,.179,1.29,1.481),(-.27,.170,1.300,1.483),(-.21,.160,1.313,1.497),(-.15,.155,1.330,1.521),(-.113,.149,1.356,1.518),(-.093,.109,1.397,1.490),(-.084,.001,1.451,1.452)]
boolean(skull,loft('_mouth_void',mp,'09_INTERNAL',None,2.35,96,lambda p:(p[0],p[2],p[1]),10),'Deep oral cavity behind muzzle')
# Reference side outline: upper x990/y206, rear bulge x1018/y229,
# lower rear x1011/y252, chin x949/y270. Coordinates are estimates, not scan data.
half=[(.169,-.142,1.538,.042),(.183,-.087,1.518,.037),(.184,-.066,1.479,.032),(.175,-.081,1.436,.032),(.153,-.145,1.385,.029),(.098,-.223,1.346,.027),(.042,-.251,1.339,.027),(0.,-.255,1.338,.027)]
path=spline(half+[(-x,y,z,r) for x,y,z,r in reversed(half[:-1])],181)
jaw=tube('_curved_mandible',[p[:3] for p in path],[p[3] for p in path],[p[3] for p in path],'02_HEAD',SHELL,40)
head=fused('Head continuous casing',[skull,jaw],'02_HEAD',SHELL,.0017)
for s,label in [(-1,'R'),(1,'L')]:
    boolean(head,ball('_orbital_cavity',(s*.065,-.264,1.592),(.0525,.076,.059),'09_INTERNAL',None,72,48),'Orbital recess '+label)
remesh_round(head,.0016,18)
head.data.materials.clear();head.data.materials.append(SHELL);head.data.materials.append(PANEL)
for face in head.data.polygons:
    c=face.center
    brow=1.607+.053*math.exp(-((abs(c.x)-.065)/.068)**2)
    if c.y<-.146 and (c.z<brow and (c.z>1.465 or c.y<-.180)):face.material_index=1
vg=head.vertex_groups.new(name='Mandible_region_for_later_rigging')
vg.add([v.index for v in head.data.vertices if v.co.z<1.454 and v.co.y<-.072],1.,'REPLACE')
head['construction']='C2 skull sections, real orbital/oral voids, continuous curved cheek-mandible wall'
head['rigging_note']='Fixed open-mouth pose, selectable mandible region; no rig'
ball('Mouth internal baffle',(0,-.043,1.455),(.136,.049,.064),'09_INTERNAL',DARK,64,40)
for i in range(10):
    theta=-1.25+2.5*i/9;o=bpy.data.objects['Lower tooth %02d'%(i+1)]
    o.location=(.143*sin(theta),-.139-.116*cos(theta),1.375+.051*sin(theta)**2)
# Smooth muzzle lobes, with slight central contact instead of detached spheres.
for s,label in [(-1,'R'),(1,'L')]:
    o=bpy.data.objects['Muzzle cushion '+label];o.location.x=s*.049;o.location.z=1.494
    mod=o.modifiers.new('Smooth muzzle curvature','SUBSURF');mod.levels=1;mod.render_levels=1;apply(o,mod)

# Rounded ear crowns and long channels which open through the lower edge.
# End controls share the crown height, producing a rounded tangent at the tip.
ep=[(1.756,.051,.047),(1.773,.056,.051),(1.900,.069,.057),(2.051,.076,.059),(2.143,.074,.056),(2.188,.058,.044),(2.210,.025,.022),(2.210,.001,.001)]
def ey(z):
    t=max(0.,min(1.,(z-1.756)/.454));return -.022-.056*t**2.7
for s,label in [(-1,'R'),(1,'L')]:
    remove('Ear outer '+label);remove('Ear recessed insert '+label);cx=s*.096
    ear=loft('Ear outer '+label,[(z,w,ey(z)-d,ey(z)+d) for z,w,d in ep],'03_EARS',SHELL,2.30,96,lambda p,cx=cx:(p[0]+cx,p[1],p[2]),12)
    ch=[(1.725,.023),(1.777,.027),(1.91,.034),(2.032,.039),(2.081,.034),(2.105,.018),(2.105,.001)]
    cut=loft('_open_ear_channel',[(z,w,ey(z)-.19,ey(z)+.016) for z,w in ch],'09_INTERNAL',None,2.10,80,lambda p,cx=cx:(p[0]+cx,p[1],p[2]),12)
    boolean(ear,cut,'Open-bottom recessed ear channel');remesh_round(ear,.0014,10)
    ch[0]=(1.758,.023)
    insert=loft('Ear recessed insert '+label,[(z,w*.93,ey(z)+.0135,ey(z)+.0155) for z,w in ch],'03_EARS',INNER,2.1,80,lambda p,cx=cx:(p[0]+cx,p[1],p[2]),12)
    ear['construction']='Rounded crown and real deep channel, no projecting bottom crossbar'
checkpoint('curved-face-and-ears','C-shaped mandible, softened sockets, C2 skull surface and rounded open-bottom ear channels')

# The new fingers begin INSIDE the palm. Rounded profile endpoints eliminate the
# flat cylinders and exposed root caps; the tips still resolve as three digits.
for s,label in [(-1,'R'),(1,'L')]:
    remove('Hand continuous '+label)
    parts=[ball('_palm',(s*.828,.001,1.244),(.099,.088,.044),'05_HANDS',SHELL,64,40)]
    for j,(yy,end) in enumerate([(-.054,1.050),(0.,1.065),(.054,1.039)]):
        fp=[(.808,.015,-.019,.019),(.834,.040,-.033,.034),(.892,.035,-.031,.033),(end-.060,.032,-.030,.031),(end-.021,.031,-.028,.027),(end-.004,.018,-.018,.016),(end,.001,-.001,.001)]
        def hand_transform(p,s=s,yy=yy):
            a=p[2];u=max(0.,min(1.,(a-.88)/.19));return (s*a,p[0]+yy,1.245+p[1]-.010*u*u)
        parts.append(loft('_finger',fp,'05_HANDS',SHELL,2.04,64,hand_transform,12))
    parts.extend([ball('_thumb_root',(s*.787,-.048,1.232),(.042,.045,.035),'05_HANDS',SHELL,64,40),ball('_thumb_tip',(s*.810,-.090,1.213),(.044,.035,.035),'05_HANDS',SHELL,64,40)])
    hand=fused('Hand continuous '+label,parts,'05_HANDS',SHELL,.00135);relax(hand,14,.40)
    for j,yy in enumerate([-.054,0.,.054]):
        g=hand.vertex_groups.new(name='Finger_'+str(j+1));ids=[v.index for v in hand.data.vertices if abs((hand.matrix_world@v.co).x)>.88 and abs((hand.matrix_world@v.co).y-yy)<.032]
        if ids:g.add(ids,1.,'REPLACE')
    g=hand.vertex_groups.new(name='Thumb');ids=[v.index for v in hand.data.vertices if (hand.matrix_world@v.co).y<-.062 and abs((hand.matrix_world@v.co).x)<.86]
    if ids:g.add(ids,1.,'REPLACE')
    hand['digits']='Three rounded continuous fingers plus thumb; grooves retained'

# Toe surfaces are analytic ellipsoid domes with a flat sole, NOT a capped loft.
# The sole is deliberately planar; there is no flat front end or ring terrace.
def toe_dome(name,cx,cy):
    n=80;nr=48;v=[];f=[]
    for i in range(nr):
        t=(pi/2)*i/nr
        for j in range(n):
            a=2*pi*j/n;v.append((cx+.0575*cos(t)*cos(a),cy+.086*cos(t)*sin(a),.003+.124*sin(t)))
    for i in range(nr-1):
        for j in range(n):
            a=i*n+j;b=i*n+(j+1)%n;f.append((a,b,b+n,a+n))
    v.append((cx,cy,.127));pole=len(v)-1
    for j in range(n):f.append(((nr-1)*n+j,(nr-1)*n+(j+1)%n,pole))
    f.append(tuple(reversed(range(n))))
    o=mesh(name,v,f,'07_FEET',PANEL);o['separate_future_material_zone']=True
    return o
for label,cx in [('R',-.170),('L',.162)]:
    for j,dx in enumerate([-.105,0,.105]):
        name='Toe cap '+label+str(j+1);remove(name);toe_dome(name,cx+dx,-.225)

# Broad, angular folded bow wings follow the reference, rather than little ovals.
def bow_wing(label,s):
    outline=[(.017,1.245),(.063,1.270),(.137,1.294),(.130,1.241),(.131,1.151),(.083,1.184),(.035,1.215)]
    edge=[]
    for i,p in enumerate(outline):
        prev=outline[(i-1)%len(outline)];nxt=outline[(i+1)%len(outline)]
        a=[p[k]*.90+prev[k]*.10 for k in range(2)];b=[p[k]*.90+nxt[k]*.10 for k in range(2)]
        for j in range(8):
            t=j/8;edge.append([(1-t)**2*a[k]+2*t*(1-t)*p[k]+t*t*b[k] for k in range(2)])
    cx=.078;cz=1.235;v=[];f=[];n=len(edge)
    for r in [1.,.96,.82,.60,.33,.08]:
        for x,z in edge:
            xx=cx+(x-cx)*r;zz=cz+(z-cz)*r
            dy=.019*(1-r*r)+.007*sin(3*math.atan2(zz-cz,xx-cx))*r*(1-r)
            v.append((s*xx,-.198-dy,zz))
    for k in range(5):
        for j in range(n):a=k*n+j;b=k*n+(j+1)%n;f.append((a,b,b+n,a+n))
    v.append((s*cx,-.217,cz));pole=len(v)-1
    for j in range(n):f.append((5*n+j,5*n+(j+1)%n,pole))
    f.append(tuple(reversed(range(n))))
    o=mesh('Bow wing '+label,v,f,'08_DETAILS',CLOTH)
    o['construction']='Soft edged, broad folded triangular wing; not texture detail'
for s,label in [(-1,'R'),(1,'L')]:
    remove('Bow wing '+label);remove('Bow fold '+label);bow_wing(label,s)
checkpoint('continuous-hands-and-domed-toes','Palm-connected fingers, smooth toe domes with planar soles, and broad folded bow geometry')

# Carry source dependencies forward: resume/ itself is excluded from durable snapshots.
scene['job_id']=JOB['job_id'];scene['previous_job_id']='form-v002'
scene['scope']='Geometry only; no textures, no finished UV layout or articulated rig'
for fn in ['reference.webp','base_geometry_source.py']:shutil.copy2(BASE/fn,OUT/fn)
(OUT/'parent_form-v002_source.py').write_text(parent)
current=Path(__file__).read_text();(OUT/'geometry_source.py').write_text(current)
for name,text in [('REFINE_form-v003.py',current),('REFINE_form-v002.py',parent)]:
    block=bpy.data.texts.get(name) or bpy.data.texts.new(name);block.clear();block.write(text)
assert hashlib.sha256((OUT/'reference.webp').read_bytes()).hexdigest()=='c878b9f1522a412c8b1174333ac456939307f3e048aea2b86120ef388d5aeaf0'
bpy.context.view_layer.update()
geos=[o for o in scene.objects if o.type in {'MESH','CURVE'} and not o.hide_render]
points=[o.matrix_world@Vector(c) for o in geos for c in o.bound_box]
lo=[min(v[k] for v in points) for k in range(3)];hi=[max(v[k] for v in points) for k in range(3)]
required={'Head continuous casing':1,'Hand continuous ':2,'Ear outer ':2,'Eye ':2,'Lower tooth ':10,'Upper tooth ':10,'Whisker ':6,'Toe cap ':6,'Button ':2,'Bow wing ':2}
counts={k:sum(o.name.startswith(k) for o in geos) for k in required}
finite=all(math.isfinite(a) for o in geos if o.type=='MESH' for v in o.data.vertices for a in v.co)
closed={}
for name in ['Head continuous casing','Hand continuous R','Hand continuous L','Ear outer R','Ear outer L']:
    bm=bmesh.new();bm.from_mesh(bpy.data.objects[name].data)
    closed[name]={'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges)};bm.free()
kept={n:fingerprint(bpy.data.objects[n])==h for n,h in kept_before.items()}
checks={'finite_coordinates':finite,'required_parts':counts==required,'closed_revised_shells':all(v['nonmanifold_edges']==0 for v in closed.values()),'preserved_unaffected_parts':all(kept.values()),'height_range':2.17<hi[2]-lo[2]<2.25,'span_range':2.05<hi[0]-lo[0]<2.18,'no_texture_nodes':not any(n.type=='TEX_IMAGE' for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes)}
audit={'job_id':JOB['job_id'],'pass':all(checks.values()),'checks':checks,'bounds_min':lo,'bounds_max':hi,'dimensions_m':[hi[k]-lo[k] for k in range(3)],'required_counts':counts,'closed_shell_checks':closed,'preserved_parts':kept,'objects':len(geos),'vertices':sum(len(o.data.vertices) for o in geos if o.type=='MESH'),'polygons':sum(len(o.data.polygons) for o in geos if o.type=='MESH'),'visual_review':'pending exact new images','limitations':['Reconstruction from 2D views, not original topology','No finished texture/UV/rig','Unseen internal geometry is inferred']}
(OUT/'geometry_audit.json').write_text(json.dumps(audit,indent=2))
(OUT/'lineage.json').write_text(json.dumps({'parent_job':'form-v002','parent_blend_sha256':'f028acd02a8dd1ddd57f64d260e75fb50382151c72668cb1ea0fec39bc8f1f4f','parent_source_sha256':hashlib.sha256(parent.encode()).hexdigest(),'preserved_parts':kept,'changes':'C-shaped cheek/jaw wall, rounded socket edges, C2 skull and ear surfaces, open-bottom ear channels, continuous finger roots, analytic domed toes, broad folded bow'},indent=2))
assert audit['pass'],json.dumps(audit)
bpy.ops.object.select_all(action='DESELECT')
checkpoint('geometry-v003','Actual geometry audit passed; exact-image visual review remains required')
