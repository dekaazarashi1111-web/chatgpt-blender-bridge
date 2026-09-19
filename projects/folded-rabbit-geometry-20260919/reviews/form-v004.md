# form-v004 — changes requested / 2026-09-19 continuation

Source: e67bb2848173b8c31f4b28e2b054999ed3c951de
Run: https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35433907363 attempt 1. prepare/create and all tool steps completed successfully; the previous PROGRESS running statement is stale.

Release: creative-folded-rabbit-geometry-20260919-form-v004-35433907363-1-3
Archive SHA256: 079b97150104e94be776e3396ae06b112f416a5680f8d45b919d4030ba4f3be2
Manifest SHA256: 6dddb80268cde1edb1c508b228cc1314fc9c48b21b1295d1d6e0b6cb8a357184
Source model: output/model/model.blend, 135385476 bytes, SHA256 6f9c5d9fc58968a0b819b21b1239948b7f29db0ac424e313b9ff3f9878a16269.
Delivery model: output/package/folded_rabbit_geometry.blend, 135390076 bytes, SHA256 9ab637f33aafb8f6f751c752ed0047152f650477a81a446755e818304713175e.

## Evidence actually checked
Downloaded review artifact 10581322258 and host artifact 10581547054. Their API SHA256 values match the complete ZIP bytes: ebca5ec8838171224f1e2e1ba03c94f66da4b976a98cdfdf0c0191cce9f32749 and 95fdb3f1bf296e950380883d0021e747f152f36daf11de8499e3092f264a3ce6. The exact CI-readback latest-manifest.json matches the state hash. Independent local verification of all 99 manifest files found zero missing files, size discrepancies or SHA discrepancies. The first local verifier used the wrong field name `size`; it stopped with KeyError before checking files, was corrected to the actual `bytes` field and rerun successfully.
Both actual CI Blender 4.0.2 saved-file reopen reports pass, missing_external_files=[], all-mesh closedness and finite coordinates pass, required parts/muzzle groups and 13 image/framing checks pass. Publication errors are empty. The final Release archive was NOT independently downloaded here: CI re-downloaded its manifest, checked the archive server digest and local files; the present session downloaded the matching Actions outputs.

## Actual visual review
Opened reference_comparison.jpg, head_front.png, head_right.png, hand_detail.png, plus ears_detail.png, feet_detail.png, feet_uniform_clay.png, head_uniform_clay.png and front_uniform_clay.png in an additional contact sheet. Opened all three native 1086x1448 reference PNGs. Native reference SHA values match INPUTS.md exactly. Their texture, spots and dirt are deliberately not copied into geometry.
The lower face remains too wide and rectangular; the muzzle does not read as the two narrower padded lobes in the reference. A horizontal crown/profile transition and shallow surface striations are visible in clay. The separate cheeks are oval button-like pads rather than shaped covers whose inner seam follows the muzzle. The finger's narrow middle control creates a pinched dimple; lengths should vary slightly. The shoulder cap has a separate rounded join above the arm where the reference has a smoother padded shoulder. Toe caps, folded-ear silhouette, body, lower legs, bow and tail do not justify rebuilding in this revision. Their existing geometry can be retained.
Verdict: changes_requested. No exact-reproduction or completion claim.
