"""Import the Kenney FBX files and give them M_Env material instances.

Run in the editor: py "<this file>". Reads Art/Environment/Kenney/_fbx
and _textures. Meshes go to /Game/Environment/Kenney/<kit>/SM_<name>.
Kits with a colormap get one MI_Env_<kit> (BaseTex = the colormap,
nearest filtering); the flat-color kits (nature, furniture) get one
MI_Env_<kit>_<slot> per material slot with the slot's diffuse color.
M_Env keeps the camera occlusion cutout of M_Graybox.
"""
import glob
import json
import os
import re
import traceback

import unreal

ART = r"C:\Users\vvovchenko\repo\acrpg\Art\Environment\Kenney"
K = "/Game/Environment/Kenney"
# slot -> color override (Kenney's mint leaves are too cyan for Poland)
COLORS = {"leafsGreen": (0.30, 0.60, 0.20), "leafsDark": (0.17, 0.42, 0.17),
          "grass": (0.38, 0.66, 0.24)}
eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()


def import_all():
    tasks = []
    for f in sorted(glob.glob(os.path.join(ART, "_fbx", "*.fbx"))):
        kit, name = os.path.splitext(os.path.basename(f))[0].split("__")
        ui = unreal.FbxImportUI()
        ui.import_mesh = True
        ui.import_as_skeletal = False
        ui.import_materials = True
        ui.import_textures = False
        ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
        ui.static_mesh_import_data.combine_meshes = True
        ui.static_mesh_import_data.auto_generate_collision = False
        t = unreal.AssetImportTask()
        t.filename = f
        t.destination_path = K + "/" + kit
        t.destination_name = "SM_" + name
        t.replace_existing = True
        t.automated = True
        t.save = True
        t.options = ui
        tasks.append(t)
    for f in sorted(glob.glob(os.path.join(ART, "_textures", "*.png"))):
        t = unreal.AssetImportTask()
        t.filename = f
        t.destination_path = K + "/Textures"
        t.destination_name = os.path.splitext(os.path.basename(f))[0]
        t.replace_existing = True
        t.automated = True
        t.save = True
        tasks.append(t)
    tools.import_asset_tasks(tasks)


def make_mi(name, tex, col):
    p = K + "/Materials/" + name
    if eal.does_asset_exist(p):
        eal.delete_asset(p)
    mi = tools.create_asset(name, K + "/Materials",
                            unreal.MaterialInstanceConstant,
                            unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(
        mi, eal.load_asset("/Game/Environment/Materials/M_Env"))
    mel.set_material_instance_texture_parameter_value(mi, "BaseTex", tex)
    mel.set_material_instance_vector_parameter_value(
        mi, "Color", unreal.LinearColor(col[0], col[1], col[2], 1))
    mel.set_material_instance_scalar_parameter_value(mi, "Roughness", 0.85)
    mel.update_material_instance(mi)
    eal.save_loaded_asset(mi)
    return mi


def diffuse(m):
    if isinstance(m, unreal.MaterialInstance):
        for v in m.get_editor_property("vector_parameter_values"):
            if str(v.parameter_info.name) == "DiffuseColor":
                c = v.parameter_value
                return (c.r, c.g, c.b)
    return (1, 1, 1)


def assign():
    white = eal.load_asset("/Engine/EngineResources/WhiteSquareTexture")
    kits = sorted(set(p.split("/")[4] for p in eal.list_assets(K, True)
                      if "/SM_" in p))
    for kit in kits:
        tp = K + "/Textures/T_%s_colormap" % kit
        shared = None
        if eal.does_asset_exist(tp):
            tex = eal.load_asset(tp)
            tex.set_editor_property("filter", unreal.TextureFilter.TF_NEAREST)
            tex.set_editor_property(
                "mip_gen_settings",
                unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
            eal.save_loaded_asset(tex)
            shared = make_mi("MI_Env_" + kit, tex, (1, 1, 1))
        made = {}
        for p in eal.list_assets(K + "/" + kit, False):
            if "/SM_" not in p:
                continue
            sm = eal.load_asset(p)
            for i, s in enumerate(sm.static_materials):
                slot = re.sub(r"_[0-9]+$", "", str(s.material_slot_name))
                mi = shared
                if mi is None:
                    if slot not in made:
                        col = COLORS.get(slot) or diffuse(sm.get_material(i))
                        made[slot] = make_mi("MI_Env_%s_%s" % (kit, slot),
                                             white, col)
                    mi = made[slot]
                sm.set_material(i, mi)
            eal.save_loaded_asset(sm)
    for p in eal.list_assets(K, True):
        a = eal.find_asset_data(p)
        if str(a.asset_class_path.asset_name) == "MaterialInstanceConstant" \
                and "/Materials/" not in p:
            eal.delete_asset(p)


res = {}
try:
    import_all()
    assign()
    res["ok"] = True
except Exception:
    res["err"] = traceback.format_exc()
json.dump(res, open(os.path.join(ART, "..", "Scripts", "out.json"), "w"))
