"""SM_BackpackOpen: the backpack she digs in while the backpack panel is open.

Run inside Blender with Source/Props.blend open:
  exec(open(r"<this file>").read()); build()
Makes SM_BackpackOpen from SM_Backpack (which stays as it is) and exports
Backpack/SM_BackpackOpen.fbx:
* the closed top above CUT_Z is cut off and swung back on a hinge at the
  back top edge, so the bag stands open,
* the opening is closed with dark faces sunk INNER cm into the bag (UV
  on a dark texel, DARK_UV) and the underside of the flap with leather
  ones (LINING_UV), so the top-down camera never sees through them,
* the shoulder straps (thin one-sided ribbons that look like debris on
  the ground) with their side buckles and slivers of fewer than SLIVER
  vertices left by the cut are deleted,
* a corn cob (SM_CornCob, second material slot) sticks out of the
  opening,
* scaled by SCALE to her size (65 cm chicken: about 24 cm wide), origin
  at the bottom center, front (pocket) toward -Y like the source.
"""
import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

ART = r"C:\Users\vvovchenko\repo\acrpg\Art\Props"
CUT_Z = 22.0
FLAP_DEG = 150.0
INNER = 4.0
DARK_UV = (0.441, 0.598)
LINING_UV = (0.895, 0.176)
SLIVER = 20
SCALE = 0.9
COB_POS = Vector((3.0, -2.0, 19.0))
COB_ROT = (math.radians(-20), math.radians(25), 0)


def boundary_loops(bm, faces):
    """Ordered vertex loops of the open edges of the given faces."""
    fs = set(faces)
    edges = [e for e in bm.edges
             if len([f for f in e.link_faces if f in fs]) == 1]
    left = set(edges)
    loops = []
    while left:
        e = left.pop()
        loop = [e.verts[0], e.verts[1]]
        while True:
            nxt = next((x for x in loop[-1].link_edges if x in left), None)
            if not nxt:
                break
            left.discard(nxt)
            v = nxt.other_vert(loop[-1])
            if v == loop[0]:
                break
            loop.append(v)
        loops.append(loop)
    return loops


def islands(bm):
    """Vertex sets of the connected parts of the mesh."""
    seen = set()
    parts = []
    for v in bm.verts:
        if v in seen:
            continue
        part = {v}
        stack = [v]
        while stack:
            for e in stack.pop().link_edges:
                for w in e.verts:
                    if w not in part:
                        part.add(w)
                        stack.append(w)
        seen |= part
        parts.append(part)
    return parts


def cap(bm, loop, depth, uv_layer, up, uv):
    """Close a loop with a dark wall sunk by depth and a fan at its end."""
    c = sum((v.co for v in loop), Vector()) / len(loop)
    inner = []
    for v in loop:
        p = c + (v.co - c) * 0.9 - up * depth
        inner.append(bm.verts.new(p))
    new = []
    n = len(loop)
    for i in range(n):
        a, b = loop[i], loop[(i + 1) % n]
        ia, ib = inner[i], inner[(i + 1) % n]
        new.append(bm.faces.new((a, b, ib, ia)))
    center = bm.verts.new(c - up * depth)
    for i in range(n):
        new.append(bm.faces.new((inner[i], inner[(i + 1) % n], center)))
    # Face out of the opening: up for the bag, down for the flap
    eye = c + up * (10.0 if depth > 0 else -10.0)
    for f in new:
        f.normal_update()
        if f.normal.dot(eye - f.calc_center_median()) < 0:
            f.normal_flip()
        for lp in f.loops:
            lp[uv_layer].uv = uv
    return new


