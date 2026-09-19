"""Preserve editable geometry, real input derivatives and side-by-side evidence."""
from pathlib import Path
import json,hashlib,shutil
from PIL import Image,ImageDraw,ImageFont
import numpy as np
OUT=Path(OUTPUT_DIR);OUT.mkdir(parents=True,exist_ok=True)
MODEL=Path(WORKSPACE_DIR)/'output'/'model';RENDER=Path(WORKSPACE_DIR)/'output'/'render'
for root in [MODEL,RENDER]:
    check=json.loads((root/'validation.json').read_text());assert check.get('pass') is True,check
assert json.loads((MODEL/'geometry_audit.json').read_text())['pass']
records=json.loads((RENDER/'render_manifest.json').read_text());assert len(records)==13 and all(x['frustum_pass'] for x in records)
for p in MODEL.iterdir():
    if p.suffix in {'.json','.py','.webp'}:shutil.copy2(p,OUT/p.name)
shutil.copy2(RENDER/'model.blend',OUT/'folded_rabbit_geometry.blend')
shutil.copy2(RENDER/'validation.json',OUT/'render_reopen_validation.json')
shutil.copy2(RENDER/'render_manifest.json',OUT/'render_manifest.json')
shutil.copy2(RENDER/'render_source.py',OUT/'render_source.py')
shutil.copy2(Path(__file__),OUT/'package_source.py')
for item in records:
    p=RENDER/item['file'];im=Image.open(p);im.verify();im=Image.open(p)
    assert list(im.size)==item['pixels'];shutil.copy2(p,OUT/p.name)
font=ImageFont.load_default(size=20)
def white(im):
    rgba=im.convert('RGBA');bg=Image.new('RGBA',rgba.size,'white');bg.alpha_composite(rgba);return bg.convert('RGB')
def contained(im,w,h):
    im=im.copy();im.thumbnail((w,h),Image.Resampling.LANCZOS);out=Image.new('RGB',(w,h),'white');out.paste(white(im),((w-im.width)//2,(h-im.height)//2));return out
sheet=Image.new('RGB',(1440,950),'white');draw=ImageDraw.Draw(sheet)
for i,name in enumerate(['front','right','back']):
    ref='side' if name=='right' else name
    draw.text((i*480+18,12),ref.upper()+' / supplied reference',font=font,fill='black')
    sheet.paste(contained(Image.open(MODEL/(ref+'.webp')),456,400),(i*480+12,48))
    draw.text((i*480+18,466),'CURRENT GEOMETRY / '+JOB['job_id'],font=font,fill='black')
    im=Image.open(RENDER/(name+'.png')).convert('RGBA');box=im.getchannel('A').getbbox();assert box
    sheet.paste(contained(im.crop(box),456,420),(i*480+12,507))
sheet.save(OUT/'reference_comparison.jpg',quality=93)
contact=Image.new('RGB',(1500,1060),'white');draw=ImageDraw.Draw(contact)
for i,name in enumerate(['front','right','back','three_quarter','head_three_quarter','head_uniform_clay']):
    x=(i%3)*500;y=(i//3)*530;draw.text((x+12,y+10),name.replace('_',' '),font=font,fill='black')
    contact.paste(contained(Image.open(RENDER/(name+'.png')),480,480),(x+10,y+40))
contact.save(OUT/'geometry_contact_sheet.jpg',quality=93)
readme='''# Folded rabbit geometry / '''+JOB['job_id']+'''
Open folded_rabbit_geometry.blend in Blender 4.0.2 or newer. Metres, front -Y.
This is editable geometry with named components and neutral inspection materials.
No final texture maps, finished UV layout or rig are supplied at this stage.
Reference WebPs are actual-pixel downsampled derivatives, not original PNG files.
The input hashes, lineage, geometry audit, reopened-file validations and 13 view
records accompany the model. A successful run is NOT a visual acceptance.
Read the pinned review and PROGRESS.md in the project repository before continuing.
'''
(OUT/'README.txt').write_text(readme)
files=[{'path':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(OUT.iterdir()) if p.is_file()]
(OUT/'delivery_manifest.json').write_text(json.dumps({'project_id':JOB['project_id'],'job_id':JOB['job_id'],'pass':True,'files':files,'visual_review':'pending'},indent=2))
checkpoint('geometry-delivery','Self-contained blend, 13 images, actual references and source/audit files are ready for visual review')
