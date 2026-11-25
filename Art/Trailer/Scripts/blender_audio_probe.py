"""Prints length and a loudness curve of audio files (run in Blender).

blender --background --python blender_audio_probe.py -- <step> <files>
"""
import sys

import aud
import numpy

args = sys.argv[sys.argv.index("--") + 1:]
step = float(args[0])
for path in args[1:]:
    sound = aud.Sound(path)
    rate = sound.specs[0]
    data = sound.data()
    mono = numpy.abs(data).max(axis=1)
    print(f"FILE {path} {len(mono) / rate:.2f} s rate {rate}")
    size = int(rate * step)
    row = []
    for start in range(0, len(mono), size):
        chunk = mono[start:start + size]
        row.append(int(numpy.sqrt((chunk ** 2).mean()) * 100))
    print("RMS", " ".join(str(value) for value in row))
