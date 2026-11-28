"""Put the stop 0 NPC models into L0_BorderBazaar (editor Python).

Deletes and re-places the ArtNPC_ actors (BP_NPC); NPC names as arguments
(py "<this file>" Kotlet Officer) re-place only those. The camera looks
south, so every NPC stands in the open, facing north, where she comes
from: a seller under a canopy or with his back to the camera is not seen.
Each MK_NPC_ marker moves to its NPC (it keeps the BPC_Interactable, so
the dialogs work as before) and its own meshes and label are hidden.
BP_NPC plays the idle clip, blends to the talk clip while the dialog's
active node belongs to its Participant, holds up to two props and blocks
her with a capsule. Run ue_layout_border.py (sellers) and
ue_dress_stalls.py first. Writes out.json here. Saves nothing: check the
result, then save the level.
"""
import json
import os
import sys
import traceback
import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out.json")
N = "/Game/Characters/NPCs/"
C = "/Game/Characters/Cooks/"
A = N + "Anims/A_NPC_"
P = N + "Props/SM_"
eal = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ml = unreal.MathLibrary

# mesh, mat: the body. idle, talk: the clips. at: (x, y, yaw).
# marker: False leaves the marker where it is (Halina's talk range is
# fitted to the yard in front of her window), None: the NPC has no marker
# (folder: its outliner folder, no data layer). block: the capsule's
# (radius, half height), None for no collision. show: story conditions
# (Type, Id, Value), the NPC is hidden while one fails.
NPCS = {
    # On a crate on the road verge, across the lane from his truck's cab
    "Kolya": dict(mesh=N + "Meshes/SK_Kolya", idle=A + "SitLook",
                  talk=A + "SitTalk", at=(2940, -800, 0), block=(45, 65)),
    # At her window: 20 cm behind the wall, so the lintel does not hide
    # her head from the camera
    "Halina": dict(mesh=N + "Meshes/SK_Halina", idle=A + "IdleLook",
                   talk=A + "TalkHip", at=(-32, 1860, 0), marker=False,
                   block=None),
    # In front of the west corner of his stall, by the alley to the
    # office, holding a stamp up
    "Zbyszek": dict(mesh=N + "Meshes/SK_Zbyszek", idle=A + "IdleRaise",
                    talk=A + "TalkPassionate", at=(1490, 740, 0)),
    # Beside his stall, by the way to the gnome field
    "Krasnal": dict(mesh=N + "Meshes/SK_Krasnal", idle=A + "IdleLook",
                    talk=A + "TalkHip", at=(1440, -650, 0)),
    # In front of the west corner of her stall, holding a cob out
    "CornLady": dict(mesh=N + "Meshes/SK_CornLady", idle=A + "IdleOffer",
                     talk=A + "TalkRightHand", at=(1485, -1765, 0)),
    # The kebab stand's cook, between its two tables. No dialog. He is
    # gone when Halina calls: the first fight's cooks come out of the stand
    "KebabShawarman": dict(mesh=C + "Meshes/SK_Shawarman",
                           mat=C + "Materials/MI_Shawarman_A",
                           idle=C + "Anims/A_Shawarman_Idle",
                           talk=C + "Anims/A_Shawarman_Idle",
                           at=(1505, -1160, 0),
                           show=[("QUEST_IS_NOT", "q_car_trouble",
                                  "office")]),
    # Sergeant Kotlet by the stopped car (KOTLET of ue_dress_border.py),
    # eating a kebab while he waits, in the day only (his marker's layer)
    "Kotlet": dict(mesh=N + "Meshes/SK_Officer", idle=A + "StandDrink",
                   talk=A + "TalkHip", at=(3000, -2640, 0)),
    # The officer checking papers at the head of the truck queue, on the
    # verge north-west of the first cab and facing it, reading his
    # clipboard. No marker and no dialog: he is in both shifts
    "Officer": dict(mesh=N + "Meshes/SK_Officer", idle=A + "IdleRead",
                    talk=A + "IdleRead", at=(3540, -2050, 90),
                    marker=None, folder="Art/Shared/TruckQueue"),
}
# Kolya's seat: (mesh, offset in his space, scale)
SEATS = {"Kolya": ("/Game/Environment/Kenney/survival_kit/SM_box",
                   (-24, 0, 0), (2.2, 2.6, 1.8))}
