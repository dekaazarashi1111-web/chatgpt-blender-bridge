# form-v001 preflight

Inputs and all four scripts were committed before job.json. Scripts locally parsed with Python py_compile. Blender geometry execution and visual acceptance are not yet claimed.

Current shared implementation limits `resume` to the same project (`bridge.artifacts.restore_snapshot`). Keep that safeguard unchanged. This new project's explicit `import` Python step reads the one public same-repository parent Release named in DECISIONS, verifies both SHA256 pins, validates its original project/job/tag, securely extracts and verifies every manifest entry using the existing extractor, and retains just the actual editable parent model and source/evidence needed for this derivative. The Blender step opens `workspace/output/import/parent/model.blend`. This is an explicitly documented source-asset import, not a forged same-project resume pointer.

Four bounded steps: import (1800 s), geometry (5400 s), renders (7200 s), package (900 s), within total 18000 s. Built-in Blender previews are tiny audit thumbnails; 13 separately rendered high-resolution Workbench images are the actual geometry review evidence. Checkpoint after body/limbs, face, full geometry, views and delivery. Do not count a local checkpoint as a remote save before publication.

Current references change the exterior proportions and pose, so affected geometry is rebuilt. Twenty-three eye/nose/dental meshes are inherited from the saved scene and refitted; original materials and verified geometric helpers are reused. Old project and its concurrently submitted form-v004 are left untouched. This new project is not a duplicate of the old T-pose revision.

The first main ref update was correctly rejected as non-fast-forward after concurrent changes. Compared 83739b1..dd37d7b: only old rabbit project files changed, no shared contract/runtime changes. Rebased only this new directory onto dd37d7b and successfully updated main without force (760c6d6). Subsequent file commits preserve current main.

Required next: track the actual run; inspect logs/state/Release readback; retrieve images; compare against original PNGs, not just old saved reference; correct differences with a new job ID; write a pinned review. No claim of complete reproduction from a successful exit alone.
