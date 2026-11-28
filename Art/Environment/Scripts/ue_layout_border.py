"""Graybox layout pass of 2026-11-26 on L0_BorderBazaar.

Run in the editor: py "<this file>", then the ue_dress_* scripts. Safe to
run again; step names after the file name run only those steps (for
example `sellers`). What it does:

* The bazaar becomes a rectangle: the side walls of the stall block move
  out to the lot's width (Y = +-2700), which adds a yard on each side of
  the stalls (ue_dress_border.py puts the shops there).
* The road is a through road: no road block, no card game. It runs on
  east past the map edge and west over the far bank (Germany). The truck
  queue is longer and is the north edge of the map: an invisible wall
  runs along its south side.
* The edge triggers get their new lines.
* The kantor clerk and the cigarette seller move to the shop buildings;
  their old stalls sell honey and socks. The gnome seller steps out
  from under his canopy, where the camera could not see him.
* The lamp posts of the lot are never cut open by the camera.
* The corn lady's and Zbyszek's stalls stand in the south row
  (2026-11-28), whose fronts face the camera: they swapped places with
  the flowers and the CDs (ue_dress_stalls.py, then
  Art/NPCs/Scripts/ue_dress_npcs.py, which puts the sellers in front).
* Night shift fixes: the graybox chairs of the grill shack and the office
  stool blocked the cooks placed on them; they are hidden, no collision.
  The wave 2 Skewermen hold ground perches instead of climbing.
* The 0A first fight cooks wait off screen near the impound office
  (step `first_fight`, 2026-11-28).
* Step `office` (2026-11-28): Zbyszek's box shows only while his quest is
  started; Halina's desk stands behind her, not round her.
"""
import json
import os
import sys
import traceback

import unreal

HERE = os.path.dirname(__file__.replace("\\", "/"))
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
eal = unreal.EditorAssetLibrary
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
sdl = unreal.SubobjectDataBlueprintFunctionLibrary
CUBE = "/Engine/BasicShapes/Cube"
WIDE = 2700.0  # half width of the lot and now of the bazaar
EAST_END = 2769.0  # the east bound across the road
res = {"log": []}


def actors():
    return {a.get_actor_label(): a for a in eas.get_all_level_actors()}


def comp(actor, name):
    return next((c for c in actor.get_components_by_class(
        unreal.SceneComponent) if c.get_name() == name), None)


def set_box(c, center, half):
    """A unit cube component as a world box: center and half sizes, cm."""
    c.modify()
    c.set_world_location(unreal.Vector(*center), False, False)
    c.set_world_scale3d(unreal.Vector(*[h / 50.0 for h in half]))


def drop_comp(actor, name):
    c = comp(actor, name)
    if c is None:
        return
    actor.modify()
    handles = sds.k2_gather_subobject_data_for_instance(actor)
    for h in handles:
        if sdl.get_object(sdl.get_data(h)) == c:
            sds.delete_subobject(handles[0], h)
            return


def box_actor(label, folder, center, half, material=None, blocks=True,
              visible=True):
    """A cube StaticMeshActor as a world box; made once, then updated."""
    a = actors().get(label) or eas.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*center), unreal.Rotator())
    a.modify()
    a.set_actor_label(label)
    a.set_folder_path(folder)
    a.set_actor_location(unreal.Vector(*center), False, False)
    a.set_actor_scale3d(unreal.Vector(*[h / 50.0 for h in half]))
    c = a.static_mesh_component
    c.modify()
    c.set_static_mesh(eal.load_asset(CUBE))
    if material:
        c.set_material(0, material)
    c.set_collision_profile_name("BlockAll" if blocks else "NoCollision")
    c.set_editor_property("can_ever_affect_navigation", blocks)
    c.set_visibility(visible)
    c.set_editor_property("hidden_in_game", not visible)
    return a


