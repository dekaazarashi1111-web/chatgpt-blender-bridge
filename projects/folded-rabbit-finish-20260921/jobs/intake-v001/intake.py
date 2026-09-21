"""Verified new-project continuation import. No geometry changes or visual verdict.
Uses the existing snapshot validator and leaves same-project resume policy intact.
"""
import sys, json, hashlib, shutil, tempfile, urllib.request
from pathlib import Path
from PIL import Image
sys.path.insert(0, '/repo')
from bridge.artifacts import extract_snapshot, validate_manifest
OUT=Path(OUTPUT_DIR); OUT.mkdir(parents=True, exist_ok=True)
REPO='dekaazarashi1111-web/chatgpt-blender-bridge'
PARENT_PROJECT='folded-rabbit-geometry-20260919'; PARENT_JOB='form-v006'
TAG='creative-folded-rabbit-geometry-20260919-form-v006-35439434026-1-3'
AH='29e9252abf66f7264d1386edfa8b8b6db290a5f345014eaa513dac04864318b7'
MH='31ad5a6d25a1d0bdef78b32ead9185a2b846362c541f5c50af53696b9d865951'
SOURCE='a2c964a566719aaa8364947a1ecddf9c0a35165b'
URL='https://github.com/'+REPO+'/releases/download/'+TAG+'/'

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def download(name, destination, limit, expected):
    request=urllib.request.Request(URL+name, headers={'User-Agent':'creative-continuation-import/1.0'})
    count=0; h=hashlib.sha256()
    with urllib.request.urlopen(request,timeout=120) as response, destination.open('xb') as target:
        while True:
            chunk=response.read(1024*1024)
            if not chunk: break
            count+=len(chunk)
            if count>limit: raise RuntimeError('Download exceeds manifest size limit')
            target.write(chunk); h.update(chunk)
    if h.hexdigest()!=expected: raise RuntimeError('Pinned '+name+' hash mismatch')
    return count

with tempfile.TemporaryDirectory(prefix='verified-v006-') as directory:
    temp=Path(directory); mp=temp/'manifest.json'; ap=temp/'workspace.tar.gz'
    download('manifest.json',mp,1024*1024,MH)
    manifest=json.loads(mp.read_bytes())
    validate_manifest(manifest,repository=REPO,project_id=PARENT_PROJECT,job_id=PARENT_JOB,tag=TAG,archive_sha256=AH)
    assert manifest['metadata']['source_commit']==SOURCE
    received=download('workspace.tar.gz',ap,manifest['archive']['bytes'],AH)
    assert received==manifest['archive']['bytes']
    restored=temp/'restored'
    extract_snapshot(ap,restored,manifest,repository=REPO,project_id=PARENT_PROJECT,job_id=PARENT_JOB,tag=TAG,archive_sha256=AH)
    shutil.copy2(mp,OUT/'parent_release_manifest.json')
    parent=restored/'output'/'model'
    assert (parent/'model.blend').is_file()
    shutil.copytree(parent,OUT/'model')
    # Keep only one editable scene, not redundant scene copies from the render/package steps.
    records={entry['path']:entry for entry in manifest['files']}
    model_entry=records['output/model/model.blend']
    assert digest(OUT/'model'/'model.blend')==model_entry['sha256']
    visual=OUT/'visual'; visual.mkdir()
    index=[]
    for section in ['render','package']:
        root=restored/'output'/section
        if not root.exists(): continue
        for original in sorted(root.rglob('*')):
            if not original.is_file(): continue
            rel=original.relative_to(root)
            if original.suffix.lower() in {'.png','.jpg','.jpeg','.webp'}:
                destination=visual/section/rel; destination.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(original,destination)
                with Image.open(destination) as image:
                    image.load(); size=list(image.size)
                index.append({'path':destination.relative_to(OUT).as_posix(),'source_path':original.relative_to(restored).as_posix(),'sha256':digest(destination),'bytes':destination.stat().st_size,'size':size,'render_job':PARENT_JOB,'geometry_changed':False})
            elif original.suffix in {'.json','.py','.md','.txt'}:
                destination=OUT/'upstream_evidence'/section/rel
                destination.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(original,destination)
    refs=OUT/'references'; refs.mkdir()
    for item in JOB['inputs']:
        source=Path(INPUT_DIR)/item['target']; assert digest(source)==item['sha256']
        shutil.copy2(source,refs/Path(item['target']).name)
    report={'project_id':JOB['project_id'],'job_id':JOB['job_id'],'pass':True,'operation':'verified explicit new-project import; unchanged geometry','parent_project_id':PARENT_PROJECT,'parent_job_id':PARENT_JOB,'parent_source_commit':SOURCE,'parent_release_tag':TAG,'parent_archive_sha256':AH,'parent_manifest_sha256':MH,'downloaded_archive_bytes':received,'verified_parent_files':manifest['file_count'],'model':{'path':'model/model.blend','sha256':model_entry['sha256'],'bytes':model_entry['bytes']},'preview_count':len(index),'previews':index,'geometry_modified':False,'visual_review':'pending actual image access; no new geometry acceptance','next_action':'Open the inherited real previews. Then refine only observed mismatches in a new job; keep textures out of scope.'}
    (OUT/'continuation_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    (visual/'index.json').write_text(json.dumps(index,indent=2)+'\n')
    # A compact, decodable view pack is separate from the large editable model archive.
    assert len(index)>=13, 'Missing inherited preview set'
    shutil.copy2(Path(__file__),OUT/'intake_source.py')
    (OUT/'NEXT.md').write_text('Restore this project snapshot. Editable unchanged parent: output/intake/model/model.blend. Scene still carries its exact original v006 identity. Preserve and hash-check it before any edits. Parent images are visual-review pending, not accepted by this import.\n')
checkpoint('verified-continuation','Editable v006, executable dependencies, real previews and exact parent hashes saved; no geometry or visual-acceptance claim')
