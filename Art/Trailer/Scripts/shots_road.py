"""Road shots: s01 (the Civic approaches), s03 (it drives into the sun).

blender --background --python shots_road.py -- s01|s03 [still <frame>]
"""
import math
import os
import random
import sys

import bpy

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import trailer_lib as lib

SHOT = lib.args()[0][:3]
FRAMES = {"s01": 144, "s03": 192}[SHOT]
SPEED = 21.0 / lib.FPS
LANE = -1.75
GLOW = 0.45
scene = lib.new_scene(FRAMES, glare=0.8, glare_threshold=1.2, samples=64)
# Ray tracing and a glossy road made the asphalt sparkle with noise.
scene.eevee.use_raytracing = False
scene.render.motion_blur_shutter = 0.5
scene.eevee.volumetric_end = 500.0
lib.sky((0.42, 0.16, 0.3), (0.012, 0.02, 0.12), strength=1.0,
        glow=(1.0, 0.33, 0.05), glow_dir=(-0.08, -1, 0.03), glow_power=3.0)
lib.fog((240, 1400, 30), (0, -100, 15), 0.0007, (1.0, 0.7, 0.5), 0.75)
# A low mist over the fields, so the ground behind the trees is not bare.
# Not in the opening: lit by the sun it glowed right in front of the lens.
if SHOT != "s01":
    lib.fog((700, 1400, 7), (0, -100, 3.5), 0.0035, (1.0, 0.62, 0.42),
            0.6)

# The road runs along Y; the car drives toward -Y, where the sun sets.
grass = lib.mat("Grass", (0.07, 0.11, 0.035), rough=1.0)
asphalt = lib.mat("Asphalt", (0.035, 0.035, 0.04), rough=0.9)
paint = lib.mat("Paint", (0.75, 0.72, 0.6), rough=0.6)
lib.box("Ground", (3000, 3000, 0.1), (0, 0, -0.05), grass)
lib.box("Road", (7.0, 3000, 0.1), (0, 0, -0.03), asphalt)
for side in (-3.2, 3.2):
    lib.box("Edge", (0.12, 3000, 0.1), (side, 0, -0.025), paint)
for index in range(-90, 90):
    lib.box("Dash", (0.14, 3.0, 0.1), (0, index * 9.0, -0.025), paint)

random.seed(7)
kinds = lib.trees(glow=GLOW)
for _ in range(620):
    side = random.choice((-1, 1))
    spot = (side * (8.0 + random.random() ** 1.6 * 70.0),
            random.uniform(-520, 700), 0)
    lib.copy_tree(random.choice(kinds), spot, random.uniform(0, 6.28),
                  random.uniform(0.8, 1.25))
for _ in range(1400):
    # The forest behind the first rows: far, so it casts no shadows.
    side = random.choice((-1, 1))
    spot = (side * random.uniform(45.0, 300.0), random.uniform(-900, 900),
            0)
    far = lib.copy_tree(random.choice(kinds), spot,
                        random.uniform(0, 6.28), random.uniform(0.9, 1.5))
    for part in far.children:
        part.visible_shadow = False
for _ in range(700):
    # A second band, 15 to 70 m from the road, so no sky shows through
    # between the trunks of the first rows.
    side = random.choice((-1, 1))
    spot = (side * random.uniform(15.0, 70.0), random.uniform(-520, 700), 0)
    mid = lib.copy_tree(random.choice(kinds), spot,
                        random.uniform(0, 6.28), random.uniform(0.9, 1.4))
    for part in mid.children:
        part.visible_shadow = False
small = lib.trees((("spruce", 5.5), ("spruce", 4.0), ("bush", 2.4)),
                  glow=GLOW)
for _ in range(1100):
    # Young spruces and thickets close the forest at trunk height.
    side = random.choice((-1, 1))
    spot = (side * random.uniform(10.0, 75.0), random.uniform(-520, 700), 0)
    low = lib.copy_tree(random.choice(small), spot,
                        random.uniform(0, 6.28), random.uniform(0.8, 1.3))
    for part in low.children:
        part.visible_shadow = False
