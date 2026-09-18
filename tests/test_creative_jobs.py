from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from bridge.creative_jobs import load_creative_job, safe_relative_path
from bridge.jobs import JobError


class CreativeJobTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.job_dir = self.root / "projects" / "sample" / "jobs" / "first"
        self.job_dir.mkdir(parents=True)
        self.descriptor = self.job_dir / "job.json"
        (self.job_dir / "model.py").write_text("import os\nimport bpy\nbpy.context.scene.unit_settings.system = 'METRIC'\n", encoding="utf-8")
        self.input_path = self.root / "projects" / "sample" / "inputs" / "reference.png"
        self.input_path.parent.mkdir(parents=True)
        self.input_path.write_bytes(b"reference image placeholder")
        self.job = {
            "schema_version": 2, "project_id": "sample", "job_id": "first", "title": "Sample asset",
            "inputs": [{"path": "projects/sample/inputs/reference.png", "target": "references/ref.png", "sha256": hashlib.sha256(self.input_path.read_bytes()).hexdigest()}],
            "steps": [{"id": "model", "tool": "blender", "script": "model.py"}],
        }

    def load(self, job: dict | None = None):
        self.descriptor.write_text(json.dumps(self.job if job is None else job), encoding="utf-8")
        return load_creative_job(self.descriptor, repo_root=self.root)

    def test_defaults_and_useful_python_are_valid(self) -> None:
        data, files = self.load()
        self.assertEqual(data["timeout_seconds"], 18000)
        self.assertTrue(data["review_required"])
        self.assertTrue(data["acceptance_criteria"])
        self.assertEqual(files.scripts["model"], self.job_dir / "model.py")
        self.assertEqual(files.inputs, (self.input_path,))
        self.assertEqual(files.project_directory, self.root / "projects" / "sample")

    def test_descriptor_and_identifiers_must_match(self) -> None:
        self.job["job_id"] = "second"
        with self.assertRaisesRegex(JobError, "location"):
            self.load()

    def test_relative_paths_reject_traversal_absolute_and_ambiguous_names(self) -> None:
        for value in ("../secret", "/etc/passwd", "a/../b", "a/./b", "a//b", "C:/file", "a\\b", "a/", "a\nb", "a\x00b"):
            with self.subTest(value=value), self.assertRaises(JobError):
                safe_relative_path(value)
        self.assertEqual(safe_relative_path("references/参考 01.png"), "references/参考 01.png")

    def test_symlink_script_and_input_are_rejected(self) -> None:
        for kind in ("script", "input"):
            with self.subTest(kind=kind):
                link = self.job_dir / "linked.py" if kind == "script" else self.input_path.parent / "linked.png"
                link.symlink_to(self.job_dir / "model.py" if kind == "script" else self.input_path)
                job = copy.deepcopy(self.job)
                if kind == "script":
                    job["steps"][0]["script"] = "linked.py"
                else:
                    job["inputs"][0]["path"] = "projects/sample/inputs/linked.png"
                with self.assertRaisesRegex(JobError, "symlink"):
                    self.load(job)

    def test_symlink_directory_is_rejected(self) -> None:
        (self.job_dir / "linked").symlink_to(self.job_dir, target_is_directory=True)
        self.job["steps"][0]["script"] = "linked/model.py"
        with self.assertRaisesRegex(JobError, "symlink"):
            self.load()

    def test_checksum_and_project_input_ownership(self) -> None:
        job = copy.deepcopy(self.job)
        job["inputs"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(JobError, "SHA-256 mismatch"):
            self.load(job)
        job["inputs"][0]["path"] = "projects/other/inputs/reference.png"
        with self.assertRaisesRegex(JobError, "this project's"):
            self.load(job)

    def test_colliding_input_targets_are_rejected(self) -> None:
        for target in ("references/ref.png", "references", "references/ref.png/nested"):
            with self.subTest(target=target):
                job = copy.deepcopy(self.job)
                job["inputs"].append({**job["inputs"][0], "target": target})
                with self.assertRaisesRegex(JobError, "collide"):
                    self.load(job)

    def test_typed_operations_and_blender_workspace_source(self) -> None:
        self.job["steps"] = [
            {"id": "resize", "tool": "imagemagick", "operation": "resize", "params": {"input": "input/references/ref.png", "output": "thumb.png", "width": 512, "height": 512}},
            {"id": "model", "tool": "blender", "script": "model.py", "source_blend": "workspace/resume/steps/model/model.blend"},
            {"id": "video", "tool": "ffmpeg", "operation": "encode", "params": {"input": "workspace/steps/model/frames/%04d.png", "output": "turntable.mp4", "width": 1024}},
        ]
        self.assertEqual(len(self.load()[0]["steps"]), 3)

    def test_operations_reject_shell_options_and_undeclared_inputs(self) -> None:
        base = {"id": "resize", "tool": "imagemagick", "operation": "convert", "params": {"input": "input/references/ref.png", "output": "thumb.png"}}
        for field, value in (("input", "input/missing.png"), ("input", "https://example.com/image.png"), ("output", "../bad.png"), ("output", "script.mvg"), ("args", ["-write", "/etc/passwd"])):
            job = copy.deepcopy(self.job)
            job["steps"] = [copy.deepcopy(base)]
            job["steps"][0]["params"][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(JobError):
                self.load(job)

    def test_script_is_bound_to_its_job(self) -> None:
        self.job["steps"][0]["script"] = "../first/model.py"
        with self.assertRaises(JobError):
            self.load()

    def test_unavailable_tool_and_duplicate_step_are_rejected(self) -> None:
        job = copy.deepcopy(self.job)
        job["steps"][0]["tool"] = "material_maker"
        with self.assertRaisesRegex(JobError, "unavailable"):
            self.load(job)
        self.job["steps"].append(copy.deepcopy(self.job["steps"][0]))
        with self.assertRaisesRegex(JobError, "unique"):
            self.load()

    def test_exact_resume_pointer_is_required(self) -> None:
        pointer = {"release_tag": "creative-sample-first-123-1-1", "project_id": "sample", "job_id": "first", "archive_sha256": "a" * 64, "manifest_sha256": "b" * 64, "release_id": 123}
        self.job["resume"] = pointer
        self.assertEqual(self.load()[0]["resume"], pointer)
        for field, value in (("project_id", "other"), ("release_tag", "latest"), ("archive_sha256", "a" * 63), ("manifest_sha256", "B" * 64), ("release_id", True)):
            job = copy.deepcopy(self.job)
            job["resume"][field] = value
            with self.subTest(field=field), self.assertRaises(JobError):
                self.load(job)
        del self.job["resume"]["manifest_sha256"]
        with self.assertRaises(JobError):
            self.load()

    def test_resume_may_come_from_previous_job_in_same_project(self) -> None:
        self.job["resume"] = {"release_tag": "creative-sample-previous-123-1-1", "project_id": "sample", "job_id": "previous", "archive_sha256": "a" * 64, "manifest_sha256": "b" * 64}
        self.assertEqual(self.load()[0]["resume"]["job_id"], "previous")

    def test_boolean_numbers_timeouts_and_nonfinite_params_are_rejected(self) -> None:
        for timeout in (True, 29, 19801, 5.5):
            job = copy.deepcopy(self.job)
            job["timeout_seconds"] = timeout
            with self.subTest(timeout=timeout), self.assertRaises(JobError):
                self.load(job)
        self.job["steps"][0]["params"] = {"number": float("nan")}
        with self.assertRaisesRegex(JobError, "finite"):
            self.load()

    def test_ffmpeg_sequence_matches_staged_inputs(self) -> None:
        self.job["inputs"][0]["target"] = "frames/0001.png"
        self.job["steps"] = [{"id": "video", "tool": "ffmpeg", "operation": "encode", "params": {"input": "input/frames/%04d.png", "output": "video.mp4"}}]
        self.load()
        for pattern in ("input/missing/%04d.png", "input/frames/%s.png", "input/frames/%d/%d.png"):
            self.job["steps"][0]["params"]["input"] = pattern
            with self.subTest(pattern=pattern), self.assertRaises(JobError):
                self.load()

    def test_invalid_json_shapes_raise_job_error(self) -> None:
        for value in ([], None, "job", 1):
            self.descriptor.write_text(json.dumps(value), encoding="utf-8")
            with self.subTest(value=value), self.assertRaises(JobError):
                load_creative_job(self.descriptor, repo_root=self.root)
        for field, value in (("steps", [{}]), ("inputs", [None]), ("title", "  "), ("review_required", 1)):
            job = copy.deepcopy(self.job)
            job[field] = value
            with self.subTest(field=field), self.assertRaises(JobError):
                self.load(job)

    def test_duplicate_json_keys_are_rejected(self) -> None:
        text = json.dumps(self.job).replace('"schema_version": 2', '"schema_version": 1, "schema_version": 2')
        self.descriptor.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(JobError, "Duplicate JSON key"):
            load_creative_job(self.descriptor, repo_root=self.root)

    def test_json_schema_and_runtime_agree_on_valid_descriptor(self) -> None:
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest("jsonschema is only needed for schema parity verification")
        schema = json.loads((Path(__file__).resolve().parents[1] / "creative-job.schema.json").read_text())
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(self.load()[0])
        for value in ("../a", "a/../b", "a//b", "a/", "/a", "a\\b"):
            job = copy.deepcopy(self.job)
            job["inputs"][0]["target"] = value
            self.assertTrue(list(Draft202012Validator(schema).iter_errors(job)), value)


if __name__ == "__main__":
    unittest.main()
