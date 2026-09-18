from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from bridge.adapters import AdapterError, build_command


ROOT = Path(__file__).resolve().parents[1]


class AdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.inputs = self.root / "input"
        self.workspace = self.root / "workspace"
        for path in (self.repo, self.inputs, self.workspace):
            path.mkdir()
        (self.repo / "build.py").write_text("pass\n")
        (self.inputs / "source.png").write_bytes(b"image-placeholder")
        (self.repo / "bridge").symlink_to(ROOT / "bridge", target_is_directory=True)
        self.context = {"repo_root": self.repo, "input_dir": self.inputs, "workspace_dir": self.workspace,
                        "output_dir": self.workspace / "output", "checkpoint_dir": self.workspace / "checkpoints"}

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_blender_passes_script_parameters_as_argv(self) -> None:
        command = build_command({"id": "make", "tool": "blender", "script": "build.py",
                                 "params": {"label": "$(do-not-run); `no-shell`"}}, self.context)
        self.assertIn("--python", command)
        self.assertNotIn("sh", command)
        self.assertIn("$(do-not-run)", command[command.index("--step-json") + 1])

    def test_input_output_and_script_cannot_escape(self) -> None:
        for value in ("../outside.png", "/etc/passwd", "input/../../outside.png", "input/./source.png", "https://example.org/a.png"):
            with self.subTest(path=value), self.assertRaises(AdapterError):
                build_command({"tool": "imagemagick", "operation": "convert",
                               "params": {"input": value, "output": "a.png"}}, self.context)
        with self.assertRaises(AdapterError):
            build_command({"tool": "imagemagick", "operation": "convert",
                           "params": {"input": "input/source.png", "output": "../escape.png"}}, self.context)
        with self.assertRaises(AdapterError):
            build_command({"tool": "python", "script": "../escape.py"}, self.context)

    def test_symlinks_cannot_escape_declared_mount(self) -> None:
        external = self.root / "private.png"
        external.write_text("not an input")
        (self.inputs / "link.png").symlink_to(external)
        with self.assertRaises(AdapterError):
            build_command({"tool": "imagemagick", "operation": "convert",
                           "params": {"input": "input/link.png", "output": "a.png"}}, self.context)

    def test_adapter_parameters_and_output_formats(self) -> None:
        for changes in ({"args": ["-write", "/tmp/other"]}, {"output": "a.pdf"}):
            with self.subTest(changes=changes), self.assertRaises(AdapterError):
                build_command({"tool": "imagemagick", "operation": "convert",
                               "params": {"input": "input/source.png", "output": "a.png", **changes}}, self.context)

    def test_ffmpeg_resolves_numbered_input_sequences(self) -> None:
        (self.inputs / "frame0000.png").write_bytes(b"image-placeholder")
        command = build_command({"tool": "ffmpeg", "operation": "encode",
                                 "params": {"input": "input/frame%04d.png", "output": "preview.mp4"}}, self.context)
        self.assertEqual(command[command.index("-i") + 1], str(self.inputs / "frame%04d.png"))
        for pattern in ("input/frame%s.png", "input/frame%04d*.png", "input/missing%04d.png"):
            with self.subTest(pattern=pattern), self.assertRaises(AdapterError):
                build_command({"tool": "ffmpeg", "operation": "encode",
                               "params": {"input": pattern, "output": "preview.mp4"}}, self.context)

    def test_material_maker_export_is_typed_and_local(self) -> None:
        (self.inputs / "sample.ptex").write_text('{}')
        step = {"tool": "material_maker", "operation": "export",
                "params": {"input": "input/sample.ptex", "output": "clay", "maps": ["albedo", "normal"]}}
        command = build_command(step, self.context)
        self.assertIn("--maps", command)
        self.assertEqual(json.loads(command[-1]), ["albedo", "normal"])
        for key, value in (("output", "../bad"), ("output", "--help"), ("maps", []),
                           ("maps", ["albedo", "albedo"]), ("maps", ["script"]), ("args", ["--script", "bad.gd"])):
            with self.subTest(key=key, value=value), self.assertRaises(AdapterError):
                build_command({**step, "params": {**step["params"], key: value}}, self.context)

    def test_python_checkpoint_retains_previous_editable_output(self) -> None:
        (self.repo / "build.py").write_text(
            "target = OUTPUT_DIR / 'texture.txt'\n"
            "target.write_text('first')\n"
            "checkpoint('first', 'saved initial texture')\n"
            "target.write_text('second')\n", encoding="utf-8")
        command = build_command({"id": "texture", "tool": "python", "script": "build.py"}, self.context)
        command[0] = sys.executable
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        checkpoints = sorted((self.workspace / "checkpoints/texture").glob("*/checkpoint.json"))
        self.assertEqual(len(checkpoints), 2)
        first = next(path for path in checkpoints if json.loads(path.read_text())["stage"] == "first")
        self.assertEqual((first.parent / "output/texture.txt").read_text(), "first")
        self.assertEqual((self.workspace / "output/texture.txt").read_text(), "second")
        report = json.loads((self.workspace / "output/tool_report.json").read_text())
        self.assertEqual(report["state"], "succeeded")

    def test_python_failure_preserves_completed_checkpoint(self) -> None:
        (self.repo / "build.py").write_text(
            "(OUTPUT_DIR / 'texture.txt').write_text('recoverable')\n"
            "checkpoint('saved')\n"
            "raise RuntimeError('intentional interruption')\n", encoding="utf-8")
        command = build_command({"id": "texture", "tool": "python", "script": "build.py"}, self.context)
        command[0] = sys.executable
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertNotEqual(result.returncode, 0)
        checkpoints = list((self.workspace / "checkpoints/texture").glob("*/checkpoint.json"))
        self.assertEqual(len(checkpoints), 1)
        self.assertEqual((checkpoints[0].parent / "output/texture.txt").read_text(), "recoverable")
        self.assertEqual(json.loads((self.workspace / "output/tool_report.json").read_text())["state"], "failed")


if __name__ == "__main__":
    unittest.main()
