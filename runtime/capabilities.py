"""Probe real executables/modules; optional software is never advertised ready."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def executable(name: str, arguments: list[str]) -> dict:
    path = shutil.which(name)
    if not path:
        return {"available": False, "reason": "not installed"}
    command = [path, *arguments]
    environment = dict(os.environ)
    if name == "krita":
        # Krita 5.2 selects xcb even for --version; Docker builds have no DISPLAY.
        display = shutil.which("xvfb-run")
        if not display:
            return {"available": False, "reason": "xvfb-run is required for headless Krita"}
        command = [display, "-a", *command]
        environment["QT_QPA_PLATFORM"] = "xcb"
    try:
        result = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=30, check=False,
                                env=environment)
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        if result.returncode:
            return {"available": False, "reason": f"version probe exited {result.returncode}", "output": lines[-10:]}
        # Qt may print an XDG warning before its actual version.
        versions = [line for line in lines if any(token in line.lower() for token in (name, "version", "blender"))]
        return {"available": True, "executable": path, "version": (versions or lines or ["unknown"])[0]}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"available": False, "reason": str(error)}


def capabilities() -> dict:
    tools = {"blender": executable("blender", ["--version"]),
             "imagemagick": executable("convert", ["-version"]),
             "ffmpeg": executable("ffmpeg", ["-version"]),
             "krita": executable("krita", ["--version"])}
    modules = {}
    for name in ("PIL", "numpy"):
        try:
            module = importlib.import_module(name)
            modules[name] = {"available": True, "version": module.__version__}
        except ImportError:
            modules[name] = {"available": False}
    tools["python"] = {"available": all(item["available"] for item in modules.values()),
                       "version": sys.version.split()[0], "modules": modules}
    tools["material_maker"] = {"available": False, "reason": "optional; adapter and headless smoke test not implemented"}
    return {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
            "tools": tools, "execution_network": "caller must use docker --network none",
            "base_ready": all(tools[name]["available"] for name in ("blender", "python", "imagemagick", "ffmpeg", "krita"))}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-base", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = capabilities()
    content = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
    print(content, end="")
    return 1 if args.require_base and not result["base_ready"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
