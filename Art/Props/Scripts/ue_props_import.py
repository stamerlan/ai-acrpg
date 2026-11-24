"""Import the prop FBX files used by gameplay and give them M_Env instances.

Run in the editor: py "<this file>" [Name ...]; with names (SM_Shotgun) only
those are imported. Meshes go to /Game/Props/<Name>/,
the base color textures next to them as T_<Mesh>_D, one MI_<Mesh> (parent
M_Env, BaseTex = the texture) per mesh. The meshes get no collision: the
Blueprints that use them (BP_Throwable, BP_CornPickup, BPC_Shotgun) bring
their own or need none.
Writes out.json next to this file.
"""
import json
import os
import sys
import traceback

import unreal

ART = r"C:\Users\vvovchenko\repo\acrpg\Art\Props"
# FBX, texture, UE folder
PROPS = [
    ("Gnome/SM_Gnome.fbx", "Gnome/SM_Gnome_textures/base_color.png",
     "/Game/Props/Gnome"),
    ("Gnome/SM_GnomeBroken.fbx",
     "Gnome/SM_GnomeBroken_textures/base_color.png", "/Game/Props/Gnome"),
    ("Corn/SM_CornCob.fbx", "Corn/SM_CornCob_base_color.png",
     "/Game/Props/Corn"),
    ("Shotgun/SM_Shotgun.fbx", "Shotgun/SM_Shotgun_base_color.png",
     "/Game/Props/Shotgun"),
]
ONLY = sys.argv[1:]
if ONLY:
    PROPS = [p for p in PROPS
             if os.path.splitext(os.path.basename(p[0]))[0] in ONLY]
eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()


def task(src, dst, name, options=None):
    t = unreal.AssetImportTask()
    t.filename = os.path.join(ART, src)
    t.destination_path = dst
    t.destination_name = name
    t.replace_existing = True
    t.automated = True
    t.save = True
    if options:
        t.options = options
    return t


def import_all():
    tasks = []
    for fbx, tex, dst in PROPS:
        name = os.path.splitext(os.path.basename(fbx))[0]
        ui = unreal.FbxImportUI()
        ui.import_mesh = True
        ui.import_as_skeletal = False
        ui.import_materials = False
        ui.import_textures = False
        ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
        ui.static_mesh_import_data.combine_meshes = True
        ui.static_mesh_import_data.auto_generate_collision = False
        tasks.append(task(fbx, dst, name, ui))
        tasks.append(task(tex, dst, "T_%s_D" % name[3:]))
    tools.import_asset_tasks(tasks)


def make_mi(dst, name, tex):
    p = "%s/MI_%s" % (dst, name)
    if eal.does_asset_exist(p):
        eal.delete_asset(p)
    mi = tools.create_asset("MI_" + name, dst,
                            unreal.MaterialInstanceConstant,
                            unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(
        mi, eal.load_asset("/Game/Environment/Materials/M_Env"))
    mel.set_material_instance_texture_parameter_value(mi, "BaseTex", tex)
    mel.set_material_instance_vector_parameter_value(
        mi, "Color", unreal.LinearColor(1, 1, 1, 1))
    mel.set_material_instance_scalar_parameter_value(mi, "Roughness", 0.8)
    mel.update_material_instance(mi)
    eal.save_loaded_asset(mi)
    return mi


def assign():
    res = {}
    for fbx, tex, dst in PROPS:
        name = os.path.splitext(os.path.basename(fbx))[0][3:]
        sm = eal.load_asset("%s/SM_%s" % (dst, name))
        mi = make_mi(dst, name, eal.load_asset("%s/T_%s_D" % (dst, name)))
        for i in range(len(sm.static_materials)):
            sm.set_material(i, mi)
        eal.save_loaded_asset(sm)
        b = sm.get_bounding_box()
        res[name] = [round(b.min.x), round(b.min.y), round(b.min.z),
                     round(b.max.x), round(b.max.y), round(b.max.z)]
    return res


res = {}
try:
    import_all()
    res["bounds"] = assign()
except Exception:
    res["err"] = traceback.format_exc()
json.dump(res, open(os.path.join(os.path.dirname(__file__), "out.json"),
                    "w"), indent=1)
