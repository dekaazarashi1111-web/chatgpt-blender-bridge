"""Reference-measured animatronic rabbit, editable shells, internals and PBR surfaces."""
import bpy
import math
import json
import random
import shutil
from pathlib import Path
from mathutils import Vector

random.seed(9181111)
OUT=Path(OUTPUT_DIR)
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for col in list(bpy.data.collections):
    if col.name != 'Collection' and col.users == 0:
        bpy.data.collections.remove(col)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene.unit_settings.scale_length=1.0
scene.render.film_transparent=False
scene.view_settings.view_transform='Standard'
scene.view_settings.look='None'
scene.view_settings.exposure=0
scene.view_settings.gamma=1
COLS={}
for name in ['01_HOUSING','02_FACE','03_EARS','04_HANDS_FEET','05_MECHANISM','06_DAMAGE','07_DETAILS','90_STUDIO','99_REFERENCE']:
    c=bpy.data.collections.new(name); scene.collection.children.link(c); COLS[name]=c

def place(obj,name,group,mat=None):
    obj.name=name
    for c in list(obj.users_collection): c.objects.unlink(obj)
    COLS[group].objects.link(obj)
    if mat is not None and hasattr(obj.data,'materials'): obj.data.materials.append(mat)
    if obj.type=='MESH':
        for p in obj.data.polygons:p.use_smooth=True
    obj['project']='worn-violet-rabbit-20260918'
    return obj

texdir=OUT/'textures';texdir.mkdir(exist_ok=True)
for p in (Path(WORKSPACE_DIR)/'output'/'textures').glob('*.png'):
    if p.name != 'reference.png':shutil.copyfile(p,texdir/p.name)
shutil.copyfile(Path(INPUT_DIR)/'reference.webp',OUT/'reference.webp')
coords=bpy.data.objects.new('Fabric_mapping_0.48m',None);COLS['07_DETAILS'].objects.link(coords)
coords.empty_display_size=.08


def simple(name,color,rough=.7,metal=0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    m.diffuse_color=(*color,1)
    return m


def cloth(name,file):
    m=simple(name,(.12,.08,.11),.85)
    n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    p.inputs['Sheen Weight'].default_value=.11
    p.inputs['Specular IOR Level'].default_value=.24
    c=n.new('ShaderNodeTexCoord');c.object=coords;c.location=(-950,100)
    v=n.new('ShaderNodeVectorMath');v.operation='SCALE';v.inputs[3].default_value=1/.48;v.location=(-750,100)
    l.new(c.outputs['Object'],v.inputs[0])
    def image_node(filename,noncolor,y):
        t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(texdir/filename),check_existing=True)
        if noncolor:t.image.colorspace_settings.name='Non-Color'
        t.projection='BOX';t.projection_blend=.28;t.extension='REPEAT';t.location=(-530,y)
        l.new(v.outputs['Vector'],t.inputs['Vector']);return t
    a=image_node(file,False,320);l.new(a.outputs['Color'],p.inputs['Base Color'])
    r=image_node('cloth_roughness.png',True,80);l.new(r.outputs['Color'],p.inputs['Roughness'])
    h=image_node('cloth_height16.png',True,-170)
    b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=.34;b.inputs['Distance'].default_value=.0021;b.location=(-220,-150)
    l.new(h.outputs['Color'],b.inputs['Height']);l.new(b.outputs['Normal'],p.inputs['Normal'])
    p.location=(50,180)
    m['surface']='short worn textile/coated foam; eroded mottles, microscale weave, no long fur'
    return m

