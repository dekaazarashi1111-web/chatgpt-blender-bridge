"""Package verified geometry and align real render pixels to the supplied orthographic scale."""
import json,shutil,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
OUT=Path(OUTPUT_DIR);OUT.mkdir(parents=True,exist_ok=True)
model=Path(WORKSPACE_DIR)/'output'/'model';render=Path(WORKSPACE_DIR)/'output'/'render'
for p in model.iterdir():
    if p.suffix in {'.py','.json','.webp'} and p.name not in {'tool_report.json','validation.json'}:shutil.copy2(p,OUT/p.name)
shutil.copy2(model/'model.blend',OUT/'rabbit_geometry.blend')
for p in render.glob('*.png'):shutil.copy2(p,OUT/p.name)
for name in ['render_manifest.json','render_source.py']:shutil.copy2(render/name,OUT/name)
shutil.copy2(Path(__file__),OUT/'package_source.py')
font=ImageFont.load_default(size=24)
ref=Image.open(model/'reference.webp').convert('RGB')
# The reference is 300px/m. Full renders are 1200px / 2.4m = 500px/m.
# This affine mapping preserves scale and places the feet at source y=672.
turnaround=Image.new('RGB',ref.size,(102,102,102));overlay=np.array(ref).copy()
qa={}
arr=np.array(ref);bg=np.median(arr[:,:60],axis=1)[:,None,:]
est=((arr.max(2).astype(float)-arr.min(2)>5)|(np.max(abs(arr.astype(float)-bg),axis=2)>19))
for name,x0,x1,cx in [('front',75,726,400),('right',916,1125,1031),('back',1324,1972,1648)]:
    im=Image.open(render/(name+'.png')).convert('RGBA')
    aligned=im.transform((x1-x0,682),Image.Transform.AFFINE,(5/3,0,600+(x0-cx)*5/3,0,5/3,40),Image.Resampling.BICUBIC)
    bgim=Image.new('RGBA',aligned.size,(102,102,102,255));bgim.alpha_composite(aligned);turnaround.paste(bgim.convert('RGB'),(x0,0))
    a=np.array(aligned.getchannel('A'))>127
    raw=Image.fromarray(est[:,x0:x1].astype('uint8')*255)
    target=np.array(raw.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3)))>127
    # No flood fill: it incorrectly fills the intentional gap between the legs.
    def edge(mask):
        m=Image.fromarray(mask.astype('uint8')*255)
        return np.array(m.filter(ImageFilter.MaxFilter(3)))!=np.array(m.filter(ImageFilter.MinFilter(3)))
    region=overlay[:,x0:x1];region[edge(target)]=(255,180,60);region[edge(a)]=(30,225,255)
    qa[name]={'estimated_silhouette_iou':float((a&target).sum()/(a|target).sum()),'scope':'Approximate image-mask overlap only, not reconstruction accuracy. Shadow, gaps, whiskers and compression influence this estimate.'}
turnaround.save(OUT/'matched_scale_turnaround.png')
Image.fromarray(overlay).save(OUT/'silhouette_overlay.png')
comparison=Image.new('RGB',(2048,1468),(37,37,37));d=ImageDraw.Draw(comparison)
d.text((18,7),'SUPPLIED REFERENCE / 300 px per metre',font=font,fill='white');comparison.paste(ref,(0,44))
d.text((18,737),'ACTUAL GEOMETRY / same scale, same camera axes and foot baseline',font=font,fill='white');comparison.paste(turnaround,(0,778))
comparison.save(OUT/'reference_comparison.jpg',quality=94)
def flatten(path,size):
    im=Image.open(path).convert('RGBA');b=Image.new('RGBA',im.size,(102,102,102,255));b.alpha_composite(im);b=b.convert('RGB');b.thumbnail(size);return b
contact=Image.new('RGB',(1800,1290),(44,44,44));d=ImageDraw.Draw(contact)
for i,name in enumerate(['front','right','back','head_front','head_three_quarter','head_uniform_clay']):
    x=i%3*600;y=i//3*645;contact.paste(flatten(render/(name+'.png'),(600,600)),(x,y+40));d.text((x+18,y+8),name,font=font,fill='white')
contact.save(OUT/'geometry_contact_sheet.jpg',quality=94)
(OUT/'silhouette_estimates.json').write_text(json.dumps(qa,indent=2))
audit=json.loads((model/'geometry_audit.json').read_text());renders=json.loads((render/'render_manifest.json').read_text())
report={'project_id':JOB['project_id'],'job_id':JOB['job_id'],'geometry_audit_pass':audit['pass'],'model_reopen':json.loads((model/'tool_report.json').read_text())['validation'],'render_reopen':json.loads((render/'tool_report.json').read_text())['validation'],'all_frustum_checks_pass':all(v['frustum_pass'] for v in renders),'image_checks':[], 'visual_review':'pending exact generated-image inspection'}
for p in OUT.glob('*.png'):
    with Image.open(p) as im:
        im.load();border_clear=None
        if im.mode=='RGBA':
            a=np.array(im.getchannel('A'));border_clear=not bool(a[0].any() or a[-1].any() or a[:,0].any() or a[:,-1].any())
            assert border_clear, 'Image border clips geometry: '+p.name
        report['image_checks'].append({'file':p.name,'size':list(im.size),'decoded':True,'alpha_border_clear':border_clear})
assert report['geometry_audit_pass'] and report['model_reopen']['pass'] and report['render_reopen']['pass'] and report['all_frustum_checks_pass']
report['files']=[{'path':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(OUT.iterdir()) if p.is_file()]
(OUT/'delivery_report.json').write_text(json.dumps(report,indent=2))
(OUT/'README.txt').write_text('GEOMETRY ONLY. Open rabbit_geometry.blend. All imagery is rendered from that revised geometry, never AI-generated or texture-projected. Compare matched_scale_turnaround.png with the reference; the scale is identical. The head and hands have named vertex regions for later editing; no articulated rig, final UVs or textures are claimed. base_geometry_source.py plus geometry_source.py and lineage.json document the verified v001-to-v002 changes. Source reference is packed. Exact visual acceptance requires the pinned GitHub review for this job.\n')
checkpoint('revised-delivery','Editable revised blend, exact-scale actual images, isolated details, dependency chain and validations packaged')
