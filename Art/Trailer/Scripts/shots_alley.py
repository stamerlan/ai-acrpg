"""Night alley shots: s08 (the Shawarman hones his knife under the neon
sign), s09 (three shadows on the wall), s12 (his cap lands).

blender --background --python shots_alley.py -- s08|s09|s12 [still <f>]
"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import trailer_lib as lib
import shots_props

SHOT = lib.args()[0][:3]
FRAMES = {"s08": 100, "s09": 96, "s12": 84}[SHOT]
PINK = (1.0, 0.08, 0.25)
CYAN = (0.1, 0.8, 1.0)
scene = lib.new_scene(FRAMES, glare=1.0, glare_threshold=1.5, samples=32)
scene.eevee.volumetric_end = 40.0
lib.sky((0.01, 0.012, 0.03), (0.002, 0.003, 0.01), strength=1.0)

wet = lib.mat("WetAsphalt", (0.02, 0.02, 0.025), rough=0.18)
brick = lib.mat("Brick", (0.07, 0.04, 0.035), rough=0.85)
nodes = brick.node_tree.nodes
bricks = nodes.new("ShaderNodeTexBrick")
bricks.inputs["Color1"].default_value = (0.36, 0.17, 0.13, 1)
bricks.inputs["Color2"].default_value = (0.26, 0.12, 0.1, 1)
bricks.inputs["Mortar"].default_value = (0.1, 0.09, 0.09, 1)
bricks.inputs["Scale"].default_value = 9.0
coords = nodes.new("ShaderNodeTexCoord")
brick.node_tree.links.new(coords.outputs["Object"], bricks.inputs[0])
brick.node_tree.links.new(
    bricks.outputs["Color"], nodes["Principled BSDF"].inputs["Base Color"])
lib.box("Floor", (60, 60, 0.1), (0, 0, -0.05), wet)
lib.box("Wall", (40, 0.4, 7), (0, 3.2, 3.5), brick)
if "flat" in sys.argv:
    lib.light("SUN", (2, -6, 6), 4.0, aim=(0, 0, 1), size=0.2)
else:
    lib.fog((40, 14, 7), (0, -2, 3.5), 0.012, (0.8, 0.85, 1.0), 0.4)
lib.neon("DONER", (-0.3, 2.95, 2.0), 0.85, PINK)
lib.neon("24 H", (2.2, 2.95, 1.55), 0.42, CYAN, power=18.0)
lib.light("AREA", (0, 2.3, 3.2), 350.0, PINK, aim=(0, 0.5, 0), size=2.5)
lib.light("AREA", (2.2, 2.5, 1.8), 60.0, CYAN, aim=(2, 0, 0), size=0.8)
lib.glb("city-kit-roads/dumpster.glb", height=1.3, location=(-3.4, 2.2, 0),
        yaw=0.2)
lib.glb("survival-kit/barrel.glb", height=0.95, location=(3.6, 2.4, 0))
lib.glb("survival-kit/box-large.glb", height=0.7, location=(4.4, 2.3, 0),
        yaw=0.5)
ACTIONS = ["A_Shawarman_Idle", "A_Cook_Walk", "A_Shawarman_Search"]


def cook(source=lib.SHAWARMAN, mesh="SK_Shawarman"):
    root, parts = lib.append(source, ["Armature", mesh], ACTIONS)
    return root, parts["Armature"]


if SHOT == "s08":
    root, parts = lib.append(
        lib.SHAWARMAN, ["Armature", "SK_Shawarman"], ACTIONS)
    rig = parts["Armature"]
    root.location = (0.2, 1.5, 0)
    # One slow pass of the clip (it must not repeat): he rubs his
    # hands, empty. A knife and a steel never sat right in them.
    lib.play(rig, "A_Shawarman_Idle", scale=1.0)
    shots_props.rub_hands(rig, parts["SK_Shawarman"], FRAMES)
    lib.light("SPOT", (-3.5, 1.0, 2.6), 900.0, CYAN, aim=(0.2, 1.5, 1.3),
              cone=35.0)
    lib.light("POINT", (0.6, -0.6, 0.5), 6.0, (1.0, 0.5, 0.3))
    cam = lib.camera(lens=50.0, fstop=2.0, focus=3.9)
    lib.key(cam, 1, location=(-1.1, -3.9, 0.55), aim=(0.2, 1.5, 1.5))
    lib.key(cam, FRAMES, location=(-0.6, -2.4, 0.75), aim=(0.2, 1.5, 1.35),
            **{"data.dof.focus_distance": 4.0})
    cam.data.dof.focus_distance = 5.6
    cam.data.dof.keyframe_insert("focus_distance", frame=1)

if SHOT == "s09":
    # The cooks walk behind the camera, between a low lamp and the wall.
    lib.light("SPOT", (9.0, -9.0, 0.25), 9000.0, (1.0, 0.75, 0.5),
              aim=(9.0, 3.0, 2.2), cone=75.0, size=0.02)
    cooks = [
        cook(),
        cook(lib.SHAWARMAN.replace("Shawarman", "Skewerman"),
             "SK_Skewerman"),
        cook(lib.SHAWARMAN.replace("Shawarman", "GrillSergeant"),
             "SK_GrillSergeant")]
    for index, (root, rig) in enumerate(cooks):
        root.rotation_euler = (0, 0, math.pi / 2)
        start = 7.6 - index * 0.6
        lane = -3.2 - index * 0.5
        lib.key(root, 1, location=(start, lane, 0), linear=True)
        lib.key(root, FRAMES, location=(start + 2.8, lane, 0), linear=True)
        lib.play(rig, "A_Cook_Walk", repeat=8.0, scale=1.3,
                 offset=index * 7.0)
    torch = lib.light("SPOT", (9.0, -1.0, 1.4), 0.0, (1.0, 0.95, 0.85),
                      aim=(4.0, 3.0, 1.5), cone=22.0, size=0.02)
    lib.key(torch, 56, **{"data.energy": 0.0})
    lib.key(torch, 60, **{"data.energy": 6000.0})
    torch.keyframe_insert("rotation_euler", frame=60)
    lib.look_at(torch, (11.0, 3.0, 2.2))
    torch.keyframe_insert("rotation_euler", frame=FRAMES)
    cam = lib.camera(lens=28.0)
    lib.key(cam, 1, location=(8.6, -1.6, 1.1), aim=(9.0, 3.0, 2.1))
    lib.key(cam, FRAMES, location=(9.4, -1.6, 1.1), aim=(9.8, 3.0, 2.1))

if SHOT == "s12":
    paper = lib.mat("Paper", (0.85, 0.85, 0.8), rough=0.7)
    props = os.path.join(lib.ART, "Enemies", "Shawarman", "Props")
    bpy.ops.import_scene.fbx(
        filepath=os.path.join(props, "SM_ShawarmanCap.fbx"))
    cap_mesh = bpy.context.selected_objects[0]
    cap_mesh.data.materials.clear()
    cap_mesh.data.materials.append(paper)
    # The cap is open where the head was, and from below the camera saw
    # through its jagged rim: a dark lining a little way up closes it.
    corners = [Vector(corner) for corner in cap_mesh.bound_box]
    low = min(corner.z for corner in corners)
    tall = max(corner.z for corner in corners) - low
    wide = max(corner.x for corner in corners) - min(
        corner.x for corner in corners)
    deep = max(corner.y for corner in corners) - min(
        corner.y for corner in corners)
    middle = sum(corners, Vector()) / 8
    bpy.ops.mesh.primitive_circle_add(
        vertices=24, radius=0.5, fill_type="NGON")
    lining = bpy.context.object
    lining.data.materials.append(lib.mat("Lining", (0.12, 0.11, 0.1)))
    lining.parent = cap_mesh
    lining.location = (middle.x, middle.y, low + 0.5 * tall)
    lining.scale = (wide * 0.66, deep * 0.66, 1.0)
    size = 0.26 / max(cap_mesh.dimensions)
    cap = lib.empty("Cap")
    cap_mesh.parent = cap
    cap_mesh.location = (0, 0, 0)
    cap_mesh.scale = [value * size for value in cap_mesh.scale]
    print("CAP", list(cap_mesh.dimensions), list(cap_mesh.location))
    for frame, height, sway, roll in (
            (1, 1.5, -0.3, 0.5), (10, 1.1, 0.22, -0.45),
            (20, 0.72, -0.18, 0.4), (29, 0.4, 0.12, -0.3),
            (37, 0.1, -0.04, 0.12), (41, 0.0, 0.0, 0.0)):
        lib.key(cap, frame, location=(sway, 0.3, height))
        cap.rotation_euler = (roll * 0.5, roll, roll)
        cap.keyframe_insert("rotation_euler", frame=frame)
    _, bread = lib.append(lib.ENEMY_PROPS, ["SM_Flatbread"])
    flat = bread["SM_Flatbread"].parent
    bread["SM_Flatbread"].location = (0, 0, 0)
    for frame, height, tilt in ((44, 1.6, 0.6), (52, 0.012, 0.0),
                                (55, 0.05, 0.05), (58, 0.012, 0.0)):
        lib.key(flat, frame, location=(0.42, 0.55, height))
        flat.rotation_euler = (tilt, tilt * 0.5, 0.4)
        flat.keyframe_insert("rotation_euler", frame=frame)
    lib.key(flat, 1, location=(0.42, 0.55, 30.0))
    cam = lib.camera(lens=35.0, fstop=1.8, focus=1.25)
    lib.key(cam, 1, location=(-0.5, -0.85, 0.09), aim=(0.15, 0.4, 0.3))
    lib.key(cam, FRAMES, location=(-0.4, -0.75, 0.09), aim=(0.2, 0.4, 0.1))

lib.render(lib.args()[0])
