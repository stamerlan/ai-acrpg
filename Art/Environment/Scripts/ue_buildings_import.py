"""Import the Meshy buildings and the border officer, with materials.

Run in the editor: py "<this file>" [Name ...]. Reads
Art/Environment/Buildings (blender_buildings_to_fbx.py,
blender_shops_open.py). Meshes go to /Game/Environment/Buildings/SM_<Name>,
each with one two-sided MI_Bld_<Name> on M_Env (BaseTex = T_<Name>_D),
Nanite off. A stall's canopy (SM_<Name>_Top) and a walk-in shop's parts
(SM_<Name>_Shell, SM_<Name>_Roof) share the material of the building;
their M_ShopInterior slot gets MI_Bld_ShopInterior (T_ShopInterior_D).
A roof keeps its imported collision box (UCX); the dressing scripts fit
a new box to the others. With names, imports only those buildings.
"""
import glob
import json
import os
import re
import sys
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


PARTS = ("_Top", "_Shell", "_Roof")
SHOPS = json.load(open(ART + "/Shops.json"))
res = {}
try:
    names = sys.argv[1:]
    meshes = [p for p in sorted(glob.glob(ART + "/SM_*.fbx"))
              if not names or re.sub(r"_(Top|Shell|Roof)$", "",
                                     os.path.basename(p)[3:-4]) in names]
    textures = [p for p in sorted(glob.glob(ART + "/T_*.png"))
                if not names or os.path.basename(p)[2:-6] in
                names + ["ShopInterior"]]
    tools.import_asset_tasks(
        [task(p, B, True) for p in meshes] +
        [task(p, B + "/Textures", False) for p in textures])
    inside_path = B + "/Materials/MI_Bld_ShopInterior"
    inside = None
    if eal.does_asset_exist(B + "/Textures/T_ShopInterior_D"):
        inside = eal.load_asset(inside_path) if eal.does_asset_exist(
            inside_path) else tools.create_asset(
            "MI_Bld_ShopInterior", B + "/Materials",
            unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew())
        mel.set_material_instance_parent(
            inside, eal.load_asset("/Game/Environment/Materials/M_Env"))
        mel.set_material_instance_texture_parameter_value(
            inside, "BaseTex",
            eal.load_asset(B + "/Textures/T_ShopInterior_D"))
        mel.set_material_instance_vector_parameter_value(
            inside, "Color", unreal.LinearColor(1, 1, 1, 1))
        mel.set_material_instance_scalar_parameter_value(
            inside, "Roughness", 0.7)
        overrides = inside.get_editor_property("base_property_overrides")
        overrides.set_editor_property("override_two_sided", True)
        overrides.set_editor_property("two_sided", True)
        inside.set_editor_property("base_property_overrides", overrides)
        mel.update_material_instance(inside)
        eal.save_loaded_asset(inside)
    for path in meshes:
        name = os.path.splitext(os.path.basename(path))[0][3:]
        if name.endswith(PARTS):
            continue
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
        for part in ("",) + PARTS:
            if eal.does_asset_exist(B + "/SM_" + name + part):
                mesh = eal.load_asset(B + "/SM_" + name + part)
                # The dressing scripts fit a new box where they need one
                if part != "_Roof":
                    unreal.EditorStaticMeshLibrary.remove_collisions(mesh)
                for i, slot in enumerate(mesh.static_materials):
                    inner = "ShopInterior" in str(slot.material_slot_name)
                    mesh.set_material(i, inside if inner and inside else mi)
                if part == "_Roof":
                    # The UCX box of the FBX, or the same box from
                    # Shops.json if the import dropped it
                    sml = unreal.EditorStaticMeshLibrary
                    if sml.get_simple_collision_count(mesh) == 0:
                        c = SHOPS[name]["box"]
                        body = mesh.get_editor_property("body_setup")
                        geom = body.get_editor_property("agg_geom")
                        box = unreal.KBoxElem()
                        box.set_editor_property(
                            "center", unreal.Vector(c[0], c[1], c[2]))
                        for axis, size in zip("xyz", c[3:]):
                            box.set_editor_property(axis, size)
                        geom.set_editor_property("box_elems", [box])
                        body.set_editor_property("agg_geom", geom)
                        mesh.set_editor_property("body_setup", body)
                    res[name + part] = sml.get_simple_collision_count(mesh)
                eal.save_loaded_asset(mesh)
        box = eal.load_asset(B + "/SM_" + name).get_bounding_box()
        res[name] = [round(box.max.x - box.min.x),
                     round(box.max.y - box.min.y),
                     round(box.max.z - box.min.z)]
    res["ok"] = True
except Exception:
    res["err"] = traceback.format_exc()
json.dump(res, open(HERE + "/out.json", "w"), indent=1)
