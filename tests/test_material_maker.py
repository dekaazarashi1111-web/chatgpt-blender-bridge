import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bridge.material_maker import copy_source_bundle, inspect_outputs, validate_graph


class MaterialMakerTests(unittest.TestCase):
    def test_editable_source_and_relative_images_survive_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input"
            source.mkdir()
            (source / "images").mkdir()
            (source / "images/ref.png").write_bytes(b"reference bytes")
            graph = {"type": "graph", "nodes": [{"type": "material"}]}
            (source / "graph.ptex").write_text(json.dumps(graph))
            validate_graph(graph)
            staged = copy_source_bundle(source / "graph.ptex", root / "output/source")
            self.assertEqual(json.loads(staged.read_text()), graph)
            self.assertEqual((staged.parent / "images/ref.png").read_bytes(), b"reference bytes")
            with self.assertRaisesRegex(ValueError, "dedicated folder"):
                copy_source_bundle(source / "graph.ptex", source / "recursive")

    def test_source_bundle_rejects_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input"
            source.mkdir()
            (source / "graph.ptex").write_text('{}')
            (source / "link").symlink_to(root)
            with self.assertRaisesRegex(ValueError, "symlinks"):
                copy_source_bundle(source / "graph.ptex", root / "output")

    def test_missing_or_partial_exports_fail_even_with_zero_cli_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(RuntimeError, "required maps"):
                inspect_outputs(root, "clay", ["albedo"])
            (root / "clay_albedo.png").write_bytes(b"image")
            with patch("bridge.material_maker.subprocess.run") as run:
                run.return_value.stdout = "2048 2048"
                with self.assertRaisesRegex(RuntimeError, "normal"):
                    inspect_outputs(root, "clay", ["albedo", "normal"])
                run.return_value.stdout = "1 1"
                with self.assertRaisesRegex(RuntimeError, "dimensions"):
                    inspect_outputs(root, "clay", ["albedo"])

    def test_graph_must_have_exactly_one_material(self):
        for graph in ({}, {"type": "graph", "nodes": []},
                      {"type": "graph", "nodes": [{"type": "material"}, {"type": "material"}]}):
            with self.assertRaises(ValueError):
                validate_graph(graph)


if __name__ == "__main__":
    unittest.main()
