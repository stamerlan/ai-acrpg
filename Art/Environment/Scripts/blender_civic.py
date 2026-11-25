"""Build the Civic with an opening hatch from the Meshy hatchback.

blender --background --python blender_civic.py

Reads Art/Trailer/Models/civic.glb (through blender_meshy_to_fbx.load)
and writes to Art/Environment/Civic:

* SM_CivicBody.fbx: the car without the hatch, with a dark trunk cavity
  (second material slot) and a box of shells inside (third slot).
* SM_CivicTrunkLid.fbx: the hatch (rear window and tailgate), 3 cm thick
  (inside in a lighter second material), with its pivot on the hinge at
  the roof edge, so it opens by pitching around its X axis.
* T_Civic_D.png: the car's texture.

Saves Art/Environment/Source/Civic.blend. Blender +Y (the rear) becomes
UE -Y. Prints the hinge position in UE centimeters.
"""
import os
import sys

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(HERE)
import blender_meshy_to_fbx as meshy  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "Civic")
HEIGHT = 1.42
# The hatch: faces behind the roof edge, above the bumper, between the
# rear pillars, that look up or back.
HATCH_Y = 1.18
HATCH_Z = 0.82
HATCH_X = 0.74
HINGE = Vector((0.0, 1.2, 1.33))
# How fast the hatch falls toward the tail (m per m).
SLOPE = 0.42
# The trunk cavity under the hatch: (x, y) ranges and the floor height.
CAVITY = ((-0.5, 0.5), (1.25, 1.98), 0.5)


def mat(name, color):
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    return material


def box(mesh, low, high, inward, index):
    """Adds a box. Inward ones face inside, have no top, and their walls
    end under the sloping hatch."""
    def top(y):
        return HINGE.z - SLOPE * (y - HINGE.y) - 0.09 if inward else high[2]
    corners = [mesh.verts.new((x, y, z if level == 0 else top(y)))
               for level, z in enumerate((low[2], high[2]))
               for y in (low[1], high[1]) for x in (low[0], high[0])]
    quads = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3),
             (0, 4, 6, 2), (1, 3, 7, 5)]
    for number, quad in enumerate(quads):
        if inward and number == 1:
            continue
        face = mesh.faces.new([corners[i] for i in quad])
        face.material_index = index
        if inward:
            face.normal_flip()


def build():
    body, image = meshy.load("civic", HEIGHT, True)
    body.material_slots[0].material.name = "M_Civic"
    body.data.materials.append(mat("M_TrunkInside", (0.03, 0.03, 0.03, 1)))
    body.data.materials.append(mat("M_ShellBox", (0.7, 0.12, 0.08, 1)))

    mesh = bmesh.new()
    mesh.from_mesh(body.data)
    # Straight cuts along the hatch outline, so its edge is not a
    # sawtooth of triangles.
    for point, normal in (((0, HATCH_Y, 0), (0, 1, 0)),
                          ((0, 0, HATCH_Z), (0, 0, 1)),
                          ((HATCH_X, 0, 0), (1, 0, 0)),
                          ((-HATCH_X, 0, 0), (1, 0, 0))):
        bmesh.ops.bisect_plane(
            mesh, geom=mesh.verts[:] + mesh.edges[:] + mesh.faces[:],
            plane_co=point, plane_no=normal)
    layer = mesh.loops.layers.uv.active
    hatch = []
    for face in mesh.faces:
        middle = face.calc_center_median()
        if (middle.y > HATCH_Y and middle.z > HATCH_Z
                and abs(middle.x) < HATCH_X
                and face.normal.dot((0, 0.5, 0.86)) > 0.35):
            hatch.append(face)
    lid = bmesh.new()
    lid_layer = lid.loops.layers.uv.new("UVMap")
    twins = {}
    for face in hatch:
        corners = []
        for vertex in face.verts:
            if vertex not in twins:
                twins[vertex] = lid.verts.new(vertex.co - HINGE)
            corners.append(twins[vertex])
        copy = lid.faces.new(corners)
        for source, target in zip(face.loops, copy.loops):
            target[lid_layer].uv = source[layer].uv
    bmesh.ops.delete(mesh, geom=hatch, context="FACES")
    (x0, x1), (y0, y1), floor = CAVITY
    box(mesh, (x0, y0, floor), (x1, y1, HINGE.z - 0.02), True, 1)
    box(mesh, (-0.3, 1.5, floor), (0.02, 1.7, floor + 0.14), False, 2)
    mesh.to_mesh(body.data)
    mesh.free()

    outside = lid.faces[:]
    made = bmesh.ops.solidify(lid, geom=outside, thickness=0.03)
    for face in lid.faces:
        if face not in outside:
            face.material_index = 1
    lid_data = bpy.data.meshes.new("SM_CivicTrunkLid")
    lid.to_mesh(lid_data)
    lid.free()
    lid_data.materials.append(body.data.materials[0])
    lid_data.materials.append(mat("M_LidInside", (0.25, 0.24, 0.22, 1)))
    lid_obj = bpy.data.objects.new("SM_CivicTrunkLid", lid_data)
    bpy.context.scene.collection.objects.link(lid_obj)

    os.makedirs(OUT, exist_ok=True)
    meshy.OUT = OUT
    meshy.export(body, "SM_CivicBody")
    meshy.export(lid_obj, "SM_CivicTrunkLid")
    meshy.save_texture(image, "T_Civic_D")
    lid_obj.location = HINGE
    bpy.context.scene.unit_settings.scale_length = 1.0
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(
        os.path.dirname(HERE), "Source", "Civic.blend"))
    print("CIVIC body", [round(v, 2) for v in body.dimensions],
          "hatch faces", len(hatch), "hinge UE cm",
          [HINGE.x * 100, -HINGE.y * 100, HINGE.z * 100])


if __name__ == "__main__":
    build()
