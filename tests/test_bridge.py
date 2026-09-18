from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from bridge.jobs import JobError, load_job, validate_script
from bridge.state import atomic_write_json, sha256_file


ROOT = Path(__file__).resolve().parents[1]


class JobTests(unittest.TestCase):
    def test_example_job_is_valid(self) -> None:
        job, files = load_job(ROOT / "examples" / "jobs" / "demo-cube" / "job.json", allow_any_location=True)
        self.assertEqual(job["job_id"], "demo-cube")
        self.assertTrue(files.script.is_file())

    def test_dangerous_import_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bad.py"
            path.write_text("import subprocess\nsubprocess.run(['echo', 'bad'])\n", encoding="utf-8")
            with self.assertRaises(JobError):
                validate_script(path)

    def test_open_builtin_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bad.py"
            path.write_text("open('outside.txt', 'w')\n", encoding="utf-8")
            with self.assertRaises(JobError):
                validate_script(path)


class StateTests(unittest.TestCase):
    def test_atomic_json_and_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state.json"
            atomic_write_json(path, {"state": "complete"})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["state"], "complete")
            self.assertEqual(len(sha256_file(path)), 64)


if __name__ == "__main__":
    unittest.main()
