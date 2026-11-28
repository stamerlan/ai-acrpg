"""Her silhouette behind things the camera does not cut open.

Run in the editor: py "<this file>" with the map open. Safe to run
again. Walls, stalls, cars and trees stay whole when she walks behind
them (CameraOcclusionComponent only hides roofs), so she would be lost
there. This makes /Game/Materials/M_PP_Silhouette, a post process
material that tints the pixels where her custom depth (everything she
is and holds renders it, AChickenCharacter) lies behind the scene depth
orange, with a dark outline around it, and puts it on an unbound post
process volume, PP_Silhouette (Shared/Lighting). It does not save: save
the material in a separate run (saving right after a material compile
hung the editor), and the map if the volume was made.
"""
import json
import os
import traceback

import unreal

HERE = os.path.dirname(__file__.replace("\\", "/"))
PATH = "/Game/Materials/M_PP_Silhouette"
# Outline width in pixels, sampled in 8 directions
OUTLINE = 3.0
eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
res = {}


def node(mat, cls, x, y, **props):
    n = mel.create_material_expression(mat, cls, x, y)
    for key, value in props.items():
        n.set_editor_property(key, value)
    return n


def link(a, b, pin="", out=""):
    mel.connect_material_expressions(a, out, b, pin)


def depth(mat, source, uv, x, y):
    """The red channel of a scene texture (a depth in cm) at uv, or at
    this pixel when uv is None."""
    tex = node(mat, unreal.MaterialExpressionSceneTexture, x, y,
               scene_texture_id=source)
    if uv:
        link(uv, tex, "UVs")
    red = node(mat, unreal.MaterialExpressionComponentMask, x + 250, y,
               r=True, g=False, b=False, a=False)
    link(tex, red, out="Color")
    return red


def hidden(mat, uv, x, y):
    """(behind and drawn, drawn) at uv: drawn is 1 on her pixels, behind
    is 1 where she is more than 10 cm behind what the camera sees."""
    hers = depth(mat, unreal.SceneTextureId.PPI_CUSTOM_DEPTH, uv, x, y)
    seen = depth(mat, unreal.SceneTextureId.PPI_SCENE_DEPTH, uv, x,
                 y + 150)
    gap = node(mat, unreal.MaterialExpressionSubtract, x + 500, y)
    link(hers, gap, "A")
    link(seen, gap, "B")
    ramp = node(mat, unreal.MaterialExpressionMultiply, x + 650, y,
                const_b=0.2)
    link(gap, ramp, "A")
    less = node(mat, unreal.MaterialExpressionSubtract, x + 800, y,
                const_b=1.0)
    link(ramp, less, "A")
    behind = node(mat, unreal.MaterialExpressionSaturate, x + 950, y)
    link(less, behind)
    # Pixels without custom depth read a huge one: 0 there
    far = node(mat, unreal.MaterialExpressionSubtract, x + 500, y + 150,
               const_a=100000.0)
    link(hers, far, "B")
    drawn = node(mat, unreal.MaterialExpressionSaturate, x + 650, y + 150)
    link(far, drawn)
    both = node(mat, unreal.MaterialExpressionMultiply, x + 1100, y)
    link(behind, both, "A")
    link(drawn, both, "B")
    return both, drawn


