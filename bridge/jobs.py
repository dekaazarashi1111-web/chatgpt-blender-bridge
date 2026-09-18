from __future__ import annotations

import ast
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
JOB_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
SCRIPT_NAME = re.compile(r"^[A-Za-z0-9._-]+\.py$")
VIEWS = {"front", "right", "back", "left", "three_quarter"}
AUTOMATIC_CHECKS = {"script_exit", "blend_exists", "reopen_ok", "report_exists"}
ALLOWED_IMPORT_ROOTS = {"bpy", "math", "mathutils", "json", "random"}
DENIED_NAMES = {"open", "eval", "exec", "compile", "__import__", "input", "breakpoint"}
DENIED_ATTRIBUTES = {"system", "popen", "spawn", "unlink", "rmdir", "remove", "rmtree"}
BLENDER_DATA_COLLECTIONS = {
    "actions", "armatures", "brushes", "cache_files", "cameras", "collections", "curves",
    "fonts", "grease_pencils", "hair_curves", "images", "lattices", "libraries", "lightprobes",
    "lights", "linestyles", "masks", "materials", "meshes", "metaballs", "movieclips",
    "node_groups", "objects", "paint_curves", "palettes", "particles", "pointclouds",
    "scenes", "screens", "shape_keys", "sounds", "speakers", "texts", "textures", "volumes",
    "window_managers", "workspaces", "worlds",
}


class JobError(RuntimeError):
    pass


@dataclass(frozen=True)
class JobFiles:
    directory: Path
    descriptor: Path
    script: Path


