from pathlib import Path
import bpy
import json

base=Path(__file__).resolve().parents[1]/'build-v001'/'render.py'
code=base.read_text()
assert 'scene.cycles.use_denoising=True' in code
code=code.replace('scene.cycles.samples=48','scene.cycles.samples=128')
code=code.replace('scene.cycles.adaptive_threshold=.035','scene.cycles.adaptive_threshold=.02')
code=code.replace('scene.cycles.use_denoising=True','scene.cycles.use_denoising=False')
code=code.replace("'samples':48", "'samples':128")
code=code.replace("'revision':'build-v001'", "'revision':JOB['job_id']")
for layer in bpy.context.scene.view_layers:
    if hasattr(layer,'cycles') and hasattr(layer.cycles,'use_denoising'):layer.cycles.use_denoising=False
assert bpy.context.scene['geometry_revision']==JOB['job_id']
exec(compile(code,str(base),'exec'),globals())
p=Path(OUTPUT_DIR)/'render_validation.json';report=json.loads(p.read_text())
report['denoising']=False;report['geometry_revision']=JOB['job_id']
report['comparison']='Same framing as render-v002; revised geometry, reference-derived albedo and calibrated lower studio illumination'
p.write_text(json.dumps(report,indent=2)+'\n')
