"""Export one portable .ptex material through the installed official CLI.

This entry point runs ONLY inside the same isolated container as other tools.
Graphs may contain shaders; JSON validation is not a sandbox.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

MAP_SUFFIXES = {"albedo": "_albedo.png", "roughness": "_rough.exr",
                "metallic": "_metal.exr", "normal": "_normal.png",
                "height": "_displace.exr", "ao": "_occlusion.exr",
                "emission": "_emission.png", "sss": "_sss.exr"}


def validate_graph(graph: dict) -> None:
    if not isinstance(graph, dict) or graph.get("type") != "graph" or not isinstance(graph.get("nodes"), list):
        raise ValueError("Expected a Material Maker graph with nodes")
    materials = []
    def visit(node):
        if not isinstance(node, dict):
            raise ValueError("Material nodes must be JSON objects")
        if node.get("type") in {"material", "material_tesselated"}:
            materials.append(node)
        for child in node.get("nodes", []):
            visit(child)
    visit(graph)
    if len(materials) != 1:
        raise ValueError("Export exactly one Static PBR Material per .ptex graph")


def copy_source_bundle(source: Path, destination: Path) -> Path:
    """Keep relative image references and editable source together in snapshots."""
    parent = source.parent.resolve()
    if destination.resolve().is_relative_to(parent):
        raise ValueError("Put the .ptex and its images in a dedicated folder outside this step's output")
    files, total = [], 0
    for path in sorted(parent.rglob("*")):
        if path.is_symlink():
            raise ValueError("Material source bundles must not contain symlinks")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError("Material source bundle contains a special file")
        files.append(path)
        total += path.stat().st_size
        if len(files) > 4096 or total > 256 * 1024 * 1024:
            raise ValueError("Material source bundle exceeds 4096 files or 256 MiB")
    destination.mkdir(parents=True, exist_ok=False)
    for path in files:
        target = destination / path.relative_to(parent)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    return destination / source.name


def inspect_outputs(directory: Path, prefix: str, required: list[str]) -> dict:
    maps = {}
    for name, suffix in MAP_SUFFIXES.items():
        path = directory / (prefix + suffix)
        if not path.exists():
            continue
        if path.is_symlink() or not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError("Invalid Material Maker output: " + path.name)
        # ImageMagick decodes PNG and EXR; existence alone is insufficient.
        try:
            result = subprocess.run(["identify", "-format", "%w %h", str(path)],
                                    capture_output=True, text=True, check=True, timeout=90)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"Could not decode {path.name}: {exc.stderr}") from exc
        width, height = map(int, result.stdout.split())
        if (width, height) != (2048, 2048):
            raise RuntimeError(f"Unexpected Material Maker image dimensions: {path.name} {width}x{height}")
        maps[name] = {"path": path.name, "width": width, "height": height,
                      "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    if not maps or set(required) - maps.keys():
        raise RuntimeError("Material Maker did not generate required maps: " + ", ".join(sorted(set(required) - maps.keys())))
    return maps


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--maps", required=True)
    args = parser.parse_args()
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    report = {"tool": "material_maker", "state": "failed", "target": "Blender"}
    try:
        required = json.loads(args.maps)
        graph = json.loads(args.input.read_text())
        validate_graph(graph)
        staged = copy_source_bundle(args.input, output / "source")
        for variable in ("HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_CONFIG_HOME", "XDG_RUNTIME_DIR"):
            if os.environ.get(variable):
                Path(os.environ[variable]).mkdir(parents=True, exist_ok=True, mode=0o700)
        # Xvfb provides a display; Mesa lavapipe supplies Vulkan compute on CPU.
        # Keep --export-material first: upstream parses application arguments
        # starting at index 1. Godot's own switches are consumed by the engine.
        command = ["xvfb-run", "-a", "-e", "/dev/stderr", "material-maker",
                   "--audio-driver", "Dummy", "--accessibility", "disabled", "--export-material",
                   "--target", "Blender", "-o", str(output), "--output-file", args.prefix, str(staged)]
        print("MATERIAL_MAKER_EXPORT " + str(staged), flush=True)
        subprocess.run(command, check=True, env={**os.environ, "VK_LOADER_DEBUG": "error,warn"})
        report["maps"] = inspect_outputs(output, args.prefix, required)
        report["source"] = staged.relative_to(output).as_posix()
        report["source_sha256"] = hashlib.sha256(staged.read_bytes()).hexdigest()
        report["release"] = json.loads(Path("/opt/material-maker/release.json").read_text())
        if "albedo" in report["maps"]:
            from PIL import Image
            preview = output / "previews" / "albedo.png"
            preview.parent.mkdir(exist_ok=True)
            with Image.open(output / report["maps"]["albedo"]["path"]) as image:
                image.thumbnail((512, 512))
                image.save(preview)
        report["state"] = "succeeded"
    except Exception as exc:
        report["error"] = str(exc)
        print(f"MATERIAL_MAKER_FAILED: {exc}", file=sys.stderr, flush=True)
    finally:
        (output / "material_report.json").write_text(json.dumps(report, indent=2) + "\n")
    return 0 if report["state"] == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
