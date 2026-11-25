"""Cuts the trailer in Blender's sequencer and renders Out/trailer.mp4.

blender --background --python blender_edit.py [-- still <second> ...]

Shots come from Saved/Trailer/frames/<shot>/, pictures from Stills/, the
sound from Audio/mix.wav (blender_mix.py). With "still", only the frames
at those seconds are written to Saved/Trailer/preview/cut_<second>.png.
"""
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
TRAILER = os.path.dirname(HERE)
SAVED = os.path.join(
    os.path.dirname(os.path.dirname(TRAILER)), "Saved", "Trailer")
FPS = 24
LENGTH = 78.0
FONT = "C:/Windows/Fonts/impact.ttf"

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = FPS
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.frame_start = 1
scene.frame_end = int(LENGTH * FPS)
scene.view_settings.view_transform = "Standard"
strips = scene.sequence_editor_create().strips
font = bpy.data.fonts.load(FONT)


def frame(second):
    return int(round(second * FPS)) + 1


def fade(strip, keys):
    """Keys the strip's opacity: ((second, alpha), ...)."""
    for second, alpha in keys:
        strip.blend_alpha = alpha
        strip.keyframe_insert("blend_alpha", frame=frame(second))


def shot(name, at, seconds, channel=1):
    """A rendered shot, from its first frame."""
    folder = os.path.join(SAVED, "frames", name)
    files = sorted(os.listdir(folder)) if os.path.isdir(folder) else []
    if not files:
        print("MISSING", name)
        return None
    strip = strips.new_image(name, os.path.join(folder, files[0]), channel,
                             frame(at), fit_method="FILL")
    for file in files[1:]:
        strip.elements.append(file)
    strip.frame_final_duration = min(len(files), int(round(seconds * FPS)))
    return strip


def still(name, at, seconds, zoom=(1.0, 1.0), drift=(0.0, 0.0), channel=1,
          slide=None):
    """A picture with a slow zoom and vertical drift (or a slide)."""
    strip = strips.new_image(name, os.path.join(TRAILER, "Stills", name),
                             channel, frame(at), fit_method="FILL")
    strip.frame_final_duration = int(round(seconds * FPS))
    strip.blend_type = "ALPHA_OVER"
    move = strip.transform
    fill = move.scale_x
    for second, size, rise in ((at, zoom[0], drift[0]),
                               (at + seconds, zoom[1], drift[1])):
        move.scale_x = move.scale_y = fill * size
        move.offset_y = rise
        for path in ("scale_x", "scale_y", "offset_y"):
            move.keyframe_insert(path, frame=frame(second))
    for second, rise in slide or ():
        move.offset_y = rise
        move.keyframe_insert("offset_y", frame=frame(second))
    return strip


def color(at, seconds, rgb=(0, 0, 0), channel=5):
    strip = strips.new_effect("Color", "COLOR", channel, frame(at),
                              length=int(round(seconds * FPS)))
    strip.color = rgb
    strip.blend_type = "ALPHA_OVER"
    return strip


def text(body, at, seconds, size, height=0.5, rgb=(1, 1, 1), channel=6):
    strip = strips.new_effect("Text", "TEXT", channel, frame(at),
                              length=int(round(seconds * FPS)))
    strip.text = body
    strip.font = font
    strip.font_size = size
    strip.color = (*rgb, 1)
    strip.location = (0.5, height)
    strip.alignment_x = "CENTER"
    strip.anchor_x = "CENTER"
    strip.anchor_y = "CENTER"
    strip.wrap_width = 1.0
    strip.use_shadow = False
    strip.blend_type = "ALPHA_OVER"
    return strip


# The road and the radio.
shot("s01j", 0.0, 6.0)
fade(color(0.0, 1.6), ((0.0, 1.0), (0.3, 1.0), (1.5, 0.0)))
shot("s02c", 6.0, 5.5)
shot("s03f", 11.5, 8.0)

