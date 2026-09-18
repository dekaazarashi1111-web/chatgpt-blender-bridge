# Creative runtime

This image includes Blender, Python/Pillow/numpy, ImageMagick, FFmpeg, Krita and
Material Maker 1.7. `tools.json` describes exactly which operations are callable.
Material Maker's official distribution includes its Godot runtime internally;
game creation tools and external AI APIs are not exposed.

## Build once, execute without external networking

Build `runtime/Dockerfile` from the repository root and run `runtime/smoke.py`
before approving/publishing that image. Build-time apt downloads require network
access. Ubuntu 24.04 currently supplies Blender 4.0.2; this is **not Blender 5.2**.
The official Material Maker release is also downloaded at build time and its
SHA-256 verified against `material-maker.lock.json`. Mesa lavapipe supplies CPU
Vulkan compute. Material Maker exports one PBR graph to 2048px PNG/EXR maps;
its editable source bundle is saved with the images. See `docs/MATERIAL_MAKER.md`.
`capabilities.json` reports the actual executable and library versions. Pin
production jobs to the tested GHCR image's `sha256` digest, so later apt/base
image changes cannot alter an existing job's environment.

The host downloads that image and declared inputs before creative processing.
The processing container must use all of:

- `--network none --read-only --cap-drop ALL --security-opt no-new-privileges`
- a non-root user, CPU/memory/PID limits and a writable, size-bounded `/tmp`
- read-only `/repo` and `/input` mounts, and one writable `/work` mount
- no tokens, credentials, Docker socket, host home, or other host mounts

GitHub control-plane uploads/downloads still require network access on the host.
This isolates the actual creative programs; an AST checker alone is not a Python
sandbox. The repository contains scripts and manifests, while GHCR stores the
installed software image. Existing image assets must be declared and staged
before the container starts; online asset searching cannot work inside it.

## Script contract

`bridge.adapters.build_command(step, context)` runs **inside** the container and
returns a list of argv values, never a shell string. The queue loader resolves a
job-relative script and passes its repository-relative path to this adapter.
`context` contains `repo_root`, `input_dir`, `output_dir`, `workspace_dir`,
`checkpoint_dir`, and optionally `job_file`. Logical external-tool inputs begin
with `input/` or `workspace/`; outputs are relative to this step's output folder.

Python and Blender scripts receive these globals:

| Name | Meaning |
| --- | --- |
| `JOB`, `STEP`, `PARAMS` | Job document, current step, and its parameters |
| `INPUT_DIR` | Read-only, explicitly declared inputs |
| `OUTPUT_DIR` | Current step's editable outputs |
| `WORKSPACE_DIR` | Persistent project working tree for cross-step input |
| `OUTPUT_BLEND` | Blender's final `OUTPUT_DIR / 'model.blend'` |
| `checkpoint(stage, summary='', evidence=None)` | Save a recoverable checkpoint |

For example, a Python texture script saves `OUTPUT_DIR / 'roughness.png'`, calls
`checkpoint('roughness', 'Base mask completed')`, and then continues. A Blender
script can use `bpy.context.scene.unit_settings.system = 'METRIC'` normally and
call `checkpoint('geometry')` after making the base mesh. Script-defined
procedural materials, baking and texture generation require no online service.

## Save/reopen and interruption behavior

A Blender checkpoint packs linked Blender libraries and image resources,
atomically saves `model.blend`, copies
the step's outputs to an immutable checkpoint directory, and exposes its
`checkpoint.json` only when copying has completed. It also provides a top-level
`scene.blend` for explicit resume. A Python checkpoint copies completed files
under `OUTPUT_DIR`; arbitrary changes elsewhere in `WORKSPACE_DIR` are only
captured by the outer runner's stopped-step workspace snapshots.

The layout is `checkpoints/<step>/<UTCtimestamp>-<stage>/`. Hidden dot-prefixed
directories are unfinished and must never be published. The host publishes only
completed directories. Calling `checkpoint()` performs a **local save**; durable
remote recovery begins only once the host's snapshot upload succeeds. No tool can
recover unsaved memory. Call it at meaningful boundaries, especially before long
bakes or renders, and keep writing to `OUTPUT_DIR` rather than old checkpoints.
Blender cannot embed every kind of external data: simulation caches, image
sequences and movies need explicit files retained under `OUTPUT_DIR` with
portable paths. The automatic reopen check covers images and linked libraries;
project-specific cache dependencies need their own validation.

Blender always saves a checkpoint before generating previews, actually reopens
the saved scene with embedded Python disabled, checks missing external image and
library paths, renders requested views, and restores the original saved scene.
The final editable file keeps the user's scene lighting/camera. Successful
execution does not approve visual quality; the review gate remains separate.

## Tested operations

`runtime/smoke.py` exercises real numpy/Pillow texture creation and recovery,
ImageMagick resize, layered ORA export through Krita, FFmpeg video encoding and
thumbnail extraction, and a textured Blender cube with four rendered previews,
packed images, reopen validation and editable checkpoints. The CI runtime build
must pass it before its image is promoted for production use. Krita is an export
adapter here, not automated brush painting or a general GUI-control tool.
Its version probe and export commands run under Xvfb with Qt's `xcb` backend:
Krita still initializes its window system for these command-line operations.
The smoke test also exports a six-map Material Maker terracotta graph, imports
its verified maps into Blender, verifies non-flat albedo and shader connections,
packs all texture images, saves/reopens the scene and renders four views.
