"""New reconstruction from measured front/profile/back proportions."""
import json
import math
from pathlib import Path
import bpy
from mathutils import Vector

exec(compile(Path(__file__).with_name('geometry.py').read_text(), 'geometry.py', 'exec'), globals())
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
scene.render.engine='CYCLES'; scene.cycles.device='CPU'; scene.cycles.use_denoising=False
scene.view_settings.view_transform='Standard'
try: scene.view_settings.look='None'
except TypeError: pass
scene.view_settings.exposure=0; scene.view_settings.gamma=1
ANCHOR=bpy.data.objects.new('REPLICA_coordinates_metres',None); scene.collection.objects.link(ANCHOR)
folder=Path(WORKSPACE_DIR)/'output/surfaces'
purple=cloth('01_Worn_muted_violet_short_nap','purple',folder,.50)
pale=cloth('02_Worn_grey_lilac_patches','pale',folder,.58)
inner=cloth('03_Dark_ear_velvet','inner',folder,0)
headmat=cloth('04_Head_shell_with_faded_eye_mask','purple',folder,.38,True)
black=plain('05_Black_woven_bow',(0.003,.003,.004),.87)
lining=plain('06_Exposed_dark_worn_lining',(.012,.009,.012),.98)
metal=plain('07_Old_dark_steel',(.023,.026,.023),.46,.78)
eye=plain('08_Black_recessed_glass',(.0007,.0008,.0007),.19)
eye.node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=.08
teeth=plain('09_Aged_olive_ivory',(.24,.265,.16),.57)
gum=plain('10_Dark_recessed_gums',(.025,.031,.016),.95)
seam=plain('11_Subtle_dark_fabric_seams',(.045,.028,.041),.98)

BODY=[(.895,.244,.204,.198,0),(.901,.277,.242,.218,0),(.922,.298,.268,.239,0),
      (1.00,.305,.296,.247,0),(1.16,.305,.304,.251,0),(1.33,.289,.271,.232,0),
      (1.465,.276,.206,.196,0),(1.515,.250,.163,.159,0),(1.552,.199,.128,.126,0),
      (1.568,.150,.107,.109,0),(1.574,.112,.088,.090,0)]
body=shell('Torso_continuous_tapered_shell',BODY,purple,.73,96,2)

def body_section(z):
    for a,b in zip(BODY[:-1],BODY[1:]):
        if a[0]<=z<=b[0]:
            t=(z-a[0])/(b[0]-a[0]); return [a[j]*(1-t)+b[j]*t for j in range(1,5)]
    return list(BODY[0][1:] if z<BODY[0][0] else BODY[-1][1:])
def body_y(x,z,back=False):
    rx,fr,ba,cy=body_section(z)
    q=min(.9999,abs(x)/rx)**(2/.73)
    return cy+(ba if back else -fr)*max(.001,1-q)**(.73/2)
rows=[(.910,.222),(.916,.237),(.932,.245),(1.00,.254),(1.12,.253),(1.26,.237),(1.39,.205),(1.50,.164),(1.548,.119)]
verts=[]; faces=[]; across=40
for z,w in rows:
    for j in range(across+1):
        x=w*(2*j/across-1); verts.append((x,body_y(x,z)-.0035,z))
for i in range(len(rows)-1):
    for j in range(across):
        k=i*(across+1)+j; faces.append((k,k+1,k+across+2,k+across+1))
bib=mesh_object('Belly_fitted_flat_bottom_patch',verts,faces,pale); subd(bib,2,True)
# Grey crescent at the back neckline, not a large pale back panel.
verts=[]; faces=[]
for i in range(5):
    for j in range(33):
        u=2*j/32-1; x=.149*u; bottom=1.487+.061*abs(u)**1.5; top=1.565-.020*abs(u)
        z=bottom+(top-bottom)*i/4; verts.append((x,body_y(x,z,True)+.003,z))
for i in range(4):
    for j in range(32):
        k=i*33+j; faces.append((k,k+1,k+34,k+33))
mesh_object('Back_neck_faded_crescent',verts,faces,pale)
cylinder('Neck_dark_support',(0,0,1.556),(0,0,1.645),.047,metal)

