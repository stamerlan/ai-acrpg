"""Meshy buildings: the shops of the bazaar, the border post, the
officer at the head of the truck queue.

Run in the editor: py "<this file>" (after ue_layout_border.py and
ue_buildings_import.py). The shops have no graybox of their own: this
script makes a hidden blocking box per building (Yard_<Name>,
Shared/Bazaar/Yards) from the model's bounds and puts the model
(ArtBld_<Name>) on it. The guard booth and the veterinary office go over
their graybox actors. The models' fronts are their local +Y. The camera
looks south, so a shop whose front is to be read faces north (0).

The buildings take no camera traces, so the camera never cuts them open:
behind one she shows as a silhouette (ue_silhouette.py). She can walk
into the shops of Shops.json (blender_shops_open.py, imported by
ue_buildings_import.py): their shell (ArtBld_<Name>) has an open door,
the inside and the fittings, and the roof with the top of the north wall
is an actor of its own (ArtBld_<Name>_Roof) with a camera-only box over
the room, tagged HideWhole, so CameraOcclusionComponent hides it whole
while she is inside. Their blocking
boxes (walls, fittings, the apron) are components of Yard_<Name>; the
script also puts in their Kenney props, lamps and signs, and moves a
shop NPC's talk point inside (the kantor clerk, behind frosted glass).

The look follows photos of today's bazaars on the German border
(Slubice, Osinow Dolny, Leknica): clean plastered or panel pavilions,
red metal tile roofs, huge ZIGARETTEN / KANTOR / FRISEUR signs.
"""
import importlib
import json
import math
import os
import random
import sys
import traceback

sys.path.insert(0, r"C:\Users\vvovchenko\repo\acrpg\Art\Environment\Scripts")
import ue_dress_lib as L  # noqa: E402
importlib.reload(L)
import unreal  # noqa: E402

D = L.__file__.rsplit("\\", 1)[0]  # out.json goes next to the scripts
B = "/Game/Environment/Buildings/SM_"
V = "survival_kit/SM_"
CM = "city_kit_commercial/SM_"
U = "furniture_kit/SM_"
SIZE = 0.9  # people here are about 0.9 of real height
# name: (model, x, y, heading of the front in degrees (0 is north, +X;
# 90 is east, +Y), size)
YARDS = {
    # East yard. The red shop stands south of the pale one: its bounce
    # light turned the wall behind it pink, and that wall faced the camera
    "Sklep": ("Sklep", 2090, 2400, 0, SIZE),
    "Zigaretten": ("Zigaretten", 1345, 2400, 0, SIZE),
    # West yard
    "Friseur": ("Friseur", 2090, -2420, 0, SIZE),
    "Toilet": ("Toilet", 1730, -2540, 90, SIZE),
    "Bar": ("Bar", 1340, -2470, 90, SIZE),
    # South verge of the road, east of the gate, facing the road
    "Kantor": ("Kantor", 2775, 700, 0, 0.85),
    "Pavilion": ("Pavilion", 2775, 1400, 0, 0.85),
}
# Walk-in shops by model (blender_shops_open.py, sizes as in YARDS)
SHOPS = json.load(open(os.path.join(os.path.dirname(D), "Buildings",
                                    "Shops.json")))
# A shop lamp: unitless intensity and radius (cm, before the size)
LAMP = 2500.0
LAMP_RADIUS = 450.0
res = {"n": 0}


def half_sizes(path, heading, size):
    """World half sizes of the model with its front (+Y) at a heading."""
    b = L.mesh(path).get_bounding_box()
    hx, hy = (b.max.x - b.min.x) / 2 * size, (b.max.y - b.min.y) / 2 * size
    if round(heading / 90) % 2 == 0:
        hx, hy = hy, hx
    return hx, hy, (b.max.z - b.min.z) * size


def block(label, folder, x, y, hx, hy, h):
    a = L.eas.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(x, y, h / 2.0),
        unreal.Rotator())
    a.set_actor_label(label)
    a.set_folder_path(folder)
    a.set_actor_scale3d(unreal.Vector(hx / 50.0, hy / 50.0, h / 100.0))
    c = a.static_mesh_component
    c.set_static_mesh(L.eal.load_asset("/Engine/BasicShapes/Cube"))
    c.set_collision_profile_name("BlockAll")
    c.set_visibility(False)
    c.set_editor_property("hidden_in_game", True)
    return a


