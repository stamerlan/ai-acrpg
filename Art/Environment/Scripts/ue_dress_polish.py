"""Ground palette, car liveries and the day sun (Fable art review 3).

Run in the editor: py "<this file>", before ue_dress_lot.py (the lot
script uses the livery instances). M_Ground gets two parameters:
Detail lerps the photo texture toward the flat Flat color, so the
ground reads like the flat-shaded Kenney props, and NormalStrength
flattens the normal map. Each zone gets its own hue: cool gray pavers,
blue-gray asphalt, dark cinder lot, warm dirt only in the gnome field.
The car_kit colormap variants (T_car_kit_colormap_<paint>.png) repaint
the green body swatch. The sun moves to the north-west so the faces the
camera sees (it looks south) are lit.
"""
import json
import os
import traceback

import unreal

ART = r"C:\Users\vvovchenko\repo\acrpg\Art\Environment\Kenney\_textures"
M = "/Game/Environment/Materials/"
K = "/Game/Environment/Kenney/"
eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
# MI: (texture, tile cm, tint, flat color, detail, normal strength)
GROUND = {
    "MI_Ground_Grass": ("leafy_grass", 300, (0.75, 1.0, 0.6),
                        (0.08, 0.19, 0.04), 0.55, 0.5),
    "MI_Ground_Asphalt": ("worn_asphalt", 225, (0.6, 0.66, 0.78),
                          (0.07, 0.08, 0.10), 0.5, 0.4),
    "MI_Ground_Pavers": ("interlocking_concrete_pavers", 90,
                         (0.85, 0.92, 1.0), (0.36, 0.38, 0.42), 0.4, 0.35),
    "MI_Ground_Dirt": ("dirt", 300, (1, 1, 1), (0.28, 0.17, 0.09), 0.6,
                       0.6),
    "MI_Ground_Gravel": ("gravel_concrete_02", 300, (0.4, 0.4, 0.45),
                         (0.05, 0.05, 0.06), 0.35, 0.45),
    "MI_Ground_Concrete": ("concrete_pavement", 300, (0.9, 0.92, 0.95),
                           (0.30, 0.30, 0.31), 0.5, 0.4),
    "MI_Ground_Water": ("worn_asphalt", 500, (0.3, 0.5, 0.6),
                        (0.02, 0.07, 0.09), 0.08, 0.25),
}
PAINTS = ["Red", "Blue", "White", "Gray", "Orange", "Yellow"]


def extend_ground():
    """BaseColor = lerp(Flat, old, Detail); Normal = lerp(up, old, k)."""
    m = eal.load_asset(M + "M_Ground")
    if "Detail" in [str(n) for n in mel.get_scalar_parameter_names(m)]:
        return
    for prop, a_name, a_def, k_name in (
            (unreal.MaterialProperty.MP_BASE_COLOR, "Flat", None, "Detail"),
            (unreal.MaterialProperty.MP_NORMAL, None, (0, 0, 1),
             "NormalStrength")):
        old = mel.get_material_property_input_node(m, prop)
        out = mel.get_material_property_input_node_output_name(m, prop)
        lerp = mel.create_material_expression(
            m, unreal.MaterialExpressionLinearInterpolate, 200, 0)
        if a_name:
            a = mel.create_material_expression(
                m, unreal.MaterialExpressionVectorParameter, 0, -200)
            a.set_editor_property("parameter_name", a_name)
            a.set_editor_property("default_value",
                                  unreal.LinearColor(0.3, 0.3, 0.3, 1))
        else:
            a = mel.create_material_expression(
                m, unreal.MaterialExpressionConstant3Vector, 0, 200)
            a.set_editor_property("constant", unreal.LinearColor(*a_def, 1))
        k = mel.create_material_expression(
            m, unreal.MaterialExpressionScalarParameter, 0, 300)
        k.set_editor_property("parameter_name", k_name)
        k.set_editor_property("default_value", 1.0)
        mel.connect_material_expressions(a, "", lerp, "A")
        mel.connect_material_expressions(old, out, lerp, "B")
        mel.connect_material_expressions(k, "", lerp, "Alpha")
        mel.connect_material_property(lerp, "", prop)
    mel.recompile_material(m)
    eal.save_loaded_asset(m)


