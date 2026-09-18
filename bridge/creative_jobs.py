"""Validate job structure, file references, script syntax, and input hashes."""
from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re

from bridge.jobs import JobError, ROOT, VIEWS


IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
RELEASE_TAG = re.compile(r"creative-[A-Za-z0-9][A-Za-z0-9._-]{0,220}\Z")
FRAME_PATTERN = re.compile(r"%0?[1-9]?d")
TOOLS = {"blender", "python", "imagemagick", "ffmpeg", "krita", "material_maker"}
DEFAULT_CRITERIA = ["Inspect generated previews against the project references before completion."]


@dataclass(frozen=True)
class CreativeJobFiles:
    directory: Path
    descriptor: Path
    project_directory: Path
    scripts: dict[str, Path]
    inputs: tuple[Path, ...]


def _object(value: object, label: str, required: set[str], optional: set[str] = frozenset()) -> dict:
    if not isinstance(value, dict):
        raise JobError(f"{label} must be an object")
    missing, extra = required - value.keys(), value.keys() - required - optional
    if missing or extra:
        raise JobError(f"{label} keys mismatch: missing={sorted(missing)} extra={sorted(extra)}")
    return value


def _string(value: object, label: str, low: int = 1, high: int = 200) -> str:
    if not isinstance(value, str) or not low <= len(value) <= high or not value.strip():
        raise JobError(f"{label} must be a nonempty string of {low}..{high} characters")
    return value


