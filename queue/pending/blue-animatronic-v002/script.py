"""Reference-based blue animatronic v002. Front -Y, up Z.
The bridge owns saving/rendering. No external assets or filesystem access.
"""
import bpy
import math
from mathutils import Vector
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene['reference']='User-supplied blue animatronic turnaround, 2026-09-18'
scene['revision']='blue-animatronic-v002'
scene['model_notes']='Editable hard-surface character test; rigid armature; visual review required.'
parts=[]

def linear(c):
    return c/12.92 if c<.04045 else ((c+.055)/1.055)**2.4

def material(name,rgb,roughness=.38,metallic=0,coat=.15):
    m=bpy.data.materials.new(name)
    m.diffuse_color=tuple(linear(c) for c in rgb)+(1,)
    m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=m.diffuse_color
    bs.inputs['Roughness'].default_value=roughness
    bs.inputs['Metallic'].default_value=metallic
    if 'Coat Weight' in bs.inputs:
        bs.inputs['Coat Weight'].default_value=coat
    return m
BLUE=material('01 | Azure blue enamel',(.075,.445,.855),.34,.05,.22)
PALE=material('02 | Ice blue panels',(.715,.855,.985),.4)
BLACK=material('03 | Charcoal soft parts',(.095,.108,.13),.62,0,0)
SEAM=material('04 | Deep blue panel seams',(.025,.09,.175),.48)
METAL=material('05 | Headphone hardware',(.215,.23,.255),.36,.35)
WHITE=material('06 | Porcelain teeth and ribbon',(.955,.975,1),.28)
GLASS=material('07 | Opaque sunglass lenses',(.009,.017,.032),.17,.05,.4)
SHINE=material('08 | Graphic white reflection',(.975,.995,1),.2)
bs=SHINE.node_tree.nodes.get('Principled BSDF')
if 'Emission Color' in bs.inputs:
    bs.inputs['Emission Color'].default_value=(.8,.87,1,1)
    bs.inputs['Emission Strength'].default_value=.18

def register(obj,name,mat,bone):
    obj.name=name
    if mat:
        obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth=True
    obj['part']=name
    obj['rig_bone']=bone
    parts.append((obj,bone))
    return obj

def mesh(name,verts,faces,mat,bone='head'):
    data=bpy.data.meshes.new(name+'.mesh')
    data.from_pydata(verts,[],faces)
    data.update()
    obj=bpy.data.objects.new(name,data)
    scene.collection.objects.link(obj)
    return register(obj,name,mat,bone)

def soften(obj,width=.025,segments=3):
    mod=obj.modifiers.new('Rounded manufactured edges','BEVEL')
    mod.width=width
    mod.segments=segments
    norm=obj.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    norm.keep_sharp=True
    return obj

def ellipsoid(name,center,scale,mat,bone='head',exponent=1):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40,ring_count=24,radius=1,location=center)
    obj=bpy.context.object
    for v in obj.data.vertices:
        for i in range(3):
            a=v.co[i]
            v.co[i]=math.copysign(abs(a)**exponent,a)*scale[i]
    return register(obj,name,mat,bone)

def box(name,center,dimensions,bevel,mat,bone='head'):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center)
    obj=bpy.context.object
    for v in obj.data.vertices:
        for i in range(3):
            v.co[i]*=dimensions[i]
    register(obj,name,mat,bone)
    return soften(obj,bevel,4)

def cylinder(name,center,radius,depth,mat,bone='head',axis=(0,0,1),rtop=None):
    bpy.ops.mesh.primitive_cone_add(vertices=64,radius1=radius,radius2=radius if rtop is None else rtop,depth=depth,location=center)
    obj=bpy.context.object
    obj.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler()
    register(obj,name,mat,bone)
    return soften(obj,min(.018,depth*.15),3)

def pipe(name,points,radius,mat,bone='head',closed=False,sides=10):
    pts=[Vector(p) for p in points]
    vertices,faces=[],[]
    count=len(pts)
    for i,p in enumerate(pts):
        a=pts[(i-1)%count] if closed or i else pts[0]
        b=pts[(i+1)%count] if closed or i<count-1 else pts[-1]
        tangent=(b-a).normalized()
        helper=Vector((0,0,1)) if abs(tangent.z)<.9 else Vector((0,1,0))
        u=tangent.cross(helper).normalized()
        v=tangent.cross(u).normalized()
        for j in range(sides):
            t=2*math.pi*j/sides
            vertices.append(tuple(p+radius*(u*math.cos(t)+v*math.sin(t))))
    for i in range(count if closed else count-1):
        for j in range(sides):
            faces.append((i*sides+j,i*sides+(j+1)%sides,((i+1)%count)*sides+(j+1)%sides,((i+1)%count)*sides+j))
    if not closed:
        faces.extend([tuple(reversed(range(sides))),tuple((count-1)*sides+j for j in range(sides))])
    return mesh(name,vertices,faces,mat,bone)

