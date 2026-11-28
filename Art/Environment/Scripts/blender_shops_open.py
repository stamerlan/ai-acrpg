"""Shops she can walk into: the Meshy shop shells cut open, fitted out.

blender --background --python blender_shops_open.py
    [-- preview_dir [name ...]]

Reads Art/Environment/Buildings/Meshy/<name>.glb like
blender_buildings_to_fbx.py (same size and turn, so the parts lie exactly
where SM_<Name> lies) and writes to Art/Environment/Buildings:

* SM_<Name>_Shell.fbx: the walls up to the eaves with the door cut open,
  the wall that faces the camera (north) cut down to CUT over the floor,
  new inner wall faces, wall tops, a floor and the shop's fittings.
  Slot 0 is the Meshy material, slot 1 M_ShopInterior on the
  T_ShopInterior_D colour atlas (MI_Bld_ShopInterior,
  ue_buildings_import.py).
* SM_<Name>_Roof.fbx: the rest, the roof and the north wall over the cut
  with its sign, and a collision box (UCX) over the room from above her
  capsule's middle to the ridge. ue_dress_border.py places it as an actor
  of its own with camera collision, tagged HideWhole: the camera rays or
  the trace straight up from her (CameraOcclusionComponent) hit the box
  while she is inside or behind the shop, and the whole roof is hidden.
* T_ShopInterior_D.png: the atlas, 8 x 8 flat colour cells.
* Shops.json: per shop, in the mesh's space (cm, UE axes, before the
  placement scale): blocking boxes (walls with the door gap, fittings,
  what stands outside on the apron, the raised floor), Kenney props,
  lamps, text signs and the talk point of a shop NPC. ue_dress_border.py
  reads it.

The low stub of the north wall still reads as a wall; behind it she
shows as a silhouette. With a preview_dir, renders each
shop from the game camera's side with and without the roof; with names
after it, converts only those shops.
"""
import json
import math
import os
import random
import sys

import bmesh
import bpy
import numpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True  # no __pycache__ in the repo
import blender_buildings_to_fbx as B  # noqa: E402

# BP_Chicken's capsule (its CDO, read in the editor), cm in the level. A
# door is opened to at least the capsule plus DOOR_SPARE; the trace up
# starts at the capsule's middle, so the roof box starts BOX_GAP over it
# (and never under the cut).
RADIUS = 25.0
HALF_HEIGHT = 33.0
DOOR_SPARE = 20.0
BOX_GAP = 15.0
CUT = 100.0  # height of the north wall's stub over the floor, cm
T = 0.1  # wall thickness kept inside the shell, model meters
REACH = 0.4  # how far before the north wall its signs and awnings reach
# The shops, in model meters (front -Y, as blender_buildings_to_fbx.py
# leaves them): size in the level (YARDS of ue_dress_border.py), the
# outer wall planes (x0, x1, y0, y1), the top of the side walls (eaves),
# the door in the front wall (x0, x1, top), the side that faces north,
# to the camera: "front" (heading 0) or "right" (+X, heading 90), the
# open door leaf (hinge side, opening angle out of the wall in degrees,
# width) and the floor's atlas cell ("checker": dark and light tiles).
# A "closed" shop (the WC) has no door and no inside: everything over the
# cut is its roof, so it gets out of the way of the camera too.
SHOPS = {
    "friseur": dict(size=0.9, walls=(-2.16, 2.18, -1.6, 1.96),
                    eaves=2.35, door=(-0.4, 0.4, 1.74), north="front",
                    leaf=("x0", 120, 0.8), floor="checker"),
    "zigaretten": dict(size=0.9, walls=(-2.94, 2.92, -0.62, 2.46),
                       eaves=2.6, door=(-0.46, 0.46, 1.85),
                       north="front", leaf=("x0", 120, 0.9),
                       floor="vinyl",
                       # The parasol on the apron (x, y, how far north)
                       parasol=(1.76, -1.6, 1.0)),
    "sklep": dict(size=0.9, walls=(-2.94, 2.94, -1.92, 2.54), eaves=2.55,
                  door=(0.22, 1.52, 1.78), north="front", floor="floor"),
    "bar": dict(size=0.9, walls=(-2.28, 2.28, -1.24, 1.72), eaves=2.7,
                door=(0.9, 2.0, 2.15), north="right",
                leaf=("x1", 100, 0.95), floor="floorwarm",
                # Meshy faces to drop (x0, x1, y0, y1, z0, z1): its awning
                # hung nearly straight down; fit_bar makes a new one
                drop=[(-2.15, 0.45, -2.0, -1.27, 1.92, 2.5)]),
    "kantor": dict(size=0.85, walls=(-1.8, 1.82, -1.8, 1.8), eaves=2.55,
                   door=(-1.2, -0.3, 1.86), north="front",
                   leaf=("x0", 120, 0.9), floor="oak"),
    # Just north of the bar: over the cut it would hide the bar's room
    "toilet": dict(size=0.9, walls=(-1.32, 1.32, -0.8, 1.53), eaves=2.0,
                   closed=True),
}
# The atlas cells, sRGB. Clean and modern: white walls, pale floors
COLORS = {
    "wall": (0.93, 0.93, 0.91), "walltop": (0.82, 0.82, 0.8),
    "floor": (0.74, 0.75, 0.74), "floorwarm": (0.8, 0.74, 0.64),
    "graphite": (0.2, 0.21, 0.23), "steel": (0.68, 0.7, 0.72),
    "wood": (0.72, 0.55, 0.36), "black": (0.05, 0.05, 0.06),
    "mirror": (0.74, 0.82, 0.86), "frosted": (0.87, 0.9, 0.92),
    "green": (0.12, 0.56, 0.22), "red": (0.84, 0.13, 0.09),
    "pink": (0.93, 0.64, 0.68), "yellow": (0.96, 0.8, 0.2),
    "blue": (0.16, 0.36, 0.76), "orange": (0.95, 0.52, 0.12),
    "purple": (0.5, 0.28, 0.62), "cyan": (0.2, 0.7, 0.78),
    "cardboard": (0.62, 0.47, 0.3), "cream": (0.95, 0.9, 0.78),
    "glassdark": (0.24, 0.36, 0.4), "leather": (0.09, 0.09, 0.1),
    "screen": (0.3, 0.56, 0.86), "white": (0.98, 0.98, 0.98),
    "brown": (0.42, 0.27, 0.16), "kebab": (0.6, 0.36, 0.18),
    # Mid-tone floors, so the white chicken stands out
    "vinyl": (0.47, 0.49, 0.5), "oak": (0.55, 0.4, 0.27),
    "checkdark": (0.24, 0.25, 0.27), "checklight": (0.7, 0.71, 0.72),
    "rope": (0.62, 0.08, 0.1),
}
# The mirror cell is painted with a gradient and highlights instead of a
# flat colour (atlas()); its faces get the whole cell
CELL = {name: i for i, name in enumerate(COLORS)}
GOODS = {
    "bottles": ["pink", "white", "blue", "black", "cyan", "purple"],
    "packs": ["red", "white", "blue", "yellow", "black", "green", "red",
              "white", "white"],
    "grocery": ["red", "yellow", "orange", "green", "blue", "cream",
                "brown", "white", "purple"],
    "household": ["white", "blue", "cyan", "purple", "green", "yellow"],
    "bread": ["cream", "wood", "brown", "orange", "cream"],
    "sweets": ["purple", "red", "yellow", "orange", "blue", "pink",
               "brown"],
    "drinks": ["green", "brown", "red", "orange", "cyan", "white",
               "yellow"],
}
# Which way a shelf, fridge or counter opens: its front and right
FACES = {"-y": ((0, -1), (1, 0)), "+y": ((0, 1), (-1, 0)),
         "-x": ((-1, 0), (0, -1)), "+x": ((1, 0), (0, 1))}
