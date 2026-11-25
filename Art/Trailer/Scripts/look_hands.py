"""The cook's hand bones with their local axes drawn as rods: X red,
Y green, Z blue (test renders only).

blender --background --python look_hands.py -- hands still 1 2 3 4
"""
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import trailer_lib as lib

scene = lib.new_scene(4, glare=0.0)
scene.render.use_motion_blur = False
lib.sky((0.5, 0.5, 0.5), (0.6, 0.65, 0.7), strength=1.0)
lib.light("SUN", (-3, -6, 6), 3.0, aim=(0, 0, 1.2), size=0.2)
root, parts = lib.append(lib.SHAWARMAN, ["Armature", "SK_Shawarman"])
rig = parts["Armature"]
colors = {"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}
for bone in ("RightHand", "LeftHand"):
    length = rig.data.bones[bone].length
    print("BONE", bone, length)
    for axis, color in colors.items():
        size = [0.6, 0.6, 0.6]
        index = "XYZ".index(axis)
        size[index] = 14.0
        offset = [0.0, 0.0, 0.0]
        offset[index] = 7.0
        rod = lib.box("Rod" + axis, size, (0, 0, 0),
                      lib.mat("Rod" + bone + axis, (0, 0, 0), emit=color,
                              power=2.0))
        rod.parent = rig
        rod.parent_type = "BONE"
        rod.parent_bone = bone
        rod.matrix_parent_inverse = Matrix.Translation((0, -length, 0))
        rod.matrix_basis = Matrix.Translation(offset)
        rod.scale = size
bpy.context.view_layer.update()
cam = lib.camera(lens=85.0)
for frame, bone, offset in ((1, "RightHand", (-0.2, -1.6, 0.2)),
                            (2, "RightHand", (-1.6, 0.0, 0.2)),
                            (3, "LeftHand", (0.2, -1.6, 0.2)),
                            (4, "LeftHand", (1.6, 0.0, 0.2))):
    hand = rig.matrix_world @ rig.pose.bones[bone].head
    lib.key(cam, frame, location=hand + Vector(offset), aim=hand)
lib.render("hands")
