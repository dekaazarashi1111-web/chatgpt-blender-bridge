from pathlib import Path
import shutil
import json
import hashlib

root=Path(WORKSPACE_DIR)
source=root/'resume'/'output'
report=json.loads((source/'model'/'tool_report.json').read_text())
assert report['state']=='succeeded'
assert report['validation']['pass'] and report['validation']['reopened']
assert not report['validation']['missing_external_files']
records=[]
for folder in ('textures','model'):
    dst=root/'output'/folder
    assert not dst.exists(), 'Do not overwrite a current output'
    shutil.copytree(source/folder,dst)
    for p in sorted(dst.rglob('*')):
        if p.is_file():
            records.append({'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,
                            'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
Path(OUTPUT_DIR).mkdir(parents=True,exist_ok=True)
(Path(OUTPUT_DIR)/'carry_report.json').write_text(json.dumps({
    'pass':True,'source_job':'build-v001','source_step':'model','geometry_changed':False,
    'materials_changed':False,'copied_files':records},indent=2)+'\n')
checkpoint('carry-verified-model','Preserved successful model and maps; no remodelling or texture regeneration')