K = "/Game/Environment/Kenney/"
# Kenney furniture faces its own -Y (model axes)
KENNEY_FRONT = -90.0


class Shop:
    """One shop's new geometry (material slot 1) and its level data."""

    def __init__(self, name, spec, bm, rng):
        self.name = name
        self.bm = bm
        self.uv = bm.loops.layers.uv.active
        self.part = bm.faces.layers.int.get("part")
        self.rng = rng
        self.size = spec["size"]
        x0, x1, y0, y1 = spec["walls"]
        self.inner = (x0 + T, x1 - T, y0 + T, y1 - T)
        self.blocks = []
        self.props = []
        self.lamps = []
        self.signs = []
        self.talk = None

    def quad(self, pts, color, roof=False):
        verts = [self.bm.verts.new(p) for p in pts]
        face = self.bm.faces.new(verts)
        face.material_index = 1
        face[self.part] = 1 if roof else 0
        u = (CELL[color] % 8 + 0.5) / 8
        v = (CELL[color] // 8 + 0.5) / 8
        k = 0.055 if color == "mirror" else 0.02
        for loop, (du, dv) in zip(face.loops, ((-1, -1), (1, -1), (1, 1),
                                               (-1, 1))):
            loop[self.uv].uv = (u + du * k, v + dv * k)

    def box(self, lo, hi, color, solid=False, bottom=False, roof=False):
        """An axis box from corner lo to corner hi, outward faces."""
        (a, b, c), (d, e, f) = lo, hi
        for pts in ([(a, b, f), (d, b, f), (d, e, f), (a, e, f)],
                    [(a, b, c), (d, b, c), (d, b, f), (a, b, f)],
                    [(d, e, c), (a, e, c), (a, e, f), (d, e, f)],
                    [(a, e, c), (a, b, c), (a, b, f), (a, e, f)],
                    [(d, b, c), (d, e, c), (d, e, f), (d, b, f)]):
            self.quad(pts, color, roof)
        if bottom:
            self.quad([(a, e, c), (d, e, c), (d, b, c), (a, b, c)], color,
                      roof)
        if solid:
            self.blocks.append((lo, hi))

    def slab(self, p, d, length, thick, z0, z1, color):
        """A box turned in plan: from p along the unit vector d."""
        n = (-d[1] * thick / 2, d[0] * thick / 2)
        q = (p[0] + d[0] * length, p[1] + d[1] * length)
        ring = [(p[0] - n[0], p[1] - n[1]), (q[0] - n[0], q[1] - n[1]),
                (q[0] + n[0], q[1] + n[1]), (p[0] + n[0], p[1] + n[1])]
        for k in range(4):
            (a, b), (e, f) = ring[k], ring[(k + 1) % 4]
            self.quad([(a, b, z0), (e, f, z0), (e, f, z1), (a, b, z1)],
                      color)
        self.quad([(a, b, z1) for a, b in ring], color)

    def local(self, c, face, d, u0, u1, v0, v1, z0, z1, color):
        """A box given across (u) and from the back (v) of a fitting."""
        f, r = FACES[face]
        p = [(c[0] + r[0] * u + f[0] * (v - d / 2),
              c[1] + r[1] * u + f[1] * (v - d / 2))
             for u, v in ((u0, v0), (u1, v1))]
        self.box((min(p[0][0], p[1][0]), min(p[0][1], p[1][1]), z0),
                 (max(p[0][0], p[1][0]), max(p[0][1], p[1][1]), z1), color)

    def prism(self, c, r, z0, z1, color, n=8):
        ring = [(c[0] + r * math.cos(2 * math.pi * k / n),
                 c[1] + r * math.sin(2 * math.pi * k / n)) for k in range(n)]
        for k in range(n):
            (a, b), (d, e) = ring[k], ring[(k + 1) % n]
            self.quad([(a, b, z0), (d, e, z0), (d, e, z1), (a, b, z1)],
                      color)
        top = [self.bm.verts.new((a, b, z1)) for a, b in ring]
        face = self.bm.faces.new(top)
        face.material_index = 1
        face[self.part] = 0
        for loop in face.loops:
            loop[self.uv].uv = ((CELL[color] % 8 + 0.5) / 8,
                                (CELL[color] // 8 + 0.5) / 8)

    def shelf(self, c, w, d, h, face, levels, goods, frame="white",
              z0=0.0):
        """A shelf unit full of goods, solid."""
        rng = self.rng
        self.local(c, face, d, -w / 2, w / 2, 0, 0.02, z0, z0 + h, frame)
        for s in (-1, 1):
            self.local(c, face, d, s * w / 2 - 0.015, s * w / 2 + 0.015,
                       0, d, z0, z0 + h, frame)
        self.local(c, face, d, -w / 2, w / 2, 0, d, z0, z0 + 0.1, frame)
        step = (h - 0.15) / levels
        for i in range(levels):
            z = z0 + 0.1 + i * step
            self.local(c, face, d, -w / 2, w / 2, 0, d, z, z + 0.02,
                       frame)
            u = -w / 2 + 0.03
            while True:
                iw = 0.09 if goods == "packs" else rng.uniform(0.06, 0.17)
                if u + iw > w / 2 - 0.03:
                    break
                ih = min(0.32, step - 0.04) * rng.uniform(0.6, 0.9)
                idp = (d - 0.04) * rng.uniform(0.6, 0.9)
                self.local(c, face, d, u, u + iw, d - 0.01 - idp, d - 0.01,
                           z + 0.02, z + 0.02 + ih,
                           rng.choice(GOODS[goods]))
                u += iw + rng.uniform(0.005, 0.02)
        self.local(c, face, d, -w / 2, w / 2, 0, d, z0 + h - 0.03,
                   z0 + h, frame)
        f, r = FACES[face]
        span = (abs(r[0]) * w + abs(f[0]) * d, abs(r[1]) * w + abs(f[1]) * d)
        self.blocks.append(((c[0] - span[0] / 2, c[1] - span[1] / 2, 0),
                            (c[0] + span[0] / 2, c[1] + span[1] / 2, h)))

    def fridge(self, c, w, d, h, face, doors, z0=0.0):
        """A drinks fridge: white body, glass doors, bottles behind."""
        self.local(c, face, d, -w / 2, w / 2, 0, d, z0, z0 + h, "white")
        self.local(c, face, d, -w / 2 + 0.04, w / 2 - 0.04, d, d + 0.005,
                   z0 + 0.15, z0 + h - 0.2, "glassdark")
        self.local(c, face, d, -w / 2 + 0.04, w / 2 - 0.04, d, d + 0.005,
                   z0 + h - 0.17, z0 + h - 0.05, "green")
        for k in range(doors + 1):
            u = -w / 2 + 0.04 + k * (w - 0.08) / doors
            self.local(c, face, d, u - 0.015, u + 0.015, d, d + 0.012,
                       z0 + 0.15, z0 + h - 0.2, "steel")
        rows = 4
        for i in range(rows):
            z = z0 + 0.2 + i * (h - 0.4) / rows
            u = -w / 2 + 0.07
            while u < w / 2 - 0.12:
                self.local(c, face, d, u, u + 0.05, d + 0.005, d + 0.008,
                           z, z + 0.22, self.rng.choice(GOODS["drinks"]))
                u += 0.075
        f, r = FACES[face]
        span = (abs(r[0]) * w + abs(f[0]) * d, abs(r[1]) * w + abs(f[1]) * d)
        self.blocks.append(((c[0] - span[0] / 2, c[1] - span[1] / 2, 0),
                            (c[0] + span[0] / 2, c[1] + span[1] / 2, h)))

    def chest(self, lo, hi, goods, glass=True):
        """A low cooler (glass lid) or display table with goods on top:
        the camera looks down on it, so its goods read from above."""
        self.box(lo, hi, "white", solid=True)
        z = hi[2]
        if glass:
            self.box((lo[0] + 0.04, lo[1] + 0.04, z),
                     (hi[0] - 0.04, hi[1] - 0.04, z + 0.005), "glassdark")
            z += 0.005
        x = lo[0] + 0.07
        while x < hi[0] - 0.12:
            y = lo[1] + 0.07
            while y < hi[1] - 0.12:
                top = z + (0.003 if glass else self.rng.uniform(0.04, 0.1))
                self.box((x, y, z), (x + 0.08, y + 0.08, top),
                         self.rng.choice(GOODS[goods]))
                y += 0.1
            x += 0.1


def fit_friseur(s, zs):
    """Two stations on the back wall, a wash basin, a desk, chairs."""
    xi0, xi1, yi0, yi1 = s.inner
    for xc in (-0.85, 0.85):
        s.box((xc - 0.42, yi1 - 0.01, 0.96), (xc + 0.42, yi1, 1.99),
              "white")
        s.box((xc - 0.38, yi1 - 0.02, 1.0), (xc + 0.38, yi1 - 0.01, 1.95),
              "mirror")
        s.box((xc - 0.5, yi1 - 0.38, zs), (xc + 0.5, yi1, 0.82), "white",
              solid=True)
        s.box((xc - 0.52, yi1 - 0.4, 0.82), (xc + 0.52, yi1, 0.86), "wood")
        for k in range(3):
            bx = xc - 0.3 + k * 0.12
            s.box((bx, yi1 - 0.2, 0.86), (bx + 0.05, yi1 - 0.15, 1.0),
                  s.rng.choice(GOODS["bottles"]))
        # A barber chair turned to the mirror, its back to the room
        y = 1.05
        s.prism((xc, y), 0.24, zs, zs + 0.04, "steel")
        s.prism((xc, y), 0.05, zs + 0.04, 0.4, "steel")
        s.box((xc - 0.25, y - 0.22, 0.4), (xc + 0.25, y + 0.23, 0.52),
              "leather")
        s.box((xc - 0.24, y - 0.3, 0.45), (xc + 0.24, y - 0.22, 1.08),
              "leather")
        for side in (-1, 1):
            ax = xc + side * 0.27
            s.box((ax - 0.03, y - 0.2, 0.52), (ax + 0.03, y + 0.2, 0.68),
                  "leather")
        s.box((xc - 0.15, y + 0.3, 0.12), (xc + 0.15, y + 0.42, 0.16),
              "steel")
        s.blocks.append(((xc - 0.3, y - 0.3, 0), (xc + 0.3, y + 0.42, 1.1)))
    # Hair wash basin on the west wall
    s.box((xi1 - 0.45, 0.15, zs), (xi1, 0.75, 0.85), "white", solid=True)
    s.box((xi1 - 0.4, 0.22, 0.85), (xi1 - 0.05, 0.68, 0.95), "black")
    # Hair products on a low cabinet by the east wall
    s.chest((xi0, 0.75, zs), (xi0 + 0.4, 1.5, 0.8), "bottles", glass=False)
    # Reception desk by the door; the hairdresser is out
    s.box((1.1, -0.85, zs), (1.8, -0.45, 0.88), "white", solid=True)
    s.box((1.1, -0.86, zs + 0.05), (1.8, -0.85, 0.8), "pink")
    s.box((1.08, -0.87, 0.88), (1.82, -0.43, 0.92), "wood")
    s.props.append(("furniture_kit/SM_radio", (1.6, -0.6, 0.92), -90, 0.9))
    # A card standing on the desk, to the camera
    s.box((1.15, -0.84, 0.92), (1.75, -0.82, 1.14), "white")
    s.signs.append(("ZARAZ WRACAM", (1.45, -0.845, 1.03), 7, "black", False))
    for y in (-0.5, 0.0):
        s.props.append(("furniture_kit/SM_chair", (xi0 + 0.25, y, zs), 0,
                        1.8))
    s.box((xi0 + 0.02, 1.53, zs), (xi0 + 0.32, 1.83, 0.4), "white",
          solid=True)
    s.props.append(("nature_kit/SM_plant_bushDetailed",
                    (xi0 + 0.17, 1.68, 0.4), 0, 0.6))
    s.lamps.append([(0.0, 0.2, 2.05), 1.0])


def fit_zigaretten(s, zs):
    """A wall of cigarette packs behind the counter, a fridge, sweets.
    The seller stands outside at his door (ue_dress_border.py)."""
    xi0, xi1, yi0, yi1 = s.inner
    for xc in (-1.75, 0.0, 1.75):
        s.shelf((xc, yi1 - 0.16), 1.7, 0.32, 2.1, "-y", 7, "packs")
    s.box((-1.4, 1.3, zs), (1.4, 1.85, 0.95), "white", solid=True)
    s.box((-1.4, 1.29, zs + 0.08), (1.4, 1.3, 0.9), "red")
    s.box((-1.45, 1.27, 0.95), (1.45, 1.88, 1.0), "graphite")
    s.box((0.6, 1.5, 1.0), (0.95, 1.8, 1.12), "black")
    s.box((0.65, 1.62, 1.12), (0.9, 1.65, 1.32), "screen")
    for k in range(6):
        s.box((-1.2 + k * 0.08, 1.35, 1.0), (-1.14 + k * 0.08, 1.45, 1.1),
              s.rng.choice(GOODS["sweets"]))
    s.box((-0.65, 1.31, 1.0), (0.05, 1.33, 1.22), "white")
    s.signs.append(("ZARAZ WRACAM", (-0.3, 1.305, 1.11), 8, "black", False))
    # Low by the side walls: the camera sees them from above
    s.chest((xi0, -0.2, zs), (xi0 + 0.6, 1.0, 0.85), "drinks")
    s.chest((xi1 - 0.6, -0.1, zs), (xi1, 1.0, 0.75), "sweets", glass=False)
    s.props.append(("furniture_kit/SM_cardboardBoxClosed", (2.1, 2.05, zs),
                    0, 1.2))
    s.props.append(("furniture_kit/SM_cardboardBoxClosed",
                    (2.12, 2.02, zs + 0.34), 20, 1.1))
    s.lamps.append([(0.0, 1.0, 2.35), 1.0])


def fit_sklep(s, zs):
    """A small modern 24 h shop with a self-checkout and no clerk."""
    xi0, xi1, yi0, yi1 = s.inner
    for xc in (-2.2, -1.2, -0.2):
        s.fridge((xc, yi1 - 0.3), 1.0, 0.6, 1.95, "-y", 2)
    s.shelf((1.6, yi1 - 0.23), 2.0, 0.45, 1.5, "-y", 3, "bread")
    # Two low rows that face the camera, the way from the door between
    s.shelf((-1.4, 0.6), 2.2, 0.45, 1.2, "-y", 3, "grocery")
    s.shelf((1.85, 0.6), 1.5, 0.45, 1.2, "-y", 3, "household")
    s.chest((xi0, -0.9, zs), (xi0 + 0.6, 0.2, 0.85), "sweets")
    # Fruit crates in front of the grocery row
    for xc, fruit, sc in ((-1.8, "apple", 0.8), (-1.3, "orange", 0.9)):
        s.box((xc - 0.22, -0.35, zs), (xc + 0.22, 0.0, 0.45), "wood",
              solid=True)
        for k in range(6):
            s.props.append(("food_kit/SM_" + fruit,
                            (xc - 0.14 + (k % 3) * 0.14,
                             -0.25 + (k // 3) * 0.15, 0.45), k * 50, sc))
    # Self-checkout: a white kiosk, its screen to the camera
    s.box((-1.0, -0.7, zs), (-0.5, -0.3, 0.95), "white", solid=True)
    s.box((-0.95, -0.55, 0.95), (-0.55, -0.45, 1.35), "graphite")
    s.box((-0.92, -0.56, 1.0), (-0.58, -0.55, 1.32), "screen")
    s.box((-1.1, -0.52, 1.42), (-0.4, -0.5, 1.62), "green")
    s.signs.append(("KASA", (-0.75, -0.53, 1.47), 10, "white", False))
    for k in range(4):
        s.box((1.65, -1.6, zs + k * 0.12), (2.05, -1.3, zs + 0.1 + k * 0.12),
              "red")
    s.blocks.append(((1.65, -1.6, 0), (2.05, -1.3, 0.5)))
    s.lamps.append([(-1.3, 0.3, 2.3), 0.7])
    s.lamps.append([(1.3, 0.3, 2.3), 0.7])


def fit_bar(s, zs):
    """A grill kitchen at the south end, a bar with stools, two tables."""
    xi0, xi1, yi0, yi1 = s.inner
    s.box((xi0, -0.9, zs), (xi0 + 0.58, 1.5, 0.9), "steel", solid=True)
    s.box((xi0 + 0.08, -0.6, 0.9), (xi0 + 0.48, 0.2, 0.93), "black")
    s.box((xi0 + 0.08, 0.4, 0.9), (xi0 + 0.48, 0.9, 1.1), "steel")
    s.box((xi0 + 0.12, 0.45, 1.1), (xi0 + 0.44, 0.85, 1.11), "black")
    s.prism((xi0 + 0.3, 1.2), 0.12, 0.9, 0.95, "steel")
    s.prism((xi0 + 0.3, 1.2), 0.09, 0.95, 1.5, "kebab")
    s.box((xi0, -0.8, 1.85), (xi0 + 0.68, 1.0, 2.25), "steel")
    # The bar: its front to the room (north)
    s.box((-1.25, yi0, zs), (-0.85, 1.1, 1.0), "graphite", solid=True)
    s.box((-1.28, yi0, 1.0), (-0.8, 1.12, 1.05), "wood")
    s.props.append(("furniture_kit/SM_radio", (-1.05, 0.85, 1.05), 0, 0.9))
    for y in (-0.8, 0.1, 1.0):
        s.props.append(("furniture_kit/SM_stoolBar", (-0.6, y, zs), 0, 1.6))
    # Two small tables with a way between them to the bar for her
    for y in (-0.5, 1.0):
        s.prism((0.55, y), 0.2, zs, zs + 0.03, "graphite")
        s.prism((0.55, y), 0.04, zs + 0.03, 0.72, "graphite")
        s.prism((0.55, y), 0.3, 0.72, 0.76, "wood")
        s.blocks.append(((0.25, y - 0.3, 0), (0.85, y + 0.3, 0.76)))
        for side in (-1, 1):
            s.props.append(("furniture_kit/SM_chair",
                            (0.55, y + side * 0.42, zs), 180 + side * 90,
                            1.7))
    s.fridge((0.1, yi1 - 0.28), 0.8, 0.55, 1.8, "-y", 1)
    s.props.append(("furniture_kit/SM_trashcan", (1.9, -0.95, zs), 0, 1.4))
    s.lamps.append([(0.0, 0.25, 2.4), 1.0])
    # The door is in the east wall, which the camera sees edge on: a
    # blade sign over it reads from the north, and a paved way leads in
    y0 = SHOPS["bar"]["walls"][2]
    s.box((2.2, y0 - 1.0, 2.2), (2.24, y0 - 0.05, 2.62), "graphite")
    s.box((2.24, y0 - 0.96, 2.24), (2.25, y0 - 0.09, 2.58), "white")
    s.box((2.205, y0 - 0.06, 2.3), (2.235, y0, 2.36), "steel")
    s.signs.append(("BAR GRILL", (2.26, y0 - 0.525, 2.41), 15, "black",
                    False))
    s.box((0.8, y0 - 2.4, 0), (2.1, y0 - 0.6, 0.012), "walltop")
    # A new striped awning over the hatch, at a gentle slope
    for k in range(12):
        a, b = -2.0 + k * 0.2, -1.8 + k * 0.2
        color = "red" if k % 2 == 0 else "white"
        s.quad([(a, y0 - 0.02, 2.42), (b, y0 - 0.02, 2.42),
                (b, y0 - 0.75, 2.2), (a, y0 - 0.75, 2.2)], color)
        s.quad([(a, y0 - 0.75, 2.2), (b, y0 - 0.75, 2.2),
                (b, y0 - 0.75, 2.08), (a, y0 - 0.75, 2.08)], color)


def fit_kantor(s, zs):
    """A lobby and the closed cash office: the clerk is behind frosted
    glass, so nobody is modelled. The talk point is at his window."""
    xi0, xi1, yi0, yi1 = s.inner
    top = SHOPS["kantor"]["eaves"]
    # The office ceiling hides with the roof; from the lobby the clerk is
    # behind frosted glass
    s.box((xi0, 0.35, zs), (xi1, 0.45, top), "wall")
    s.box((xi0, 0.45, top - 0.05), (xi1, yi1, top), "walltop", roof=True)
    s.blocks.append(((xi0, 0.35, 0), (xi1, yi1, top)))
    # The teller window: a glazed pane in a steel frame, a tray under it
    s.box((0.12, 0.33, 0.9), (0.98, 0.35, 0.95), "steel")
    s.box((0.12, 0.33, 1.75), (0.98, 0.35, 1.8), "steel")
    for x in (0.12, 0.93):
        s.box((x, 0.33, 0.9), (x + 0.05, 0.35, 1.8), "steel")
    s.box((0.17, 0.335, 0.95), (0.93, 0.345, 1.75), "frosted")
    s.box((0.4, 0.31, 0.95), (0.7, 0.35, 1.0), "black")
    s.box((0.05, 0.08, 0.88), (1.05, 0.35, 0.95), "wood")
    s.box((0.05, 0.3, zs), (1.05, 0.35, 0.88), "wood")
    s.blocks.append(((0.05, 0.08, 0), (1.05, 0.35, 0.95)))
    # Rates board, big enough to read
    s.box((-1.6, 0.33, 1.0), (-0.15, 0.35, 1.95), "black")
    for i, flag in enumerate(("blue", "red", "green", "yellow", "cyan")):
        z = 1.72 - i * 0.15
        s.box((-1.5, 0.32, z), (-1.36, 0.33, z + 0.1), flag)
        s.box((-1.26, 0.32, z), (-0.25, 0.33, z + 0.1), "yellow")
    s.signs.append(("KURSY WALUT", (-0.875, 0.31, 2.05), 10, "black",
                    False))
    # The clerk's side: desk, money counter, monitor, chair and a safe
    s.box((0.05, 0.75, zs), (1.05, 1.2, 0.78), "wood", solid=True)
    s.box((0.35, 0.85, 0.78), (0.6, 1.05, 0.9), "graphite")
    s.box((0.7, 1.05, 0.78), (0.98, 1.1, 1.05), "black")
    s.box((0.72, 1.045, 0.82), (0.96, 1.05, 1.03), "screen")
    s.props.append(("furniture_kit/SM_chair", (0.55, 1.45, zs), -90, 1.7))
    s.box((xi1 - 0.6, yi1 - 0.55, zs), (xi1 - 0.05, yi1 - 0.05, 1.0),
          "graphite", solid=True)
    s.prism((xi1 - 0.33, yi1 - 0.56), 0.1, 0.45, 0.47, "steel")
    s.box((xi0 + 0.05, yi1 - 0.4, zs), (xi0 + 0.85, yi1 - 0.05, 1.6),
          "wood", solid=True)
    # A queue rope keeps the way to the window
    for x in (-0.1, 0.55, 1.2):
        s.prism((x, -0.75), 0.12, zs, zs + 0.03, "steel")
        s.prism((x, -0.75), 0.025, zs + 0.03, 0.85, "steel")
    s.box((-0.1, -0.765, 0.74), (1.2, -0.735, 0.78), "rope")
    s.blocks.append(((-0.13, -0.78, 0), (1.23, -0.72, 0.85)))
    s.box((1.35, 0.0, zs), (1.65, 0.3, 0.4), "white", solid=True)
    s.props.append(("nature_kit/SM_plant_bushDetailed", (1.5, 0.15, 0.4), 0,
                    0.6))
    s.props.append(("furniture_kit/SM_trashcan", (-1.5, 0.15, zs), 0, 1.3))
    s.talk = {"marker": "MK_NPC_KantorClerk", "at": [0.55, -0.2, zs],
              "radius": 80.0}
    s.lamps.append([(0.0, -0.6, 2.3), 0.8])


FIT = {"friseur": fit_friseur, "zigaretten": fit_zigaretten,
       "sklep": fit_sklep, "bar": fit_bar, "kantor": fit_kantor}
ACCENT = {"friseur": "pink", "zigaretten": "red", "sklep": "green",
          "bar": "graphite", "kantor": "yellow"}


def atlas():
    img = bpy.data.images.new("T_ShopInterior_D", 512, 512)
    px = numpy.ones((512, 512, 4), dtype=numpy.float32)
    for name, rgb in COLORS.items():
        c = CELL[name]
        row, col = c // 8, c % 8
        px[row * 64:(row + 1) * 64, col * 64:(col + 1) * 64, :3] = rgb
    # The mirror: pale blue at the top to a deeper blue, two highlights
    c = CELL["mirror"]
    row, col = c // 8, c % 8
    for j in range(64):
        for i in range(64):
            t = j / 63
            rgb = [0.38 + 0.42 * t, 0.5 + 0.36 * t, 0.62 + 0.3 * t]
            if (i - j) % 64 in range(12, 20) or (i - j) % 64 in range(26, 29):
                rgb = [min(1.0, v + 0.14) for v in rgb]
            px[row * 64 + j, col * 64 + i, :3] = rgb
    img.pixels.foreach_set(px.ravel())
    img.filepath_raw = os.path.join(B.OUT, "T_ShopInterior_D.png")
    img.file_format = "PNG"
    img.save()
    mat = bpy.data.materials.new("M_ShopInterior")
    mat.use_nodes = True
    tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = img
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def apron(tree, spec, start, lo, hi):
    """Boxes over what stands outside the walls (pots, racks, pipes):
    a 10 cm grid of rays down from start, merged into boxes."""
    x0, x1, y0, y1 = spec["walls"]
    dx0, dx1, dz = spec["door"]
    rows = {}
    n_x = int((hi.x - lo.x) / 0.1)
    n_y = int((hi.y - lo.y) / 0.1)
    for j in range(n_y):
        cy = lo.y + (j + 0.5) * 0.1
        for i in range(n_x):
            cx = lo.x + (i + 0.5) * 0.1
            if x0 - 0.02 < cx < x1 + 0.02 and y0 - 0.02 < cy < y1 + 0.02:
                continue
            if dx0 - 0.1 < cx < dx1 + 0.1 and cy < y0:
                continue
            # Overhead, under a parasol or an awning (a face turned down,
            # or a thin sheet), look on below it
            down = Vector((0, 0, -1))
            hit = tree.ray_cast(Vector((cx, cy, start)), down)
            while hit[0] is not None and hit[0].z > 1.2:
                under = tree.ray_cast(hit[0] + down * 0.01, down)
                if hit[1].z < -0.2:
                    hit = under
                elif (under[0] is not None and under[1].z < -0.2 and
                      hit[0].z - under[0].z < 0.15):
                    hit = tree.ray_cast(under[0] + down * 0.01, down)
                else:
                    break
            if hit[0] is not None and hit[0].z > 0.12:
                rows.setdefault(j, []).append(i)
    runs = []
    for j in sorted(rows):
        cells = rows[j]
        start = prev = cells[0]
        for i in cells[1:] + [None]:
            if i is not None and i == prev + 1:
                prev = i
                continue
            runs.append([start, prev, j, j])
            if i is not None:
                start = prev = i
    merged = []
    for run in runs:
        last = next((m for m in merged if m[0] == run[0] and
                     m[1] == run[1] and m[3] == run[2] - 1), None)
        if last:
            last[3] = run[2]
        else:
            merged.append(run)
    return [((lo.x + i0 * 0.1, lo.y + j0 * 0.1, 0),
             (lo.x + (i1 + 1) * 0.1, lo.y + (j1 + 1) * 0.1, 1.0))
            for i0, i1, j0, j1 in merged]


def export_parts(obj, bm, title, spec, zb):
    """Splits the mesh by the part layer into the shell and the roof and
    writes both FBX files. The roof's collision is a box over the walls
    only, from zb up: the camera hides the roof while she is under it, not
    under the eaves. Returns the roof object and its top."""
    x0, x1, y0, y1 = spec["walls"]
    bm.to_mesh(obj.data)
    bm.free()
    roof = obj.copy()
    roof.data = obj.data.copy()
    bpy.context.scene.collection.objects.link(roof)
    for o_, keep in ((obj, 0), (roof, 1)):
        bm = bmesh.new()
        bm.from_mesh(o_.data)
        layer = bm.faces.layers.int.get("part")
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[layer] != keep],
                         context="FACES")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces],
                         context="VERTS")
        bm.to_mesh(o_.data)
        bm.free()
    top = max(v.co.z for v in roof.data.vertices)
    ucx = bpy.data.meshes.new("UCX")
    ucx.from_pydata([(x, y, z) for x in (x0, x1) for y in (y0, y1)
                     for z in (zb, top)], [],
                    [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6),
                     (0, 2, 6, 4), (1, 5, 7, 3)])
    hull = bpy.data.objects.new("UCX_SM_" + title + "_Roof", ucx)
    bpy.context.scene.collection.objects.link(hull)
    roof.name = roof.data.name = "SM_" + title + "_Roof"
    for other in bpy.context.scene.objects:
        other.select_set(other in (roof, hull))
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(B.OUT, roof.name + ".fbx"), use_selection=True,
        object_types={"MESH"}, global_scale=1.0, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_NONE", mesh_smooth_type="FACE",
        path_mode="STRIP", bake_anim=False)
    hull.hide_render = True
    B.export(obj, "SM_" + title + "_Shell")
    return roof, top


def close_shop(name, spec, obj, bm, title):
    """A closed building (the WC): everything over the cut is its roof,
    with a lid on the cut walls. Its blocking box stays the old one."""
    size = spec["size"]
    x0, x1, y0, y1 = spec["walls"]
    zc = CUT / 100 / size
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
                           plane_co=(0, 0, zc), plane_no=(0, 0, 1))
    part = bm.faces.layers.int.new("part")
    for f in bm.faces:
        f[part] = 1 if f.calc_center_median().z > zc else 0
    s = Shop(name, spec, bm, random.Random(name))
    s.quad([(x0 - 0.02, y0 - 0.02, zc), (x1 + 0.02, y0 - 0.02, zc),
            (x1 + 0.02, y1 + 0.02, zc), (x0 - 0.02, y1 + 0.02, zc)],
           "walltop")
    roof, top = export_parts(obj, bm, title, spec, zc)
    data = {"closed": True, "cut": round(zc * 100, 1),
            "box": [round((x0 + x1) * 50, 1), round(-(y0 + y1) * 50, 1),
                    round((zc + top) * 50, 1), round((x1 - x0) * 100, 1),
                    round((y1 - y0) * 100, 1), round((top - zc) * 100, 1)]}
    print("SHOP", title, "closed, cut", round(zc * size, 2))
    return obj, roof, data


