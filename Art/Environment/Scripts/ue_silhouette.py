"""Her silhouette behind things the camera does not cut open.

Run in the editor: py "<this file>" with the map open. Safe to run
again. Buildings, her car and poles keep whole when she walks behind
them (see CameraOcclusionComponent, tag NoOcclusionCutout), so she
would be lost there. This makes /Game/Materials/M_PP_Silhouette, a post
process material that tints the pixels where her custom depth (her mesh
renders it, AChickenCharacter) lies behind the scene depth, and puts it
on an unbound post process volume, PP_Silhouette (Shared/Lighting).
"""
import json
import os
import traceback

import unreal

HERE = os.path.dirname(__file__.replace("\\", "/"))
PATH = "/Game/Materials/M_PP_Silhouette"
eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
res = {}


def node(mat, cls, x, y, **props):
    n = mel.create_material_expression(mat, cls, x, y)
    for key, value in props.items():
        n.set_editor_property(key, value)
    return n


def depth(mat, source, y):
    """The red channel of a scene texture: a depth in cm."""
    tex = node(mat, unreal.MaterialExpressionSceneTexture, -1200, y,
               scene_texture_id=source)
    red = node(mat, unreal.MaterialExpressionComponentMask, -950, y,
               r=True, g=False, b=False, a=False)
    mel.connect_material_expressions(tex, "Color", red, "")
    return red


try:
    if eal.does_asset_exist(PATH):
        mat = eal.load_asset(PATH)
        mel.delete_all_material_expressions(mat)
    else:
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "M_PP_Silhouette", "/Game/Materials", unreal.Material,
            unreal.MaterialFactoryNew())
    mat.set_editor_property("material_domain",
                            unreal.MaterialDomain.MD_POST_PROCESS)
    # Before the temporal upscale: the depths still match the color
    mat.set_editor_property(
        "blendable_location",
        unreal.BlendableLocation.BL_SCENE_COLOR_BEFORE_DOF)
    scene = node(
        mat, unreal.MaterialExpressionSceneTexture, -700, -200,
        scene_texture_id=unreal.SceneTextureId.PPI_POST_PROCESS_INPUT0)
    color = node(mat, unreal.MaterialExpressionComponentMask, -450, -200,
                 r=True, g=True, b=True, a=False)
    mel.connect_material_expressions(scene, "Color", color, "")
    hers = depth(mat, unreal.SceneTextureId.PPI_CUSTOM_DEPTH, 100)
    seen = depth(mat, unreal.SceneTextureId.PPI_SCENE_DEPTH, 300)
    # 1 where she is more than 10 cm behind what the camera sees
    gap = node(mat, unreal.MaterialExpressionSubtract, -700, 150)
    mel.connect_material_expressions(hers, "", gap, "A")
    mel.connect_material_expressions(seen, "", gap, "B")
    ramp = node(mat, unreal.MaterialExpressionMultiply, -550, 150,
                const_b=0.2)
    mel.connect_material_expressions(gap, "", ramp, "A")
    less = node(mat, unreal.MaterialExpressionSubtract, -400, 150,
                const_b=1.0)
    mel.connect_material_expressions(ramp, "", less, "A")
    behind = node(mat, unreal.MaterialExpressionSaturate, -250, 150)
    mel.connect_material_expressions(less, "", behind, "")
    # Pixels without custom depth read a huge one: 0 there
    far = node(mat, unreal.MaterialExpressionSubtract, -700, 400,
               const_a=100000.0)
    mel.connect_material_expressions(hers, "", far, "B")
    drawn = node(mat, unreal.MaterialExpressionSaturate, -550, 400)
    mel.connect_material_expressions(far, "", drawn, "")
    mask = node(mat, unreal.MaterialExpressionMultiply, -100, 250)
    mel.connect_material_expressions(behind, "", mask, "A")
    mel.connect_material_expressions(drawn, "", mask, "B")
    amount = node(mat, unreal.MaterialExpressionScalarParameter, -100, 450,
                  parameter_name="Amount", default_value=0.85)
    alpha = node(mat, unreal.MaterialExpressionMultiply, 50, 300)
    mel.connect_material_expressions(mask, "", alpha, "A")
    mel.connect_material_expressions(amount, "", alpha, "B")
    # The tint is a screen color: bring it to the scene's exposure
    tint = node(mat, unreal.MaterialExpressionVectorParameter, -400, -450,
                parameter_name="Tint",
                default_value=unreal.LinearColor(1.0, 0.7, 0.05, 1.0))
    lit = node(mat, unreal.MaterialExpressionEyeAdaptationInverse, -150,
               -450)
    mel.connect_material_expressions(tint, "", lit, "LightValueInput")
    out = node(mat, unreal.MaterialExpressionLinearInterpolate, 250, 0)
    mel.connect_material_expressions(color, "", out, "A")
    mel.connect_material_expressions(lit, "", out, "B")
    mel.connect_material_expressions(alpha, "", out, "Alpha")
    mel.connect_material_property(out, "",
                                  unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    res["nodes"] = mel.get_num_material_expressions(mat)
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == "PP_Silhouette":
            eas.destroy_actor(a)
    vol = eas.spawn_actor_from_class(unreal.PostProcessVolume,
                                     unreal.Vector(0, 0, -1000))
    vol.set_actor_label("PP_Silhouette")
    vol.set_folder_path("Shared/Lighting")
    vol.set_editor_property("unbound", True)
    settings = vol.get_editor_property("settings")
    settings.set_editor_property(
        "weighted_blendables", unreal.WeightedBlendables(
            array=[unreal.WeightedBlendable(weight=1.0, object=mat)]))
    vol.set_editor_property("settings", settings)
    res["ok"] = True
except Exception:
    res["err"] = traceback.format_exc()
json.dump(res, open(HERE + "/out.json", "w"), indent=1)
