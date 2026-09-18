from pathlib import Path
import json

base=Path(__file__).resolve().parents[1]/'render-v002'/'package.py'
exec(compile(base.read_text(),str(base),'exec'),globals())
root=Path(WORKSPACE_DIR)/'output'
provenance=json.loads((root/'surfaces'/'surface_provenance.json').read_text())
assert provenance['pass']
p=Path(OUTPUT_DIR)/'verification.json';report=json.loads(p.read_text())
report['surface_provenance']='../surfaces/surface_provenance.json'
report['surface_note']='2K reconstructed tiles derived from the actual reference crop; original patch resolution and added microdetail are explicitly recorded. Not recovered original UV maps.'
p.write_text(json.dumps(report,indent=2)+'\n')
p=Path(OUTPUT_DIR)/'DELIVERY_README.txt'
p.write_text(p.read_text()+'\nNew material maps: output/surfaces/*.png. Source crops, dimensions, periodic reconstruction and hashes: surface_provenance.json.\n')
checkpoint('revised-delivery','Packed edited scene, actual comparison renders and traceable surface maps retained')
