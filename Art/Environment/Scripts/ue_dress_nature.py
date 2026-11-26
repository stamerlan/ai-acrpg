import importlib
import json
import random
import sys
import traceback

sys.path.insert(0, r"C:\Users\vvovchenko\repo\acrpg\Art\Environment\Scripts")
import ue_dress_lib as L  # noqa: E402
importlib.reload(L)
import unreal  # noqa: E402

D = L.__file__.rsplit("\\", 1)[0]  # out.json goes next to the scripts
N = "nature_kit/SM_"
# Meshy plants at real size (blender_meshy_to_fbx.py): pine 13 m,
# spruce 11 m, birch and oak 9 m, bush 1.5 m, fern 0.7 m
P = "/Game/Environment/Meshy/SM_"
PINES = [P + "Pine", P + "Spruce"]
LEAFY = [P + "Oak", P + "Birch"]
POPLAR = [P + "Birch"]
BUSH = [P + "Bush"]
FERN = [P + "Fern"]
GRASS = [N + "grass", N + "grass_large", N + "grass_leafs"]
FLOWER = [N + "flower_redA", N + "flower_yellowA", N + "flower_purpleA"]
ROCK = [N + "rock_largeA", N + "rock_largeC", N + "rock_smallA",
        N + "rock_smallC"]
# (meshes, scale range, min gap in cm)
# The world is 0.6 scale in plan, so the trees are about 0.55 of real
KIND = {"pine": (PINES, (0.48, 0.66), 260), "leafy": (LEAFY, (0.5, 0.7), 330),
        "poplar": (POPLAR, (0.62, 0.8), 220), "bush": (BUSH, (0.55, 0.95), 120),
        "fern": (FERN, (0.8, 1.3), 70),
        "grass": (GRASS, (1.4, 2.2), 60), "flower": (FLOWER, (1.6, 2.4), 50),
        "rock": (ROCK, (1.0, 1.8), 150)}
# region: (x0, x1, y0, y1, [(kind, count)])
REGIONS = {
    "North": (4060, 4600, -3300, 2800,
              [("bush", 90), ("grass", 90), ("rock", 8)]),
    # Behind the truck queue, so it reads as the edge of the map
    "QueueVerge": (3620, 4060, -1650, 2800,
                   [("bush", 110), ("grass", 80), ("rock", 6)]),
    "NorthEast": (2600, 4600, 2800, 4800,
                  [("leafy", 30), ("pine", 18), ("bush", 40),
                   ("grass", 60), ("rock", 6)]),
    "East": (-6800, 2560, 2780, 4800,
             [("poplar", 26), ("leafy", 60), ("pine", 20), ("bush", 70),
              ("grass", 120), ("flower", 50), ("rock", 10)]),
    "South": (-6800, -4240, -3300, 2780,
              [("leafy", 50), ("pine", 40), ("bush", 60), ("grass", 110),
               ("flower", 40), ("rock", 10)]),
    "WestLot": (-4240, 0, -3290, -2770,
                [("bush", 56), ("grass", 60), ("rock", 4)]),
    "WestBazaar": (0, 2560, -3290, -2760,
                   [("bush", 44), ("grass", 50), ("flower", 20)]),
    "RiverBank": (-6800, 4600, -3420, -3320,
                  [("bush", 70), ("grass", 80), ("rock", 16)]),
    "FarBank": (-6800, 4600, -6800, -4850,
                [("leafy", 70), ("pine", 70), ("poplar", 14),
                 ("bush", 60)]),
}
# The bridge and the road beyond it on both sides, with the truck queue
NO_GO = [(2900, 3660, -6900, -3200), (2900, 3660, 2700, 4900)]
res = {}
try:
    L.clear("Art_Nature_")
    L.clear("Ground_Patch_FarBank")
    cube = L.eal.load_asset("/Engine/BasicShapes/Cube")
    g = L.eas.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(-1100, -5800, -0.5),
        unreal.Rotator())
    g.set_actor_label("Ground_Patch_FarBank")
    g.set_folder_path("Shared/Ground")
    g.static_mesh_component.set_static_mesh(cube)
    g.set_actor_scale3d(unreal.Vector(114, 20, 0.01))
    g.static_mesh_component.set_material(0, L.eal.load_asset(
        "/Game/Environment/Materials/MI_Ground_Grass"))
    L.camera_only(g.static_mesh_component, False)
    rng = random.Random(22)
    for rname, (x0, x1, y0, y1, plan) in REGIONS.items():
        h = L.holder("Art_Nature_" + rname, "Art/Nature")
        comps = {}
        taken = []
        count = 0
        plan = plan + [("fern", n // 3) for kind, n in plan
                       if kind == "grass"]
        for kind, n in plan:
            meshes, (s0, s1), gap = KIND[kind]
            pts = L.scatter(rng, x0, x1, y0, y1, n, gap,
                            taken if kind in ("pine", "leafy", "poplar",
                                              "rock") else None)
            for x, y in pts:
                if any(a <= x <= b and c <= y <= d for a, b, c, d in NO_GO):
                    continue
                m = rng.choice(meshes)
                if m not in comps:
                    big = kind in ("pine", "leafy", "poplar")
                    comps[m] = L.ism(h, m.split("SM_")[1], m, occluder=big)
                L.add(comps[m], x, y, 0.0, rng.uniform(0, 360),
                      rng.uniform(s0, s1))
                count += 1
        res[rname] = count
except Exception:
    res["err"] = traceback.format_exc()
json.dump(res, open(D + r"\out.json", "w"), indent=0)
