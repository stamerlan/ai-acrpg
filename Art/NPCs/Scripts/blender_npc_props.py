"""NPC hand props from primitives, to Art/NPCs/Props/SM_<Name>.fbx (cm).

Run headless from the repo root:
  blender --background --python Art/NPCs/Scripts/blender_npc_props.py

Every prop has +Z up and +X to the front, with the origin in the grip, so
ue_dress_npcs.py can stand it upright in a hand (BP_NPC HandProp):

  SM_Thermos    Kolya's green thermos, 27 cm
  SM_Stamp      Zbyszek's and Halina's rubber stamp, 17 cm (oversized, so
                it reads from the game camera)
  SM_TongsCorn  the corn lady's tongs holding a grilled cob, 30 cm
  SM_GnomeSign  Krasnal's cardboard sign on a stick: GNOMES 2 FOR 1!
"""
import bmesh
import bpy
import math
import os
from mathutils import Matrix, Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "NPCs", "Props")
COLORS = {
    "M_Thermos_Green": ((0.05, 0.32, 0.12), 0.45),
    "M_Thermos_Steel": ((0.55, 0.56, 0.57), 0.3),
    "M_NPCProp_Wood": ((0.42, 0.27, 0.13), 0.7),
    "M_NPCProp_DarkWood": ((0.2, 0.12, 0.06), 0.6),
    "M_NPCProp_RedRubber": ((0.7, 0.05, 0.05), 0.5),
    "M_NPCProp_Steel": ((0.6, 0.61, 0.62), 0.3),
    "M_NPCProp_Corn": ((0.95, 0.68, 0.1), 0.55),
    "M_NPCProp_Char": ((0.3, 0.17, 0.05), 0.7),
    "M_NPCProp_Cardboard": ((0.66, 0.5, 0.3), 0.85),
    "M_NPCProp_Ink": ((0.1, 0.05, 0.03), 0.8),
}


def material(name):
    m = bpy.data.materials.get(name)
    if m:
        return m
    rgb, rough = COLORS[name]
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1)
    p.inputs["Roughness"].default_value = rough
    return m


class Prop:
    """One mesh built part by part; each part takes a material."""

    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.mats = []

    def _add(self, make, mat, smooth):
        if mat not in self.mats:
            self.mats.append(mat)
        for f in {f for v in make()["verts"] for f in v.link_faces}:
            f.material_index = self.mats.index(mat)
            f.smooth = smooth

    def box(self, size, at, mat, rot=None):
        m = Matrix.Translation(at) @ (rot or Matrix()) @ Matrix.Diagonal(
            (*size, 1))
        self._add(lambda: bmesh.ops.create_cube(self.bm, size=1.0, matrix=m),
                  mat, False)

    def cylinder(self, r, depth, at, mat, rot=None, r2=None):
        m = Matrix.Translation(at) @ (rot or Matrix())
        self._add(lambda: bmesh.ops.create_cone(
            self.bm, cap_ends=True, segments=20, radius1=r,
            radius2=r if r2 is None else r2, depth=depth, matrix=m),
            mat, True)

    def sphere(self, r, at, mat, scale=(1, 1, 1)):
        m = Matrix.Translation(at) @ Matrix.Diagonal((*scale, 1))
        self._add(lambda: bmesh.ops.create_uvsphere(
            self.bm, u_segments=16, v_segments=10, radius=r, matrix=m),
            mat, True)

    def text(self, body, size, at, mat, depth=0.25):
        """Extruded text on the plane facing +X, centered on `at`."""
        cu = bpy.data.curves.new(self.name + "_Text", 'FONT')
        cu.body = body
        cu.size = size
        cu.align_x = 'CENTER'
        cu.align_y = 'CENTER'
        cu.extrude = depth
        cu.offset = 0.02 * size
        ob = bpy.data.objects.new(self.name + "_Text", cu)
        bpy.context.scene.collection.objects.link(ob)
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        # Text plane XY to YZ: readable from +X with +Z up
        me.transform(Matrix.Translation(at) @
                     Matrix.Rotation(math.radians(90), 4, 'Z') @
                     Matrix.Rotation(math.radians(90), 4, 'X'))
        if mat not in self.mats:
            self.mats.append(mat)
        n = len(self.bm.faces)
        self.bm.from_mesh(me)
        self.bm.faces.ensure_lookup_table()
        for f in self.bm.faces[n:]:
            f.material_index = self.mats.index(mat)
            f.smooth = False
        bpy.data.objects.remove(ob)

    def build(self):
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(material(m))
        ob = bpy.data.objects.new(self.name, me)
        bpy.context.scene.collection.objects.link(ob)
        return ob


