from PIL import Image, ImageDraw
import json

image = Image.new("RGB", (256, 256), (32, 75, 124))
draw = ImageDraw.Draw(image)
for y in range(0, 256, 32):
    for x in range(0, 256, 32):
        if (x // 32 + y // 32) % 2:
            draw.rectangle((x, y, x + 31, y + 31), fill=(120, 190, 230))
image.save(OUTPUT_DIR / "albedo.png")
Image.new("L", image.size, 180).save(OUTPUT_DIR / "roughness.png")
(OUTPUT_DIR / "material.json").write_text(json.dumps({"albedo": "albedo.png", "roughness": "roughness.png"}))
checkpoint("material-created", "Editable texture maps and material metadata are ready")
