"""Builds the trailer's sound track, Audio/mix.wav (run in Blender).

blender --background --python blender_mix.py

Voices, the song and the radio tuning effect come from Audio/, every
other effect is synthesized here. Times are trailer seconds.
"""
import os

import aud
import numpy

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.join(os.path.dirname(HERE), "Audio")
RATE = 48000
LENGTH = 78.0
rng = numpy.random.default_rng(5)
master = numpy.zeros((int(LENGTH * RATE), 2), dtype=numpy.float32)


def load(path, low=None, high=None):
    """A file as stereo samples at RATE, optionally band limited."""
    sound = aud.Sound(path).resample(RATE, 3).rechannel(2)
    for _ in range(3):
        if high:
            sound = sound.highpass(high)
        if low:
            sound = sound.lowpass(low)
    return sound.data().copy()


def shape(mono, low=None, high=None):
    """Band limits generated mono samples, returns them as stereo."""
    stereo = numpy.repeat(mono.astype(numpy.float32)[:, None], 2, axis=1)
    sound = aud.Sound.buffer(numpy.ascontiguousarray(stereo), RATE)
    for _ in range(3):
        if high:
            sound = sound.highpass(high)
        if low:
            sound = sound.lowpass(low)
    return sound.data().copy()


def put(samples, at, gain=1.0, start=0.0, end=None, fade_in=0.01,
        fade_out=0.03):
    """Mixes samples[start:end] (seconds) into the master at a time."""
    part = samples[int(start * RATE):int(end * RATE) if end else None]
    first = int(at * RATE)
    part = part[:max(0, len(master) - first)].copy()
    ramp = numpy.ones(len(part), dtype=numpy.float32)
    rise = min(len(part), int(fade_in * RATE))
    fall = min(len(part), int(fade_out * RATE))
    ramp[:rise] = numpy.linspace(0, 1, rise)
    ramp[len(part) - fall:] *= numpy.linspace(1, 0, fall)
    master[first:first + len(part)] += part * ramp[:, None] * gain


def clock(seconds):
    return numpy.arange(int(seconds * RATE)) / RATE


def noise(seconds):
    return rng.standard_normal(int(seconds * RATE)).astype(numpy.float32)


def thud(seconds=0.5, pitch=55.0):
    time = clock(seconds)
    body = numpy.sin(2 * numpy.pi * pitch * time * (1 + 0.6 * numpy.exp(
        -time * 30))) * numpy.exp(-time * 9)
    click = noise(seconds) * numpy.exp(-time * 120) * 0.5
    return shape(body + click, low=2500)


def crackle(seconds):
    """Fire: a low wavering roar with irregular snaps of varied length."""
    time = clock(seconds)
    pops = numpy.zeros(len(time), dtype=numpy.float32)
    at = 0.0
    while at < seconds - 0.2:
        at += rng.exponential(0.28)
        length = rng.uniform(0.004, 0.05)
        first = int(at * RATE)
        size = min(len(pops) - first, int(length * RATE))
        if size <= 0:
            break
        decay = numpy.exp(-numpy.arange(size) / (size / 4.0))
        pops[first:first + size] += (
            noise(length)[:size] * decay * rng.uniform(0.1, 1.0) ** 2)
    waver = 0.55 + 0.45 * numpy.sin(time * 1.7) * numpy.sin(time * 0.53)
    roar = shape(noise(seconds) * waver, low=220)
    hiss = shape(noise(seconds) * waver, low=1800, high=700)
    return roar * 0.6 + hiss * 0.05 + shape(pops, low=2600, high=350) * 0.8


def crickets(seconds):
    time = clock(seconds)
    chirp = (numpy.sin(2 * numpy.pi * 4300 * time)
             * (numpy.sin(2 * numpy.pi * 38 * time) > 0.2)
             * (numpy.sin(2 * numpy.pi * 1.4 * time) > 0.55))
    return shape(chirp, high=3000) * 0.5


