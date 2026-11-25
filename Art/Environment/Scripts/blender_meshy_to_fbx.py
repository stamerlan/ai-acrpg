"""Meshy GLB -> FBX for UE: real size, meters, Z up, standing on z = 0.

blender --background --python blender_meshy_to_fbx.py

Reads Art/Trailer/Models/<name>.glb (made for the trailer, see
Art/Trailer/README.md) and writes Art/Environment/Meshy/SM_<Name>.fbx
with its texture T_<Name>_D.png (scale 1, so 1 m = 100 cm in UE, like
blender_kenney_to_fbx.py). Vehicles get their long axis on Y with the
front toward -Y, like the Kenney cars. The Civic is cut into a body and
a hatch by blender_civic.py.
"""
import math
import os

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ART, "Trailer", "Models")
OUT = os.path.join(ART, "Environment", "Meshy")
# name: (height in meters, is a vehicle)
MODELS = {
    "civic": (1.42, True), "sedan": (1.4, True), "suv": (1.8, True),
    "van": (2.0, True),
    "truck": (2.9, True), "pine": (13.0, False), "spruce": (11.0, False),
    "birch": (9.0, False), "oak": (9.0, False), "bush": (1.5, False),
    "fern": (0.7, False)}


def load(name, height, vehicle):
    """The model as one mesh object at real size, its texture image."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(SRC, name + ".glb"))
    obj = next(o for o in bpy.context.scene.objects if o.type == "MESH")
    world = obj.matrix_world.copy()
    obj.parent = None
    if vehicle:
        world = Matrix.Rotation(math.pi / 2, 4, "Z") @ world
    obj.data.transform(world)
    obj.matrix_world = Matrix()
    points = [vertex.co for vertex in obj.data.vertices]
    low = min(point.z for point in points)
    size = height / (max(point.z for point in points) - low)
    middle = Vector((
        (min(p.x for p in points) + max(p.x for p in points)) / 2,
        (min(p.y for p in points) + max(p.y for p in points)) / 2, low))
    obj.data.transform(Matrix.Scale(size, 4) @ Matrix.Translation(-middle))
    for other in list(bpy.context.scene.objects):
        if other != obj:
            bpy.data.objects.remove(other)
    image = next(node.image
                 for node in obj.material_slots[0].material.node_tree.nodes
                 if node.type == "TEX_IMAGE" and node.image)
    return obj, image


def export(obj, name):
    for other in bpy.context.scene.objects:
        other.select_set(other == obj)
    obj.name = obj.data.name = name
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(OUT, name + ".fbx"), use_selection=True,
        object_types={"MESH"}, global_scale=1.0, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_NONE", mesh_smooth_type="FACE",
        path_mode="STRIP", bake_anim=False)


def save_texture(image, name):
    image.filepath_raw = os.path.join(OUT, name + ".png")
    image.file_format = "PNG"
    image.save()


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, (height, vehicle) in MODELS.items():
        obj, image = load(name, height, vehicle)
        title = name.capitalize()
        obj.material_slots[0].material.name = "M_" + title
        export(obj, "SM_" + title)
        save_texture(image, "T_" + title + "_D")
        print("MODEL", title, [round(v, 2) for v in obj.dimensions],
              len(obj.data.polygons), image.size[:])
