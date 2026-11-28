"""Import the stop 0 NPCs into /Game/Characters/NPCs (editor Python).

  py ".../Art/NPCs/Scripts/ue_npcs_import.py"            meshes, clips, props
  py ".../Art/NPCs/Scripts/ue_npcs_import.py" materials  MIs on the meshes
  py ".../Art/NPCs/Scripts/ue_npcs_import.py" props      the hand props only
  py ".../Art/NPCs/Scripts/ue_npcs_import.py" anims      the clips only

The meshes use the cooks' SK_Shawarman_Skeleton, so the cook and NPC clips
play on every one of them. Writes out.json next to this file.
"""
import glob
import json
import os
import sys
import traceback
import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
DST = "/Game/Characters/NPCs"
SKEL = "/Game/Characters/Cooks/Meshes/SK_Shawarman_Skeleton"
NPCS = ["Kolya", "Halina", "Zbyszek", "Krasnal", "CornLady"]
OUT = os.path.join(HERE, "out.json")
eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
log = {"steps": []}


def step(name, value):
    log["steps"].append([name, value])
    with open(OUT, "w") as f:
        json.dump(log, f, indent=1)


def run(filename, dest, name, options=None):
    t = unreal.AssetImportTask()
    t.filename = filename
    t.destination_path = dest
    t.destination_name = name
    t.replace_existing = True
    t.automated = True
    t.save = True
    if options:
        t.options = options
    tools.import_asset_tasks([t])
    return list(t.imported_object_paths)


def fbx_options(skeleton, mesh):
    ui = unreal.FbxImportUI()
    ui.import_mesh = mesh
    ui.import_as_skeletal = True
    ui.import_animations = not mesh
    ui.import_materials = False
    ui.import_textures = False
    ui.create_physics_asset = False
    ui.skeleton = skeleton
    ui.mesh_type_to_import = (unreal.FBXImportType.FBXIT_SKELETAL_MESH if mesh
                              else unreal.FBXImportType.FBXIT_ANIMATION)
    if mesh:
        ui.skeletal_mesh_import_data.normal_import_method = \
            unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
    return ui


def prop_options():
    ui = unreal.FbxImportUI()
    ui.import_mesh = True
    ui.import_as_skeletal = False
    ui.import_animations = False
    ui.import_materials = True
    ui.import_textures = False
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    ui.static_mesh_import_data.combine_meshes = True
    ui.static_mesh_import_data.auto_generate_collision = False
    return ui


def import_all():
    skel = eal.load_asset(SKEL)
    for n in NPCS:
        step("T_" + n, run(f"{ART}/{n}/Mesh/T_{n}_BaseColor.png",
                           DST + "/Textures", f"T_{n}_BaseColor"))
        step("SK_" + n, run(f"{ART}/{n}/Mesh/SK_{n}.fbx", DST + "/Meshes",
                            "SK_" + n, fbx_options(skel, True)))
    anims()
    props()


def anims():
    skel = eal.load_asset(SKEL)
    for p in sorted(glob.glob(f"{ART}/Anims/A_NPC_*.fbx")):
        nm = os.path.splitext(os.path.basename(p))[0]
        step(nm, run(p, DST + "/Anims", nm, fbx_options(skel, False)))


def props():
    for p in sorted(glob.glob(f"{ART}/Props/SM_*.fbx")):
        nm = os.path.splitext(os.path.basename(p))[0]
        step(nm, run(p, DST + "/Props", nm, prop_options()))


def materials():
    parent = eal.load_asset("/Game/Characters/Cooks/Materials/M_Cook")
    for n in NPCS:
        path = f"{DST}/Materials/MI_{n}"
        mi = (eal.load_asset(path) if eal.does_asset_exist(path) else
              tools.create_asset(f"MI_{n}", DST + "/Materials",
                                 unreal.MaterialInstanceConstant,
                                 unreal.MaterialInstanceConstantFactoryNew()))
        mel.set_material_instance_parent(mi, parent)
        mel.set_material_instance_texture_parameter_value(
            mi, "BaseColor", eal.load_asset(f"{DST}/Textures/T_{n}_BaseColor"))
        eal.save_loaded_asset(mi)
        sk = eal.load_asset(f"{DST}/Meshes/SK_{n}")
        old = sk.get_editor_property("materials")
        mats = []
        for m in old:
            s = unreal.SkeletalMaterial()
            s.set_editor_property("material_interface", mi)
            s.set_editor_property("material_slot_name",
                                  m.get_editor_property("material_slot_name"))
            mats.append(s)
        sk.set_editor_property("materials", mats)
        eal.save_loaded_asset(sk)
        step("MI_" + n, len(mats))


try:
    if "materials" in sys.argv[1:]:
        materials()
    elif "props" in sys.argv[1:]:
        props()
    elif "anims" in sys.argv[1:]:
        anims()
    else:
        import_all()
    step("done", True)
except Exception:
    step("error", traceback.format_exc())
