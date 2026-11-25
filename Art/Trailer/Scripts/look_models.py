"""Neutral-light line-up of the Meshy models (test renders only).

blender --background --python look_models.py -- models still 1 2 3 4
"""
import os
import sys

import bpy

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import trailer_lib as lib

MODELS = os.path.join(lib.ART, "Trailer", "Models")
scene = lib.new_scene(4, glare=0.0)
scene.render.use_motion_blur = False
lib.sky((0.5, 0.5, 0.5), (0.6, 0.65, 0.7), strength=1.0)
lib.box("Floor", (80, 80, 0.1), (0, 0, -0.05),
        lib.mat("Floor", (0.3, 0.3, 0.3)))
lib.light("SUN", (5, -8, 9), 3.0, aim=(0, 0, 0), size=0.1)
cars = (("civic", 1.42), ("sedan", 1.4), ("suv", 1.8), ("van", 2.0),
        ("truck", 2.9))
plants = (("pine", 11.0), ("spruce", 10.0), ("birch", 8.0), ("oak", 8.0),
          ("bush", 1.3), ("fern", 0.6))
for row, group in enumerate((cars, plants)):
    for index, (name, tall) in enumerate(group):
        root = lib.glb(os.path.join(MODELS, name + ".glb"), height=tall,
                       location=(index * 5.0, row * 30.0, 0))
        sizes = [part.dimensions[:] for part in root.children]
        tris = sum(len(part.data.polygons) for part in root.children)
        print("MODEL", name, tris, sizes, root.scale[0])
hen, _ = lib.append(lib.CHICKEN,
                    ["Armature", "SK_Chicken", "SK_Chicken_Glasses"])
hen.location = (2.5, -1.5, 0)
cam = lib.camera(lens=35.0)
lib.key(cam, 1, location=(10.0, -14.0, 4.0), aim=(10.0, 0, 0.8))
lib.key(cam, 2, location=(-3.5, -4.5, 1.6), aim=(1.0, 0, 0.7))
lib.key(cam, 3, location=(12.5, 2.0, 30.0), aim=(12.5, 30.0, 4.5))
lib.key(cam, 4, location=(26.0, 5.0, 2.5), aim=(20.0, 0, 1.2))
lib.render("models")
