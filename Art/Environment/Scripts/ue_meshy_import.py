"""Import the Meshy vehicles and plants and the Civic, with materials.

Run in the editor: py "<this file>". Reads Art/Environment/Meshy
(blender_meshy_to_fbx.py) and Art/Environment/Civic (blender_civic.py).
Meshes go to /Game/Environment/Meshy/SM_<Name> (Nanite on for the
plants: the trees are about 10k triangles each and there are hundreds;
off for the vehicles, whose thin shells Nanite tore apart), each with one
MI_Meshy_<Name> on M_Env (BaseTex = T_<Name>_D), and
MI_Meshy_<Car>_<Paint> for the repaints in Meshy/Paints. The instances are
two-sided: the plants are flat leaf cards, and the vehicles have faces
that point inward (holes in the truck box otherwise). The Civic keeps its paths
in /Game/Environment/Civic; its car paint slot gets MI_Civic.
"""
import glob
import json
import os
import traceback

import unreal

ART = r"C:\Users\vvovchenko\repo\acrpg\Art\Environment"
M = "/Game/Environment/Meshy"
CIVIC = "/Game/Environment/Civic"
PLANTS = ("Pine", "Spruce", "Birch", "Oak", "Bush", "Fern")
eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()


def mesh_task(path, folder, nanite):
    ui = unreal.FbxImportUI()
    ui.import_mesh = True
    ui.import_as_skeletal = False
    ui.import_materials = False
    ui.import_textures = False
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    ui.static_mesh_import_data.combine_meshes = True
    ui.static_mesh_import_data.auto_generate_collision = False
    ui.static_mesh_import_data.build_nanite = nanite
    task = unreal.AssetImportTask()
    task.filename = path
    task.destination_path = folder
    task.destination_name = os.path.splitext(os.path.basename(path))[0]
    task.replace_existing = True
    task.automated = True
    task.save = True
    task.options = ui
    return task


def texture_task(path, folder):
    task = unreal.AssetImportTask()
    task.filename = path
    task.destination_path = folder
    task.destination_name = os.path.splitext(os.path.basename(path))[0]
    task.replace_existing = True
    task.automated = True
    task.save = True
    return task


def instance(name, folder, texture, two_sided=False, rough=0.85):
    """The M_Env instance, made once and updated in place after that."""
    path = folder + "/" + name
    made = eal.load_asset(path) if eal.does_asset_exist(path) else (
        tools.create_asset(name, folder, unreal.MaterialInstanceConstant,
                           unreal.MaterialInstanceConstantFactoryNew()))
    mel.set_material_instance_parent(
        made, eal.load_asset("/Game/Environment/Materials/M_Env"))
    mel.set_material_instance_texture_parameter_value(
        made, "BaseTex", eal.load_asset(texture))
    mel.set_material_instance_vector_parameter_value(
        made, "Color", unreal.LinearColor(1, 1, 1, 1))
    mel.set_material_instance_scalar_parameter_value(
        made, "Roughness", rough)
    if two_sided:
        overrides = made.get_editor_property("base_property_overrides")
        overrides.set_editor_property("override_two_sided", True)
        overrides.set_editor_property("two_sided", True)
        made.set_editor_property("base_property_overrides", overrides)
    mel.update_material_instance(made)
    eal.save_loaded_asset(made)
    return made


res = {}
try:
    tasks = []
    for path in sorted(glob.glob(os.path.join(ART, "Meshy", "*.fbx"))):
        name = os.path.splitext(os.path.basename(path))[0][3:]
        tasks.append(mesh_task(path, M, name in PLANTS))
    for path in sorted(glob.glob(os.path.join(ART, "Meshy", "*.png"))):
        tasks.append(texture_task(path, M + "/Textures"))
    paints = sorted(glob.glob(os.path.join(ART, "Meshy", "Paints", "*.png")))
    for path in paints:
        tasks.append(texture_task(path, M + "/Textures"))
    for name in ("SM_CivicBody", "SM_CivicTrunkLid"):
        tasks.append(mesh_task(
            os.path.join(ART, "Civic", name + ".fbx"), CIVIC, False))
    tasks.append(texture_task(
        os.path.join(ART, "Civic", "T_Civic_D.png"), CIVIC))
    tools.import_asset_tasks(tasks)
    for path in sorted(glob.glob(os.path.join(ART, "Meshy", "*.fbx"))):
        name = os.path.splitext(os.path.basename(path))[0][3:]
        made = instance("MI_Meshy_" + name, M + "/Materials",
                        M + "/Textures/T_" + name + "_D",
                        two_sided=True,
                        rough=0.85 if name in PLANTS else 0.45)
        mesh = eal.load_asset(M + "/SM_" + name)
        mesh.set_material(0, made)
        eal.save_loaded_asset(mesh)
        box = mesh.get_bounding_box()
        res[name] = [round(box.max.x - box.min.x), round(box.max.y - box.min.y),
                     round(box.max.z - box.min.z)]
    for path in paints:
        # T_<Car>_<Paint>_D: a repaint (blender_car_paints.py)
        name = os.path.splitext(os.path.basename(path))[0][2:-2]
        instance("MI_Meshy_" + name, M + "/Materials",
                 M + "/Textures/T_" + name + "_D", two_sided=True,
                 rough=0.45)
    res["paints"] = len(paints)
    paint = instance("MI_Civic", CIVIC, CIVIC + "/T_Civic_D",
                     two_sided=True, rough=0.35)
    for name in ("SM_CivicBody", "SM_CivicTrunkLid"):
        mesh = eal.load_asset(CIVIC + "/" + name)
        mesh.set_material(0, paint)
        eal.save_loaded_asset(mesh)
        box = mesh.get_bounding_box()
        res[name] = {
            "size": [round(box.max.x - box.min.x),
                     round(box.max.y - box.min.y),
                     round(box.max.z - box.min.z)],
            "slots": [str(slot.material_slot_name) + "=" + (
                slot.material_interface.get_name()
                if slot.material_interface else "None")
                for slot in mesh.static_materials]}
    res["ok"] = True
except Exception:
    res["err"] = traceback.format_exc()
json.dump(res, open(os.path.join(ART, "Scripts", "out.json"), "w"),
          indent=1)
