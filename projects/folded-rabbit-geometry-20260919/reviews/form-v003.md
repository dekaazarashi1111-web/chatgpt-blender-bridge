# form-v003 — changes requested after actual image review

Project folded-rabbit-geometry-20260919. Source `c89554674a7ed6a55bcb6a2d0ecefb8ffcb7711f`; Actions https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35432676691 attempt1. prepare/create and all three production steps succeeded. Final state needs_review, publication_errors empty. No duplicate was submitted while this run was active.

## Exact durable output and independently retrieved evidence
Release `creative-folded-rabbit-geometry-20260919-form-v003-35432676691-1-3`.
Archive: 172080545 bytes; SHA256 `eab8cfd9b794382f18439f37dcbda061040f551052c6f6040537d71e845b9a3f`.
Manifest: 17055 bytes; SHA256 `45d3eab89f2912a10bcdb42038b4a017d9ffaaf76718480809c639191cad358e`.
Resume blend: `workspace/resume/output/model/model.blend`, 125810148 bytes, SHA256 `7d3ca0c79a149f1377392b071444b4adbe8f94e2d71af4a2cfef3e5fa682f1bb`.
Delivery `output/package/folded_rabbit_geometry.blend`: 125814748 bytes, SHA256 `20475c878ca0188f882cf606d396b025abc6dcb5948fb633b965bc4ef35a3dc7`.

Downloaded review artifact 10581586266 (185328782 bytes, SHA256 5095e076d3ef952a728f3b856666c9db2c4d422afbf66dcf30a83e9cdf82236e) and host artifact 10581621015 (14709 bytes, SHA256 5da60a847916b44bd61ec7b2a4e49abab5fb13f1d19dbb6f367401b16811a032). Both ZIP hashes equal API digests. Independently verified exact read-back Release-manifest bytes and all 96 output-file sizes/hashes: zero missing or mismatched files. CI readback passed. The current audit obtained artifacts, not the final Release TAR directly; the next runner must verify that pinned TAR on restore.
Both Blender save/reopen validations pass, no missing external files. All visible mesh objects have zero checked nonmanifold/boundary edges. Required components, both continuous-muzzle vertex groups, finite coordinates and no image-texture nodes pass. 86 geometry objects, 1635238 vertices, 1632180 polygons. The old audit dimensions use transformed bounding-box corners and report 2.2213m; rotated ear bounding boxes overestimate actual surface height. Next audit must report actual transformed mesh-vertex extrema rather than calling that conservative box the physical height.

## Actual previews examined
Opened reference_comparison.jpg, full-resolution head_front.png, head_right.png, hand_detail.png and ears_detail.png. Generated and opened native-reference front and side height-aligned comparisons/outline overlays. Opened enlarged native reference face and mouth to distinguish geometry from the grime/colour reserved for a later session. No image-generation substitute was used.

## Improvements and remaining defects
The upper arms/shoulders are less cylindrical, the calf and thigh forms are padded, the muzzle is in a single editable mesh and the major current-reference proportions remain present. These do not constitute full acceptance.
The cheeks still appear mainly at the sides instead of covering a substantial part of the front face. The fused muzzle still shows two raised oval-boss boundaries rather than a smooth nasal-bridge transition. Eyes protrude too far in profile and have too little visible dark socket below; do not solve this by adding floating pale goggles. The mouth incorrectly exposes a row of many upper teeth. The native reference shows mainly two short upper central tips and rounded taller lower teeth, with side teeth turning inward. The new two-piece finger segments read as beads and are excessively hidden behind the palm edge. A continuous curled digit with a subtle joint groove is preferable. The top of the pelvis retains a horizontal surface band. Ear recesses have thin, sharp open-ended rims. Toe domes need an intermediate softly squared shape, between the v002 plateaus and v003 egg-like tops. Upper shoulder silhouette can be slightly narrower.

## Next controlled revision
New job ID form-v004, exact final v003 snapshot above. Replace the face's primitive-union bumps with a smooth depth field on one head shell, orient cheek covers toward the front, seat eyes in dark-lined recesses, correct visible dental layout and whisker trajectories. Refine fingers/palm edge, hip transition, toe domes and inner-ear rims. Preserve torso, lower-leg shells, tail, bow and accepted folded-cap geometry. No texture, UV finishing or rig. Run the same actual 13-view renderer and independently review the exact new outputs.

## Auxiliary silhouette measurement
Native-reference threshold maxRGB<185, connected components >80px, filled holes, model alpha>127, only overall height and horizontal bounding-box-centre alignment: front IoU 0.8812, side 0.8247, back 0.8881. These are threshold/projection-dependent diagnostics, NOT a reproduction percentage or automatic acceptance criterion. Side and rear references are not perfectly consistent projections; actual anatomical/component shape review takes priority.
