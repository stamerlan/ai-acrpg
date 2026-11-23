import bpy
import mathutils
import sys
sys.path.insert(0, r"C:\Users\vvovchenko\repo\acrpg\Saved\ClaudeScripts")
import blender_animtools as at  # noqa: E402

# (new name, source action, (start, end) or None, mode)
# Frames are at 30 fps as imported. Modes: loop (in place, crossfade),
# drift (remove start-to-end travel), offset (start centered), keep.
PLAN = [
    ("A_Cook_Walk", "Armature|walking_man|baselayer", None, "loop_move"),
    ("A_Cook_Run", "Armature|running|baselayer", None, "loop_move"),
    ("A_Cook_WalkBack", "Walk_Backward_inplace", None, "loop_move"),
    ("A_Shawarman_Idle", "Scheming_Hand_Rub", None, "loop"),
    ("A_Shawarman_Search", "Torch_Look_Around", None, "loop"),
    ("A_Shawarman_Shout", "Angry_Stomp", (6, 66), "oneshot"),
    ("A_Shawarman_Swing", "Charged_Slash", (0, 30), "oneshot"),
    ("A_Shawarman_Eat", "Stand_and_Drink", None, "loop"),
    ("A_Shawarman_Sleep", "Sit_and_Doze_Off", None, "loop"),
    ("A_Shawarman_WakeUp", "Sit_to_Stand_Transition_M", (36, 120),
     "offset"),
    ("A_Shawarman_HitReact", "Hit_Reaction", None, "drift"),
    ("A_Shawarman_Knockdown", "Knock_Down", None, "offset"),
    ("A_Shawarman_GetUp", "Stand_Up1", (40, 200), "keep"),
    ("A_Shawarman_Death", "dying_backwards", None, "offset"),
    ("A_Skewerman_Throw", "Crouch_Charge_and_Throw", (130, 215), "offset"),
    ("A_Skewerman_KneelThrow", "Crouch_Charge_and_Throw", (0, 50),
     "offset"),
    ("A_Skewerman_Climb", "climbing_up_wall", None, "offset"),
    ("A_Skewerman_Death", "Shot_and_Blown_Back", None, "blown"),
    ("A_GrillSergeant_Slam", "Charged_Ground_Slam", None, "oneshot"),
]


def hips_curves(arm, act):
    cb = at.channelbag(act, arm)
    return [cb.fcurves.find('pose.bones["Hips"].location', index=i)
            for i in range(3)]


def scale_travel(arm, act, factor):
    """Scale the horizontal hips travel (relative to frame 0)."""
    curves = hips_curves(arm, act)
    rest = arm.data.bones["Hips"].matrix_local.to_3x3()
    inv = rest.inverted()
    f0 = act.frame_range[0]
    base = rest @ mathutils.Vector([c.evaluate(f0) for c in curves])
    keys = {}
    for c in curves:
        for kp in c.keyframe_points:
            keys.setdefault(kp.co.x, None)
    new = {}
    for f in keys:
        w = rest @ mathutils.Vector([c.evaluate(f) for c in curves])
        d = w - base
        d.x *= factor
        d.y *= factor
        new[f] = inv @ (base + d)
    for i, c in enumerate(curves):
        for kp in c.keyframe_points:
            dv = new[kp.co.x][i] - kp.co.y
            kp.co.y += dv
            kp.handle_left.y += dv
            kp.handle_right.y += dv


def copy_action(src, name):
    a = src.copy()
    a.name = name
    a.use_fake_user = True
    return a


def process(arm):
    report = {}
    for name, src, rng, mode in PLAN:
        old = bpy.data.actions.get(name)
        if old:
            bpy.data.actions.remove(old)
        a = copy_action(bpy.data.actions[src], name)
        f0, f1 = a.frame_range
        if f0 != 0:
            at.trim(a, f0, f1)
        if rng:
            at.trim(a, rng[0], rng[1])
        info = {}
        if mode in ("loop_move", "drift"):
            d = at.remove_drift(arm, a)
            info["travel"] = d
            info["speed"] = round((d[0] ** 2 + d[1] ** 2) ** 0.5
                                  / (a.frame_range[1] / 30.0), 1)
        if mode in ("loop_move", "loop", "offset", "oneshot", "blown"):
            info["offset"] = at.remove_offset(arm, a)
        if mode == "blown":
            scale_travel(arm, a, 0.3)
        if mode == "loop":
            at.crossfade_loop(arm, a, 8)
        info["frames"] = [round(v) for v in a.frame_range]
        report[name] = info
    return report


def retime_swing(arm):
    """Knife swing: 0.6 s windup, 0.2 s strike, 0.4 s recovery."""
    a = bpy.data.actions["A_Shawarman_Swing"]
    at.retime(a, [0, 10, 20, 30], [0, 18, 24, 36])
    at.crossfade_loop(arm, a, 8)