VIOLET=cloth('01_Dusty_violet_worn_textile','violet_albedo.png')
PALE=cloth('02_Chalky_grey_lilac_wear','pale_albedo.png')
INNER=cloth('03_Recessed_dark_plum_ear','ear_albedo.png')
DARK=simple('04_Deep_cavity_charcoal',(.0035,.004,.0043),.96)
METAL=simple('05_Graphite_endoskeleton',(.029,.033,.031),.48,.78)
STEEL=simple('06_Tarnished_joint_edges',(.09,.095,.087),.43,.73)
EYES=simple('07_Black_glass_eyes',(.002,.0025,.0023),.2,.0)
BUTTON=simple('08_Black_bakelite',(.007,.007,.008),.3)
TIE=simple('09_Black_cotton_bow',(.0055,.0053,.006),.92)
TIE.node_tree.nodes.get('Principled BSDF').inputs['Sheen Weight'].default_value=.18
TEETH=simple('10_Aged_dull_ivory',(.255,.273,.145),.65)
TN=TEETH.node_tree.nodes;TL=TEETH.node_tree.links
nt=TN.new('ShaderNodeTexNoise');nt.inputs['Scale'].default_value=160
bt=TN.new('ShaderNodeBump');bt.inputs['Strength'].default_value=.18;bt.inputs['Distance'].default_value=.0007
TL.new(nt.outputs['Fac'],bt.inputs['Height']);TL.new(bt.outputs['Normal'],TN.get('Principled BSDF').inputs['Normal'])
THREAD=simple('11_Faded_frayed_edges',(.12,.087,.107),.96)


def spow(x,e):return math.copysign(abs(x)**e,x)


def mesh_obj(name,verts,faces,mat,group,uvs=None):
    me=bpy.data.meshes.new(name+'_mesh');me.from_pydata(verts,[],faces);me.update()
    ob=bpy.data.objects.new(name,me);COLS[group].objects.link(ob)
    if mat:me.materials.append(mat)
    for poly in me.polygons:poly.use_smooth=True
    if uvs:
        uv=me.uv_layers.new(name='UVMap')
        for poly in me.polygons:
            for li in poly.loop_indices:uv.data[li].uv=uvs[me.loops[li].vertex_index]
    ob['project']='worn-violet-rabbit-20260918'
    return ob


def rounded(name,loc,scale,mat,group='01_HOUSING',ez=.6,ex=.75,n=64,m=36,damage=None):
    verts=[(loc[0],loc[1],loc[2]-scale[2])];uvs=[(.5,0)];faces=[]
    for k in range(1,m):
        t=-math.pi/2+math.pi*k/m
        for j in range(n):
            a=2*math.pi*j/n
            x=scale[0]*spow(math.cos(t),ez)*spow(math.cos(a),ex)
            y=scale[1]*spow(math.cos(t),ez)*spow(math.sin(a),ex)
            z=scale[2]*spow(math.sin(t),ez)
            if mat in (VIOLET,PALE,INNER):
                q=1+.004*math.sin(19*a+1.7)*math.cos(13*t)
                x*=q;y*=q
            verts.append((loc[0]+x,loc[1]+y,loc[2]+z));uvs.append((j/n,k/m))
    top=len(verts);verts.append((loc[0],loc[1],loc[2]+scale[2]));uvs.append((.5,1))
    for j in range(n):faces.append((0,1+(j+1)%n,1+j))
    for k in range(m-2):
        for j in range(n):
            f=(1+k*n+j,1+k*n+(j+1)%n,1+(k+1)*n+(j+1)%n,1+(k+1)*n+j)
            center=sum((Vector(verts[i]) for i in f),Vector())/4
            if damage is None or not damage(center):faces.append(f)
    for j in range(n):faces.append((top,1+(m-2)*n+j,1+(m-2)*n+(j+1)%n))
    ob=mesh_obj(name,verts,faces,mat,group,uvs)
    if damage:
        mod=ob.modifiers.new('Real_torn_shell_thickness','SOLIDIFY');mod.thickness=.007;mod.offset=-1
        ob['intentional_open_surface']='torn fabric shell; solidify retains wall thickness'
    return ob


def ell(name,loc,scale,mat,group='02_FACE',n=48):
    return rounded(name,loc,scale,mat,group,1,1,n=n,m=32)


