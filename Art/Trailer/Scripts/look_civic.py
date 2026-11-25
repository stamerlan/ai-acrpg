"""Close views of the Civic and the truck (test renders only)."""
import os
import sys

import bpy

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import trailer_lib as lib

MODELS = os.path.join(lib.ART, "Trailer", "Models")
scene = lib.new_scene(6, glare=0.0)
scene.render.use_motion_blur = False
lib.sky((0.5, 0.5, 0.5), (0.6, 0.65, 0.7), strength=1.0)
lib.box("Floor", (80, 80, 0.1), (0, 0, -0.05),
        lib.mat("Floor", (0.3, 0.3, 0.3)))
lib.light("SUN", (-5, -8, 9), 3.0, aim=(0, 0, 0), size=0.1)
civic = lib.glb(os.path.join(MODELS, "civic.glb"), height=1.42)
truck = lib.glb(os.path.join(MODELS, "truck.glb"), height=2.9,
                location=(0, 20, 0))
bpy.context.view_layer.update()
for root in (civic, truck):
    part = root.children[0]
    print("SIZE", root.name, [round(v * root.scale[0], 2)
                              for v in part.dimensions])
cam = lib.camera(lens=50.0)
lib.key(cam, 1, location=(-9.0, 0.0, 0.9), aim=(0, 0, 0.7))
lib.key(cam, 2, location=(9.0, 0.0, 0.9), aim=(0, 0, 0.7))
lib.key(cam, 3, location=(0.0, -9.0, 0.9), aim=(0, 0, 0.7))
lib.key(cam, 4, location=(0.0, 0.0, 12.0), aim=(0, 0.01, 0.7))
lib.key(cam, 5, location=(12.0, 20.0, 1.6), aim=(0, 20, 1.4))
lib.key(cam, 6, location=(-12.0, 12.0, 3.0), aim=(0, 20, 1.4))
lib.render("civic")
