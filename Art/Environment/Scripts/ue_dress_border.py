"""Meshy buildings: the shops of the bazaar, the border post, the
officer at the head of the truck queue.

Run in the editor: py "<this file>" (after ue_layout_border.py and
ue_buildings_import.py). The shops have no graybox of their own: this
script makes a hidden blocking box per building (Yard_<Name>,
Shared/Bazaar/Yards) from the model's bounds and puts the model
(ArtBld_<Name>) on it. The guard booth and the veterinary office go over
their graybox actors. The models' fronts are their local +Y. The camera
looks south, so a shop whose front is to be read faces north (0).

The buildings are empty shells, so the camera never cuts them open:
the models take no camera traces. Behind one she shows as a silhouette
(ue_silhouette.py).

The look follows photos of today's bazaars on the German border
(Slubice, Osinow Dolny, Leknica): clean plastered or panel pavilions,
red metal tile roofs, huge ZIGARETTEN / KANTOR / FRISEUR signs.
"""
import importlib
import json
import math
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
        hx, hy, h = half_sizes(B + model, heading, size)
        block("Yard_" + name, "Shared/Bazaar/Yards", x, y, hx, hy, h)
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
