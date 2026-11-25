"""Build SM_ShellCasing, the shotgun shell she loads and ejects.

Run headless: blender --background --python blender_shell.py
A red plastic hull with a brass head, 1.8 cm across and 5.6 cm long (a bit
fatter than a real 12 gauge, so it reads from the game camera). The axis
is +X, the brass end at -X, origin in the middle. One material; the color
comes from a 2-texel base color texture (red, brass), so it gets an M_Env
instance like the other props. Writes Shell/SM_ShellCasing.fbx,
Shell/SM_ShellCasing_base_color.png and Source/Shell.blend.
"""
import math
import os

import bmesh
import bpy

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(R, "Shell")
RED = (0.82, 0.23, 0.16, 1.0)
BRASS = (0.85, 0.65, 0.23, 1.0)
LENGTH = 0.056
HULL_R = 0.009
RIM_R = 0.0105
BRASS_LEN = 0.013
RIM_LEN = 0.002
SIDES = 12


def ring(bm, x, r):
    return [bm.verts.new((x, r * math.cos(a), r * math.sin(a)))
            for a in (2 * math.pi * i / SIDES for i in range(SIDES))]


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.scale_length = 1.0
    me = bpy.data.meshes.new("SM_ShellCasing")
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    x0 = -LENGTH / 2
    # Profile from the brass end to the crimped tip: (x, radius, brass)
    prof = [(x0, RIM_R, True), (x0 + RIM_LEN, RIM_R, True),
            (x0 + RIM_LEN, HULL_R + 0.0003, True),
            (x0 + BRASS_LEN, HULL_R + 0.0003, True),
            (x0 + BRASS_LEN, HULL_R, False),
            (-x0 - 0.003, HULL_R, False),
            (-x0, HULL_R * 0.7, False)]
    rings = [ring(bm, x, r) for x, r, _ in prof]
    for k in range(len(rings) - 1):
        brass = prof[k][2] and prof[k + 1][2]
        for i in range(SIDES):
            j = (i + 1) % SIDES
            f = bm.faces.new((rings[k][i], rings[k][j], rings[k + 1][j],
                              rings[k + 1][i]))
            for lp in f.loops:
                lp[uv].uv = (0.75 if brass else 0.25, 0.5)
    for k, brass in ((0, True), (len(rings) - 1, False)):
        f = bm.faces.new(rings[k] if k else list(reversed(rings[k])))
        for lp in f.loops:
            lp[uv].uv = (0.75 if brass else 0.25, 0.5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("SM_ShellCasing", me)
    bpy.context.scene.collection.objects.link(ob)

    img = bpy.data.images.new("SM_ShellCasing_base_color", 2, 1)
    img.pixels = list(RED) + list(BRASS)
    os.makedirs(OUT, exist_ok=True)
    img.filepath_raw = os.path.join(OUT, "SM_ShellCasing_base_color.png")
    img.file_format = "PNG"
    img.save()
    mat = bpy.data.materials.new("MI_ShellCasing")
    me.materials.append(mat)

    for o in bpy.context.scene.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(OUT, "SM_ShellCasing.fbx"),
        use_selection=True, object_types={"MESH"}, global_scale=1.0,
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_NONE",
        mesh_smooth_type="FACE", path_mode="STRIP", bake_anim=False)
    bpy.ops.wm.save_as_mainfile(
        filepath=os.path.join(R, "Source", "Shell.blend"))


build()
