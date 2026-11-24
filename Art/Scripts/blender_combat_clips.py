"""Combat clips keyed by script (issue #22).

Run inside Blender with the matching file open:
  SK_Chicken.blend:   build_peck_jump(), build_chicken_hit(),
                      build_eat_corn(), build_shotgun_fire(),
                      build_kneel_dig()
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
# Corn cob held for A_Chicken_EatCorn, armature space (cm): center and
# half the distance between the wing tips
COB = Vector((0, -22, 37))
COB_GRIP = 8.5
# Middle of the open backpack's mouth for A_Chicken_Kneel, armature space
# (cm): BP_AcrpgHUD puts the bag BAG_MOUTH.y in front of her
BAG_MOUTH = Vector((0, -31, 15))


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


def reach(arm, pose, chain, tip, target, steps=20):
    """Turn the chain (root bone first) so the tip lands on the target.

    tip is a skinned vertex: (rest position, [(bone, weight)]), so the
    point is where the mesh really is, not where one bone puts it. Cyclic
    coordinate descent in armature space, each bone turned the least
    angle.
    """
    pose_with_edits(arm, pose, [])
    bones = [arm.pose.bones[n] for n in chain]
    co, weights = tip
    skin = [(arm.pose.bones[b], arm.data.bones[b].matrix_local.inverted()
             @ co, w) for b, w in weights]
    for _ in range(steps):
        for pb in reversed(bones):
            bpy.context.view_layer.update()
            end = sum((p.matrix @ local * w for p, local, w in skin),
                      Vector())
            head = pb.matrix.translation
            a, b = end - head, target - head
            if a.length < 1e-4 or b.length < 1e-4:
                continue
            r = a.rotation_difference(b).to_matrix().to_4x4()
            pb.matrix = (Matrix.Translation(head) @ r @
                         Matrix.Translation(-head) @ pb.matrix)
    bpy.context.view_layer.update()
    return {pb.name: (pb.location.copy(), pb.rotation_quaternion.copy(),
                      pb.scale.copy()) for pb in arm.pose.bones}


def wing_tips(arm):
    """{"Left"/"Right": the outermost wing vertex as a reach() tip}."""
    mesh = next(o for o in bpy.data.objects if o.type == 'MESH' and
                o.find_armature() == arm and o.vertex_groups.get("Head"))
    tips = {}
    for side, pick in (("Left", max), ("Right", min)):
        v = pick(mesh.data.vertices, key=lambda v: v.co.x)
        total = sum(g.weight for g in v.groups)
        tips[side] = (arm.matrix_world.inverted() @ mesh.matrix_world @ v.co,
                      [(mesh.vertex_groups[g.group].name, g.weight / total)
                       for g in v.groups if g.weight > 0])
    return tips


def build_eat_corn():
    """A_Chicken_EatCorn: three quick pecks at a cob held in the wings.

    24 fps, 28 frames (1.17 s), played on the UpperBody slot. The wing
    tips grip the ends of a cob lying across in front of her chest
    (center COB, along X), the cob mesh rides `Hips` in UE. The pecks
    bend Spine02, neck and Head so the beak tip bites into the top of
    the cob on frames 7, 12 and 17 (the cob dips 1.5 cm on each); between
    them she throws the head back, then chews with head turns on 19-23.
    """
    arm = armature()
    acts = bpy.data.actions
    if "A_Chicken_EatCornOld" not in acts:
        acts["A_Chicken_EatCorn"].name = "A_Chicken_EatCornOld"
    idle = sample(arm, acts["A_Chicken_Idle"], 0)
    tips = wing_tips(arm)

    def hold(pose, edits, dip=0.0):
        out = pose_with_edits(arm, pose, edits)
        for side, sx in (("Left", 1), ("Right", -1)):
            out = reach(arm, out, [side + "Arm", side + "ForeArm",
                                   side + "Hand"], tips[side],
                        COB + Vector((sx * COB_GRIP, 0, -dip)))
        return out

    def bend(spine, neck, head, turn=0):
        return [("rot", "Spine02", X, spine), ("rot", "neck", X, neck),
                ("rot", "Head", X, head), ("rot", "Head", Z, turn)]

    up = hold(idle, bend(4, 0, 10))
    peck = hold(idle, bend(18, 15, 10), 1.5)
    rise = hold(idle, bend(2, -5, -8))
    keys = [
        (0, idle),
        (4, up),
        (7, peck),
        (9, rise),
        (12, peck),
        (14, rise),
        (17, peck),
        (19, hold(idle, bend(5, 0, 6, 10))),
        (21, hold(idle, bend(5, 0, 6, -10))),
        (23, hold(idle, bend(5, 0, 8, 6))),
        (25, mix(up, idle, 0.5)),
        (28, idle),
    ]
    return write_action(arm, "A_Chicken_EatCorn", keys)


def build_shotgun_fire(kick=0.8):
    """A_Chicken_ShotgunFire: one recoil kick out of the aim pose.

    24 fps, 16 frames (0.67 s, under the 0.7 s ShotInterval), played on
    the UpperBody slot at rate 1. Starts and ends on frame 0 of
    A_Chicken_ShotgunAim, the pose ABP_Chicken layers under the slot, so
    the gun never leaves the aim. The shot throws both wings up about the
    shoulders and the chest and head back on frame 1 (muzzle about 23
    degrees up in game), eases back with a small dip past the aim on
    frame 8 and is settled on frame 10.
    The Meshy clip is kept as A_Chicken_ShotgunFireOld.
    """
    arm = armature()
    acts = bpy.data.actions
    if "A_Chicken_ShotgunFireOld" not in acts:
        acts["A_Chicken_ShotgunFire"].name = "A_Chicken_ShotgunFireOld"
    aim = sample(arm, acts["A_Chicken_ShotgunAim"], 0)

    def recoil(t):
        a = kick * t
        return pose_with_edits(arm, aim, [
            ("rot", "Spine02", X, -6 * a), ("rot", "Head", X, -8 * a),
            ("rot", "RightArm", X, -16 * a), ("rot", "LeftArm", X, -12 * a),
            ("rot", "RightHand", X, -8 * a)])

    keys = [(0, aim), (1, recoil(1.0)), (2, recoil(0.85)),
            (4, recoil(0.45)), (6, recoil(0.1)), (8, recoil(-0.06)),
            (10, aim), (16, aim)]
    return write_action(arm, "A_Chicken_ShotgunFire", keys)


def build_kneel_dig():
    """A_Chicken_Kneel: crouch, rummage in the open backpack, stand up.

    24 fps, 120 frames (5 s) like the Meshy clip it is made from (kept as
    A_Chicken_KneelOld), whose crouch (frames 0-20) and stand-up (96-119)
    stay. In between she digs at the ground short of the bag, so frames
    28-86 are re-keyed: from the frame 75 crouch the upper body leans back
    up (Spine02 and neck) so the beak hangs over the bag opening (BAG_MOUTH,
    30 cm ahead, under the 15 cm rim), and the wing tips reach into the
    opening, one up while the other digs. BP_AcrpgHUD pauses the clip on
    frame 75 (2.6 s at 1.2x) while the panel is open and plays the
    stand-up from frame 86 (3.6 s) when it closes; both are the dig pose.
    """
    arm = armature()
    acts = bpy.data.actions
    if "A_Chicken_KneelOld" not in acts:
        acts["A_Chicken_Kneel"].name = "A_Chicken_KneelOld"
    old = acts["A_Chicken_KneelOld"]
    tips = wing_tips(arm)
    crouch = sample(arm, old, 75)

    def dig(left, right, nod):
        out = pose_with_edits(arm, crouch, [
            ("rot", "Spine02", X, -22), ("rot", "neck", X, -20),
            ("rot", "Head", X, nod)])
        for side, sx, dz in (("Left", 1, left), ("Right", -1, right)):
            out = reach(arm, out, [side + "Arm", side + "ForeArm",
                                   side + "Hand"], tips[side],
                        BAG_MOUTH + Vector((sx * 6, 0, dz)))
        return out

    a = dig(-6, -6, 4)
    keys = [(f, sample(arm, old, f)) for f in range(0, 21, 4)]
    keys += [(28, a), (36, dig(-2, -9, 8)), (44, dig(-9, -2, 0)),
             (52, dig(-2, -9, 8)), (60, dig(-9, -2, 0)), (68, a), (75, a),
             (86, a)]
    keys += [(f, sample(arm, old, f)) for f in range(96, 120, 4)]
    keys.append((119, sample(arm, old, 119)))
    return write_action(arm, "A_Chicken_Kneel", keys)


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
