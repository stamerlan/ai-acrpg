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
V = "survival_kit/SM_"
R = "city_kit_roads/SM_"
CM = "city_kit_commercial/SM_"
U = "furniture_kit/SM_"
C = "car_kit/SM_"
res = {"n": 0}


def put(path, x, y, yaw=0.0, s=1.0, folder="Art/Props", occ=True, z=0.0):
    L.place(path, (x, y, z), yaw, s, "ArtProp_" + path.split("SM_")[1],
            folder, occ)
    res["n"] += 1


try:
    for a in list(L.eas.get_all_level_actors()):
        if a.get_actor_label().startswith(("ArtProp_", "ArtWall_")):
            L.eas.destroy_actor(a)
    rng = random.Random(11)
    # corrugated walls over the bazaar walls (collision stays graybox)
    walls = next(a for a in L.eas.get_all_level_actors()
                 if a.get_actor_label() == "Bazaar_Walls")
    h = L.holder("ArtWall_Bazaar", "Art/Shared/Bazaar/Walls")
    comps = {}
    for c in walls.get_components_by_class(unreal.StaticMeshComponent):
        if not c.static_mesh:
            continue
        o, e, _ = unreal.SystemLibrary.get_component_bounds(c)
        along_x = e.x > e.y
        length = 2 * (e.x if along_x else e.y)
        n = max(1, round(length / 200))
        step = length / n
        for i in range(n):
            m = V + rng.choice(["metal_panel", "metal_panel",
                                "metal_panel_screws"])
            if m not in comps:
                comps[m] = L.ism(h, m.split("SM_")[1], m, True)
            t = -length / 2 + (i + 0.5) * step
            x, y = (o.x + t, o.y) if along_x else (o.x, o.y + t)
            yaw = (0 if along_x else 90) + rng.uniform(-1.5, 1.5)
            sc = unreal.Vector(step / 50 * 1.02, 1.6, rng.uniform(4.2, 4.6))
            tr = unreal.Transform(unreal.Vector(x, y, 0),
                                  unreal.Rotator(0, rng.uniform(-1.5, 1.5),
                                                 yaw), sc)
            comps[m].add_instance(tr, True)
            res["n"] += 1
        c.set_visibility(False)
        c.set_editor_property("hidden_in_game", True)

    # road: lamps on the south verge, none in front of the gate
    for y in (-2900, -1800, -700, 1500):
        put(R + "light_square", 2985, y, 180, 4.2, "Art/Road")
    # road end behind the jackknifed trucks
    for i, y in enumerate((1780, 1900, 2020, 2140)):
        put(R + "construction_barrier", 3180 + (i % 2) * 120, y, 90, 6,
            "Art/Road")
        put(R + "construction_barrier", 3440 + (i % 2) * 120, y, 90, 6,
            "Art/Road")
    for i in range(6):
        put(R + "construction_cone", 3100 + i * 80,
            1680 + rng.uniform(-20, 20),
            0, 5.5, "Art/Road", False)
    put(R + "road_sign_warning", 3000, 1650, 90, 4, "Art/Road")
    # bridge entrance on the German side, barriers across the far end
    for i in range(4):
        put(R + "construction_barrier", 3130 + i * 120, -4150, 0, 6,
            "Art/Road")

    # office yard: beer corner with parasols, crates and pallets
    for (x, y) in ((700, -300), (860, 260), (640, 640)):
        put(CM + "detail_parasol_a", x, y, rng.uniform(0, 360), 5.2,
            "Art/Shared/OfficeYard")
        for k in range(3):
            a = k * 2.1 + rng.uniform(0, 0.5)
            put(U + "chair", x + math.cos(a) * 110, y + math.sin(a) * 110,
                math.degrees(a) + 90, 1.9, "Art/Shared/OfficeYard", False)
    for (x, y) in ((150, 900), (150, 1000), (230, 950), (150, -800)):
        put(V + "box_large", x, y, rng.uniform(-10, 10), 2.2,
            "Art/Shared/OfficeYard")
    put(R + "dumpster", 180, 300, 90, 6.5, "Art/Shared/OfficeYard")
    for (x, y) in ((900, 1300), (960, 1400)):
        put(V + "barrel", x, y, 0, 2.8, "Art/Shared/OfficeYard")

    # lot aprons: dark cover along the west and east fences
    for (x, y) in ((-700, -2450), (-1700, -2500), (-2000, -2350),
                   (-900, 2350), (-1500, 2450), (-2200, 2300)):
        put(V + rng.choice(["box_large", "barrel", "box"]), x, y,
            rng.uniform(0, 360), 2.6, "Art/Shared/Lot/Aprons")
        put(V + "box", x + 60, y + rng.uniform(-60, 60), rng.uniform(0, 360),
            2.4, "Art/Shared/Lot/Aprons")
    put(C + "truck", -2300, 2350, 0, (1.2, 1.4, 1.2), "Art/Shared/Lot/Aprons")
except Exception:
    res["err"] = traceback.format_exc()
json.dump(res, open(D + r"\out.json", "w"), indent=0)
