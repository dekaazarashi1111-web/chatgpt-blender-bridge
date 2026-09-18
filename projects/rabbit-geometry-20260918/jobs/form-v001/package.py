"""Package actual renders, source and editable .blend; create review comparisons."""
import json, shutil, hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
OUT=Path(OUTPUT_DIR);OUT.mkdir(parents=True,exist_ok=True)
model=Path(WORKSPACE_DIR)/'output'/'model';render=Path(WORKSPACE_DIR)/'output'/'render'
for name in ['geometry_audit.json','geometry_source.py','reference.webp']:
    shutil.copy2(model/name,OUT/name)
shutil.copy2(model/'model.blend',OUT/'rabbit_geometry.blend')
for p in render.glob('*.png'):shutil.copy2(p,OUT/p.name)
shutil.copy2(render/'render_manifest.json',OUT/'render_manifest.json')
shutil.copy2(Path(__file__),OUT/'package_source.py')
font=ImageFont.load_default(size=22)
def flat(p):
    im=Image.open(p).convert('RGBA');bg=Image.new('RGBA',im.size,(106,106,106,255));bg.alpha_composite(im);return bg.convert('RGB')
# Full-resolution source supplied to the job, versus geometry renders. No invented target image.
ref=Image.open(model/'reference.webp').convert('RGB')
canvas=Image.new('RGB',(2048,1500),(38,38,38));draw=ImageDraw.Draw(canvas)
canvas.paste(ref,(0,38));draw.text((20,7),'SUPPLIED TURNAROUND / source image (lossy reference copy)',font=font,fill='white')
for i,name in enumerate(['front','right','back']):
    im=flat(render/(name+'.png'));im.thumbnail((678,678));canvas.paste(im,(i*684,776));draw.text((i*684+18,737),'GEOMETRY / '+name,font=font,fill='white')
canvas.save(OUT/'reference_comparison.jpg',quality=94)
contact=Image.new('RGB',(1800,1860),(54,54,54));d=ImageDraw.Draw(contact)
for i,name in enumerate(['front','right','back','head_front','head_three_quarter','head_uniform_clay']):
    im=flat(render/(name+'.png'));im.thumbnail((600,870));x=(i%3)*600;y=(i//3)*930
    contact.paste(im,(x,y+45));d.text((x+18,y+10),name,font=font,fill='white')
contact.save(OUT/'geometry_contact_sheet.jpg',quality=94)
records=[]
for p in sorted(OUT.iterdir()):
    if p.is_file():records.append({'path':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
audit=json.loads((OUT/'geometry_audit.json').read_text())
report={'job_id':JOB['job_id'],'geometry_audit_pass':audit['pass'],'model_reopen':json.loads((model/'tool_report.json').read_text())['validation'],'render_reopen':json.loads((render/'tool_report.json').read_text())['validation'],'images_checked_for_decode':[], 'files':records,'visual_review':'pending actual ChatGPT image inspection'}
for p in OUT.glob('*.png'):
    with Image.open(p) as im:im.load();report['images_checked_for_decode'].append({'file':p.name,'size':list(im.size),'mode':im.mode})
assert report['geometry_audit_pass'] and report['model_reopen']['pass'] and report['render_reopen']['pass']
(OUT/'delivery_report.json').write_text(json.dumps(report,indent=2))
(OUT/'README.txt').write_text('GEOMETRY ONLY. Open rabbit_geometry.blend. The original model stage and this delivery copy have identical bytes. Reference image is packed in the blend, not projected onto geometry. Named neutral materials are inspection labels; textures, final UVs and rigging are intentionally out of scope. Review reference_comparison.jpg, geometry_contact_sheet.jpg and full-size PNG views. A successful execution is not visual acceptance. See the pinned GitHub project review for this exact job.\n')
checkpoint('delivery','Editable geometry, decoded views, reports and references packaged; visual review pending')
