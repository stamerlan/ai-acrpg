"""NPC hand props from primitives, to Art/NPCs/Props/SM_<Name>.fbx (cm).

Run headless from the repo root:
  blender --background --python Art/NPCs/Scripts/blender_npc_props.py

SM_Thermos: Kolya's green thermos, 28 cm, its axis along +Z with the
origin at the middle of the grip, so it sits in the fist like the cooks'
knife (see BP_NPC HandProp).
"""
import bpy
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "NPCs", "Props")


def material(name, rgb, rough):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1)
    p.inputs["Roughness"].default_value = rough
    return m


def cylinder(r, depth, z, mat, verts=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r,
                                        depth=depth, location=(0, 0, z))
    o = bpy.context.active_object
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return o


def thermos():
    green = material("M_Thermos_Green", (0.05, 0.32, 0.12), 0.45)
    steel = material("M_Thermos_Steel", (0.55, 0.56, 0.57), 0.3)
    parts = [cylinder(4.6, 20.0, 0.0, green),
             cylinder(4.7, 1.2, -10.0, steel),
             cylinder(4.7, 1.0, 10.2, steel),
             cylinder(4.2, 6.0, 13.6, steel)]
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    o.name = o.data.name = "SM_Thermos"
    return o


def export(o, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for x in bpy.data.objects:
        x.select_set(x is o)
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, object_types={'MESH'},
        apply_unit_scale=True, global_scale=1.0,
        apply_scale_options='FBX_SCALE_ALL', mesh_smooth_type='FACE',
        path_mode='STRIP')


if __name__ == "__main__":
    bpy.ops.wm.read_homefile(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 0.01
    export(thermos(), os.path.join(OUT, "SM_Thermos.fbx"))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "NPCProps.blend"))