def cylinder(name,a,b,r,mat,group='05_MECHANISM',vertices=40):
    vec=Vector(b)-Vector(a);mid=(Vector(a)+Vector(b))/2
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=vec.length,location=mid)
    ob=place(bpy.context.object,name,group,mat);ob.rotation_euler=vec.to_track_quat('Z','Y').to_euler()
    bev=ob.modifiers.new('Machined_edge','BEVEL');bev.width=min(.0025,r*.14);bev.segments=2
    return ob


def curve(name,pts,r,mat,group='07_DETAILS',cyclic=False):
    cu=bpy.data.curves.new(name+'_curve','CURVE');cu.dimensions='3D';cu.resolution_u=12
    s=cu.splines.new('POLY');s.points.add(len(pts)-1)
    for p,co in zip(s.points,pts):p.co=(*co,1)
    s.use_cyclic_u=cyclic;cu.bevel_depth=r;cu.bevel_resolution=3
    ob=bpy.data.objects.new(name,cu);COLS[group].objects.link(ob);cu.materials.append(mat)
    return ob


def ring(name,center,rx,ry,r,mat,axis='Z',group='07_DETAILS'):
    pts=[]
    for j in range(96):
        a=2*math.pi*j/96
        u=rx*spow(math.cos(a),.78);v=ry*spow(math.sin(a),.78)
        d=(u,v,0) if axis=='Z' else ((0,u,v) if axis=='X' else (u,0,v))
        pts.append(tuple(center[i]+d[i] for i in range(3)))
    return curve(name,pts,r,mat,group,True)

# Torso: measured tapered shell, curved front and nearly straight back.
profiles=[(.895,.263,.224,.227),(.911,.289,.249,.241),(1.00,.300,.269,.245),
          (1.17,.288,.266,.239),(1.34,.270,.230,.230),(1.48,.252,.183,.213),
          (1.545,.216,.157,.187),(1.566,.168,.144,.155)]

def torso_r(z):
    for i in range(len(profiles)-1):
        a,b=profiles[i:i+2]
        if z<=b[0]:
            f=max(0,min(1,(z-a[0])/(b[0]-a[0])))
            return tuple(a[j]*(1-f)+b[j]*f for j in (1,2,3))
    return profiles[-1][1:]

verts=[];faces=[];uvs=[]
for k in range(81):
    z=profiles[0][0]+(profiles[-1][0]-profiles[0][0])*k/80
    rx,front,back=torso_r(z)
    for j in range(96):
        a=2*math.pi*j/96;s=math.sin(a);x=rx*spow(math.cos(a),.72)
        y=(front if s<0 else back)*spow(s,.86)
        verts.append((x,y,z));uvs.append((j/96,k/80))
for k in range(80):
    for j in range(96):faces.append((k*96+j,k*96+(j+1)%96,(k+1)*96+(j+1)%96,(k+1)*96+j))
faces.append(tuple(reversed(range(96))));faces.append(tuple(80*96+j for j in range(96)))
body=mesh_obj('Torso_tapered_housing',verts,faces,VIOLET,'01_HOUSING',uvs)
sub=body.modifiers.new('Soft_shell_transition','SUBSURF');sub.levels=1
# A conforming, nearly flush chest panel; no floating oval badge.
verts=[(0,-torso_r(1.229)[1]-.006,1.229)];uvs=[(.5,.5)];faces=[]
for k in range(1,25):
    rr=k/24
    for j in range(128):
        a=2*math.pi*j/128
        x=.230*rr*spow(math.cos(a),.73)
        z=1.229+.310*rr*spow(math.sin(a),.65)
        rx,f,b=torso_r(z)
        c=min(.99999,abs(x)/rx)**(1/.72)
        y=-f*(max(0,1-c*c)**.5)**.86-.006
        verts.append((x,y,z));uvs.append((.5+x/.48,.5+(z-1.229)/.64))
for j in range(128):faces.append((0,1+j,1+(j+1)%128))
for k in range(23):
    for j in range(128):faces.append((1+k*128+j,1+(k+1)*128+j,1+(k+1)*128+(j+1)%128,1+k*128+(j+1)%128))
