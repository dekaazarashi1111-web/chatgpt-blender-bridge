from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from bridge.jobs import JobError, load_job, validate_script
from bridge.state import atomic_write_json, public_value, sha256_file


ROOT = Path(__file__).resolve().parents[1]


class JobTests(unittest.TestCase):
    def validate_source(self, source: str) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "script.py"
            path.write_text(source, encoding="utf-8")
            validate_script(path)

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

    def test_blender_unit_system_is_allowed_for_known_scenes(self) -> None:
        self.validate_source("import bpy\nscene = bpy.context.scene\nscene.unit_settings.system = 'METRIC'\n")
        self.validate_source("import bpy\nbpy.context.scene.unit_settings.system = 'METRIC'\n")
        self.validate_source("import bpy\nbpy.data.scenes['Scene'].unit_settings.system = 'NONE'\n")

    def test_blender_datablock_removal_is_allowed(self) -> None:
        self.validate_source("import bpy\nbpy.data.objects.remove(bpy.data.objects['Cube'], do_unlink=True)\n")
        self.validate_source("import bpy\nbpy.data.materials.remove(bpy.data.materials['Material'])\n")

    def test_unsafe_attribute_receivers_remain_rejected(self) -> None:
        for source in (
            "thing.system('echo bad')\n",
            "thing.unit_settings.system = 'METRIC'\n",
            "thing.remove('file')\n",
            "import bpy\nscene = bpy.context.scene\nscene = other\nscene.unit_settings.system = 'METRIC'\n",
        ):
            with self.subTest(source=source), self.assertRaises(JobError):
                self.validate_source(source)


class StateTests(unittest.TestCase):
    def test_atomic_json_and_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state.json"
            atomic_write_json(path, {"state": "complete"})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["state"], "complete")
            self.assertEqual(len(sha256_file(path)), 64)

    def test_public_value_removes_machine_path(self) -> None:
        run_dir = ROOT / ".worker" / "runs" / "demo"
        payload = {"path": str(run_dir / "previews" / "front.png")}
        cleaned = public_value(payload, run_dir)
        self.assertEqual(cleaned["path"], ".worker/run/previews/front.png")


if __name__ == "__main__":
    unittest.main()