def _integer(value: object, label: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise JobError(f"{label} must be an integer in {low}..{high}")
    return value


def _identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise JobError(f"{label} is not a valid identifier")
    return value


def safe_relative_path(value: object, label: str = "path") -> str:
    """Return a portable relative path without traversal or ambiguous separators."""
    if not isinstance(value, str) or not 1 <= len(value) <= 1024:
        raise JobError(f"{label} must be a relative path of 1..1024 characters")
    if any(c in value for c in "\\:") or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise JobError(f"{label} contains a non-portable character")
    if any(part in {"", ".", ".."} for part in value.split("/")):
        raise JobError(f"{label} must not be absolute or contain empty/dot/traversal components")
    return value


def _repo_file(root: Path, value: str, label: str) -> Path:
    safe_relative_path(value, label)
    current = root
    for part in value.split("/"):
        current = current / part
        if current.is_symlink():
            raise JobError(f"{label} must not use symlinks: {value}")
    if not current.is_file():
        raise JobError(f"{label} file does not exist: {value}")
    if not current.resolve().is_relative_to(root.resolve()):
        raise JobError(f"{label} escapes repository")
    return current


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise JobError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _json_params(value: object) -> dict:
    if not isinstance(value, dict):
        raise JobError("step.params must be an object")
    def visit(item: object, depth: int) -> None:
        if depth > 8:
            raise JobError("step.params nesting exceeds 8 levels")
        if isinstance(item, dict):
            if any(not isinstance(key, str) for key in item):
                raise JobError("step.params keys must be strings")
            for child in item.values():
                visit(child, depth + 1)
        elif isinstance(item, list):
            for child in item:
                visit(child, depth + 1)
        elif isinstance(item, float) and not math.isfinite(item):
            raise JobError("step.params numbers must be finite")
        elif item is not None and type(item) not in {str, int, float, bool}:
            raise JobError("step.params must contain JSON values")
    visit(value, 0)
    if len(json.dumps(value, ensure_ascii=False).encode("utf-8")) > 32768:
        raise JobError("step.params exceeds 32768 bytes")
    return value


def _logical_input(value: object, targets: set[str], *, sequence: bool = False) -> str:
    value = safe_relative_path(value, "tool input")
    area, separator, relative = value.partition("/")
    if not separator or area not in {"input", "workspace"}:
        raise JobError("tool input must start with input/ or workspace/")
    if "%" in relative:
        matches = list(FRAME_PATTERN.finditer(relative))
        if not sequence or len(matches) != 1 or "%" in FRAME_PATTERN.sub("", relative):
            raise JobError("Only ffmpeg encode supports one %d or %01d..%09d frame placeholder")
        token = matches[0].group()
        if token != "%d" and not re.fullmatch(r"%0[1-9]d", token):
            raise JobError("Frame placeholder must be %d or %01d..%09d")
        if area == "input":
            width = int(token[2:-1]) if token != "%d" else None
            digits = r"[0-9]+" if width is None else r"[0-9]{" + str(width) + r",}"
            pattern = re.escape(relative).replace(re.escape(token), digits)
            if not any(re.fullmatch(pattern, target) for target in targets):
                raise JobError("Frame sequence does not match any declared input")
    elif area == "input" and relative not in targets:
        raise JobError(f"Tool input is not declared in inputs: {value}")
    return value


def _preview(value: object) -> None:
    value = _object(value, "preview", {"views", "width", "height", "samples"})
    views = value["views"]
    if not isinstance(views, list) or not 1 <= len(views) <= len(VIEWS):
        raise JobError("preview.views must contain 1..5 views")
    if any(not isinstance(view, str) or view not in VIEWS for view in views) or len(set(views)) != len(views):
        raise JobError("preview.views must be supported and unique")
    for name, low, high in (("width", 128, 2048), ("height", 128, 2048), ("samples", 1, 256)):
        _integer(value[name], f"preview.{name}", low, high)


def _resume(value: object, project_id: str) -> None:
    required = {"release_tag", "project_id", "job_id", "archive_sha256", "manifest_sha256"}
    optional = {"release_id", "archive_asset_id", "manifest_asset_id", "release_url", "archive_url", "manifest_url", "source_commit", "current_step"}
    value = _object(value, "resume", required, optional)
    if not isinstance(value["release_tag"], str) or not RELEASE_TAG.fullmatch(value["release_tag"]):
        raise JobError("resume.release_tag must be an exact creative-* snapshot tag")
    if _identifier(value["project_id"], "resume.project_id") != project_id:
        raise JobError("resume.project_id must match project_id")
    _identifier(value["job_id"], "resume.job_id")
    for name in ("archive_sha256", "manifest_sha256"):
        if not isinstance(value[name], str) or not SHA256.fullmatch(value[name]):
            raise JobError(f"resume.{name} must be a lowercase SHA-256 digest")
    for name in ("release_id", "archive_asset_id", "manifest_asset_id"):
        if name in value:
            _integer(value[name], f"resume.{name}", 1, 2**63 - 1)
    for name in ("release_url", "archive_url", "manifest_url"):
        if name in value:
            url = _string(value[name], f"resume.{name}", high=2048)
            if not url.startswith("https://") or any(ord(c) < 32 for c in url):
                raise JobError(f"resume.{name} must be an HTTPS URL; it is informational only")
    if "source_commit" in value and (not isinstance(value["source_commit"], str) or not re.fullmatch(r"[0-9a-f]{40}", value["source_commit"])):
        raise JobError("resume.source_commit must be a 40-character commit SHA")
    if "current_step" in value:
        _identifier(value["current_step"], "resume.current_step")


def _operation(step: dict, targets: set[str]) -> None:
    tool, operation = step["tool"], step.get("operation")
    options = {
        ("imagemagick", "convert"): ({"input", "output"}, {"quality"}),
        ("imagemagick", "resize"): ({"input", "output", "width", "height"}, {"quality"}),
        ("ffmpeg", "encode"): ({"input", "output"}, {"fps", "crf", "width"}),
        ("ffmpeg", "thumbnail"): ({"input", "output"}, {"time_seconds", "width"}),
        ("krita", "export"): ({"input", "output"}, set()),
        ("material_maker", "export"): ({"input", "output"}, {"maps"}),
    }
    if not isinstance(operation, str) or (tool, operation) not in options:
        raise JobError(f"Unsupported operation for {tool}: {operation}")
    required, optional = options[(tool, operation)]
    params = _object(step.get("params", {}), "operation.params", required, optional)
    source = _logical_input(params["input"], targets, sequence=(tool, operation) == ("ffmpeg", "encode"))
    output = safe_relative_path(params["output"], "operation output")
    if tool == "material_maker":
        if Path(source).suffix.lower() != ".ptex":
            raise JobError("Material Maker input must be a .ptex graph")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", output):
            raise JobError("Material Maker output must be a filename prefix (letters, digits, _ or -)")
        maps = params.get("maps", ["albedo"])
        allowed = {"albedo", "roughness", "metallic", "normal", "height", "ao", "emission", "sss"}
        if not isinstance(maps, list) or not 1 <= len(maps) <= 8 or any(not isinstance(m, str) or m not in allowed for m in maps) or len(set(maps)) != len(maps):
            raise JobError("Material Maker maps must be a nonempty unique list of supported map names")
        return
    suffixes = {
        "imagemagick": {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp", ".tga", ".exr", ".hdr"},
        "krita": {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"},
        "ffmpeg": {".mp4", ".webm"} if operation == "encode" else {".png", ".jpg", ".jpeg"},
    }
    if Path(output).suffix.lower() not in suffixes[tool]:
        raise JobError(f"Unsupported output extension for {tool} {operation}")
    image_inputs = suffixes["imagemagick"]
    if tool == "imagemagick" and Path(source).suffix.lower() not in image_inputs:
        raise JobError("Unsupported ImageMagick input format")
    if tool == "krita" and Path(source).suffix.lower() not in image_inputs | {".kra", ".ora", ".psd"}:
        raise JobError("Unsupported Krita input format")
    for name, low, high in (("fps", 1, 120), ("crf", 0, 51), ("quality", 1, 100), ("height", 1, 16384)):
        if name in params:
            _integer(params[name], f"params.{name}", low, high)
    if "width" in params:
        _integer(params["width"], "params.width", 2 if tool == "ffmpeg" else 1, 8192 if tool == "ffmpeg" else 16384)
        if tool == "ffmpeg" and params["width"] % 2:
            raise JobError("ffmpeg width must be even")
    if "time_seconds" in params:
        seconds = params["time_seconds"]
        if type(seconds) not in {int, float} or not math.isfinite(seconds) or not 0 <= seconds <= 86400:
            raise JobError("params.time_seconds must be a finite number in 0..86400")


def load_creative_job(descriptor: Path, *, repo_root: Path = ROOT) -> tuple[dict, CreativeJobFiles]:
    """Load a v2 job, validate referenced files, and fill documented defaults."""
    root = Path(repo_root).absolute()
    descriptor = Path(descriptor).absolute()
    try:
        relative = descriptor.relative_to(root).as_posix()
    except ValueError as exc:
        raise JobError("Job descriptor must be inside the repository") from exc
    _repo_file(root, relative, "job descriptor")
    if descriptor.stat().st_size > 1_000_000:
        raise JobError("Job descriptor exceeds 1,000,000 bytes")
    try:
        data = json.loads(descriptor.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise JobError(f"Invalid job JSON: {exc}") from exc
    required = {"schema_version", "project_id", "job_id", "title", "steps"}
    optional = {"timeout_seconds", "review_required", "inputs", "resume", "acceptance_criteria"}
    _object(data, "job", required, optional)
    if type(data["schema_version"]) is not int or data["schema_version"] != 2:
        raise JobError("Expected schema_version 2")
    project_id = _identifier(data["project_id"], "project_id")
    job_id = _identifier(data["job_id"], "job_id")
    if relative != f"projects/{project_id}/jobs/{job_id}/job.json":
        raise JobError("Job location must be projects/<project_id>/jobs/<job_id>/job.json")
    _string(data["title"], "title")
    data.setdefault("timeout_seconds", 18000)
    _integer(data["timeout_seconds"], "timeout_seconds", 30, 19800)
    data.setdefault("review_required", True)
    if type(data["review_required"]) is not bool:
        raise JobError("review_required must be boolean")
    criteria = data.setdefault("acceptance_criteria", DEFAULT_CRITERIA.copy())
    if not isinstance(criteria, list) or not 1 <= len(criteria) <= 32:
        raise JobError("acceptance_criteria must contain 1..32 strings")
    for criterion in criteria:
        _string(criterion, "acceptance criterion", high=1000)
    if "resume" in data:
        _resume(data["resume"], project_id)
    inputs = data.setdefault("inputs", [])
    if not isinstance(inputs, list) or len(inputs) > 4096:
        raise JobError("inputs must be an array of at most 4096 entries")
    targets: set[str] = set()
    input_files = []
    for item in inputs:
        _object(item, "input", {"path", "target", "sha256"})
        source = safe_relative_path(item["path"], "input.path")
        if not any(source.startswith(f"projects/{project_id}/{area}/") for area in ("inputs", "source")):
            raise JobError("input.path must be under this project's inputs/ or source/")
        target = safe_relative_path(item["target"], "input.target")
        if target in targets or any(target.startswith(previous + "/") or previous.startswith(target + "/") for previous in targets):
            raise JobError("input.target paths collide")
        targets.add(target)
        if not isinstance(item["sha256"], str) or not SHA256.fullmatch(item["sha256"]):
            raise JobError("input.sha256 must be a lowercase SHA-256 digest")
        path = _repo_file(root, source, "input.path")
        if _hash(path) != item["sha256"]:
            raise JobError(f"Input SHA-256 mismatch: {source}")
        input_files.append(path)
    steps = data["steps"]
    if not isinstance(steps, list) or not 1 <= len(steps) <= 32:
        raise JobError("steps must contain 1..32 entries")
    ids: set[str] = set()
    scripts: dict[str, Path] = {}
    for step in steps:
        _object(step, "step", {"id", "tool"}, {"script", "params", "operation", "source_blend", "preview", "timeout_seconds"})
        step_id = _identifier(step["id"], "step.id")
        if step_id in ids:
            raise JobError("step.id values must be unique")
        ids.add(step_id)
        tool = step["tool"]
        if not isinstance(tool, str) or tool not in TOOLS:
            raise JobError(f"Unsupported or unavailable tool: {tool}")
        _json_params(step.setdefault("params", {}))
        if "timeout_seconds" in step:
            _integer(step["timeout_seconds"], "step.timeout_seconds", 30, 19800)
        if tool in {"blender", "python"}:
            if "operation" in step or (tool == "python" and ({"source_blend", "preview"} & step.keys())):
                raise JobError(f"Unexpected fields for {tool} script step")
            script_name = safe_relative_path(step.get("script"), "step.script")
            if not script_name.endswith(".py"):
                raise JobError("step.script must be a .py file")
            script = _repo_file(root, f"projects/{project_id}/jobs/{job_id}/{script_name}", "step.script")
            if script.stat().st_size > 1_000_000:
                raise JobError("step.script exceeds 1,000,000 bytes")
            try:
                ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
            except (SyntaxError, UnicodeError) as exc:
                raise JobError(f"Invalid Python script: {exc}") from exc
            scripts[step_id] = script
            if "source_blend" in step:
                source = _logical_input(step["source_blend"], targets)
                if not source.endswith(".blend"):
                    raise JobError("source_blend must end in .blend")
            if "preview" in step:
                _preview(step["preview"])
        else:
            if {"script", "source_blend", "preview"} & step.keys():
                raise JobError(f"Unexpected script/Blender fields for {tool}")
            _operation(step, targets)
    return data, CreativeJobFiles(descriptor.parent, descriptor, root / "projects" / project_id, scripts, tuple(input_files))