def ground_mis():
    parent = eal.load_asset(M + "M_Ground")
    for name, (tex, tile, tint, flat, detail, nk) in GROUND.items():
        p = M + name
        mi = eal.load_asset(p) if eal.does_asset_exist(p) else \
            tools.create_asset(name, M[:-1], unreal.MaterialInstanceConstant,
                               unreal.MaterialInstanceConstantFactoryNew())
        mel.set_material_instance_parent(mi, parent)
        t = "/Game/Environment/Textures/T_%s_" % tex
        mel.set_material_instance_texture_parameter_value(
            mi, "BaseTex", eal.load_asset(t + "D"))
        mel.set_material_instance_texture_parameter_value(
            mi, "NormalTex", eal.load_asset(t + "N"))
        for pn, v in (("TileSize", tile), ("Detail", detail),
                      ("NormalStrength", nk),
                      ("Roughness", 0.15 if "Water" in name else 0.9)):
            mel.set_material_instance_scalar_parameter_value(mi, pn, v)
        for pn, c in (("Color", tint), ("Flat", flat)):
            mel.set_material_instance_vector_parameter_value(
                mi, pn, unreal.LinearColor(c[0], c[1], c[2], 1))
        mel.update_material_instance(mi)
        eal.save_loaded_asset(mi)


def liveries():
    tasks = []
    for p in PAINTS:
        t = unreal.AssetImportTask()
        t.filename = os.path.join(ART, "T_car_kit_colormap_%s.png" % p)
        t.destination_path = K + "Textures"
        t.destination_name = "T_car_kit_colormap_" + p
        t.replace_existing = True
        t.automated = True
        t.save = True
        tasks.append(t)
    tools.import_asset_tasks(tasks)
    base = eal.load_asset(K + "Materials/MI_Env_car_kit")
    for p in PAINTS:
        tex = eal.load_asset(K + "Textures/T_car_kit_colormap_" + p)
        tex.set_editor_property("filter", unreal.TextureFilter.TF_NEAREST)
        tex.set_editor_property("mip_gen_settings",
                                unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        eal.save_loaded_asset(tex)
        name = "MI_Env_car_kit_" + p
        path = K + "Materials/" + name
        if eal.does_asset_exist(path):
            eal.delete_asset(path)
        mi = eal.duplicate_asset(base.get_path_name().split(".")[0], path)
        mel.set_material_instance_texture_parameter_value(mi, "BaseTex", tex)
        mel.update_material_instance(mi)
        eal.save_loaded_asset(mi)


def level():
    water = eal.load_asset(M + "MI_Ground_Water")
    concrete = eal.load_asset(M + "MI_Ground_Concrete")
    for a in eas.get_all_level_actors():
        n = a.get_actor_label()
        if n == "DirectionalLight":
            a.set_actor_rotation(unreal.Rotator(roll=0, pitch=-48, yaw=140),
                                 False)
        elif n == "SkyLight":
            c = a.get_component_by_class(unreal.SkyLightComponent)
            c.set_intensity(max(c.intensity, 1.6))
        if not isinstance(a, unreal.StaticMeshActor):
            continue
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            for i in range(c.get_num_materials()):
                mat = c.get_material(i)
                mn = mat.get_name() if mat else ""
                if mn == "MI_GB_Water":
                    c.set_material(i, water)
                elif mn == "MI_GB_Concrete" and n == "Lot_Ground":
                    c.set_material(i, concrete)


res = {}
try:
    extend_ground()
    ground_mis()
    liveries()
    level()
    res["ok"] = True
except Exception:
    res["err"] = traceback.format_exc()
json.dump(res, open(os.path.join(ART, "..", "..", "Scripts", "out.json"), "w"))