def _inside(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def resolve_repo_path(value: str, *, must_exist: bool = True) -> Path:
    path = (ROOT / value).resolve()
    if not _inside(ROOT, path):
        raise JobError(f"Path escapes repository: {value}")
    if must_exist and not path.is_file():
        raise JobError(f"Required file does not exist: {value}")
    return path


def _attribute_path(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _attribute_path(node.value)
        if parent is not None:
            return f"{parent}.{node.attr}"
    return None


def _known_scene(node: ast.AST) -> bool:
    if _attribute_path(node) == "bpy.context.scene":
        return True
    if isinstance(node, ast.Subscript) and _attribute_path(node.value) == "bpy.data.scenes":
        return True
    return isinstance(node, ast.Call) and _attribute_path(node.func) == "bpy.data.scenes.new"


def _safe_blender_attribute(node: ast.Attribute, scene_aliases: set[str]) -> bool:
    if node.attr == "remove":
        receiver = _attribute_path(node.value)
        return receiver in {f"bpy.data.{name}" for name in BLENDER_DATA_COLLECTIONS}
    if node.attr == "system" and isinstance(node.value, ast.Attribute) and node.value.attr == "unit_settings":
        scene = node.value.value
        return _known_scene(scene) or isinstance(scene, ast.Name) and scene.id in scene_aliases
    return False


def validate_script(path: Path) -> None:
    """Legacy restrictive lint; this is not a security sandbox for Python."""
    source = path.read_text(encoding="utf-8")
    if len(source.encode("utf-8")) > 1_000_000:
        raise JobError("script.py exceeds 1,000,000 bytes")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        raise JobError(f"Invalid Python syntax: {exc}") from exc
    # Only accept scene aliases assigned once from a known Blender scene. An
    # arbitrary object's .system or .remove remains forbidden by this lint.
    stores: dict[str, int] = {}
    aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            stores[node.id] = stores.get(node.id, 0) + 1
        if isinstance(node, ast.Assign) and _known_scene(node.value):
            aliases.update(target.id for target in node.targets if isinstance(target, ast.Name))
        elif isinstance(node, ast.AnnAssign) and node.value is not None and _known_scene(node.value) and isinstance(node.target, ast.Name):
            aliases.add(node.target.id)
    scene_aliases = {name for name in aliases if stores.get(name) == 1}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] not in ALLOWED_IMPORT_ROOTS:
                    raise JobError(f"Import is not allowed: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".", 1)[0]
            if root not in ALLOWED_IMPORT_ROOTS:
                raise JobError(f"Import is not allowed: {node.module}")
        elif isinstance(node, ast.Name) and node.id in DENIED_NAMES:
            raise JobError(f"Builtin is not allowed: {node.id}")
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("__") or node.attr in DENIED_ATTRIBUTES and not _safe_blender_attribute(node, scene_aliases):
                raise JobError(f"Attribute is not allowed: {node.attr}")


def load_job(descriptor: Path, *, allow_any_location: bool = False) -> tuple[dict, JobFiles]:
    if descriptor.name != "job.json" or (not allow_any_location and descriptor.parent.parent.name != "pending"):
        raise JobError(f"Unexpected job descriptor location: {descriptor}")
    try:
        data = json.loads(descriptor.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise JobError(f"Invalid job JSON: {exc}") from exc
    allowed_keys = {
        "schema_version", "job_id", "title", "created_at", "script", "source_blend",
        "timeout_seconds", "preview", "acceptance_criteria", "review_required",
    }
    extra = set(data) - allowed_keys
    required = allowed_keys - {"source_blend"}
    missing = required - set(data)
    if extra or missing:
        raise JobError(f"Job keys mismatch. missing={sorted(missing)} extra={sorted(extra)}")
    if data["schema_version"] != 1:
        raise JobError("Unsupported job schema_version")
    if not isinstance(data["job_id"], str) or not JOB_ID.fullmatch(data["job_id"]):
        raise JobError("Invalid job_id")
    if descriptor.parent.name != data["job_id"]:
        raise JobError("job_id must match its directory name")
    if not isinstance(data["title"], str) or not 1 <= len(data["title"]) <= 200:
        raise JobError("title must be 1..200 characters")
    try:
        datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise JobError("created_at must be ISO-8601") from exc
    if not isinstance(data["script"], str) or not SCRIPT_NAME.fullmatch(data["script"]):
        raise JobError("script must be a simple .py filename")
    script = (descriptor.parent / data["script"]).resolve()
    if not _inside(descriptor.parent, script) or not script.is_file():
        raise JobError("script does not exist inside job directory")
    timeout = data["timeout_seconds"]
    if not isinstance(timeout, int) or not 30 <= timeout <= 21600:
        raise JobError("timeout_seconds must be 30..21600")
    preview = data["preview"]
    if set(preview) != {"views", "width", "height", "samples"}:
        raise JobError("preview keys are invalid")
    views = preview["views"]
    if not isinstance(views, list) or not views or len(views) != len(set(views)) or not set(views) <= VIEWS:
        raise JobError("preview.views contains invalid or duplicate values")
    for key, low, high in (("width", 128, 2048), ("height", 128, 2048), ("samples", 1, 256)):
        if not isinstance(preview[key], int) or not low <= preview[key] <= high:
            raise JobError(f"preview.{key} must be {low}..{high}")
    criteria = data["acceptance_criteria"]
    if not isinstance(criteria, list) or not 4 <= len(criteria) <= 8:
        raise JobError("acceptance_criteria must contain 4..8 items")
    ids: set[str] = set()
    for item in criteria:
        if set(item) != {"id", "description", "kind", "check"}:
            raise JobError("acceptance criterion keys are invalid")
        if not re.fullmatch(r"C[0-9]{2}", item["id"]) or item["id"] in ids:
            raise JobError("acceptance criterion IDs must be unique C00 values")
        ids.add(item["id"])
        if item["kind"] not in {"automatic", "review"}:
            raise JobError("criterion kind must be automatic or review")
        check = item["check"]
        if item["kind"] == "automatic" and check not in AUTOMATIC_CHECKS and not check.startswith("preview:"):
            raise JobError(f"Unsupported automatic check: {check}")
        if check.startswith("preview:") and check.split(":", 1)[1] not in views:
            raise JobError(f"Criterion preview is not requested: {check}")
    if not isinstance(data["review_required"], bool):
        raise JobError("review_required must be boolean")
    if data["review_required"] and not any(item["kind"] == "review" for item in criteria):
        raise JobError("review_required jobs need at least one review criterion")
    source = data.get("source_blend")
    if source is not None:
        if not isinstance(source, str) or not source.endswith(".blend"):
            raise JobError("source_blend must be null or a .blend repository path")
        resolve_repo_path(source)
    validate_script(script)
    return data, JobFiles(descriptor.parent, descriptor.resolve(), script)
