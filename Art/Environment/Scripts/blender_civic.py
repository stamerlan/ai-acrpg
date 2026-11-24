"""Build the Civic with an opening trunk from the Kenney sedan.

Run in Blender (Blender MCP or the Python console). Reads
Art/Environment/Kenney/car-kit/sedan.glb and writes to Art/Environment/Civic:

* SM_CivicBody.fbx: the sedan without the trunk lid, with a dark trunk
  cavity (second material slot) and a box of shells inside.
* SM_CivicTrunkLid.fbx: the lid, 4 cm thick (underside in a lighter second
  material), with its pivot on the hinge (front edge of the deck) so it
  opens by pitching around its X axis.

Saves Art/Environment/Source/Civic.blend. Same FBX settings as
blender_kenney_to_fbx.py (scale 1, 1 m = 100 cm in UE). Blender +Y (the
rear) becomes UE -Y. Returns the hinge position in UE centimeters.
"""
import os

import bmesh
import bpy
from mathutils import Vector

R = r"C:\Users\vvovchenko\repo\acrpg\Art\Environment"
SRC = os.path.join(R, "Kenney", "car-kit", "sedan.glb")
OUT = os.path.join(R, "Civic")
# Deck faces: behind the rear window, facing up, above the fenders
DECK_Y = (0.74, 1.26)
DECK_MIN_Z = 0.7
HINGE = Vector((0.0, 0.75, 0.8))
# Inside the deck opening (x +-0.55); the top follows the deck slope
CAVITY = ((-0.545, 0.545), (0.76, 1.24), 0.42)


def ctx():
    win = bpy.context.window_manager.windows[0]
    area = next(a for a in win.screen.areas if a.type == "VIEW_3D") \
        if any(a.type == "VIEW_3D" for a in win.screen.areas) else None
    d = {"window": win, "screen": win.screen}
    if area:
        d["area"] = area
        d["region"] = next(r for r in area.regions if r.type == "WINDOW")
    return d


def mat(name, color):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = color
    return m


def box(bm, lo, hi, inward):
    """Adds a box, its top sloped like the deck when inward (then it is
    flipped to face inside and has no top)."""
    def top(y):
        return HINGE.z - 0.205 * (y - HINGE.y) - 0.005 if inward else hi[2]
    vs = [bm.verts.new((x, y, z if k == 0 else top(y)))
          for k, z in enumerate((lo[2], hi[2]))
          for y in (lo[1], hi[1]) for x in (lo[0], hi[0])]
    quads = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3),
             (0, 4, 6, 2), (1, 3, 7, 5)]
    faces = []
    for i, q in enumerate(quads):
        if inward and i == 1:
            continue
        f = bm.faces.new([vs[j] for j in q])
        if inward:
            f.normal_flip()
        faces.append(f)
    return faces


def build():
    bpy.ops.wm.read_homefile(use_empty=True)
    bpy.context.scene.unit_settings.scale_length = 1.0
    bpy.ops.import_scene.gltf(filepath=SRC)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    with bpy.context.temp_override(**ctx(), active_object=meshes[0],
                                   selected_objects=meshes,
                                   selected_editable_objects=meshes):
        bpy.ops.object.join()
    body = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
    body.parent = None
    with bpy.context.temp_override(**ctx(), active_object=body,
                                   selected_objects=[body],
                                   selected_editable_objects=[body]):
        bpy.ops.object.transform_apply(location=True, rotation=True,
                                       scale=True)
    for o in list(bpy.context.scene.objects):
        if o != body:
            bpy.data.objects.remove(o, do_unlink=True)
    body.name = "SM_CivicBody"
    body.data.materials.append(mat("M_TrunkInside", (0.03, 0.03, 0.03, 1)))
    body.data.materials.append(mat("M_ShellBox", (0.7, 0.12, 0.08, 1)))

    bm = bmesh.new()
    bm.from_mesh(body.data)
    lid_faces = [f for f in bm.faces
                 if DECK_Y[0] < f.calc_center_median().y < DECK_Y[1]
                 and f.calc_center_median().z > DECK_MIN_Z
                 and f.normal.z > 0.9]
    lid_bm = bmesh.new()
    vmap = {}
    for f in lid_faces:
        nv = []
        for v in f.verts:
            if v not in vmap:
                vmap[v] = lid_bm.verts.new(v.co - HINGE)
            nv.append(vmap[v])
        lid_bm.faces.new(nv)
    bmesh.ops.delete(bm, geom=lid_faces, context="FACES_ONLY")
    (x0, x1), (y0, y1), z0 = CAVITY
    for f in box(bm, (x0, y0, z0), (x1, y1, z0), True):
        f.material_index = 1
    for f in box(bm, (-0.22, 0.9, z0), (0.08, 1.08, z0 + 0.14), False):
        f.material_index = 2
    bm.to_mesh(body.data)
    bm.free()

    bmesh.ops.solidify(lid_bm, geom=lid_bm.faces[:], thickness=0.04)
    bmesh.ops.recalc_face_normals(lid_bm, faces=lid_bm.faces[:])
    for f in lid_bm.faces:
        f.material_index = 1 if f.normal.z < -0.5 else 0
    lid_me = bpy.data.meshes.new("SM_CivicTrunkLid")
    lid_bm.to_mesh(lid_me)
    lid_bm.free()
    for m in body.data.materials[:1]:
        lid_me.materials.append(m)
    lid_me.materials.append(mat("M_LidInside", (0.25, 0.24, 0.22, 1)))
    lid = bpy.data.objects.new("SM_CivicTrunkLid", lid_me)
    bpy.context.scene.collection.objects.link(lid)

    os.makedirs(OUT, exist_ok=True)
    for ob in (body, lid):
        for o in bpy.context.scene.objects:
            o.select_set(o == ob)
        with bpy.context.temp_override(**ctx()):
            bpy.ops.export_scene.fbx(
                filepath=os.path.join(OUT, ob.name + ".fbx"),
                use_selection=True, object_types={"MESH"},
                global_scale=1.0, apply_unit_scale=True,
                apply_scale_options="FBX_SCALE_NONE",
                mesh_smooth_type="FACE", path_mode="STRIP", bake_anim=False)
    lid.location = HINGE
    bpy.ops.wm.save_as_mainfile(
        filepath=os.path.join(R, "Source", "Civic.blend"))
    return {"lid_faces": len(lid_faces),
            "hinge_ue_cm": [HINGE.x * 100, -HINGE.y * 100, HINGE.z * 100]}


result = build()