def bazaar(A):
    walls = A["Bazaar_Walls"]
    walls.modify()
    half = (WIDE - 148) / 2 + 9  # from the gnome yard wall to the north one
    for name, y in (("P5", -WIDE), ("P8", WIDE)):
        set_box(comp(walls, name), (8 + half, y, 110), (half, 9, 110))
    # North wall, east of the arch: on to the new corner
    set_box(comp(walls, "P2"), (2569, (330 + WIDE + 9) / 2, 110),
            (9, (WIDE + 9 - 330) / 2, 110))
    for name in ("P3", "P4", "P6", "P7"):
        drop_comp(walls, name)
    north = A["Ground_Patch_BazaarNorth"]
    north.modify()
    o, e = north.get_actor_bounds(False)
    s = north.get_actor_scale3d()
    north.set_actor_scale3d(unreal.Vector(s.x, s.y * WIDE / e.y, s.z))


def road(A):
    for label in ("Truck_Block_1", "Truck_Block_2", "Truckers_CardGame",
                  "MK_NPC_Trucker_1", "MK_NPC_Trucker_2",
                  "MK_NPC_Trucker_3"):
        if label in A:
            eas.destroy_actor(A[label])
    # Queue slots are 540 apart; slot 3 is Kolya's truck. The last ones
    # stand past the map edge, for the look.
    last = A["Truck_Queue_5"]
    for i in range(6, 13):
        label = "Truck_Queue_%d" % i
        if label not in A:
            a = eas.duplicate_actor(last, None, unreal.Vector(
                0, 540.0 * (i - 5), 0))
            a.set_actor_label(label)
            a.set_folder_path("Shared/TruckQueue")
    bounds = A["Bounds_Invisible"]
    bounds.modify()
    set_box(comp(bounds, "P5"), (3280, EAST_END, 150), (720, 9, 250))
    y0 = -3312.0
    set_box(comp(bounds, "P4"), (4000, (y0 + EAST_END + 9) / 2, 150),
            (10, (EAST_END + 9 - y0) / 2, 250))
    # The queue is the edge of the map: a wall along its south side, from
    # the exit fence (Y = -1770) to the east bound
    box_actor("Bounds_Queue", "Shared/Bounds",
              (3322, (-1770 + EAST_END) / 2, 150),
              (4, (EAST_END + 1770) / 2, 250), visible=False)
    # Paving under the shops on the south verge, east of the gate
    if "Ground_Patch_RoadShops" not in A:
        a = eas.duplicate_actor(A["Ground_Patch_GateApron"], None,
                                unreal.Vector(0, 1175, 0))
        a.set_actor_label("Ground_Patch_RoadShops")
        s = a.get_actor_scale3d()
        a.set_actor_scale3d(unreal.Vector(s.x, s.y * 1.9, s.z))
    strip = A["Road_Border"]
    strip.modify()
    y0, y1 = -3270.0, 4800.0
    set_box(comp(strip, "Road"), (3280, (y0 + y1) / 2, 0),
            (270, (y1 - y0) / 2, 0.5))
    white = comp(strip, "Dash1").get_material(0)
    asphalt = comp(strip, "Road").get_material(0)
    box_actor("Road_West", "Shared/Ground", (3280, -5800, 0.5),
              (270, 1000, 0.5), asphalt, blocks=False)
    # Center line east of the old road end, on the bridge and beyond it
    ys = [y for y in range(2250, 4800, 360)] + [
        y for y in range(-6630, -3300, 360)]
    for i, y in enumerate(ys):
        z = 1.5 if y < -4800 else 1.0
        box_actor("Road_Dash_%02d" % i, "Shared/Ground/Dashes",
                  (3280, y, z), (4, 90, 0.5), white, blocks=False)


def edges(A):
    east = A["Edge_QueueEast"]
    east.modify()
    east.set_actor_location(unreal.Vector(2950, 2660, 100), False, False)
    # From the bazaar's north wall to the queue: not into the east yard
    box = comp(east, "Trigger")
    box.modify()
    box.set_box_extent(unreal.Vector(365, 70, 200), True)
    back = comp(east, "ReturnPoint")
    back.modify()
    back.set_world_location(unreal.Vector(3180, 2150, 60), False, False)
    back.set_world_rotation(unreal.Rotator(roll=0, pitch=0, yaw=-90),
                            False, False)
    east.set_editor_property("Message", unreal.Text(
        "Poland is too far to walk on chicken feet. "
        "You need to pick up a car first."))
    west = A["Edge_BridgeWest"]
    west.modify()
    west.set_editor_property("Message", unreal.Text(
        "That way is Germany. Co-co-cosmos is the other way."))


