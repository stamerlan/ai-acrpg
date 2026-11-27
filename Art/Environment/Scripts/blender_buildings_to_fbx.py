"""Meshy buildings and the border officer: GLB -> FBX for UE.

blender --background --python blender_buildings_to_fbx.py
    [-- preview_dir [name ...]]

Reads Art/Environment/Buildings/Meshy/<name>.glb (Meshy image to 3D,
meshy-7.1 remeshed to 20-30k triangles) and writes
Art/Environment/Buildings/SM_<Name>.fbx with T_<Name>_D.png: meters, Z
up, standing on z = 0, centered. A stall is cut in two at the lower edge
of its canopy: SM_<Name>_Top.fbx is the tarp, which the game hides whole
when it covers her, SM_<Name>.fbx the frame, tables and goods under it.
Meshy leaves a model turned the way its concept image was drawn, so each
one is first squared to the axes (the turn with the smallest bounding
box) and then turned by a quarter-turn count picked by eye so that its
front faces -Y, like the vehicles of blender_meshy_to_fbx.py. With a
preview_dir, renders each result from the front (-Y) and from above to
check that; with names after it, converts only those models.
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
SRC = os.path.join(ART, "Buildings", "Meshy")
OUT = os.path.join(ART, "Buildings")
# name: (asset name, size in meters, measured along, quarter turns)
# "z" is the height, "xy" the longer side of the footprint
MODELS = {
    "officer": ("Officer", 1.78, "z", 0),
    "seller": ("Seller", 1.75, "z", 0),
    "booth": ("Booth", 2.6, "z", 0),
    "vetoffice": ("VetOffice", 4.0, "xy", 0),
    "zigaretten": ("Zigaretten", 6.0, "xy", 0),
    "kantor": ("Kantor", 4.4, "xy", 0),
    "friseur": ("Friseur", 5.2, "xy", 0),
    "sklep": ("Sklep", 6.0, "xy", 0),
    "bar": ("Bar", 5.0, "xy", 0),
    "pavilion": ("Pavilion", 10.0, "xy", 0),
    "toilet": ("Toilet", 3.2, "xy", 0),
    # Open market stalls of the main street, one per trade
    "stall_fruit": ("Stall_Fruit", 4.0, "xy", 0),
    "stall_tools": ("Stall_Tools", 4.0, "xy", 0),
    "stall_bags": ("Stall_Bags", 4.0, "xy", 0),
    "stall_cds": ("Stall_CDs", 4.0, "xy", 0),
    "stall_toys": ("Stall_Toys", 4.0, "xy", 0),
    "stall_household": ("Stall_Household", 4.0, "xy", 0),
    "stall_gnomes": ("Stall_Gnomes", 4.0, "xy", 0),
    "stall_flowers": ("Stall_Flowers", 4.0, "xy", 0),
    "stall_shoes": ("Stall_Shoes", 4.0, "xy", 0),
    "stall_tracksuits": ("Stall_Tracksuits", 4.0, "xy", 0),
    "stall_zbyszek": ("Stall_Zbyszek", 4.0, "xy", 0),
    "stall_honey": ("Stall_Honey", 4.0, "xy", 0),
    "stall_carparts": ("Stall_CarParts", 4.0, "xy", 0),
    "stall_cornlady": ("Stall_CornLady", 4.0, "xy", 0),
    "stall_socks": ("Stall_Socks", 4.0, "xy", 0),
    "stall_kebab": ("Stall_Kebab", 7.0, "xy", 0),
}
# Where a stall is cut, as a part of its height: just under the canopy
CUT = {"stall_cds": 0.68, "stall_kebab": 0.68, "stall_gnomes": 0.64,
       "stall_cornlady": 0.62, "stall_fruit": 0.62, "stall_honey": 0.62,
       "stall_household": 0.62}


def footprint(points, angle):
    c, s = math.cos(angle), math.sin(angle)
    xs = [p.x * c - p.y * s for p in points]
    ys = [p.x * s + p.y * c for p in points]
    return (max(xs) - min(xs)) * (max(ys) - min(ys))


def load(name, size, along, turns):
    """The model as one mesh object, squared, sized, on the ground."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(SRC, name + ".glb"))
    obj = next(o for o in bpy.context.scene.objects if o.type == "MESH")
    world = obj.matrix_world.copy()
    obj.parent = None
    obj.data.transform(world)
    obj.matrix_world = Matrix()
    points = [v.co for v in obj.data.vertices][::7]
    square = 0.0
    if name not in ("officer", "seller"):
        square = min((math.radians(d * 0.5) for d in range(-90, 90)),
                     key=lambda a: footprint(points, a))
    obj.data.transform(Matrix.Rotation(
        square + turns * math.pi / 2, 4, "Z"))
    points = [v.co for v in obj.data.vertices]
    low = Vector((min(p.x for p in points), min(p.y for p in points),
                  min(p.z for p in points)))
    high = Vector((max(p.x for p in points), max(p.y for p in points),
                   max(p.z for p in points)))
    span = high - low
    scale = size / (span.z if along == "z" else max(span.x, span.y))
    middle = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, low.z))
    obj.data.transform(Matrix.Scale(scale, 4) @ Matrix.Translation(-middle))
    if name.startswith("stall_"):
        # Cloth and goods: flat faces shade a tarp into blotches
        for poly in obj.data.polygons:
            poly.use_smooth = True
        obj.data.set_sharp_from_angle(angle=math.radians(40))
    for other in list(bpy.context.scene.objects):
        if other != obj:
            bpy.data.objects.remove(other)
    image = next(node.image
                 for node in obj.material_slots[0].material.node_tree.nodes
                 if node.type == "TEX_IMAGE" and node.image)
    return obj, image