def thermos():
    p = Prop("SM_Thermos")
    p.cylinder(4.6, 20.0, (0, 0, 0), "M_Thermos_Green")
    p.cylinder(4.7, 1.2, (0, 0, -10.0), "M_Thermos_Steel")
    p.cylinder(4.7, 1.0, (0, 0, 10.2), "M_Thermos_Steel")
    p.cylinder(4.2, 6.0, (0, 0, 13.6), "M_Thermos_Steel")
    return p.build()


def stamp():
    p = Prop("SM_Stamp")
    p.cylinder(2.0, 9.0, (0, 0, 2.5), "M_NPCProp_Wood")
    p.sphere(3.0, (0, 0, 8.5), "M_NPCProp_Wood")
    p.box((6.0, 9.0, 3.0), (0, 0, -3.5), "M_NPCProp_DarkWood")
    p.box((6.4, 9.4, 0.8), (0, 0, -5.4), "M_NPCProp_RedRubber")
    return p.build()


def tongs_corn():
    p = Prop("SM_TongsCorn")
    for sign in (1, -1):
        rot = Matrix.Rotation(math.radians(-5 * sign), 4, 'Y')
        p.box((30.0, 1.4, 0.35), (11.0, 0, 1.3 * sign), "M_NPCProp_Steel",
              rot)
    p.box((1.0, 1.6, 3.2), (-4.2, 0, 0), "M_NPCProp_Steel")
    side = Matrix.Rotation(math.radians(90), 4, 'X')
    p.cylinder(2.7, 13.0, (25.5, 0, 0), "M_NPCProp_Corn", side)
    for y in (-6.5, 6.5):
        p.sphere(2.7, (25.5, y, 0), "M_NPCProp_Corn", (1, 0.9, 1))
    for y in (-3.5, 0.5, 4.0):
        p.cylinder(2.78, 0.9, (25.5, y, 0), "M_NPCProp_Char", side)
    return p.build()


def gnome_sign():
    p = Prop("SM_GnomeSign")
    # The board is off the stick, to the holder's right (-Y here, +Y in
    # UE), and above his shoulder: it must not cover him
    p.box((2.2, 2.2, 92.0), (0, 0, 31.0), "M_NPCProp_Wood")
    p.box((1.0, 50.0, 31.0), (1.6, -12.0, 60.0), "M_NPCProp_Cardboard")
    p.text("GNOMES\n2 FOR 1!", 9.5, Vector((2.2, -12.0, 60.0)),
           "M_NPCProp_Ink")
    return p.build()


def export(o, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for x in bpy.data.objects:
        x.select_set(x is o)
    bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, object_types={'MESH'},
        apply_unit_scale=True, global_scale=1.0,
        apply_scale_options='FBX_SCALE_ALL', mesh_smooth_type='FACE',
        path_mode='STRIP')


def preview(path, objs):
    """All props side by side from the front (+X), for a look."""
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'
    sc.display.shading.color_type = 'MATERIAL'
    sc.render.resolution_x = 1200
    sc.render.resolution_y = 500
    for i, o in enumerate(objs):
        o.location.y = (i - (len(objs) - 1) / 2) * 60
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    sc.collection.objects.link(cam)
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 260
    cam.data.clip_end = 5000
    c = Vector((0, 0, 25))
    cam.location = c + Vector((1.0, 0.35, 0.35)).normalized() * 600
    cam.rotation_euler = (c - cam.location).to_track_quat(
        '-Z', 'Y').to_euler()
    sc.camera = cam
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for o in objs:
        o.location.y = 0
    bpy.data.objects.remove(cam)


if __name__ == "__main__":
    import sys
    bpy.ops.wm.read_homefile(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 0.01
    props = [thermos(), stamp(), tongs_corn(), gnome_sign()]
    for o in props:
        export(o, os.path.join(OUT, o.name + ".fbx"))
    if "--" in sys.argv and len(sys.argv) > sys.argv.index("--") + 1:
        preview(sys.argv[sys.argv.index("--") + 1], props)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "NPCProps.blend"))
