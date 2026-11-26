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
G = "/Game/Environment/Stall/"
TARPS = {"MI_GB_TarpBlue": "MI_Tarp_Blue", "MI_GB_TarpGreen": "MI_Tarp_Green",
         "MI_GB_TarpRed": "MI_Tarp_Red", "MI_GB_TarpYellow": "MI_Tarp_Yellow",
         "MI_GB_TarpStripe": "MI_Tarp_Stripe"}
F = "food_kit/SM_"
U = "furniture_kit/SM_"
V = "survival_kit/SM_"
N = "nature_kit/SM_"
# stall: [(mesh, scale)]
GOODS = {
    "Stall_Fruit": [(F + "apple", 1.0), (F + "orange", 1.1),
                    (F + "watermelon", 0.7), (F + "banana", 1.0),
                    (F + "tomato", 1.2), (F + "cabbage", 0.8)],
    "Stall_CornLady": [(F + "corn", 0.9), (F + "corn", 0.9), (F + "corn", 0.9),
                       (F + "carrot", 0.6)],
    "Stall_Kebab": [(F + "meat_cooked", 0.8), (F + "meat_sausage", 1.2),
                    (F + "bread", 0.8), (F + "bottle_oil", 0.5)],
    "Stall_Socks": [(U + "cardboardBoxOpen", 1.3),
                    (U + "cardboardBoxClosed", 1.2)],
    "Stall_CarParts": [(V + "box_open", 1.6), (V + "bucket", 1.6),
                       (V + "barrel", 1.4)],
    "Stall_Household": [(F + "bottle_oil", 0.5), (F + "can", 0.5),
                        (V + "bucket", 1.6)],
    "Stall_Toys": [(V + "box", 1.4), (U + "cardboardBoxOpen", 1.3)],
    "Stall_Zbyszek": [(U + "cardboardBoxClosed", 1.2), (V + "box", 1.2)],
    "Stall_Tracksuits": [(U + "cardboardBoxOpen", 1.3)],
    "Stall_Shoes": [(U + "cardboardBoxOpen", 1.3), (V + "box", 1.2)],
    "Stall_Bags": [(U + "cardboardBoxOpen", 1.3)],
    "Stall_CDs": [(U + "cardboardBoxOpen", 1.2),
                  (U + "cardboardBoxClosed", 1.0)],
    "Stall_Tools": [(V + "box_open", 1.5), (V + "bucket", 1.5)],
    "Stall_Flowers": [(N + "flower_redA", 2.0), (N + "flower_yellowA", 2.0),
                      (N + "flower_purpleA", 2.0)],
    "Stall_Honey": [(F + "can", 0.5), (F + "bottle_oil", 0.5)],
    "Stall_Gnomes": [],
}
res = {"stalls": 0, "goods": 0}
try:
    for a in list(L.eas.get_all_level_actors()):
        if a.get_actor_label().startswith("ArtStall_"):
            L.eas.destroy_actor(a)
    rng = random.Random(7)
    for a in list(L.eas.get_all_level_actors()):
        n = a.get_actor_label()
        if not n.startswith("Stall_"):
            continue
        yaw = a.get_actor_rotation().yaw
        ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        al = a.get_actor_location()
        aw = None
        counter = None
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            cn = c.get_name()
            if cn.startswith("Awning"):
                aw = c
            elif cn.startswith("Counter"):
                counter = c
            elif cn.startswith("Back") and abs(abs(yaw) - 180) < 1:
                c.set_visibility(False)
                c.set_editor_property("hidden_in_game", True)
        if aw is None:
            continue
        o, e, _ = unreal.SystemLibrary.get_component_bounds(aw)
        rel = (yaw % 180)
        ex, ey = (e.x, e.y) if rel < 45 or rel > 135 else (e.y, e.x)
        sx, sy = ex / 198.0, ey / 183.0
        tarp = TARPS.get(aw.get_material(0).get_name(), "MI_Tarp_Blue")
        folder = "Art/Shared/Bazaar/Stalls"
        L.place(G + "SM_StallFrame", (o.x, o.y, 0), yaw, (sx, sy, 1.0),
                "ArtStall_Frame_" + n, folder, True)
        L.place(G + "SM_StallTarp", (o.x, o.y, 0), yaw, (sx, sy, 1.0),
                "ArtStall_Tarp_" + n, folder, True, G + tarp)
        aw.set_visibility(False)
        aw.set_editor_property("hidden_in_game", True)
        for t in a.get_components_by_class(unreal.TextRenderComponent):
            loc = t.get_world_location()
            if loc.z > 200:
                loc.z = 296
                t.set_world_location(loc, False, False)
        res["stalls"] += 1
        goods = GOODS.get(n, [])
        if counter is None or not goods:
            continue
        co, ce, _ = unreal.SystemLibrary.get_component_bounds(counter)
        span = max(ce.x, ce.y) * 0.85
        k = int(span * 2 / 55)
        for i in range(k):
            m, s = goods[i % len(goods)] if rng.random() < 0.7 else \
                rng.choice(goods)
            off = -span + (i + 0.5) * span * 2 / k
            # along the counter's long axis in world space
            if ce.x > ce.y:
                gx, gy = co.x + off, co.y + rng.uniform(-8, 8)
            else:
                gx, gy = co.x + rng.uniform(-8, 8), co.y + off
            L.place(m, (gx, gy, co.z + ce.z), rng.uniform(0, 360),
                    s * rng.uniform(0.9, 1.1), "ArtStall_Good_" + n,
                    folder + "/Goods", False)
            res["goods"] += 1
except Exception:
    res["err"] = traceback.format_exc()
json.dump(res, open(D + r"\out.json", "w"), indent=0)