# Arms: closely fitted cuffs, real irregular open tears and dark lining.
for s,label in [(-1,'L'),(1,'R')]:
    def arm_damage(t,a):
        return s<0 and .08<t<.63+.04*math.sin(a*7) and .14+.1*math.sin(t*25)<a<1.69
    cuff(label+'_upper_arm_shell',(s*.306,0,1.465),(s*.574,0,1.465),.104,.097,purple,arm_damage if s<0 else None,lining)
    cuff(label+'_forearm_shell',(s*.591,0,1.465),(s*.862,0,1.465),.096,.091,purple,None,lining)
    cylinder(label+'_shoulder_axle',(s*.263,0,1.465),(s*.334,0,1.465),.058,metal)
    cylinder(label+'_elbow_axle',(s*.561,0,1.465),(s*.607,0,1.465),.054,metal)
    cylinder(label+'_wrist_axle',(s*.845,0,1.465),(s*.899,0,1.465),.042,metal)
    ellipsoid(label+'_palm',(s*.963,0,1.455),(.094,.102,.057),purple)
    for k,y in enumerate([-.071,-.024,.026,.073]):
        tip=1.247-[.023,0,.006,.035][k]
        ellipsoid(label+'_finger_'+str(k+1),(s*(tip-.110),y,1.453),(.112,.038,.049),purple)
    thumb=ellipsoid(label+'_curled_thumb',(s*.987,-.104,1.419),(.057,.040,.055),purple)
    thumb.rotation_euler.y=s*.4
    # A few thin fracture lines on the damaged cuff, not square inspection windows.
    if s<0:
        tube_curve('L_upper_shell_hairline_1',[(-.545,-.066,1.534),(-.521,-.080,1.523),(-.486,-.085,1.516)],.0012,seam)
        tube_curve('L_upper_shell_hairline_2',[(-.543,-.080,1.512),(-.520,-.090,1.498)],.0010,seam)

# Legs align with the torso. Broad feet extend slightly outwards, as in the image.
for s,label in [(-1,'L'),(1,'R')]:
    x=s*.148
    def thigh_damage(t,a):
        return s<0 and t>.51+.07*math.sin(a*5)+.025*math.sin(a*17) and .27<a<2.15
    cuff(label+'_thigh_shell',(x,0,.596),(x,0,.884),.119,.105,purple,thigh_damage if s<0 else None,lining)
    cuff(label+'_shin_shell',(x,0,.205),(x,0,.581),.113,.098,purple,None,lining)
    cuff(label+'_ankle_fabric_rim',(x,0,.178),(x,0,.210),.109,.096,purple)
    cylinder(label+'_hip_support',(x,0,.866),(x,0,.925),.054,metal)
    ellipsoid(label+'_knee_joint',(x,0,.591),(.073,.068,.049),metal)
    cylinder(label+'_ankle_support',(x,0,.138),(x,0,.189),.052,metal)
    pieces=[ellipsoid(label+'_heel',(x,.033,.079),(.146,.172,.074),purple),
            ellipsoid(label+'_forefoot',(s*.190,-.118,.065),(.186,.199,.060),purple)]
    for k,dx in enumerate([-.122,0,.122]):
        pieces.append(ellipsoid(label+'_toe_form_'+str(k),(s*.19+dx,-.258,.071),(.064,.094,.077),purple))
    foot=fuse(label+'_continuous_three_toed_foot',pieces,purple,.0035,2)
    foot.data.materials.append(pale)
    for v in foot.data.vertices:
        world=foot.matrix_world @ v.co
        if world.z<.006: v.co.z += .006-world.z
    for p in foot.data.polygons:
        c=foot.matrix_world @ p.center
        p.material_index=1 if c.y<-.221 and c.z<.161 else 0

# Main head and cheeks form one smooth shell before eye and mouth cavities are cut.
HEAD=[(1.621,.158,.145,.145,.024),(1.64,.201,.174,.187,.018),(1.72,.223,.220,.220,.014),
      (1.82,.222,.230,.224,.009),(1.91,.214,.219,.215,.005),(1.986,.176,.177,.178,0),
      (2.027,.119,.121,.126,0),(2.046,.057,.063,.070,0),(2.051,.007,.014,.015,0)]
