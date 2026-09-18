# build-v001 preparation and local checks

New model implemented from the supplied three-view proportions; no existing project .blend is reused. Registered tools: Python/Pillow/NumPy and Blender script operations. Five source files have been compiled with Python py_compile locally. All uploaded Git blob SHAs match the actual locally syntax-checked bytes.

- geometry.py 29ce0529cfbb89ae9dec77a4babeee5ea32c2012
- model.py ba9d1be86528980fb291e06557e79478d95416c2
- surfaces.py 0a4b37fccf404ed49a2d75a458ba1b483ff52893
- render.py 94debc551d56fb459f4912e1c685d8943148e2cb
- package.py 0cade37b414a891fa0ed8bad0887cc3f57e5b602

The surfaces script was actually run locally against the byte-verified reference. 2048px albedo/roughness/height images were produced, along with effective source crop resolution and provenance. The material sheet was opened: the purple and pale mottles are usable as a first lookdev source. The first ear exemplar included an outer rim and made a blocky stripe pattern; this was corrected BEFORE job submission by using a narrow safe inner-ear colour sample and recolouring purple-pigment quilting. No failed executed job ID has been overwritten.

Source crop dimensions: purple95x91; pale74x74; inner colour13x56. 2K is export size, not recovered high-resolution original texture detail. Fine nap is synthesized. Low-strength front/back/profile projection is explicitly labelled as screenshot-derived appearance information and contains some source lighting, not original intrinsic UV albedo.

The local maps are not called a remote checkpoint. GitHub execution will generate and save them through the existing Release mechanism. Blender is not installed in the chat container; actual Blender validation and visual comparison are still pending Actions. No runtime rebuild is needed based only on this absence.

Planned steps: surfaces -> model (packed save/reopen + four technical thumbnails) -> lookdev (seven Cycles CPU 768px/72sample views; denoising disabled) -> package (editable blend, all maps, source, input copy, comparison images, file hashes). Geometry and surface refinement will use a new job ID and valid snapshot once real previews are reviewed.
