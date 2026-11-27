"""Stop 0 NPCs: Meshy rigs to UE FBX, clips on the shared cook skeleton.

Run headless, from the repo root:
  blender --background --python Art/NPCs/Scripts/blender_npc.py -- mesh
  blender --background --python Art/NPCs/Scripts/blender_npc.py -- clips
  blender --background --python Art/NPCs/Scripts/blender_npc.py -- check
"""
import bpy
import json
import math
import os
import sys
import numpy as np
import mathutils

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ART = os.path.join(ROOT, "NPCs")
sys.path.insert(0, os.path.join(ROOT, "Enemies", "Scripts"))
import blender_animtools as at  # noqa: E402
import blender_rigcheck as rc  # noqa: E402

NPCS = ["Kolya", "Halina", "Zbyszek", "Krasnal", "CornLady"]
SHAWARMAN = os.path.join(ROOT, "Enemies", "Shawarman", "Source",
                         "SK_Shawarman.blend")

# (clip, Meshy library action[, (first, last) frame at 30 fps]) - all
# loops, made in place
CLIPS = [
    ("A_NPC_Idle", "Idle"),
    ("A_NPC_IdleLook", "Idle_3"),
    ("A_NPC_TalkPassionate", "Talk_Passionately"),
    ("A_NPC_TalkHip", "Talk_with_Left_Hand_on_Hip"),
    ("A_NPC_TalkOpen", "Talk_with_Hands_Open"),
    ("A_NPC_TalkRightHand", "Talk_with_Right_Hand_Open"),
    ("A_NPC_SitIdle", "Chair_Sit_Idle_F"),
    ("A_NPC_SitDrink", "Sit_and_Drink"),
    # The quiet start of Sit and Drink: the cup stays on the lap. On Kolya
    # the drink itself lands on his forehead (bigger, lower head)
    ("A_NPC_SitHold", "Sit_and_Drink", (36, 96)),
    ("A_NPC_SitTalk", "Sitting_Answering_Questions"),
]

# Idle and talk clip per NPC, as ue_dress_npcs.py uses them, for the check
# renders. A_NPC_Idle turns the whole body 90 degrees and back: unused.
LOOK = {
    "Kolya": ("A_NPC_SitHold", "A_NPC_SitTalk"),
    "Halina": ("A_NPC_IdleLook", "A_NPC_TalkHip"),
    "Zbyszek": ("A_NPC_IdleLook", "A_NPC_TalkPassionate"),
    "Krasnal": ("A_NPC_IdleLook", "A_NPC_TalkHip"),
    "CornLady": ("A_NPC_IdleLook", "A_NPC_TalkRightHand"),
}
# Hand props: (object in Props/NPCProps.blend, bone, location in cm and
# XYZ euler in degrees in pose-bone space); BP_NPC HandProp in UE
HAND_PROPS = {"Kolya": ("SM_Thermos", "RightHand", (0, 8, 0), (0, 0, 0))}


def import_glb(path):
    before = set(bpy.data.objects)
    units = bpy.context.scene.unit_settings
    old = units.scale_length
    units.scale_length = 1.0
    bpy.ops.import_scene.gltf(filepath=path)
    units.scale_length = old
    return [o for o in bpy.data.objects if o not in before]


def fresh_scene():
    bpy.ops.wm.read_homefile(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 0.01
    return sc


def set_mode(arm, mode):
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode=mode)


def add_root(arm):
    set_mode(arm, 'EDIT')
    eb = arm.data.edit_bones
    root = eb.new("root")
    root.head = (0, 0, 0)
    root.tail = (0, 0, 20)
    eb["Hips"].parent = root
    set_mode(arm, 'OBJECT')


def fbx(path, objects, anim):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for o in bpy.data.objects:
        o.select_set(o in objects)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True,
        object_types={'ARMATURE', 'MESH'},
        apply_unit_scale=True, global_scale=1.0,
        apply_scale_options='FBX_SCALE_ALL',
        add_leaf_bones=False, use_armature_deform_only=False,
        primary_bone_axis='Y', secondary_bone_axis='X',
        bake_anim=anim, bake_anim_use_all_actions=False,
        bake_anim_use_nla_strips=False,
        bake_anim_force_startend_keying=True,
        bake_anim_simplify_factor=0.0,
        mesh_smooth_type='FACE', path_mode='STRIP')


def rest_pose(arm):
    ad = arm.animation_data
    if ad:
        ad.action = None
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.scale = (1, 1, 1)


