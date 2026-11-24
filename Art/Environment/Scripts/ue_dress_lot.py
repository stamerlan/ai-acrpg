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
C = "car_kit/SM_"
CARS = [C + "sedan", C + "hatchback_sports", C + "suv", C + "van", C + "taxi",
        C + "truck", C + "sedan", C + "hatchback_sports", C + "suv"]
CONT = ["city_kit_industrial/SM_shipping_container_a",
        "city_kit_industrial/SM_shipping_container_b",
        "city_kit_industrial/SM_shipping_container_c"]
# car_kit colormaps with the body swatch repainted (ue_dress_polish.py)
LIV = "/Game/Environment/Kenney/Materials/MI_Env_car_kit_"
PAINT = ["Red", "Blue", "White", "Gray", "Orange", "Yellow"]
res = {"placed": 0}


def local_box(actor, names):
    """Union of cube components in the actor's frame: (lo, hi) vectors."""
    al = actor.get_actor_location()
    ay = actor.get_actor_rotation().yaw
    ca, sa = math.cos(math.radians(-ay)), math.sin(math.radians(-ay))
    lo = [1e9, 1e9, 1e9]
    hi = [-1e9, -1e9, -1e9]
    for c in actor.get_components_by_class(unreal.StaticMeshComponent):
        if not c.static_mesh or (names and c.get_name() not in names):
            continue
        b = c.static_mesh.get_bounding_box()
        s = c.get_world_scale()
        h = [(b.max.x - b.min.x) / 2 * abs(s.x),
             (b.max.y - b.min.y) / 2 * abs(s.y),
             (b.max.z - b.min.z) / 2 * abs(s.z)]
        rel = (c.get_world_rotation().yaw - ay) % 180
        if 45 < rel < 135:
            h[0], h[1] = h[1], h[0]
        o, e, _ = unreal.SystemLibrary.get_component_bounds(c)
        dx, dy = o.x - al.x, o.y - al.y
        cx, cy = dx * ca - dy * sa, dx * sa + dy * ca
        for i, v in enumerate((cx, cy, o.z)):
            lo[i] = min(lo[i], v - h[i])
            hi[i] = max(hi[i], v + h[i])
    return lo, hi


def fit(actor, path, names=(), label=None, folder=None, flip=False,
        mi=None, keep_aspect=False):
    """Place mesh path over the actor's box; Kenney long axis is Y."""
    lo, hi = local_box(actor, names)
    dims = [hi[i] - lo[i] for i in range(3)]
    sm = L.mesh(path)
    b = sm.get_bounding_box()
    md = [b.max.x - b.min.x, b.max.y - b.min.y, b.max.z - b.min.z]
    ay = actor.get_actor_rotation().yaw
    along_x = dims[0] > dims[1]
    yaw = ay + (90 if along_x else 0) + (180 if flip else 0)
    L_, W_ = (dims[0], dims[1]) if along_x else (dims[1], dims[0])
    sc = [W_ / md[0], L_ / md[1], dims[2] / md[2]]
    if keep_aspect:
        k = L_ / md[1]
        sc = [min(sc[0], k * 1.15), k, min(sc[2], k * 1.2)]
    cxl, cyl = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    ca, sa = math.cos(math.radians(ay)), math.sin(math.radians(ay))
    al = actor.get_actor_location()
    wx = al.x + cxl * ca - cyl * sa
    wy = al.y + cxl * sa + cyl * ca
    a = L.place(path, (wx, wy, lo[2]), yaw, tuple(sc),
                label or "Art_" + actor.get_actor_label(),
                folder or "Art/" + str(actor.get_folder_path()), True, mi)
    res["placed"] += 1
    return a