bib=mesh_obj('Conforming_pale_belly_panel',verts,faces,PALE,'01_HOUSING',uvs)
solid=bib.modifiers.new('Thin_textile_panel','SOLIDIFY');solid.thickness=.003
rounded('Back_neck_facing',(0,.180,1.527),(.146,.030,.052),PALE,'01_HOUSING',ez=.7,ex=.85)
cylinder('Neck_spindle',(0,.025,1.52),(0,.025,1.649),.080,METAL)
for z in (1.576,1.603,1.625):ring('Neck_bearing_'+str(z),(0,.025,z),.081,.078,.003,STEEL,'Z','05_MECHANISM')

# Limbs and concealed structure.
for s in (-1,1):
    tag='R' if s<0 else 'L'
    x=s*.146
    cylinder(tag+'_hip_spindle',(x,0,.83),(x,0,.93),.048,METAL)
    cylinder(tag+'_leg_internal',(x,0,.18),(x,0,.862),.034,METAL)
    thigh_damage=(lambda p:p.y<-.043 and p.x<-.101 and p.z>.756+.011*math.sin(101*p.x) and p.z<.879) if s<0 else None
    rounded(tag+'_thigh_inner_dark',(x,0,.749),(.096,.074,.145),DARK,'05_MECHANISM',ez=.42,ex=.66)
    rounded(tag+'_upper_leg_shell',(x,0,.743),(.119,.104,.151),VIOLET,ez=.36,ex=.68,damage=thigh_damage)
    rounded(tag+'_shin_shell',(x,0,.385),(.116,.101,.202),VIOLET,ez=.29,ex=.70)
    ell(tag+'_knee_ball',(x,0,.579),(.065,.063,.059),METAL,'05_MECHANISM')
    ring(tag+'_shin_lower_cuff',(x,0,.197),.107,.094,.009,VIOLET)
    ring(tag+'_ankle_bearing',(x,0,.163),.060,.062,.005,STEEL,'Z','05_MECHANISM')
    footx=s*.180
    rounded(tag+'_foot_housing',(footx,-.084,.081),(.193,.229,.079),VIOLET,'04_HANDS_FEET',ez=.52,ex=.67)
    for k in range(3):
        tx=footx+(k-1)*.125
        rounded(tag+'_pale_toe_'+str(k+1),(tx,-.263,.079),(.061,.095,.070),PALE,'04_HANDS_FEET',ez=.60,ex=.92)
    cylinder(tag+'_shoulder_axle',(s*.242,0,1.455),(s*.375,0,1.455),.056,METAL)
    ell(tag+'_shoulder_joint',(s*.327,0,1.455),(.073,.072,.075),DARK,'05_MECHANISM')
    cylinder(tag+'_arm_internal',(s*.327,0,1.455),(s*.915,0,1.455),.034,METAL)
    upper_damage=(lambda p:p.x>-.54 and p.x<-.372 and p.z>1.501+.009*math.sin(104*p.x) and p.y<.028) if s<0 else None
    rounded(tag+'_upper_arm_inner',(s*.463,0,1.455),(.139,.075,.075),DARK,'05_MECHANISM',ez=.5,ex=.4)
    rounded(tag+'_upper_arm_shell',(s*.463,0,1.455),(.144,.096,.097),VIOLET,ez=.55,ex=.36,damage=upper_damage)
    rounded(tag+'_forearm_shell',(s*.751,0,1.455),(.136,.091,.087),VIOLET,ez=.50,ex=.35)
    ell(tag+'_elbow',(s*.609,0,1.455),(.030,.064,.064),METAL,'05_MECHANISM')
    cylinder(tag+'_wrist',(s*.87,0,1.455),(s*.948,0,1.455),.039,METAL)
    ring(tag+'_forearm_end',(s*.879,0,1.455),.086,.081,.004,VIOLET,'X')
    rounded(tag+'_palm',(s*.981,-.002,1.451),(.084,.078,.047),VIOLET,'04_HANDS_FEET',ez=.68,ex=.55)
    for k in range(3):
        yy=(k-1)*.047
        tip=1.246-(.017 if k!=1 else 0)
        cx=(1.035+tip)/2
        finger=rounded(tag+'_mitten_finger_'+str(k+1),(s*cx,yy,1.450),((tip-1.035)/2,.031,.039),VIOLET,'04_HANDS_FEET',ez=.78,ex=.64)
    thumb=rounded(tag+'_thumb',(s*1.012,-.091,1.420),(.061,.044,.049),VIOLET,'04_HANDS_FEET',ez=.90,ex=.80)

