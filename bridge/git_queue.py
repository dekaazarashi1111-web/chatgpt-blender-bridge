from __future__ import annotations

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


class GitError(RuntimeError):
    pass


def run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if check and completed.returncode != 0:
        raise GitError(f"Command failed ({completed.returncode}): {' '.join(command)}\n{completed.stdout}")
    return completed


def has_remote(name: str = "origin") -> bool:
    return run(["git", "remote", "get-url", name], check=False).returncode == 0


def sync(branch: str) -> None:
    if not has_remote():
        raise GitError("origin remote is not configured")
    run(["git", "pull", "--ff-only", "origin", branch])


def commit_sha_for_path(path: Path) -> str:
    relative = path.resolve().relative_to(ROOT).as_posix()
    completed = run(["git", "log", "-1", "--format=%H", "--", relative])
    sha = completed.stdout.strip()
    if not sha:
        raise GitError(f"No commit found for {relative}")
    return sha


def publish(paths: list[Path], message: str, branch: str, *, push: bool) -> str:
    relative_paths = [path.resolve().relative_to(ROOT).as_posix() for path in paths]
    run(["git", "add", "--", *relative_paths])
    changed = run(["git", "diff", "--cached", "--quiet"], check=False).returncode != 0
    if not changed:
        return run(["git", "rev-parse", "HEAD"]).stdout.strip()
    run(["git", "commit", "-m", message])
    sha = run(["git", "rev-parse", "HEAD"]).stdout.strip()
    if push:
        run(["git", "push", "origin", branch])
    return sha
