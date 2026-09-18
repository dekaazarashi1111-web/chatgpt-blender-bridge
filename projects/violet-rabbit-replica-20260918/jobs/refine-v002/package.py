"""Validate real files, preserve editable dependencies, and create review sheets."""
import hashlib
import json
import shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

out=Path(OUTPUT_DIR);out.mkdir(parents=True,exist_ok=True)
work=Path(WORKSPACE_DIR)/'output'
surfaces=work/'surfaces';model=work/'model';lookdev=work/'lookdev'
for folder in ['previews','textures','source','docs']: (out/folder).mkdir(exist_ok=True)
for step in [model,lookdev]:
    report=json.loads((step/'tool_report.json').read_text())
    assert report['state']=='succeeded',step
    assert report['validation']['reopened'] and report['validation']['pass']
    assert report['validation']['missing_external_files']==[]
shutil.copy2(lookdev/'model.blend',out/'violet-rabbit-replica.blend')
for p in surfaces.iterdir():
    if p.is_file():shutil.copy2(p,out/'textures'/p.name)
# Preserve the relative helper import as source/jobs/build-v001/geometry.py.
for jobdir in [Path(__file__).parents[1]/'build-v001',Path(__file__).parent]:
    target=out/'source'/'jobs'/jobdir.name;target.mkdir(parents=True,exist_ok=True)
    for p in jobdir.iterdir():
        if p.suffix in {'.py','.json'}:shutil.copy2(p,target/p.name)
for name in ['BRIEF.md','DECISIONS.md','INPUTS.md']:
    p=Path(__file__).parents[2]/name
    if p.is_file():shutil.copy2(p,out/'docs'/name)
for p in [model/'geometry_validation.json',model/'tool_report.json',lookdev/'render_settings.json',lookdev/'tool_report.json']:
    shutil.copy2(p,out/'docs'/(p.parent.name+'_'+p.name))
ref=Image.open(surfaces/'reference.webp').convert('RGB')
bg=(94,94,94)
images={}
for p in sorted((lookdev/'views').glob('*.png')):
    a=Image.open(p).convert('RGBA');alpha=np.asarray(a.getchannel('A'))
    assert alpha.max()>250 and float((alpha>128).mean())>.012,p
    b=Image.new('RGB',a.size,bg);b.paste(a,mask=a.getchannel('A'))
    assert np.asarray(b).std()>5,p
    b.save(out/'previews'/p.name);images[p.stem]=a
# Transparent cutouts place all three views at the reference's measured centres.
contact=Image.new('RGB',(2048,682),bg)
for key,cx in [('front',400),('right',1033),('back',1648)]:
    a=images[key].resize((682,682),Image.Resampling.LANCZOS)
    contact.paste(a,(cx-341,0),a.getchannel('A'))
contact.save(out/'previews'/'turnaround.png')
try: font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
except OSError: font=ImageFont.load_default()
sheet=Image.new('RGB',(2048,1436),bg);draw=ImageDraw.Draw(sheet)
draw.text((20,7),'REFERENCE | original dimensions; saved WebP copy',font=font,fill=(230,230,230))
sheet.paste(ref,(0,36));draw.text((20,723),'REFINE V002 | actual 3D render; appearance review pending',font=font,fill=(230,230,230))
sheet.paste(contact,(0,754));sheet.save(out/'previews'/'comparison.png')
measurements={}
for name,box in {'purple_back':(1609,322,1684,393),'pale_belly':(368,358,432,418)}.items():
    a=np.asarray(ref.crop(box),np.float32);b=np.asarray(contact.crop(box),np.float32)
    measurements[name]={'reference_rgb_mean':a.mean((0,1)).tolist(),'render_rgb_mean':b.mean((0,1)).tolist(),
                        'note':'Appearance diagnostic only: geometry/lighting are not perfectly registered.'}
report={'job_id':JOB['job_id'],'reopened_model_and_lookdev':True,'missing_external_files':[],
        'reference_input_verified':True,'images_checked_for_nonempty_alpha':sorted(images),
        'appearance_review':'pending_actual_inspection','colour_diagnostics':measurements}
(out/'package_validation.json').write_text(json.dumps(report,indent=2))
(out/'README.txt').write_text('Violet rabbit replica / violet-rabbit-replica-20260918\nEditable .blend with packed images. External maps and reproducible source are included.\nReference is a lossy full-dimension copy of the supplied PNG. This is a reconstructed mesh and surface, not the original asset.\nSee the project on main and workspace-state for the review pinned to this exact job and source commit. Execution success does not certify visual acceptance.\n')
files=[]
for p in sorted(out.rglob('*')):
    if p.is_file():files.append({'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(out/'delivery_files.json').write_text(json.dumps(files,indent=2))
checkpoint('delivery','Packed editable blend, maps, reference, source and real comparison sheets ready for review')
