"""Kenney GLB -> FBX for UE: one joined mesh per model, meters, Z up.

Run in Blender. Reads Art/Environment/Kenney/<kit>/*.glb and writes
Art/Environment/Kenney/_fbx/<kit>__<name>.fbx (scale 1, so 1 m = 100 cm
in UE). Kenney models are small and inconsistent in scale; the dressing
scripts scale them in the level.
"""
import glob
import os

import bpy

A = r"C:\Users\vvovchenko\repo\acrpg\Art\Environment\Kenney"
OUT = os.path.join(A, "_fbx")


def ctx():
    win = bpy.context.window_manager.windows[0]
    area = next((a for a in win.screen.areas if a.type == 'VIEW_3D'),
                win.screen.areas[0])
    region = next((r for r in area.regions if r.type == 'WINDOW'),
                  area.regions[0])
    return dict(window=win, area=area, region=region)


def convert():
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.wm.read_homefile(use_empty=True)
    done = []
    for kit in sorted(os.listdir(A)):
        kd = os.path.join(A, kit)
        if not os.path.isdir(kd) or kit.startswith("_"):
            continue
        for f in sorted(glob.glob(os.path.join(kd, "*.glb"))):
            name = os.path.splitext(os.path.basename(f))[0]
            for o in list(bpy.data.objects):
                bpy.data.objects.remove(o, do_unlink=True)
            bpy.ops.import_scene.gltf(filepath=f)
            meshes = [o for o in bpy.context.scene.objects
                      if o.type == 'MESH']
            with bpy.context.temp_override(
                    **ctx(), active_object=meshes[0],
                    selected_objects=meshes,
                    selected_editable_objects=meshes):
                if len(meshes) > 1:
                    bpy.ops.object.join()
            ob = [o for o in bpy.context.scene.objects
                  if o.type == 'MESH'][0]
            ob.parent = None
            with bpy.context.temp_override(
                    **ctx(), active_object=ob, selected_objects=[ob],
                    selected_editable_objects=[ob]):
                bpy.ops.object.transform_apply(location=False, rotation=True,
                                               scale=True)
            for o in list(bpy.context.scene.objects):
                if o != ob:
                    bpy.data.objects.remove(o, do_unlink=True)
            ob.name = name
            for o in bpy.context.scene.objects:
                o.select_set(o == ob)
            fn = os.path.join(OUT, kit.replace("-", "_") + "__" +
                              name.replace("-", "_") + ".fbx")
            with bpy.context.temp_override(**ctx()):
                bpy.ops.export_scene.fbx(
                    filepath=fn, use_selection=True, object_types={'MESH'},
                    global_scale=1.0, apply_unit_scale=True,
                    apply_scale_options='FBX_SCALE_NONE',
                    mesh_smooth_type='FACE', path_mode='STRIP',
                    bake_anim=False)
            done.append(name)
    return done
