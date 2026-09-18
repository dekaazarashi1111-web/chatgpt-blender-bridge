from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import bpy


def arguments() -> argparse.Namespace:
    values = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    return parser.parse_args(values)


def main() -> int:
    args = arguments()
    missing: list[str] = []
    for image in bpy.data.images:
        if image.source in {"GENERATED", "VIEWER"} or image.packed_file:
            continue
        if image.filepath:
            resolved = Path(bpy.path.abspath(image.filepath))
            if not resolved.is_file():
                missing.append(str(resolved))
    payload = {
        "schema_version": 1,
        "validated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "blend_file": bpy.data.filepath,
        "object_count": len(bpy.data.objects),
        "mesh_count": len(bpy.data.meshes),
        "material_count": len(bpy.data.materials),
        "missing_external_files": sorted(set(missing)),
        "pass": bool(bpy.data.filepath) and len(bpy.data.objects) > 0 and not missing,
    }
    target = Path(args.report).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"BLEND_REOPEN={'PASS' if payload['pass'] else 'FAIL'} objects={payload['object_count']} report={target}")
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