def build():
    src = bpy.data.objects["SM_Backpack"]
    old = bpy.data.objects.get("SM_BackpackOpen")
    if old:
        bpy.data.objects.remove(old)
    ob = src.copy()
    ob.data = src.data.copy()
    ob.data.name = ob.name = "SM_BackpackOpen"
    bpy.context.scene.collection.objects.link(ob)

    bm = bmesh.new()
    bm.from_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, CUT_Z),
                           plane_no=(0, 0, 1))
    # Split the top from the bottom along the cut
    cut_edges = [e for e in bm.edges
                 if all(abs(v.co.z - CUT_Z) < 1e-3 for v in e.verts)]
    bmesh.ops.split_edges(bm, edges=cut_edges)
    top = [f for f in bm.faces
           if f.calc_center_median().z > CUT_Z]
    bottom = [f for f in bm.faces if f not in set(top)]
    top_verts = {v for f in top for v in f.verts}

    up = Vector((0, 0, 1))
    loops_b = [lp for lp in boundary_loops(bm, bottom)
               if all(abs(v.co.z - CUT_Z) < 1e-3 for v in lp)]
    loops_t = [lp for lp in boundary_loops(bm, top)
               if all(abs(v.co.z - CUT_Z) < 1e-3 for v in lp)]
    main_b = max(loops_b, key=len)
    main_t = max(loops_t, key=len)
    hinge_y = max(v.co.y for v in main_b)
    top_new = cap(bm, main_t, -INNER * 0.5, uv, up, LINING_UV)
    cap(bm, main_b, INNER, uv, up, DARK_UV)
    top_verts |= {v for f in top_new for v in f.verts}

    # Slivers, the shoulder straps behind the back and their side buckles
    parts = islands(bm)
    body = max(parts, key=len)
    back = max(v.co.y for v in body)
    side = max(abs(v.co.x) for v in body)
    junk = [v for p in parts
            if len(p) < SLIVER or (max(v.co.y for v in p) > back + 3 and
                                   max(v.co.z for v in p) < CUT_Z) or
            min(abs(v.co.x) for v in p) > side
            for v in p]
    bmesh.ops.delete(bm, geom=junk, context='VERTS')
    top_verts = {v for v in top_verts if v.is_valid}

    # Swing the flap back on the hinge at the back top edge
    hinge = Vector((0, hinge_y, CUT_Z))
    rot = (Matrix.Translation(hinge) @
           Matrix.Rotation(math.radians(-FLAP_DEG), 4, 'X') @
           Matrix.Translation(-hinge))
    for v in top_verts:
        v.co = rot @ v.co
    bm.to_mesh(ob.data)
    bm.free()

    cob_src = bpy.data.objects["SM_CornCob"]
    cob = cob_src.copy()
    cob.data = cob_src.data.copy()
    bpy.context.scene.collection.objects.link(cob)
    cob.location = COB_POS
    cob.rotation_euler = COB_ROT
    cob.scale = (0.8, 0.8, 0.8)
    for o in bpy.data.objects:
        o.select_set(o in (ob, cob))
    bpy.context.view_layer.objects.active = ob
    with bpy.context.temp_override(active_object=ob,
                                   selected_editable_objects=[ob, cob]):
        bpy.ops.object.join()
    for m in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(m)
    ob.data.transform(Matrix.Scale(SCALE, 4))
    ob.data.update()

    for o in bpy.data.objects:
        o.select_set(o == ob)
    win = bpy.context.window_manager.windows[0]
    area = next((a for a in win.screen.areas if a.type == 'VIEW_3D'),
                win.screen.areas[0])
    region = next(r for r in area.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=win, area=area, region=region,
                                   active_object=ob, selected_objects=[ob]):
        bpy.ops.export_scene.fbx(
            filepath=os.path.join(ART, "Backpack", "SM_BackpackOpen.fbx"),
            use_selection=True, object_types={'MESH'}, global_scale=1.0,
            apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE',
            mesh_smooth_type='FACE', path_mode='STRIP', bake_anim=False)
    return {"dims": list(ob.dimensions), "faces": len(ob.data.polygons),
            "mats": [m.name for m in ob.data.materials],
            "hinge_y": hinge_y}
