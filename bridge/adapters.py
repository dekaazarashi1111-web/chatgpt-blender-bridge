"""Validated, shell-free commands for the isolated creative runtime.

This module does not sandbox programs. The caller MUST run the returned command
inside the no-network, read-only runtime described in runtime/README.md.
"""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Mapping


class AdapterError(ValueError):
    pass


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp", ".tga", ".exr", ".hdr"}
SEQUENCE = re.compile(r"%(?:0[1-9])?d")


def relative_path(value: str) -> Path:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise AdapterError("Expected a nonempty POSIX relative path")
    pure = PurePosixPath(value)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in value.split("/")):
        raise AdapterError(f"Unsafe relative path: {value}")
    return Path(*pure.parts)


def contained(root: Path, value: str, *, must_exist: bool = False) -> Path:
    root = root.resolve()
    result = (root / relative_path(value)).resolve()
    if not result.is_relative_to(root):
        raise AdapterError(f"Path escapes its directory: {value}")
    if must_exist and not result.is_file():
        raise AdapterError(f"Input file is missing: {value}")
    return result


def input_path(value: str, context: Mapping[str, Any], *, sequence: bool = False) -> Path:
    relative_path(value)
    prefix, separator, rest = value.partition("/")
    if not separator or prefix not in {"input", "workspace"}:
        raise AdapterError("Input paths must begin with input/ or workspace/")
    root = Path(context["input_dir" if prefix == "input" else "workspace_dir"])
    result = contained(root, rest, must_exist=not sequence)
    if sequence:
        matches = list(SEQUENCE.finditer(rest))
        if len(matches) != 1 or "%" in SEQUENCE.sub("", rest):
            raise AdapterError("Image sequences require exactly one %d or %01d..%09d token")
        # Disallow glob syntax so only the declared sequence is selected.
        if any(character in rest for character in "*?[]"):
            raise AdapterError("Glob syntax is not allowed in an image sequence")
        glob = SEQUENCE.sub("*", rest)
        candidates = [item for item in root.glob(glob) if item.is_file()]
        if not candidates or any(not item.resolve().is_relative_to(root.resolve()) for item in candidates):
            raise AdapterError("Image sequence is missing or escapes its input directory")
    return result


def output_path(value: str, context: Mapping[str, Any], suffixes: set[str]) -> Path:
    result = contained(Path(context["output_dir"]), value)
    if result.suffix.lower() not in suffixes:
        raise AdapterError(f"Unsupported output format: {result.suffix}")
    result.parent.mkdir(parents=True, exist_ok=True)
    return result


def integer(params: dict, name: str, low: int, high: int, default: int | None = None) -> int:
    value = params.get(name, default)
    if type(value) is not int or not low <= value <= high:
        raise AdapterError(f"{name} must be an integer from {low} to {high}")
    return value


def parameters(step: dict, allowed: set[str], required: set[str]) -> dict:
    params = step.get("params", {})
    if not isinstance(params, dict) or set(params) - allowed or required - set(params):
        raise AdapterError(f"Invalid parameters for {step.get('tool')}/{step.get('operation')}")
    return params


