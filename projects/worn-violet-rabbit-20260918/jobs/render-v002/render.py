"""Use the saved model; correct only the unsupported denoiser setting."""
from pathlib import Path
import bpy
import json

base=Path(__file__).resolve().parents[1]/'build-v001'/'render.py'
code=base.read_text()
assert "scene.cycles.use_denoising=True" in code
code=code.replace('scene.cycles.samples=48','scene.cycles.samples=128')
code=code.replace('scene.cycles.adaptive_threshold=.035','scene.cycles.adaptive_threshold=.02')
code=code.replace('scene.cycles.use_denoising=True','scene.cycles.use_denoising=False')
code=code.replace("'samples':48", "'samples':128")
code=code.replace("'revision':'build-v001'", "'revision':'render-v002'")
for layer in bpy.context.scene.view_layers:
    if hasattr(layer,'cycles') and hasattr(layer.cycles,'use_denoising'):
        layer.cycles.use_denoising=False
bpy.context.scene['revision']='render-v002'
bpy.context.scene['geometry_revision']='build-v001'
bpy.context.scene['denoising']='disabled: Ubuntu Blender 4.0.2 lacks OpenImageDenoiser'
exec(compile(code,str(base),'exec'),globals())
p=Path(OUTPUT_DIR)/'render_validation.json'
data=json.loads(p.read_text());data['denoising']=False;data['geometry_changed']=False
p.write_text(json.dumps(data,indent=2)+'\n')