ell('Small_round_pale_tail',(0,.284,1.004),(.076,.077,.075),PALE,'04_HANDS_FEET')

# Head: rounded cranial shell and broad cheeks; black eye sockets remain small.
rounded('Head_cranial_shell',(0,.027,1.837),(.246,.228,.229),VIOLET,'02_FACE',ez=.82,ex=.90,n=96,m=64)
for s in (-1,1):
    tag='R' if s<0 else 'L'
    ell(tag+'_purple_cheek',(s*.182,-.132,1.781),(.085,.103,.090),VIOLET)
    ell(tag+'_pale_orbital_surround',(s*.076,-.191,1.885),(.083,.044,.084),PALE)
    ell(tag+'_black_orbital_depth',(s*.076,-.224,1.885),(.055,.019,.060),DARK)
    eye=ell(tag+'_black_eye',(s*.076,-.232,1.884),(.045,.024,.049),EYES)
    ell(tag+'_subtle_pupil',(s*.074,-.254,1.884),(.020,.004,.026),EYES)
    ell(tag+'_muzzle_lobe',(s*.102,-.242,1.780),(.118,.096,.064),PALE)
    ell(tag+'_outer_muzzle_fold',(s*.194,-.197,1.769),(.055,.062,.067),PALE)
ell('Open_mouth_cavity',(0,-.166,1.674),(.188,.087,.106),DARK)
verts=[];faces=[];uv=[]
for i in range(97):
    t=math.pi*i/96
    center=Vector((-.202*math.cos(t),-.196-.072*math.sin(t),1.758-.183*math.sin(t)))
    radial=Vector((-math.cos(t),0,-math.sin(t)))
    for j in range(24):
        a=2*math.pi*j/24
        v=center+radial*(.024*math.cos(a))+Vector((0,.051*math.sin(a),0))
        verts.append(tuple(v));uv.append((i/96,j/24))
for i in range(96):
    for j in range(24):faces.append((i*24+j,i*24+(j+1)%24,(i+1)*24+(j+1)%24,(i+1)*24+j))
faces.append(tuple(reversed(range(24))));faces.append(tuple(96*24+j for j in range(24)))
mesh_obj('Separate_pale_lower_jaw',verts,faces,PALE,'02_FACE',uv)
for upper in (False,True):
    for i in range(9):
        t=-1.28+2.56*i/8
        x=.164*math.sin(t)
        y=-.174-(.115 if upper else .145)*math.cos(t)
        z=(1.714+.030*(1-math.cos(t))) if upper else (1.637+.065*(1-math.cos(t)))
        h=.018 if upper else .022
        tooth=rounded(('Upper' if upper else 'Lower')+'_tooth_%02d'%i,(x,y,z),(.017,.025,h),TEETH,'02_FACE',ez=.65,ex=.75,n=32,m=20)
