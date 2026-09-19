"""Explicit new-project asset import; leaves same-project resume safeguards intact.
All bytes come from one public same-repository immutable Release, pinned by SHA256.
"""
import sys,json,hashlib,shutil,tempfile,urllib.request
from pathlib import Path
sys.path.insert(0,'/repo')
from bridge.artifacts import extract_snapshot,validate_manifest
OUT=Path(OUTPUT_DIR);OUT.mkdir(parents=True,exist_ok=True)
repository='dekaazarashi1111-web/chatgpt-blender-bridge'
parent_project='rabbit-geometry-20260918';parent_job='form-v003'
tag='creative-rabbit-geometry-20260918-form-v003-35427795287-1-3'
ah='2f3aae4e8f79ccb4e16abcfc618c9d6adb0d53d4ff225a23cf84f9b99d525cf5'
mh='dccba482459774e15e1dac8250b298778acee37937da4bc901b7217019efe74a'
url='https://github.com/'+repository+'/releases/download/'+tag+'/'
def download(name,dest,limit,expected):
    req=urllib.request.Request(url+name,headers={'User-Agent':'creative-reference-import/1.0'})
    h=hashlib.sha256();n=0
    with urllib.request.urlopen(req,timeout=120) as response,dest.open('xb') as out:
        while chunk:=response.read(1024*1024):
            n+=len(chunk);assert n<=limit,'Download exceeds pinned size limit';out.write(chunk);h.update(chunk)
    assert h.hexdigest()==expected,'Pinned parent asset hash mismatch'
    return n
with tempfile.TemporaryDirectory(prefix='verified-parent-') as temp:
    temp=Path(temp);mp=temp/'manifest.json';ap=temp/'workspace.tar.gz'
    download('manifest.json',mp,1024*1024,mh);manifest=json.loads(mp.read_bytes())
    validate_manifest(manifest,repository=repository,project_id=parent_project,job_id=parent_job,tag=tag,archive_sha256=ah)
    count=download('workspace.tar.gz',ap,manifest['archive']['bytes'],ah)
    assert count==manifest['archive']['bytes']
    extract_snapshot(ap,temp/'restored',manifest,repository=repository,project_id=parent_project,job_id=parent_job,tag=tag,archive_sha256=ah)
    target=OUT/'parent';target.mkdir()
    for name in ['model.blend','base_geometry_source.py','geometry_source.py','geometry_audit.json','validation.json']:
        shutil.copy2(temp/'restored'/'output'/'model'/name,target/name)
    shutil.copy2(mp,OUT/'parent_release_manifest.json')
    evidence={'pass':True,'operation':'explicit new-project import, not cross-project resume','source_project':parent_project,'source_job':parent_job,'source_release_tag':tag,'source_commit':manifest['metadata']['source_commit'],'archive_sha256':ah,'manifest_sha256':mh,'downloaded_archive_bytes':count,'all_extracted_files_verified':manifest['file_count'],'copied_files':[]}
    for p in sorted(target.iterdir()):evidence['copied_files'].append({'path':'parent/'+p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    (OUT/'import_evidence.json').write_text(json.dumps(evidence,indent=2))
shutil.copy2(Path(__file__),OUT/'import_source.py')
checkpoint('verified-parent-import','Parent Release archive and manifest downloaded and verified; editable model imported without changing resume policy')
