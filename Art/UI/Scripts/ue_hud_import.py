"""Import the HUD pictures (shell, corn cob) as UI textures.

Run in the editor: py "<this file>". Imports Art/UI/HUD/T_HUD_<Name>.png
(made by key_icons.ps1) to /Game/UI/Textures with the UI group, no mips and
the editor icon compression (keeps the alpha), and writes out.json next to
this file.
"""
import glob
import json
import os
import traceback

import unreal

HUD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))), "HUD")
DST = "/Game/UI/Textures"
eal = unreal.EditorAssetLibrary
res = {"done": []}
try:
    tasks = []
    for f in sorted(glob.glob(os.path.join(HUD, "T_HUD_*.png"))):
        t = unreal.AssetImportTask()
        t.filename = f
        t.destination_path = DST
        t.destination_name = os.path.splitext(os.path.basename(f))[0]
        t.replace_existing = True
        t.automated = True
        t.save = False
        tasks.append(t)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    for t in tasks:
        tex = eal.load_asset(DST + "/" + t.destination_name)
        tex.set_editor_property("lod_group",
                                unreal.TextureGroup.TEXTUREGROUP_UI)
        tex.set_editor_property(
            "compression_settings",
            unreal.TextureCompressionSettings.TC_EDITOR_ICON)
        tex.set_editor_property(
            "mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        eal.save_loaded_asset(tex)
        res["done"].append(tex.get_path_name())
except Exception:
    res["err"] = traceback.format_exc()
json.dump(res, open(os.path.join(os.path.dirname(__file__), "out.json"),
                    "w"), indent=1)
