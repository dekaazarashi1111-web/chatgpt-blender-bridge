"""Reuse verified package checks and save the actual expanded script and corrected lineage text."""
import hashlib
from pathlib import Path
parent=Path(WORKSPACE_DIR)/'resume'/'output'/'package'/'package_source.py'
source=parent.read_text()
assert hashlib.sha256(source.encode()).hexdigest()=='169c0d95be992cded6debdac732596cf7d9953e5bde86e2b231ec32943b06d57'
source=source.replace('base_geometry_source.py plus geometry_source.py and lineage.json document the verified v001-to-v002 changes.','base_geometry_source.py, parent_form-v002_source.py, parent_form-v003_source.py, geometry_source.py and lineage.json preserve the verified v001 through v004 dependency chain.')
out=Path(OUTPUT_DIR);out.mkdir(parents=True,exist_ok=True)
path=out/'executed_package.py';path.write_text(source)
__file__=str(path)
exec(compile(source,str(path),'exec'),globals())
