"""Car shots: s02 (her at the wheel), s10 (the trunk opens, seen from
inside), s11 (she raises the shotgun at the camera).

blender --background --python shots_car.py -- s02|s10|s11 [still <f>]
"""
import math
import os
import random
import sys

import bpy

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import trailer_lib as lib

SHOT = lib.args()[0][:3]
FRAMES = {"s02": 144, "s10": 84, "s11": 84}[SHOT]
scene = lib.new_scene(FRAMES, glare=0.8, glare_threshold=1.3, samples=32)
dark = lib.mat("Interior", (0.012, 0.012, 0.014), rough=0.6)
hen, hen_parts = lib.append(
    lib.CHICKEN, ["Armature", "SK_Chicken", "SK_Chicken_Glasses"],
    ["A_Chicken_Idle", "A_Chicken_TrunkRummage", "A_Chicken_ShotgunAim"])
rig = hen_parts["Armature"]

if SHOT == "s02":
    # She faces -Y (the way the car drives); the sun is low ahead.
    lib.sky((0.42, 0.16, 0.3), (0.012, 0.02, 0.12), strength=1.0,
            glow=(1.0, 0.33, 0.05), glow_dir=(-0.08, -1, 0.03),
            glow_power=3.0)
    lib.light("SUN", (-3.0, -10.0, 1.6), 7.0, (1.0, 0.5, 0.22),
              aim=(0, 0, 0.5), size=0.03)
    lib.light("AREA", (-1.5, 0.6, 1.0), 12.0, (0.4, 0.5, 1.0),
              aim=(0, 0, 0.5), size=1.0)
    lib.play(rig, "A_Chicken_Idle", repeat=3.0)
    lib.box("Seat", (0.5, 0.14, 0.8), (0, 0.33, 0.4), dark)
    lib.box("Headrest", (0.3, 0.1, 0.2), (0, 0.33, 0.88), dark)
    lib.box("Roof", (1.6, 2.4, 0.06), (0.1, 0, 1.0), dark)
    lib.box("Dash", (1.6, 0.4, 0.5), (0.1, -0.75, 0.1), dark)
    lib.box("DoorNear", (0.08, 2.4, 0.5), (-0.62, 0, 0.05), dark)
    lib.box("DoorFar", (0.08, 2.4, 0.5), (0.78, 0, 0.05), dark)
    lib.box("PillarNear", (0.08, 0.1, 1.2), (-0.62, -0.72, 0.6), dark,
            rotation=(0.5, 0, 0))
    lib.box("PillarFar", (0.08, 0.1, 1.2), (0.78, -0.72, 0.6), dark,
            rotation=(0.5, 0, 0))
    lib.box("PostFar", (0.08, 0.12, 1.0), (0.78, 0.55, 0.55), dark)
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.17, minor_radius=0.022, location=(0, -0.42, 0.42),
        rotation=(-1.15, 0, 0))
    bpy.context.object.data.materials.append(dark)
    grass = lib.mat("Grass", (0.07, 0.11, 0.035), rough=1.0)
    lib.box("Ground", (600, 3000, 0.1), (0, 0, -0.9), grass)
    # Trees and poles rush past (the car stands still, the world moves).
    world = lib.empty("World")
    random.seed(3)
    kinds = lib.trees()
    for index in range(150):
        side = 1 if index % 3 else -1
        spot = (side * random.uniform(7, 30), random.uniform(-160, 20),
                -0.9)
        twin = lib.copy_tree(random.choice(kinds), spot,
                             random.uniform(0, 6.28))
        twin.parent = world
    travel = 16.0 / lib.FPS * FRAMES
    lib.key(world, 1, location=(0, 0, 0), linear=True)
    lib.key(world, FRAMES, location=(0, travel, 0), linear=True)
    cam = lib.camera(lens=70.0, fstop=2.0, focus=1.45)
    lib.key(cam, 1, location=(-1.25, -0.7, 0.6), aim=(0.02, -0.06, 0.52))
    lib.key(cam, FRAMES, location=(-1.05, -0.95, 0.6),
            aim=(0.02, -0.06, 0.52))