# A small warm lamp: (offset in the NPC's space, intensity, radius). The
# office is dark behind Halina's window
LIGHTS = {"Halina": ((14, 0, 185), 600.0, 160.0)}
# Graybox markers an NPC replaces (no component of theirs is used)
HIDE = ["MK_Interact_OfficeWindow"]
# Held props, at most two an NPC: (mesh, bone, axes, offset, scale).
# The prop is turned so that, in the NPC's idle pose, its first axis is
# world up and its second one points where the NPC looks (HANDS below),
# with its origin in the palm; offset moves it in its own space. Axes
# "RAW" takes offset as the (location, (roll, pitch, yaw)) in the bone's
# space instead: the cook's are BP_Shawarman's (SetupBody, read in PIE).
PROPS = {
    "Kolya": [(P + "Thermos", "RightHand", "ZX", (0, 0, 0), 1.0)],
    "Halina": [(P + "Stamp", "RightHand", "ZX", (0, 0, 0), 1.0),
               (C + "Props/SM_MiniKebab", "LeftHand", "XZ", (2, 0, 0), 1.3)],
    "Zbyszek": [(P + "Stamp", "RightHand", "ZX", (0, 0, 0), 1.5)],
    "Krasnal": [(P + "GnomeSign", "RightHand", "ZX", (0, 0, 0), 1.0),
                ("/Game/Props/Gnome/SM_Gnome", "LeftHand", "ZX",
                 (8, 0, -24), 1.0)],
    "CornLady": [(P + "TongsCorn", "RightHand", "ZX", (0, 0, 0), 1.0)],
    "Kotlet": [(C + "Props/SM_MiniKebab", "LeftHand", "XZ", (2, 0, 0), 1.3)],
    "Officer": [(P + "Clipboard", "RightHand", "ZX", (0, 0, 0), 1.0)],
    # Honing his knife, as the enemy Shawarman does in his idle
    "KebabShawarman": [
        (C + "Props/SM_DonerKnife", "RightHand", "RAW",
         ((-1.4, -6.9, 0.9), (177.5, 54.7, -1.5)), 1.0),
        (C + "Props/SM_SharpeningSteel", "LeftHand", "RAW",
         ((2.1, -8.0, 0.6), (-169.6, 54.1, -168.8)), 1.0)],
}
PALM = (0, -8, 0)  # in a hand bone's space: 8 cm from the wrist
# World up and the NPC's forward in a hand bone's space in the idle
# clip, measured in PIE (get_socket_transform, unrotate the two vectors;
# the NPC must be on screen or its pose does not tick). They depend on
# the clip only: the retargeted bone rotations are the same on every body
HANDS = {
    "A_NPC_IdleLook": {
        "RightHand": ((0.23, 0.95, -0.17), (0.89, -0.14, 0.44)),
        "LeftHand": ((-0.37, 0.91, -0.17), (-0.87, -0.27, 0.41))},
    # blender_npc.py derive prints the right hand of its clips
    "A_NPC_IdleRaise": {
        "RightHand": ((0.77, -0.5, 0.4), (-0.6, -0.78, 0.18))},
    "A_NPC_IdleOffer": {
        "RightHand": ((0.97, -0.22, 0.14), (-0.19, -0.96, -0.2))},
    "A_NPC_IdleRead": {
        "RightHand": ((0.82, 0.53, 0.22), (0.54, -0.84, 0.02))},
    # The hand with the cup moves: the pose it holds longest
    "A_NPC_SitLook": {
        "RightHand": ((0.18, 0.55, -0.82), (1, 0, 0))},
    # The left hand holds the kebab at the chest, lifts it to bite (frames
    # 80-160): the held pose
    "A_NPC_StandDrink": {
        "LeftHand": ((-0.62, 0.03, 0.78), (-0.64, -0.59, -0.49))},
}
res = {}


def hide_marker(m):
    for c in (m.get_components_by_class(unreal.StaticMeshComponent) +
              m.get_components_by_class(unreal.TextRenderComponent)):
        c.modify()
        c.set_collision_profile_name("NoCollision")
        c.set_visibility(False)
        c.set_editor_property("hidden_in_game", True)


def condition(t, i, v):
    c = unreal.StoryCondition()
    c.set_editor_property("type", getattr(unreal.StoryConditionType, t))
    c.set_editor_property("id", i)
    c.set_editor_property("value", v)
    return c


def hold(a, idle, slot, mesh, bone, axes, offset, scale):
    if axes == "RAW":
        loc = unreal.Vector(*offset[0])
        rot = unreal.Rotator(roll=offset[1][0], pitch=offset[1][1],
                             yaw=offset[1][2])
    else:
        up, fwd = HANDS[idle.rsplit("/", 1)[1]][bone]
        make = ml.make_rot_from_zx if axes == "ZX" else ml.make_rot_from_xz
        rot = make(unreal.Vector(*up), unreal.Vector(*fwd))
        loc = unreal.Vector(*PALM) + rot.quaternion().rotate_vector(
            unreal.Vector(*offset) * scale)
    hp = a.get_editor_property("HandProp" if slot == 0 else "HandProp2")
    hp.set_static_mesh(eal.load_asset(mesh))
    hp.set_relative_location_and_rotation(loc, rot, False, False)
    hp.set_relative_scale3d(unreal.Vector(scale, scale, scale))


