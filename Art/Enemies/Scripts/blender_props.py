import bpy
import bmesh
import math
import random
import mathutils

MATS = {
    "Steel": (0.78, 0.8, 0.82, 0.9, 0.25),
    "DarkSteel": (0.18, 0.18, 0.2, 0.8, 0.45),
    "Handle": (0.08, 0.05, 0.04, 0.0, 0.6),
    "Wood": (0.55, 0.36, 0.18, 0.0, 0.7),
    "BlackPlastic": (0.03, 0.03, 0.03, 0.0, 0.5),
    "WhitePlastic": (0.92, 0.92, 0.9, 0.0, 0.4),
    "Lens": (1.0, 0.95, 0.6, 0.0, 0.1),
    "Paper": (0.93, 0.88, 0.75, 0.0, 0.8),
    "Flatbread": (0.86, 0.7, 0.45, 0.0, 0.8),
    "Toast": (0.6, 0.38, 0.16, 0.0, 0.8),
    "Meat": (0.42, 0.2, 0.1, 0.0, 0.7),
    "Pepper": (0.2, 0.55, 0.12, 0.0, 0.5),
    "Onion": (0.9, 0.85, 0.8, 0.0, 0.5),
    "Red": (0.75, 0.08, 0.06, 0.0, 0.5),
    "White": (0.95, 0.95, 0.93, 0.0, 0.5),
    "Leather": (0.35, 0.2, 0.1, 0.0, 0.7),
    "Coals": (1.0, 0.35, 0.05, 0.0, 0.9),
    "Ash": (0.12, 0.11, 0.1, 0.0, 0.9),
    "Gold": (0.9, 0.7, 0.2, 1.0, 0.3),
}