for _ in range(420):
    # Behind the car's start the road seems to bend into the forest:
    # trees close the gap that the straight road leaves on the horizon.
    spot = (random.uniform(-32.0, 32.0), random.uniform(470.0, 900.0), 0)
    wall = lib.copy_tree(random.choice(kinds), spot,
                         random.uniform(0, 6.28), random.uniform(1.2, 1.9))
    for part in wall.children:
        part.visible_shadow = False
shrubs = lib.trees((("bush", 1.5), ("bush", 1.0), ("fern", 0.7)),
                   glow=GLOW)
for _ in range(260):
    side = random.choice((-1, 1))
    spot = (side * (5.5 + random.random() ** 2 * 30.0),
            random.uniform(-520, 500), 0)
    if -14.0 < spot[1] < 26.0 and abs(spot[0]) < 9.0:
        continue
    lib.copy_tree(random.choice(shrubs), spot, random.uniform(0, 6.28),
                  random.uniform(0.7, 1.3))

sun_at = (-130.0, -1500.0, 60.0)
lib.light("SUN", sun_at, 6.0, color=(1.0, 0.5, 0.22), aim=(0, 0, 0),
          size=0.03)
disc = lib.mat("SunDisc", (0, 0, 0), emit=(1.0, 0.45, 0.12), power=60.0)
bpy.ops.mesh.primitive_uv_sphere_add(radius=40.0, location=sun_at)
bpy.context.object.data.materials.append(disc)
bpy.context.object.visible_shadow = False

# No beams in the mist and a duller paint: both read as a glowing car.
car = lib.civic(haze=False, lamps=9.0 if SHOT == "s01" else 25.0,
                gloss=0.6, coat=0.05)
if SHOT == "s01":
    # Low by the roadside, looking away from the sun at the car coming.
    lib.key(car, 1, location=(LANE, 150.0, 0), linear=True)
    lib.key(car, FRAMES, location=(LANE, 150.0 - SPEED * FRAMES, 0),
            linear=True)
    cam = lib.camera(lens=85.0, fstop=2.8, focus=car)
    # The camera is locked off: any pan made the thin leaf cards cover
    # and uncover each other from frame to frame, which read as blinking
    # polygons. With a still camera the forest is identical in every
    # frame and only the car moves, from the distance to past the lens.
    lib.key(cam, 1, location=(4.5, -2.0, 0.5), aim=(LANE, 70.0, 1.1))
else:
    # Behind the car, rising and falling back while it drives off.
    lib.key(car, 1, location=(LANE, 0.0, 0), linear=True)
    lib.key(car, FRAMES, location=(LANE, -SPEED * FRAMES, 0), linear=True)
    cam = lib.camera(lens=40.0, fstop=4.0, focus=car)
    lib.key(cam, 1, location=(LANE + 0.45, 8.5, 0.9),
            aim=(LANE, -20.0, 1.0), linear=True)
    lib.key(cam, FRAMES, location=(-0.4, -SPEED * FRAMES * 0.72, 5.5),
            aim=(-1.2, -SPEED * FRAMES - 40.0, 2.0), linear=True)

if "noshadow" in sys.argv:
    # Test: are the dark shards on the plants shadows?
    for light in bpy.data.lights:
        light.use_shadow = False
if "freeze" in sys.argv:
    # Test: nothing moves, so any change between frames is flicker.
    for obj in bpy.data.objects:
        obj.animation_data_clear()
    lib.LINEAR.clear()
if "clip" in sys.argv:
    scene.camera.data.clip_start = 1.0
    scene.camera.data.clip_end = 1700.0
if "bigblur" in sys.argv:
    scene.render.motion_blur_shutter = 4.0
if "steps" in sys.argv:
    scene.eevee.motion_blur_steps = 8
if "nodof" in sys.argv:
    scene.camera.data.dof.use_dof = False
if "noblur" in sys.argv:
    scene.render.use_motion_blur = False
if "softsun" in sys.argv:
    for light in bpy.data.lights:
        if light.type == "SUN":
            light.angle = 0.35
lib.render(lib.args()[0])
