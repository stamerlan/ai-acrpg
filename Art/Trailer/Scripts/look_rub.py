"""Measures the gap between the cook's palms over the idle clip, and
renders close views of his hands (test renders only).

blender --background --python look_rub.py -- rub still 10 40 70 [fix]
"""
import os
import sys

import bpy
from mathutils import Vector

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import trailer_lib as lib
import shots_props

scene = lib.new_scene(100, glare=0.0)
scene.render.use_motion_blur = False
lib.sky((0.5, 0.5, 0.5), (0.6, 0.65, 0.7), strength=1.0)
lib.light("SUN", (-3, -6, 6), 3.0, aim=(0, 0, 1.2), size=0.2)
root, parts = lib.append(lib.SHAWARMAN, ["Armature", "SK_Shawarman"],
                         ["A_Shawarman_Idle"])
rig = parts["Armature"]
print("BONES", [bone.name for bone in rig.data.bones])
lib.play(rig, "A_Shawarman_Idle", scale=1.0)
if "fix" in sys.argv:
    shots_props.rub_hands(rig, parts["SK_Shawarman"], 100)
centers = {bone: shots_props.grip(rig, parts["SK_Shawarman"], bone)
           for bone in ("RightHand", "LeftHand")}
gaps = []
for frame in range(1, 101, 3):
    scene.frame_set(frame)
    spots = [rig.pose.bones[bone].matrix @ centers[bone][0]
             for bone in centers]
    gaps.append(round((spots[0] - spots[1]).length, 1))
print("GAPS", gaps)
cam = lib.camera(lens=85.0)
for frame in (10, 40, 70):
    scene.frame_set(frame)
    hands = [rig.matrix_world @ rig.pose.bones[name].head
             for name in ("RightHand", "LeftHand")]
    middle = (hands[0] + hands[1]) / 2
    lib.key(cam, frame, location=middle + Vector((-0.5, -1.9, -0.4)),
            aim=middle)
lib.render("rub")