core=shell('Head_base',HEAD,headmat,.9,96,2)
cheeks=[ellipsoid('cheek_union_'+str(s),(s*.194,-.148,1.79),(.068,.088,.083),headmat) for s in [-1,1]]
head=fuse('Head_sculpted_continuous_shell',[core]+cheeks,headmat,.0030,3)
for s in [-1,1]:
    cut=ellipsoid('Eye_cutter',(s*.077,-.200,1.881),(.058,.085,.064),lining,64,32)
    boolean_cut(head,cut)
    ellipsoid(('L' if s<0 else 'R')+'_recessed_black_eye',(s*.077,-.158,1.881),(.052,.049,.055),eye,64,32)
cut=ellipsoid('Mouth_cutter',(0,-.222,1.688),(.197,.158,.082),lining,64,32)
boolean_cut(head,cut)
mask=head.data.attributes.new('FaceMask','FLOAT','POINT')
for v,item in zip(head.data.vertices,mask.data):
    p=head.matrix_world @ v.co
    d=min(((p.x-s*.078)/.106)**2+((p.z-1.867)/.094)**2 for s in [-1,1])
    c=min(((p.x-s*.205)/.075)**2+((p.z-1.782)/.071)**2 for s in [-1,1])
    d=min(d,c)
    feather=max(0,min(1,(1.03-d)/.19))
    front=max(0,min(1,(-p.y-.105)/.055))
    item.value=feather*front*.92
ellipsoid('Mouth_deep_black_interior',(0,-.156,1.690),(.186,.107,.086),lining)
# Narrow, continuous bilobed muzzle, no head-wide white bar.
parts=[]
for s in [-1,1]:
    parts.append(ellipsoid('Muzzle_lobe',(s*.059,-.290,1.757),(.081,.097,.052),pale))
    parts.append(ellipsoid('Muzzle_cheek_transition',(s*.132,-.219,1.771),(.075,.060,.047),pale))
muzzle=fuse('Muzzle_continuous_bilobed',parts,pale,.0025,3)
tube_curve('Muzzle_central_split',[(0,-.386,1.763),(0,-.385,1.740),(0,-.368,1.710)],.0017,lining)
# Rounded triangular black nose, with proper depth.
verts=[]
for y in [-.401,-.433]:
    for x,z in [(-.048,1.794),(.048,1.794),(0,1.747)]: verts.append((x,y,z))
nose=mesh_object('Nose_soft_triangle',verts,[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],eye)
m=nose.modifiers.new('Rounded nose edges','BEVEL');m.width=.013;m.segments=6;apply(nose,m)
# Swept 3D U-shaped lower jaw: depth and side rise match the profile.
verts=[];faces=[];na=100;nc=20
for i in range(na+1):
    t=math.pi*i/na
    center=Vector((-.216*math.cos(t),-.159-.164*math.sin(t)**.9,1.798-.213*math.sin(t)))
    tangent=Vector((.216*math.sin(t),0,-.213*math.cos(t))).normalized()
    radial=Vector((-tangent.z,0,tangent.x)); radius=.022+.006*abs(math.cos(t)); deep=.039+.016*abs(math.cos(t))
    for j in range(nc):
        a=2*math.pi*j/nc
        p=center+radial*(radius*math.cos(a))+Vector((0,deep*math.sin(a),0));verts.append(tuple(p))
for i in range(na):
    for j in range(nc): faces.append((i*nc+j,i*nc+(j+1)%nc,(i+1)*nc+(j+1)%nc,(i+1)*nc+j))
faces.extend([tuple(reversed(range(nc))),tuple(na*nc+j for j in range(nc))])
jaw=mesh_object('Jaw_continuous_deep_horseshoe',verts,faces,pale)
for s in [-1,1]:
    cylinder('Jaw_hinge_'+str(s),(s*.213,-.102,1.774),(s*.231,-.102,1.774),.014,metal)
