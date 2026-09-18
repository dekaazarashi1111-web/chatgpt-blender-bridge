# refine-v002 preflight

Actual v001 review drives this revision, not memory or a reused other project. Resume the v001 sequence4 Release. Four revision Python files passed local py_compile; uploaded Git blob SHAs match the locally checked bytes.

- surfaces.py 4c45b00ed629bfc639ce21eb54fd0697261a72de
- refine.py 94d2846c3730e08f364761fad711e8ced0680a5d
- render.py fc03341275655b9ab2ecba3b29ed21feb43a1279
- package.py f2217ac7d3ee1b360807d6626588d0d91f4b7ddc

The new surfaces script was executed locally on byte-verified inputs. The real purple and pale texture maps were opened against the original PNG crops. Lossless pigment details are visibly retained; this is not yet validation of their appearance on the rendered model. The 2K export does not create original 2K detail. Geometry script is syntax-checked only until Blender executes it.

A larger binary crop transfer produced a different Git blob SHA and was rejected before linking into the project. Smaller exact48x48 and13x56 samples were uploaded and their expected Git SHAs matched. The rejected blob is not a declared input. The source PNG full bytes remain only in the originating chat, while the whole reference copy and exact limited crops are saved on main.

Revision preserves unaffected meshes and UV layouts, reconstructs only the visibly inadequate jaw/ears/feet/torn shells, conforms bib/bow to the actual body, changes affected materials and half-strength lighting, then renders seven896px/96sample views. Package preserves both job directories for the relative geometry helper dependency. No runtime rebuild is necessary for these changes.
