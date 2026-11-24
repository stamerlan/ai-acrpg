"""Combat clips keyed by script (issue #22).

Run inside Blender with the matching file open:
  SK_Chicken.blend:   build_peck_jump(), build_chicken_hit()
  SK_Shawarman.blend: build_chop(), build_flinch()

Poses are built from frames of existing clips plus edits in armature
space: ("rot", bone, axis, degrees) turns a bone about an axis through
its head, ("move", bone, (x, y, z)) shifts it. Children follow their
parents, so list edits parent first. Both rigs face -Y: +X is the pitch
axis (positive turns the nose down), +Z is up.
"""
import math

import bpy
from mathutils import Matrix, Vector

X = Vector((1, 0, 0))
Y = Vector((0, 1, 0))
Z = Vector((0, 0, 1))
WING_BONES = ["LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand",
              "RightShoulder", "RightArm", "RightForeArm", "RightHand"]
LEG_BONES = ["LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase",
             "RightUpLeg", "RightLeg", "RightFoot", "RightToeBase"]


def armature():
    return next(o for o in bpy.data.objects if o.type == 'ARMATURE')


def sample(arm, action, frame):
    """Local loc/rot/scale of every bone at a frame of a clip."""
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = action
    ad.action_slot = action.slots[0]
    bpy.context.scene.frame_set(int(frame), subframe=frame - int(frame))
    pose = {pb.name: (pb.location.copy(), pb.rotation_quaternion.copy(),
                      pb.scale.copy()) for pb in arm.pose.bones}
    ad.action = None
    return pose


def mix(a, b, t, bones=None):
    """Blend pose b into pose a by t, for the given bones (all if None)."""
    out = dict(a)
    for name in bones or a:
        la, ra, sa = a[name]
        lb, rb, sb = b[name]
        out[name] = (la.lerp(lb, t), ra.slerp(rb, t), sa.lerp(sb, t))
    return out


def pose_with_edits(arm, base, edits):
    """Apply base, then the edits; returns the resulting local pose."""
    for pb in arm.pose.bones:
        loc, rot, scale = base[pb.name]
        pb.rotation_mode = 'QUATERNION'
        pb.location, pb.rotation_quaternion, pb.scale = loc, rot, scale
    for kind, bone, value, *rest in edits:
        bpy.context.view_layer.update()
        pb = arm.pose.bones[bone]
        m = pb.matrix.copy()
        if kind == "rot":
            h = m.translation.copy()
            r = Matrix.Rotation(math.radians(rest[0]), 4, value)
            pb.matrix = Matrix.Translation(h) @ r @ Matrix.Translation(-h) @ m
        else:
            pb.matrix = Matrix.Translation(Vector(value)) @ m
    bpy.context.view_layer.update()
    return {pb.name: (pb.location.copy(), pb.rotation_quaternion.copy(),
                      pb.scale.copy()) for pb in arm.pose.bones}


def write_action(arm, name, keys, interp=None):
    """keys: [(frame, pose)]. Replaces the action of that name."""
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = act
    prev = {}
    for frame, pose in keys:
        for pb in arm.pose.bones:
            loc, rot, scale = pose[pb.name]
            rot = rot.copy()
            if pb.name in prev:
                rot.make_compatible(prev[pb.name])
            prev[pb.name] = rot
            pb.location, pb.rotation_quaternion, pb.scale = loc, rot, scale
            for path in ("location", "rotation_quaternion", "scale"):
                pb.keyframe_insert(path, frame=frame)
    for layer in act.layers:
        for strip in layer.strips:
            cb = strip.channelbag(act.slots[0])
            for c in cb.fcurves:
                for kp in c.keyframe_points:
                    if interp and int(kp.co.x) in interp:
                        kp.interpolation = interp[int(kp.co.x)]
    act.frame_range = (keys[0][0], keys[-1][0])
    act.use_frame_range = True
    ad.action = None
    return act


