import bpy
import sys
sys.path.insert(0, r"C:\Users\vvovchenko\repo\acrpg\Saved\ClaudeScripts")
import blender_rigcheck as rc  # noqa: E402

ART = r"C:\Users\vvovchenko\repo\acrpg\Art\Enemies"


def build_base(name):
    """Fresh scene with the rigged Meshy cook in centimeters."""
    bpy.ops.wm.read_homefile(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 0.01
    sc.render.fps = 30
    objs = rc.import_glb(rf"{ART}\{name}\Meshy\SK_{name}_Rigged.glb")
    for o in list(objs):
        if o.type == 'MESH' and o.name.startswith("Icosphere"):
            bpy.data.objects.remove(o)
    arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
    arm.name = "Armature"
    arm.data.name = "Armature"
    arm.scale = (1, 1, 1)
    mesh.name = "SK_" + name
    mesh.data.name = "SK_" + name
    mesh.data.materials[0].name = "M_" + name
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    add_root(arm)
    return arm, mesh


def edit_mode(arm, mode):
    win = bpy.context.window_manager.windows[0]
    area = next((a for a in win.screen.areas if a.type == 'VIEW_3D'),
                win.screen.areas[0])
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    with bpy.context.temp_override(window=win, area=area,
                                   active_object=arm, object=arm):
        bpy.ops.object.mode_set(mode=mode)


def add_root(arm):
    edit_mode(arm, 'EDIT')
    eb = arm.data.edit_bones
    root = eb.new("root")
    root.head = (0, 0, 0)
    root.tail = (0, 0, 20)
    eb["Hips"].parent = root
    edit_mode(arm, 'OBJECT')


def add_bone(arm, name, parent, head, tail):
    edit_mode(arm, 'EDIT')
    b = arm.data.edit_bones.new(name)
    b.head = head
    b.tail = tail
    b.parent = arm.data.edit_bones[parent]
    edit_mode(arm, 'OBJECT')


def import_actions(arm, glb):
    """Import a Meshy animation GLB and return its actions (cm units)."""
    before_a = set(bpy.data.actions)
    objs = rc.import_glb(glb)
    acts = [a for a in bpy.data.actions if a not in before_a]
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
    for a in acts:
        a.use_fake_user = True
    return acts
