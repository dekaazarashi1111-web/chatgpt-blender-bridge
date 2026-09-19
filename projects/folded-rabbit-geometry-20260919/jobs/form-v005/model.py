"""Continue the verified v004 scene; geometry-only correction of actual reviewed defects."""
import ast,bpy,bmesh,math,json,hashlib,shutil,struct
from pathlib import Path
from mathutils import Vector,Matrix
from math import sin,cos,pi,sqrt
OUT=Path(OUTPUT_DIR);OUT.mkdir(parents=True,exist_ok=True)
PREV=Path(WORKSPACE_DIR)/'resume'/'output'/'model';scene=bpy.context.scene
PARENT='6f9c5d9fc58968a0b819b21b1239948b7f29db0ac424e313b9ff3f9878a16269'
assert scene['project_id']==JOB['project_id'] and scene['job_id']=='form-v004'
assert hashlib.sha256((PREV/'model.blend').read_bytes()).hexdigest()==PARENT
COL={c.name:c for c in bpy.data.collections}
SHELL=bpy.data.materials['Clay | shell'];PANEL=bpy.data.materials['Clay | face and panel'];INNER=bpy.data.materials['Clay | inner ear']
DARK=bpy.data.materials['Inspection | internal'];EYE=bpy.data.materials['Inspection | eyes and nose'];CLOTH=bpy.data.materials['Inspection | bow tie'];TOOTH=bpy.data.materials['Clay | teeth'];METAL=bpy.data.materials['Inspection | connectors']
sources=[('base_geometry_source.py','4a81f39cf97f8990133e98de9f9c834e259b213a9699b25eab3020b53d554b5f',{'place','mesh','apply','ball','spow','tube','curve','fused'}),('form-v001_source.py','5d1276e96ed77008f7d02b409644c6bf5656991ecfbcbce0d5f0f44e2cfa63f0',{'fit','roundbox','orient','smooth'}),('form-v002_source.py','023d673f457493a9e6385a900694ffdff02f09aabe4cfc983396335d58390a46',{'fingerprint','closed_outline'}),('form-v003_source.py','26a1c6b8d55d238c1ca0e9eafb2d15e93bb5d8a869a3e774331f068547bc5099',{'deform','smoothstep'}),('geometry_source.py','05dc9fc28b3a7e1e2d31e71debbe9cc5b2f0573bddb4794c37831fd49b935b8b',{'through','actual_bounds'})]
for filename,digest,names in sources:
    text=(PREV/filename).read_text();assert hashlib.sha256(text.encode()).hexdigest()==digest,filename
    nodes=[n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name in names];assert {n.name for n in nodes}==names
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<verified '+filename+'>','exec'),globals())
before={o.name:fingerprint(o) for o in scene.objects if o.type in {'MESH','CURVE'}};changed=set()
def delete(name):
    if name in bpy.data.objects:changed.add(name);bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
def mark(name):changed.add(name);return bpy.data.objects[name]
scene['job_id']=JOB['job_id'];scene['geometry_revision']='form-v005 / continuous implicit face, shaped cheeks and unpinched fingers'
# Shared-grid-edge welding produces one closed surface, without stacked latitude seams.
implicit_path=Path(__file__).with_name('implicit.py')
exec(compile(implicit_path.read_text(),str(implicit_path),'exec'),globals())
vertices,faces,mesher_report=isosurface(head_field,(-.258,-.385,1.565),(.258,.196,2.025),.0025)
delete('Head casing');head=mesh('Head casing',vertices,faces,'02_HEAD',SHELL);del vertices,faces
smooth(head,None,18)
head.data.materials.append(PANEL);head.data.materials.append(DARK)
for p in head.data.polygons:
    x,y,z=p.center;brow=1.861+.054*math.exp(-((abs(x)-.069)/.068)**2)
    if y<-.105 and z<brow:p.material_index=1
    if y<-.130 and any(((x-s*.069)/.044)**2+((z-1.823)/.053)**2<1.01**2 for s in [-1,1]):p.material_index=2
for s,label in [(-1,'R'),(1,'L')]:
    g=head.vertex_groups.new(name='Muzzle cushion '+label)
    ids=[v.index for v in head.data.vertices if .001<s*v.co.x<.133 and v.co.y<-.255 and 1.599<v.co.z<1.745]
    assert len(ids)>100;g.add(ids,1.0,'REPLACE')
