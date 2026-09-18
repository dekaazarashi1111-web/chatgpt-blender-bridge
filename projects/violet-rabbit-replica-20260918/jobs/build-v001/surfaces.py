"""Deterministic exemplar quilting; input pixels, not a generated reference."""
import hashlib
import json
import math
import shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

OUT = Path(OUTPUT_DIR)
OUT.mkdir(parents=True, exist_ok=True)
reference = Path(INPUT_DIR) / 'reference.webp'
assert hashlib.sha256(reference.read_bytes()).hexdigest() == 'c878b9f1522a412c8b1174333ac456939307f3e048aea2b86120ef388d5aeaf0'
ref = Image.open(reference).convert('RGB')
shutil.copy2(reference, OUT / 'reference.webp')
rng = np.random.default_rng(9181639)
N = 2048

def minimum_cut(cost):
    h, w = cost.shape
    acc = cost.astype(np.float64).copy()
    parents = np.zeros((h, w), dtype=np.int16)
    for y in range(1, h):
        for x in range(w):
            lo, hi = max(0, x - 1), min(w, x + 2)
            p = lo + int(np.argmin(acc[y - 1, lo:hi]))
            parents[y, x] = p
            acc[y, x] += acc[y - 1, p]
    path = np.empty(h, dtype=np.int16)
    path[-1] = np.argmin(acc[-1])
    for y in range(h - 1, 0, -1):
        path[y - 1] = parents[y, path[y]]
    return np.arange(w)[None, :] >= path[:, None]

def quilt(exemplar, size=320, patch=36, overlap=12):
    # Minimum-error overlap seams rather than a regular cloud/noise grid.
    a = np.asarray(exemplar, np.float32) / 255
    h, w = a.shape[:2]
    canvas = np.zeros((size + patch, size + patch, 3), np.float32)
    for y in range(0, size, patch - overlap):
        for x in range(0, size, patch - overlap):
            best, score = None, float('inf')
            region = canvas[y:y + patch, x:x + patch]
            for _ in range(32):
                yy = int(rng.integers(0, h - patch + 1))
                xx = int(rng.integers(0, w - patch + 1))
                p = np.rot90(a[yy:yy + patch, xx:xx + patch], int(rng.integers(0, 4)))
                if rng.random() < .5:
                    p = p[:, ::-1]
                err = 0.0
                if x:
                    err += float(np.mean((p[:, :overlap] - region[:, :overlap]) ** 2))
                if y:
                    err += float(np.mean((p[:overlap] - region[:overlap]) ** 2))
                if err < score:
                    best, score = p.copy(), err
            mask = np.ones((patch, patch), bool)
            if x:
                cost = np.sum((best[:, :overlap] - region[:, :overlap]) ** 2, axis=2)
                mask[:, :overlap] &= minimum_cut(cost)
            if y:
                cost = np.sum((best[:overlap] - region[:overlap]) ** 2, axis=2).T
                mask[:overlap] &= minimum_cut(cost).T
            region[mask] = best[mask]
    return canvas[:size, :size]

def periodic(a):
    h, w = a.shape[:2]
    v = np.zeros_like(a)
    v[0] = a[-1] - a[0]
    v[-1] = -v[0]
    delta = a[:, -1] - a[:, 0]
    v[:, 0] += delta
    v[:, -1] -= delta
    ky = np.arange(h)[:, None]
    kx = np.arange(w)[None, :]
    den = 2 * np.cos(2 * np.pi * kx / w) + 2 * np.cos(2 * np.pi * ky / h) - 4
    den[0, 0] = 1
    s = np.fft.fft2(v, axes=(0, 1)) / den[:, :, None]
    s[0, 0] = 0
    return np.clip(a - np.fft.ifft2(s, axes=(0, 1)).real, 0, 1)

def srgb_to_lin(x):
    return np.where(x <= .04045, x / 12.92, ((x + .055) / 1.055) ** 2.4)

def lin_to_srgb(x):
    x = np.maximum(x, 0)
    return np.where(x <= .0031308, 12.92 * x, 1.055 * x ** (1 / 2.4) - .055)

