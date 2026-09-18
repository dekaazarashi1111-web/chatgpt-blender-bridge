"""Reference-derived tiles, not the original asset's recovered UV textures."""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageFilter

OUT=Path(OUTPUT_DIR);OUT.mkdir(parents=True,exist_ok=True)
ref=Path(INPUT_DIR)/'reference.webp'
assert hashlib.sha256(ref.read_bytes()).hexdigest()=='c878b9f1522a412c8b1174333ac456939307f3e048aea2b86120ef388d5aeaf0'
image=Image.open(ref).convert('RGB')
N=2048;rng=np.random.default_rng(9183003)

def periodic_component(a):
    h,w,c=a.shape
    v=np.zeros_like(a,dtype=np.float64)
    v[0,:,:]=a[-1,:,:]-a[0,:,:];v[-1,:,:]=-v[0,:,:]
    v[:,0,:]+=a[:,-1,:]-a[:,0,:];v[:,-1,:]-=a[:,-1,:]-a[:,0,:]
    yy,xx=np.mgrid[0:h,0:w]
    denom=2*np.cos(2*np.pi*xx/w)+2*np.cos(2*np.pi*yy/h)-4
    denom[0,0]=1
    spectrum=np.fft.fft2(v,axes=(0,1))/denom[:,:,None];spectrum[0,0,:]=0
    smooth=np.fft.ifft2(spectrum,axes=(0,1)).real
    return a-smooth

specs=[('violet',(1601,296,1693,392),(101,77,92),15.0,.36),
       ('pale',(366,361,440,425),(131,124,128),24.0,.27),
       ('ear',(1601,296,1693,392),(44,22,41),7.0,.36)]
records=[]
for name,box,target,std,period in specs:
    crop=image.crop(box)
    crop.save(OUT/(name+'_reference_crop.png'))
    a=np.asarray(crop,dtype=np.float64)
    broad=np.asarray(crop.filter(ImageFilter.GaussianBlur(22)),dtype=np.float64)
    residual=periodic_component(a-.75*broad)
    residual-=residual.mean((0,1),keepdims=True)
    residual*=std/max(float(np.mean(residual.std((0,1)))),1e-6)
    channels=[]
    for c in range(3):
        tiled=np.tile(residual[:,:,c],(3,3)).astype(np.float32)
        big=Image.fromarray(tiled,'F').resize((3*N,3*N),Image.Resampling.BICUBIC)
        channels.append(np.asarray(big.crop((N,N,2*N,2*N))).copy())
    field=np.stack(channels,axis=-1)
    grain=rng.normal(0,1,(N,N)).astype(np.float32)
    rgb=np.asarray(target)[None,None,:]+field+.60*grain[...,None]
    Image.fromarray(np.clip(rgb,0,255).astype(np.uint8),'RGB').save(OUT/(name+'_reference_albedo.png'))
    pattern=np.clip(field.mean(-1)/std,-2.5,2.5)
    t=np.arange(N,dtype=np.float32)/N
    weave=np.sin(2*np.pi*768*t)[None,:]*np.sin(2*np.pi*768*t)[:,None]
    height=np.clip(.5+.011*pattern+.009*grain+.006*weave,0,1)
    rough=np.clip(.85+.016*pattern+.024*grain,.73,.96)
    Image.fromarray((height*65535).astype(np.uint16)).save(OUT/(name+'_reference_height16.png'))
    Image.fromarray((rough*255).astype(np.uint8),'L').save(OUT/(name+'_reference_roughness.png'))
    dx=(np.roll(height,-1,1)-np.roll(height,1,1))*.8
    dy=(np.roll(height,-1,0)-np.roll(height,1,0))*.8
    normal=np.stack((-dx,dy,np.ones_like(dx)),axis=-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
    Image.fromarray(((normal*.5+.5)*255).astype(np.uint8),'RGB').save(OUT/(name+'_reference_normal.png'))
    records.append({'material':name,'reference_box_xyxy':list(box),'source_patch_size':list(crop.size),
                    'tile_resolution':[N,N],'physical_repeat_m':period,'albedo_mean_target_srgb':list(target),
                    'measured_output_mean':rgb.mean((0,1)).tolist(),'measured_output_std':rgb.std((0,1)).tolist(),
                    'note':'Original reference pixels, broad shading suppressed and periodic boundary correction applied. Fine grain/weave are added procedural detail, not recovered source detail.'})
files=[]
for p in sorted(OUT.glob('*.png')):
    assert p.stat().st_size>0
    files.append({'path':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(OUT/'surface_provenance.json').write_text(json.dumps({'pass':True,'reference_sha256':hashlib.sha256(ref.read_bytes()).hexdigest(),
    'method':'reference-derived pixel tiles with low-frequency shading suppression and periodic-plus-smooth boundary decomposition; independent subtle microrelief',
    'seed':9183003,'maps':records,'files':files},indent=2)+'\n')
checkpoint('reference-derived-surfaces','Saved actual reference crops, traceable 2K albedo/roughness/height/normal tiles and their hashes')