verts=[(-.052,-.334,1.800),(.052,-.334,1.800),(0,-.348,1.760),(-.043,-.367,1.795),(.043,-.367,1.795),(0,-.378,1.768)]
faces=[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)]
nose=mesh_obj('Soft_black_triangular_nose',verts,faces,BUTTON,'02_FACE')
be=nose.modifiers.new('Rounded_nose_edges','BEVEL');be.width=.016;be.segments=5
no=nose.modifiers.new('Nose_normals','WEIGHTED_NORMAL')
curve('Nose_to_muzzle_division',[(0,-.342,1.772),(0,-.338,1.749),(0,-.330,1.736)],.0028,DARK,'02_FACE')
for s in (-1,1):
    curve('Muzzle_smile_'+str(s),[(0,-.329,1.737),(s*.065,-.329,1.732),(s*.126,-.300,1.743),(s*.180,-.253,1.758)],.0022,DARK,'02_FACE')
    for j in range(3):
        curve('Cheek_crease_%s_%s'%(s,j),[(s*.126,-.321,1.772-j*.013),(s*.171,-.295,1.778-j*.026),(s*.233,-.220,1.786-j*.039)],.0009,METAL,'02_FACE')
    for dx,dz in [(.081,1.788),(.119,1.799),(.131,1.778)]:
        ell('Whisker_root_%s_%s'%(s,dx),(s*dx,-.337 if dx<.12 else -.327,dz),(.0023,.0013,.0023),METAL,n=16)

# Ears are a continuous rim and a genuinely recessed well, with a purple back.
for s in (-1,1):
    tag='R' if s<0 else 'L'
    cx=s*.112;cz=2.338
    cylinder(tag+'_ear_stem',(cx,.02,2.052),(cx,.02,2.100),.020,METAL)
    for zz in (2.070,2.083):ring(tag+'_ear_stem_ring_'+str(zz),(cx,.02,zz),.021,.021,.0025,STEEL,'Z','05_MECHANISM')
    layers=[(.087,.263,.055),(.087,.263,-.019),(.060,.237,-.044),(.044,.208,-.040),(.043,.205,.007)]
    verts=[];faces=[];uvs=[]
    for w,h,depth in layers:
        for j in range(128):
            a=2*math.pi*j/128
            nz=spow(math.sin(a),.58)
            x=w*spow(math.cos(a),.69)*(.89+.11*(nz+1)/2)
            lean=-.028*max(0,(nz-.35)/.65)**2
            verts.append((cx+x,depth+lean,cz+h*nz));uvs.append((.5+x/.18,.5+nz/2))
    for k in range(len(layers)-1):
        for j in range(128):faces.append((k*128+j,k*128+(j+1)%128,(k+1)*128+(j+1)%128,(k+1)*128+j))
    faces.append(tuple(reversed(range(128))))
    faces.append(tuple(4*128+j for j in range(128)))
    ear=mesh_obj(tag+'_sculpted_recessed_ear',verts,faces,VIOLET,'03_EARS',uvs)
    ear.data.materials.append(PALE);ear.data.materials.append(INNER)
    for poly in ear.data.polygons:
        k=poly.index//128
        poly.material_index=1 if k==1 else (2 if k in (2,3) or poly.index==len(faces)-1 else 0)
    bevel=ear.modifiers.new('Soft_ear_rim','BEVEL');bevel.width=.003;bevel.segments=3

# Bow tie with folded lobes, a knot and short fabric tails.
for s in (-1,1):
    verts=[];faces=[];uv=[]
    for i in range(25):
        u=i/24;xx=s*(.022+.148*u);half=.017+.048*u**.55
        for j in range(17):
            v=2*j/16-1
            z=1.477+half*v+.005*u
            y=-.229-.022*math.sin(math.pi*u)-.008*math.cos(2*math.pi*v)*(1-u)
            verts.append((xx,y,z));uv.append((u,j/16))
    for i in range(24):
        for j in range(16):
            f=(i*17+j,(i+1)*17+j,(i+1)*17+j+1,i*17+j+1)
            faces.append(f if s>0 else tuple(reversed(f)))
    bow=mesh_obj('Bow_lobe_'+str(s),verts,faces,TIE,'07_DETAILS',uv)
    mod=bow.modifiers.new('Cotton_thickness','SOLIDIFY');mod.thickness=.006
    verts=[(s*.018,-.231,1.473),(s*.077,-.227,1.466),(s*.127,-.230,1.358),(s*.087,-.241,1.382),(s*.052,-.233,1.364)]
    tail=mesh_obj('Bow_tail_'+str(s),verts,[(0,1,2,3,4)],TIE,'07_DETAILS')
    mod=tail.modifiers.new('Folded_tail_thickness','SOLIDIFY');mod.thickness=.007
    be=tail.modifiers.new('Soft_fabric_edge','BEVEL');be.width=.004;be.segments=3
