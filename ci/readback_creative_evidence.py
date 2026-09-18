"""Read back existing Release manifests; never alter a snapshot or job state."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from bridge.artifacts import GitHubReleases, validate_manifest, MAX_MANIFEST_BYTES
from bridge.creative_jobs import load_creative_job
from bridge.workspace_store import WorkspaceStore


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--job',required=True);args=parser.parse_args()
    job,_=load_creative_job(ROOT/args.job,repo_root=ROOT)
    project,jid=job['project_id'],job['job_id']
    run,attempt=os.environ['GITHUB_RUN_ID'],os.environ.get('GITHUB_RUN_ATTEMPT','1')
    root=ROOT/'.creative-runs'/f'{project}-{jid}-{run}-{attempt}'
    result=json.loads((root/'host'/'result.json').read_text())
    assert result['project_id']==project and result['job_id']==jid and str(result['run_id'])==run
    destination=root/'host'/'evidence';destination.mkdir(exist_ok=True)
    repo=os.environ['GITHUB_REPOSITORY'];client=GitHubReleases(repo)
    store=WorkspaceStore(repo,result['source_commit'])
    pointers=[]
    if job.get('resume'):pointers.append(('resume',job['resume']))
    if result.get('latest_snapshot'):pointers.append(('latest',result['latest_snapshot']))
    evidence=[]
    for label,pin in pointers:
        release=client.release(pin['release_tag'])
        assert release['draft'] is False
        asset=next(a for a in release['assets'] if a['name']=='manifest.json')
        path=destination/(label+'-manifest.json')
        client.download(asset['id'],path,max_bytes=MAX_MANIFEST_BYTES,expected_sha256=pin['manifest_sha256'])
        manifest=json.loads(path.read_text())
        records=validate_manifest(manifest,repository=repo,project_id=pin['project_id'],job_id=pin['job_id'],
                                  tag=pin['release_tag'],archive_sha256=pin['archive_sha256'])
        archive=next(a for a in release['assets'] if a['name']=='workspace.tar.gz')
        assert archive['state']=='uploaded' and archive['size']==manifest['archive']['bytes']
        assert archive.get('digest')=='sha256:'+pin['archive_sha256'], 'Server digest must match the pinned archive'
        base=root/'work' if label=='latest' else root/'work'/'resume'
        checked=[]
        for relative,entry in records.items():
            p=base/relative
            assert p.is_file() and not p.is_symlink(), relative
            digest=hashlib.sha256(p.read_bytes()).hexdigest()
            assert p.stat().st_size==entry['bytes'] and digest==entry['sha256'], relative
            checked.append(relative)
        target=f'workspaces/{project}/evidence/{jid}/{label}-manifest.json'
        store.write_file(target,path.read_bytes(),f'evidence({project}): verified {jid} {label} manifest readback')
        evidence.append({'label':label,'release_tag':pin['release_tag'],'manifest_sha256':pin['manifest_sha256'],
                         'archive_sha256':pin['archive_sha256'],'archive_bytes':archive['size'],
                         'manifest_downloaded_and_hash_verified':True,'server_archive_digest_verified':True,
                         'local_files_verified_against_manifest':len(checked),'manifest_state_path':target})
    report={'pass':True,'project_id':project,'job_id':jid,'run_id':run,'source_commit':result['source_commit'],
            'evidence':evidence,'scope':'Downloaded exact Release manifest bytes; matched every manifest file to stopped local outputs/resume and server archive digest. The archive itself was not downloaded again by this audit.'}
    p=destination/'readback.json';p.write_text(json.dumps(report,indent=2)+'\n')
    store.write_file(f'workspaces/{project}/evidence/{jid}/readback.json',p.read_bytes(),f'evidence({project}): {jid} readback audit')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