def mat(name):
    full = "M_Prop_" + name
    m = bpy.data.materials.get(full)
    if m:
        return m
    m = bpy.data.materials.new(full)
    r, g, b, metal, rough = MATS[name]
    m.diffuse_color = (r, g, b, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (r, g, b, 1)
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Roughness"].default_value = rough
    return m


class Builder:
    """Collects bmesh parts with material indices into one object."""

    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.mats = []

    def _mi(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def _add(self, geom_fn, m, matrix):
        tmp = bmesh.new()
        geom_fn(tmp)
        bmesh.ops.transform(tmp, matrix=matrix, verts=tmp.verts)
        mi = self._mi(m)
        for f in tmp.faces:
            f.material_index = mi
        me = bpy.data.meshes.new("_tmp")
        tmp.to_mesh(me)
        tmp.free()
        self.bm.from_mesh(me)
        bpy.data.meshes.remove(me)

    def cyl(self, m, r1, r2, length, matrix, seg=12, caps=True):
        def g(b):
            bmesh.ops.create_cone(b, cap_ends=caps, cap_tris=False,
                                  segments=seg, radius1=r1, radius2=r2,
                                  depth=length)
        self._add(g, m, matrix)

    def box(self, m, sx, sy, sz, matrix):
        def g(b):
            bmesh.ops.create_cube(b, size=1.0)
            bmesh.ops.scale(b, vec=(sx, sy, sz), verts=b.verts)
        self._add(g, m, matrix)

    def sphere(self, m, r, matrix, seg=12, rings=8):
        def g(b):
            bmesh.ops.create_uvsphere(b, u_segments=seg, v_segments=rings,
                                      radius=r)
        self._add(g, m, matrix)

    def torus(self, m, r_major, r_minor, matrix, seg=16, sides=6):
        def g(b):
            verts = []
            for i in range(seg):
                a = 2 * math.pi * i / seg
                ring = []
                for j in range(sides):
                    t = 2 * math.pi * j / sides
                    x = (r_major + r_minor * math.cos(t)) * math.cos(a)
                    y = (r_major + r_minor * math.cos(t)) * math.sin(a)
                    z = r_minor * math.sin(t)
                    ring.append(b.verts.new((x, y, z)))
                verts.append(ring)
            for i in range(seg):
                for j in range(sides):
                    a = verts[i][j]
                    bb = verts[(i + 1) % seg][j]
                    c = verts[(i + 1) % seg][(j + 1) % sides]
                    d = verts[i][(j + 1) % sides]
                    b.faces.new((a, bb, c, d))
        self._add(g, m, matrix)

    def finish(self):
        me = bpy.data.meshes.new(self.name)
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(self.name, me)
        bpy.context.scene.collection.objects.link(ob)
        return ob


def T(x=0, y=0, z=0):
    return mathutils.Matrix.Translation((x, y, z))


def R(axis, deg):
    return mathutils.Matrix.Rotation(math.radians(deg), 4, axis)


ALONG_X = R('Y', 90)


def knife():
    """Doner knife: grip at the origin, blade along +X, edge down."""
    b = Builder("SM_DonerKnife")
    b.cyl(mat("Handle"), 1.6, 1.4, 13, T(-6.5) @ ALONG_X)
    b.cyl(mat("Steel"), 2.2, 2.2, 0.8, T(0.4) @ ALONG_X)
    tmp_m = mat("Steel")

    def blade(bm):
        pts = [(0, 0), (40, 0), (45, 1.6), (44, 3.6), (0, 4.2)]
        top = [bm.verts.new((x, -0.2, z - 2.6)) for x, z in pts]
        bot = [bm.verts.new((x, 0.2, z - 2.6)) for x, z in pts]
        bm.faces.new(top)
        bm.faces.new(list(reversed(bot)))
        n = len(pts)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((top[i], top[j], bot[j], bot[i]))
        for v in top + bot:
            if v.co.z < -2.0:
                v.co.y *= 0.2
    b._add(blade, tmp_m, T(0.8))
    return b.finish()


def steel():
    b = Builder("SM_SharpeningSteel")
    b.cyl(mat("Handle"), 1.5, 1.5, 11, T(-5.5) @ ALONG_X)
    b.cyl(mat("Steel"), 2.0, 2.0, 0.8, T(0.4) @ ALONG_X)
    b.cyl(mat("Steel"), 0.7, 0.45, 26, T(13.8) @ ALONG_X, seg=8)
    b.torus(mat("Steel"), 1.4, 0.3, T(-11.6) @ R('Y', 90), seg=10)
    return b.finish()


def flashlight():
    b = Builder("SM_Flashlight")
    b.cyl(mat("BlackPlastic"), 1.8, 1.8, 16, T(0) @ ALONG_X)
    b.cyl(mat("BlackPlastic"), 1.8, 3.0, 4, T(10) @ ALONG_X)
    b.cyl(mat("Lens"), 2.7, 2.7, 0.4, T(12.1) @ ALONG_X)
    return b.finish()


def mini_kebab():
    b = Builder("SM_MiniKebab")
    b.cyl(mat("Paper"), 2.6, 3.2, 9, T(-2) @ ALONG_X)
    b.cyl(mat("Flatbread"), 3.2, 3.0, 4, T(4.5) @ ALONG_X)
    b.sphere(mat("Meat"), 2.6, T(6.5) @ mathutils.Matrix.Diagonal(
        (0.6, 1, 1, 1)), seg=8, rings=6)
    return b.finish()


def flatbread():
    b = Builder("SM_Flatbread")
    b.cyl(mat("Flatbread"), 15, 15, 1.2, T(0, 0, 0.6), seg=20)
    rnd = random.Random(3)
    for i in range(9):
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(2, 12)
        b.cyl(mat("Toast"), 1.3, 1.3, 0.2,
              T(r * math.cos(a), r * math.sin(a), 1.25), seg=8)
    return b.finish()


def chair():
    """White plastic chair, origin on the floor at the seat center."""
    b = Builder("SM_PlasticChair")
    w = mat("WhitePlastic")
    b.box(w, 46, 44, 3, T(0, 0, 44))
    b.box(w, 46, 3, 42, T(0, 23, 66) @ R('X', -12))
    for sx in (-1, 1):
        for sy in (-1, 1):
            m = T(sx * 19, sy * 18, 22) @ R('Y', -sx * 6) @ R('X', sy * 6)
            b.cyl(w, 2.0, 2.4, 44, m, seg=8)
        b.box(w, 3, 40, 3, T(sx * 23, 0, 52))
    return b.finish()


def skewer():
    """0.55 m skewer: grip ring at the origin, tip along +X."""
    b = Builder("SM_Skewer")
    b.cyl(mat("Steel"), 0.35, 0.2, 55, T(27.5) @ ALONG_X, seg=6)
    b.torus(mat("Steel"), 2.0, 0.35, T(-1.8) @ R('Y', 90), seg=10)
    order = ["Meat", "Pepper", "Meat", "Onion", "Meat", "Pepper", "Meat"]
    for i, m in enumerate(order):
        x = 18 + i * 4.6
        if m == "Onion":
            b.cyl(mat(m), 2.2, 2.2, 1.6, T(x) @ ALONG_X, seg=10)
        else:
            s = 3.4 if m == "Meat" else 2.8
            b.box(mat(m), s, s, s, T(x) @ R('X', 20 * i))
    return b.finish()


def bucket():
    """Striped kebab bucket worn on the back, origin at the back strap."""
    b = Builder("SM_SkewerBucket")
    seg = 16
    for i in range(seg):
        a0 = 2 * math.pi * i / seg
        a1 = 2 * math.pi * (i + 1) / seg
        m = mat("Red" if i % 2 == 0 else "White")

        def stripe(bm, a0=a0, a1=a1):
            r0, r1, h = 10.0, 13.0, 32.0
            v = [bm.verts.new((r0 * math.cos(a0), r0 * math.sin(a0), 0)),
                 bm.verts.new((r0 * math.cos(a1), r0 * math.sin(a1), 0)),
                 bm.verts.new((r1 * math.cos(a1), r1 * math.sin(a1), h)),
                 bm.verts.new((r1 * math.cos(a0), r1 * math.sin(a0), h))]
            bm.faces.new(v)
        b._add(stripe, m, T(0, 13, -16))
    b.cyl(mat("White"), 10, 10, 0.6, T(0, 13, -15.7), seg=seg)
    rnd = random.Random(5)
    for i in range(7):
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(1, 7)
        tilt = R('X', rnd.uniform(-12, 12)) @ R('Y', rnd.uniform(-12, 12))
        base = T(r * math.cos(a), 13 + r * math.sin(a), -10)
        b.cyl(mat("Steel"), 0.3, 0.3, 46, base @ tilt @ T(0, 0, 23), seg=5)
        for k, m in enumerate(["Meat", "Pepper", "Meat", "Onion"]):
            b.box(mat(m), 3, 3, 3, base @ tilt @ T(0, 0, 26 + k * 3.8))
    b.box(mat("Leather"), 4, 1, 60, T(0, 0, 0) @ R('Y', 35))
    return b.finish()


def grill_lid():
    """Dented kettle-grill lid. Origin at the inner handle, dome faces -Y
    (forward when held in front of the body)."""
    b = Builder("SM_GrillLid")

    def dome(bm):
        bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=10,
                                  radius=27)
        for v in list(bm.verts):
            if v.co.z < -0.5:
                bm.verts.remove(v)
        rnd = random.Random(7)
        for v in bm.verts:
            v.co.z *= 0.5
            if v.co.z > 2:
                v.co.z -= rnd.uniform(0, 1.2)
        dent = mathutils.Vector((8, 6, 12))
        for v in bm.verts:
            d = (v.co - dent).length
            if d < 8:
                v.co.z -= (8 - d) * 0.45
    b._add(dome, mat("DarkSteel"), T(0, -3, 0) @ R('X', 90))
    b.torus(mat("DarkSteel"), 27, 0.8, T(0, -3, 0) @ R('X', 90), seg=24)
    b.box(mat("Handle"), 10, 2, 2.4, T(0, -18.5, 0))
    b.box(mat("Steel"), 1.2, 4, 1.2, T(-4.5, -16.5, 0))
    b.box(mat("Steel"), 1.2, 4, 1.2, T(4.5, -16.5, 0))
    b.box(mat("Steel"), 9, 1.5, 1.5, T(0, 1.5, 0))
    return b.finish()


def charcoal_grill():
    """Portable charcoal grill held by the side handle at the origin."""
    b = Builder("SM_CharcoalGrill")

    def bowl(bm):
        bmesh.ops.create_uvsphere(bm, u_segments=18, v_segments=10,
                                  radius=20)
        for v in list(bm.verts):
            if v.co.z > 0.5:
                bm.verts.remove(v)
        for v in bm.verts:
            v.co.z *= 0.7
    cx = 26
    b._add(bowl, mat("DarkSteel"), T(cx, 0, 0))
    b.torus(mat("DarkSteel"), 20, 0.7, T(cx, 0, 0), seg=24)
    b.cyl(mat("Ash"), 19, 19, 1.0, T(cx, 0, -3.0), seg=18)
    rnd = random.Random(11)
    for i in range(22):
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(0, 15)
        s = rnd.uniform(2.5, 4.5)
        m = T(cx + r * math.cos(a), r * math.sin(a), -1.6) @ R(
            'Z', rnd.uniform(0, 90)) @ R('X', rnd.uniform(-20, 20))
        b.box(mat("Coals"), s, s * 0.8, s * 0.6, m)
    for i in range(7):
        b.cyl(mat("Steel"), 0.3, 0.3, 38, T(cx, -15 + i * 5, 0.6) @ ALONG_X,
              seg=5)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.5
        m = T(cx + 13 * math.cos(a), 13 * math.sin(a), -22) @ R(
            'X', 12 * math.sin(a)) @ R('Y', -12 * math.cos(a))
        b.cyl(mat("DarkSteel"), 0.8, 0.8, 30, m, seg=6)
    b.box(mat("Handle"), 3, 10, 2.5, T(0, 0, 0))
    b.box(mat("Steel"), 6, 1.2, 1.2, T(3, -4, 0))
    b.box(mat("Steel"), 6, 1.2, 1.2, T(3, 4, 0))
    return b.finish()


ALL = {
    "Shawarman": [knife, steel, flashlight, mini_kebab, flatbread, chair],
    "Skewerman": [skewer, bucket],
    "GrillSergeant": [grill_lid, charcoal_grill],
}