def open_shop(name, spec):
    title, size_m, along, turns = B.MODELS[name]
    obj, image = B.load(name, size_m, along, turns)
    obj.material_slots[0].material.name = "M_" + title
    obj.data.materials.append(atlas())
    size = spec["size"]
    x0, x1, y0, y1 = spec["walls"]
    ze = spec["eaves"]
    north = spec.get("north", "front")
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    if "parasol" in spec:
        # Its canopy cut into the front wall: it goes (canopy, pole and
        # foot; not the facade or the rack beside it), and a new one
        # stands further north (open_shop adds it)
        px, py, dy = spec["parasol"]
        doomed = []
        for f in bm.faces:
            c = f.calc_center_median()
            r = math.hypot(c.x - px, c.y - py)
            rack = (0.7 < c.x < 1.55 and -1.42 < c.y < -1.08 and
                    c.z < 1.55)
            wall = (abs(f.normal.y) > 0.8 and
                    all(abs(v.co.y - y0) < 0.1 for v in f.verts))
            if not rack and not wall and (
                    r < 1.05 and 1.3 < c.z < 2.1 or r < 0.09 or
                    r < 0.3 and 0.035 < c.z < 0.12):
                doomed.append(f)
        bmesh.ops.delete(bm, geom=doomed, context="FACES")
    for a, b, c, d, e, f in spec.get("drop", []):
        bmesh.ops.delete(bm, geom=[
            g for g in bm.faces
            if a < g.calc_center_median().x < b and
            c < g.calc_center_median().y < d and
            e < g.calc_center_median().z < f], context="FACES")
    tree = BVHTree.FromBMesh(bm)
    pts = [v.co for v in bm.verts]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), 0))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), 0))
    if spec.get("closed"):
        return close_shop(name, spec, obj, bm, title)
    # The floor: the top of the step at the door
    dx0, dx1, dz = spec["door"]
    hit = tree.ray_cast(Vector(((dx0 + dx1) / 2, y0 - 0.05, 1.0)),
                        Vector((0, 0, -1)))
    zs = (hit[0].z if hit[0] is not None and hit[0].z < 0.25 else 0.0)
    zs = max(zs, 0.0) + 0.005
    zc = (zs * 100 * size + CUT) / 100 / size
    zb = max(zc, (zs * 100 * size + HALF_HEIGHT + BOX_GAP) / 100 / size)
    # Wide enough for her
    need = (RADIUS * 2 + DOOR_SPARE) / 100 / size
    if dx1 - dx0 < need:
        mid = (dx0 + dx1) / 2
        dx0, dx1 = mid - need / 2, mid + need / 2
    # The north wall's strip that goes with the roof reaches this far in
    front = y0 + T + 0.1
    right = x1 - T - 0.1
    planes = [((dx0, 0, 0), (1, 0, 0)), ((dx1, 0, 0), (1, 0, 0)),
              ((0, 0, dz), (0, 0, 1)), ((0, 0, zc), (0, 0, 1)),
              ((0, 0, ze), (0, 0, 1)), ((0, 0, zs + 0.01), (0, 0, 1))]
    planes.append(((0, front, 0), (0, 1, 0)) if north == "front" else
                  ((right, 0, 0), (1, 0, 0)))
    for co, no in planes:
        bmesh.ops.bisect_plane(
            bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
            plane_co=co, plane_no=no)
    part = bm.faces.layers.int.new("part")
    doomed = []
    for f in bm.faces:
        c = f.calc_center_median()
        door = (dx0 < c.x < dx1 and zs + 0.01 < c.z < dz and
                y0 - 0.15 < c.y < y0 + T + 0.08)
        # Meshy bits inside the room (a window tray reaching in)
        inside = (x0 + T + 0.02 < c.x < x1 - T - 0.02 and
                  front < c.y < y1 - T - 0.02 and
                  zs + 0.02 < c.z < ze)
        if door or inside:
            doomed.append(f)
            continue
        if north == "front":
            # The wall over the cut; what sticks out of it (signs, the
            # canopy) only over the door, so a locker or a rack stays
            strip = (x0 - 0.05 < c.x < x1 + 0.05 and c.y < front and
                     (c.y > y0 - 0.1 or c.z > dz and c.y > y0 - REACH))
        else:
            strip = (y0 - 0.05 < c.y < y1 + 0.05 and c.x > right and
                     (c.x < x1 + 0.1 or c.z > dz and c.x < x1 + REACH))
        f[part] = 1 if c.z > ze or (c.z > zc and strip) else 0
    bmesh.ops.delete(bm, geom=doomed, context="FACES")
    s = Shop(name, spec, bm, random.Random(name))
    xi0, xi1, yi0, yi1 = s.inner
    floor = spec.get("floor", "floor")
    tile = 0.3 if floor == "checker" else 99.0
    for i in range(int((xi1 - xi0) / tile) + 1):
        for j in range(int((yi1 - yi0) / tile) + 1):
            a, b = xi0 + i * tile, min(xi1, xi0 + (i + 1) * tile)
            c, d = yi0 + j * tile, min(yi1, yi0 + (j + 1) * tile)
            cell = floor
            if floor == "checker":
                cell = "checkdark" if (i + j) % 2 else "checklight"
            s.quad([(a, c, zs), (b, c, zs), (b, d, zs), (a, d, zs)], cell)
    s.quad([(dx0, y0 - 0.03, zs), (dx1, y0 - 0.03, zs), (dx1, yi0, zs),
            (dx0, yi0, zs)], "graphite")
    # Inner faces: the north wall up to the cut, the others to the eaves
    tops = {"front": zc if north == "front" else ze, "back": ze,
            "left": ze, "right": zc if north == "right" else ze}
    tf = tops["front"]
    s.quad([(xi0, yi0, zs), (dx0, yi0, zs), (dx0, yi0, tf), (xi0, yi0, tf)],
           "wall")
    s.quad([(dx1, yi0, zs), (min(xi1, right), yi0, zs),
            (min(xi1, right), yi0, tf), (dx1, yi0, tf)], "wall")
    if dz < tf:
        s.quad([(dx0, yi0, dz), (dx1, yi0, dz), (dx1, yi0, tf),
                (dx0, yi0, tf)], "wall")
    # Next to the north wall the others go only up to the cut, like it
    if north == "front":
        for x in (xi0, xi1):
            s.quad([(x, yi0, zs), (x, front, zs), (x, front, zc),
                    (x, yi0, zc)], "wall")
            s.quad([(x, front, zs), (x, yi1, zs), (x, yi1, ze),
                    (x, front, ze)], "wall")
        s.quad([(xi1, yi1, zs), (xi0, yi1, zs), (xi0, yi1, ze),
                (xi1, yi1, ze)], "wall")
    else:
        for y in (yi0, yi1):
            s.quad([(right, y, zs), (xi1, y, zs), (xi1, y, zc),
                    (right, y, zc)], "wall")
        s.quad([(right, yi1, zs), (xi0, yi1, zs), (xi0, yi1, ze),
                (right, yi1, ze)], "wall")
        s.quad([(xi0, yi1, zs), (xi0, yi0, zs), (xi0, yi0, ze),
                (xi0, yi1, ze)], "wall")
        s.quad([(xi1, yi0, zs), (xi1, yi1, zs), (xi1, yi1, zc),
                (xi1, yi0, zc)], "wall")
    # The north wall's inside over the cut goes with the roof: seen
    # through the door while the roof is on
    if north == "front":
        for a, b, c in ((xi0, dx0, zc), (dx1, xi1, zc), (dx0, dx1, dz)):
            if c < ze:
                s.quad([(a, yi0, c), (b, yi0, c), (b, yi0, ze),
                        (a, yi0, ze)], "wall", True)
    else:
        s.quad([(xi1, yi0, zc), (xi1, yi1, zc), (xi1, yi1, ze),
                (xi1, yi0, ze)], "wall", True)
    accent = ACCENT[name]
    for a, b in (((xi0, yi0 + 0.003), (dx0, yi0 + 0.003)),
                 ((dx1, yi0 + 0.003), (xi1, yi0 + 0.003)),
                 ((xi1, yi1 - 0.003), (xi0, yi1 - 0.003)),
                 ((xi0 + 0.003, yi1), (xi0 + 0.003, yi0)),
                 ((xi1 - 0.003, yi0), (xi1 - 0.003, yi1))):
        s.quad([(a[0], a[1], zs), (b[0], b[1], zs), (b[0], b[1], zs + 0.1),
                (a[0], a[1], zs + 0.1)], accent)
    # Door reveals and lintel; over the cut they belong to the roof
    for x, sign in ((dx0, 1), (dx1, -1)):
        for z0, z1, roof in ((zs, min(dz, tf), False), (tf, dz, True)):
            if z1 <= z0:
                continue
            p = [(x, y0 - 0.03, z0), (x, yi0, z0), (x, yi0, z1),
                 (x, y0 - 0.03, z1)]
            s.quad(p if sign < 0 else p[::-1], "graphite", roof)
    s.quad([(dx0, yi0, dz), (dx1, yi0, dz), (dx1, y0 - 0.03, dz),
            (dx0, y0 - 0.03, dz)], "graphite", dz > tf)
    # A dark aluminium frame round the door, an open glass leaf and a mat
    fy0, fy1 = y0 - 0.07, y0 + 0.02
    for xa, xb in ((dx0 - 0.06, dx0), (dx1, dx1 + 0.06)):
        s.box((xa, fy0, zs), (xb, fy1, min(dz, tf)), "graphite")
        if dz > tf:
            s.box((xa, fy0, tf), (xb, fy1, dz), "graphite", roof=True)
    s.box((dx0 - 0.06, fy0, dz), (dx1 + 0.06, fy1, dz + 0.06), "graphite",
          roof=dz > tf)
    if "leaf" in spec:
        side, angle, w = spec["leaf"]
        a = math.radians(angle)
        d = ((1 if side == "x0" else -1) * math.cos(a), -math.sin(a))
        h = (dx0 if side == "x0" else dx1, y0 - 0.08)
        top = min(dz, 2.1) - 0.02
        s.slab(h, d, w, 0.045, zs + 0.01, top, "graphite")
        s.slab((h[0] + d[0] * 0.07, h[1] + d[1] * 0.07), d, w - 0.14, 0.055,
               zs + 0.15, top - 0.1, "glassdark")
        s.slab((h[0] + d[0] * (w - 0.12), h[1] + d[1] * (w - 0.12)), d,
               0.03, 0.09, 0.95, 1.15, "steel")
        e = (h[0] + d[0] * w, h[1] + d[1] * w)
        s.blocks.append(((min(h[0], e[0]), min(h[1], e[1]), 0),
                         (max(h[0], e[0]), max(h[1], e[1]), top)))
    if "parasol" in spec:
        px, py, dy = spec["parasol"]
        py -= dy
        s.prism((px, py), 0.25, 0, 0.05, "steel")
        s.prism((px, py), 0.025, 0.05, 2.05, "steel")
        rim = [(px + 0.95 * math.cos(math.pi * k / 4),
                py + 0.95 * math.sin(math.pi * k / 4)) for k in range(8)]
        for k in range(8):
            (a, b), (e, f) = rim[k], rim[(k + 1) % 8]
            s.quad([(a, b, 1.68), (e, f, 1.68), (px, py, 2.05)], "red")
            s.quad([(e, f, 1.68), (a, b, 1.68), (px, py, 2.0)], "red")
    deep = 0.25 if zs > 0.04 else 0.55
    s.box((dx0, y0 - deep, 0), (dx1, y0 - 0.08, zs + 0.012), "graphite")
    # Wall tops over the hollow between the shell and the inner faces
    # The stub top stays just inside the facade, or it shows as a line
    # with the roof on; the others are under the eaves
    o = 0.04
    n = 0.02
    if north == "front":
        for a, b in ((x0 + n, dx0), (dx1, x1 - n)):
            s.quad([(a, y0 + n, zc), (b, y0 + n, zc), (b, yi0, zc),
                    (a, yi0, zc)], "walltop")
        if dz < zc:
            s.quad([(dx0, y0 + n, zc), (dx1, y0 + n, zc), (dx1, yi0, zc),
                    (dx0, yi0, zc)], "walltop")
        for a, b in ((x0 - o, xi0), (xi1, x1 + o)):
            s.quad([(a, front, ze), (b, front, ze), (b, y1 + o, ze),
                    (a, y1 + o, ze)], "walltop")
            s.quad([(b, front, zc), (a, front, zc), (a, front, ze),
                    (b, front, ze)], "walltop")
        s.quad([(xi0, yi1, ze), (xi1, yi1, ze), (xi1, y1 + o, ze),
                (xi0, y1 + o, ze)], "walltop")
    else:
        s.quad([(xi1, y0 + n, zc), (x1 - n, y0 + n, zc),
                (x1 - n, y1 - n, zc), (xi1, y1 - n, zc)], "walltop")
        for a, b in ((y0 - o, yi0), (yi1, y1 + o)):
            s.quad([(x0 - o, a, ze), (right, a, ze), (right, b, ze),
                    (x0 - o, b, ze)], "walltop")
            s.quad([(right, a, zc), (right, b, zc), (right, b, ze),
                    (right, a, ze)], "walltop")
        s.quad([(x0 - o, yi0, ze), (xi0, yi0, ze), (xi0, yi1, ze),
                (x0 - o, yi1, ze)], "walltop")
    FIT[name](s, zs)
    walls = [((x0 - 0.03, y0 - 0.03, 0), (dx0, yi0, ze)),
             ((dx1, y0 - 0.03, 0), (x1 + 0.03, yi0, ze)),
             ((x0 - 0.03, yi1, 0), (x1 + 0.03, y1 + 0.03, ze)),
             ((x0 - 0.03, yi0, 0), (xi0, yi1, ze)),
             ((xi1, yi0, 0), (x1 + 0.03, yi1, ze))]
    if zs > 0.04:
        walls += [((xi0, yi0, 0), (xi1, yi1, zs)),
                  ((dx0, y0 - 0.25, 0), (dx1, yi0, zs))]
    blocks = walls + s.blocks + apron(tree, spec, min(ze, 2.2) - 0.02, lo, hi)
    roof, top = export_parts(obj, bm, title, spec, zb)

    def ue(p):
        return [round(p[0] * 100, 1), round(-p[1] * 100, 1),
                round(p[2] * 100, 1)]

    data = {
        "blocks": [[round((a[0] + b[0]) * 50, 1),
                    round(-(a[1] + b[1]) * 50, 1),
                    round(abs(b[0] - a[0]) * 50, 1),
                    round(abs(b[1] - a[1]) * 50, 1), round(b[2] * 100, 1)]
                   for a, b in blocks],
        "props": [[K + p, ue(at), round(KENNEY_FRONT - facing, 1), sc]
                  for p, at, facing, sc in s.props],
        "lamps": [[ue(at), k] for at, k in s.lamps],
        "signs": [[t, ue(at), sz, COLORS[col], up]
                  for t, at, sz, col, up in s.signs],
        "talk": s.talk and dict(s.talk, at=ue(s.talk["at"])),
        # The roof's box (center, size) for ue_buildings_import.py, in
        # case the UCX does not come through the import
        "box": [round((x0 + x1) * 50, 1), round(-(y0 + y1) * 50, 1),
                round((zb + top) * 50, 1), round((x1 - x0) * 100, 1),
                round((y1 - y0) * 100, 1), round((top - zb) * 100, 1)],
        "cut": round(zc * 100, 1), "floor": round(zs * 100, 1),
        "door": [round(dx0 * 100, 1), round(dx1 * 100, 1)],
    }
    print("SHOP", title, "cut", round(zc * size, 2), "floor",
          round(zs * size, 3), "door", round((dx1 - dx0) * size, 2),
          "shell", len(obj.data.polygons), "roof", len(roof.data.polygons),
          "blocks", len(blocks))
    return obj, roof, data


