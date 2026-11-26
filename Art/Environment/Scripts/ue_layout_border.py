"""Graybox layout pass of 2026-11-26 on L0_BorderBazaar.

Run in the editor: py "<this file>", then the ue_dress_* scripts. Safe to
run again. What it does:

* The bazaar becomes a rectangle: the side walls of the stall block move
  out to the lot's width (Y = +-2700), which adds a yard on each side of
  the stalls (ue_dress_border.py puts the buildings there).
* The road is a through road: no road block, no card game. It runs on
  east past the map edge and west over the far bank (Germany). The truck
  queue is longer and is the north edge of the map: an invisible wall
  runs along its south side.
* The edge triggers get their new lines.
* Night shift fixes: the graybox chairs of the grill shack and the office
  stool blocked the cooks placed on them; they are hidden, no collision.
"""
import json
import os
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
    for label in ("Skewerman_Wave2_1", "Skewerman_Wave2_2"):
        a = A[label]
        a.modify()
        for prop in ("ClimbFrom", "ClimbTop"):
            v = a.get_editor_property(prop)
            a.set_editor_property(prop, unreal.Vector(-3020, v.y, v.z))
    # The sleeper stood 6 cm inside the CCTV desk
    for label in ("Shawarman_Night_Sleeping", "MK_Enemy_Shawarman_Sleeping"):
        a = A[label]
        a.modify()
        l = a.get_actor_location()
        a.set_actor_location(unreal.Vector(-222, l.y, l.z), False, False)


try:
    for step in (bazaar, road, edges, night_shift):
        step(actors())
        res["log"].append(step.__name__)
    res["ok"] = True
except Exception:
    res["err"] = traceback.format_exc()
json.dump(res, open(HERE + "/out.json", "w"), indent=1)
