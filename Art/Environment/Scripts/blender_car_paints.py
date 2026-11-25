"""Repaints of the Meshy sedan and van textures, for variety in the lot.

blender --background --python blender_car_paints.py

Reads Art/Environment/Meshy/T_Sedan_D.png and T_Van_D.png and writes
Art/Environment/Meshy/Paints/T_<Car>_<Paint>_D.png. Only the body paint
changes: the sedan's beige pixels get a new hue, the van's white pixels
a tint; glass, tires, chrome and rust keep their colors.
"""
import colorsys
import os

import bpy
import numpy

HERE = os.path.dirname(os.path.abspath(__file__))
MESHY = os.path.join(os.path.dirname(HERE), "Meshy")
# paint: (hue 0-1, saturation, brightness factor)
SEDAN = {"Blue": (0.58, 0.55, 0.75), "Red": (0.0, 0.7, 0.75),
         "Green": (0.33, 0.45, 0.6), "Gray": (0.6, 0.06, 0.6),
         "Orange": (0.07, 0.75, 0.95)}
VAN = {"Yellow": (0.13, 0.75, 1.0), "Blue": (0.6, 0.5, 0.75),
       "Red": (0.01, 0.7, 0.8)}


def hsv(pixels):
    high = pixels.max(axis=2)
    low = pixels.min(axis=2)
    spread = high - low
    sat = numpy.where(high > 0, spread / numpy.maximum(high, 1e-6), 0)
    red, green, blue = pixels[..., 0], pixels[..., 1], pixels[..., 2]
    safe = numpy.maximum(spread, 1e-6)
    hue = numpy.where(high == red, ((green - blue) / safe) % 6,
                      numpy.where(high == green, (blue - red) / safe + 2,
                                  (red - green) / safe + 4)) / 6
    return hue, sat, high


def repaint(car, paints, body):
    image = bpy.data.images.load(os.path.join(MESHY, f"T_{car}_D.png"))
    width, height = image.size
    source = numpy.array(image.pixels[:], dtype=numpy.float32).reshape(
        height, width, 4)
    # The file is sRGB; judge the paint in display values.
    hue, sat, value = hsv(source[..., :3] ** (1 / 2.2))
    mask = body(hue, sat, value)[..., None]
    os.makedirs(os.path.join(MESHY, "Paints"), exist_ok=True)
    for paint, (new_hue, new_sat, factor) in paints.items():
        color = numpy.array(colorsys.hsv_to_rgb(new_hue, new_sat, 1.0),
                            dtype=numpy.float32)
        shade = (value[..., None] * factor) * color
        result = source.copy()
        result[..., :3] = numpy.where(mask, shade ** 2.2, source[..., :3])
        out = bpy.data.images.new("out", width, height, alpha=True)
        out.pixels = result.ravel()
        out.filepath_raw = os.path.join(
            MESHY, "Paints", f"T_{car}_{paint}_D.png")
        out.file_format = "PNG"
        out.save()
        bpy.data.images.remove(out)
    print("PAINT", car, f"{mask.mean() * 100:.0f}% of the texture is body")


repaint("Sedan", SEDAN, lambda hue, sat, value: (
    (hue > 0.06) & (hue < 0.2) & (sat > 0.06) & (sat < 0.45) & (value > 0.5)))
repaint("Van", VAN, lambda hue, sat, value: (sat < 0.1) & (value > 0.72))
