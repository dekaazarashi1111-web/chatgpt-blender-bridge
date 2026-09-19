"""Render the new saved shape using the verified 13-view implementation."""
from pathlib import Path
import hashlib,shutil
p=Path(WORKSPACE_DIR)/'resume'/'output'/'render'/'render_source.py'
source=p.read_text();assert hashlib.sha256(source.encode()).hexdigest()=='2b033d1d49e690ad529731181399d5cdc1eb9cd6f6c5c0df08a145bb719c6611'
target=Path(OUTPUT_DIR)/'executed_render.py';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(source)
shutil.copy2(Path(__file__),target.parent/'render_entry.py')
namespace=dict(globals());namespace['__file__']=str(target)
exec(compile(source,str(target),'exec'),namespace)