try:
    for a in list(L.eas.get_all_level_actors()):
        lab = a.get_actor_label()
        if lab.startswith("Art_") and not lab.startswith("Art_Nature_"):
            L.eas.destroy_actor(a)
    rng = random.Random(4)
    eal = L.eal
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    blk = "/Game/Environment/Kenney/Materials/MI_Env_car_kit_Black"
    if not eal.does_asset_exist(blk):
        mi = tools.create_asset("MI_Env_car_kit_Black",
                                "/Game/Environment/Kenney/Materials",
                                unreal.MaterialInstanceConstant,
                                unreal.MaterialInstanceConstantFactoryNew())
        # untextured: a tint on a textured instance did not show up
        mel = unreal.MaterialEditingLibrary
        mel.set_material_instance_parent(
            mi, eal.load_asset("/Game/Environment/Materials/M_Env"))
        mel.set_material_instance_texture_parameter_value(
            mi, "BaseTex",
            eal.load_asset("/Engine/EngineResources/WhiteSquareTexture"))
        mel.set_material_instance_vector_parameter_value(
            mi, "Color", unreal.LinearColor(0.04, 0.04, 0.05, 1))
        mel.update_material_instance(mi)
        eal.save_loaded_asset(mi)
    for a in list(L.eas.get_all_level_actors()):
        n = a.get_actor_label()
        body = ("Body1", "Cabin2")
        if n.startswith("Car_R") or n.startswith("Arena_Car_"):
            fit(a, rng.choice(CARS), body, flip=rng.random() < 0.5,
                mi=LIV + rng.choice(PAINT) if rng.random() < 0.8 else None)
            L.hide_graybox(a)
        elif n == "Car_Hatchback":
            fit(a, C + "hatchback_sports", body)
            L.hide_graybox(a)
        elif n == "Car_Trabant":
            fit(a, C + "hatchback_sports", body)
            L.hide_graybox(a, keep=("P3", "P4", "P5", "P6"))
        elif n == "Car_Limousine":
            fit(a, C + "sedan", body,
                mi="/Game/Environment/Kenney/Materials/MI_Env_car_kit")
            L.hide_graybox(a)
        elif n == "Tractor":
            fit(a, C + "tractor", (), flip=True)
            L.hide_graybox(a)
        elif n in ("Civic_Start", "Civic"):
            fit(a, C + "sedan", body, mi=blk)
            L.hide_graybox(a)
        elif n == "Truck_Kolya":
            fit(a, C + "delivery", ("Box3", "Cab2", "Chassis1"), flip=True,
                mi=LIV + "White")
            L.hide_graybox(a)
        elif n.startswith("Truck_Queue_"):
            fit(a, C + "delivery", ("Box3", "Cab2", "Chassis1"), flip=True,
                mi=LIV + rng.choice(["Red", "Blue", "Orange", "Gray"]))
            L.hide_graybox(a)
        elif n.startswith("Truck_Block_"):
            fit(a, C + "delivery", (), flip=True,
                mi=LIV + rng.choice(["Red", "Blue", "Yellow"]))
            L.hide_graybox(a)
        elif n.startswith(("Container_", "Arena_Container_")) and any(
                c.get_name() == "Box1" for c in
                a.get_components_by_class(unreal.StaticMeshComponent)):
            fit(a, rng.choice(CONT), ("Box1",))
            L.hide_graybox(a, keep=tuple(c.get_name() for c in
                           a.get_components_by_class(
                               unreal.StaticMeshComponent)
                           if c.get_name() not in ("Box1",)))
        elif n.startswith("Flank_ContainerStacks_"):
            h = L.holder("Art_" + n, "Art/Shared/Lot/Containers")
            comps = {}
            for c in a.get_components_by_class(unreal.StaticMeshComponent):
                if not c.static_mesh:
                    continue
                o, e, _ = unreal.SystemLibrary.get_component_bounds(c)
                rows = 2
                levels = max(1, round(e.z * 2 / 260))
                for j in range(rows):
                    y = o.y - e.y + e.y * (2 * j + 1) / rows
                    for k in range(levels):
                        m = rng.choice(CONT)
                        if m not in comps:
                            comps[m] = L.ism(h, m.split("SM_")[1], m, True)
                        sm = L.mesh(m)
                        bb = sm.get_bounding_box()
                        sx = (e.y * 2 / rows) / (bb.max.x - bb.min.x)
                        sy = (e.x * 2) / (bb.max.y - bb.min.y)
                        sz = 260 / (bb.max.z - bb.min.z)
                        t = unreal.Transform(
                            unreal.Vector(o.x, y, k * 260),
                            unreal.Rotator(0, 0, 90),
                            unreal.Vector(sx, sy, sz))
                        comps[m].add_instance(t, True)
                        res["placed"] += 1
                c.set_visibility(False)
                c.set_editor_property("hidden_in_game", True)
except Exception:
    res["err"] = traceback.format_exc()
json.dump(res, open(D + r"\out.json", "w"), indent=0)
