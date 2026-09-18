from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from bridge.config import load_config
from bridge.git_queue import GitError
from bridge.worker import process_job, reconcile_reviews

ROOT = Path(__file__).resolve().parents[1]


class LegacyWorkerTests(unittest.TestCase):
    def test_job_runs_with_standard_config_and_local_sources(self):
        config = load_config(ROOT / "config.example.json")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            job_dir = root / "pending/demo-cube"
            shutil.copytree(ROOT / "examples/jobs/demo-cube", job_dir)
            run_dir = root / "run"

            def execute(command, log_path, timeout):
                if "--report" in command:
                    (run_dir / "validation.json").write_text('{"pass": true}')
                else:
                    (run_dir / "output").mkdir()
                    (run_dir / "output/model.blend").write_bytes(b"test fixture")
                    (run_dir / "blender_report.json").write_text('{}')
                    (run_dir / "previews").mkdir()
                    for view in ("front", "right", "back", "three_quarter"):
                        (run_dir / f"previews/{view}.png").write_bytes(b"test fixture")
                return 0, False

            with patch("bridge.worker.commit_sha_for_path", side_effect=GitError("Uncommitted source")), \
                 patch("bridge.worker.locate_blender", return_value=Path("blender")), \
                 patch("bridge.worker._run_process", side_effect=execute) as launch:
                result = process_job(job_dir / "job.json", config,
                                     publish_updates=False, publish_results=False,
                                     run_dir_override=run_dir,
                                     status_path_override=root / "status.json")
            self.assertEqual(launch.call_count, 2)
            self.assertEqual(result["state"], "complete")
            self.assertEqual(result["source_commits"]["script"], {"commit": "local"})
            self.assertEqual(json.loads((root / "status.json").read_text())["state"], "complete")

    def test_review_updates_quality_state_with_standard_config(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for folder in ("queue/status", "queue/reviews", "results/sample"):
                (root / folder).mkdir(parents=True)
            status = root / "queue/status/sample.json"
            status.write_text(json.dumps({"state": "needs_review"}))
            manifest = root / "results/sample/manifest.json"
            manifest.write_text(json.dumps({"acceptance_criteria": [
                {"id": "C01", "kind": "review", "status": "pending_review"}]}))
            (root / "queue/reviews/sample.json").write_text(json.dumps({
                "schema_version": 1, "job_id": "sample", "verdict": "approved",
                "reviewed_at": "2026-09-18T00:00:00Z", "summary": "Preview checked",
                "criteria": {"C01": "pass"}}))
            with patch("bridge.worker.ROOT", root):
                changed = reconcile_reviews(load_config(ROOT / "config.example.json"), publish_updates=False)
            self.assertEqual(changed, 1)
            self.assertEqual(json.loads(status.read_text())["state"], "complete")
            self.assertEqual(json.loads(manifest.read_text())["review"]["criteria"], {"C01": "pass"})


if __name__ == "__main__":
    unittest.main()
