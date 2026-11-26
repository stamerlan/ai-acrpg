"""Shawarman knife and patrol walk fixes (#TBD).

Run inside Blender with Enemies/Shawarman/Source/SK_Shawarman.blend open:

    import blender_knife_fix as kf
    kf.run()

* `A_Cook_Walk` is rebuilt from the Meshy "Quick Walk" clip (action 115,
  `Meshy/Anim_QuickWalk.glb`, 24 fps, three identical cycles): one cycle
  from the left foot plant, retimed to 30 fps (30 frames, 111 cm/s).
* The doner knife sits in `RightHand` with its blade up through the face
  during the idle hand rub, and across the face when the shout throws the
  arms up. The hand is rolled (local Y, then X) over those frames so the
  blade leans up and out instead; the hands still rub.
"""
import math
import os
import sys

import bpy
from mathutils import Quaternion

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_animtools as at  # noqa: E402
import blender_cook as ck  # noqa: E402

ART = r"C:\Users\vvovchenko\repo\acrpg\Art\Enemies\Shawarman"
QUICK_WALK = os.path.join(ART, "Meshy", "Anim_QuickWalk.glb")
# (action, first frame, full-weight start, full-weight end, last frame,
#  roll about the hand's Y, then X, in degrees)
KNIFE_ROLLS = [
    ("A_Shawarman_Idle", 12, 20, 60, 68, -50, -40),
    ("A_Shawarman_Shout", 12, 18, 26, 32, -50, -20),
]


def armature():
    return bpy.data.objects["Armature"]


def build_walk(arm):
    """A_Cook_Walk from the Meshy Quick Walk GLB."""
    sc = bpy.context.scene
    acts = ck.import_actions(arm, QUICK_WALK)
    sc.render.fps = 30
    src = acts[0]
    old = bpy.data.actions.get("A_Cook_Walk")
    if old:
        bpy.data.actions.remove(old)
    src.name = "A_Cook_Walk"
    # left foot plants on frame 3 of the 24 fps clip, one cycle is 24 frames
    at.trim(src, 3, 27)
    at.retime(src, [0, 24], [0, 30])
    src.frame_range = (0, 30)
    at.crossfade_loop(arm, src, 4)
    return src


def roll_hand(arm, name, f0, f1, f2, f3, roll_y, roll_x):
    act = bpy.data.actions[name]
    cb = at.channelbag(act, arm)
    path = 'pose.bones["RightHand"].rotation_quaternion'
    fcs = {c.array_index: c for c in cb.fcurves if c.data_path == path}
    end = int(act.frame_range[1])
    keys = {}
    for f in range(0, end + 1):
        keys[f] = Quaternion([fcs[i].evaluate(f) for i in range(4)])
    for f, q in keys.items():
        if f <= f0 or f >= f3:
            continue
        w = 1.0
        if f < f1:
            w = (f - f0) / float(f1 - f0)
        elif f > f2:
            w = (f3 - f) / float(f3 - f2)
        w = w * w * (3 - 2 * w)
        q = q @ Quaternion((0, 1, 0), math.radians(roll_y) * w)
        q = q @ Quaternion((1, 0, 0), math.radians(roll_x) * w)
        for i in range(4):
            fcs[i].keyframe_points.insert(f, q[i], options={'REPLACE'})
    for c in fcs.values():
        c.update()


def export(arm):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import blender_export as ex
    for name in ["A_Cook_Walk"] + [r[0] for r in KNIFE_ROLLS]:
        ex.export_clip(arm, bpy.data.actions[name],
                       os.path.join(ART, "Anims", name + ".fbx"))


def run():
    arm = armature()
    build_walk(arm)
    for row in KNIFE_ROLLS:
        roll_hand(arm, *row)
    export(arm)
    bpy.ops.wm.save_mainfile()
