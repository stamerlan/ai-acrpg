import bpy
import mathutils


def import_glb(path):
    win = bpy.context.window_manager.windows[0]
    area = next((a for a in win.screen.areas if a.type == 'VIEW_3D'),
                win.screen.areas[0])
    region = next(r for r in area.regions if r.type == 'WINDOW')
    before = set(bpy.data.objects)
    units = bpy.context.scene.unit_settings
    old = units.scale_length
    units.scale_length = 1.0
    with bpy.context.temp_override(window=win, area=area, region=region):
        bpy.ops.import_scene.gltf(filepath=path)
    units.scale_length = old
    return [o for o in bpy.data.objects if o not in before]


def rig_report(objs):
    arm = next(o for o in objs if o.type == 'ARMATURE')
    meshes = [o for o in objs if o.type == 'MESH']
    m = max(meshes, key=lambda o: len(o.data.polygons))
    heads = {b.name: (arm.matrix_world @ b.head_local) for b in arm.data.bones}
    vg = {g.index: g.name for g in m.vertex_groups}
    stats = {}
    for v in m.data.vertices:
        for g in v.groups:
            if g.weight > 0.5:
                s = stats.setdefault(vg[g.group], [0, mathutils.Vector()])
                s[0] += 1
                s[1] += m.matrix_world @ v.co
    out = {}
    for n, h in heads.items():
        c, acc = stats.get(n, [0, mathutils.Vector()])
        cen = acc / c if c else None
        out[n] = [c, [round(x, 2) for x in h],
                  [round(x, 2) for x in cen] if cen else None]
    return {"mesh": m.name, "tris": len(m.data.polygons),
            "dims": [round(x, 3) for x in m.dimensions],
            "others": [(o.name, len(o.data.polygons)) for o in meshes
                       if o is not m],
            "bones": out}
