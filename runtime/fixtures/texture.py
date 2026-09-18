"""Small reproducible texture used by the runtime smoke test."""
import numpy as np
from PIL import Image

y, x = np.indices((128, 128))
checks = ((x // 16 + y // 16) % 2).astype(np.uint8)
pixels = np.stack((checks * 150 + 40, checks * 60 + 30, checks * 30 + 100), axis=-1)
Image.fromarray(pixels, "RGB").save(OUTPUT_DIR / "checker.png")
checkpoint("texture", "Pillow and numpy generated a checker texture")
