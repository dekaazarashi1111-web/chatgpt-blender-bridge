# form-v005 — changes requested

Source `464b693576b7ef291ab475149d3b9932e2014359`.
Actions https://github.com/dekaazarashi1111-web/chatgpt-blender-bridge/actions/runs/35437918879 attempt1, all tool steps exit0, finished 2026-09-19 10:56:57 UTC. Publication errors empty.
Final Release `creative-folded-rabbit-geometry-20260919-form-v005-35437918879-1-3`.
Archive 262359909 bytes / SHA256 `88ddbc0eb62eb3805c2b1d283699bdff3b7ba9d7fc1c51a824b8c1454cc73f17`.
Manifest SHA256 `a9e70d2357c836ecc733efac24d3cb625809595b20f6049bf551ab1c8929f199`.
Source blend `workspace/resume/output/model/model.blend`, 185443584 bytes / SHA256 `1b03ae315e87e6243b57349532e954fe71f9a375cdc9c02d240a8d136e3daf44`.
Delivery blend `output/package/folded_rabbit_geometry.blend`, 185448184 bytes / SHA256 `afe1a24c860d3fc2f42b61c8027eed68025eedd05808edb965151c633bdcd6db`.

## Actual evidence
Downloaded review artifact10583151870 (290559886 bytes, SHA2565576704be36c7a12a204060a1e9f14b26753e3c789dd3c18c75870aa0c6cdc29), host artifact10583321690 (15055 bytes, SHA2566e3010ec5df5fed491b511aaa1a40bc4303de1e17b7ac005fe9dfe6722a4785a). Verified both complete ZIP digests, exact CI-readback latest manifest bytes, all105 manifest output sizes/hashes with zero failures. Both saved-file CI reopen reports pass and missing external files are empty. Mesh required-parts/groups, actual mesh dimensions, finite coordinates, closedness, no image texture nodes and preservation fingerprints pass. All13 PNG dimensions and frustum evidence pass. Feet detail/clay and ears detail are the actual unchanged v004 images with exact hashes, not freshly rendered claims.
This is an independent check of downloaded Actions output bytes plus CI Release-manifest readback/server digest. It is not an independent local download of the final Release TAR itself.

## Actual visual review
Opened package/reference_comparison.jpg and full-resolution head_front.png; also opened the ten newly rendered images together (front/right/back/three_quarter/front_uniform_clay/head_front/head_right/head_three_quarter/head_uniform_clay/hand_detail). Native1086x1448 front/side/back references, including a native-pixel facial crop, were inspected. The crown's horizontal loft band and finger pinch are improved. The complete shape is still not approved: the muzzle is a flat rectangular padded block, the cheek pads look like petals applied to a spherical head rather than inset lower covers following the continuous cheek bulges, and the cleft/socket edges have small surface ripples. These are geometry errors, not issues to hide under texture.

## Continuation
Use final v005 snapshot for the next face-only job. Preserve torso, shoulders/arms, hands, hip, legs, feet, ears, bow, tail, jaw and unaffected dentition geometry except an explicitly reviewed small tooth-top correction if needed. Replace the rounded-box muzzle with smooth convex lobes and a continuous lower face. Integrate cheek bulk into the head and make thin following covers with an actual seam. Adjust the soft nose and clean the central cleft. Reuse the four isolated unchanged ear/foot/hand views by exact hash; redraw affected whole/head views.
The v005 model-step snapshot contains a valid self-contained blend, but the existing reuse renderer also expects parent render-cache files under resume. Therefore that model-only checkpoint alone does not close the later render-cache dependency. The next revision will copy necessary cached PNGs and renderer/records into its own model output before checkpointing. The final v005 snapshot has all rendered and reused outputs. Do not rerun the successful model merely to change this historical record.
