"""Market stall kit: steel pipe frame and a sloped, sagging tarp.

Run in Blender; writes Art/Environment/Source/StallKit.blend and
Art/Environment/Stall/SM_StallFrame.fbx, SM_StallTarp.fbx. Centimeters
(unit scale 0.01). Front is +X, the footprint matches the graybox stall
awning (396 x 366 cm); the tarp runs from 285 cm at the back to 250 cm
at the front, sags 9 cm and has a scalloped valance along the front.
Tarp UVs tile every 60 cm across, for the stripe texture.
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

W, DP = 366.0, 396.0
ZF, ZB = 250.0, 285.0
ART = r"C:\Users\vvovchenko\repo\acrpg\Art"


def pipe(bm, a, b, r=3.0):
    a, b = Vector(a), Vector(b)
    rot = (b - a).to_track_quat('Z', 'Y').to_matrix().to_4x4()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=r,
                          radius2=r, depth=(b - a).length,
                          matrix=Matrix.Translation((a + b) / 2) @ rot)


def frame():
    me = bpy.data.meshes.new("SM_StallFrame")
    bm = bmesh.new()
    xs = (-DP / 2 + 8, DP / 2 - 8)
    ys = (-W / 2 + 6, W / 2 - 6)
    for x in xs:
        top = ZF if x > 0 else ZB
        for y in ys:
            pipe(bm, (x, y, 0), (x, y, top - 4))
        pipe(bm, (x, ys[0], top - 6), (x, ys[1], top - 6), 2.5)
    for y in ys:
        pipe(bm, (xs[0], y, ZB - 6), (xs[1], y, ZF - 6), 2.5)
    bm.to_mesh(me)
    bm.free()
    return me


def tarp():
    me = bpy.data.meshes.new("SM_StallTarp")
    bm = bmesh.new()
    nx, ny, ox, oy = 10, 12, 18.0, 14.0
    v = {}
    for i in range(nx + 1):
        for j in range(ny + 1):
            u, w = i / nx, j / ny
            sag = 9.0 * math.sin(math.pi * w) * \
                math.sin(math.pi * min(1, u * 1.1))
            v[i, j] = bm.verts.new((-DP / 2 - ox + (DP + 2 * ox) * u,
                                    -W / 2 - oy + (W + 2 * oy) * w,
                                    ZB + (ZF - ZB) * u - sag))
    for i in range(nx):
        for j in range(ny):
            bm.faces.new((v[i, j], v[i + 1, j], v[i + 1, j + 1],
                          v[i, j + 1]))
    xf, nv = DP / 2 + ox, 24
    top, bot = [], []
    for k in range(nv + 1):
        y = -W / 2 - oy + (W + 2 * oy) * k / nv
        top.append(bm.verts.new((xf, y, ZF + 0.5)))
        bot.append(bm.verts.new((xf + 1, y,
                                 ZF - (22.0 if k % 2 == 0 else 34.0))))
    for k in range(nv):
        bm.faces.new((top[k], top[k + 1], bot[k + 1], bot[k]))
    uv = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for lp in f.loops:
            co = lp.vert.co
            lp[uv].uv = ((co.y + W / 2 + oy) / 60.0,
                         (co.x + DP / 2 + ox) / 60.0 + co.z / 200.0)
    bm.to_mesh(me)
    bm.free()
    return me


def build():
    bpy.ops.wm.read_homefile(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 0.01
    fo = bpy.data.objects.new("SM_StallFrame", frame())
    to = bpy.data.objects.new("SM_StallTarp", tarp())
    for o in (fo, to):
        sc.collection.objects.link(o)
    to.modifiers.new("solid", 'SOLIDIFY').thickness = 1.5
    sys.path.insert(0, os.path.join(ART, "Enemies", "Scripts"))
    import blender_export as E
    with bpy.context.temp_override(**E.ctx(), active_object=to,
                                   selected_objects=[to],
                                   selected_editable_objects=[to]):
        bpy.ops.object.modifier_apply(modifier="solid")
    out = os.path.join(ART, "Environment", "Stall")
    os.makedirs(out, exist_ok=True)
    for o in (to, fo):
        E.fbx(os.path.join(out, o.name + ".fbx"), [o], anim=False)
    bpy.ops.wm.save_as_mainfile(
        filepath=os.path.join(ART, "Environment", "Source", "StallKit.blend"))