def split_top(obj, z):
    """Cuts the mesh at a height; returns what is above as a new object."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.bisect_plane(
        bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
        plane_co=(0, 0, z), plane_no=(0, 0, 1))
    bm.to_mesh(obj.data)
    bm.free()
    top = obj.copy()
    top.data = obj.data.copy()
    bpy.context.scene.collection.objects.link(top)
    for part, above in ((obj, True), (top, False)):
        bm = bmesh.new()
        bm.from_mesh(part.data)
        bmesh.ops.delete(
            bm, geom=[f for f in bm.faces
                      if (f.calc_center_median().z > z) == above],
            context="FACES")
        bm.to_mesh(part.data)
        bm.free()
    return top


def export(obj, name):
    for other in bpy.context.scene.objects:
        other.select_set(other == obj)
    obj.name = obj.data.name = name
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(OUT, name + ".fbx"), use_selection=True,
        object_types={"MESH"}, global_scale=1.0, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_NONE", mesh_smooth_type="FACE",
        path_mode="STRIP", bake_anim=False)


def preview(obj, folder, name):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "FLAT"
    scene.display.shading.color_type = "TEXTURE"
    scene.render.resolution_x = scene.render.resolution_y = 400
    data = bpy.data.cameras.new("Cam")
    data.type = "ORTHO"
    data.ortho_scale = max(obj.dimensions) * 1.2
    cam = bpy.data.objects.new("Cam", data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    mid = obj.dimensions.z / 2
    for tag, loc, rot in (("front", (0, -30, mid), (math.pi / 2, 0, 0)),
                          ("top", (0, 0, 30), (0, 0, 0))):
        cam.location = loc
        cam.rotation_euler = rot
        scene.render.filepath = os.path.join(folder, name + "_" + tag)
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    for name, (title, size, along, turns) in MODELS.items():
        if args[1:] and name not in args[1:]:
            continue
        obj, image = load(name, size, along, turns)
        obj.material_slots[0].material.name = "M_" + title
        if name.startswith("stall_"):
            height = max(v.co.z for v in obj.data.vertices)
            top = split_top(obj, CUT.get(name, 0.59) * height)
            export(top, "SM_" + title + "_Top")
        export(obj, "SM_" + title)
        image.filepath_raw = os.path.join(OUT, "T_" + title + "_D.png")
        image.file_format = "PNG"
        image.save()
        print("MODEL", title, [round(v, 2) for v in obj.dimensions],
              len(obj.data.polygons), image.size[:])
        if args:
            preview(obj, args[0], title)