if SHOT == "s10":
    # Camera on the trunk floor looking up; she leans in from +Y.
    lib.sky((0.02, 0.03, 0.08), (0.004, 0.006, 0.03), strength=1.0)
    for name, size, spot in (
            ("Left", (0.05, 1.0, 0.5), (-0.55, 0, 0.25)),
            ("Right", (0.05, 1.0, 0.5), (0.55, 0, 0.25)),
            ("Front", (1.15, 0.05, 0.5), (0, -0.5, 0.25)),
            ("Back", (1.15, 0.05, 0.24), (0, 0.5, 0.12)),
            ("Floor", (1.15, 1.0, 0.05), (0, 0, -0.025))):
        lib.box(name, size, spot, dark)
    hinge = lib.empty("Hinge", location=(0, -0.5, 0.5))
    lib.box("Lid", (1.2, 1.05, 0.04), (0, 0.52, 0), dark, parent=hinge)
    hinge.rotation_euler = (0, 0, 0)
    hinge.keyframe_insert("rotation_euler", frame=8)
    hinge.rotation_euler = (math.radians(74), 0, 0)
    hinge.keyframe_insert("rotation_euler", frame=22)
    hen.location = (0, 0.7, 0.08)
    hen.rotation_euler = (0, 0, 0)
    lib.play(rig, "A_Chicken_Idle", start=1)
    lib.play(rig, "A_Chicken_TrunkRummage", start=34, blend_in=8)
    _, gun = lib.append(lib.PROPS, ["SM_Shotgun"])
    gun["SM_Shotgun"].parent.location = (0.05, -0.12, 0.05)
    gun["SM_Shotgun"].parent.rotation_euler = (1.4, 0, 0.35)
    lamp = lib.light("POINT", (0.3, -0.3, 0.3), 0.0, (1.0, 0.7, 0.4),
                     size=0.05)
    for frame, power in ((16, 0.0), (17, 30.0), (19, 6.0), (21, 40.0)):
        lib.key(lamp, frame, **{"data.energy": power})
    lib.light("SPOT", (-2.5, 3.0, 2.5), 500.0, (0.35, 0.5, 1.0),
              aim=(0, 0.8, 0.6), cone=40.0)
    lib.light("POINT", (0.0, 0.75, 0.2), 3.0, (1.0, 0.05, 0.02))
    cam = lib.camera(lens=20.0, fstop=2.8, focus=0.9)
    lib.key(cam, 1, location=(0.05, -0.33, 0.06), aim=(0, 0.6, 0.6))
    lib.key(cam, FRAMES, location=(0.05, -0.36, 0.06), aim=(0, 0.55, 0.55))

if SHOT == "s11":
    # She stands behind the open trunk, facing +Y and the camera.
    scene.eevee.volumetric_end = 40.0
    lib.sky((0.02, 0.03, 0.08), (0.004, 0.006, 0.03), strength=1.0)
    wet = lib.mat("WetAsphalt", (0.02, 0.02, 0.025), rough=0.18)
    lib.box("Floor", (60, 60, 0.1), (0, 0, -0.05), wet)
    lib.fog((30, 30, 6), (0, 0, 3), 0.02, (0.8, 0.85, 1.0), 0.5)
    car = lib.civic(beams=0.0, tail=9.0)
    car.location = (0, -1.4, 0)
    for side in (-0.56, 0.56):
        lib.light("POINT", (side, 1.2, 0.9), 25.0, (1.0, 0.04, 0.02))
    lib.light("SPOT", (-3.0, -1.0, 3.0), 1500.0, (0.35, 0.5, 1.0),
              aim=(0, 2.1, 0.4), cone=30.0)
    lib.light("AREA", (1.2, 4.5, 1.2), 14.0, (1.0, 0.25, 0.3),
              aim=(0, 2.1, 0.4), size=1.5)
    hen.location = (0, 2.1, 0)
    hen.rotation_euler = (0, 0, math.pi)
    lib.play(rig, "A_Chicken_ShotgunAim", repeat=4.0)
    _, gun = lib.append(lib.PROPS, ["SM_Shotgun"])
    grip = lib.empty("Grip", location=(-0.17, 2.12, 0.3))
    gun["SM_Shotgun"].parent.parent = grip
    gun["SM_Shotgun"].parent.location = (0, 0.38, 0)
    gun["SM_Shotgun"].parent.rotation_euler = (0, 0, math.pi / 2)
    # A long lens on her head hides the hold below the wing; she lifts
    # the barrel into the lens while the camera drops onto the muzzle.
    for frame, pitch, back in ((1, -0.42, 0.0), (20, -0.42, 0.0),
                               (24, -0.42, -0.05), (30, -0.42, 0.0),
                               (54, 0.1, 0.0), (FRAMES, 0.11, 0.0)):
        grip.rotation_euler = (pitch, 0, 0)
        grip.keyframe_insert("rotation_euler", frame=frame)
        lib.key(grip, frame, location=(-0.17, 2.12 + back, 0.3))
    cam = lib.camera(lens=85.0, fstop=2.0, focus=1.0)
    lib.key(cam, 1, location=(0.06, 3.95, 0.5), aim=(0.0, 2.1, 0.5))
    lib.key(cam, 30, location=(0.03, 3.85, 0.5), aim=(0.0, 2.1, 0.5))
    lib.key(cam, FRAMES, location=(-0.17, 3.55, 0.44),
            aim=(-0.17, 2.3, 0.41), **{"data.dof.focus_distance": 0.62})
    cam.data.dof.focus_distance = 1.8
    cam.data.dof.keyframe_insert("focus_distance", frame=1)
    cam.data.dof.keyframe_insert("focus_distance", frame=44)

lib.render(lib.args()[0])
