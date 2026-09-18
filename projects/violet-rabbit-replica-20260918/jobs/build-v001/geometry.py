"""Reusable explicit mesh construction for the replica; Blender 4.x."""
import bpy
import bmesh
import math
import random
from mathutils import Vector
from pathlib import Path

random.seed(9181639)
scene = bpy.context.scene
ANCHOR = None

def mesh_object(name, verts, faces, material=None):
    me = bpy.data.meshes.new(name + '_mesh')
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    if material:
        me.materials.append(material)
    for p in me.polygons:
        p.use_smooth = True
    return ob

def active(ob):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob

def apply(ob, modifier):
    active(ob)
    bpy.ops.object.modifier_apply(modifier=modifier.name)

def subd(ob, levels=1, apply_now=False):
    m = ob.modifiers.new('Soft shell subdivision', 'SUBSURF'); m.levels = levels; m.render_levels = levels
    if apply_now:
        apply(ob, m)
    return ob

def ellipsoid(name, center, radii, material, segments=48, rings=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=center)
    ob = bpy.context.object; ob.name = name
    ob.scale = radii
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(material)
    for p in ob.data.polygons: p.use_smooth = True
    return ob

def fuse(name, objects, material, voxel=.0035, smooth=3):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects: ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    ob = bpy.context.object; ob.name = name
    m = ob.modifiers.new('Continuous joined shell', 'REMESH')
    m.mode = 'VOXEL'; m.voxel_size = voxel; m.use_smooth_shade = True
    apply(ob, m)
    m = ob.modifiers.new('Sculpt smoothing', 'SMOOTH'); m.factor = .6; m.iterations = smooth
    apply(ob, m)
    ob.data.materials.clear(); ob.data.materials.append(material)
    return ob

def boolean_cut(ob, cutter):
    m = ob.modifiers.new('Actual recessed opening', 'BOOLEAN')
    m.operation = 'DIFFERENCE'; m.solver = 'EXACT'; m.object = cutter
    apply(ob, m)
    bpy.data.objects.remove(cutter, do_unlink=True)

def spow(x, p):
    return math.copysign(abs(x) ** p, x)

def shell(name, profiles, material, power=.83, around=80, subdivision=1):
    # Each section: z, half-width, front depth, back depth, y center.
    verts, faces = [], []
    for z, rx, front, back, cy in profiles:
        for j in range(around):
            a = 2 * math.pi * j / around
            sy = spow(math.sin(a), power)
            verts.append((rx * spow(math.cos(a), power), cy + sy * (back if sy >= 0 else front), z))
    for i in range(len(profiles) - 1):
        for j in range(around):
            nj = (j + 1) % around
            faces.append((i * around + j, i * around + nj, (i + 1) * around + nj, (i + 1) * around + j))
    faces += [tuple(reversed(range(around))), tuple((len(profiles) - 1) * around + j for j in range(around))]
    ob = mesh_object(name, verts, faces, material)
    if subdivision: subd(ob, subdivision, True)
    return ob

def cuff(name, start, end, depth, radius, material, damage=None, liner=None):
    start, end = Vector(start), Vector(end)
    axis = (end - start).normalized()
    if abs(axis.z) > .8:
        e1, e2 = Vector((1, 0, 0)), Vector((0, -1, 0))
    else:
        e1, e2 = Vector((0, -1, 0)), Vector((0, 0, 1))
    n, rings = 64, 32
    verts, faces = [], []
    for i in range(rings + 1):
        t = i / rings
        bevel = min(1, .79 + 4.3 * min(t, 1-t))
        taper = 1 - .035 * math.cos(math.pi * t)
        for j in range(n):
            a = 2 * math.pi * j / n
            v = start.lerp(end, t) + bevel * taper * (e1 * depth * math.cos(a) + e2 * radius * math.sin(a))
            verts.append(tuple(v))
    for i in range(rings):
        t = (i + .5) / rings
        for j in range(n):
            a = 2 * math.pi * (j + .5) / n
            if damage and damage(t, a): continue
            faces.append((i*n+j, i*n+(j+1)%n, (i+1)*n+(j+1)%n, (i+1)*n+j))
    # Open ends and real shell thickness: dark fitted lining remains underneath tears.
    ob = mesh_object(name, verts, faces, material)
    m = ob.modifiers.new('Cloth-covered shell thickness', 'SOLIDIFY'); m.thickness = .006; m.offset = -1
    apply(ob, m)
    if liner:
        cuff(name + '_dark_inner_lining', start, end, depth*.935, radius*.935, liner)
    return ob

def tube_curve(name, points, radius, material, cyclic=False, resolution=12):
    curve = bpy.data.curves.new(name + '_curve', 'CURVE'); curve.dimensions = '3D'
    curve.resolution_u = resolution; curve.bevel_depth = radius; curve.bevel_resolution = 3
    sp = curve.splines.new('BEZIER'); sp.bezier_points.add(len(points)-1)
    for b, p in zip(sp.bezier_points, points):
        b.co = p; b.handle_left_type = 'AUTO'; b.handle_right_type = 'AUTO'
    sp.use_cyclic_u = cyclic
    ob = bpy.data.objects.new(name, curve); scene.collection.objects.link(ob)
    curve.materials.append(material)
    return ob

def cylinder(name, p1, p2, radius, material, vertices=40):
    p1, p2 = Vector(p1), Vector(p2)
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=(p2-p1).length, location=(p1+p2)/2)
    ob=bpy.context.object; ob.name=name; ob.rotation_euler=(p2-p1).to_track_quat('Z', 'Y').to_euler()
    ob.data.materials.append(material)
    m=ob.modifiers.new('Machined edge', 'BEVEL'); m.width=.002; m.segments=3
    apply(ob,m)
    for p in ob.data.polygons: p.use_smooth=True
    return ob