try:
    if eal.does_asset_exist(PATH):
        mat = eal.load_asset(PATH)
        # One delete_all pass removes only about half of the nodes (it
        # skips every other one), so run it until none are left
        res["before"] = mel.get_num_material_expressions(mat)
        for _ in range(20):
            if not mel.get_num_material_expressions(mat):
                break
            mel.delete_all_material_expressions(mat)
        res["left"] = mel.get_num_material_expressions(mat)
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
        mat, unreal.MaterialExpressionSceneTexture, 1200, -400,
        scene_texture_id=unreal.SceneTextureId.PPI_POST_PROCESS_INPUT0)
    color = node(mat, unreal.MaterialExpressionComponentMask, 1450, -400,
                 r=True, g=True, b=True, a=False)
    link(scene, color, out="Color")
    fill, drawn = hidden(mat, None, -1200, 0)
    # The outline: pixels outside her that have a hidden pixel of hers
    # OUTLINE pixels away
    screen = node(mat, unreal.MaterialExpressionScreenPosition, -2000, 600)
    size = node(mat, unreal.MaterialExpressionViewSize, -2000, 800)
    step = node(mat, unreal.MaterialExpressionDivide, -1800, 800,
                const_a=OUTLINE)
    link(size, step, "B")
    near = None
    for i, (dx, dy) in enumerate(((1, 0), (-1, 0), (0, 1), (0, -1),
                                  (0.7, 0.7), (-0.7, 0.7), (0.7, -0.7),
                                  (-0.7, -0.7))):
        y = 600 + i * 400
        off = node(mat, unreal.MaterialExpressionConstant2Vector, -1800, y,
                   r=dx, g=dy)
        px = node(mat, unreal.MaterialExpressionMultiply, -1650, y)
        link(off, px, "A")
        link(step, px, "B")
        uv = node(mat, unreal.MaterialExpressionAdd, -1500, y)
        link(screen, uv, "A", "ViewportUV")
        link(px, uv, "B")
        there, _ = hidden(mat, uv, -1200, y)
        if near is None:
            near = there
        else:
            most = node(mat, unreal.MaterialExpressionMax, 200, y)
            link(near, most, "A")
            link(there, most, "B")
            near = most
    outside = node(mat, unreal.MaterialExpressionOneMinus, 400, 300)
    link(drawn, outside)
    edge = node(mat, unreal.MaterialExpressionMultiply, 550, 400)
    link(near, edge, "A")
    link(outside, edge, "B")
    line = node(mat, unreal.MaterialExpressionScalarParameter, 550, 550,
                parameter_name="OutlineAmount", default_value=1.0)
    edge_a = node(mat, unreal.MaterialExpressionMultiply, 700, 450)
    link(edge, edge_a, "A")
    link(line, edge_a, "B")
    amount = node(mat, unreal.MaterialExpressionScalarParameter, 550, 150,
                  parameter_name="Amount", default_value=0.9)
    fill_a = node(mat, unreal.MaterialExpressionMultiply, 700, 100)
    link(fill, fill_a, "A")
    link(amount, fill_a, "B")
    # The tint is a screen color: bring it to the scene's exposure. A
    # saturated orange: yellow got lost on the yellow tents and the
    # light green trees
    tint = node(mat, unreal.MaterialExpressionVectorParameter, 1200, -200,
                parameter_name="Tint",
                default_value=unreal.LinearColor(0.9, 0.2, 0.0, 1.0))
    lit = node(mat, unreal.MaterialExpressionEyeAdaptationInverse, 1450,
               -200)
    link(tint, lit, "LightValueInput")
    dark = node(mat, unreal.MaterialExpressionVectorParameter, 1200, 0,
                parameter_name="OutlineColor",
                default_value=unreal.LinearColor(0.02, 0.008, 0.0, 1.0))
    dark_lit = node(mat, unreal.MaterialExpressionEyeAdaptationInverse,
                    1450, 0)
    link(dark, dark_lit, "LightValueInput")
    tinted = node(mat, unreal.MaterialExpressionLinearInterpolate, 1700,
                  -300)
    link(color, tinted, "A")
    link(lit, tinted, "B")
    link(fill_a, tinted, "Alpha")
    out = node(mat, unreal.MaterialExpressionLinearInterpolate, 1900, -100)
    link(tinted, out, "A")
    link(dark_lit, out, "B")
    link(edge_a, out, "Alpha")
    mel.connect_material_property(out, "",
                                  unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    res["nodes"] = mel.get_num_material_expressions(mat)
    vol = next((a for a in eas.get_all_level_actors()
                if a.get_actor_label() == "PP_Silhouette"), None)
    if vol is None:
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
        res["volume"] = "made"
    res["ok"] = True
except Exception:
    res["err"] = traceback.format_exc()
json.dump(res, open(HERE + "/out.json", "w"), indent=1)