rounded('Bow_center_knot',(0,-.242,1.478),(.029,.023,.024),TIE,'07_DETAILS',ez=.7,ex=.5)
for i,z in enumerate([1.377,1.311],1):
    y=-torso_r(z)[1]-.012
    ell('Black_button_%02d'%i,(0,y-.008,z),(.020,.010,.020),BUTTON,'07_DETAILS')
    for sx in (-.004,.004):ell('Button_hole_%s_%s'%(i,sx),(sx,y-.019,z),(.002,.001,.002),DARK,'07_DETAILS')

curve('Upper_arm_diagonal_split',[(-.565,-.077,1.520),(-.525,-.092,1.511),(-.500,-.096,1.484),(-.468,-.097,1.477)],.0015,DARK,'06_DAMAGE')
curve('Arm_split_branch',[(-.525,-.092,1.511),(-.544,-.070,1.539),(-.557,-.035,1.547)],.0011,DARK,'06_DAMAGE')
for j in range(22):
    xx=-.252+j*.0065;zz=.756+.011*math.sin(101*xx)
    curve('Thigh_fray_%02d'%j,[(xx,-.082,zz),(xx+.002*math.sin(j),-.087,zz-.005-random.random()*.003)],.00055,THREAD,'06_DAMAGE')
pts=[]
for i in range(45):
    nz=-.70+1.47*i/44
    yy=.027+.228*max(0,1-abs(nz)**(2/.82))**(.82/2)+.0008
    pts.append((0,yy,1.837+.229*nz))
curve('Rear_cranial_join',pts,.00065,THREAD,'07_DETAILS')

refimage=bpy.data.images.load(str(OUT/'reference.webp'),check_existing=True)
refimage.name='REFERENCE_user_three_view_2048x682';refimage.pack()
refempty=bpy.data.objects.new('REFERENCE_original_layout_hidden',None)
COLS['99_REFERENCE'].objects.link(refempty)
refempty.empty_display_type='IMAGE';refempty.data=refimage
refempty.hide_render=True;refempty.hide_viewport=True
refempty['provenance']='User PNG converted without resizing to lossy WebP; SHA-256 in INPUTS.md'
COLS['99_REFERENCE'].hide_render=True

for ob in list(scene.objects):
    if ob.type=='MESH' and ob.location.length < 1e-9 and ob.rotation_euler.to_matrix().is_identity:
        vs=ob.data.vertices
        if not vs: continue
        center=sum((v.co.copy() for v in vs),Vector())/len(vs)
        for v in vs:v.co-=center
        ob.location=center

world=bpy.data.worlds.new('Reference_neutral_gray_world');world.use_nodes=True;scene.world=world
nodes=world.node_tree.nodes;nodes.clear();links=world.node_tree.links
out=nodes.new('ShaderNodeOutputWorld')
ambient=nodes.new('ShaderNodeBackground');ambient.name='Ambient_illumination'
ambient.inputs['Color'].default_value=(.35,.35,.35,1);ambient.inputs['Strength'].default_value=.55
bg=nodes.new('ShaderNodeBackground');bg.name='Camera_gray_background'
bg.inputs['Color'].default_value=(.112,.112,.112,1);bg.inputs['Strength'].default_value=1
path=nodes.new('ShaderNodeLightPath');mix=nodes.new('ShaderNodeMixShader')
links.new(path.outputs['Is Camera Ray'],mix.inputs[0]);links.new(ambient.outputs[0],mix.inputs[1])
links.new(bg.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],out.inputs['Surface'])