def ring(name,center,rx,ry,radius,mat,bone='torso',axis=(0,0,1)):
    q=Vector(axis).to_track_quat('Z','Y')
    c=Vector(center)
    pts=[tuple(c+q@Vector((rx*math.cos(t),ry*math.sin(t),0))) for t in [2*math.pi*i/64 for i in range(64)]]
    return pipe(name,pts,radius,mat,bone,True)

def catmull(rows,subdivisions=5):
    output=[]
    for i in range(len(rows)-1):
        p0,p1=rows[max(0,i-1)],rows[i]
        p2,p3=rows[i+1],rows[min(len(rows)-1,i+2)]
        for step in range(subdivisions):
            t=step/subdivisions
            output.append(tuple(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t) for a,b,c,d in zip(p0,p1,p2,p3)))
    output.append(tuple(rows[-1]))
    return output

def loft(name,rows,mat,bone='torso',exponent=1,sides=64):
    profiles=catmull(rows)
    verts,faces=[],[]
    for z,rx,ry,cy in profiles:
        for j in range(sides):
            a=2*math.pi*j/sides
            co,si=math.cos(a),math.sin(a)
            verts.append((max(rx,.006)*math.copysign(abs(co)**exponent,co),cy+max(ry,.006)*math.copysign(abs(si)**exponent,si),z))
    for k in range(len(profiles)-1):
        for j in range(sides):
            faces.append((k*sides+j,k*sides+(j+1)%sides,(k+1)*sides+(j+1)%sides,(k+1)*sides+j))
    faces.append(tuple(reversed(range(sides))))
    faces.append(tuple((len(profiles)-1)*sides+j for j in range(sides)))
    return mesh(name,verts,faces,mat,bone)