def engine(seconds, pitch, low):
    """A small four-cylinder drone at the given pitch curve (Hz)."""
    phase = numpy.cumsum(2 * numpy.pi * pitch * numpy.ones(
        int(seconds * RATE))) / RATE
    wave = sum(numpy.sin(phase * part) / part for part in range(1, 9))
    wave += 0.6 * numpy.sin(phase * 0.5)
    flutter = 1 + 0.15 * numpy.sin(phase * 0.25)
    return shape(wave * flutter, low=low)


# The Civic comes up the road and passes the camera, then we ride in it.
time = clock(6.0)
near = (time / 5.6).clip(0, 1) ** 3 * numpy.exp(-(time - 5.6).clip(0) * 3)
doppler = 118.0 * (1.04 - 0.1 / (1 + numpy.exp(-(time - 5.6) * 9)))
put(engine(6.0, doppler, 1500) * near[:, None], 0.0, 0.3, fade_in=0.5,
    fade_out=0.05)
put(shape(noise(6.0) * near, low=1600, high=250), 0.0, 0.6, fade_out=0.05)
put(engine(13.5, 96.0, 260), 6.0, 0.16, fade_in=0.05, fade_out=0.6)
put(shape(noise(13.5), low=320), 6.0, 0.25, fade_in=0.05, fade_out=0.6)

# She tunes the radio in while the car comes up the road (a sound
# effect from YouTube: "Radio Tuning Sound Effect [ HD ]" by n Beats).
tuning = load(os.path.join(AUDIO, "sfx_radio_tuning.m4a"))
tuning /= numpy.abs(tuning).max()
put(tuning, 0.8, 1.3, start=2.0, end=8.5, fade_in=0.5, fade_out=0.6)

# The song plays once, without a break, from 0:07 to the end. Two bars
# of its intro are repeated (16 s back to 12 s, on the bar line), so
# the chorus starts on the shot (0:51) and the last chord lands on the
# title. It starts thin, on the car radio, and opens up in her daydream;
# after that only its level changes.
SONG_AT = 7.0


def spliced(samples):
    head = samples[:int(16.0 * RATE)].copy()
    tail = samples[int(12.0 * RATE):].copy()
    blend = int(0.02 * RATE)
    ramp = numpy.linspace(0, 1, blend, dtype=numpy.float32)[:, None]
    head[-blend:] = (head[-blend:] * (1 - ramp)
                     + samples[int(12.0 * RATE) - blend:int(12.0 * RATE)]
                     * ramp)
    return numpy.concatenate((head, tail))


song = spliced(load(os.path.join(AUDIO, "song_a.mp3")))
radio = spliced(load(os.path.join(AUDIO, "song_a.mp3"), low=3200,
                     high=350))
radio *= numpy.sqrt((song[:16 * RATE] ** 2).mean()
                    / (radio[:16 * RATE] ** 2).mean())
when = SONG_AT + numpy.arange(len(song)) / RATE
opened = numpy.interp(when, (19.5, 21.5), (0.0, 1.0))[:, None]
LEVELS = (
    (7.0, 0.5), (11.5, 0.5), (12.0, 0.3), (19.3, 0.3), (19.8, 0.3),
    (35.4, 0.3), (35.9, 0.8), (54.9, 0.8), (55.6, 0.2), (68.9, 0.2),
    (69.6, 0.9), (80.0, 0.9))
level = numpy.interp(when, [point[0] for point in LEVELS],
                     [point[1] for point in LEVELS])[:, None]
put((radio * (1 - opened) + song * opened) * level, SONG_AT, 1.0,
    fade_in=0.4, fade_out=0.3)
for echo in range(1, 8):
    # The last chord rings on a little longer.
    put(song, 74.0 + echo * 0.17, 0.9 * 0.6 ** echo, start=67.0, end=67.5,
        fade_in=0.05, fade_out=0.4)

# Voices. The TTS files start with the read-out direction: skip it.
VOICES = (
    ("dj_ad", 7.75, 11.9, 1.3),
    ("hen_ambitious", 8.4, 20.4, 2.0),
    ("hen_unambitious", 8.9, 25.9, 2.0),
    ("dj_back3", 6.45, 33.0, 1.5),
    ("kolya", 14.6, 55.9, 2.0),
    ("hen_hungry", 7.9, 64.3, 2.0))
