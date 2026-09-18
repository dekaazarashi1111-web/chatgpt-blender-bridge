"""Stage an actual reference file and print a checksum-pinned job input entry."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bridge.creative_jobs import safe_relative_path


def import_reference(project, source, target, *, encoded=False, repo_root=ROOT):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", project):
        raise ValueError("Invalid project ID")
    safe_relative_path(target)
    source = Path(source)
    if source.stat().st_size > 28_000_000:
        raise ValueError("Reference upload exceeds this helper's 20 MiB binary limit")
    data = source.read_bytes()
    if encoded:
        data = base64.b64decode(b"".join(data.split()), validate=True)
    if not data or len(data) > 20 * 1024**2:
        raise ValueError("Reference must contain 1 byte to 20 MiB")
    path = Path(repo_root) / "projects" / project / "inputs" / target
    for parent in (path, *path.parents):
        if parent.is_symlink():
            raise ValueError("Input destination cannot contain symlinks")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
    return {"path": path.relative_to(repo_root).as_posix(), "target": target,
            "sha256": hashlib.sha256(data).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--base64", action="store_true")
    args = parser.parse_args()
    print(json.dumps(import_reference(args.project, args.source, args.target, encoded=args.base64), indent=2))


if __name__ == "__main__":
    main()