def prism(name,outline,front_y,thickness,mat,bone='head',bevel=.02):
    n=len(outline)
    verts=[(x,front_y,z) for x,z in outline]+[(x,front_y+thickness,z) for x,z in outline]
    faces=[tuple(range(n)),tuple(reversed(range(n,2*n)))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    obj=mesh(name,verts,faces,mat,bone)
    return soften(obj,bevel,4) if bevel else obj

def segment(name,start,end,radius,mat,bone):
    a,b=Vector(start),Vector(end)
    length=(b-a).length
    rows=[(0,radius*.64,radius*.64,0),(.06*length,radius*.87,radius*.87,0),(.24*length,radius,radius,0),(.66*length,radius*.98,radius*.98,0),(.92*length,radius*.78,radius*.78,0),(length,radius*.65,radius*.65,0)]
    obj=loft(name,rows,mat,bone,sides=48)
    obj.location=a
    obj.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return obj

body_rows=[(2.64,.84,.49,.04),(2.72,1.015,.61,.04),(2.95,1.04,.64,.045),(3.35,1.005,.66,.05),(3.82,.94,.64,.055),(4.18,.83,.565,.05),(4.40,.68,.45,.04),(4.47,.50,.33,.03)]
loft('Torso | blue outer shell',body_rows,BLUE,'torso',.86)
head_rows=[(4.39,.22,.18,-.43),(4.46,.39,.31,-.35),(4.68,.55,.44,-.20),(4.92,.84,.64,.04),(5.15,1.025,.745,.10),(5.38,.965,.75,.13),(5.66,.845,.72,.13),(5.95,.785,.655,.12),(6.18,.63,.49,.11),(6.29,.34,.28,.10),(6.31,.06,.08,.10)]
loft('Head | sculpted cheek and chin silhouette',head_rows,BLUE,'head',.92)
cylinder('Neck | flexible connector',(0,.02,4.46),.43,.22,BLACK,'neck')
ring('Neck | top collar',(0,.02,4.48),.48,.37,.055,BLACK,'neck')
loft('Pelvis | rounded blue casing',[(2.12,.33,.26,.03),(2.20,.66,.47,.03),(2.37,.91,.59,.03),(2.58,1.005,.625,.03),(2.67,.98,.61,.03)],BLUE,'hips',.90)
ring('Waist | shell separation',(0,.04,2.68),.977,.604,.024,SEAM,'hips')

def body_section(z):
    rows=catmull(body_rows,8)
    for i in range(len(rows)-1):
        if rows[i][0]<=z<=rows[i+1][0]:
            t=(z-rows[i][0])/max(rows[i+1][0]-rows[i][0],.00001)
            return tuple(rows[i][j]*(1-t)+rows[i+1][j]*t for j in range(1,4))
    return tuple(rows[0 if z<rows[0][0] else -1][1:])

def front_surface(x,z,offset=.016):
    rx,ry,cy=body_section(z)
    return cy-ry*max(.001,1-(abs(x)/rx)**(2/.86))**(.86/2)-offset

panel_rows=catmull([(2.68,.43),(2.77,.63),(3.08,.68),(3.46,.635),(3.79,.53),(4.02,.365),(4.15,.17)],6)
panel_verts=[]
for z,w in panel_rows:
    for j in range(25):
        x=w*(-1+2*j/24)
        panel_verts.append((x,front_surface(x,z),z))
panel_faces=[]
for k in range(len(panel_rows)-1):
    for j in range(24):
        panel_faces.append((k*25+j,k*25+j+1,(k+1)*25+j+1,(k+1)*25+j))
mesh('Belly | fitted ice-blue panel',panel_verts,panel_faces,PALE,'torso')
border=[(-w,front_surface(-w,z)-.003,z) for z,w in panel_rows]+[(w,front_surface(w,z)-.003,z) for z,w in reversed(panel_rows)]
pipe('Belly | fine perimeter gasket',border,.014,SEAM,'torso',True)
pipe('Belly | central panel split',[(0,front_surface(0,z)-.006,z) for z in [2.70+i*1.40/48 for i in range(49)]],.009,SEAM,'torso')
for i,z in enumerate((3.02,3.48,3.88),1):
    cylinder('Button %02d | black fastener'%i,(0,front_surface(0,z)-.031,z),.079,.040,BLACK,'torso',(0,-1,0))
prism('Pelvis | lower ice-blue inset',[(-.52,2.62),(.52,2.62),(.35,2.34),(.13,2.23),(-.13,2.23),(-.35,2.34)],-.596,.048,PALE,'hips',.032)
for s,label in ((-1,'R'),(1,'L')):
    outline=[(s*x,z) for x,z in [(.06,4.20),(.18,4.39),(.47,4.43),(.59,4.33),(.52,4.17),(.55,4.02),(.44,3.98),(.21,4.09)]]
    if s<0:
        outline.reverse()
    prism('Bow tie | '+label,outline,-.73,.18,BLACK,'torso',.055)
ellipsoid('Bow tie | center knot',(0,-.77,4.21),(.185,.115,.155),BLACK,'torso',.84)
prism('Mouth | recessed charcoal cavity',[(-.34,4.98),(.34,4.98),(.33,4.78),(.23,4.46),(-.23,4.46),(-.33,4.78)],-.727,.09,BLACK,'jaw',.055)
for s,label in ((-1,'R'),(1,'L')):
    ellipsoid('Muzzle | '+label,(s*.345,-.736,5.085),(.392,.305,.218),PALE,'head',.85)
    tooth=box('Incisor | '+label,(s*.106,-.876,4.699),(.198,.184,.454),.047,WHITE,'jaw')
    tooth.rotation_euler[1]=s*math.radians(-2)
    box('Small upper tooth | '+label,(s*.258,-.796,4.845),(.085,.11,.17),.025,WHITE,'jaw')
    pipe('Smile crease | '+label,[(s*.64,-.807,5.087),(s*.77,-.68,5.072),(s*.86,-.60,5.015)],.017,SEAM,'head')
prism('Nose | soft triangular button',[(-.139,5.261),(.139,5.261),(.11,5.189),(0,5.134),(-.11,5.189)],-1.04,.135,BLACK,'head',.032)
ellipsoid('Nose | small glint',(-.03,-1.074,5.235),(.047,.011,.016),PALE,'head')
pipe('Muzzle | center division',[(0,-1.024,5.14),(0,-1.02,5.025),(0,-.97,4.929)],.013,SEAM,'head')
for s,label in ((-1,'R'),(1,'L')):
    x=s*.357
    ellipsoid('Eye underneath glasses | '+label,(x,-.58,5.684),(.27,.125,.287),WHITE,'head')
    shape=[(-.30,.22),(.30,.22),(.30,-.035),(.21,-.245),(.02,-.285),(-.205,-.25),(-.30,-.07)]
    prism('Sunglasses | frame '+label,[(x+u,5.744+v) for u,v in shape],-.781,.114,BLACK,'head',.035)
    prism('Sunglasses | lens '+label,[(x+u*.865,5.744+v*.865) for u,v in shape],-.804,.025,GLASS,'head',.023)
    prism('Sunglasses | white reflection '+label,[(x+.060,5.914),(x+.148,5.89),(x-.01,5.554),(x-.087,5.607)],-.833,.007,SHINE,'head',.008)
    box('Sunglasses | temple '+label,(s*.735,-.27,5.906),(.103,.92,.074),.026,BLACK,'head')
    pipe('Eyebrow | '+label,[(x-.14,-.543,6.079),(x-.065,-.568,6.135),(x+.03,-.575,6.14),(x+.116,-.567,6.08)],.016,SEAM,'head')
box('Sunglasses | straight brow bar',(0,-.773,5.967),(1.43,.12,.085),.025,BLACK,'head')
box('Sunglasses | bridge',(0,-.82,5.845),(.18,.095,.063),.021,BLACK,'head')
for s,label in ((-1,'R'),(1,'L')):
    ellipsoid('Ear | blue outer '+label,(s*.745,.10,6.272),(.35,.165,.36),BLUE,'head')
    ellipsoid('Ear | inset shadow '+label,(s*.745,-.057,6.278),(.215,.035,.244),SEAM,'head')
    ellipsoid('Ear | ice-blue inner '+label,(s*.745,-.086,6.285),(.178,.031,.205),PALE,'head')
    cylinder('Headphones | soft cushion '+label,(s*.904,.105,5.695),.337,.19,BLACK,'head',(s,0,0))
    cylinder('Headphones | outer cup '+label,(s*1.035,.105,5.695),.32,.135,METAL,'head',(s,0,0))
    cylinder('Headphones | cup face '+label,(s*1.113,.105,5.695),.277,.030,BLACK,'head',(s,0,0))
    cylinder('Headphones | central badge '+label,(s*1.135,.105,5.695),.114,.022,METAL,'head',(s,0,0))
    ring('Headphones | badge rim '+label,(s*1.150,.105,5.695),.113,.113,.011,BLACK,'head',(s,0,0))
    pipe('Headphones | support '+label,[(s*.81,.13,6.10),(s*.94,.14,6.06),(s*.965,.12,5.935)],.056,BLACK,'head')
pipe('Headphones | headband',[(.93*math.sin(t),.19,5.77+.55*math.cos(t)) for t in [-math.pi/2+i*math.pi/64 for i in range(65)]],.06,BLACK,'head')

def tuft(name,rows):
    samples=catmull(rows,8)
    verts,faces=[],[]
    sides=20
    for i,(x,y,z,w,d) in enumerate(samples):
        p=Vector((x,y,z))
        before=Vector(samples[max(0,i-1)][:3])
        after=Vector(samples[min(len(samples)-1,i+1)][:3])
        tangent=(after-before).normalized()
        u=tangent.cross(Vector((0,1,0))).normalized()
        v=tangent.cross(u).normalized()
        for j in range(sides):
            a=2*math.pi*j/sides
            verts.append(tuple(p+u*max(.003,w)*math.cos(a)+v*max(.003,d)*math.sin(a)))
    for k in range(len(samples)-1):
        for j in range(sides):
            faces.append((k*sides+j,k*sides+(j+1)%sides,(k+1)*sides+(j+1)%sides,(k+1)*sides+j))
    faces.extend([tuple(reversed(range(sides))),tuple((len(samples)-1)*sides+j for j in range(sides))])
    mesh(name,verts,faces,BLUE,'head')
tuft('Forelock | main swept curl',[(.07,-.43,6.135,.23,.14),(-.16,-.48,6.235,.21,.14),(-.40,-.49,6.38,.11,.09),(-.48,-.48,6.62,.003,.003)])
tuft('Forelock | outward point',[(-.16,-.37,6.23,.17,.13),(-.40,-.45,6.26,.15,.095),(-.66,-.55,6.30,.095,.045),(-.82,-.65,6.43,.003,.003)])
tuft('Forelock | lower flick',[(-.22,-.38,6.15,.14,.10),(-.42,-.48,6.135,.12,.073),(-.62,-.59,6.145,.07,.04),(-.76,-.66,6.20,.003,.003)])
pipe('Head | rear casing seam',[(0,cy+ry+.01,z) for z,rx,ry,cy in catmull(head_rows[3:-1],5)],.01,SEAM,'head')
pipe('Torso | rear casing seam',[(0,cy+ry+.01,z) for z,rx,ry,cy in catmull(body_rows[1:-1],5)],.009,SEAM,'torso')
cylinder('Top hat | brim',(0,.10,6.465),.37,.075,BLACK,'head')
cylinder('Top hat | crown',(0,.10,6.739),.212,.47,BLACK,'head',rtop=.268)
cylinder('Top hat | white ribbon',(0,.10,6.566),.230,.095,WHITE,'head',rtop=.237)
ring('Top hat | crown top piping',(0,.10,6.977),.252,.252,.014,BLACK,'head')
bone_specs=[]
for s,label in ((-1,'R'),(1,'L')):
    shoulder=(s*1.015,.01,4.245)
    elbow=(s*1.435,0,3.375)
    wrist=(s*1.685,-.025,2.683)
    hand=(s*1.782,-.035,2.29)
    upper,lower,palm='upper_arm.'+label,'forearm.'+label,'hand.'+label
    bone_specs.extend([(upper,shoulder,elbow,'torso'),(lower,elbow,wrist,upper),(palm,wrist,hand,lower)])
    ellipsoid('Shoulder | dark joint '+label,shoulder,(.25,.265,.27),BLACK,upper)
    a,b=Vector(shoulder),Vector(elbow)
    axis=b-a
    segment('Upper arm | blue shell '+label,shoulder,tuple(b-axis.normalized()*.075),.353,BLUE,upper)
    for k,t in enumerate((.235,.36,.485),1):
        c=a+axis*t
        cylinder('Upper arm | pale stripe %d '%k+label,c,.359,.066,PALE,upper,axis)
        for sign in (-1,1):
            ring('Upper arm | stripe edge %d %d '%(k,sign)+label,c+axis.normalized()*(sign*.037),.354,.354,.009,SEAM,upper,axis)
    ellipsoid('Elbow | flexible joint '+label,elbow,(.246,.235,.232),BLACK,lower)
    lower_start=Vector(elbow)+(Vector(wrist)-Vector(elbow)).normalized()*.075
    segment('Forearm | blue shell '+label,lower_start,wrist,.318,BLUE,lower)
    axis2=Vector(wrist)-Vector(elbow)
    cylinder('Wrist | pale cuff '+label,Vector(wrist)-axis2.normalized()*.012,.255,.113,PALE,lower,axis2)
    ring('Wrist | cuff gasket '+label,Vector(wrist)+axis2.normalized()*.049,.248,.248,.012,SEAM,lower,axis2)
    ellipsoid('Hand | charcoal palm '+label,(s*1.782,-.014,2.431),(.264,.224,.294),BLACK,palm,.83)
    for j,dx in enumerate((-.175,0,.175),1):
        ellipsoid('Hand | blue finger %d '%j+label,(s*(1.782+dx),-.099,2.198+(.035 if j!=2 else 0)),(.128,.17,.175),BLUE,palm,.86)
    ellipsoid('Hand | blue thumb '+label,(s*1.528,-.155,2.482),(.168,.169,.202),BLUE,palm,.90)
for s,label in ((-1,'R'),(1,'L')):
    hip,knee,ankle,toe=(s*.60,.025,2.34),(s*.716,.02,1.475),(s*.737,-.02,.63),(s*.79,-.68,.24)
    thigh,shin,foot='thigh.'+label,'shin.'+label,'foot.'+label
    bone_specs.extend([(thigh,hip,knee,'hips'),(shin,knee,ankle,thigh),(foot,ankle,toe,shin)])
    ellipsoid('Hip | ball joint '+label,hip,(.31,.33,.30),BLACK,thigh)
    segment('Thigh | blue casing '+label,(s*.625,.02,2.28),(s*.716,.02,1.59),.411,BLUE,thigh)
    ellipsoid('Knee | dark hinge '+label,knee,(.268,.258,.236),BLACK,shin)
    ellipsoid('Knee | ice-blue cap '+label,(s*.716,-.237,1.50),(.267,.115,.18),PALE,shin,.83)
    segment('Shin | blue casing '+label,(s*.721,.025,1.335),(s*.737,-.015,.775),.356,BLUE,shin)
    for j,z in enumerate((.659,.785),1):
        cylinder('Ankle | ice-blue band %d '%j+label,(s*.737,-.012,z),.334,.107,PALE,foot)
        ring('Ankle | band edge %d '%j+label,(s*.737,-.012,z+.056),.326,.326,.013,SEAM,foot)
    ellipsoid('Foot | blue boot '+label,(s*.80,-.195,.333),(.598,.747,.308),BLUE,foot,.70)
    ellipsoid('Foot | dark undersole '+label,(s*.80,-.215,.095),(.595,.713,.074),SEAM,foot,.70)
    for j,dx in enumerate((-.356,0,.356),1):
        ellipsoid('Foot | ice-blue toe %d '%j+label,(s*.80+dx,-.764,.266),(.204,.251,.223),PALE,foot,.76)
checkpoint('geometry_ready','Reference-based shells, face, accessories and segmented limbs created')
arm_data=bpy.data.armatures.new('BlueAnimatronicRig.data')
rig=bpy.data.objects.new('BlueAnimatronicRig',arm_data)
scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig
rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
core=[('root',(0,0,.1),(0,0,.65),None),('hips',(0,0,2.20),(0,0,2.78),'root'),('torso',(0,0,2.78),(0,0,4.33),'hips'),('neck',(0,0,4.33),(0,0,4.68),'torso'),('head',(0,0,4.68),(0,0,6.22),'neck'),('jaw',(0,-.37,4.90),(0,-.49,4.45),'head')]
for name,head,tail,parent in core+bone_specs:
    bone=arm_data.edit_bones.new(name)
    bone.head=head
    bone.tail=tail
    if parent:
        bone.parent=arm_data.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
rig.show_in_front=True
rig.display_type='WIRE'
for obj,bone in parts:
    vg=obj.vertex_groups.new(name=bone)
    vg.add(list(range(len(obj.data.vertices))),1,'REPLACE')
    mod=obj.modifiers.new('Rigid articulation','ARMATURE')
    mod.object=rig
    obj.parent=rig
rig['instructions']='Pose Mode: head, jaw, upper_arm, forearm, hand, thigh, shin, foot. Rigid weighting, not a soft-body character rig.'
world=bpy.data.worlds.new('Blue character studio') if scene.world is None else scene.world
scene.world=world
world.use_nodes=True
world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.12,.15,.20,1)
world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.5