def walk_in(actors, name, model, x, y, heading, size):
    """A shop she walks into: shell, roof, blocks, props, lamps, signs."""
    shop = SHOPS[model]
    folder = "Art/Shared/Bazaar/Yards"
    a = L.place(B + model + "_Shell", (x, y, 0), heading - 90, size,
                "ArtBld_" + name, folder, False)
    roof = L.place(B + model + "_Roof", (x, y, 0), heading - 90, size,
                   "ArtBld_" + name + "_Roof", folder, True)
    # Hidden whole while the camera rays or the trace up from her hit its
    # box (CameraOcclusionComponent)
    roof.tags = ["HideWhole"]
    t = a.get_actor_transform()
    # Boxes are in the mesh's axes: a quarter turn swaps them
    swap = round(heading / 90) % 2 == 0
    yard = L.holder("Yard_" + name, "Shared/Bazaar/Yards", (x, y, 0))
    cube = L.eal.load_asset("/Engine/BasicShapes/Cube")
    for i, (cx, cy, hx, hy, h) in enumerate(shop["blocks"]):
        p = t.transform_location(unreal.Vector(cx, cy, 0))
        if swap:
            hx, hy = hy, hx
        c = L.part(yard, "Block%02d" % i, unreal.StaticMeshComponent)
        c.set_static_mesh(cube)
        c.set_world_location(unreal.Vector(p.x, p.y, h * size / 2),
                             False, False)
        c.set_world_scale3d(unreal.Vector(hx * size / 50, hy * size / 50,
                                          h * size / 100))
        c.set_collision_profile_name("BlockAll")
        c.set_visibility(False)
        c.set_editor_property("hidden_in_game", True)
    for i, (path, at, yaw, scale) in enumerate(shop["props"]):
        # Kenney models stand on a corner: put the middle of the
        # footprint on the spot
        b = L.mesh(path).get_bounding_box()
        k = scale * size
        turn = unreal.Rotator(roll=0, pitch=0, yaw=heading - 90 + yaw)
        mid = unreal.MathLibrary.greater_greater_vector_rotator(
            unreal.Vector((b.min.x + b.max.x) / 2 * k,
                          (b.min.y + b.max.y) / 2 * k, 0), turn)
        p = t.transform_location(unreal.Vector(*at)) - mid
        L.place(path, (p.x, p.y, p.z), heading - 90 + yaw, k,
                "ArtBld_Prop_%s_%02d" % (name, i), folder, False)
    for i, (at, power) in enumerate(shop["lamps"]):
        lamp = L.eas.spawn_actor_from_class(
            unreal.PointLight, t.transform_location(unreal.Vector(*at)),
            unreal.Rotator())
        lamp.set_actor_label("ArtBld_Light_%s_%d" % (name, i))
        lamp.set_folder_path(folder)
        lc = lamp.point_light_component
        lc.set_mobility(unreal.ComponentMobility.MOVABLE)
        lc.set_editor_property("intensity_units",
                               unreal.LightUnits.UNITLESS)
        lc.set_intensity(LAMP * power)
        lc.set_attenuation_radius(LAMP_RADIUS * size)
        lc.set_light_color(unreal.LinearColor(1.0, 0.95, 0.88, 1.0))
    for i, (text, at, world_size, rgb, up) in enumerate(shop["signs"]):
        # Flat on a counter, its top to the south (the camera looks
        # south), or on a wall facing north
        s = L.eas.spawn_actor_from_class(
            unreal.TextRenderActor, t.transform_location(unreal.Vector(*at)),
            unreal.Rotator(roll=0, pitch=90 if up else 0, yaw=0))
        s.set_actor_label("ArtBld_Text_%s_%d" % (name, i))
        s.set_folder_path(folder)
        tr = s.text_render
        tr.set_text(unreal.Text(text))
        tr.set_world_size(world_size)
        tr.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
        tr.set_vertical_alignment(
            unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
        tr.set_text_render_color(unreal.Color(
            r=int(rgb[0] * 255), g=int(rgb[1] * 255), b=int(rgb[2] * 255),
            a=255))
    talk = shop.get("talk")
    if talk:
        # The marker faces north with its talk point (its interactable,
        # 112 cm ahead of it) on the spot; it stays hidden
        m = actors[talk["marker"]]
        it = next(c for c in m.get_components_by_class(
            unreal.SphereComponent)
            if "Interactable" in c.get_class().get_name())
        p = t.transform_location(unreal.Vector(*talk["at"]))
        m.modify()
        it.modify()
        m.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=heading),
                             False)
        w = it.get_world_location()
        loc = m.get_actor_location()
        m.set_actor_location(unreal.Vector(loc.x + p.x - w.x,
                                           loc.y + p.y - w.y, loc.z),
                             False, False)
        it.set_sphere_radius(talk["radius"])
        res[talk["marker"]] = [round(p.x), round(p.y)]
    res["n"] += 1


