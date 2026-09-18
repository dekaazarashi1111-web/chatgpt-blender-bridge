"""Run real headless tool operations in the same isolation as production jobs.

Example: docker run --network none --read-only ... -v "$PWD:/repo:ro" \
  IMAGE python3 /repo/runtime/smoke.py --output /work/smoke
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import traceback
import zipfile


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("/repo"))
    parser.add_argument("--output", type=Path, default=Path("/work/smoke"))
    args = parser.parse_args()
    repo, work = args.repo.resolve(), args.output.resolve()
    sys.path.insert(0, str(repo))
    from bridge.adapters import build_command
    from PIL import Image
    from capabilities import capabilities

    for name in ("HOME", "XDG_CACHE_HOME", "XDG_CONFIG_HOME", "XDG_RUNTIME_DIR"):
        if os.environ.get(name):
            Path(os.environ[name]).mkdir(parents=True, exist_ok=True, mode=0o700)
    work.mkdir(parents=True, exist_ok=True)
    inputs, outputs, checkpoints = work / "inputs", work / "outputs", work / "checkpoints"
    inputs.mkdir(exist_ok=True)
    print("SMOKE capabilities", flush=True)
    report = {"capabilities": capabilities(), "operations": [], "pass": False}

    def execute(step: dict) -> Path:
        output = outputs / step["id"]
        output.mkdir(parents=True, exist_ok=True)
        context = {"repo_root": repo, "input_dir": inputs, "workspace_dir": work,
                   "output_dir": output, "checkpoint_dir": checkpoints}
        command = build_command(step, context)
        log = work / (step["id"] + ".log")
        print("SMOKE " + step["id"], flush=True)
        with log.open("w", encoding="utf-8") as stream:
            process = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                process.wait(timeout=360)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=10)
                stream.flush()
                report["operations"].append({"step": step["id"], "exit_code": 124, "log": log.name})
                raise RuntimeError(f"{step['id']} timed out after 360s: {log.read_text()[-10000:]}")
        report["operations"].append({"step": step["id"], "exit_code": process.returncode, "log": log.name})
        if process.returncode:
            raise RuntimeError(f"{step['id']} exited {process.returncode}: {log.read_text()[-10000:]}")
        return output

    try:
        if not report["capabilities"]["base_ready"]:
            raise RuntimeError("One or more required tools are unavailable")
        texture = execute({"id": "texture", "tool": "python", "script": "runtime/fixtures/texture.py"}) / "checker.png"
        with Image.open(texture) as image:
            assert image.size == (128, 128)
        shutil.copyfile(texture, inputs / "checker.png")
        resized = execute({"id": "resize", "tool": "imagemagick", "operation": "resize",
                           "params": {"input": "input/checker.png", "output": "small.png", "width": 64, "height": 64}})
        with Image.open(resized / "small.png") as image:
            assert image.size == (64, 64)

        # Real layered ORA import + raster export exercises Krita's CLI.
        with zipfile.ZipFile(inputs / "layered.ora", "w") as archive:
            archive.writestr("mimetype", "image/openraster")
            archive.writestr("stack.xml", '<image version="0.0.3" w="128" h="128" name="Smoke"><stack><layer name="Checker" src="data/layer0.png" opacity="1.0" visibility="visible" composite-op="svg:src-over" x="0" y="0"/></stack></image>')
            archive.write(texture, "data/layer0.png")
            archive.write(texture, "mergedimage.png")
        exported = execute({"id": "krita", "tool": "krita", "operation": "export",
                            "params": {"input": "input/layered.ora", "output": "export.png"}})
        with Image.open(exported / "export.png") as image:
            assert image.size == (128, 128)

        frames = inputs / "frames"
        frames.mkdir(exist_ok=True)
        for index in range(8):
            shutil.copyfile(texture, frames / f"frame{index:04d}.png")
        video = execute({"id": "video", "tool": "ffmpeg", "operation": "encode",
                         "params": {"input": "input/frames/frame%04d.png", "output": "turntable.mp4", "fps": 8}})
        assert (video / "turntable.mp4").stat().st_size > 0
        thumbnail = execute({"id": "thumbnail", "tool": "ffmpeg", "operation": "thumbnail",
                             "params": {"input": "workspace/outputs/video/turntable.mp4", "output": "frame.png"}})
        with Image.open(thumbnail / "frame.png") as image:
            assert image.size == (128, 128)

        scene = execute({"id": "scene", "tool": "blender", "script": "runtime/fixtures/scene.py",
                         "preview": {"views": ["front", "right", "back", "three_quarter"],
                                     "width": 128, "height": 128, "samples": 8}})
        scene_report = json.loads((scene / "tool_report.json").read_text())
        assert scene_report["validation"]["pass"] and scene_report["validation"]["objects"] == 1
        assert len(scene_report["previews"]) == 4
        for name in ("front", "right", "back", "three_quarter"):
            with Image.open(scene / f"previews/{name}.png") as image:
                assert image.size == (128, 128)
        scene_checkpoints = sorted((checkpoints / "scene").glob("*/checkpoint.json"))
        assert len(scene_checkpoints) >= 3
        assert all((path.parent / "scene.blend").is_file() for path in scene_checkpoints)
        assert list((checkpoints / "texture").glob("*/output/checker.png"))
        shutil.copytree(repo / "runtime/fixtures/material", inputs / "material")
        exported = execute({"id": "material", "tool": "material_maker", "operation": "export",
                            "params": {"input": "input/material/terracotta.ptex", "output": "terracotta",
                                       "maps": ["albedo", "roughness", "metallic", "normal", "height", "ao"]}})
        material_report = json.loads((exported / "material_report.json").read_text())
        assert material_report["state"] == "succeeded" and len(material_report["maps"]) >= 6
        assert (exported / material_report["source"]).is_file()
        material_scene = execute({"id": "material_scene", "tool": "blender", "script": "runtime/fixtures/material_scene.py",
                                  "preview": {"views": ["front", "right", "back", "three_quarter"],
                                              "width": 256, "height": 256, "samples": 8}})
        assert json.loads((material_scene / "material_integration.json").read_text())["pass"]
        assert json.loads((material_scene / "tool_report.json").read_text())["validation"]["pass"]
        report["pass"] = True
    except Exception as error:
        report["error"] = str(error)
        traceback.print_exc()
    finally:
        (work / "smoke_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2), flush=True)
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
