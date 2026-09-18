"""Reference-driven, geometry-only rabbit. Units m; front -Y. No texture generation."""
import bpy, bmesh, math, json, hashlib, shutil
from pathlib import Path
from mathutils import Vector
from math import sin, cos, pi, sqrt

OUT = Path(OUTPUT_DIR)
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
scene['project_id'] = JOB['project_id']
scene['job_id'] = JOB['job_id']
scene['scope'] = 'Geometry only; neutral inspection materials, no texture maps'
scene['reference_scale_px_per_m'] = 300.0
scene['front_axis'] = '-Y'
COL = {}
for name in ['01_BODY','02_HEAD','03_EARS','04_ARMS','05_HANDS','06_LEGS','07_FEET','08_DETAILS','09_INTERNAL','10_REFERENCE']:
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    COL[name] = c

def material(name, value, roughness=.68, metallic=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (value,value,value,1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (value,value,value,1)
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Metallic'].default_value = metallic
    return m

SHELL = material('Clay | shell', .48)
PANEL = material('Clay | face and panel', .61)
INNER = material('Clay | inner ear', .24)
DARK = material('Inspection | internal', .028, .48)
EYE = material('Inspection | eyes and nose', .012, .19)
CLOTH = material('Inspection | bow tie', .055, .82)
TOOTH = material('Clay | teeth', .63, .58)
METAL = material('Inspection | connectors', .13, .36, .35)


def place(o, name, col, mat=SHELL):
    o.name = name
    for c in list(o.users_collection): c.objects.unlink(o)
    COL[col].objects.link(o)
    if mat:
        o.data.materials.clear()
        o.data.materials.append(mat)
    o['part'] = name
    o['geometry_only'] = True
    if o.type == 'MESH':
        for p in o.data.polygons: p.use_smooth = True
    return o


def mesh(name, vertices, faces, col, mat=SHELL):
    me = bpy.data.meshes.new(name + 'Mesh')
    me.from_pydata(vertices, [], faces)
    me.update()
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    scene.collection.objects.link(o)
    return place(o,name,col,mat)


def apply(o, modifier):
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    o.select_set(False)


def ball(name, loc, scale, col, mat=SHELL, seg=48, rings=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=loc)
    o = bpy.context.object
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return place(o,name,col,mat)


def cylinder(name, a, b, radius, col='09_INTERNAL', mat=METAL, vertices=48):
    a,b=Vector(a),Vector(b)
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=(b-a).length, location=(a+b)/2)
    o=bpy.context.object
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    bevel=o.modifiers.new('Small manufactured edge','BEVEL');bevel.width=.002;bevel.segments=3
    apply(o,bevel)
    return place(o,name,col,mat)


def interp(profile, density=6):
    # Shape-preserving cubic Hermite interpolation, no scipy dependency.
    xs=[r[0] for r in profile]; dim=len(profile[0])-1
    slopes=[]
    for j in range(dim):
        ds=[(profile[i+1][j+1]-profile[i][j+1])/(xs[i+1]-xs[i]) for i in range(len(xs)-1)]
        ms=[ds[0]]
        for i in range(1,len(xs)-1):
            a,b=ds[i-1],ds[i]
            if a*b <= 0: ms.append(0.)
            else:
                h0,h1=xs[i]-xs[i-1],xs[i+1]-xs[i]
                w1,w2=2*h1+h0,h1+2*h0
                ms.append((w1+w2)/(w1/a+w2/b))
        ms.append(ds[-1]);slopes.append(ms)
    out=[]
    for i in range(len(xs)-1):
        h=xs[i+1]-xs[i]
        for k in range(density):
            t=k/density;t2=t*t;t3=t2*t
            v=[xs[i]+h*t]
            for j in range(dim):
                a,b=profile[i][j+1],profile[i+1][j+1]
                v.append((2*t3-3*t2+1)*a+(t3-2*t2+t)*h*slopes[j][i]+(-2*t3+3*t2)*b+(t3-t2)*h*slopes[j][i+1])
            out.append(v)
    out.append(list(profile[-1]))
    return out


def spow(x,p): return math.copysign(abs(x)**p,x)


def loft(name, profile, col, mat=SHELL, exponent=2.5, n=64, transform=None, density=6):
    rows=interp(profile,density);v=[];f=[]
    for z,rx,yf,yb in rows:
        for j in range(n):
            t=2*pi*j/n
            p=(rx*spow(cos(t),2/exponent),(yf+yb)/2+(yb-yf)/2*spow(sin(t),2/exponent),z)
            v.append(transform(p) if transform else p)
    for i in range(len(rows)-1):
        for j in range(n):
            a=i*n+j;b=i*n+(j+1)%n
            f.append((a,b,b+n,a+n))
    f.append(tuple(reversed(range(n))))
    f.append(tuple((len(rows)-1)*n+j for j in range(n)))
    return mesh(name,v,f,col,mat)


def boolean(o, cutter, label='Carved geometry'):
    mod=o.modifiers.new(label,'BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
    apply(o,mod)
    bpy.data.objects.remove(cutter,do_unlink=True)
    if len(o.data.vertices)<8: raise RuntimeError('Boolean erased '+o.name)


def hollow(o, thickness=.007):
    pts=[v.co.copy() for v in o.data.vertices]
    lo=Vector(tuple(min(p[k] for p in pts) for k in range(3)))
    hi=Vector(tuple(max(p[k] for p in pts) for k in range(3)))
    center=(lo+hi)/2
    factors=[max(.5,1-2*thickness/(hi[k]-lo[k])) for k in range(3)]
    me=o.data.copy()
    for v in me.vertices:
        v.co=Vector(tuple(center[k]+(v.co[k]-center[k])*factors[k] for k in range(3)))
    inner=bpy.data.objects.new('_hollow_cutter',me);scene.collection.objects.link(inner)
    boolean(o,inner,'True shell interior')
    o['approx_shell_thickness_m']=thickness


def prism(name, outline, ya, yb):
    n=len(outline)
    v=[(x,y,z) for y in (ya,yb) for x,z in outline]
    f=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    f += [(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
    return mesh(name,v,f,'09_INTERNAL',None)


def tube(name, points, r1, r2, col, mat=SHELL, sides=16):
    ps=[Vector(p) for p in points];v=[];f=[]
    for i,p in enumerate(ps):
        tangent=(ps[min(i+1,len(ps)-1)]-ps[max(0,i-1)]).normalized()
        ref=Vector((0,1,0))
        if abs(tangent.dot(ref))>.94: ref=Vector((0,0,1))
        u=(ref-tangent*tangent.dot(ref)).normalized();w=tangent.cross(u).normalized()
        a=r1[i] if isinstance(r1,list) else r1;b=r2[i] if isinstance(r2,list) else r2
        for j in range(sides):
            q=p+a*cos(2*pi*j/sides)*u+b*sin(2*pi*j/sides)*w;v.append(tuple(q))
    for i in range(len(ps)-1):
        for j in range(sides):
            a=i*sides+j;b=i*sides+(j+1)%sides;f.append((a,b,b+sides,a+sides))
    f += [tuple(reversed(range(sides))),tuple((len(ps)-1)*sides+j for j in range(sides))]
    return mesh(name,v,f,col,mat)


def curve(name, points, radius, col='08_DETAILS', mat=DARK):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=16
    cu.bevel_depth=radius;cu.bevel_resolution=3;cu.use_fill_caps=True
    s=cu.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
    for b,p in zip(s.bezier_points,points):
        b.co=p;b.handle_left_type='AUTO';b.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,cu);scene.collection.objects.link(o)
    return place(o,name,col,mat)


def fused(name, objects, col, mat=SHELL, voxel=.003):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.object.join();o=bpy.context.object
    r=o.modifiers.new('Continuous sculpted shell','REMESH');r.mode='VOXEL';r.voxel_size=voxel;r.use_smooth_shade=True
    apply(o,r)
    s=o.modifiers.new('Surface relaxation','SMOOTH');s.factor=.48;s.iterations=4;apply(o,s)
    return place(o,name,col,mat)


def pillow(name, outline, y, depth, col, mat):
    n=len(outline);cx=sum(p[0] for p in outline)/n;cz=sum(p[1] for p in outline)/n
    v=[];f=[]
    for scale,dy in [(1.,.008),(1.,0.),(.84,-depth*.62),(.42,-depth*.94)]:
        v += [(cx+(x-cx)*scale,y+dy,cz+(z-cz)*scale) for x,z in outline]
    for k in range(3):
        for j in range(n):f.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
    v.append((cx,y-depth,cz));pole=len(v)-1
    for j in range(n):f.append((3*n+j,3*n+(j+1)%n,pole))
    f.append(tuple(reversed(range(n))))
    return mesh(name,v,f,col,mat)

# Barrel torso: the silhouette is lofted from both orthographic references.
body_profile=[(.748,.199,-.143,.163),(.754,.236,-.176,.187),(.768,.251,-.193,.202),(.82,.255,-.218,.208),(.94,.255,-.244,.207),(1.06,.246,-.233,.189),(1.17,.235,-.207,.170),(1.26,.224,-.169,.139),(1.31,.203,-.139,.106),(1.342,.143,-.106,.081),(1.36,.083,-.075,.064),(1.365,.018,-.021,.023)]
body=loft('Torso outer casing',body_profile,'01_BODY',exponent=2.55)
body['reference']='front 323:476, side 958:1094'
# Thin fitted belly insert, not a floating plaque.
rows=interp(body_profile,12)
def body_at(z):
    for a,b in zip(rows,rows[1:]):
        if a[0]<=z<=b[0]:
            t=(z-a[0])/(b[0]-a[0]);return [a[j]*(1-t)+b[j]*t for j in range(1,4)]
    return rows[0][1:]
panel_profile=[(.766,.150),(.781,.178),(.86,.195),(1.01,.186),(1.15,.158),(1.25,.111),(1.315,.076)]
pr=interp(panel_profile,9);v=[];f=[];nx=40
for z,w in pr:
    rx,yf,yb=body_at(z)
    for j in range(nx+1):
        x=w*(2*j/nx-1)
        y=(yf+yb)/2-(yb-yf)/2*max(0.,1-(abs(x)/rx)**2.55)**(1/2.55)-.0015
        v.append((x,y,z))
for i in range(len(pr)-1):
    for j in range(nx):
        a=i*(nx+1)+j;f.append((a,a+1,a+nx+2,a+nx+1))
panel=mesh('Fitted belly panel',v,f,'01_BODY',PANEL)
so=panel.modifiers.new('Thin sewn panel geometry','SOLIDIFY');so.thickness=.0015;so.offset=0;apply(panel,so)
ball('Tail',(0,.240,.836),(.067,.063,.066),'01_BODY',PANEL)
cylinder('Neck connector',(0,-.020,1.336),(0,-.020,1.404),.073)

# Skull, cheek and brow volumes are unified before cavities are cut.
hp=[(1.370,.135,-.117,.074),(1.385,.168,-.154,.111),(1.426,.184,-.181,.132),(1.49,.195,-.197,.143),(1.558,.194,-.199,.145),(1.62,.181,-.200,.137),(1.678,.159,-.173,.117),(1.719,.120,-.139,.088),(1.742,.066,-.090,.051),(1.750,.009,-.033,-.018)]
headbits=[loft('_cranium',hp,'02_HEAD',exponent=2.15)]
for s in (-1,1):
    headbits.append(ball('_cheek',(s*.151,-.151,1.515),(.075,.091,.074),'02_HEAD'))
    headbits.append(ball('_orbital_carrier',(s*.065,-.181,1.592),(.070,.065,.079),'02_HEAD'))
    path=[(s*.102,-.248,1.492),(s*.146,-.237,1.509),(s*.186,-.204,1.527)]
    headbits.append(tube('_smile_ridge',path,.026,.020,'02_HEAD'))
head=fused('Head continuous casing',headbits,'02_HEAD',SHELL,.0026)
boolean(head,ball('_mouth_cutter',(0,-.219,1.407),(.177,.224,.081),'09_INTERNAL',None),'Open mouth, real volume')
for s,label in [(-1,'R'),(1,'L')]:
    boolean(head,ball('_eye_cutter',(s*.065,-.232,1.592),(.052,.071,.060),'09_INTERNAL',None),'Recessed orbital socket '+label)
    ball('Eye '+label,(s*.065,-.195,1.591),(.043,.043,.048),'02_HEAD',EYE)
# Future face material zone is assigned by real surface position, never an image map.
head.data.materials.append(PANEL)
for p in head.data.polygons:
    c=p.center
    if c.y < -.145 and abs(c.x)<.214:
        brow=1.600+.067*math.exp(-((abs(c.x)-.067)/.06)**2)
        if 1.451<c.z<brow:p.material_index=1
# Independent paired upper muzzle cushions.
for s,label in [(-1,'R'),(1,'L')]:
    pad=ball('Muzzle cushion '+label,(s*.050,-.281,1.488),(.077,.061,.049),'02_HEAD',PANEL)
    # Gentle lower flattening retains the split, plush-like lobes.
    for vert in pad.data.vertices:
        if vert.co.z < -.036:vert.co.z=-.036+(vert.co.z+.036)*.60
# U-shaped jaw, with the side profile sweeping back to the cheek hinges.
jawpath=[]
for i in range(97):
    t=pi*i/96
    jawpath.append((.192*cos(t),-.151-.142*sin(t)**.72,1.495-.160*sin(t)))
jaw=tube('Lower jaw U shell',jawpath,.033,.027,'02_HEAD',PANEL,24)
ball('Mouth internal baffle',(0,-.090,1.410),(.151,.070,.077),'09_INTERNAL',DARK)
for s,label in [(-1,'R'),(1,'L')]:
    cylinder('Jaw hinge '+label,(s*.164,-.110,1.423),(s*.192,-.110,1.423),.022)
# Rounded inverted-triangle nose with a volumetric front, rather than a black decal.
nose_outline=[(-.040,1.532),(-.022,1.540),(.020,1.540),(.042,1.531),(.035,1.514),(.010,1.491),(0,1.486),(-.012,1.493),(-.035,1.515)]
pillow('Nose',nose_outline,-.333,.030,'02_HEAD',EYE)
curve('Muzzle center split',[(0,-.339,1.491),(0,-.342,1.473),(0,-.335,1.452)],.0020,'02_HEAD',DARK)
# Ten small domed teeth in each arch; not elongated rabbit incisors.
for row in ['Lower','Upper']:
    for i in range(10):
        t=-1.25+2.5*i/9
        x=.144*sin(t)
        if row=='Lower':
            y=-.162-.132*cos(t);base=1.336+.061*sin(t)**2
            z=base+.018;sz=.025-.004*abs(sin(t));sx=.018-.003*abs(sin(t))
        else:
            y=-.142-.126*cos(t);z=1.442+.026*sin(t)**2;sz=.021;sx=.016
        o=ball(f'{row} tooth {i+1:02d}',(x,y,z),(sx,.020,sz),'02_HEAD',TOOTH,32,20)
        o.rotation_euler[2]=-t
        if row=='Lower':
            for ve in o.data.vertices:
                if ve.co.z<-.010:ve.co.z=-.010+(ve.co.z+.010)*.32

# Ears: rounded tapered outer shells and carved front channels.
for s,label in [(-1,'R'),(1,'L')]:
    cx=s*.096
    def ear_y(z):return -.028-.075*((z-1.765)/.445)
    ear_spec=[(1.765,.048),(1.790,.051),(1.87,.058),(1.97,.066),(2.067,.073),(2.125,.073),(2.167,.060),(2.194,.038),(2.207,.010),(2.208,.001)]
    ep=[(z,w,ear_y(z)-.040,ear_y(z)+.041) for z,w in ear_spec]
    ear=loft('Ear outer '+label,ep,'03_EARS',SHELL,2.65,64,lambda p:(p[0]+cx,p[1],p[2]))
    inn=[(1.782,.025),(1.81,.028),(1.93,.034),(2.048,.037),(2.080,.033),(2.102,.023),(2.112,.005),(2.113,.001)]
    cutp=[(z,w,ear_y(z)-.18,ear_y(z)+.010) for z,w in inn]
    cutter=loft('_ear_channel',cutp,'09_INTERNAL',None,2.2,48,lambda p:(p[0]+cx,p[1],p[2]))
    boolean(ear,cutter,'Recessed inner channel')
    panelp=[(z,w*.96,ear_y(z)+.0105,ear_y(z)+.0135) for z,w in inn]
    loft('Ear recessed insert '+label,panelp,'03_EARS',INNER,2.2,48,lambda p:(p[0]+cx,p[1],p[2]))
    cylinder('Ear stem '+label,(cx,-.024,1.740),(cx,-.024,1.780),.011)
    pts=[]
    for k in range(100):
        t=5*pi*k/99;pts.append((cx+.015*cos(t),-.024+.015*sin(t),1.742+.026*k/99))
    curve('Ear spring '+label,pts,.0022,'09_INTERNAL',METAL)
checkpoint('head-body-ears','Continuous head, carved sockets, open jaw, torso and hollow ear channels')

# T-pose arm shells. Longitudinal cross sections are rounded rectangular, not spheres.
arm_objs={}
for s,label in [(-1,'R'),(1,'L')]:
    z=1.239
    cylinder('Shoulder axle '+label,(s*.202,0,z),(s*.280,0,z),.055)
    upper=[(.244,.060,-.067,.067),(.254,.079,-.081,.081),(.282,.088,-.086,.086),(.362,.087,-.085,.085),(.445,.078,-.078,.078),(.477,.073,-.071,.071),(.484,.057,-.057,.057)]
    lower=[(.495,.063,-.064,.064),(.504,.077,-.078,.078),(.560,.076,-.078,.078),(.673,.074,-.076,.076),(.722,.069,-.070,.070),(.734,.056,-.058,.058)]
    trans=lambda p,s=s:(s*p[2],p[1],z+p[0])
    up=loft('Upper arm shell '+label,upper,'04_ARMS',SHELL,2.8,56,trans)
    lo=loft('Forearm shell '+label,lower,'04_ARMS',SHELL,2.9,56,trans)
    arm_objs[label]=up
    cylinder('Elbow joint '+label,(s*.469,0,z),(s*.512,0,z),.058)
    cylinder('Wrist joint '+label,(s*.720,0,z),(s*.770,0,z),.043)
    # Broad, flattened palm and three distinct rounded finger tips.
    palm=ball('Palm '+label,(s*.823,-.002,1.244),(.090,.090,.047),'05_HANDS',SHELL)
    for j,(yy,length) in enumerate([(-.056,.156),(0,.169),(.055,.143)]):
        a=.881;b=a+length
        profile=[(a,.027,yy-.030,yy+.030),(a+.022,.033,yy-.032,yy+.032),(b-.036,.031,yy-.031,yy+.031),(b-.012,.023,yy-.024,yy+.024),(b,.001,yy-.001,yy+.001)]
        loft('Finger '+label+str(j+1),profile,'05_HANDS',SHELL,2.25,40,lambda p,s=s:(s*p[2],p[1],1.245+p[0]),5)
    thumb=ball('Thumb '+label,(s*.792,-.077,1.208),(.047,.044,.040),'05_HANDS',SHELL)
    thumb.rotation_euler[1]=s*.28
# Missing shell at the front/top of the right upper arm.
hollow(arm_objs['R'],.006)
outline=[(-.490,1.345),(-.258,1.345),(-.258,1.271),(-.287,1.268),(-.312,1.289),(-.337,1.282),(-.368,1.301),(-.391,1.292),(-.426,1.308),(-.451,1.301),(-.474,1.318)]
boolean(arm_objs['R'],prism('_arm_break',outline,-.2,.019),'Jagged missing upper-arm shell')
cylinder('Exposed upper arm interior',(-.480,0,1.239),(-.252,0,1.239),.053,mat=DARK)
curve('Upper arm fine fracture',[(-.475,-.045,1.309),(-.450,-.058,1.300),(-.432,-.069,1.291)],.0009,'04_ARMS',DARK)

# Legs with short thighs, long shins and narrow mechanical gaps.
thighs={}
for s,label in [(-1,'R'),(1,'L')]:
    cx=s*.128
    thighp=[(.506,.075,-.074,.079),(.519,.096,-.093,.099),(.577,.100,-.099,.105),(.672,.105,-.104,.110),(.736,.104,-.102,.109),(.745,.092,-.090,.096)]
    thigh=loft('Thigh shell '+label,thighp,'06_LEGS',SHELL,2.85,56,lambda p,cx=cx:(p[0]+cx,p[1]+.007,p[2]))
    thighs[label]=thigh
    shinp=[(.154,.078,-.080,.085),(.163,.096,-.096,.103),(.181,.099,-.100,.109),(.28,.098,-.101,.111),(.410,.096,-.098,.108),(.479,.093,-.093,.102),(.492,.078,-.079,.087)]
    loft('Shin shell '+label,shinp,'06_LEGS',SHELL,2.9,56,lambda p,cx=cx:(p[0]+cx,p[1]+.008,p[2]))
    cylinder('Hip connector '+label,(cx,.014,.716),(cx,.014,.782),.057)
    cylinder('Knee connector '+label,(cx,.014,.476),(cx,.014,.532),.048)
    cylinder('Ankle connector '+label,(cx,.015,.126),(cx,.015,.174),.050)
    # Small lower-shell roll, visible in all orthographic views.
    loft('Ankle cuff '+label,[(.143,.079,-.080,.087),(.150,.096,-.097,.104),(.157,.095,-.096,.103),(.165,.084,-.085,.092)],'06_LEGS',SHELL,2.9,56,lambda p,cx=cx:(p[0]+cx,p[1]+.008,p[2]),3)
# The two visible breaks occur on different faces, consistent with the supplied views.
hollow(thighs['R'],.007)
frontbreak=[(-.250,.770),(-.047,.770),(-.047,.630),(-.089,.630),(-.112,.651),(-.159,.647),(-.189,.665),(-.222,.658),(-.250,.682)]
boolean(thighs['R'],prism('_front_thigh_break',frontbreak,-.25,.025),'Front thigh missing panel')
cylinder('Right thigh interior',(-.128,.014,.533),(-.128,.014,.748),.067,mat=DARK)
hollow(thighs['L'],.007)
backbreak=[(.047,.770),(.250,.770),(.250,.650),(.222,.649),(.207,.674),(.179,.662),(.157,.687),(.117,.690),(.096,.715),(.047,.707)]
boolean(thighs['L'],prism('_back_thigh_break',backbreak,.045,.25),'Rear thigh missing panel')
cylinder('Left thigh interior',(.128,.014,.533),(.128,.014,.748),.067,mat=DARK)

# Broad low feet, narrower heel and three rounded toe caps per foot.
for s,label in [(-1,'R'),(1,'L')]:
    cx=s*.155
    # Foot section axes: longitudinal Y, transverse X, vertical Z.
    fp=[(-.284,.096,.010,.059),(-.266,.140,.004,.091),(-.205,.160,.003,.117),(-.110,.161,.004,.138),(.007,.136,.005,.138),(.093,.105,.006,.102),(.129,.075,.011,.072),(.135,.023,.025,.049)]
    foot=loft('Foot base '+label,fp,'07_FEET',SHELL,2.75,64,lambda p,cx=cx:(p[0]+cx,p[2],p[1]),5)
    for j,dx in enumerate([-.105,0,.105]):
        toe=ball('Toe cap '+label+str(j+1),(cx+dx,-.230,.056),(.056,.077,.060),'07_FEET',PANEL,40,24)
        for ve in toe.data.vertices:
            if ve.co.z<-.050:ve.co.z=-.050+(ve.co.z+.050)*.12
        toe['separate_future_material_zone']=True

# Bow tie: volumetric folded wings and knot. Two buttons, not three.
wing=[(.014,1.245),(.052,1.262),(.139,1.296),(.123,1.240),(.128,1.159),(.085,1.181),(.041,1.207)]
for s,label in [(-1,'R'),(1,'L')]:
    pillow('Bow wing '+label,[(s*x,z) for x,z in wing],-.197,.024,'08_DETAILS',CLOTH)
    curve('Bow fold '+label,[(s*.021,-.220,1.239),(s*.055,-.222,1.235),(s*.102,-.206,1.215)],.0012,'08_DETAILS',CLOTH)
ball('Bow knot',(0,-.223,1.239),(.025,.018,.023),'08_DETAILS',CLOTH)
for i,z in enumerate([1.162,1.105]):
    rx,yf,yb=body_at(z)
    button=ball('Button '+str(i+1),(0,yf-.012,z),(.015,.008,.016),'08_DETAILS',EYE,32,20)
for s,label in [(-1,'R'),(1,'L')]:
    for i,(endz,endy) in enumerate([(1.509,-.258),(1.465,-.255),(1.417,-.253)]):
        curve('Whisker '+label+str(i+1),[(s*.097,-.332,1.487-i*.009),(s*.153,-.300,1.493-i*.022),(s*.213,endy,endz)],.0011,'08_DETAILS',DARK)

# Reference is packed but not used as a texture or included in render bounds.
ref=Path(INPUT_DIR)/'reference.webp'
assert hashlib.sha256(ref.read_bytes()).hexdigest()=='c878b9f1522a412c8b1174333ac456939307f3e048aea2b86120ef388d5aeaf0'
shutil.copy2(ref,OUT/'reference.webp')
image=bpy.data.images.load(str(ref),check_existing=True);image.pack()
empty=bpy.data.objects.new('Reference | supplied turnaround',None);COL['10_REFERENCE'].objects.link(empty)
empty.empty_display_type='IMAGE';empty.data=image;empty.empty_display_size=6.827
empty.location=(2.10,.50,1.10);empty.rotation_euler=(pi/2,0,0);empty.hide_render=True;empty.hide_viewport=True
# Include editable generator source in the scene and the durable output snapshot.
source=Path(__file__).read_text(encoding='utf-8')
text=bpy.data.texts.new('GEOMETRY_SOURCE.py');text.write(source)
shutil.copy2(Path(__file__),OUT/'geometry_source.py')
readme=bpy.data.texts.new('READ_ME')
readme.write('rabbit-geometry-20260918 / geometry only. Front -Y, +Z up, metric. Named separate casing, jaw, ears, eyes, teeth, digits, bow and connectors. Neutral inspection materials are not finished textures. User-provided reference image packed. No rig or finished UV layout. See GitHub project reviews for the precise accepted revision.\n')
# Geometry audit uses the actual scene after all booleans, not planned object counts.
bpy.context.view_layer.update()
geometry=[o for o in scene.objects if o.type in {'MESH','CURVE'} and not o.hide_render]
pts=[o.matrix_world@Vector(c) for o in geometry for c in o.bound_box]
lo=[min(p[k] for p in pts) for k in range(3)];hi=[max(p[k] for p in pts) for k in range(3)]
invalid=[];empty_mesh=[]
for o in geometry:
    if o.type=='MESH':
        if len(o.data.polygons)==0:empty_mesh.append(o.name)
        if any(not math.isfinite(a) for ve in o.data.vertices for a in ve.co):invalid.append(o.name)
counts={prefix:sum(o.name.startswith(prefix) for o in geometry) for prefix in ['Ear outer','Eye ','Lower tooth','Upper tooth','Whisker ','Finger ','Thumb ','Toe cap','Button ','Bow wing','Thigh shell','Shin shell']}
expected={'Ear outer':2,'Eye ':2,'Lower tooth':10,'Upper tooth':10,'Whisker ':6,'Finger ':6,'Thumb ':2,'Toe cap':6,'Button ':2,'Bow wing':2,'Thigh shell':2,'Shin shell':2}
checks={'finite_coordinates':not invalid,'nonempty_meshes':not empty_mesh,'required_parts':counts==expected,'height_range':2.17<hi[2]-lo[2]<2.25,'span_range':2.06<hi[0]-lo[0]<2.18,'no_texture_nodes':not any(n.type=='TEX_IMAGE' for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes)}
audit={'job_id':JOB['job_id'],'checks':checks,'pass':all(checks.values()),'bounds_min':lo,'bounds_max':hi,'dimensions_m':[hi[k]-lo[k] for k in range(3)],'counts':counts,'objects':len(geometry),'vertices':sum(len(o.data.vertices) for o in geometry if o.type=='MESH'),'polygons':sum(len(o.data.polygons) for o in geometry if o.type=='MESH'),'invalid':invalid,'empty':empty_mesh,'limitations':['2D reconstruction, not original topology','Neutral material zones only; no finished textures, UV layout or rig','Hidden structure inferred']}
(OUT/'geometry_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
assert audit['pass'],json.dumps(audit)
# A useful opening viewport; do not save the model with helper objects selected.
bpy.ops.object.select_all(action='DESELECT')
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.clip_end=100
            area.spaces.active.region_3d.view_distance=3.2
            area.spaces.active.region_3d.view_location=Vector((0,0,1.12))
checkpoint('geometry-final','Geometry only: all named parts, actual cavities, shell breaks and finite-coordinate audit')
