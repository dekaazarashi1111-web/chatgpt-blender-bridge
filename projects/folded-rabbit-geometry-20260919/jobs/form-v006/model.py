"""Continue the verified v005 scene; geometry-only correction of actual reviewed defects."""
import ast,bpy,bmesh,math,json,hashlib,shutil,struct
from pathlib import Path
from mathutils import Vector,Matrix
from math import sin,cos,pi,sqrt
OUT=Path(OUTPUT_DIR);OUT.mkdir(parents=True,exist_ok=True)
PREV=Path(WORKSPACE_DIR)/'resume'/'output'/'model';scene=bpy.context.scene
PARENT='1b03ae315e87e6243b57349532e954fe71f9a375cdc9c02d240a8d136e3daf44'
assert scene['project_id']==JOB['project_id'] and scene['job_id']=='form-v005'
assert hashlib.sha256((PREV/'model.blend').read_bytes()).hexdigest()==PARENT
COL={c.name:c for c in bpy.data.collections}
SHELL=bpy.data.materials['Clay | shell'];PANEL=bpy.data.materials['Clay | face and panel'];INNER=bpy.data.materials['Clay | inner ear']
DARK=bpy.data.materials['Inspection | internal'];EYE=bpy.data.materials['Inspection | eyes and nose'];CLOTH=bpy.data.materials['Inspection | bow tie'];TOOTH=bpy.data.materials['Clay | teeth'];METAL=bpy.data.materials['Inspection | connectors']
sources=[('base_geometry_source.py','4a81f39cf97f8990133e98de9f9c834e259b213a9699b25eab3020b53d554b5f',{'place','mesh','apply','ball','spow','tube','curve','fused','boolean'}),('form-v001_source.py','5d1276e96ed77008f7d02b409644c6bf5656991ecfbcbce0d5f0f44e2cfa63f0',{'fit','roundbox','orient','smooth'}),('form-v002_source.py','023d673f457493a9e6385a900694ffdff02f09aabe4cfc983396335d58390a46',{'fingerprint','closed_outline'}),('form-v003_source.py','26a1c6b8d55d238c1ca0e9eafb2d15e93bb5d8a869a3e774331f068547bc5099',{'deform','smoothstep'}),('form-v004_source.py','05dc9fc28b3a7e1e2d31e71debbe9cc5b2f0573bddb4794c37831fd49b935b8b',{'through','actual_bounds'})]
for filename,digest,names in sources:
    text=(PREV/filename).read_text();assert hashlib.sha256(text.encode()).hexdigest()==digest,filename
    nodes=[n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name in names];assert {n.name for n in nodes}==names
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<verified '+filename+'>','exec'),globals())
before={o.name:fingerprint(o) for o in scene.objects if o.type in {'MESH','CURVE'}};changed=set()
def delete(name):
    if name in bpy.data.objects:changed.add(name);bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
def mark(name):changed.add(name);return bpy.data.objects[name]
scene['job_id']=JOB['job_id'];scene['geometry_revision']='form-v006 / convex muzzle, continuous cheeks and inset covers'
CACHE=OUT/'reference_render_cache';CACHE.mkdir(exist_ok=True)
CACHE_HASHES={'feet_detail.png': '1990751c17c277c3704dc579e1717897ee515007928370488cf4e71b93450c18', 'feet_uniform_clay.png': '961a4d09436f722c91174e4364cb649773e3c9a0638dea2148d65f969e04e588', 'ears_detail.png': 'bbc183d980a33648bb6e7ded6bbfd1f2693eba48508cf93cb62e4540b9379ca9', 'hand_detail.png': '465e7632bed1391e3a002088558ac4dce8be2507657182eea0eb4455fc9e5476', 'render_manifest.json': 'b59d231e46113896d790e879ff6d6a6f5965a601beb6ea999ad9b70ba5ab77b0', 'render_source.py': '620bf498b60347281d8b9384b0c55c9dab6a7d77c55f85171b7ed145a096a49c'}
for name,digest in CACHE_HASHES.items():
    source=Path(WORKSPACE_DIR)/'resume'/'output'/'render'/name
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest,name
    shutil.copy2(source,CACHE/name)
(OUT/'render_cache_audit.json').write_text(json.dumps({'source_job':'form-v005','files':CACHE_HASHES},indent=2))
# Retain executable source closure before a recoverable checkpoint is exposed.
for p in PREV.iterdir():
    if p.suffix in {'.py','.webp'}:
        rename={'geometry_source.py':'form-v005_source.py','implicit.py':'form-v005_implicit.py'}
        shutil.copy2(p,OUT/rename.get(p.name,p.name))
for name in ['accepted_parent_import.json','parent_release_manifest.json']:shutil.copy2(PREV/name,OUT/name)
for name in ['implicit.py','cheek.py']:
    path=Path(__file__).with_name(name);shutil.copy2(path,OUT/name)
    exec(compile(path.read_text(),str(path),'exec'),globals())