def build_command(step: dict, context: Mapping[str, Any]) -> list[str]:
    """Build argv inside the container; context paths are container paths.

    Required context: repo_root, input_dir, output_dir, workspace_dir,
    checkpoint_dir. Optional: job_file. Scripts are repository-relative here;
    the queue loader converts job-relative script names before this call.
    """
    tool = step.get("tool")
    if tool in {"blender", "python"}:
        script = contained(Path(context["repo_root"]), step.get("script", ""), must_exist=True)
        if script.suffix != ".py":
            raise AdapterError("Script must have a .py extension")
        entry = Path(context["repo_root"]) / "bridge/tool_entry.py"
        args = ["--tool", tool, "--script", str(script), "--step-json", json.dumps(step, ensure_ascii=False)]
        for key in ("input_dir", "output_dir", "workspace_dir", "checkpoint_dir"):
            args += ["--" + key.replace("_", "-"), str(context[key])]
        if context.get("job_file"):
            args += ["--job", str(context["job_file"])]
        if tool == "python":
            return ["python3", "-u", str(entry), *args]
        return ["xvfb-run", "-a", "blender", "--background", "--factory-startup", "--disable-autoexec",
                "--threads", "2", "--python-exit-code", "1", "--python", str(entry), "--", *args]
    if tool == "imagemagick":
        operation = step.get("operation")
        if operation not in {"resize", "convert"}:
            raise AdapterError("ImageMagick supports resize or convert")
        allowed = {"input", "output", "quality"} | ({"width", "height"} if operation == "resize" else set())
        params = parameters(step, allowed, {"input", "output"} | ({"width", "height"} if operation == "resize" else set()))
        source = input_path(params["input"], context)
        if source.suffix.lower() not in IMAGE_SUFFIXES:
            raise AdapterError("Unsupported input image format")
        target = output_path(params["output"], context, IMAGE_SUFFIXES)
        command = ["convert", str(source)]
        if operation == "resize":
            width = integer(params, "width", 1, 16384)
            height = integer(params, "height", 1, 16384)
            command += ["-resize", f"{width}x{height}"]
        return [*command, "-quality", str(integer(params, "quality", 1, 100, 95)), str(target)]
    if tool == "ffmpeg":
        operation = step.get("operation")
        allowed = {"input", "output", "width"}
        if operation == "encode":
            allowed |= {"fps", "crf"}
        elif operation == "thumbnail":
            allowed |= {"time_seconds"}
        else:
            raise AdapterError("FFmpeg supports encode or thumbnail")
        params = parameters(step, allowed, {"input", "output"})
        is_sequence = operation == "encode" and "%" in params["input"]
        source = input_path(params["input"], context, sequence=is_sequence)
        target = output_path(params["output"], context,
                             {".mp4", ".webm"} if operation == "encode" else {".png", ".jpg", ".jpeg"})
        command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                   "-protocol_whitelist", "file,pipe"]
        if operation == "thumbnail":
            at = params.get("time_seconds", 0)
            if type(at) not in {int, float} or not 0 <= at <= 86400:
                raise AdapterError("time_seconds must be between 0 and 86400")
            command += ["-ss", str(at)]
        elif is_sequence:
            command += ["-framerate", str(integer(params, "fps", 1, 120, 24))]
        command += ["-i", str(source)]
        if "width" in params:
            width = integer(params, "width", 2, 8192)
            if width % 2:
                raise AdapterError("width must be even for video encoding")
            command += ["-vf", f"scale={width}:-2"]
        elif operation == "encode":
            command += ["-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2"]
        if operation == "thumbnail":
            command += ["-frames:v", "1"]
        else:
            command += ["-r", str(integer(params, "fps", 1, 120, 24)), "-an", "-c:v",
                        "libx264" if target.suffix.lower() == ".mp4" else "libvpx-vp9",
                        "-crf", str(integer(params, "crf", 0, 51, 18)), "-pix_fmt", "yuv420p"]
            command += ["-movflags", "+faststart"] if target.suffix.lower() == ".mp4" else ["-b:v", "0"]
        return [*command, str(target)]
    if tool == "krita":
        if step.get("operation") != "export":
            raise AdapterError("Krita supports export")
        params = parameters(step, {"input", "output"}, {"input", "output"})
        source = input_path(params["input"], context)
        if source.suffix.lower() not in IMAGE_SUFFIXES | {".kra", ".ora", ".psd"}:
            raise AdapterError("Unsupported Krita input format")
        target = output_path(params["output"], context, {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"})
        return ["xvfb-run", "-a", "env", "QT_QPA_PLATFORM=xcb", "krita", "--nosplash",
                "--export", "--export-filename", str(target), str(source)]
    raise AdapterError(f"Tool is not available in this runtime: {tool}")
