from __future__ import annotations

import json
import os
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]


class ConfigError(RuntimeError):
    pass


def _blender_candidates() -> list[Path]:
    candidates: list[Path] = []
    configured = os.environ.get("BLENDER_BIN", "").strip()
    if configured:
        candidates.append(Path(configured))
    found = shutil.which("blender")
    if found:
        candidates.append(Path(found))
    if os.name == "nt":
        program_files = Path(os.environ.get("ProgramFiles", "C:/Program Files"))
        candidates.extend(sorted(program_files.glob("Blender Foundation/Blender */blender.exe"), reverse=True))
    else:
        candidates.extend(
            [
                Path("/usr/bin/blender"),
                Path("/usr/local/bin/blender"),
                ROOT / "runtime" / "blender" / "blender",
            ]
        )
    return candidates


def locate_blender(configured: str = "") -> Path:
    candidates = ([Path(configured)] if configured else []) + _blender_candidates()
    seen: set[Path] = set()
    for candidate in candidates:
        expanded = candidate.expanduser()
        try:
            resolved = expanded.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file():
            return resolved
    raise ConfigError("Blender executable was not found. Set blender_bin in config.json or BLENDER_BIN.")


def load_config(path: Path | None = None) -> dict:
    config_path = path or (ROOT / "config.json")
    if not config_path.is_file():
        config_path = ROOT / "config.example.json"
    data = json.loads(config_path.read_text(encoding="utf-8"))
    required = {
        "schema_version",
        "repository",
        "branch",
        "poll_seconds",
        "blender_bin",
        "git_sync",
        "git_publish",
        "max_publish_bytes",
        "max_job_seconds",
    }
    missing = required - set(data)
    if missing:
        raise ConfigError(f"Missing config keys: {sorted(missing)}")
    if data["schema_version"] != 1:
        raise ConfigError("Unsupported config schema_version")
    return data
