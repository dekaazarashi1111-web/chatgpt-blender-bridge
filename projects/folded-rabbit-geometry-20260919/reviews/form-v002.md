# form-v002 — actual-image review, changes requested

Reviewed in the continuation beginning 2026-09-19 08:26 UTC. Project: folded-rabbit-geometry-20260919. This is the current folded-ear, arms-down original character, not studio-smoke or the older T-pose rabbit.

## Pinned execution and durable evidence
Source commit: `72039ccb10a6b1b83d23f14abe84c46a6c416e45`.
Actions: https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35430997050 attempt 1. prepare/create are completed/success; model/render/package all exit 0. The previous PROGRESS running statement is stale. Do not rerun v002.
Final Release: `creative-folded-rabbit-geometry-20260919-form-v002-35430997050-1-3`.
Archive: 140208305 bytes, SHA256 `536ed187f54383979428459739169a9405394d76caf55476e5f74472306d5c4c`.
Manifest: SHA256 `2496607eb41d29ecc00d75a2f404c59f4c00d875df9ccb6cae0d368798663c47`.
Resume model: `workspace/resume/output/model/model.blend`, 92576224 bytes, SHA256 `adbb099ed8f76fc69a6c309064ad82b04c472c6e8d8457a3b4be49b73374d3f3`.

Downloaded review artifact 10581002720 (148856912 bytes, SHA256 e4f4e38cbfc0e2dc486585ae40d1f8ef6cfbf1ed1edc919201b2afa30d53a8af) and host artifact 10580708120 (14651 bytes, SHA256 a0c193704e72f749164c714c484111ec37c2d4584e69fd4c95a9d3d7cb136911). Both match the API digests. Independently hashed the exact Release-manifest bytes preserved by CI and every one of the 93 output files against that manifest: no mismatch or missing file. Release API asset sizes/digests also agree. CI readback passed. This audit did not itself re-download the final Release archive; the next job must restore and verify the pinned archive.
Both saved-file reopen validations pass with no missing external files. geometry_audit passes required counts, finite coordinates, checked closed shells and no image-texture nodes. 88 geometry objects, 1329434 vertices; dimensions approximately 1.03643 x 0.66758 x 2.20091 m. These are technical results, not visual acceptance.

## Images actually opened in this review
reference_comparison.jpg (front/right/back reference and current geometry), head_three_quarter.png and hand_detail.png were opened at actual pixels. The three newly attached native PNGs were also visible in the conversation. Their SHA256 values exactly match the originals recorded in INPUTS.md: front a4cd35087eab4f7366a861f6c979978f922b1142755df9fcf739dc53718886d4; side f141575e4534d9715d3d9baeec31de0ef1f5251a1f7f5d473e3ec8d71a42df4c; back 3374bfb35690e31997e1051f631d199202fe2d5a7e9164685a3630344efd158c. No new reference or texture-generation task is implied.

## Remaining visible discrepancies / next revision
The overall component layout and lowered-arm pose are present, but the form is NOT accepted as a complete reproduction. Upper arms, forearms and shins still read as straight cylinders with nearly planar end transitions rather than the reference's padded, changing cross sections. Shoulder balls remain too exposed. The hip has residual primitive-union creases. Eye apertures leave excessive pale empty space around the small recessed eyes and carry a double raised edge; the reference has fuller eyes and a quieter socket edge. Muzzle volumes have conspicuous conical top boundaries instead of a continuous bridge-to-snout transition. Ear bars are too slender and mallet-like. Toes have over-flat tops. Fingers require cleaner buried roots and the reference's articulated bends; bow lower tips need fuller extension.

Next job: new ID form-v003, pinned same-project v002 final snapshot, targeted shape refinement with new exact-version render/reopen/audit. Accepted parent import and unchanged resource verification must not be rebuilt. Preserve all needed sources and reference derivatives in the new output. Keep the two visible muzzle lobes, but a continuous editable head mesh with named muzzle regions is allowed if it removes the false surface intersection; component-object counts must describe the actual construction, not dummy objects.

## Session execution route
Remote main at session start: a0038498903f950579e97dbddfde7b0f8d8c77ef. Read that commit's CHATGPT_JOB_PROMPT, README, EXECUTION_CONTRACT, tools.json, v2 schema and samples, INPUTS/RESUME/runtime docs, current workflow and project instructions. Recursive source tree contains no AGENTS.md match. GitHub reports push permission. Actual shell git ls-remote failed with `Could not resolve host: github.com`; use the connected GitHub file/Git Data APIs and non-force main updates. Public web/raw retrieval was also unavailable; the connected artifact download succeeds. No tool success is inferred from another route's failure.

User continuation: finish geometry in this session as far as actual execution and review permit; no textures, UV finishing or rig. Record any residual mismatch honestly, never equate exit 0 with a perfect reproduction.
