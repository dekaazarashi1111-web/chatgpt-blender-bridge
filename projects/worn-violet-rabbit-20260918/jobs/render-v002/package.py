"""Package actual renders; technical verification is not artistic approval."""
from pathlib import Path
import hashlib
import json
import shutil
import numpy as np
from PIL import Image, ImageDraw

OUT=Path(OUTPUT_DIR);OUT.mkdir(parents=True,exist_ok=True)
root=Path(WORKSPACE_DIR)/'output';render=root/'presentation';vp=render/'views'
job_id=JOB['job_id'];project=JOB['project_id']
geom=json.loads((root/'model'/'geometry_validation.json').read_text())
reports=[json.loads((root/f/'tool_report.json').read_text()) for f in ('model','presentation')]
for report in reports:
    assert report['state']=='succeeded'
    assert report['validation']['reopened'] and report['validation']['pass']
    assert not report['validation']['missing_external_files']
assert geom['pass']
images={}
framing=[]
for name in ('front','right','back','face','face_profile','surface','three_quarter'):
    im=Image.open(vp/(name+'.png')).convert('RGB');im.load()
    assert im.size==(1024,1024)
    a=np.asarray(im)
    assert a.std()>5
    images[name]=im
    bg=np.median(np.concatenate([a[0],a[-1]],axis=0),axis=0)
    mask=np.max(np.abs(a.astype(float)-bg),axis=2)>10
    yy,xx=np.where(mask)
    framing.append({'view':name,'bbox':[int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())],
                    'touches_frame':bool(mask[0].any() or mask[-1].any() or mask[:,0].any() or mask[:,-1].any()),
                    'background_rgb':bg.tolist(),'image_std':float(a.std())})
# Match figure center spacing in the reference (400, 1024, 1648 at 2048px wide).
bg=tuple(int(x) for x in np.asarray(images['front'])[0,0])
sheet=Image.new('RGB',(3072,1024),bg)
for name,cx in zip(('front','right','back'),(600,1536,2472)):
    info=next(r for r in framing if r['view']==name)
    x0,y0,x1,y1=info['bbox'];x0=max(0,x0-4);x1=min(1024,x1+5)
    crop=images[name].crop((x0,0,x1,1024))
    sheet.paste(crop,(cx-512+x0,0))
sheet.save(OUT/'three_view.png')
ref=Image.open(Path(INPUT_DIR)/'reference.webp').convert('RGB').resize((3072,1024),Image.Resampling.LANCZOS)
comparison=Image.new('RGB',(3072,2112),(42,42,42));draw=ImageDraw.Draw(comparison)
comparison.paste(ref,(0,24));comparison.paste(sheet,(0,1080))
draw.text((16,7),'USER REFERENCE / saved image pixels (lossy full-resolution copy)',fill=(230,230,230))
draw.text((16,1063),job_id+' / actual Blender render; see exact-version review',fill=(230,230,230))
comparison.save(OUT/'comparison.png')
details=Image.new('RGB',(3072,1024),bg)
for i,name in enumerate(('face','face_profile','surface')):details.paste(images[name],(1024*i,0))
details.save(OUT/'details.png')
shutil.copyfile(render/'model.blend',OUT/'worn_violet_rabbit.blend')
preview=OUT/'previews';preview.mkdir(exist_ok=True)
for name,im in [('three_view',sheet),('comparison',comparison),('details',details)]:
    copy=im.copy();copy.thumbnail((1536,1200),Image.Resampling.LANCZOS);copy.save(preview/(name+'.png'),optimize=True)
for name in ('front','right','back','three_quarter'):
    copy=images[name].copy();copy.thumbnail((768,768),Image.Resampling.LANCZOS);copy.save(preview/(name+'.png'),optimize=True)
files=[]
for p in sorted(root.rglob('*')):
    if p.is_file() and p.suffix.lower() in {'.blend','.png','.webp','.json'}:
        files.append({'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,
                       'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(OUT/'verification.json').write_text(json.dumps({
    'technical_pass':True,'visual_review':'REQUIRED - not approved automatically','project_id':project,
    'job_id':job_id,'geometry_revision':geom.get('revision'), 'geometry':geom,
    'save_reopen':[r['validation'] for r in reports], 'framing':framing,'files':files,
    'reference_sha256':hashlib.sha256((Path(INPUT_DIR)/'reference.webp').read_bytes()).hexdigest()
},indent=2)+'\n')
(OUT/'DELIVERY_README.txt').write_text(
    project+' / '+job_id+'\n\nEditable scene: worn_violet_rabbit.blend (packed dependencies).\n'
    'Reference comparison: comparison.png (reference above actual rendering).\n'
    'Three-view: three_view.png. Face/profile/surface: details.png.\n'
    'The 2048px texture maps and their deterministic source are retained.\n'
    'No rig, animation, or print-ready certification. Source UV maps were not recovered.\n'
    'Technical save/reopen success does not constitute visual acceptance. Read the pinned project review.\n')
checkpoint('rendered-delivery','Real comparison views, packed scene and file verification saved for review')
