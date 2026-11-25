"""One bush on magenta, shadeless light: are its dark shards holes,
back faces or paint? (test renders only)"""
import os
import sys

import bpy

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import trailer_lib as lib

scene = lib.new_scene(2, glare=0.0)
scene.render.use_motion_blur = False
lib.sky((1, 0, 1), (1, 0, 1), strength=1.0)
bush = lib.glb(os.path.join(lib.MODELS, "bush.glb"), height=1.5)
mesh = bush.children[0]
print("TRIS", len(mesh.data.polygons), "MATS",
      [(s.material.name, s.material.use_backface_culling)
       for s in mesh.material_slots])
if "paint" in sys.argv:
    # Back faces in flat cyan: anything cyan is the inside of the shell.
    material = mesh.material_slots[0].material
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    out = next(n for n in nodes if n.type == "OUTPUT_MATERIAL")
    front = out.inputs["Surface"].links[0].from_socket
    side = nodes.new("ShaderNodeNewGeometry")
    cyan = nodes.new("ShaderNodeEmission")
    cyan.inputs["Color"].default_value = (0, 1, 1, 1)
    mix = nodes.new("ShaderNodeMixShader")
    links.new(side.outputs["Backfacing"], mix.inputs["Fac"])
    links.new(front, mix.inputs[1])
    links.new(cyan.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out.inputs["Surface"])
if "unlit" in sys.argv:
    # The texture alone, no lighting: is the dark painted in?
    material = mesh.material_slots[0].material
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    out = next(n for n in nodes if n.type == "OUTPUT_MATERIAL")
    shader = nodes["Principled BSDF"]
    glow = nodes.new("ShaderNodeEmission")
    links.new(shader.inputs["Base Color"].links[0].from_socket,
              glow.inputs["Color"])
    links.new(glow.outputs[0], out.inputs["Surface"])
bpy.context.view_layer.update()
print("SIZE", [round(v, 2) for v in mesh.dimensions], bush.scale[0])
cam = lib.camera(lens=50.0)
lib.key(cam, 1, location=(1.0, -9.0, 2.0), aim=(0, 0, 0.75))
lib.render("bush")
