# form-v004: reviewed geometry corrections only

Preparation commit; job.json is deliberately added later. Parent is the exact final v003 snapshot documented in reviews/form-v003.md.

refine.py local syntax check and isolated modified-hand block parse passed. Git blob `9599a73d70bac3f1f5d3ebbaa9eab10f966eb13f`, SHA256 `0ac89b530563c40abc86c223c76e74cd4ef02a0a8d3fb16f6190edded8768e81`. This does NOT establish Blender execution or visual success.

Corrections: buried mandibular sweep terminations, a real hollow oral cup, shortened forefoot casing plus broad dome toes, single thumb mound, smoothly varying casing profiles, reference-positioned upper-arm/front-thigh/rear-thigh defects, and local ear/bow polishing. Eye, teeth, muzzle, whiskers, nose, tail and joint coordinates are fingerprint-protected. Geometry only; texture, final UV and rig remain excluded.

All ancestor scripts and the actual reference are copied to current output BEFORE the first modeling checkpoint; scene job identity is also updated immediately. Local checkpoint publication still must be verified remotely.

The render and package wrappers verify the actual previous expanded scripts by SHA256 before using them. The wrappers save their complete expanded execution sources inside output, and those are the render_source.py/package_source.py included in the package. No unseen helper code is downloaded. The renderer adds three 1100px damage closeups to the previous 13 technical views; all are frustum checked. README lineage text is corrected to v004. Package review state remains pending, never self-approving.

After run: read exact manifest and logs, inspect actual images against the supplied references including local front/right/back face and damaged-part crops, then save a pinned review. Further changes require a new ID.
