"""Shows what changes between neighbouring frames of a shot.

blender --background --python frame_diff.py -- <shot> <frame> ...

For each frame and the next one, writes preview/diff_<shot>_<frame>.png
(the difference, 8x brighter) and prints how much of the picture
changed strongly, per ninth of the frame.
"""
import os
import sys

import bpy
import numpy

HERE = os.path.dirname(os.path.abspath(__file__))
SAVED = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))),
                     "Saved", "Trailer")
args = sys.argv[sys.argv.index("--") + 1:]
shot = args[0]


def load(frame):
    folder = os.path.join(SAVED, "frames", shot)
    if not os.path.isdir(folder):
        # A test still: preview/<shot>_<frame>.png
        folder = os.path.join(SAVED, "preview")
        image = bpy.data.images.load(
            os.path.join(folder, f"{shot}_{frame:04d}.png"))
    else:
        image = bpy.data.images.load(
            os.path.join(folder, f"{frame:04d}.png"))
    size = image.size[:]
    pixels = numpy.array(image.pixels[:], dtype=numpy.float32)
    bpy.data.images.remove(image)
    return pixels.reshape(size[1], size[0], 4)[::-1, :, :3], size


for frame in (int(value) for value in args[1:]):
    first, size = load(frame)
    second, _ = load(frame + 1)
    change = numpy.abs(second - first).max(axis=2)
    strong = change > 0.15
    rows = [" ".join(
        f"{strong[r * size[1] // 3:(r + 1) * size[1] // 3, c * size[0] // 3:(c + 1) * size[0] // 3].mean() * 100:5.2f}"
        for c in range(3)) for r in range(3)]
    print("DIFF", shot, frame, f"{strong.mean() * 100:.2f}% |",
          " | ".join(rows))
    out = numpy.ones((size[1], size[0], 4), dtype=numpy.float32)
    out[:, :, :3] = numpy.clip(change * 8, 0, 1)[:, :, None]
    image = bpy.data.images.new("diff", size[0], size[1])
    image.pixels = out[::-1].ravel()
    image.filepath_raw = os.path.join(
        SAVED, "preview", f"diff_{shot}_{frame:04d}.png")
    image.file_format = "PNG"
    image.save()