for name, start, at, gain in VOICES:
    path = os.path.join(AUDIO, f"vo_{name}.wav")
    on_radio = name.startswith("dj")
    voice = load(path, low=3400, high=450) if on_radio else load(path)
    voice = voice[int(start * RATE):]
    voice /= max(1e-6, numpy.abs(voice).max())
    put(voice, at, gain)

# Effects: the slices close, the stamp, the neon, the trunk, the
# pump, the shot, the cap and the flatbread.
put(thud(0.5, 70.0), 31.6, 0.3)
# The stamp comes down as the box is ticked.
put(thud(0.5, 95.0), 32.17, 1.6)
put(shape(noise(0.08) * numpy.exp(-clock(0.08) * 60), low=3000, high=200),
    32.17, 1.4, fade_in=0.001)
buzz = numpy.sign(numpy.sin(2 * numpy.pi * 100 * clock(4.0))) * 0.5
put(shape(buzz + noise(4.0) * 0.1, low=2400, high=90), 40.0, 0.05,
    fade_in=0.1, fade_out=0.1)
time = clock(0.9)
creak = numpy.sin(2 * numpy.pi * numpy.cumsum(
    380 + 240 * time + 30 * numpy.sin(2 * numpy.pi * 23 * time)) / RATE)
put(shape(creak * numpy.exp(-time * 1.5), low=3000, high=250), 44.3, 0.12,
    fade_in=0.05, fade_out=0.2)
put(thud(0.4, 60.0), 44.9, 0.5)
for at in (48.4, 48.7):
    # The pump: two dry mechanical racks.
    time = clock(0.11)
    rack = noise(0.11) * numpy.exp(-time * 40)
    put(shape(rack, low=2400, high=280), at, 1.3, fade_in=0.001)
    put(thud(0.12, 120.0), at, 0.5)
# The shot: a hard crack, a mid body, a long low tail and a thump.
SHOT_AT = 51.0
time = clock(2.5)
crack = noise(0.06) * numpy.exp(-clock(0.06) * 45)
body = shape(noise(2.5) * numpy.exp(-time * 9), low=4200, high=180)
tail = shape(noise(2.5) * numpy.exp(-time * 2.6), low=950)
put(numpy.repeat(crack[:, None], 2, axis=1), SHOT_AT, 2.6, fade_in=0.0002)
put(body * 2.6 + tail * 2.4 + thud(2.5, 58.0) * 2.0, SHOT_AT, 1.0,
    fade_in=0.0005, fade_out=1.0)
put(thud(0.2, 140.0), 53.35, 0.12)
put(thud(0.25, 95.0), 53.8, 0.2)

# The camp: fire, crickets, the river, then the truck fridge.
put(crackle(15.0), 54.7, 2.2, fade_in=1.5, fade_out=1.0)
put(crickets(14.0), 55.15, 0.1, fade_in=2.0, fade_out=1.5)
put(shape(noise(14.0), low=900, high=300), 55.15, 0.03, fade_in=2.0,
    fade_out=1.5)
time = clock(6.5)
hum = (numpy.sin(2 * numpy.pi * 50 * time)
       + 0.5 * numpy.sin(2 * numpy.pi * 100 * time)
       + 0.25 * numpy.sin(2 * numpy.pi * 150 * time))
put(shape(hum, low=400), 63.0, 0.07, fade_in=2.5, fade_out=0.3)

# A soft limiter: voices sit near full level, the shot runs into it.
master = numpy.tanh(master / 2.0) * 0.97
aud.Sound.buffer(
    numpy.ascontiguousarray(master, dtype=numpy.float32), RATE).write(
    os.path.join(AUDIO, "mix.wav"), RATE, 2, aud.FORMAT_S16,
    aud.CONTAINER_WAV, aud.CODEC_PCM)
print("WROTE mix.wav")
