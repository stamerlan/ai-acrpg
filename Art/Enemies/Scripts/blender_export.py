import bpy
import os

ART = r"C:\Users\vvovchenko\repo\acrpg\Art\Enemies"


def ctx():
    win = bpy.context.window_manager.windows[0]
    area = next((a for a in win.screen.areas if a.type == 'VIEW_3D'),
                win.screen.areas[0])
    region = next(r for r in area.regions if r.type == 'WINDOW')
    return dict(window=win, area=area, region=region)


def save_texture(mesh, path):
    img = next(n.image for n in mesh.data.materials[0].node_tree.nodes
               if n.type == 'TEX_IMAGE' and n.image)
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    if img.packed_file:
        img.unpack(method='REMOVE')
    img.filepath = path
    img.name = os.path.splitext(os.path.basename(path))[0]
    img.reload()


def fbx(path, objects, anim, all_actions=False):
    for o in bpy.data.objects:
        o.select_set(o in objects)
    bpy.context.view_layer.objects.active = objects[0]
    with bpy.context.temp_override(**ctx()):
        bpy.ops.export_scene.fbx(
            filepath=path, use_selection=True,
            object_types={'ARMATURE', 'MESH'},
            apply_unit_scale=True, global_scale=1.0,
            apply_scale_options='FBX_SCALE_ALL',
            add_leaf_bones=False, use_armature_deform_only=False,
            primary_bone_axis='Y', secondary_bone_axis='X',
            bake_anim=anim, bake_anim_use_all_actions=all_actions,
            bake_anim_use_nla_strips=False,
            bake_anim_force_startend_keying=True,
            bake_anim_simplify_factor=0.0,
            mesh_smooth_type='FACE', path_mode='STRIP')


def export_mesh(arm, mesh, path):
    ad = arm.animation_data
    if ad:
        ad.action = None
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.scale = (1, 1, 1)
    fbx(path, [arm, mesh], anim=False)


def export_clip(arm, action, path):
    """One clip, skeleton only."""
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = action
    ad.action_slot = action.slots[0]
    sc = bpy.context.scene
    sc.frame_start = int(action.frame_range[0])
    sc.frame_end = int(action.frame_range[1])
    fbx(path, [arm], anim=True)
