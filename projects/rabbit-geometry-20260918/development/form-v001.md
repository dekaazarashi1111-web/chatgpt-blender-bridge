# form-v001 implementation

New geometry is generated from the measurements and direct visual interpretation in this project. No prior character .blend or prior model script is used. The single reused Git blob contains the byte-identical, verified lossy conversion of the supplied turnaround only.

Model: sampled smooth profile lofts for casing and limbs, continuous remeshed skull/cheek/orbital carriers, real boolean eye and ear cavities, swept U jaw, domed teeth, separate rounded digits and low broad feet, thin fitted belly insert, volumetric bow wings, shell hollows and jagged missing sections. No texture image nodes. Body, head and ear checkpoint before smaller limbs/details.

Views: Blender Workbench orthographic front/right/back, oblique, head details, uniform single-material clay. Bridge's own small previews remain enabled for technical validation; the high-resolution custom views are the intended visual review images. Each Blender step is automatically saved and actually reopened by bridge/tool_entry.py. Python packaging uses the actual generated files and actual reopen reports.

Job definition is intentionally not in this commit. It will be added only after these scripts and the checksummed input exist on main. Runtime execution, syntax checks, audit and visual quality are not yet verified at this preparation point.
