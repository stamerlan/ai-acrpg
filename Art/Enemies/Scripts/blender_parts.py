import bpy
import bmesh
import numpy as np


def vertex_colors(ob):
    """Base color sampled at each vertex's first UV."""
    me = ob.data
    img = next(n.image for n in me.materials[0].node_tree.nodes
               if n.type == 'TEX_IMAGE' and n.image)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    uv = me.uv_layers.active.data
    col = {}
    for poly in me.polygons:
        for li, vi in zip(poly.loop_indices, poly.vertices):
            if vi in col:
                continue
            u, v = uv[li].uv
            x = min(w - 1, max(0, int(u * w)))
            y = min(h - 1, max(0, int(v * h)))
            col[vi] = px[y, x, :3]
    return col


def islands(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    seen = set()
    out = []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack = [v]
        isl = []
        seen.add(v.index)
        while stack:
            x = stack.pop()
            isl.append(x.index)
            for e in x.link_edges:
                o = e.other_vert(x)
                if o.index not in seen:
                    seen.add(o.index)
                    stack.append(o)
        out.append(isl)
    bm.free()
    return out


def assign_rigid(ob, vids, group):
    """Skin the vertices 100% to one vertex group."""
    vg = ob.vertex_groups.get(group) or ob.vertex_groups.new(name=group)
    for vi in vids:
        for g in list(ob.data.vertices[vi].groups):
            ob.vertex_groups[g.group].remove([vi])
        vg.add([vi], 1.0, 'REPLACE')


def blend_weights(ob, weights, group):
    """weights: {vi: w}; blends `group` in, scaling others by (1 - w)."""
    vg = ob.vertex_groups.get(group) or ob.vertex_groups.new(name=group)
    for vi, w in weights.items():
        if w <= 0:
            continue
        v = ob.data.vertices[vi]
        for g in list(v.groups):
            if g.group == vg.index:
                continue
            ob.vertex_groups[g.group].add([vi], g.weight * (1 - w),
                                          'REPLACE')
        vg.add([vi], w, 'REPLACE')