(OUT/'geometry_source.py').write_text(Path(__file__).read_text())
# Smooth implicit union replaces the old rounded-box slab. The cheek volume is continuous.
vertices,faces,mesher_report=isosurface(head_field,(-.270,-.385,1.565),(.270,.196,2.025),.0023)
delete('Head casing');head=mesh('Head casing',vertices,faces,'02_HEAD',SHELL);del vertices,faces
smooth(head,.0016,30)
# Each thin cover follows the front-facing root of the very same head field.
# A larger closed cutter seats it in a shallow real joint, rather than painting a line.
for sign,label in [(-1,'R'),(1,'L')]:
    delete('Cheek pad '+label)
    v,f=cheek_mesh(sign,front_surface,True);cutter=mesh('Cheek recess cutter '+label,v,f,'02_HEAD',SHELL)
    boolean(head,cutter,'DIFFERENCE')
    v,f=cheek_mesh(sign,front_surface,False);cheek=mesh('Cheek pad '+label,v,f,'02_HEAD',PANEL)
    smooth(cheek,None,3);cheek['construction']='Thin continuous-surface-following lower cover in a true shallow recess'
    fit(mark('Eye '+label),(sign*.069,-.211,1.823),(.075,.063,.079))
# Cosmetic material labels only; uniform-clay views must also show the real form.
head.data.materials.append(PANEL);head.data.materials.append(DARK)
for p in head.data.polygons:
    x,y,z=p.center;brow=1.861+.054*math.exp(-((abs(x)-.069)/.068)**2)
    p.material_index=1 if y<-.105 and z<brow else 0
    if y<-.130 and any(((x-s*.069)/.044)**2+((z-1.823)/.051)**2<1.01**2 for s in [-1,1]):p.material_index=2
for sign,label in [(-1,'R'),(1,'L')]:
    g=head.vertex_groups.new(name='Muzzle cushion '+label)
    ids=[v.index for v in head.data.vertices if .001<sign*v.co.x<.140 and v.co.y<-.265 and 1.592<v.co.z<1.747]
    assert len(ids)>100;g.add(ids,1.0,'REPLACE')
head['muzzle_construction']='Convex twin lobes with smooth nasal rise and integrated cheek bulk, narrow central lower cleft and inset independent covers'
(OUT/'implicit_surface_audit.json').write_text(json.dumps(mesher_report,indent=2))
delete('Nose');nose=ball('Nose',(0,-.332,1.669),(.060,.019,.027),'02_HEAD',EYE,128,96)
deform(nose,lambda p:(p.x*(.83+.17*(p.z-1.669)/.027),p.y,p.z))
# No changes to the already improved arms/fingers, jaw, teeth, ears, feet or body.
for name in ['model.py','implicit.py','cheek.py']:
    text=Path(__file__).with_name(name).read_text();title='SOURCE_form-v006_'+name
    block=bpy.data.texts.get(title) or bpy.data.texts.new(title);block.clear();block.write(text)
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
audit={'job_id':JOB['job_id'],'pass':all(checks.values()),'checks':checks,'bounds_method':'actual transformed mesh vertices','bounds_min':lo,'bounds_max':hi,'dimensions_m':[hi[k]-lo[k] for k in range(3)],'required_counts':counts,'closed_shell_checks':closed,'object_bounds':bounds,'objects':len(geos),'vertices':sum(len(o.data.vertices) for o in geos if o.type=='MESH'),'polygons':sum(len(o.data.polygons) for o in geos if o.type=='MESH'),'unchanged_object_fingerprints':preserved,'visual_review':'pending exact form-v006 images'}
(OUT/'geometry_audit.json').write_text(json.dumps(audit,indent=2));assert audit['pass'],json.dumps(checks)
(OUT/'lineage.json').write_text(json.dumps({'project_id':JOB['project_id'],'from_job':'form-v005','to_job':JOB['job_id'],'source_blend_sha256':PARENT,'preserved_objects':sorted(preserved),'modified_or_replaced_objects':sorted(changed),'scope':'Geometry only; no repeated parent import or reconstruction of unaffected arms, hands, torso, hip, legs, feet, jaw, dentition, bow, tail and folded ears'},indent=2))

# Export exact evaluated head meshes to a portable NumPy container; no generated-image proxy.
export={};objects=[];deps=bpy.context.evaluated_depsgraph_get()
headnames={o.name for o in bpy.data.collections['02_HEAD'].objects}
headnames|={o.name for o in geos if o.name.startswith(('Whisker ','Socket lining ','Mouth internal'))}
for index,name in enumerate(sorted(headnames)):
    obj=bpy.data.objects[name]
    if obj.type not in {'MESH','CURVE'}:continue
    evaluated=obj.evaluated_get(deps);data=evaluated.to_mesh();data.calc_loop_triangles()
    key='o'+str(index);verts=np.asarray([evaluated.matrix_world@v.co for v in data.vertices],dtype=np.float32)
    triangles=np.asarray([p.vertices[:] for p in data.loop_triangles],dtype=np.int32)
    export[key+'_vertices']=verts;export[key+'_triangles']=triangles
    objects.append({'key':key,'name':name,'vertices':len(verts),'triangles':len(triangles),'material':obj.active_material.name if obj.active_material else ''})
    evaluated.to_mesh_clear()
np.savez_compressed(OUT/'head_geometry.npz',**export)
(OUT/'head_geometry.json').write_text(json.dumps({'project_id':JOB['project_id'],'job_id':JOB['job_id'],'coordinates':'world metres, -Y front, +Z up','objects':objects,'npz_sha256':hashlib.sha256((OUT/'head_geometry.npz').read_bytes()).hexdigest()},indent=2))

bpy.ops.object.select_all(action='DESELECT');checkpoint('form-v006-ready','Editable geometry, exact lineage and technical audit saved; final-image comparison remains mandatory')
