import bpy
import math
import os
import numpy as np
import mathutils

SCRATCH = (r"C:\Users\vvovchenko\AppData\Local\Temp\claude\012932be8eb9bb70"
           r"\b831081e-6e9d-497e-aa23-a7ba43e17c69\scratchpad")


def setup(size=256, ortho=220.0):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'
    sc.display.shading.color_type = 'TEXTURE'
    sc.render.resolution_x = size
    sc.render.resolution_y = size
    sc.render.film_transparent = False
    cam = bpy.data.objects.get("StripCam")
    if not cam:
        cd = bpy.data.cameras.new("StripCam")
        cam = bpy.data.objects.new("StripCam", cd)
        sc.collection.objects.link(cam)
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = ortho
    cam.data.clip_end = 5000
    sc.camera = cam
    return cam


def place(cam, view, center=(0, 0, 90), dist=600):
    c = mathutils.Vector(center)
    dirs = {
        "front": mathutils.Vector((0, -1, 0)),
        "side": mathutils.Vector((-1, 0, 0)),
        "back": mathutils.Vector((0, 1, 0)),
        "top": mathutils.Vector((0, -0.6, 1)).normalized(),
        "iso": mathutils.Vector((-0.6, -0.8, 0.9)).normalized(),
    }
    d = dirs[view]
    cam.location = c + d * dist
    rot = (c - cam.location).to_track_quat('-Z', 'Y')
    cam.rotation_euler = rot.to_euler()


def render_strip(name, frames, view="side", center=(0, 0, 90),
                 ortho=220.0, size=256):
    """Render the frames side by side into SCRATCH/name.png."""
    sc = bpy.context.scene
    cam = setup(size, ortho)
    place(cam, view, center)
    tiles = []
    for i, f in enumerate(frames):
        sc.frame_set(int(f))
        p = os.path.join(SCRATCH, "_tile.png")
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(p, check_existing=False)
        px = np.array(img.pixels[:], dtype=np.float32).reshape(
            size, size, 4)
        tiles.append(px)
        bpy.data.images.remove(img)
    strip = np.concatenate(tiles, axis=1)
    h, w = strip.shape[:2]
    out = bpy.data.images.new("strip_" + name, w, h, alpha=True)
    out.pixels[:] = strip.ravel()
    out.filepath_raw = os.path.join(SCRATCH, name + ".png")
    out.file_format = 'PNG'
    out.save()
    path = out.filepath_raw
    bpy.data.images.remove(out)
    return path