def save_rgb(path, a):
    Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255 + .5), 'RGB').save(path)

def save_gray(path, a):
    Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255 + .5), 'L').save(path)

specs = {
    'purple': ((1603, 310, 1698, 401), 1.42),
    'pale': ((365, 352, 439, 426), 1.46),
    'inner': ((370, 69, 383, 125), 1.35),
}
report = {'source_sha256': hashlib.sha256(reference.read_bytes()).hexdigest(),
          'seed': 9181639, 'map_size': [N, N], 'tile_width_m': 1.25,
          'method': 'minimum-cut image quilting + periodic boundary correction + fine synthetic nap',
          'warning': '2K is export size, not recovered detail. Original screenshot illumination is only approximately compensated.',
          'materials': {}}
for key, (box, gain) in specs.items():
    crop = ref.crop(box)
    crop.save(OUT / (key + '_exemplar.png'))
    if min(crop.size) < 40:
        crop = crop.resize((max(48, crop.width), max(48, crop.height)), Image.Resampling.LANCZOS)
    texture = periodic(quilt(ref.crop(specs['purple'][0]) if key == 'inner' else crop))
    if key == 'inner':
        target = np.asarray(ref.crop(box), np.float32).mean((0, 1)) / 255
        texture = np.clip(texture / texture.mean((0, 1)) * target, 0, 1)
    smooth = Image.fromarray(np.uint8(texture * 255)).resize((N, N), Image.Resampling.LANCZOS)
    a = np.asarray(smooth, np.float32) / 255
    # The fine fibers are newly synthesized; the coarse pigment pattern is exemplar-derived.
    yy, xx = np.mgrid[:N, :N].astype(np.float32)
    grain = rng.normal(0, 1, (N, N)).astype(np.float32)
    nap = .50 * grain + .15 * np.sin(xx * 2.3 + np.sin(yy * .13))
    linear = srgb_to_lin(a) * gain
    linear *= 1 + .012 * nap[:, :, None]
    albedo = np.clip(lin_to_srgb(linear), 0, 1)
    luma = np.mean(a, axis=2)
    height = np.clip(.5 + .015 * (luma - luma.mean()) + .055 * nap, 0, 1)
    rough = np.clip(.85 + .055 * (luma - luma.mean()) + .015 * nap, .74, .94)
    save_rgb(OUT / (key + '_albedo.png'), albedo)
    save_gray(OUT / (key + '_height.png'), height)
    save_gray(OUT / (key + '_roughness.png'), rough)
    edge = float(np.mean(np.abs(texture[:, 0] - texture[:, -1])))
    step = float(np.mean(np.abs(texture[:, 1:] - texture[:, :-1])))
    report['materials'][key] = {'source_crop_xyxy': list(box), 'source_pixels': list(ref.crop(box).size),
        'pattern_source': 'purple pigment, recoloured from inner-ear sample' if key == 'inner' else 'same material exemplar',
        'linear_exposure_multiplier': gain, 'albedo_rgb_mean': (albedo.mean((0, 1)) * 255).tolist(),
        'edge_jump': edge, 'ordinary_pixel_jump': step, 'nonflat': float(albedo.std()) > .015}

# Low-strength calibrated projection preserves distinctive reference mottles.
# These maps contain screenshot shading; shader strength is editable and deliberately limited.
for key, box in {'front': (64, 0, 736, 682), 'back': (1312, 0, 1984, 682), 'side': (896, 0, 1196, 682)}.items():
    a = np.asarray(ref.crop(box), np.float32) / 255
    save_rgb(OUT / ('projection_' + key + '.png'), lin_to_srgb(srgb_to_lin(a) * 1.44))
    report['projection_' + key] = {'crop': list(box), 'linear_gain': 1.44, 'status': 'appearance guide, not recovered original UV albedo'}
assert all(v['nonflat'] for v in report['materials'].values())
(OUT / 'surface_report.json').write_text(json.dumps(report, indent=2))
checkpoint('surfaces', 'Reference-derived editable maps saved with original effective resolutions')