def night_shift(A):
    # The eating cooks and the sleeper bring their own chair (SetupBody
    # of BP_Shawarman): the graybox chairs under them only trapped them
    seats = [comp(A["Office_CCTV"], "P3")]
    for i, y in enumerate((-1560, -1500, -1440)):
        a = A["GrillShack_Chair_%d" % (i + 1)]
        a.modify()
        a.set_actor_location(unreal.Vector(-1984, y, 0), False, False)
        seats += a.get_components_by_class(unreal.StaticMeshComponent)
    for c in seats:
        c.modify()
        c.set_collision_profile_name("NoCollision")
        c.set_editor_property("can_ever_affect_navigation", False)
        c.set_visibility(False)
        c.set_editor_property("hidden_in_game", True)
    stool = seats[0]
    stool.set_world_location(unreal.Vector(-234, 1770, 22), False, False)
    # Climb points stood at the seams between the arena containers (and
    # one past the end of its row): a Skewerman ended up on the gap. Each
    # goes to the middle part of a container, with its step crate.
    steps = A["Arena_ClimbSteps"]
    for i, x in ((1, -3020), (2, -3700), (3, -3020), (4, -3600)):
        for thing in (A["MK_Enemy_ClimbPoint_%d" % i],
                      comp(steps, "P%d" % i)):
            thing.modify()
            if isinstance(thing, unreal.Actor):
                l = thing.get_actor_location()
                thing.set_actor_location(unreal.Vector(x, l.y, l.z),
                                         False, False)
            else:
                l = thing.get_world_location()
                thing.set_world_location(unreal.Vector(x, l.y, l.z),
                                         False, False)
    # Up on a container a Skewerman could not be shot: the pellets fly
    # level at her height into the container wall, and the cursor aim
    # (projected on the ground) missed him by meters at that height. He
    # holds a ground perch instead, by the middle container of a side
    # wall between two cars: BP_Skewerman has no ClimbMontage, so
    # FinishClimb (BP_EnemyBase) does not move him, he only throws
    for label, y in (("Skewerman_Wave2_1", -650), ("Skewerman_Wave2_2", 650)):
        a = A[label]
        a.modify()
        a.set_editor_property("ClimbFrom", unreal.Vector(-3420, y, 0))
        a.set_editor_property("ClimbTop", unreal.Vector(-3420, y, 80))
    # The sleeper stood 6 cm inside the CCTV desk
    for label in ("Shawarman_Night_Sleeping", "MK_Enemy_Shawarman_Sleeping"):
        a = A[label]
        a.modify()
        l = a.get_actor_location()
        a.set_actor_location(unreal.Vector(-222, l.y, l.z), False, False)


def first_fight(A):
    # The 0A cooks wait close to the impound office (halina_call fires
    # at her window, about (120, 1860)), off screen for the gameplay
    # camera there and at the CP_LeaveOffice checkpoint (365, 1800):
    # the first one in the gap between the tools stall and the
    # Zigaretten shop, the other two on the main street behind the
    # toys stall, out of view while she fights in front of the office.
    # They are dormant (hidden) until the fight wakes them
    world = unreal.EditorLevelLibrary.get_editor_world()
    for label, x, y in (("Shawarman_1", 1450, 1950),
                        ("Shawarman_2", 1600, 560),
                        ("Shawarman_3", 1600, 700)):
        a = A[label]
        hit = unreal.SystemLibrary.line_trace_single(
            world, unreal.Vector(x, y, 500), unreal.Vector(x, y, -500),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [a],
            unreal.DrawDebugTrace.NONE, True)
        t = hit.to_tuple() if hit else None
        ground = t[4].z if t and t[0] else 0.0
        half = a.get_component_by_class(
            unreal.CapsuleComponent).get_scaled_capsule_half_height()
        a.modify()
        a.set_actor_location_and_rotation(
            unreal.Vector(x, y, ground + half + 2),
            unreal.Rotator(roll=0, pitch=0, yaw=180), False, False)
        res["log"].append([label, ground])


