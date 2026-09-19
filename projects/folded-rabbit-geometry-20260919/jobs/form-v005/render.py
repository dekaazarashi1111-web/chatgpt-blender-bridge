"""Reuse accepted isolated foot/ear evidence; render the ten changed views."""
from pathlib import Path
import hashlib
parent=Path(WORKSPACE_DIR)/'resume'/'output'/'render'
text=(parent/'render_source.py').read_text()
assert hashlib.sha256(text.encode()).hexdigest()=='2b033d1d49e690ad529731181399d5cdc1eb9cd6f6c5c0df08a145bb719c6611'
reuse='''
def reuse_view(name,names,digest):
    parent=Path(WORKSPACE_DIR)/'resume'/'output'/'render'
    preserved=json.loads((Path(WORKSPACE_DIR)/'output'/'model'/'lineage.json').read_text())['preserved_objects']
    assert names and set(names).issubset(preserved), 'Cannot reuse a view of modified geometry'
    source=parent/(name+'.png');assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
    old=next(r for r in json.loads((parent/'render_manifest.json').read_text()) if r['view']==name)
    assert old['frustum_pass'];shutil.copy2(source,OUT/source.name)
    records.append({**old,'reused_from_job':'form-v004','image_sha256':digest,'unchanged_geometry_confirmed':True})
'''
text=text.replace('records=[]','records=[]\n'+reuse,1)
for name,group,digest in [('feet_detail','feet','1990751c17c277c3704dc579e1717897ee515007928370488cf4e71b93450c18'),('feet_uniform_clay','feet','961a4d09436f722c91174e4364cb649773e3c9a0638dea2148d65f969e04e588'),('ears_detail','ears','bbc183d980a33648bb6e7ded6bbfd1f2693eba48508cf93cb62e4540b9379ca9')]:
    lines=text.splitlines();matches=[i for i,line in enumerate(lines) if line.startswith("image('"+name+"',")];assert len(matches)==1
    lines[matches[0]]="reuse_view(%r,%s,%r)"%(name,group,digest);text='\n'.join(lines)+'\n'
text=text.replace('13 checked orthographic, clay and detailed views rendered from the saved model','Ten affected views rendered; three unchanged isolated views inherited with hashes and fingerprints')
exec(compile(text,'<verified renderer with exact-view reuse>','exec'),globals())
(OUT/'render_source.py').write_text('import hashlib\n'+text)
(OUT/'render_entry_v005.py').write_text(Path(__file__).read_text())
checkpoint('view-evidence-complete','Saved exact executed renderer, ten new views and three hash-verified unchanged views')