for row in ['lower','upper']:
    gum_points=[]
    for i in range(9):
        a=-1.13+2.26*i/8
        x=.174*math.sin(a)
        if row=='lower': y=-.318+.098*(1-math.cos(a)); z=1.628+.050*abs(math.sin(a))**1.6
        else: y=-.303+.086*(1-math.cos(a)); z=1.697+.025*abs(math.sin(a))
        tooth=ellipsoid(row+'_tooth_'+str(i+1),(x,y,z),(.0173,.020,.023),teeth,32,16)
        tooth.rotation_euler.x=(.15 if row=='lower' else -.12)
        gum_points.append((x,y+.010,z+(-.018 if row=='lower' else .018)))
    tube_curve(row+'_gum_recess',gum_points,.011,gum)
for s in [-1,1]:
    for k,(dz,endy) in enumerate([(.022,-.328),(-.003,-.317),(-.029,-.303)]):
        tube_curve('Whisker_'+str(s)+'_'+str(k),[(s*.100,-.365,1.756+dz*.3),(s*.159,-.345,1.755+dz),(s*.235,endy,1.752+dz*1.7)],.0009,black)

# Thick ear shells with real recessed inner channels and small spring supports.
for s,label in [(-1,'L'),(1,'R')]:
    cx=s*.113; n=96; verts=[];faces=[]
    contours=[]
    for kind in range(5):
        for j in range(n):
            t=2*math.pi*j/n
            if kind in [0,1,4]:
                zz=2.338+.262*spow(math.sin(t),.84)
                rx=.082*(.89+.11*(zz-2.076)/.524)
                xx=cx+rx*spow(math.cos(t),.84)
                yy={0:-.044,1:.050,4:.056}[kind]+.012*(zz-2.30)
                if kind==4: xx=cx+(xx-cx)*.90;zz=2.338+(zz-2.338)*.98
            else:
                zz=2.287+.202*spow(math.sin(t),.83);xx=cx+.049*spow(math.cos(t),.86)
                yy=-.048 if kind==2 else -.018
            verts.append((xx,yy,zz))
    # front annulus outer0 -> inner2, recessed wall2 -> inner3, outer depth0 -> back1
    for a,b in [(0,2),(2,3),(0,1),(1,4)]:
        for j in range(n):faces.append((a*n+j,a*n+(j+1)%n,b*n+(j+1)%n,b*n+j))
    faces.append(tuple(4*n+j for j in range(n)))
    ear=mesh_object(label+'_thick_ear_shell',verts,faces,purple)
    ear.data.materials.append(pale);ear.data.materials.append(inner)
    for p in ear.data.polygons:
        p.material_index=2 if n<=p.index<2*n else 0
        if p.center.z>2.497 and p.center.y<-.025: p.material_index=1
    # Dark, slightly convex inset contained behind the front rim.
    inset=ellipsoid(label+'_recessed_inner_ear',(cx,-.006,2.287),(.048,.018,.199),inner,48,32)
    cylinder(label+'_ear_pin',(cx,0,2.038),(cx,0,2.097),.014,metal)
    pts=[]
    for k in range(89):
        t=k/88; ang=2*math.pi*4*t
        pts.append((cx+.017*math.cos(ang),.017*math.sin(ang),2.046+.042*t))
    tube_curve(label+'_ear_coil_spring',pts,.0025,metal,resolution=3)

# Sculpted cloth bow wings with folds, plus two recessed buttons.
for s,label in [(-1,'L'),(1,'R')]:
    verts=[];faces=[]
    for i in range(9):
        u=i/8
        for j in range(9):
            v=2*j/8-1
            x=s*(.015+.143*u)
            z=1.457+v*(.027+.061*u)-.014*u*u
            y=-.207-.028*math.sin(math.pi*u)-.010*math.cos(v*math.pi*2)*math.sin(math.pi*u)
            verts.append((x,y,z))
    for i in range(8):
        for j in range(8):
            k=i*9+j;faces.append((k,k+1,k+10,k+9))
    bow=mesh_object(label+'_bow_wing_with_folds',verts,faces,black)
    subd(bow,2,True);m=bow.modifiers.new('Cloth thickness','SOLIDIFY');m.thickness=.006;apply(bow,m)