try:
    # NPC names after the file name re-place only those
    only = sys.argv[1:] or list(NPCS)
    for a in list(eas.get_all_level_actors()):
        kind, _, name = a.get_actor_label().partition("_")
        if kind in ("ArtNPC", "ArtNPCSeat", "ArtNPCLight") and name in only:
            eas.destroy_actor(a)
    labels = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
    cls = unreal.EditorAssetLibrary.load_blueprint_class(N + "BP_NPC")
    for name, d in NPCS.items():
        if name not in only:
            continue
        x, y, yaw = d["at"]
        rot = unreal.Rotator(roll=0, pitch=0, yaw=yaw)
        if d.get("marker", True) is None:
            loc = unreal.Vector(x, y, 0)
            folder = d["folder"]
            layers = []
        else:
            m = labels["MK_NPC_" + name]
            loc = unreal.Vector(x, y, m.get_actor_location().z)
            m.modify()
            if d.get("marker", True):
                m.set_actor_location_and_rotation(loc, rot, False, False)
            hide_marker(m)
            folder = str(m.get_folder_path()).replace("Markers/NPC", "NPCs")
            layers = m.get_editor_property("data_layer_assets")
        a = eas.spawn_actor_from_class(cls, loc, rot)
        a.set_actor_label("ArtNPC_" + name)
        a.set_folder_path(folder)
        a.set_editor_property("data_layer_assets", layers)
        # The actor's own properties first: setting one reruns the
        # construction and drops what was set on its components
        props = PROPS.get(name, [])
        a.set_editor_property("Participant", name)
        a.set_editor_property("IdleAnim", eal.load_asset(d["idle"]))
        a.set_editor_property("TalkAnim", eal.load_asset(d["talk"]))
        a.set_editor_property("ShowWhile", [
            condition(*c) for c in d.get("show", [])])
        for i, prop in enumerate(props):
            a.set_editor_property("PropSocket2" if i else "PropSocket",
                                  prop[1])
        body = a.get_editor_property("Body")
        body.set_skeletal_mesh_asset(eal.load_asset(d["mesh"]))
        if d.get("mat"):
            body.set_material(0, eal.load_asset(d["mat"]))
        block = a.get_editor_property("Block")
        size = d.get("block", (32, 85))
        if size:
            block.set_capsule_size(size[0], size[1])
            block.set_relative_location(unreal.Vector(0, 0, size[1]),
                                        False, False)
        else:
            block.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        for i, prop in enumerate(props):
            hold(a, d["idle"], i, *prop)
        if name in SEATS:
            sm, off, sc = SEATS[name]
            s = eas.spawn_actor_from_class(
                unreal.StaticMeshActor,
                a.get_actor_transform().transform_location(
                    unreal.Vector(*off)), rot)
            s.set_actor_label("ArtNPCSeat_" + name)
            s.set_folder_path(a.get_folder_path())
            s.set_editor_property("data_layer_assets", layers)
            smc = s.static_mesh_component
            smc.set_static_mesh(eal.load_asset(sm))
            s.set_actor_scale3d(unreal.Vector(*sc))
            smc.set_editor_property("can_ever_affect_navigation", False)
        if name in LIGHTS:
            off, power, radius = LIGHTS[name]
            lamp = eas.spawn_actor_from_class(
                unreal.PointLight,
                a.get_actor_transform().transform_location(
                    unreal.Vector(*off)), rot)
            lamp.set_actor_label("ArtNPCLight_" + name)
            lamp.set_folder_path(a.get_folder_path())
            lamp.set_editor_property("data_layer_assets", layers)
            lc = lamp.point_light_component
            lc.set_editor_property("intensity_units",
                                   unreal.LightUnits.UNITLESS)
            lc.set_intensity(power)
            lc.set_attenuation_radius(radius)
            lc.set_light_color(unreal.LinearColor(1.0, 0.82, 0.6, 1.0))
            lc.set_cast_shadows(False)
        res[name] = {"at": [x, y, yaw],
                     "layers": [str(l.get_name()) for l in layers]}
    for label in HIDE:
        labels[label].modify()
        hide_marker(labels[label])
    res["ok"] = True
except Exception:
    res["error"] = traceback.format_exc()
with open(OUT, "w") as f:
    json.dump(res, f, indent=1)
