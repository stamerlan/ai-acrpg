"""Neutral-light look at the trailer's assets (test renders only).

blender --background --python look_assets.py -- look still 1 2 3
"""
import os
import sys

import bpy

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import trailer_lib as lib

scene = lib.new_scene(3, glare=0.0)
scene.render.use_motion_blur = False
lib.sky((0.5, 0.5, 0.5), (0.6, 0.65, 0.7), strength=1.0)
lib.box("Floor", (40, 40, 0.1), (0, 0, -0.05),
        lib.mat("Floor", (0.3, 0.3, 0.3)))
lib.light("SUN", (5, -5, 8), 3.0, aim=(0, 0, 0), size=0.1)
car, parts = lib.append(lib.CIVIC, ["SM_CivicBody", "SM_CivicTrunkLid"])
hen, hen_parts = lib.append(
    lib.CHICKEN, ["Armature", "SK_Chicken", "SK_Chicken_Glasses"],
    ["A_Chicken_Idle", "A_Chicken_ShotgunAim"])
hen.location = (2.0, 0, 0)
lib.play(hen_parts["Armature"], "A_Chicken_Idle")
cook, cook_parts = lib.append(
    lib.SHAWARMAN, ["Armature", "SK_Shawarman"], ["A_Shawarman_Idle"])
cook.location = (3.5, 0, 0)
lib.play(cook_parts["Armature"], "A_Shawarman_Idle")
truck = lib.glb("car-kit/truck.glb", height=3.2, location=(-4.5, 0, 0))
tent = lib.glb("survival-kit/tent-canvas.glb", height=1.2,
               location=(6, 0, 0))
lib.paint_civic(parts["SM_CivicBody"], (0.012, 0.012, 0.016))
print("MATS", [m.name for m in bpy.data.materials])
cam = lib.camera(lens=35.0)
lib.key(cam, 1, location=(1.0, -11.0, 2.2), aim=(1.0, 0, 0.8))
lib.key(cam, 2, location=(9.0, 8.0, 2.5), aim=(1.0, 0, 0.8))
lib.key(cam, 3, location=(2.6, -1.6, 0.5), aim=(2.0, 0, 0.4))
for obj in bpy.data.objects:
    if obj.type == "MESH":
        print("MAT", obj.name, [s.material.name for s in obj.material_slots])
lib.render("look")