def save_texture(mesh, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = next(n.image for n in mesh.data.materials[0].node_tree.nodes
               if n.type == 'TEX_IMAGE' and n.image)
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    if img.packed_file:
        img.unpack(method='REMOVE')
    img.filepath = path
    img.name = os.path.splitext(os.path.basename(path))[0]
    img.reload()


def build_mesh(name):
    """Rigged Meshy GLB to SK_<name>.blend and SK_<name>.fbx (cm)."""
    fresh_scene()
    objs = import_glb(os.path.join(ART, name, "Meshy",
                                   "SK_%s_Rigged.glb" % name))
    for o in list(objs):
        if o.type == 'MESH' and o.name.startswith("Icosphere"):
            bpy.data.objects.remove(o)
    arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
    report = rc.rig_report([arm, mesh])
    arm.name = arm.data.name = "Armature"
    arm.scale = (1, 1, 1)
    mesh.name = mesh.data.name = "SK_" + name
    mesh.data.materials[0].name = "M_" + name
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    add_root(arm)
    save_texture(mesh, os.path.join(ART, name, "Mesh",
                                    "T_%s_BaseColor.png" % name))
    bpy.context.view_layer.update()
    src = os.path.join(ART, name, "Source", "SK_%s.blend" % name)
    os.makedirs(os.path.dirname(src), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=src)
    rest_pose(arm)
    fbx(os.path.join(ART, name, "Mesh", "SK_%s.fbx" % name),
        [arm, mesh], anim=False)
    bones = {b.name: [round(v, 1) for v in b.head_local]
             for b in arm.data.bones}
    return {"tris": report["tris"], "height": round(mesh.dimensions.z, 1),
            "owned": {b: v[0] for b, v in report["bones"].items()},
            "Hips": bones["Hips"], "Head": bones["Head"]}


def build_clips():
    """Library clips on the Shawarman rig, loops in place, to FBX."""
    bpy.ops.wm.open_mainfile(filepath=SHAWARMAN)
    sc = bpy.context.scene
    arm = bpy.data.objects["Armature"]
    for o in list(bpy.data.objects):
        if o.type == 'MESH':
            bpy.data.objects.remove(o)
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    before = set(bpy.data.actions)
    objs = import_glb(os.path.join(ART, "Meshy", "Anims_NPC.glb"))
    fps = sc.render.fps
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
    lib = {a.name: a for a in bpy.data.actions if a not in before}
    report = {"fps": fps}
    for name, src, *rng in CLIPS:
        a = lib[src].copy()
        a.name = name
        a.use_fake_user = True
        f0, f1 = a.frame_range
        if f0 != 0:
            at.trim(a, f0, f1)
        if rng:
            at.trim(a, *rng[0])
        drift = at.remove_drift(arm, a)
        off = at.remove_offset(arm, a)
        at.crossfade_loop(arm, a, 8)
        report[name] = {"frames": [round(v) for v in a.frame_range],
                        "drift": drift, "offset": off}
    for a in list(lib.values()):
        bpy.data.actions.remove(a)
    sc.render.fps = fps
    src = os.path.join(ART, "Source", "NPC_Anims.blend")
    os.makedirs(os.path.dirname(src), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=src)
    for name, *_ in CLIPS:
        a = bpy.data.actions[name]
        ad = arm.animation_data or arm.animation_data_create()
        ad.action = a
        ad.action_slot = a.slots[0]
        sc.frame_start = 0
        sc.frame_end = int(a.frame_range[1])
        fbx(os.path.join(ART, "Anims", name + ".fbx"), [arm], anim=True)
    return report


def local_rest(b):
    m = b.matrix_local
    if b.parent:
        m = b.parent.matrix_local.inverted() @ m
    return m.to_quaternion()


def pose_like_ue(arm, src):
    """Pose arm as UE plays src's current pose on it: local rotations as
    they are, translations from arm's own rest pose (Skeleton retargeting)
    except root and Hips, Hips scaled by the hip height ratio."""
    for pb in arm.pose.bones:
        sp = src.pose.bones.get(pb.name)
        if not sp:
            continue
        b, sb = arm.data.bones[pb.name], src.data.bones[pb.name]
        rn, rs = local_rest(b), local_rest(sb)
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = (rn.inverted() @ rs @
                                  sp.matrix_basis.to_quaternion())
        pb.location = (0, 0, 0)
        if pb.name in ("root", "Hips"):
            k = (b.head_local.z / sb.head_local.z if pb.name == "Hips"
                 else 1.0)
            loc = rs @ sp.matrix_basis.to_translation() * k
            pb.location = rn.inverted() @ loc
    bpy.context.view_layer.update()


def render_sheet(path, rows, size=256, src=None, props=(),
                 center=(0, 0, 100), ortho=230):
    """rows: list of (arm, action, frames); one strip per row. With src
    (the Shawarman rig) the action plays on src and arm copies it the way
    UE retargets. props: (object, bone, matrix in pose-bone space)."""
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'
    sc.display.shading.color_type = 'TEXTURE'
    sc.display.shading.single_color = (0.1, 0.6, 0.2)
    sc.render.resolution_x = size
    sc.render.resolution_y = size
    sc.view_settings.view_transform = 'Standard'
    cam = bpy.data.objects.get("SheetCam")
    if not cam:
        cam = bpy.data.objects.new("SheetCam", bpy.data.cameras.new("C"))
        sc.collection.objects.link(cam)
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = ortho
    cam.data.clip_end = 5000
    sc.camera = cam
    c = mathutils.Vector(center)
    d = mathutils.Vector((-0.45, -1.0, 0.35)).normalized()
    cam.location = c + d * 800
    cam.rotation_euler = (c - cam.location).to_track_quat(
        '-Z', 'Y').to_euler()
    tile = os.path.join(os.path.dirname(path), "_tile.png")
    out_rows = []
    for arm, action, frames in rows:
        driven = src or arm
        ad = driven.animation_data or driven.animation_data_create()
        ad.action = action
        ad.action_slot = action.slots[0]
        tiles = []
        for f in frames:
            sc.frame_set(int(f))
            if src:
                pose_like_ue(arm, src)
            for o, bone, m in props:
                o.matrix_world = (arm.matrix_world @
                                  arm.pose.bones[bone].matrix @ m)
            sc.render.filepath = tile
            bpy.ops.render.render(write_still=True)
            img = bpy.data.images.load(tile, check_existing=False)
            tiles.append(np.array(img.pixels[:], dtype=np.float32)
                         .reshape(size, size, 4))
            bpy.data.images.remove(img)
        out_rows.append(np.concatenate(tiles, axis=1))
    sheet = np.concatenate(out_rows[::-1], axis=0)
    h, w = sheet.shape[:2]
    img = bpy.data.images.new("sheet", w, h, alpha=True)
    img.pixels[:] = sheet.ravel()
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    return path


def check(out_dir):
    """Per NPC: its idle and talk clip on its own mesh, 6 frames each,
    posed the way UE retargets the Shawarman clips, with its hand prop."""
    paths = []
    for name in NPCS:
        bpy.ops.wm.open_mainfile(
            filepath=os.path.join(ART, name, "Source", "SK_%s.blend" % name))
        arm = bpy.data.objects["Armature"]
        with bpy.data.libraries.load(os.path.join(
                ART, "Source", "NPC_Anims.blend")) as (lib, dst):
            dst.actions = list(LOOK[name])
            dst.objects = ["Armature"]
        src = dst.objects[0]
        src.name = "ShawarmanRig"
        bpy.context.scene.collection.objects.link(src)
        src.hide_render = True
        props = []
        if name in HAND_PROPS:
            prop, bone, loc, rot = HAND_PROPS[name]
            with bpy.data.libraries.load(os.path.join(
                    ART, "Props", "NPCProps.blend")) as (lib, pd):
                pd.objects = [prop]
            o = pd.objects[0]
            bpy.context.scene.collection.objects.link(o)
            m = (mathutils.Matrix.Translation(loc) @
                 mathutils.Euler([math.radians(v) for v in rot])
                 .to_matrix().to_4x4())
            props.append((o, bone, m))
        rows = []
        for a in dst.actions:
            n = int(a.frame_range[1])
            rows.append((arm, a, [round(n * i / 6) for i in range(6)]))
        paths.append(render_sheet(
            os.path.join(out_dir, "check_%s.png" % name), rows, src=src,
            props=props))
    return paths


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    what = args[0] if args else "mesh"
    if what == "mesh":
        names = args[1:] or NPCS
        result = {n: build_mesh(n) for n in names}
    elif what == "clips":
        result = build_clips()
    else:
        result = check(args[1])
    print("JSON" + json.dumps(result))
