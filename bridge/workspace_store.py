"""Trusted host-side state index. Never import this module into user tool processes."""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

STATE_BRANCH = "workspace-state"


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class WorkspaceStore:
    def __init__(self, repository, source_commit, token=None):
        self.repository = repository
        self.source_commit = source_commit
        self.token = token or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise RuntimeError("GitHub token missing from trusted publisher")

    def api(self, path, data=None, method=None):
        request = Request("https://api.github.com/repos/" + self.repository + path,
                          data=None if data is None else json.dumps(data).encode(),
                          method=method or ("GET" if data is None else "POST"),
                          headers={"Authorization": "Bearer " + self.token,
                                   "Accept": "application/vnd.github+json",
                                   "Content-Type": "application/json",
                                   "X-GitHub-Api-Version": "2022-11-28",
                                   "User-Agent": "creative-bridge"})
        with urlopen(request, timeout=60) as response:
            body = response.read()
        return json.loads(body) if body else None

    def ensure_branch(self):
        try:
            self.api("/git/ref/heads/" + STATE_BRANCH)
        except HTTPError as exc:
            if exc.code != 404:
                raise
            try:
                self.api("/git/refs", {"ref": "refs/heads/" + STATE_BRANCH, "sha": self.source_commit})
            except HTTPError as conflict:
                if conflict.code != 422:
                    raise

    def get_file(self, path):
        try:
            return self.api("/contents/" + quote(path, safe="/") + "?ref=" + STATE_BRANCH)
        except HTTPError as exc:
            if exc.code == 404:
                return None
            raise

    def get_job(self, project, job):
        found = self.get_file(f"workspaces/{project}/jobs/{job}.json")
        return json.loads(base64.b64decode(found["content"])) if found else None

    def write_file(self, path, content, message):
        for attempt in range(5):
            current = self.get_file(path)
            payload = {"branch": STATE_BRANCH, "message": message,
                       "content": base64.b64encode(content).decode()}
            if current:
                payload["sha"] = current["sha"]
            try:
                return self.api("/contents/" + quote(path, safe="/"), payload, "PUT")
            except HTTPError as exc:
                if exc.code not in (409, 422) or attempt == 4:
                    raise
                time.sleep(attempt + 1)

    def save(self, record, *, review_only=False):
        self.ensure_branch()
        record = {**record, "updated_at": now()}
        project, job = record["project_id"], record["job_id"]
        content = (json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode()
        self.write_file(f"workspaces/{project}/jobs/{job}.json", content, f"workspace({project}): {job} {record['state']}")
        # The latest pointer is written only after the full per-job record exists.
        latest = self.get_file(f"workspaces/{project}/state.json") if review_only else None
        latest_job = json.loads(base64.b64decode(latest["content"])).get("job_id") if latest else None
        if not review_only or latest_job == job:
            self.write_file(f"workspaces/{project}/state.json", content, f"workspace({project}): update resume pointer")
        return record

    def publish_previews(self, project, job, work_dir):
        """Small real renders are convenient for chat; originals remain in the snapshot."""
        records = []
        for path in sorted((Path(work_dir) / "output").glob("*/previews/*.png"))[:12]:
            if path.is_symlink() or any(p.is_symlink() for p in path.parents) or not path.is_file():
                continue
            if path.stat().st_size > 2_000_000:
                continue
            relative = path.relative_to(work_dir).as_posix()
            target = f"workspaces/{project}/previews/{job}/{relative}"
            self.write_file(target, path.read_bytes(), f"workspace({project}): preview {job}")
            records.append({"path": relative, "url": f"https://github.com/{self.repository}/blob/{STATE_BRANCH}/{target}",
                            "raw_url": f"https://raw.githubusercontent.com/{self.repository}/{STATE_BRANCH}/{target}"})
        return records