def shops(A):
    # The kantor and the cigarettes are shop buildings now
    # (ue_dress_border.py): their stalls on the main street sell
    # something else. She walks into the kantor and talks to the clerk at
    # his window inside, behind frosted glass (ue_dress_border.py puts
    # the clerk's marker there). Kotlet sits in his booth. Nobody is
    # modelled inside, so their markers are hidden. The cigarette seller
    # stands at his door (his model: ue_dress_border.py). The gnome seller
    # stands beside his stall, by the way to the gnome field: under the
    # canopy the camera did not see him.
    for old, new, text in (("Stall_Kantor", "Stall_Honey", "MIOD"),
                           ("Stall_Cigarettes", "Stall_Socks", "SKARPETY")):
        a = A.get(old) or A[new]
        a.modify()
        a.set_actor_label(new)
        for t in a.get_components_by_class(unreal.TextRenderComponent):
            t.modify()
            t.set_text(unreal.Text(text))
        glass = comp(a, "Glass7")
        if glass and new == "Stall_Honey":
            glass.modify()
            glass.set_collision_profile_name("NoCollision")
            glass.set_visibility(False)
            glass.set_editor_property("hidden_in_game", True)
    for label, spot, hide in (("MK_NPC_KantorClerk", None, True),
                              ("MK_NPC_CigaretteSeller", (1615, 2465), True),
                              ("MK_NPC_Krasnal", (1440, -650), False),
                              ("MK_NPC_Kotlet", None, True)):
        a = A[label]
        a.modify()
        if spot:
            a.set_actor_location_and_rotation(
                unreal.Vector(spot[0], spot[1], a.get_actor_location().z),
                unreal.Rotator(), False, False)
        if not hide:
            continue
        for c in (a.get_components_by_class(unreal.StaticMeshComponent) +
                  a.get_components_by_class(unreal.TextRenderComponent)):
            c.modify()
            c.set_collision_profile_name("NoCollision")
            c.set_visibility(False)
            c.set_editor_property("hidden_in_game", True)


# Stall: (x, y, yaw). The south row (yaw 0) faces north, to the camera
SELLER_SLOTS = {"Stall_Zbyszek": (1240, 900, 0),
                "Stall_CDs": (1960, 900, 180),
                "Stall_CornLady": (1240, -1620, 0),
                "Stall_Flowers": (1960, -1260, 180)}


def sellers(A):
    # A seller in the north row turns her back on the camera, which
    # looks south: the stalls with a story seller go to the south row
    for label, (x, y, yaw) in SELLER_SLOTS.items():
        a = A[label]
        a.modify()
        a.set_actor_location_and_rotation(
            unreal.Vector(x, y, a.get_actor_location().z),
            unreal.Rotator(roll=0, pitch=0, yaw=yaw), False, False)


def poles(A):
    # A hole cut in a thin pole only looks broken
    for a in A.values():
        tags = [str(t) for t in a.tags]
        if "LampPost" in tags and "NoOcclusionCutout" not in tags:
            a.modify()
            a.tags = tags + ["NoOcclusionCutout"]


def office(A):
    # Zbyszek's box is on the evidence shelf only once he has asked her for
    # it: else she does not know to look for it, and with it a van would
    # wait for her after the exit. BPC_Interactable hides its owner while
    # its conditions fail
    m = A["MK_Pickup_ZbyszekBox"]
    it = m.get_components_by_class(unreal.InteractableComponent)[0]
    c = unreal.StoryCondition()
    c.set_editor_property("type", unreal.StoryConditionType.QUEST_IS)
    c.set_editor_property("id", "q_zbyszek_box")
    c.set_editor_property("value", "started")
    m.modify()
    it.modify()
    it.set_editor_property("conditions", [c])
    it.set_editor_property("bHideWhileUnavailable", True)
    # Halina stands 20 cm behind her window (ue_dress_npcs.py, any further
    # and the lintel hides her head): her desk goes behind her, she stood
    # in it
    set_box(comp(A["Office_HalinaDesk"], "P1"), (-86, 1860, 48),
            (24, 60, 48))


try:
    for step in (bazaar, road, edges, night_shift, first_fight, shops,
                 poles, sellers, office):
        if sys.argv[1:] and step.__name__ not in sys.argv[1:]:
            continue
        step(actors())
        res["log"].append(step.__name__)
    res["ok"] = True
except Exception:
    res["err"] = traceback.format_exc()
json.dump(res, open(HERE + "/out.json", "w"), indent=1)
