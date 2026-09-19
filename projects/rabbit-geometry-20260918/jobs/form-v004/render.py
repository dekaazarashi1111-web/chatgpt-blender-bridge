"""Extend the hash-verified v003 renderer; save the fully expanded execution source."""
import hashlib
from pathlib import Path
parent=Path(WORKSPACE_DIR)/'resume'/'output'/'render'/'render_source.py'
source=parent.read_text()
assert hashlib.sha256(source.encode()).hexdigest()=='89237380f97a2284ec45f4000770e7602c9c6d4e4445c0f42631cc629d6162f4'
anchor="for o in geos:o.hide_render=original_hide[o.name]\nsh.color_type='MATERIAL'"
assert source.count(anchor)==1
extra="""arm_names={'Upper arm shell R','Exposed upper arm interior','Upper arm fine fracture'}
image('arm_damage_detail',(-2,-4,3),(-.365,0,1.24),.46,1100,arm_names)
thigh_names={'Thigh shell R','Thigh shell L','Right thigh interior','Left thigh interior'}
image('thigh_front_detail',(0,-6,.64),(0,0,.64),.59,1100,thigh_names)
image('thigh_back_detail',(0,6,.64),(0,0,.64),.59,1100,thigh_names)
"""
source=source.replace(anchor,extra+anchor).replace('13 frustum-checked','16 frustum-checked')
out=Path(OUTPUT_DIR);out.mkdir(parents=True,exist_ok=True)
path=out/'executed_render.py';path.write_text(source)
__file__=str(path)
exec(compile(source,str(path),'exec'),globals())
