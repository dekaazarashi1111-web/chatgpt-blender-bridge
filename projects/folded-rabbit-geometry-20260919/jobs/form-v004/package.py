"""Package this job's verified editable scene and sources."""
from pathlib import Path
import hashlib,shutil
p=Path(WORKSPACE_DIR)/'resume'/'output'/'package'/'package_source.py'
source=p.read_text();assert hashlib.sha256(source.encode()).hexdigest()=='9511aed29099eb0e4bda972fb9db50e4828054e04bfad4aad41ed924bc4d3e2c'
target=Path(OUTPUT_DIR)/'executed_package.py';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(source)
shutil.copy2(Path(__file__),target.parent/'package_entry.py')
namespace=dict(globals());namespace['__file__']=str(target)
exec(compile(source,str(target),'exec'),namespace)