head['muzzle_construction']='Two narrow padded lobes and nasal bridge smoothly united in a shared implicit field; central lower cleft; closed editable mesh'
(OUT/'implicit_surface_audit.json').write_text(json.dumps(mesher_report,indent=2))
# Cheek covers have a shaped inner edge following the muzzle, not an oval front button.
edge=closed_outline([(.130,1.641),(.163,1.649),(.195,1.672),(.227,1.714),(.240,1.748),(.232,1.783),(.208,1.799),(.180,1.784),(.146,1.765),(.135,1.740),(.139,1.705)],10)
for s,label in [(-1,'R'),(1,'L')]:
    delete('Cheek pad '+label);n=len(edge);nr=64;v=[];f=[]
    for i in range(nr):
        lat=-pi/2+pi*(i+.25)/(nr-.5);r=cos(lat)
        for xx,zz in edge:
            x=.182+(xx-.182)*r;z=1.722+(zz-1.722)*r
            y=-.185+1.25*(x-.185)+(.046 if lat>=0 else .041)*sin(lat)
            v.append((s*x,y,z))
    for i in range(nr-1):
        for j in range(n):a=i*n+j;b=i*n+(j+1)%n;f.append((a,b,b+n,a+n))
    f.extend([tuple(reversed(range(n))),tuple((nr-1)*n+j for j in range(n))])
    cheek=mesh('Cheek pad '+label,v,f,'02_HEAD',PANEL);smooth(cheek,.0014,9)
    fit(mark('Eye '+label),(s*.069,-.211,1.827),(.075,.063,.079))
    delete('Socket lining '+label);ball('Socket lining '+label,(s*.069,-.175,1.822),(.043,.049,.052),'09_INTERNAL',DARK,96,64)
# Rounded trapezoid/bean nose; no sharp inverted-triangle tip.
delete('Nose');nose=roundbox('Nose',(0,-.335,1.679),(.100,.044,.049),.019,'02_HEAD',EYE)
deform(nose,lambda p:(p.x*(.68+.32*smoothstep(1.654,1.700,p.z)),p.y,p.z))
smooth(nose,.0009,10)
checkpoint('continuous-face','Implicit crown, narrow twin muzzle, cheek cover seams and rounded nose saved')
# Blend the cap into its own upper-arm cover; do not remake the torso or the accepted lower limbs.
for s,label in [(-1,'R'),(1,'L')]:
    shoulder=mark('Shoulder cap '+label);arm=mark('Upper arm casing '+label)
    arm=fused('Upper arm casing '+label,[arm,shoulder],'04_ARMS',SHELL,.0017);smooth(arm,None,85)
    group=arm.vertex_groups.new(name='Shoulder transition')
    ids=[v.index for v in arm.data.vertices if (arm.matrix_world@v.co).z>1.435]
    if ids:group.add(ids,1.0,'REPLACE')
# Continuous curl with a gentle radius change, not the previous five-millimetre pinching controls.
for s,label in [(-1,'R'),(1,'L')]:
    for j,y in enumerate([-.055,0,.055],1):
        delete('Finger '+label+str(j))
        controls=[(s*.450,y,.858,.018),(s*.470,y,.835,.029),(s*.485,y,.808,.030),(s*.488,y,.784,.028),(s*.476,y,.757,.0285),(s*.453,y,.737,.027),(s*.434,y,.728,.021),(s*.424,y,.728,.010),(s*.421,y,.729,.0008)]
        pts=through(controls,12);offset=[-.002,-.008,.004][j-1]
        coords=[(p[0],p[1],p[2]+offset*smoothstep(.840,.745,p[2])) for p in pts]
        radii=[max(.0006,p[3]) for p in pts]
        finger=tube('Finger '+label+str(j),coords,radii,radii,'05_HANDS',SHELL,48);smooth(finger,.0010,8)
        finger['construction']='Continuous closed padded curl; slightly staggered tip; no narrow bead junction'
# Preserve the editable dependency closure, including the complete previous implementation.
for p in PREV.iterdir():
    if p.suffix in {'.py','.webp'}:shutil.copy2(p,OUT/('form-v004_source.py' if p.name=='geometry_source.py' else p.name))
for name in ['accepted_parent_import.json','parent_release_manifest.json']:shutil.copy2(PREV/name,OUT/name)
(OUT/'geometry_source.py').write_text(Path(__file__).read_text());shutil.copy2(implicit_path,OUT/'implicit.py')
for title,text in [('BUILD_folded_form-v005.py',Path(__file__).read_text()),('IMPLICIT_form-v005.py',implicit_path.read_text())]:
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
audit={'job_id':JOB['job_id'],'pass':all(checks.values()),'checks':checks,'bounds_method':'actual transformed mesh vertices','bounds_min':lo,'bounds_max':hi,'dimensions_m':[hi[k]-lo[k] for k in range(3)],'required_counts':counts,'closed_shell_checks':closed,'object_bounds':bounds,'objects':len(geos),'vertices':sum(len(o.data.vertices) for o in geos if o.type=='MESH'),'polygons':sum(len(o.data.polygons) for o in geos if o.type=='MESH'),'unchanged_object_fingerprints':preserved,'visual_review':'pending exact form-v005 images'}
(OUT/'geometry_audit.json').write_text(json.dumps(audit,indent=2));assert audit['pass'],json.dumps(checks)
(OUT/'lineage.json').write_text(json.dumps({'project_id':JOB['project_id'],'from_job':'form-v004','to_job':JOB['job_id'],'source_blend_sha256':PARENT,'preserved_objects':sorted(preserved),'modified_or_replaced_objects':sorted(changed),'scope':'Geometry only; no repeated parent import or reconstruction of unaffected torso, hip, lower legs, feet, bow, tail or folded ears'},indent=2))
bpy.ops.object.select_all(action='DESELECT');checkpoint('form-v005-ready','Editable geometry, exact lineage and technical audit saved; final-image comparison remains mandatory')
