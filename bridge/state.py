from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def file_record(path: Path, *, published_path: str | None = None) -> dict:
    record = {
        "exists": path.is_file(),
        "bytes": path.stat().st_size if path.is_file() else 0,
        "sha256": sha256_file(path) if path.is_file() else None,
    }
    if published_path is not None:
        record["path"] = published_path
    return record


def public_value(value: object, run_dir: Path) -> object:
    if isinstance(value, str):
        return value.replace(str(run_dir), ".worker/run").replace(str(ROOT), ".")
    if isinstance(value, list):
        return [public_value(item, run_dir) for item in value]
    if isinstance(value, dict):
        return {key: public_value(item, run_dir) for key, item in value.items()}
    return value


def publish_artifacts(job_id: str, run_dir: Path, max_bytes: int) -> tuple[Path, dict]:
    destination = ROOT / "results" / job_id
    destination.mkdir(parents=True, exist_ok=True)
    published: dict[str, dict] = {}

    def copy_one(source: Path, relative: Path) -> None:
        target = destination / relative
        if not source.is_file():
            published[relative.as_posix()] = {"published": False, "reason": "missing"}
            return
        record = file_record(source)
        if record["bytes"] > max_bytes:
            published[relative.as_posix()] = {
                **record,
                "published": False,
                "reason": f"exceeds max_publish_bytes={max_bytes}",
            }
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix in {".json", ".log"}:
            text = source.read_text(encoding="utf-8", errors="replace")
            text = text.replace(str(run_dir), ".worker/run").replace(str(ROOT), ".")
            target.write_text(text, encoding="utf-8")
        else:
            shutil.copy2(source, target)
        published[relative.as_posix()] = {
            **file_record(target, published_path=(Path("results") / job_id / relative).as_posix()),
            "published": True,
        }

    copy_one(run_dir / "output" / "model.blend", Path("model.blend"))
    copy_one(run_dir / "blender.log", Path("blender.log"))
    copy_one(run_dir / "blender_report.json", Path("blender_report.json"))
    copy_one(run_dir / "validation.json", Path("validation.json"))
    for preview in sorted((run_dir / "previews").glob("*.png")):
        copy_one(preview, Path("previews") / preview.name)
    return destination, published
