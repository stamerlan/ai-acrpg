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
# A stall with a Meshy model of its own (SM_<stall label>: frame, tables
# and goods; SM_<stall label>_Top: the canopy, blender_buildings_to_fbx.py)
# gets that instead of the kit frame, tarp and Kenney goods
B = "/Game/Environment/Buildings/SM_"
PEAK = 330.0  # height of a model stall's canopy top, cm
# Name boards differ from stall to stall, like real ones
BOARDS = ["/Game/Materials/Graybox/MI_GB_" + m for m in (
    "Black", "ContainerBlue", "Red", "ContainerGreen")]
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
        aw.set_visibility(False)
        aw.set_editor_property("hidden_in_game", True)
        res["stalls"] += 1
        if L.eal.does_asset_exist(B + n):
            # The model's front is its local +Y, the stall's its +X. The
            # canopy is an actor of its own: the camera occlusion hides
            # all of it, with the name board on it, when it covers her
            b = L.mesh(B + n + "_Top").get_bounding_box()
            scale = (ey * 1.94 / (b.max.x - b.min.x),
                     ex * 1.94 / (b.max.y - b.min.y), PEAK / b.max.z)
            L.place(B + n, (o.x, o.y, 0), yaw - 90, scale,
                    "ArtStall_Model_" + n, folder, True)
            top = L.place(B + n + "_Top", (o.x, o.y, 0), yaw - 90, scale,
                          "ArtStall_Top_" + n, folder, True)
            # The graybox walls, counter and goods only collide now
            for c in a.get_components_by_class(unreal.StaticMeshComponent):
                c.modify()
                c.set_visibility(False)
                c.set_editor_property("hidden_in_game", True)
            # The name: a board on the canopy's north edge, to the camera
            board = L.part(top, "Board", unreal.StaticMeshComponent)
            board.set_static_mesh(L.mesh("/Engine/BasicShapes/Cube"))
            board.set_material(0, L.eal.load_asset(
                BOARDS[res["stalls"] % len(BOARDS)]))
            board.set_world_location_and_rotation(
                unreal.Vector(o.x + e.x, o.y, 228), unreal.Rotator(),
                False, False)
            board.set_world_scale3d(
                unreal.Vector(0.03, e.y * 1.5 / 100, 0.46))
            L.camera_only(board, False)
            for t in a.get_components_by_class(unreal.TextRenderComponent):
                t.modify()
                t.set_visibility(False)
                t.set_editor_property("hidden_in_game", True)
                name = L.part(top, "Name", unreal.TextRenderComponent)
                name.set_text(t.text)
                name.set_text_material(t.text_material)
                name.set_font(t.font)
                name.set_text_render_color(t.text_render_color)
                name.set_horizontal_alignment(t.horizontal_alignment)
                name.set_vertical_alignment(
                    unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
                name.set_world_size(38)
                name.set_world_location_and_rotation(
                    unreal.Vector(o.x + e.x + 3, o.y, 228),
                    unreal.Rotator(), False, False)
                name.set_world_scale3d(unreal.Vector(1, 1, 1))
            continue
        L.place(G + "SM_StallFrame", (o.x, o.y, 0), yaw, (sx, sy, 1.0),
                "ArtStall_Frame_" + n, folder, True)
        L.place(G + "SM_StallTarp", (o.x, o.y, 0), yaw, (sx, sy, 1.0),
                "ArtStall_Tarp_" + n, folder, True, G + tarp)
        for t in a.get_components_by_class(unreal.TextRenderComponent):
            loc = t.get_world_location()
            if loc.z > 200:
                loc.z = 296
                t.set_world_location(loc, False, False)
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
    # The graybox bunting over the aisle (flat boards on a cable) hung
    # just over the new canopies and read as loose panels, its cables as
    # poles through the tarps
    for a in L.eas.get_all_level_actors():
        if a.get_actor_label() == "StringLights_Banners":
            for c in a.get_components_by_class(unreal.StaticMeshComponent):
                if c.get_name().startswith(("Banner", "Cable")):
                    c.modify()
                    c.set_visibility(False)
                    c.set_editor_property("hidden_in_game", True)
except Exception:
    res["err"] = traceback.format_exc()
json.dump(res, open(D + r"\out.json", "w"), indent=0)
