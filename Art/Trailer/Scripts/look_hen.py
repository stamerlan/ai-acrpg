"""Close neutral views of the hen: glasses fit and the shotgun hold
(test renders only)."""
import math
import os
import sys

import bpy

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import trailer_lib as lib

scene = lib.new_scene(6, glare=0.0)
scene.render.use_motion_blur = False
lib.sky((0.5, 0.5, 0.5), (0.6, 0.65, 0.7), strength=1.0)
lib.light("SUN", (-3, -6, 6), 3.0, aim=(0, 0, 0.4), size=0.2)
hen, parts = lib.append(
    lib.CHICKEN, ["Armature", "SK_Chicken", "SK_Chicken_Glasses"],
    ["A_Chicken_ShotgunAim"])
lib.play(parts["Armature"], "A_Chicken_ShotgunAim", repeat=4.0)
shades = bpy.data.materials["M_Sunglasses"]
shades.node_tree.nodes["Principled BSDF"].inputs[
    "Base Color"].default_value = (0.1, 0.3, 1.0, 1)
if "gun" in sys.argv:
    _, gun = lib.append(lib.PROPS, ["SM_Shotgun"])
    grip = lib.empty("Grip", location=(0.2, -0.33, 0.3))
    gun["SM_Shotgun"].parent.parent = grip
    gun["SM_Shotgun"].parent.rotation_euler = (0, 0, -math.pi / 2)
cam = lib.camera(lens=85.0)
head = (0, -0.1, 0.52)
lib.key(cam, 1, location=(0, -1.6, 0.55), aim=head)
lib.key(cam, 2, location=(1.6, -0.1, 0.55), aim=head)
lib.key(cam, 3, location=(1.0, -1.2, 0.8), aim=head)
lib.key(cam, 4, location=(0.0, -0.3, 2.0), aim=(0, -0.29, 0.5))
lib.key(cam, 5, location=(2.6, -0.2, 0.4), aim=(0, -0.2, 0.32))
lib.key(cam, 6, location=(1.6, -2.0, 1.2), aim=(0, -0.2, 0.32))
lib.render("hen")