def preview(obj, roof, spec, folder, name):
    """Game camera side: 50 degrees down from the north."""
    bpy.context.view_layer.update()
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "TEXTURE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 700
    data = bpy.data.cameras.new("Cam")
    data.type = "ORTHO"
    data.ortho_scale = max(obj.dimensions) * 1.25
    cam = bpy.data.objects.new("Cam", data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    p = math.radians(50)
    mid = obj.dimensions.z / 3
    if spec.get("north", "front") == "front":
        cam.location = (0, -30 * math.cos(p), mid + 30 * math.sin(p))
        cam.rotation_euler = (math.pi / 2 - p, 0, 0)
    else:
        cam.location = (30 * math.cos(p), 0, mid + 30 * math.sin(p))
        cam.rotation_euler = (math.pi / 2 - p, 0, math.pi / 2)
    for tag, shown in (("closed", True), ("open", False)):
        roof.hide_render = not shown
        scene.render.filepath = os.path.join(folder, name + "_" + tag)
        bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    path = os.path.join(B.OUT, "Shops.json")
    shops = json.load(open(path)) if os.path.exists(path) else {}
    for name, spec in SHOPS.items():
        if args[1:] and name not in args[1:]:
            continue
        obj, roof, data = open_shop(name, spec)
        shops[B.MODELS[name][0]] = data
        if args:
            preview(obj, roof, spec, args[0], name)
    with open(path, "w") as f:
        json.dump(shops, f, indent=1)
