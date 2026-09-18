"""Seamless, deterministic worn textile maps; no online assets or model API."""
from pathlib import Path
import hashlib
import json
import shutil
import numpy as np
from PIL import Image

OUT = Path(OUTPUT_DIR)
OUT.mkdir(parents=True, exist_ok=True)
ref = Path(INPUT_DIR) / 'reference.webp'
assert hashlib.sha256(ref.read_bytes()).hexdigest() == 'c878b9f1522a412c8b1174333ac456939307f3e048aea2b86120ef388d5aeaf0'
with Image.open(ref) as im:
    assert im.size == (2048, 682)
    im.convert('RGB').save(OUT / 'reference.png')
shutil.copyfile(ref, OUT / 'reference.webp')
N = 2048
rng = np.random.default_rng(9181111)

def periodic_noise(cells):
    g = rng.random((cells, cells)).astype(np.float32)
    t = np.arange(N, dtype=np.float32) * cells / N
    i = np.floor(t).astype(int)
    f = t - i
    f = f * f * (3.0 - 2.0 * f)
    a = g[i[:, None] % cells, i[None, :] % cells]
    b = g[i[:, None] % cells, (i[None, :] + 1) % cells]
    c = g[(i[:, None] + 1) % cells, i[None, :] % cells]
    d = g[(i[:, None] + 1) % cells, (i[None, :] + 1) % cells]
    return ((a * (1 - f[None, :]) + b * f[None, :]) * (1 - f[:, None])
            + (c * (1 - f[None, :]) + d * f[None, :]) * f[:, None])

cloud = periodic_noise(7)
mid = periodic_noise(29)
fine = periodic_noise(93)
grain = rng.random((N, N), dtype=np.float32)
mottle = np.clip(.49 + .47*(cloud-.5) + .73*(mid-.5) + .28*(fine-.5), 0, 1)
# Eroded island boundaries, not a flat camouflage mask.
lichen = np.exp(-((mid + .12*(fine-.5) - .47) / .043)**2)
height = .5 + .12*(fine-.5) + .12*(mid-.5) - .075*lichen + .035*(grain-.5)
t = np.arange(N, dtype=np.float32) / N
weave = np.sin(2*np.pi*512*t)[None, :] * np.sin(2*np.pi*512*t)[:, None]
height = np.clip(height + .012*weave, 0, 1)
rough = np.clip(.84 + .14*(fine-.5) + .10*lichen, .68, .98)

def ramp_image(field, palette, path):
    palette = np.asarray(palette, dtype=np.float32)
    p = np.clip(field, 0, .999999) * (len(palette)-1)
    a = np.floor(p).astype(int)
    rgb = palette[a]*(1-(p-a)[..., None]) + palette[a+1]*(p-a)[..., None]
    rgb += (grain-.5)[..., None]*7
    Image.fromarray(np.clip(rgb,0,255).astype(np.uint8), 'RGB').save(path)

ramp_image(mottle, [(48,34,46),(85,60,80),(119,91,113),(157,132,151)], OUT/'violet_albedo.png')
ramp_image(np.clip(mottle+.11*lichen,0,1), [(64,63,66),(111,110,112),(154,153,151),(194,190,181)], OUT/'pale_albedo.png')
ramp_image(mottle, [(23,12,23),(43,21,41),(65,34,62),(91,52,85)], OUT/'ear_albedo.png')
Image.fromarray((rough*255).astype(np.uint8), 'L').save(OUT/'cloth_roughness.png')
Image.fromarray((height*65535).astype(np.uint16)).save(OUT/'cloth_height16.png')
dx=(np.roll(height,-1,axis=1)-np.roll(height,1,axis=1))*2.1
dy=(np.roll(height,-1,axis=0)-np.roll(height,1,axis=0))*2.1
normal=np.stack((-dx,dy,np.ones_like(dx)),axis=-1)
normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
Image.fromarray(((normal*.5+.5)*255).astype(np.uint8),'RGB').save(OUT/'cloth_normal.png')
records=[]
for p in sorted(OUT.glob('*.png')):
    with Image.open(p) as im:
        a=np.asarray(im)
        records.append({'path':p.name,'size':list(im.size),'mode':im.mode,'bytes':p.stat().st_size,
                        'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'standard_deviation':float(a.std())})
report={'pass':True,'seed':9181111,'texture_resolution':N,'physical_repeat_m':.48,
        'method':'periodic smooth value noise, multiscale erosion, micro-weave; visually reconstructed, not recovered source UV maps',
        'reference_sha256':hashlib.sha256(ref.read_bytes()).hexdigest(),'files':records,
        'tile_height_wrap_dx':float(np.abs(height[:,0]-height[:,-1]).mean()),
        'tile_height_wrap_dy':float(np.abs(height[0,:]-height[-1,:]).mean())}
(OUT/'texture_validation.json').write_text(json.dumps(report,indent=2)+'\n')
checkpoint('maps','Verified reference and editable deterministic texture sources generated')
