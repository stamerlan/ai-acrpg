"""Put the stop 0 NPC models over their markers (editor Python).

Deletes and re-places the ArtNPC_ actors (BP_NPC) at the MK_NPC_ markers,
copies each marker's data layers and hides the marker's own meshes and
label; the marker keeps its BPC_Interactable, so dialogs work as before.
BP_NPC plays the idle clip and blends to the talk clip while the dialog's
active node belongs to its Participant. Writes out.json here.
Saves nothing: check the result, then save the level.
"""
import json
import math
import os
import traceback
import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out.json")
N = "/Game/Characters/NPCs/"
C = "/Game/Characters/Cooks/"
A = N + "Anims/A_NPC_"
eal = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# marker: (mesh, material or None, idle, talk, place, offset, extra yaw)
# place "marker" stands on the marker, "interact" on its talk point
# (the stall sellers, behind their counters); the offset in marker space
# is added to either.
NPCS = {
    "Kolya": (N + "Meshes/SK_Kolya", None, A + "SitHold", A + "SitTalk",
              "marker", (0, 0, 0), 0),
    "Halina": (N + "Meshes/SK_Halina", None, A + "IdleLook", A + "TalkHip",
               "marker", (0, 0, 0), 0),
    "Zbyszek": (N + "Meshes/SK_Zbyszek", None, A + "IdleLook",
                A + "TalkPassionate", "interact", (0, 0, 0), 0),
    "Krasnal": (N + "Meshes/SK_Krasnal", None, A + "IdleLook", A + "TalkHip",
                "marker", (0, 0, 0), 0),
    # Beside the folding chair of her stall, not behind it
    "CornLady": (N + "Meshes/SK_CornLady", None, A + "IdleLook",
                 A + "TalkRightHand", "interact", (0, 55, 0), 0),
    "KebabShawarman": (C + "Meshes/SK_Shawarman",
                       C + "Materials/MI_Shawarman_A",
                       C + "Anims/A_Shawarman_Idle",
                       C + "Anims/A_Shawarman_Idle", "marker", (0, 0, 0), 0),
}
# Shown only while these story conditions pass (Type, Id, Value)
SHOW_WHILE = {
    # The cook runs out of the stand when Halina calls; the stand is
    # empty after the fight
    "KebabShawarman": [("QUEST_IS_NOT", "q_car_trouble", "office")],
}
# Kolya sits on a crate by his truck: (mesh, offset, scale)
SEATS = {"Kolya": ("/Game/Environment/Kenney/survival_kit/SM_box",
                   (-20, 0, 0), (1.3, 1.3, 1.8))}
# Held props: (mesh, socket, location, up) in UE socket space. "up" is the
# prop's +Z: world up in the socket while Kolya holds the cup on his lap
# in A_NPC_SitHold (measured in PIE), so the thermos stands upright
HAND_PROPS = {"Kolya": (N + "Props/SM_Thermos", "RightHand", (0, -8, 0),
                        (0.18, 0.55, -0.82))}
res = {}


def hide_marker(m):
    for c in (m.get_components_by_class(unreal.StaticMeshComponent) +
              m.get_components_by_class(unreal.TextRenderComponent)):
        c.modify()
        c.set_collision_profile_name("NoCollision")
        c.set_visibility(False)
        c.set_editor_property("hidden_in_game", True)


def to_world(m, off):
    yaw = math.radians(m.get_actor_rotation().yaw)
    ca, sa = math.cos(yaw), math.sin(yaw)
    lo = m.get_actor_location()
    return unreal.Vector(lo.x + off[0] * ca - off[1] * sa,
                         lo.y + off[0] * sa + off[1] * ca, lo.z + off[2])


def condition(t, i, v):
    c = unreal.StoryCondition()
    c.set_editor_property("type", getattr(unreal.StoryConditionType, t))
    c.set_editor_property("id", i)
    c.set_editor_property("value", v)
    return c


try:
    for a in list(eas.get_all_level_actors()):
        if a.get_actor_label().startswith(("ArtNPC_", "ArtNPCSeat_")):
            eas.destroy_actor(a)
    markers = {a.get_actor_label(): a for a in eas.get_all_level_actors()
               if a.get_actor_label().startswith("MK_NPC_")}
    cls = unreal.EditorAssetLibrary.load_blueprint_class(N + "BP_NPC")
    for name, (mesh, mat, idle, talk, place, off, dyaw) in NPCS.items():
        m = markers["MK_NPC_" + name]
        inter = next((c for c in m.get_components_by_class(
            unreal.SceneComponent) if "Interactable" in c.get_name()), None)
        loc = to_world(m, off)
        if place == "interact" and inter:
            p = inter.get_world_location()
            o = m.get_actor_location()
            loc = unreal.Vector(loc.x + p.x - o.x, loc.y + p.y - o.y, loc.z)
        rot = unreal.Rotator(roll=0, pitch=0,
                             yaw=m.get_actor_rotation().yaw + dyaw)
        a = eas.spawn_actor_from_class(cls, loc, rot)
        a.set_actor_label("ArtNPC_" + name)
        a.set_folder_path(str(m.get_folder_path()).replace("Markers/NPC",
                                                           "NPCs"))
        a.set_editor_property("data_layer_assets",
                              m.get_editor_property("data_layer_assets"))
        body = a.get_editor_property("Body")
        body.set_skeletal_mesh_asset(eal.load_asset(mesh))
        if mat:
            body.set_material(0, eal.load_asset(mat))
        a.set_editor_property("Participant", name)
        a.set_editor_property("IdleAnim", eal.load_asset(idle))
        a.set_editor_property("TalkAnim", eal.load_asset(talk))
        if name in HAND_PROPS:
            pm, sock, pl, pr = HAND_PROPS[name]
            hp = a.get_editor_property("HandProp")
            hp.set_static_mesh(eal.load_asset(pm))
            hp.set_editor_property("relative_location", unreal.Vector(*pl))
            hp.set_editor_property("relative_rotation",
                                   unreal.MathLibrary.make_rot_from_z(
                                       unreal.Vector(*pr)))
            a.set_editor_property("PropSocket", sock)
        if name in SHOW_WHILE:
            a.set_editor_property("ShowWhile", [
                condition(*c) for c in SHOW_WHILE[name]])
        hide_marker(m)
        info = {"loc": [round(loc.x), round(loc.y), round(loc.z)],
                "yaw": round(rot.yaw),
                "layers": [str(d.get_name()) for d in
                           a.get_editor_property("data_layer_assets")]}
        if name in SEATS:
            sm, soff, sc = SEATS[name]
            s = eas.spawn_actor_from_class(unreal.StaticMeshActor,
                                           to_world(m, soff), rot)
            s.set_actor_label("ArtNPCSeat_" + name)
            s.set_folder_path(a.get_folder_path())
            s.set_editor_property("data_layer_assets",
                                  m.get_editor_property("data_layer_assets"))
            smc = s.static_mesh_component
            smc.set_static_mesh(eal.load_asset(sm))
            s.set_actor_scale3d(unreal.Vector(*sc))
            smc.set_editor_property("can_ever_affect_navigation", False)
            o, e = s.get_actor_bounds(False)
            info["seat_top"] = round(o.z + e.z, 1)
        res[name] = info
except Exception:
    res["error"] = traceback.format_exc()
with open(OUT, "w") as f:
    json.dump(res, f, indent=1)
