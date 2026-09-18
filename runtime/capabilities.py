"""Probe real executables/modules; optional software is never advertised ready."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys


def run_probe(command: list[str], environment: dict, timeout: float = 30) -> tuple[int, str]:
    """Bound the entire Xvfb/tool process group, including inherited pipes."""
    process = subprocess.Popen(command, text=True, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, env=environment,
                               start_new_session=True)
    try:
        output, _ = process.communicate(timeout=timeout)
        return process.returncode, output
    except subprocess.TimeoutExpired as error:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            output, _ = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            # Even a child that detached its session must not hold this probe
            # indefinitely. Container teardown is the final cleanup boundary.
            output = error.output or ""
            if isinstance(output, bytes):
                output = output.decode("utf-8", errors="replace")
            if process.stdout:
                process.stdout.close()
            process.wait(timeout=5)
        return 124, output


def executable(name: str, arguments: list[str]) -> dict:
    print(f"CAPABILITY_PROBE {name}", file=sys.stderr, flush=True)
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
        returncode, output = run_probe(command, environment)
        lines = [line for line in output.splitlines() if line.strip()]
        if returncode:
            return {"available": False, "reason": f"version probe exited {returncode}", "output": lines[-10:]}
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
    tools["material_maker"] = executable("material-maker", ["--version"])
    release_file = Path("/opt/material-maker/release.json")
    if tools["material_maker"]["available"] and release_file.is_file():
        release = json.loads(release_file.read_text())
        tools["material_maker"].update(engine_version=tools["material_maker"]["version"],
                                       version=release["version"], archive_sha256=release["sha256"])
    return {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
            "tools": tools, "execution_network": "Docker default networking",
            "base_ready": all(tools[name]["available"] for name in ("blender", "python", "imagemagick", "ffmpeg", "krita", "material_maker"))}


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
