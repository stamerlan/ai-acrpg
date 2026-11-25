"""Close neutral views of the cook's hands and props (test renders).

blender --background --python look_knife.py -- knife still 20 60 110
"""
import os
import sys

import bpy
from mathutils import Vector

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import trailer_lib as lib
import shots_props

scene = lib.new_scene(120, glare=0.0)
scene.render.use_motion_blur = False
lib.sky((0.5, 0.5, 0.5), (0.6, 0.65, 0.7), strength=1.0)
lib.light("SUN", (-3, -6, 6), 3.0, aim=(0, 0, 1.2), size=0.2)
root, parts = lib.append(lib.SHAWARMAN, ["Armature", "SK_Shawarman"],
                         ["A_Shawarman_Idle", "A_Shawarman_Search"])
rig = parts["Armature"]
lib.play(rig, "A_Shawarman_Idle", scale=1.0)

shots_props.arm_cook(rig, parts["SK_Shawarman"])
cam = lib.camera(lens=85.0)
for frame in (2, 30, 50):
    scene.frame_set(frame)
    hands = [rig.matrix_world @ rig.pose.bones[name].head
             for name in ("RightHand", "LeftHand")]
    middle = (hands[0] + hands[1]) / 2
    lib.key(cam, frame, location=middle + Vector((0.5, -2.2, 0.3)),
            aim=middle)
lib.render("knife")