# Her daydream: the ambitious chickens, then the bread plane, which the
# two slices close on.
still("ambitious.png", 19.5, 6.0, zoom=(1.22, 1.1), drift=(30.0, -70.0))
still("bread_plane_clean.jpg", 25.5, 6.5, zoom=(1.0, 1.4))
still("bread_face.jpg", 31.1, 0.9, channel=2,
      slide=((31.1, 1090.0), (31.6, 545.0)))
still("bread_face.jpg", 31.1, 0.9, channel=3,
      slide=((31.1, -1090.0), (31.6, -545.0)))
fade(color(31.5, 0.5), ((31.55, 0.0), (31.85, 1.0)))

# The stamp, and the cards.
still("form_empty.jpg", 32.0, 0.17, zoom=(1.0, 1.0))
punch = still("form_stamped.jpg", 32.17, 3.83, zoom=(1.0, 1.06))
fill = punch.transform.scale_x / 1.06
for second, size in ((32.17, 1.16), (32.34, 1.0)):
    punch.transform.scale_x = punch.transform.scale_y = fill * size
    for path in ("scale_x", "scale_y"):
        punch.transform.keyframe_insert(path, frame=frame(second))
color(36.0, 4.0, channel=1)
text("ONE CHICKEN.", 36.0, 2.0, 150)
text("ZERO DOCUMENTS.", 38.0, 2.0, 150)

# The night: the cook, the trunk, the shotgun, what is left of a cook.
# The shot lands on the first beat of the chorus (0:51).
shot("s08h", 40.0, 4.0)
shot("s10", 44.0, 3.5)
shot("s11b", 47.5, 3.5)
shot("s12b", 51.65, 3.5)
fade(color(51.0, 1.3, rgb=(1, 1, 1)),
     ((51.0, 1.0), (51.65, 1.0), (52.25, 0.0)))

# The camp, and the truck.
shot("s13f", 55.15, 6.0)
shot("s14b", 61.15, 2.0)
shot("s15e", 63.15, 6.0)
fade(color(68.65, 0.6), ((68.7, 0.0), (69.15, 1.0)))

# The title, both lines at once; the tagline comes in on the song's
# last chord (1:14).
color(69.15, 8.85, channel=1)
title = text("AMBITIOUS CHICKEN 2", 69.15, 8.85, 150, height=0.6,
             rgb=(1.0, 0.82, 0.25))
fade(title, ((69.15, 0.0), (69.6, 1.0), (77.0, 1.0), (77.9, 0.0)))
name = text("KUDAKH HARDER", 69.15, 8.85, 84, height=0.45)
fade(name, ((69.15, 0.0), (69.6, 1.0), (77.0, 1.0), (77.9, 0.0)))
line = text("In co-co-cosmos, no one can hear you cluck.", 74.0, 4.0, 40,
            height=0.33, rgb=(0.7, 0.7, 0.7))
fade(line, ((74.0, 0.0), (74.4, 1.0), (77.0, 1.0), (77.9, 0.0)))

# Cinema bars on everything, and the sound.
for side in (-1, 1):
    bar = color(0.0, LENGTH, channel=8 + (side > 0))
    bar.transform.scale_y = 138.0 / 1080.0
    bar.transform.offset_y = side * (540.0 - 69.0)
strips.new_sound("Mix", os.path.join(TRAILER, "Audio", "mix.wav"), 12, 1)

rest = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if rest and rest[0] == "still":
    scene.render.image_settings.file_format = "PNG"
    scene.render.resolution_percentage = 50
    for second in rest[1:]:
        scene.frame_set(frame(float(second)))
        scene.render.filepath = os.path.join(
            SAVED, "preview", f"cut_{float(second):05.1f}.png")
        bpy.ops.render.render(write_still=True)
else:
    scene.render.image_settings.media_type = "VIDEO"
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "HIGH"
    scene.render.ffmpeg.gopsize = 24
    scene.render.ffmpeg.audio_codec = "AAC"
    scene.render.ffmpeg.audio_bitrate = 256
    scene.render.ffmpeg.audio_mixrate = 48000
    scene.render.filepath = os.path.join(TRAILER, "Out", "trailer.mp4")
    bpy.ops.render.render(animation=True)
    print("WROTE trailer.mp4")
