"""Lists objects, actions and materials of .blend files (run in Blender).

blender --background --python blender_dump.py -- <file.blend> ...
"""
import sys

import bpy

for path in sys.argv[sys.argv.index("--") + 1:]:
    bpy.ops.wm.open_mainfile(filepath=path)
    scene = bpy.context.scene
    print(f"FILE {path} unit {scene.unit_settings.scale_length}"
          f" fps {scene.render.fps}")
    for obj in bpy.data.objects:
        dims = [round(value, 1) for value in obj.dimensions]
        loc = [round(value, 1) for value in obj.location]
        mats = [slot.material.name for slot in obj.material_slots
                if slot.material]
        parent = obj.parent.name if obj.parent else "-"
        bone = obj.parent_bone or "-"
        users = [c.name for c in obj.users_collection]
        print(f"OBJ {obj.name} {obj.type} dims {dims} loc {loc} parent"
              f" {parent}/{bone} mats {mats} hide {obj.hide_render}"
              f" coll {users}")
    for action in bpy.data.actions:
        slots = [slot.identifier for slot in action.slots]
        print(f"ACT {action.name} {tuple(action.frame_range)} {slots}")
    for image in bpy.data.images:
        print(f"IMG {image.name} {image.filepath} packed"
              f" {bool(image.packed_file)}")
