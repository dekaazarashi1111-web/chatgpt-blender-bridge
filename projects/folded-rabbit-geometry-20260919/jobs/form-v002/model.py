"""Execute the review-driven model program with the preflight center-rotation fix.
Keep both the authored template and the exact executed source in the snapshot.
"""
from pathlib import Path
import shutil
source=Path(__file__).with_name('refine.py').read_text()
old='    o.rotation_euler[2]=-t*.35'
new="    center=Vector((x,y,z));rotation=Matrix.Rotation(-t*.35,3,'Z')\n    for vertex in o.data.vertices:vertex.co=center+rotation@(vertex.co-center)"
assert source.count(old)==1
source=source.replace(old,new)
target=Path(OUTPUT_DIR)/'executed_refine.py';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(source)
shutil.copy2(Path(__file__),target.parent/'model_entry.py')
shutil.copy2(Path(__file__).with_name('refine.py'),target.parent/'refine_template.py')
namespace=dict(globals());namespace['__file__']=str(target)
exec(compile(source,str(target),'exec'),namespace)