def light(name,location,energy,size):
    data=bpy.data.lights.new(name,'AREA')
    data.energy=energy
    data.shape='DISK'
    data.size=size
    obj=bpy.data.objects.new(name,data)
    scene.collection.objects.link(obj)
    obj.location=location
    obj.rotation_euler=(Vector((0,0,3.5))-obj.location).to_track_quat('-Z','Y').to_euler()
light('Studio | soft key',(-4.5,-7,9),1450,5)
light('Studio | front fill',(4.5,-5,5.5),950,4.5)
light('Studio | blue shell rim',(2.5,4.5,9),1750,4)
cam_data=bpy.data.cameras.new('PortraitCamera.data')
cam_data.type='ORTHO'
cam_data.ortho_scale=8.1
camera=bpy.data.objects.new('PortraitCamera',cam_data)
scene.collection.objects.link(camera)
camera.location=(9,-16,9)
camera.rotation_euler=(Vector((0,0,3.5))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.camera=camera
scene.render.engine='CYCLES'
scene.cycles.device='CPU'
scene.cycles.samples=32
scene.cycles.use_denoising=True
scene.render.resolution_x=900
scene.render.resolution_y=1000
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='Standard'
scene.view_settings.look='None'
scene.view_settings.exposure=0
scene.view_settings.gamma=1
if hasattr(scene,'eevee') and hasattr(scene.eevee,'use_gtao'):
    scene.eevee.use_gtao=True
    scene.eevee.gtao_distance=3
    scene.eevee.gtao_factor=1.2
    scene.eevee.use_soft_shadows=True
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_distance=10
            area.spaces.active.region_3d.view_location=Vector((0,0,3.4))
            area.spaces.active.shading.type='MATERIAL'
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.context.view_layer.update()
assert len(parts)>100
assert len(rig.data.bones)==18
scene['mesh_parts']=len(parts)
scene['rig_bones']=len(rig.data.bones)
checkpoint('rig_and_studio_ready','Created %d editable mesh parts and %d rigid-control bones; visual review pending'%(len(parts),len(rig.data.bones)))