def over(actors, label, model, heading, size, names, sign, sign_size):
    """A model over a graybox actor's box, centered on the named parts.

    The graybox's sign text lies on a black plate on the model's roof,
    where the camera reads it (like the stall names on their tarps).
    """
    a = actors[label]
    lo = [1e9, 1e9]
    hi = [-1e9, -1e9]
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        if c.get_name() in names:
            o, e, _ = unreal.SystemLibrary.get_component_bounds(c)
            lo = [min(lo[0], o.x - e.x), min(lo[1], o.y - e.y)]
            hi = [max(hi[0], o.x + e.x), max(hi[1], o.y + e.y)]
    L.place(B + model, ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, 0),
            heading - 90, size, "ArtBld_" + label,
            "Art/Shared/BorderPost", False)
    L.hide_graybox(a)
    top = L.mesh(B + model).get_bounding_box().max.z * size
    mid = ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2)
    L.place("/Engine/BasicShapes/Cube", (mid[0], mid[1], top + 1), 0,
            (sign_size * 1.6 / 100, (hi[1] - lo[1]) * 0.9 / 100, 0.02),
            "ArtBld_Sign_" + label, "Art/Shared/BorderPost", False,
            "/Game/Materials/Graybox/MI_GB_Black")
    for t in a.get_components_by_class(unreal.TextRenderComponent):
        t.modify()
        t.set_text(unreal.Text(sign))
        t.set_world_size(sign_size)
        t.set_world_location_and_rotation(
            unreal.Vector(mid[0], mid[1], top + 3),
            unreal.Rotator(roll=0, pitch=90, yaw=0), False, False)
        t.set_visibility(True)
    res["n"] += 1


try:
    for a in list(L.eas.get_all_level_actors()):
        if a.get_actor_label().startswith(("ArtBld_", "Yard_")):
            L.eas.destroy_actor(a)
    rng = random.Random(7)
    actors = {a.get_actor_label(): a for a in L.eas.get_all_level_actors()}
    for name, (model, x, y, heading, size) in YARDS.items():
        if model in SHOPS and not SHOPS[model].get("closed"):
            walk_in(actors, name, model, x, y, heading, size)
            continue
        hx, hy, h = half_sizes(B + model, heading, size)
        block("Yard_" + name, "Shared/Bazaar/Yards", x, y, hx, hy, h)
        if model in SHOPS:
            # Closed (the WC by the bar): its upper part is a roof that
            # the camera hides, so it does not cover the bar's room
            L.place(B + model + "_Shell", (x, y, 0), heading - 90, size,
                    "ArtBld_" + name, "Art/Shared/Bazaar/Yards", False)
            roof = L.place(B + model + "_Roof", (x, y, 0), heading - 90,
                           size, "ArtBld_" + name + "_Roof",
                           "Art/Shared/Bazaar/Yards", True)
            roof.tags = ["HideWhole"]
            res["n"] += 1
            continue
        L.place(B + model, (x, y, 0), heading - 90, size, "ArtBld_" + name,
                "Art/Shared/Bazaar/Yards", False)
        res["n"] += 1
    # Border post: the booth's door and the office door face the road
    # (north), the booth's window faces the trucks coming from the east
    over(actors, "BorderBooth", "Booth", 0, 0.84, ("P1",),
         "STRAZ GRANICZNA", 22)
    over(actors, "CustomsShed", "VetOffice", 0, 0.97, ("P1",),
         "ODPRAWA WETERYNARYJNA", 24)
    # The officer checks papers at the head of the queue, on the verge
    # north-west of the first truck, facing it
    ox, oy = 3540, -2050
    L.place(B + "Officer", (ox, oy, 0), 90 - 90, 0.95, "ArtBld_Officer",
            "Art/Shared/TruckQueue", False)
    block("Yard_OfficerBlock", "Shared/TruckQueue", ox, oy, 22, 22, 170)
    # The cigarette seller stands by his shop's door, east of it (the
    # parasol is on the west side); MK_NPC_CigaretteSeller is on the
    # same spot (ue_layout_border.py)
    sx, sy = 1615, 2465
    L.place(B + "Seller", (sx, sy, 0), 0 - 90, 0.95, "ArtBld_Seller",
            "Art/Shared/Bazaar/Yards", False)
    block("Yard_SellerBlock", "Shared/Bazaar/Yards", sx, sy, 22, 22, 160)

    def put(path, x, y, yaw=0.0, s=1.0, occ=True):
        L.place(path, (x, y, 0), yaw, s, "ArtBld_Prop_" +
                path.split("SM_")[1], "Art/Shared/Bazaar/Yards", occ)
        res["n"] += 1

    # West yard: the bar's tables under parasols, its stock behind it
    for (x, y) in ((1230, -2040), (1500, -2010)):
        put(CM + "detail_parasol_a", x, y, rng.uniform(0, 360), 5.2)
        for k in range(3):
            ang = k * 2.1 + rng.uniform(0, 0.5)
            put(U + "chair", x + math.cos(ang) * 110,
                y + math.sin(ang) * 110, math.degrees(ang) + 90, 1.9, False)
    for (x, y) in ((1150, -2180), (1100, -2250)):
        put(V + rng.choice(["barrel", "box"]), x, y, rng.uniform(0, 360),
            2.5)
except Exception:
    res["err"] = traceback.format_exc()
json.dump(res, open(D + r"\out.json", "w"), indent=0)
