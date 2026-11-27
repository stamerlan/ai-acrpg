"""Import the Meshy buildings and the border officer, with materials.

Run in the editor: py "<this file>". Reads Art/Environment/Buildings
(blender_buildings_to_fbx.py). Meshes go to
/Game/Environment/Buildings/SM_<Name>, each with one two-sided
MI_Bld_<Name> on M_Env (BaseTex = T_<Name>_D), Nanite off.
"""
import glob
import json
import os
import traceback

import unreal

HERE = os.path.dirname(__file__.replace("\\", "/"))
ART = os.path.dirname(HERE) + "/Buildings"
B = "/Game/Environment/Buildings"
eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()


def task(path, folder, mesh):
    made = unreal.AssetImportTask()
    made.filename = path
    made.destination_path = folder
    made.destination_name = os.path.splitext(os.path.basename(path))[0]
    made.replace_existing = True
    made.automated = True
    made.save = True
    if mesh:
        ui = unreal.FbxImportUI()
        ui.import_mesh = True
        ui.import_as_skeletal = False
        ui.import_materials = False
        ui.import_textures = False
        ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
        ui.static_mesh_import_data.combine_meshes = True
        ui.static_mesh_import_data.auto_generate_collision = False
        ui.static_mesh_import_data.build_nanite = False
        made.options = ui
    return made


res = {}
try:
    meshes = sorted(glob.glob(ART + "/SM_*.fbx"))
    tools.import_asset_tasks(
        [task(p, B, True) for p in meshes] +
        [task(p, B + "/Textures", False)
         for p in sorted(glob.glob(ART + "/T_*.png"))])
    for path in meshes:
        name = os.path.splitext(os.path.basename(path))[0][3:]
        mi_path = B + "/Materials/MI_Bld_" + name
        mi = eal.load_asset(mi_path) if eal.does_asset_exist(mi_path) else (
            tools.create_asset("MI_Bld_" + name, B + "/Materials",
                               unreal.MaterialInstanceConstant,
                               unreal.MaterialInstanceConstantFactoryNew()))
        mel.set_material_instance_parent(
            mi, eal.load_asset("/Game/Environment/Materials/M_Env"))
        mel.set_material_instance_texture_parameter_value(
            mi, "BaseTex", eal.load_asset(B + "/Textures/T_" + name + "_D"))
        # Stall tarps wash out in the sun at full brightness
        tint = 0.75 if name.startswith("Stall_") else 1.0
        mel.set_material_instance_vector_parameter_value(
            mi, "Color", unreal.LinearColor(tint, tint, tint, 1))
        mel.set_material_instance_scalar_parameter_value(
            mi, "Roughness", 0.8)
        overrides = mi.get_editor_property("base_property_overrides")
        overrides.set_editor_property("override_two_sided", True)
        overrides.set_editor_property("two_sided", True)
        mi.set_editor_property("base_property_overrides", overrides)
        mel.update_material_instance(mi)
        eal.save_loaded_asset(mi)
        mesh = eal.load_asset(B + "/SM_" + name)
        mesh.set_material(0, mi)
        eal.save_loaded_asset(mesh)
        box = mesh.get_bounding_box()
        res[name] = [round(box.max.x - box.min.x),
                     round(box.max.y - box.min.y),
                     round(box.max.z - box.min.z)]
    res["ok"] = True
except Exception:
    res["err"] = traceback.format_exc()
json.dump(res, open(HERE + "/out.json", "w"), indent=1)