def plain(name, color, rough=.8, metallic=0):
    mat=bpy.data.materials.new(name); mat.use_nodes=True
    bs=mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=rough
    bs.inputs['Metallic'].default_value=metallic
    bs.inputs['Specular IOR Level'].default_value=.2
    return mat

def cloth(name, key, folder, projection=.52, face_mask=False):
    mat=bpy.data.materials.new(name); mat.use_nodes=True
    nt=mat.node_tree; nd=nt.nodes; lk=nt.links
    bs=nd.get('Principled BSDF'); bs.inputs['Roughness'].default_value=.85
    bs.inputs['Specular IOR Level'].default_value=.17
    bs.inputs['Sheen Weight'].default_value=.10
    bs.inputs['Sheen Roughness'].default_value=.85
    coord=nd.new('ShaderNodeTexCoord'); coord.object=ANCHOR
    scale=nd.new('ShaderNodeVectorMath'); scale.operation='SCALE'; scale.inputs[3].default_value=.8
    lk.new(coord.outputs['Object'],scale.inputs[0])
    def tile(k, kind):
        tex=nd.new('ShaderNodeTexImage'); tex.name=k+'_'+kind
        tex.image=bpy.data.images.load(str(Path(folder)/(k+'_'+kind+'.png')),check_existing=True)
        if kind!='albedo': tex.image.colorspace_settings.name='Non-Color'
        tex.projection='BOX'; tex.projection_blend=.3; tex.extension='REPEAT'
        lk.new(scale.outputs['Vector'],tex.inputs['Vector'])
        return tex
    alb=tile(key,'albedo'); color=alb.outputs['Color']
    geo=nd.new('ShaderNodeNewGeometry'); sep=nd.new('ShaderNodeSeparateXYZ'); lk.new(geo.outputs['Normal'],sep.inputs[0])
    for view, axis, sign, weight in [('front','Y',-1,projection),('back','Y',1,projection if key=='purple' else .15),('side','X',0,projection*.45)]:
        uv=nd.new('ShaderNodeUVMap'); uv.uv_map='Ref'+view.title()
        tex=nd.new('ShaderNodeTexImage'); tex.name='Reference projection '+view
        tex.image=bpy.data.images.load(str(Path(folder)/('projection_'+view+'.png')),check_existing=True)
        tex.extension='EXTEND'; lk.new(uv.outputs['UV'],tex.inputs['Vector'])
        a=nd.new('ShaderNodeMath'); a.operation='ABSOLUTE' if sign==0 else 'MULTIPLY'
        lk.new(sep.outputs[axis],a.inputs[0]); a.inputs[1].default_value=sign
        b=nd.new('ShaderNodeMath'); b.operation='MAXIMUM'; b.inputs[1].default_value=0; lk.new(a.outputs[0],b.inputs[0])
        c=nd.new('ShaderNodeMath'); c.operation='POWER'; c.inputs[1].default_value=6; lk.new(b.outputs[0],c.inputs[0])
        d=nd.new('ShaderNodeMath'); d.name='Photo strength '+view; d.operation='MULTIPLY'; d.inputs[1].default_value=weight
        lk.new(c.outputs[0],d.inputs[0])
        mix=nd.new('ShaderNodeMixRGB'); mix.blend_type='MIX'
        lk.new(d.outputs[0],mix.inputs[0]); lk.new(color,mix.inputs[1]); lk.new(tex.outputs['Color'],mix.inputs[2]); color=mix.outputs[0]
    if face_mask:
        attr=nd.new('ShaderNodeAttribute'); attr.attribute_name='FaceMask'
        pale=tile('pale','albedo'); mix=nd.new('ShaderNodeMixRGB')
        lk.new(attr.outputs['Fac'],mix.inputs[0]); lk.new(color,mix.inputs[1]); lk.new(pale.outputs['Color'],mix.inputs[2]); color=mix.outputs[0]
    lk.new(color,bs.inputs['Base Color'])
    rough=tile(key,'roughness'); lk.new(rough.outputs['Color'],bs.inputs['Roughness'])
    height=tile(key,'height'); bump=nd.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.3; bump.inputs['Distance'].default_value=.004
    lk.new(height.outputs['Color'],bump.inputs['Height']); lk.new(bump.outputs['Normal'],bs.inputs['Normal'])
    mat['provenance']='Exemplar-derived pigment; synthetic fine nap; limited screenshot projection; see surface_report.json'
    return mat

def project_uvs(ob):
    if ob.type!='MESH': return
    me=ob.data
    layers={name:me.uv_layers.get(name) or me.uv_layers.new(name=name) for name in ['UVMap','RefFront','RefBack','RefSide']}
    for poly in me.polygons:
        for li in poly.loop_indices:
            v=ob.matrix_world @ me.vertices[me.loops[li].vertex_index].co
            layers['UVMap'].data[li].uv=(v.x*.8,v.z*.8)
            layers['RefFront'].data[li].uv=((336+v.x*254.6)/672,(11+v.z*254.6)/682)
            layers['RefBack'].data[li].uv=((336-v.x*254.6)/672,(11+v.z*254.6)/682)
            layers['RefSide'].data[li].uv=((137+v.y*254.6)/300,(11+v.z*254.6)/682)
    me.uv_layers.active=layers['UVMap']
