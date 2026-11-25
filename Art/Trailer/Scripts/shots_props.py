"""Props in the cooks' hands, shared by the shots and the test views."""
import bpy
import numpy
from mathutils import Vector

import trailer_lib as lib


def grip(rig, mesh, bone):
    """Where a fist around a handle sits, in the hand bone's space.

    Found from the glove's shape (the vertices skinned to the bone): its
    long axis is the hand, its thinnest axis the palm normal, the third
    the knuckle line a handle lies along. Returns (center, along the
    knuckles toward the thumb, toward the palm), in bone units.
    """
    group = mesh.vertex_groups[bone].index
    to_bone = rig.data.bones[bone].matrix_local.inverted()
    points = numpy.array([
        to_bone @ vertex.co for vertex in mesh.data.vertices
        if any(g.group == group and g.weight > 0.6 for g in vertex.groups)])
    center = points.mean(axis=0)
    spread = points - center
    _, axes = numpy.linalg.eigh(numpy.cov(spread.T))
    palm, knuckles, hand = axes[:, 0], axes[:, 1], axes[:, 2]
    if hand[1] < 0:
        hand = -hand
    # The fingers curl toward the palm: the far end leans that way.
    far = spread[spread @ hand > numpy.percentile(spread @ hand, 85)]
    if (far @ palm).mean() < 0:
        palm = -palm
    # The glove is lopsided away from the thumb side of the knuckle line.
    if ((spread @ knuckles) ** 3).mean() > 0:
        knuckles = -knuckles
    return (Vector(center) + Vector(hand) * 2.0, Vector(knuckles),
            Vector(palm))


def arm_cook(rig, mesh):
    """Doner knife in the right fist, sharpening steel in the left."""
    _, props = lib.append(
        lib.ENEMY_PROPS, ["SM_DonerKnife", "SM_SharpeningSteel"])
    for prop, bone in (("SM_DonerKnife", "RightHand"),
                       ("SM_SharpeningSteel", "LeftHand")):
        center, knuckles, palm = grip(rig, mesh, bone)
        lib.hold(props[prop], rig, bone, knuckles, center + palm * 2.5)
    steel = bpy.data.materials["M_Prop_Steel"]
    shader = steel.node_tree.nodes["Principled BSDF"]
    shader.inputs["Metallic"].default_value = 1.0
    shader.inputs["Roughness"].default_value = 0.42


def rub_hands(rig, mesh, frames, touch=8.5):
    """Brings the cook's palms together while he rubs them.

    In the library clip they pass 15 cm apart. Whenever they come near
    each other, both wrists are pulled along the line between the palms
    (two-bone IK on each arm) until the palm centers are touch apart, so
    the rubbing motion itself is kept.
    """
    scene = bpy.context.scene
    bones = ("RightHand", "LeftHand")
    arms = ("RightForeArm", "LeftForeArm")
    # Meshy's bones are very long, so their tails are nowhere near the
    # joints. A short helper bone at each wrist gives the IK a tip there.
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    for bone, arm in zip(bones, arms):
        tip = rig.data.edit_bones.new("Wrist" + arm)
        tip.head = rig.data.edit_bones[bone].head
        tip.tail = tip.head + Vector((0, 0, 1.0))
        tip.parent = rig.data.edit_bones[arm]
    bpy.ops.object.mode_set(mode="OBJECT")
    centers = [grip(rig, mesh, bone)[0] for bone in bones]
    targets = []
    for frame in range(1, frames + 1):
        scene.frame_set(frame)
        palms = [rig.pose.bones[bone].matrix @ center
                 for bone, center in zip(bones, centers)]
        tips = [rig.pose.bones["Wrist" + arm].tail.copy() for arm in arms]
        apart = palms[1] - palms[0]
        near = min(1.0, max(0.0, (48.0 - apart.length) / 26.0))
        pull = apart.normalized() * (apart.length - touch) / 2 * near
        targets.append((tips[0] + pull, tips[1] - pull))
    for index, arm in enumerate(arms):
        goal = bpy.data.objects.new("Goal" + arm, None)
        scene.collection.objects.link(goal)
        goal.parent = rig
        for frame, spots in enumerate(targets, start=1):
            goal.location = spots[index]
            goal.keyframe_insert("location", frame=frame)
        reach = rig.pose.bones["Wrist" + arm].constraints.new("IK")
        reach.target = goal
        reach.chain_count = 3
