from __future__ import annotations
import base64
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from contextlib import redirect_stdout
import io

from bridge.creative_jobs import load_creative_job
from bridge.jobs import JobError
from bridge.workspace_store import WorkspaceStore
from ci.import_reference import import_reference
from ci.review_workspace import apply_review
from ci.run_creative_job import docker_command, ROOT
from ci.run_creative_job import main as run_main


class WorkspaceTests(unittest.TestCase):
    def record(self):
        return {"project_id": "sample", "job_id": "job-v001", "source_commit": "a" * 40,
                "state": "needs_review", "latest_snapshot": {"archive_sha256": "b" * 64},
                "acceptance_criteria": ["Silhouette matches"]}

    def review(self):
        return {"schema_version": 1, "project_id": "sample", "job_id": "job-v001",
                "source_commit": "a" * 40, "snapshot_sha256": "b" * 64,
                "verdict": "approved", "criteria": {"Silhouette matches": "pass"}, "summary": "Inspected four real renders."}

    def test_review_is_pinned_to_exact_artifact(self):
        self.assertEqual(apply_review(self.review(), self.record())["state"], "complete")
        changed = self.review()
        changed["snapshot_sha256"] = "c" * 64
        with self.assertRaises(ValueError):
            apply_review(changed, self.record())

    def test_failed_job_cannot_be_reviewed_complete(self):
        with self.assertRaises(ValueError):
            apply_review(self.review(), {**self.record(), "state": "failed"})

    def test_reviewing_older_job_does_not_regress_latest_pointer(self):
        store = WorkspaceStore("owner/repo", "a" * 40, "test-token")
        current = {"content": base64.b64encode(json.dumps({"job_id": "job-v002"}).encode()).decode()}
        with patch.object(store, "ensure_branch"), patch.object(store, "get_file", return_value=current), patch.object(store, "write_file") as write:
            store.save(self.record(), review_only=True)
        self.assertEqual(write.call_count, 1)
        self.assertIn("jobs/job-v001.json", write.call_args.args[0])

    def test_production_container_routes_workspace_and_pins_image(self):
        image = "ghcr.io/owner/runtime@sha256:" + "a" * 64
        args = docker_command(image, ROOT / "projects/a/jobs/b/job.json", "shape",
                              Path("/job/work"), Path("/job/inputs"), "test")
        self.assertIn("type=bind,src=/job/work,dst=/work", args)
        self.assertIn("type=bind,src=/job/inputs,dst=/input", args)
        self.assertIn(image, args)
        self.assertEqual(args[-4:], ["--job", "projects/a/jobs/b/job.json", "--step", "shape"])
        with self.assertRaises(ValueError):
            docker_command("ubuntu:latest", ROOT / "job.json", "shape", Path("/w"), Path("/i"), "test")

    def test_reference_import_hash_and_refuses_overwrite_or_escape(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "encoded.txt"
            source.write_bytes(base64.b64encode(b"reference bytes"))
            result = import_reference("sample", source, "ref.png", encoded=True, repo_root=root)
            self.assertEqual((root / result["path"]).read_bytes(), b"reference bytes")
            self.assertEqual(len(result["sha256"]), 64)
            with self.assertRaises(FileExistsError):
                import_reference("sample", source, "ref.png", encoded=True, repo_root=root)
            with self.assertRaises(JobError):
                import_reference("sample", source, "../escape.png", repo_root=root)

    def test_all_committed_v2_jobs_load(self):
        descriptors = sorted((ROOT / "projects").glob("*/jobs/*/job.json"))
        self.assertGreaterEqual(len(descriptors), 2)
        for descriptor in descriptors:
            job, _ = load_creative_job(descriptor)
            self.assertLessEqual(job["timeout_seconds"], 19800)

    def test_interrupted_job_preserves_resume_pointer_and_does_not_restart(self):
        old = {**self.record(), "state": "running", "run_id": "99", "run_attempt": "1"}
        store = MagicMock()
        store.get_job.return_value = old
        store.api.return_value = {"status": "completed"}
        with patch("sys.argv", ["runner", "--job", "projects/studio-smoke/jobs/blender-v001/job.json", "--image", "unused"]), patch.dict("os.environ", {"GITHUB_RUN_ID": "100", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_SHA": "a" * 40}), patch("ci.run_creative_job.WorkspaceStore", return_value=store), patch("ci.run_creative_job.subprocess.Popen") as launch, redirect_stdout(io.StringIO()):
            self.assertEqual(run_main(), 0)
        launch.assert_not_called()
        saved = store.save.call_args.args[0]
        self.assertEqual(saved["state"], "blocked")
        self.assertEqual(saved["latest_snapshot"], old["latest_snapshot"])


if __name__ == "__main__":
    unittest.main()
