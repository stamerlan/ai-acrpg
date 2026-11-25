"""Camp shots: s13 (the fire by the river, wide), s14 (close on her),
s15 (the truck's back door, frost rolling out).

blender --background --python shots_camp.py -- s13|s14|s15 [still <f>]
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import trailer_lib as lib

SHOT = lib.args()[0][:3]
FRAMES = {"s13": 144, "s14": 132, "s15": 144}[SHOT]
FIRE = (1.0, 0.42, 0.1)
scene = lib.new_scene(FRAMES, glare=0.9, glare_threshold=1.4, samples=32)
scene.eevee.volumetric_end = 80.0
lib.sky((0.012, 0.02, 0.06), (0.002, 0.004, 0.02), strength=1.0)
random.seed(11)

grass = lib.mat("Grass", (0.03, 0.05, 0.02), rough=1.0)
water = lib.mat("Water", (0.01, 0.02, 0.04), rough=0.05, metallic=0.9)
lib.box("Ground", (400, 400, 0.1), (0, 0, -0.05), grass)
lib.box("River", (400, 14, 0.1), (0, 16, -0.02), water)
star = lib.mat("Star", (0, 0, 0), emit=(0.8, 0.9, 1.0), power=12.0)
for _ in range(260):
    turn = random.uniform(0, 6.28)
    rise = random.uniform(0.08, 1.2)
    spot = (700 * math.cos(turn) * math.cos(rise),
            700 * math.sin(turn) * math.cos(rise), 700 * math.sin(rise))
    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=1, radius=random.uniform(0.5, 1.4), location=spot)
    bpy.context.object.data.materials.append(star)
lib.light("SUN", (-20, 30, 40), 0.25, (0.5, 0.65, 1.0), aim=(0, 0, 0),
          size=0.05)
lib.fog((60, 60, 8), (0, 0, 4), 0.012, (0.8, 0.85, 1.0), 0.3)

kinds = lib.trees()
shrubs = lib.trees((("bush", 1.4), ("fern", 0.6), ("fern", 0.45)))
for index in range(260):
    turn = random.uniform(0, 6.28)
    reach = random.uniform(7.0, 45.0)
    spot = Vector((reach * math.cos(turn),
                   reach * math.sin(turn) * 0.8 - 6.0, 0))
    if 8.0 < spot.y < 24.0 or spot.length < 7.5:
        continue
    if -13.0 < spot.x < 4.0 and -3.5 < spot.y < 7.0:
        continue
    lib.copy_tree(random.choice(kinds if index % 2 else shrubs), spot,
                  random.uniform(0, 6.28), random.uniform(0.8, 1.3))
# Her camp, on the far side of the fire from the truck: the tent, her
# backpack, and bushes and ferns at the edge of the firelight.
lib.glb("survival-kit/tent-canvas.glb", height=1.6, location=(4.5, 0.9, 0),
        yaw=1.2)
_, pack = lib.append(lib.PROPS, ["SM_Backpack"])
pack["SM_Backpack"].parent.location = (2.5, 0.5, 0)
pack["SM_Backpack"].parent.rotation_euler = (0, 0, 2.2)
for spot, kind, size in (((5.4, -0.6, 0), 0, 1.3), ((6.2, 2.6, 0), 0, 1.6),
                         ((4.6, -2.2, 0), 0, 1.0),
                         ((2.4, 2.6, 0), 2, 1.4), ((6.3, 0.4, 0), 1, 1.5),
                         ((3.4, 3.4, 0), 0, 1.2)):
    lib.copy_tree(shrubs[kind], spot, sum(spot) * 2.0, size)

# Behind the hen: a log to sit on, bushes and ferns.
lib.glb("nature-kit/log.glb", height=0.32, location=(1.3, 2.5, 0), yaw=0.5)
for spot, kind, size in (((-1.6, 4.6, 0), 0, 1.5), ((0.6, 5.2, 0), 0, 1.2),
                         ((-3.4, 5.4, 0), 0, 1.3), ((-0.6, 3.4, 0), 1, 1.3),
                         ((2.0, 4.2, 0), 2, 1.5), ((-2.2, 4.0, 0), 2, 1.2)):
    lib.copy_tree(shrubs[kind], spot, sum(spot) * 2.0, size)
# Grass tufts over the clearing, thinner near the fire and the truck.
tufts = [lib.glb(f"nature-kit/{name}.glb", height=tall,
                 location=(0, 0, -300))
         for name, tall in (("grass", 0.12), ("grass_large", 0.2),
                            ("grass_leafs", 0.15))]
for material in bpy.data.materials:
    if material.name.lower().startswith(("grass", "leafs")) and (
            material.name != "Grass"):
        lib.tint(material.name, (0.05, 0.11, 0.03))
for _ in range(900):
    turn = random.uniform(0, 6.28)
    reach = random.uniform(1.0, 11.0)
    spot = Vector((reach * math.cos(turn), reach * math.sin(turn), 0))
    if spot.y > 8.5 or (reach < 2.2 and random.random() < 0.7):
        continue
    # None close to the cameras, where a tuft is a black blob in the lens.
    if min((spot - Vector(eye)).length
           for eye in ((-3.2, -4.4, 0), (2.0, -1.6, 0))) < 3.6:
        continue
    tuft = lib.copy_tree(random.choice(tufts), spot,
                         random.uniform(0, 6.28), random.uniform(0.7, 1.5))
    for part in tuft.children:
        part.visible_shadow = False

# The fire: logs on a bed of embers, tongues of flame that rise, sway
# and shrink in loops, sparks, and a flickering light.
bark = lib.mat("Log", (0.05, 0.03, 0.02), rough=0.9)
for turn in range(6):
    lib.box("Log", (0.75, 0.11, 0.11), (0, 0, 0.1), bark,
            rotation=(0, 0.3, turn * 1.05))
for turn in range(9):
    spot = (0.48 * math.cos(turn * 0.7), 0.48 * math.sin(turn * 0.7), 0.04)
    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=1, radius=random.uniform(0.1, 0.15), location=spot)
    bpy.context.object.scale.z = 0.6
    bpy.context.object.data.materials.append(
        lib.mat("Stone", (0.12, 0.12, 0.13), rough=0.9))
embers = lib.mat("Embers", (0.02, 0.01, 0.01), emit=(1.0, 0.22, 0.03),
                 power=14.0)
lib.box("Embers", (0.5, 0.5, 0.06), (0, 0, 0.03), embers)

flame = bpy.data.materials.new("Flame")
flame.use_nodes = True
flame.surface_render_method = "BLENDED"
nodes = flame.node_tree.nodes
links = flame.node_tree.links
nodes.clear()
coord = nodes.new("ShaderNodeTexCoord")
split = nodes.new("ShaderNodeSeparateXYZ")
ramp = nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.1
ramp.color_ramp.elements[0].color = (1.0, 0.8, 0.35, 1)
ramp.color_ramp.elements[1].position = 0.95
ramp.color_ramp.elements[1].color = (1.0, 0.08, 0.0, 1)
middle = ramp.color_ramp.elements.new(0.5)
middle.color = (1.0, 0.35, 0.04, 1)
fade = nodes.new("ShaderNodeMapRange")
fade.inputs["From Min"].default_value = 0.35
fade.inputs["From Max"].default_value = 1.0
fade.inputs["To Min"].default_value = 0.9
fade.inputs["To Max"].default_value = 0.0
glow_node = nodes.new("ShaderNodeEmission")
glow_node.inputs["Strength"].default_value = 22.0
clear = nodes.new("ShaderNodeBsdfTransparent")
mix = nodes.new("ShaderNodeMixShader")
out = nodes.new("ShaderNodeOutputMaterial")
links.new(coord.outputs["Generated"], split.inputs[0])
links.new(split.outputs["Z"], ramp.inputs[0])
links.new(split.outputs["Z"], fade.inputs["Value"])
links.new(ramp.outputs[0], glow_node.inputs["Color"])
links.new(fade.outputs[0], mix.inputs["Fac"])
links.new(clear.outputs[0], mix.inputs[1])
links.new(glow_node.outputs[0], mix.inputs[2])
links.new(mix.outputs[0], out.inputs["Surface"])
spark = lib.mat("Spark", (0, 0, 0), emit=(1.0, 0.5, 0.1), power=90.0)

for index in range(34):
    # A tongue: born wide at the logs, climbs, leans and thins out.
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.5)
    tongue = bpy.context.object
    tongue.data.materials.append(flame)
    tongue.visible_shadow = False
    life = random.randint(11, 19)
    frame = 1 - random.randint(0, life)
    while frame < FRAMES + life:
        turn = random.uniform(0, 6.28)
        reach = random.uniform(0.0, 0.17)
        base = Vector((reach * math.cos(turn), reach * math.sin(turn), 0.16))
        wide = random.uniform(0.13, 0.24) * (1.3 - reach * 3.5)
        climb = random.uniform(0.45, 0.85) * (1.2 - reach * 3.0)
        lean = Vector((random.uniform(-0.08, 0.08),
                       random.uniform(-0.08, 0.08), climb))
        for step, grow in ((0, 0.25), (life * 0.3, 1.0), (life, 0.12)):
            part = step / life
            lib.key(tongue, frame + step, location=base + lean * part,
                    linear=True)
            tongue.scale = (wide * grow, wide * grow,
                            wide * (1.6 + 2.2 * part) * max(grow, 0.5))
            tongue.keyframe_insert("scale", frame=frame + step)
        frame += life + 1
for index in range(22):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.008)
    dot = bpy.context.object
    dot.data.materials.append(spark)
    dot.visible_shadow = False
    life = random.randint(20, 38)
    frame = 1 - random.randint(0, life)
    while frame < FRAMES + life:
        start = Vector((random.uniform(-0.1, 0.1),
                        random.uniform(-0.1, 0.1), 0.3))
        drift = Vector((random.uniform(-0.35, 0.35),
                        random.uniform(-0.35, 0.35),
                        random.uniform(1.1, 2.2)))
        bend = Vector((random.uniform(-0.12, 0.12),
                       random.uniform(-0.12, 0.12), 0))
        lib.key(dot, frame, location=start)
        lib.key(dot, frame + life // 2, location=start + drift / 2 + bend)
        lib.key(dot, frame + life, location=start + drift)
        dot.scale = (1, 1, 1)
        dot.keyframe_insert("scale", frame=frame + life // 2)
        dot.scale = (0.01, 0.01, 0.01)
        dot.keyframe_insert("scale", frame=frame + life)
        dot.keyframe_insert("scale", frame=frame)
        frame += life + random.randint(1, 12)
glow = lib.light("POINT", (0, 0, 0.6), 220.0, FIRE, size=0.3)
level = 220.0
for frame in range(1, FRAMES + 2, 2):
    level = min(290.0, max(160.0, level + random.uniform(-45, 45)))
    lib.key(glow, frame, location=(random.uniform(-0.04, 0.04),
                                   random.uniform(-0.04, 0.04), 0.6),
            **{"data.energy": level})

# She sits at the fire; Uncle Kolya is a big shape on a log opposite.
hen, hen_parts = lib.append(
    lib.CHICKEN, ["Armature", "SK_Chicken", "SK_Chicken_Glasses"],
    ["A_Chicken_Idle"])
hen.location = (0.2, 1.3, 0)
hen.rotation_euler = (0, 0, 0.15)
lib.play(hen_parts["Armature"], "A_Chicken_Idle", repeat=3.0)
kolya, kolya_parts = lib.append(
    lib.SHAWARMAN, ["Armature", "SK_Shawarman"], ["A_Shawarman_Sleep"])
kolya.location = (-0.5, -1.9, -0.12)
kolya.rotation_euler = (0, 0, math.pi - 0.25)
kolya.scale = [value * 1.3 for value in kolya.scale]
lib.play(kolya_parts["Armature"], "A_Shawarman_Sleep", scale=0.8,
         offset=40)
kolya_parts["Armature"].pose.bones["Cap"].scale = (0.01, 0.01, 0.01)
# He is a big dark shape against the fire: his colors are cut to a
# fraction, so the moon and the truck light barely show him and only
# the fire draws a rim on him.
skin = kolya_parts["SK_Shawarman"].material_slots[0].material
shader = skin.node_tree.nodes["Principled BSDF"]
source = shader.inputs["Base Color"].links[0].from_socket
dim = skin.node_tree.nodes.new("ShaderNodeMix")
dim.data_type = "RGBA"
dim.blend_type = "MULTIPLY"
dim.inputs["Factor"].default_value = 1.0
dim.inputs["B"].default_value = (0.07, 0.06, 0.06, 1)
skin.node_tree.links.new(source, dim.inputs["A"])
skin.node_tree.links.new(dim.outputs["Result"], shader.inputs["Base Color"])
shader.inputs["Roughness"].default_value = 0.9
for link in list(shader.inputs["Roughness"].links):
    skin.node_tree.links.remove(link)
lib.box("Seat", (1.6, 0.35, 0.3), (-0.5, -2.05, 0.15), bark,
        rotation=(0, 0, -0.25))

# His refrigerated truck backs onto the camp, its door ajar, cold
# light and frost coming out.
truck = lib.vehicle("truck", 2.9)
truck.location = (-7.5, 3.2, 0)
truck.rotation_euler = (0, 0, -1.95)
# Lettering on the rear doors says what he hauls.
ink = lib.mat("Lettering", (0.004, 0.025, 0.18), rough=0.5)
impact = bpy.data.fonts.load("C:/Windows/Fonts/impact.ttf")
for words, across, tall, size in (
        ("FROZEN", 0.47, 2.2, 0.22), ("CHICKEN", -0.47, 2.2, 0.22),
        ("-18 C", 0.47, 1.95, 0.13), ("KOLYA TRANS", -0.47, 1.95, 0.09)):
    bpy.ops.object.text_add(location=(across, 2.972, tall),
                            rotation=(math.pi / 2, 0, math.pi))
    label = bpy.context.object
    label.data.body = words
    label.data.size = size
    label.data.font = impact
    label.data.align_x = "CENTER"
    label.data.extrude = 0.003
    label.data.materials.append(ink)
    label.parent = truck
bpy.context.view_layer.update()
door_at = truck.matrix_world @ Vector((0.0, 2.95, 1.75))
cold = (0.55, 0.8, 1.0)
slit = lib.mat("Slit", (0, 0, 0), emit=cold, power=25.0)
lib.box("Slit", (0.07, 0.05, 1.7), door_at, slit, rotation=(0, 0, -1.95))
door_light = lib.light("POINT", door_at + Vector((0.5, -0.2, 0)), 160.0,
                       cold, size=0.2)
frost = lib.fog((5.0, 5.0, 1.6), door_at + Vector((1.4, -0.6, -0.7)), 0.5,
                cold, 0.2, cloud=True)
lib.key(frost, 1, location=frost.location.copy(), linear=True)
lib.key(frost, FRAMES, location=frost.location + Vector((0.7, -0.3, 0)),
        linear=True)

if SHOT == "s13":
    # The truck is out of frame here: its cold light and frost showed
    # as an unexplained glow at the left edge.
    door_light.data.energy = 0.0
    frost.hide_render = True
    cam = lib.camera(lens=32.0, fstop=2.8, focus=5.0)
    lib.key(cam, 1, location=(-3.4, -4.6, 1.3), aim=(0.4, 0.4, 0.55))
    lib.key(cam, FRAMES, location=(-3.0, -4.1, 1.2), aim=(0.4, 0.4, 0.55))
if SHOT == "s14":
    scene.view_settings.exposure = -1.0
    cam = lib.camera(lens=85.0, fstop=1.8, focus=1.75)
    lib.key(cam, 1, location=(-0.55, -0.35, 0.5), aim=(0.2, 1.3, 0.5))
    lib.key(cam, FRAMES, location=(-0.4, -0.2, 0.5), aim=(0.2, 1.3, 0.52))
if SHOT == "s15":
    cam = lib.camera(lens=50.0, fstop=2.4, focus=6.0)
    lib.key(cam, 1, location=(2.4, -1.7, 0.8), aim=(0.0, 0.0, 0.4))
    lib.key(cam, 78, location=(2.2, -1.6, 0.9), aim=door_at)
    lib.key(cam, FRAMES, location=(1.5, -1.3, 1.0), aim=door_at)

lib.render(lib.args()[0])