def area(name,loc,energy,size):
    data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size
    ob=bpy.data.objects.new(name,data);COLS['90_STUDIO'].objects.link(ob);ob.location=loc
    ob.rotation_euler=(Vector((0,0,1.3))-ob.location).to_track_quat('-Z','Y').to_euler()
    return ob

area('Studio_soft_key',(-3,-4,5),650,4)
area('Studio_soft_fill',(4,-3,3),400,4)
area('Studio_rear_softbox',(0,4,4),350,3)
camdata=bpy.data.cameras.new('Reference_orthographic_camera');camdata.type='ORTHO';camdata.ortho_scale=2.678
camera=bpy.data.objects.new('Reference_orthographic_camera',camdata);COLS['90_STUDIO'].objects.link(camera)
camera.location=(0,-7,1.303);camera.rotation_euler=(Vector((0,0,1.303))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=48
scene.cycles.use_denoising=True;scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.035
scene.render.threads_mode='FIXED';scene.render.threads=3
scene.render.resolution_x=1024;scene.render.resolution_y=1024;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene['project_id']='worn-violet-rabbit-20260918'
scene['reference_axes']='front -Y; up +Z; dimensions inferred, nominal height 2.60 m'
scene['revision']='build-v001'
scene['review_status']='unreviewed; compare real front/right/back and face renders'
text=bpy.data.texts.new('READ_ME_project.txt')
text.write('Worn violet rabbit / reference reconstruction\nProject: worn-violet-rabbit-20260918\n'
           'Editable separate housings, face, ears, teeth, fabric folds, metal mechanism and damage.\n'
           'Units: meters, front -Y, up +Z. Height ~2.60 m; scale is an artistic assumption.\n'
           'PBR image textures reconstructed with deterministic multiscale noise; not recovered original UV maps.\n'
           'Box/triplanar mapping uses Fabric_mapping_0.48m; UV layers also retained where generated.\n'
           'Source reference is packed as REFERENCE_user_three_view_2048x682. Original PNG not archived, see INPUTS.md.\n'
           'No long-fur system, no animation rig requested. Intentional torn shells and open mouth.\n'
           'Technical success is not visual acceptance; check the pinned review for this exact job.\n')

bpy.context.view_layer.update()
objects=[o for o in scene.objects if o.type in {'MESH','CURVE'} and not o.hide_render]
points=[o.matrix_world@Vector(corner) for o in objects for corner in o.bound_box]
lo=[min(v[i] for v in points) for i in range(3)];hi=[max(v[i] for v in points) for i in range(3)]
size=[hi[i]-lo[i] for i in range(3)]
finite=all(math.isfinite(c) for o in objects if o.type=='MESH' for v in o.data.vertices for c in v.co)
teeth=[o.name for o in objects if 'tooth' in o.name.lower()]
missingmaterials=[o.name for o in objects if not o.data.materials]
report={'pass':finite and not missingmaterials and 2.55<size[2]<2.67 and 2.40<size[0]<2.60,
        'revision':'build-v001','project_id':scene['project_id'],'nominal_units':'meters',
        'bounds_min':lo,'bounds_max':hi,'dimensions':size,'finite_vertices':finite,
        'renderable_objects':len(objects),'mesh_vertices':sum(len(o.data.vertices) for o in objects if o.type=='MESH'),
        'teeth_count':len(teeth),'teeth_names':teeth,'missing_materials':missingmaterials,
        'intentional_torn_shells':[o.name for o in objects if o.get('intentional_open_surface')],
        'texture_images':[i.name for i in bpy.data.images if i.source=='FILE'],
        'uv_mapped_meshes':sum(bool(o.data.uv_layers) for o in objects if o.type=='MESH'),
        'unverified':['visual fidelity','production rigging','watertight-printability'],
        'notes':'Overlapping shells, mouth tubes and cloth folds are intentional; not a 3D-print-ready mesh.'}
(OUT/'geometry_validation.json').write_text(json.dumps(report,indent=2)+'\n')
assert report['pass'],report
checkpoint('geometry-and-materials','Measured shells, face, real ear wells, mechanisms, damage and packed materials complete')
