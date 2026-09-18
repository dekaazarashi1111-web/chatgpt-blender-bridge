"""Install an official release at build time, verifying its pinned archive."""
import hashlib
import json
from pathlib import Path
import shutil
import tarfile
import tempfile
import urllib.request

root = Path(__file__).parent
release = json.loads((root / "material-maker.lock.json").read_text())
destination = Path("/opt/material-maker")
with tempfile.TemporaryDirectory() as temporary:
    archive = Path(temporary) / "release.tar.gz"
    digest = hashlib.sha256()
    with urllib.request.urlopen(release["url"], timeout=120) as response, archive.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            digest.update(chunk)
            output.write(chunk)
    if digest.hexdigest() != release["sha256"]:
        raise RuntimeError("Material Maker release SHA-256 mismatch")
    with tarfile.open(archive) as package:
        package.extractall(Path(temporary) / "unpacked", filter="data")
    shutil.move(str(Path(temporary) / "unpacked" / release["archive_root"]), destination)
(destination / release["executable"]).chmod(0o755)
shim = root / "material-maker-renderer.gd"
release["compatibility_shim_sha256"] = hashlib.sha256(shim.read_bytes()).hexdigest()
(destination / "override.cfg").write_text('[autoload]\nmm_renderer="*' + str(shim) + '"\n')
(destination / "release.json").write_text(json.dumps(release, indent=2) + "\n")
shutil.copyfile(root / "material-maker-LICENSE.md", destination / "LICENSE.md")
Path("/usr/local/bin/material-maker").symlink_to(destination / release["executable"])
# Ubuntu's Mesa updates may change whether the ICD filename has an arch suffix.
icds = list(Path("/usr/share/vulkan/icd.d").glob("*lvp*.json"))
if len(icds) != 1:
    raise RuntimeError("Expected exactly one installed Mesa lavapipe ICD")
shutil.copyfile(icds[0], root / "lavapipe.json")
print("Vulkan CPU driver:", icds[0])
print("Installed verified Material Maker", release["version"])
