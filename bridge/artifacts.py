"""Durable, hash-pinned workspace snapshots in the current GitHub repository.

Only the trusted Actions supervisor imports this module. Tokens are used for
GitHub HTTP requests here, never copied into an archive or a tool container.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request

from bridge.state import atomic_write_json, sha256_file

MAX_ARCHIVE_BYTES = 1_800_000_000
MAX_UNPACKED_BYTES = 4 * 1024**3
MAX_FILES = 10_000
MAX_MANIFEST_BYTES = 8 * 1024**2
ARCHIVE_NAME = "workspace.tar.gz"
MANIFEST_NAME = "manifest.json"
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}\Z")
_REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
_SHA256 = re.compile(r"[a-f0-9]{64}\Z")
_RELEASE_TAG = re.compile(r"creative-[A-Za-z0-9][A-Za-z0-9._-]{0,220}\Z")
_ASSET_HOSTS = {"release-assets.githubusercontent.com", "objects.githubusercontent.com", "github-releases.githubusercontent.com"}


class ArtifactError(RuntimeError):
    pass


def _identifier(value: object, name: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise ArtifactError(f"Invalid {name}")
    return value


def _number(value: object, name: str, digits: int = 10) -> str:
    if isinstance(value, bool) or not re.fullmatch(r"[0-9]{1," + str(digits) + r"}", str(value)):
        raise ArtifactError(f"Invalid {name}")
    return str(value)


def release_tag(project_id: str, job_id: str, run_id: str, attempt: int, sequence: int) -> str:
    return "creative-" + "-".join((
        _identifier(project_id, "project_id"), _identifier(job_id, "job_id"),
        _number(run_id, "run_id", 20), _number(attempt, "attempt"), _number(sequence, "sequence"),
    ))


def _safe_path(value: object) -> str:
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > 1024:
        raise ArtifactError("Invalid snapshot path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in value.split("/")) or "\\" in value or ":" in value or "\x00" in value:
        raise ArtifactError("Unsafe snapshot path")
    return value


def _quota(value: object, maximum: int, name: str) -> int:
    if type(value) is not int or not 0 <= value <= maximum:
        raise ArtifactError(f"Invalid or excessive {name}")
    return value


def _directory_fd(path: Path) -> int:
    """Open EVERY absolute path component without following symlinks."""
    if not hasattr(os, "O_NOFOLLOW"):
        raise ArtifactError("Safe workspace snapshots require O_NOFOLLOW support")
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for component in Path(os.path.abspath(path)).parts[1:]:
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


@contextmanager
def _regular_file(root: Path, relative: str):
    """Walk using directory descriptors; a symlink swap cannot escape root."""
    if not hasattr(os, "O_NOFOLLOW"):
        raise ArtifactError("Safe workspace snapshots require O_NOFOLLOW support")
    directory = None
    descriptor = None
    try:
        directory = _directory_fd(root)
        parts = _safe_path(relative).split("/")
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        descriptor = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ArtifactError("Snapshot contains a non-regular file")
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = None
            yield stream
    except OSError as exc:
        raise ArtifactError("Snapshot file changed or could not be safely opened") from exc
    finally:
        if directory is not None:
            os.close(directory)
        if descriptor is not None:
            os.close(descriptor)


def _list_files(root: Path, maximum: int, excluded: tuple[str, ...]) -> list[str]:
    found: list[str] = []
    visited = 0

    def visit(descriptor: int, prefix: str) -> None:
        nonlocal visited
        with os.scandir(descriptor) as entries:
            for entry in entries:
                if not prefix and entry.name in excluded:
                    continue
                visited += 1
                if visited > maximum * 3:
                    raise ArtifactError("Snapshot contains too many directory entries")
                relative = _safe_path(prefix + entry.name)
                info = entry.stat(follow_symlinks=False)
                if stat.S_ISDIR(info.st_mode):
                    child = os.open(entry.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
                    try:
                        visit(child, relative + "/")
                    finally:
                        os.close(child)
                elif stat.S_ISREG(info.st_mode):
                    found.append(relative)
                    if len(found) > maximum:
                        raise ArtifactError("Snapshot contains too many files")
                else:
                    raise ArtifactError("Snapshot contains a symlink or special file")

    try:
        descriptor = _directory_fd(root)
        try:
            visit(descriptor, "")
        finally:
            os.close(descriptor)
    except OSError as exc:
        raise ArtifactError("Snapshot source changed or cannot be safely opened") from exc
    return sorted(found)


class _LimitedWriter:
    def __init__(self, raw, limit: int):
        self.raw, self.limit, self.count = raw, limit, 0

    def write(self, data: bytes) -> int:
        if self.count + len(data) > self.limit:
            raise ArtifactError("Compressed snapshot exceeds archive quota")
        count = self.raw.write(data)
        self.count += count
        return count

    def flush(self) -> None:
        self.raw.flush()


class _HashReader:
    def __init__(self, raw):
        self.raw, self.digest = raw, hashlib.sha256()

    def read(self, size: int = -1) -> bytes:
        data = self.raw.read(size)
        self.digest.update(data)
        return data


class _LimitedReader:
    def __init__(self, raw, limit: int):
        self.raw, self.remaining = raw, limit

    def read(self, size: int = -1) -> bytes:
        # Bound decompression including malicious tar extension headers.
        requested = self.remaining + 1 if size < 0 else min(size, self.remaining + 1)
        data = self.raw.read(requested)
        self.remaining -= len(data)
        if self.remaining < 0:
            raise ArtifactError("Expanded archive exceeds extraction quota")
        return data


def create_snapshot(source_dir: Path, output_dir: Path, *, repository: str,
                    project_id: str, job_id: str, run_id: str, attempt: int,
                    sequence: int, metadata: dict | None = None,
                    exclude_top_level: tuple[str, ...] = (),
                    max_archive_bytes: int = MAX_ARCHIVE_BYTES,
                    max_unpacked_bytes: int = MAX_UNPACKED_BYTES,
                    max_files: int = MAX_FILES) -> tuple[Path, Path, dict]:
    """Archive a *quiescent* checkpoint. Caller must not snapshot a running writer."""
    tag = release_tag(project_id, job_id, run_id, attempt, sequence)
    if not _REPOSITORY.fullmatch(repository):
        raise ArtifactError("Invalid repository")
    source_dir, output_dir = Path(source_dir), Path(output_dir)
    if source_dir.is_symlink():
        raise ArtifactError("Snapshot source cannot be a symlink")
    if output_dir.resolve().is_relative_to(source_dir.resolve()):
        raise ArtifactError("Archive output must be outside the snapshot source")
    if metadata is not None and (not isinstance(metadata, dict) or len(json.dumps(metadata).encode()) > 16_384):
        raise ArtifactError("Snapshot metadata must be a small JSON object")
    if not isinstance(exclude_top_level, tuple) or any(not isinstance(name, str) or "/" in _safe_path(name) for name in exclude_top_level):
        raise ArtifactError("Snapshot exclusions must be simple top-level names")
    files = _list_files(source_dir, max_files, exclude_top_level)
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path, manifest_path = output_dir / ARCHIVE_NAME, output_dir / MANIFEST_NAME
    temporary = output_dir / ".workspace.tar.gz.tmp"
    records: list[dict] = []
    total = 0
    try:
        with temporary.open("wb") as raw:
            with tarfile.open(fileobj=_LimitedWriter(raw, max_archive_bytes), mode="w|gz", format=tarfile.PAX_FORMAT) as archive:
                for relative in files:
                    with _regular_file(source_dir, relative) as stream:
                        before = os.fstat(stream.fileno())
                        total += before.st_size
                        if total > max_unpacked_bytes:
                            raise ArtifactError("Snapshot exceeds unpacked quota")
                        info = tarfile.TarInfo(relative)
                        info.size, info.mode, info.mtime = before.st_size, 0o600, 0
                        reader = _HashReader(stream)
                        archive.addfile(info, reader)
                        after = os.fstat(stream.fileno())
                        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                            raise ArtifactError("Checkpoint changed while being archived")
                        records.append({"path": relative, "bytes": info.size, "sha256": reader.digest.hexdigest()})
            raw.flush()
            os.fsync(raw.fileno())
        os.replace(temporary, archive_path)
    finally:
        temporary.unlink(missing_ok=True)
    manifest = {
        "schema_version": 1, "format": "creative-workspace", "repository": repository,
        "project_id": project_id, "job_id": job_id, "run_id": str(run_id),
        "attempt": int(attempt), "sequence": int(sequence), "release_tag": tag,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "archive": {"name": ARCHIVE_NAME, "bytes": archive_path.stat().st_size, "sha256": sha256_file(archive_path)},
        "unpacked_bytes": total, "file_count": len(records), "files": records,
        "metadata": metadata or {}, "excluded_top_level": list(exclude_top_level),
    }
    atomic_write_json(manifest_path, manifest)
    if manifest_path.stat().st_size > MAX_MANIFEST_BYTES:
        raise ArtifactError("Snapshot manifest exceeds quota")
    return archive_path, manifest_path, manifest


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class GitHubReleases:
    """Minimal same-repository REST client; remote URLs never come from a job."""
    def __init__(self, repository: str, token: str | None = None, *, opener=None):
        if not _REPOSITORY.fullmatch(repository):
            raise ArtifactError("Invalid repository")
        self.repository = repository
        self.token = token if token is not None else os.environ.get("GH_TOKEN", os.environ.get("GITHUB_TOKEN", ""))
        self.opener = opener or urllib.request.build_opener(_NoRedirect())
        self.base = f"https://api.github.com/repos/{repository}"

    def _headers(self, accept: str = "application/vnd.github+json") -> dict:
        headers = {"Accept": accept, "User-Agent": "chatgpt-creative-workspace", "X-GitHub-Api-Version": "2022-11-28"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        return headers

    def _json(self, method: str, url: str, *, payload=None, stream=None, size=None) -> dict:
        parsed = urllib.parse.urlparse(url)
        expected = f"/repos/{self.repository}/releases"
        if parsed.scheme != "https" or parsed.hostname not in {"api.github.com", "uploads.github.com"} or not (parsed.path == expected or parsed.path.startswith(expected + "/")):
            raise ArtifactError("Refusing an unrelated GitHub API path")
        headers = self._headers()
        if stream is not None:
            data = stream
            headers.update({"Content-Type": "application/octet-stream", "Content-Length": str(size)})
        elif payload is not None:
            data = json.dumps(payload).encode()
            headers["Content-Type"] = "application/json"
        else:
            data = None
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=120) as response:
                raw = response.read(MAX_MANIFEST_BYTES + 1)
        except urllib.error.HTTPError as exc:
            raise ArtifactError(f"GitHub {method} failed (HTTP {exc.code}); no workspace pointer was advanced") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ArtifactError("GitHub request failed; no workspace pointer was advanced") from None
        if len(raw) > MAX_MANIFEST_BYTES:
            raise ArtifactError("GitHub API response exceeds quota")
        try:
            result = json.loads(raw)
        except (ValueError, UnicodeError):
            raise ArtifactError("Invalid GitHub API JSON") from None
        if not isinstance(result, dict):
            raise ArtifactError("Expected GitHub API object")
        return result

    def release(self, tag: str) -> dict:
        if not isinstance(tag, str) or not _RELEASE_TAG.fullmatch(tag):
            raise ArtifactError("Invalid workspace release tag")
        return self._json("GET", self.base + "/releases/tags/" + urllib.parse.quote(tag, safe=""))

    def create_release(self, tag: str) -> dict:
        if not self.token:
            raise ArtifactError("GH_TOKEN or GITHUB_TOKEN is required to publish")
        payload = {"tag_name": tag, "name": tag, "draft": True, "prerelease": True,
                   "body": "Durable creative workspace checkpoint. Resume using the pinned manifest and archive hashes. Do not replace these assets."}
        commit = os.environ.get("GITHUB_SHA", "")
        if re.fullmatch(r"[a-fA-F0-9]{40}", commit):
            payload["target_commitish"] = commit
        return self._json("POST", self.base + "/releases", payload=payload)

    def publish_release(self, release_id: int) -> dict:
        _quota(release_id, 2**63 - 1, "release_id")
        return self._json("PATCH", self.base + f"/releases/{release_id}", payload={"draft": False})

    def upload(self, release_id: int, path: Path) -> dict:
        _quota(release_id, 2**63 - 1, "release_id")
        if path.name not in {ARCHIVE_NAME, MANIFEST_NAME}:
            raise ArtifactError("Unexpected workspace asset name")
        url = f"https://uploads.github.com/repos/{self.repository}/releases/{release_id}/assets?name={path.name}"
        with path.open("rb") as stream:
            return self._json("POST", url, stream=stream, size=path.stat().st_size)

    def download(self, asset_id: int, destination: Path, *, max_bytes: int, expected_sha256: str) -> None:
        _quota(asset_id, 2**63 - 1, "asset_id")
        if not _SHA256.fullmatch(expected_sha256):
            raise ArtifactError("Invalid expected asset digest")
        url = self.base + f"/releases/assets/{asset_id}"
        digest, total = hashlib.sha256(), 0
        for redirect in range(4):
            headers = self._headers("application/octet-stream") if redirect == 0 else {"User-Agent": "chatgpt-creative-workspace"}
            request = urllib.request.Request(url, headers=headers)
            try:
                response = self.opener.open(request, timeout=120)
            except urllib.error.HTTPError as exc:
                if exc.code not in {301, 302, 303, 307, 308}:
                    raise ArtifactError(f"GitHub asset download failed (HTTP {exc.code})") from None
                location = exc.headers.get("Location", "")
                parsed = urllib.parse.urlparse(location)
                if parsed.scheme != "https" or parsed.hostname not in _ASSET_HOSTS or parsed.username or parsed.password or parsed.port not in {None, 443}:
                    raise ArtifactError("Refusing an unrecognized asset download redirect") from None
                url = location
                continue
            except (urllib.error.URLError, TimeoutError, OSError):
                raise ArtifactError("GitHub asset download failed") from None
            try:
                with response, destination.open("wb") as stream:
                    while chunk := response.read(1024 * 1024):
                        total += len(chunk)
                        if total > max_bytes:
                            raise ArtifactError("Downloaded asset exceeds quota")
                        digest.update(chunk)
                        stream.write(chunk)
                if digest.hexdigest() != expected_sha256:
                    raise ArtifactError("Downloaded asset SHA-256 mismatch")
                return
            except Exception:
                destination.unlink(missing_ok=True)
                raise
        raise ArtifactError("Too many asset download redirects")

    def verify_upload(self, asset: dict, path: Path) -> None:
        if asset.get("size") != path.stat().st_size or asset.get("name") != path.name or asset.get("state") != "uploaded":
            raise ArtifactError("Uploaded asset metadata does not match snapshot")
        digest = sha256_file(path)
        remote_digest = asset.get("digest")
        if isinstance(remote_digest, str) and remote_digest.startswith("sha256:"):
            if remote_digest != "sha256:" + digest:
                raise ArtifactError("Uploaded asset digest mismatch")
            return
        # Older API responses omit digest. Download back and verify before publishing.
        with tempfile.TemporaryDirectory(prefix="verify-workspace-") as temporary:
            self.download(asset["id"], Path(temporary) / path.name, max_bytes=path.stat().st_size, expected_sha256=digest)


def publish_snapshot(source_dir: Path, *, repository: str, project_id: str, job_id: str,
                     run_id: str, attempt: int, sequence: int, output_dir: Path,
                     token: str | None = None, metadata: dict | None = None,
                     exclude_top_level: tuple[str, ...] = (),
                     client: GitHubReleases | None = None) -> dict:
    """Return a pointer only after all immutable release assets are verified."""
    archive_path, manifest_path, manifest = create_snapshot(
        source_dir, output_dir, repository=repository, project_id=project_id,
        job_id=job_id, run_id=run_id, attempt=attempt, sequence=sequence, metadata=metadata,
        exclude_top_level=exclude_top_level,
    )
    client = client or GitHubReleases(repository, token)
    release = client.create_release(manifest["release_tag"])
    release_id = release["id"]
    archive_asset = client.upload(release_id, archive_path)
    client.verify_upload(archive_asset, archive_path)
    manifest_asset = client.upload(release_id, manifest_path)
    client.verify_upload(manifest_asset, manifest_path)
    published = client.publish_release(release_id)
    if published.get("draft") is not False or published.get("tag_name") != manifest["release_tag"]:
        raise ArtifactError("Release publication could not be verified")
    tag = manifest["release_tag"]
    record = {
        "release_tag": tag, "release_id": release_id, "project_id": project_id, "job_id": job_id,
        "archive_sha256": manifest["archive"]["sha256"], "manifest_sha256": sha256_file(manifest_path),
        "archive_asset_id": archive_asset["id"], "manifest_asset_id": manifest_asset["id"],
        "release_url": f"https://github.com/{repository}/releases/tag/{tag}",
        "archive_url": f"https://github.com/{repository}/releases/download/{tag}/{ARCHIVE_NAME}",
        "manifest_url": f"https://github.com/{repository}/releases/download/{tag}/{MANIFEST_NAME}",
    }
    commit = (metadata or {}).get("source_commit", os.environ.get("GITHUB_SHA", ""))
    if isinstance(commit, str) and re.fullmatch(r"[a-fA-F0-9]{40}", commit):
        record["source_commit"] = commit
    return record


def validate_manifest(manifest: dict, *, repository: str, project_id: str,
                      job_id: str, tag: str, archive_sha256: str,
                      max_unpacked_bytes: int = MAX_UNPACKED_BYTES,
                      max_files: int = MAX_FILES) -> dict[str, dict]:
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1 or manifest.get("format") != "creative-workspace":
        raise ArtifactError("Unsupported workspace manifest")
    for key, expected in (("repository", repository), ("project_id", project_id), ("job_id", job_id), ("release_tag", tag)):
        if manifest.get(key) != expected:
            raise ArtifactError(f"Workspace manifest {key} mismatch")
    if release_tag(project_id, job_id, manifest.get("run_id"), manifest.get("attempt"), manifest.get("sequence")) != tag:
        raise ArtifactError("Workspace tag does not match snapshot identity")
    archive = manifest.get("archive")
    if not isinstance(archive, dict) or archive.get("name") != ARCHIVE_NAME or archive.get("sha256") != archive_sha256:
        raise ArtifactError("Workspace archive identity mismatch")
    _quota(archive.get("bytes"), MAX_ARCHIVE_BYTES, "archive bytes")
    files = manifest.get("files")
    if not isinstance(files, list) or len(files) > max_files or manifest.get("file_count") != len(files):
        raise ArtifactError("Invalid workspace file count")
    records, total = {}, 0
    for entry in files:
        if not isinstance(entry, dict):
            raise ArtifactError("Invalid workspace file entry")
        path = _safe_path(entry.get("path"))
        if path in records:
            raise ArtifactError("Duplicate workspace file path")
        size = _quota(entry.get("bytes"), max_unpacked_bytes, "file bytes")
        if not isinstance(entry.get("sha256"), str) or not _SHA256.fullmatch(entry["sha256"]):
            raise ArtifactError("Invalid workspace file hash")
        total += size
        if total > max_unpacked_bytes:
            raise ArtifactError("Workspace exceeds unpacked quota")
        records[path] = entry
    if manifest.get("unpacked_bytes") != total:
        raise ArtifactError("Workspace total size mismatch")
    # A file cannot also be a parent directory of another file.
    for path in records:
        if any(parent.as_posix() in records for parent in PurePosixPath(path).parents):
            raise ArtifactError("Conflicting workspace file paths")
    return records


class _SafeTarInfo(tarfile.TarInfo):
    def _proc_member(self, archive):
        # tarfile processes extension headers before yielding a member. Reject
        # huge metadata and sparse/link formats before that allocation occurs.
        if self.size < 0:
            raise ArtifactError("Negative tar member size")
        if self.type in {tarfile.XHDTYPE, tarfile.GNUTYPE_LONGNAME}:
            if self.size > 8192:
                raise ArtifactError("Archive metadata header exceeds quota")
        elif self.type not in {tarfile.REGTYPE, tarfile.AREGTYPE}:
            raise ArtifactError("Archive contains an unsupported member type")
        return super()._proc_member(archive)


def extract_snapshot(archive_path: Path, destination: Path, manifest: dict, *,
                     repository: str, project_id: str, job_id: str,
                     tag: str, archive_sha256: str,
                     max_unpacked_bytes: int = MAX_UNPACKED_BYTES,
                     max_files: int = MAX_FILES) -> None:
    """Extract regular files only, into a private staging directory, then rename."""
    records = validate_manifest(manifest, repository=repository, project_id=project_id,
                                job_id=job_id, tag=tag, archive_sha256=archive_sha256,
                                max_unpacked_bytes=max_unpacked_bytes, max_files=max_files)
    if archive_path.stat().st_size != manifest["archive"]["bytes"] or sha256_file(archive_path) != archive_sha256:
        raise ArtifactError("Workspace archive size or SHA-256 mismatch")
    destination = Path(destination)
    if destination.is_symlink() or (destination.exists() and (not destination.is_dir() or any(destination.iterdir()))):
        raise ArtifactError("Restore destination must be absent or an empty real directory")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staged = Path(tempfile.mkdtemp(prefix=".workspace-restore-", dir=destination.parent))
    try:
        seen: set[str] = set()
        expanded_limit = manifest["unpacked_bytes"] + len(records) * 8192 + 1024**2
        with archive_path.open("rb") as compressed, gzip.GzipFile(fileobj=compressed) as unpacked:
            with tarfile.open(fileobj=_LimitedReader(unpacked, expanded_limit), mode="r|", tarinfo=_SafeTarInfo) as archive:
                for member in archive:
                    relative = _safe_path(member.name)
                    if not member.isreg() or member.issparse() or relative in seen or relative not in records:
                        raise ArtifactError("Archive contains an unexpected, duplicate, linked, or special file")
                    entry = records[relative]
                    if member.size != entry["bytes"]:
                        raise ArtifactError("Archive file size differs from manifest")
                    target = staged / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    source = archive.extractfile(member)
                    if source is None:
                        raise ArtifactError("Archive file cannot be opened")
                    digest, count = hashlib.sha256(), 0
                    with source, target.open("xb") as output:
                        while chunk := source.read(1024 * 1024):
                            count += len(chunk)
                            if count > entry["bytes"]:
                                raise ArtifactError("Extracted file exceeds manifest size")
                            digest.update(chunk)
                            output.write(chunk)
                    target.chmod(0o600)
                    if count != entry["bytes"] or digest.hexdigest() != entry["sha256"]:
                        raise ArtifactError("Extracted file hash or size mismatch")
                    seen.add(relative)
        if seen != set(records):
            raise ArtifactError("Archive is missing manifest files")
        if destination.exists():
            destination.rmdir()
        os.replace(staged, destination)
    except (tarfile.TarError, EOFError, OSError) as exc:
        raise ArtifactError("Invalid or incomplete workspace archive") from exc
    finally:
        if staged.exists():
            shutil.rmtree(staged)


def restore_snapshot(record: dict, destination: Path, *, repository: str,
                     project_id: str, token: str | None = None,
                     client: GitHubReleases | None = None) -> dict:
    """Restore a pinned checkpoint from this repository and this project only."""
    _identifier(project_id, "project_id")
    if not isinstance(record, dict) or record.get("project_id") != project_id:
        raise ArtifactError("Resume pointer belongs to a different project")
    job_id = _identifier(record.get("job_id"), "job_id")
    for name in ("archive_sha256", "manifest_sha256"):
        if not isinstance(record.get(name), str) or not _SHA256.fullmatch(record[name]):
            raise ArtifactError("Resume requires pinned SHA-256 hashes")
    client = client or GitHubReleases(repository, token)
    release = client.release(record.get("release_tag"))
    if release.get("tag_name") != record["release_tag"] or release.get("draft") is not False:
        raise ArtifactError("Resume release does not match its pinned tag")
    if "release_id" in record and record["release_id"] != release.get("id"):
        raise ArtifactError("Resume release ID mismatch")
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise ArtifactError("Resume release assets are missing")
    selected = {}
    for name, key in ((ARCHIVE_NAME, "archive_asset_id"), (MANIFEST_NAME, "manifest_asset_id")):
        matches = [asset for asset in assets if asset.get("name") == name and asset.get("state") == "uploaded"]
        if len(matches) != 1:
            raise ArtifactError("Resume release must contain exactly one of each workspace asset")
        asset = matches[0]
        if key in record and record[key] != asset.get("id"):
            raise ArtifactError("Resume asset ID mismatch")
        selected[name] = asset
    with tempfile.TemporaryDirectory(prefix="download-workspace-") as temporary:
        manifest_path, archive_path = Path(temporary) / MANIFEST_NAME, Path(temporary) / ARCHIVE_NAME
        _quota(selected[MANIFEST_NAME].get("size"), MAX_MANIFEST_BYTES, "manifest bytes")
        client.download(selected[MANIFEST_NAME]["id"], manifest_path, max_bytes=MAX_MANIFEST_BYTES, expected_sha256=record["manifest_sha256"])
        try:
            manifest = json.loads(manifest_path.read_bytes())
        except (ValueError, UnicodeError):
            raise ArtifactError("Invalid workspace manifest JSON") from None
        validate_manifest(manifest, repository=repository, project_id=project_id, job_id=job_id,
                          tag=record["release_tag"], archive_sha256=record["archive_sha256"])
        if selected[ARCHIVE_NAME].get("size") != manifest["archive"]["bytes"]:
            raise ArtifactError("Resume archive API size differs from manifest")
        client.download(selected[ARCHIVE_NAME]["id"], archive_path, max_bytes=manifest["archive"]["bytes"], expected_sha256=record["archive_sha256"])
        extract_snapshot(archive_path, destination, manifest, repository=repository,
                         project_id=project_id, job_id=job_id, tag=record["release_tag"],
                         archive_sha256=record["archive_sha256"])
    return manifest