def build_peck_jump():
    """A_Chicken_Peck: hop at the enemy, peck at the apex, hop back.

    24 fps, 16 frames (0.67 s). The capsule moves in Blueprint
    (BPC_ChickenCombat): out on frames 2-6, back on frames 8-13. The
    clip only lifts her: root up to 40 cm at the strike (frame 6), so the
    beak lands at belly height of a cook.
    """
    arm = armature()
    acts = bpy.data.actions
    old_peck = acts.get("A_Chicken_PeckOld") or acts["A_Chicken_Peck"]
    if old_peck.name == "A_Chicken_Peck":
        old_peck.name = "A_Chicken_PeckOld"
    idle = sample(arm, acts["A_Chicken_Idle"], 0)
    windup = sample(arm, old_peck, 2)
    strike = sample(arm, old_peck, 5)
    held = sample(arm, old_peck, 7)
    flut = acts["A_Chicken_Flutter"]
    wing_up = sample(arm, flut, 12)
    wing_down = sample(arm, flut, 18)
    wing_mid = sample(arm, flut, 6)

    def lift(z):
        return ("move", "root", (0, 0, z))

    def tuck(deg):
        return [("rot", "LeftUpLeg", X, -deg), ("rot", "RightUpLeg", X, -deg),
                ("rot", "LeftLeg", X, deg * 1.4),
                ("rot", "RightLeg", X, deg * 1.4)]

    def kick(deg):
        return [("rot", "LeftUpLeg", X, -deg),
                ("rot", "RightUpLeg", X, -deg)]

    p = pose_with_edits
    keys = [
        (0, idle),
        (2, p(arm, windup, [lift(-3)])),
        (3, p(arm, mix(mix(windup, strike, 0.3), wing_up, 0.6, WING_BONES),
              [lift(8), ("rot", "Hips", X, 6)] + tuck(25))),
        (4, p(arm, mix(mix(windup, strike, 0.6), wing_up, 1.0, WING_BONES),
              [lift(24), ("rot", "Hips", X, 10)] + tuck(45))),
        (5, p(arm, mix(strike, wing_down, 0.7, WING_BONES),
              [lift(35), ("rot", "Hips", X, 12)] + tuck(50))),
        (6, p(arm, strike, [lift(40), ("rot", "Hips", X, 8),
                            ("rot", "neck", X, -12)] + tuck(45))),
        (7, p(arm, held, [lift(41), ("rot", "Hips", X, 4),
                          ("rot", "neck", X, -10)] + tuck(30))),
        (8, p(arm, mix(mix(held, windup, 0.6), wing_up, 0.8, WING_BONES),
              [lift(39), ("rot", "Hips", X, -22)] + kick(35))),
        (9, p(arm, mix(idle, wing_up, 1.0, WING_BONES),
              [lift(35), ("rot", "Hips", X, -18)] + kick(25))),
        (10, p(arm, mix(idle, wing_down, 1.0, WING_BONES),
               [lift(28), ("rot", "Hips", X, -12)] + kick(10))),
        (11, p(arm, mix(idle, wing_mid, 0.8, WING_BONES),
               [lift(18), ("rot", "Hips", X, -6)])),
        (12, p(arm, mix(idle, wing_up, 0.5, WING_BONES),
               [lift(7), ("rot", "Hips", X, -2)])),
        (13, p(arm, mix(idle, wing_mid, 0.4, WING_BONES),
               [lift(-3), ("rot", "Hips", X, 6)])),
        (14, p(arm, idle, [lift(-1), ("rot", "Hips", X, 2)])),
        (16, idle),
    ]
    return write_action(arm, "A_Chicken_Peck", keys)


def build_chicken_hit():
    """A_Chicken_HitReact: the first recoil of the Meshy clip only.

    Frames 0-20 of A_Chicken_HitReactOld (head and body thrown back,
    wings flared), then back to the idle pose by frame 26 (1.08 s).
    """
    arm = armature()
    acts = bpy.data.actions
    old = acts.get("A_Chicken_HitReactOld") or acts["A_Chicken_HitReact"]
    if old.name == "A_Chicken_HitReact":
        old.name = "A_Chicken_HitReactOld"
    idle = sample(arm, acts["A_Chicken_Idle"], 0)
    keys = [(f, sample(arm, old, f)) for f in range(0, 21, 2)]
    keys.append((23, mix(sample(arm, old, 21), idle, 0.6)))
    keys.append((26, idle))
    return write_action(arm, "A_Chicken_HitReact", keys)


def build_chop():
    """A_Shawarman_Chop: overhead knife chop down at the chicken.

    The Grill Sergeant's ground slam, retimed to 30 fps frames
    0-40 (1.33 s): knife up by frame 7, chop from frame 13, the knife
    reaches the ground about 65 cm in front of him on frame 18 (0.6 s,
    WindupTime), kneel held to frame 24, stand up by frame 40.
    """
    import sys
    sys.path.insert(0, bpy.path.abspath("//../../Scripts"))
    import blender_animtools as at
    arm = armature()
    old = bpy.data.actions.get("A_Shawarman_Chop")
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions["A_GrillSergeant_Slam"].copy()
    act.name = "A_Shawarman_Chop"
    act.use_fake_user = True
    at.retime(act, [0, 12, 40, 46, 54, 66, 90], [0, 7, 13, 15, 18, 24, 40])
    return act


def build_flinch():
    """A_Shawarman_Flinch: doubled over by a peck to the belly.

    30 fps, 24 frames (0.8 s), from the first frame of the idle: the
    hips pushed back, the spine and head curled forward over the belly on
    frame 3, held, then back up.
    """
    arm = armature()
    idle = sample(arm, bpy.data.actions["A_Shawarman_Idle"], 0)

    def bend(amount, back):
        return [("move", "Hips", (0, back, -amount * 0.12)),
                ("rot", "Spine", X, amount * 0.45),
                ("rot", "Spine01", X, amount * 0.35),
                ("rot", "Spine02", X, amount * 0.3),
                ("rot", "neck", X, amount * 0.25),
                ("rot", "Head", X, -amount * 0.2),
                ("rot", "LeftArm", X, -amount * 1.3),
                ("rot", "LeftArm", Y, amount * 0.4),
                ("rot", "RightArm", X, -amount * 1.3),
                ("rot", "RightArm", Y, -amount * 0.4),
                ("rot", "LeftForeArm", X, -amount * 1.0),
                ("rot", "RightForeArm", X, -amount * 1.0)]

    p = pose_with_edits
    keys = [
        (0, idle),
        (3, p(arm, idle, bend(40, 9))),
        (6, p(arm, idle, bend(46, 10))),
        (10, p(arm, idle, bend(38, 8))),
        (16, p(arm, idle, bend(14, 3))),
        (24, idle),
    ]
    return write_action(arm, "A_Shawarman_Flinch", keys)
