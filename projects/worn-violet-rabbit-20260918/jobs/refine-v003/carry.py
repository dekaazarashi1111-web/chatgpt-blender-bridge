from pathlib import Path
import shutil
import json
import hashlib

root=Path(WORKSPACE_DIR);source=root/'resume'/'output'
report=json.loads((source/'presentation'/'tool_report.json').read_text())
assert report['state']=='succeeded' and report['validation']['pass']
assert report['validation']['reopened'] and not report['validation']['missing_external_files']
records=[]
for folder in ('textures','model'):
    dst=root/'output'/folder
    assert not dst.exists(), 'Never replace a current job output during carry'
    shutil.copytree(source/folder,dst)
    # Old camera images must not masquerade as renders of the revised geometry.
    shutil.rmtree(dst/'previews',ignore_errors=True)
    for p in sorted(dst.rglob('*')):
        if p.is_file():
            records.append({'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,
                            'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
Path(OUTPUT_DIR).mkdir(parents=True,exist_ok=True)
(Path(OUTPUT_DIR)/'carry_report.json').write_text(json.dumps({
    'pass':True,'source_job':'render-v002','source_blend':'resume/output/presentation/model.blend',
    'method':'Retain editable source maps and original model provenance. Revision step will modify only selected parts of the restored scene.',
    'stale_previews_removed':True,'files':records},indent=2)+'\n')
checkpoint('carry-reference-assets','Verified saved scene and source maps retained; stale camera images excluded')
