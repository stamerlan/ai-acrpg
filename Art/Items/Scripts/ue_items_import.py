"""Import the backpack item icons and set them as the item pictures.

Run in the editor: py "<this file>". Imports Art/Items/T_Item_<Name>.png to
/Game/Items/Textures (UI group, no mips) and sets each as the Picture of
/Game/Items/DA_Item_<Name>. Writes out.json next to this file.
"""
import glob
import json
import os
import traceback

import unreal

ART = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
eal = unreal.EditorAssetLibrary
res = {"done": []}
try:
    tasks = []
    for f in sorted(glob.glob(os.path.join(ART, "T_Item_*.png"))):
        t = unreal.AssetImportTask()
        t.filename = f
        t.destination_path = "/Game/Items/Textures"
        t.destination_name = os.path.splitext(os.path.basename(f))[0]
        t.replace_existing = True
        t.automated = True
        t.save = False
        tasks.append(t)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    for t in tasks:
        name = t.destination_name
        tex = eal.load_asset("/Game/Items/Textures/" + name)
        tex.set_editor_property("lod_group",
                                unreal.TextureGroup.TEXTUREGROUP_UI)
        tex.set_editor_property(
            "compression_settings",
            unreal.TextureCompressionSettings.TC_EDITOR_ICON)
        tex.set_editor_property(
            "mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        eal.save_loaded_asset(tex)
        da = "/Game/Items/DA_Item_" + name[len("T_Item_"):]
        if eal.does_asset_exist(da):
            item = eal.load_asset(da)
            item.set_editor_property("picture", tex)
            eal.save_loaded_asset(item)
            res["done"].append(da)
except Exception:
    res["err"] = traceback.format_exc()
json.dump(res, open(os.path.join(os.path.dirname(__file__), "out.json"),
                    "w"), indent=1)
