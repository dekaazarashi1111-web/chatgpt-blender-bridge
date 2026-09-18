"""Build review sheets and validate real output files; this does not approve appearance."""
from pathlib import Path
import hashlib
import json
import shutil
import numpy as np
from PIL import Image, ImageDraw

OUT=Path(OUTPUT_DIR);OUT.mkdir(parents=True,exist_ok=True)
root=Path(WORKSPACE_DIR)/'output'
render=root/'presentation';vp=render/'views'
geom=json.loads((root/'model'/'geometry_validation.json').read_text())
maps=json.loads((root/'textures'/'texture_validation.json').read_text())
modeltool=json.loads((root/'model'/'tool_report.json').read_text())
rendertool=json.loads((render/'tool_report.json').read_text())
assert geom['pass'] and maps['pass']
for report in (modeltool,rendertool):
    assert report['state']=='succeeded'
    assert report['validation']['reopened'] and report['validation']['pass']
    assert not report['validation']['missing_external_files']

sheet=Image.new('RGB',(3072,1024))
records=[]
for n,name in enumerate(['front','right','back']):
    with Image.open(vp/(name+'.png')) as image:
        image.load();assert image.size==(1024,1024)
        a=np.asarray(image.convert('RGB'))
        assert float(a.std())>5
        sheet.paste(image,(n*1024,0))
        bg=np.median(np.concatenate([a[0],a[-1]],axis=0),axis=0)
        mask=np.max(np.abs(a.astype(float)-bg),axis=2)>10
        yy,xx=np.where(mask)
        records.append({'view':name,'foreground_bbox_px':[int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())],
                        'touches_frame':bool(mask[0].any() or mask[-1].any() or mask[:,0].any() or mask[:,-1].any()),
                        'background_rgb':bg.tolist(),'standard_deviation':float(a.std())})
sheet.save(OUT/'three_view.png')
ref=Image.open(Path(INPUT_DIR)/'reference.webp').convert('RGB').resize((3072,1024),Image.Resampling.LANCZOS)
comparison=Image.new('RGB',(3072,2120),(42,42,42));draw=ImageDraw.Draw(comparison)
comparison.paste(ref,(0,28));comparison.paste(sheet,(0,1092))
draw.text((18,9),'USER REFERENCE / uploaded pixels (lossy WebP copy)',fill=(230,230,230))
draw.text((18,1073),'BUILD-V001 / actual Blender model renders - unreviewed',fill=(230,230,230))
comparison.save(OUT/'comparison.png')
details=Image.new('RGB',(3072,1024))
for i,name in enumerate(['face','face_profile','surface']):
    with Image.open(vp/(name+'.png')) as im:details.paste(im,(i*1024,0))
details.save(OUT/'details.png')
shutil.copyfile(render/'model.blend',OUT/'worn_violet_rabbit.blend')
assets=[]
for p in sorted(root.rglob('*')):
    if p.is_file() and p.suffix.lower() in {'.blend','.png','.webp','.json'}:
        assets.append({'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,
                       'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
report={'technical_pass':True,'visual_review':'REQUIRED - not automatically approved',
        'project_id':'worn-violet-rabbit-20260918','job_id':'build-v001',
        'geometry':geom,'maps':maps,'save_reopen':[modeltool['validation'],rendertool['validation']],
        'framing':records,'files':assets,
        'reference_webp_sha256':hashlib.sha256((Path(INPUT_DIR)/'reference.webp').read_bytes()).hexdigest(),
        'remaining_acceptance':'Open three_view.png, comparison.png and details.png; evaluate against BRIEF.md.'}
(OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
(OUT/'DELIVERY_README.txt').write_text('Worn violet rabbit / build-v001\n\n'
    'Editable scene: worn_violet_rabbit.blend (packed textures and reference).\n'
    'Reference-aligned renders: three_view.png; comparison.png places the user reference above the actual model.\n'
    'Detail evidence: details.png, plus output/presentation/views/*.png.\n'
    'Deterministic source textures: output/textures/*.png; 2048x2048 PBR maps.\n'
    'Reopen and dependency checks: verification.json and step tool_report.json files.\n'
    'The output is a reconstructed 3D asset, not the source image or its original mesh/UVs.\n'
    'No rig/animation/3D-printing certification. Visual review is a separate requirement.\n'
    'Source, instructions and authoritative snapshot pointers are in the project on GitHub.\n')
checkpoint('review-delivery','Editable scene, real render sheets and technical verification are ready for visual review')