ellipsoid('Bow_central_knot',(0,-.235,1.455),(.031,.025,.032),black)
for i,z in enumerate([1.366,1.301]):
    y=body_y(0,z)-.012
    ellipsoid('Button_'+str(i+1),(0,y,z),(.022,.010,.022),eye,32,20)
    for dx in [-.004,.004]:
        ellipsoid('Button_sewing_hole',(dx,y-.009,z),(.0025,.0018,.0025),lining,16,8)
ellipsoid('Tail_round_worn_pom',(0,.324,.998),(.076,.073,.076),pale,48,32)

# All meshes retain explicit UVs, plus editable calibrated projection UV sets.
bpy.context.view_layer.update()
for ob in list(scene.objects):
    project_uvs(ob)
    if ob.type in {'MESH','CURVE'}: ob['asset']='violet-rabbit-replica-20260918'
# A real editable UV unwrap, separate from the calibrated projection coordinate sets.
bpy.ops.object.select_all(action='DESELECT')
for ob in scene.objects:
    if ob.type=='MESH': ob.select_set(True)
bpy.context.view_layer.objects.active=head
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15192,island_margin=.008)
bpy.ops.object.mode_set(mode='OBJECT')
# Pack the genuine reference copy too, separate from reconstructed textures.
reference=bpy.data.images.load(str(Path(INPUT_DIR)/'reference.webp'),check_existing=True)
reference.name='REFERENCE_front_side_back_original_dimensions_lossy_copy';reference.use_fake_user=True;reference.pack()
scene['project_id']='violet-rabbit-replica-20260918'
scene['source_description']='Measured reconstruction, not the source mesh. See BRIEF and surface_report.'
scene['front_axis']='-Y';scene['intended_height_m']=2.60
# A gentle neutral studio is saved in the editable deliverable.
world=bpy.data.worlds.new('Neutral_world') if not scene.world else scene.world
scene.world=world;world.use_nodes=True;world.node_tree.nodes.get('Background').inputs[0].default_value=(.12,.12,.12,1)
world.node_tree.nodes.get('Background').inputs[1].default_value=.7
for name,loc,power,size in [('Key',(-3,-4,5),650,4),('Fill',(3,-3,3),260,4),('Rear',(0,3,4),400,4)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,0,1.3))-ob.location).to_track_quat('-Z','Y').to_euler()
# Validate data rather than marking the appearance accepted.
points=[];empty=[];uv_missing=[]
for ob in scene.objects:
    if ob.type=='MESH':
        if not ob.data.materials:empty.append(ob.name)
        if not ob.data.uv_layers:uv_missing.append(ob.name)
        for v in ob.data.vertices:
            p=ob.matrix_world@v.co
            assert all(math.isfinite(x) for x in p),ob.name
            points.append(p)
minimum=[min(v[k] for v in points) for k in range(3)]
maximum=[max(v[k] for v in points) for k in range(3)]
report={'project_id':JOB['project_id'],'job_id':JOB['job_id'],'blender':bpy.app.version_string,
    'objects':len(scene.objects),'mesh_vertices':len(points),'bounds_min':minimum,'bounds_max':maximum,
    'dimensions':[maximum[k]-minimum[k] for k in range(3)],'missing_materials':empty,'missing_uvs':uv_missing,
    'teeth':len([o for o in scene.objects if '_tooth_' in o.name]),'recessed_eyes':2,
    'uv_layout_operation':'Blender multi-object Smart UV Project', 'editable_materials':len(bpy.data.materials),'appearance_acceptance':'pending_actual_image_review'}
assert not empty and not uv_missing
assert 2.55<report['dimensions'][2]<2.65
assert report['teeth']==18
(Path(OUTPUT_DIR)/'geometry_validation.json').write_text(json.dumps(report,indent=2))
checkpoint('modelled','New measured shell, cavities, deep jaw, segmented limbs and editable surfaces saved')
