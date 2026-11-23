import bpy
import mathutils


def channelbag(action, arm):
    slot = action.slots[0]
    for layer in action.layers:
        for strip in layer.strips:
            cb = strip.channelbag(slot)
            if cb:
                return cb
    return None


def set_action(arm, action):
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = action
    ad.action_slot = action.slots[0]


def sample_bones(arm, action, bones, step=1):
    """World positions of bones per frame: {bone: [(f, x, y, z)]}"""
    set_action(arm, action)
    sc = bpy.context.scene
    f0, f1 = (int(round(v)) for v in action.frame_range)
    out = {b: [] for b in bones}
    for f in range(f0, f1 + 1, step):
        sc.frame_set(f)
        for b in bones:
            p = arm.matrix_world @ arm.pose.bones[b].head
            out[b].append((f, round(p.x, 1), round(p.y, 1), round(p.z, 1)))
    return out


def remove_drift(arm, action, bone="Hips", keep_z=True):
    """Make a clip in place: subtract the linear start-to-end travel."""
    cb = channelbag(action, arm)
    path = 'pose.bones["%s"].location' % bone
    curves = [cb.fcurves.find(path, index=i) for i in range(3)]
    if not all(curves):
        return None
    f0, f1 = action.frame_range
    rest = arm.data.bones[bone].matrix_local.to_3x3()
    inv = rest.inverted()

    def world(f):
        loc = mathutils.Vector([c.evaluate(f) for c in curves])
        return rest @ loc

    d = world(f1) - world(f0)
    if keep_z:
        d.z = 0.0
    for c_i, c in enumerate(curves):
        for kp in c.keyframe_points:
            t = (kp.co.x - f0) / max(f1 - f0, 1)
            delta = inv @ (d * t)
            kp.co.y -= delta[c_i]
            kp.handle_left.y -= delta[c_i]
            kp.handle_right.y -= delta[c_i]
    return [round(v, 1) for v in d]


def remove_offset(arm, action, bone="Hips", frame=None):
    """Shift horizontal hips so the given frame is at the rest XY."""
    cb = channelbag(action, arm)
    path = 'pose.bones["%s"].location' % bone
    curves = [cb.fcurves.find(path, index=i) for i in range(3)]
    if not all(curves):
        return None
    f = action.frame_range[0] if frame is None else frame
    rest = arm.data.bones[bone].matrix_local.to_3x3()
    w = rest @ mathutils.Vector([c.evaluate(f) for c in curves])
    w.z = 0.0
    delta = rest.inverted() @ w
    for i, c in enumerate(curves):
        for kp in c.keyframe_points:
            kp.co.y -= delta[i]
            kp.handle_left.y -= delta[i]
            kp.handle_right.y -= delta[i]
    return [round(v, 1) for v in w]


def crossfade_loop(arm, action, frames):
    """Blend the last `frames` frames toward the first frame's values."""
    cb = channelbag(action, arm)
    f0, f1 = action.frame_range
    for c in cb.fcurves:
        start = c.evaluate(f0)
        for kp in c.keyframe_points:
            if kp.co.x > f1 - frames:
                w = (kp.co.x - (f1 - frames)) / frames
                w = w * w * (3 - 2 * w)
                v = kp.co.y * (1 - w) + start * w
                dv = v - kp.co.y
                kp.co.y = v
                kp.handle_left.y += dv
                kp.handle_right.y += dv


def trim(action, f_start, f_end):
    """Keep keys in [f_start, f_end], shift so f_start becomes 0."""
    for layer in action.layers:
        for strip in layer.strips:
            for slot in action.slots:
                cb = strip.channelbag(slot)
                if not cb:
                    continue
                for c in cb.fcurves:
                    vals = {}
                    for f in range(int(f_start), int(f_end) + 1):
                        vals[f] = c.evaluate(f)
                    while c.keyframe_points:
                        c.keyframe_points.remove(c.keyframe_points[0])
                    for f, v in vals.items():
                        c.keyframe_points.insert(f - f_start, v,
                                                 options={'FAST'})
                    c.update()
    action.frame_range = (0, f_end - f_start)


def retime(action, src_marks, dst_marks):
    """Piecewise-linear time remap; marks are frame lists of equal size."""
    def remap(x):
        for i in range(len(src_marks) - 1):
            a, b = src_marks[i], src_marks[i + 1]
            if x <= b or i == len(src_marks) - 2:
                t = (x - a) / (b - a)
                return dst_marks[i] + t * (dst_marks[i + 1] - dst_marks[i])
        return x
    for layer in action.layers:
        for strip in layer.strips:
            for slot in action.slots:
                cb = strip.channelbag(slot)
                if not cb:
                    continue
                for c in cb.fcurves:
                    f0, f1 = int(src_marks[0]), int(src_marks[-1])
                    vals = [(remap(f), c.evaluate(f)) for f in
                            range(f0, f1 + 1)]
                    while c.keyframe_points:
                        c.keyframe_points.remove(c.keyframe_points[0])
                    for x, v in vals:
                        c.keyframe_points.insert(x, v, options={'FAST'})
                    c.update()
    action.frame_range = (dst_marks[0], dst_marks[-1])
