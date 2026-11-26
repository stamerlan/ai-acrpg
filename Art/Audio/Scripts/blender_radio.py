"""Builds the stop 0 radio broadcasts and car sounds (run in Blender).

blender --background --python Art/Audio/Scripts/blender_radio.py

Writes to Art/Audio:
* SW_Radio_Intro.wav: tuning, the road song on the radio, the Kudakhstan
  ad and "And not one chicken came back!" (the trailer's DJ voice).
* SW_Radio_News.wav: the kebab stand radio's news.
* SW_Radio_Exit.wav: the exit ad, then the song opens up to full.
* SW_Engine.wav: a 4 s loop of the Civic's engine.
* SW_GateCrash.wav: the Civic through the lot's main gate.
* radio_times.json: where each voice starts and ends, for the subtitles.

The trailer voices are Gemini TTS (Art/Trailer/Audio). The news and the
exit ad are placeholders in a Windows voice (Source/, made by
make_placeholder_voices.ps1) until they get the trailer's DJ voice.
"""
import json
import os
import wave

import aud
import numpy

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.dirname(HERE)
TRAILER = os.path.join(os.path.dirname(AUDIO), "Trailer", "Audio")
RATE = 48000
rng = numpy.random.default_rng(7)
times = {}


def load(path, low=None, high=None):
    """A file as mono samples at RATE, optionally band limited."""
    sound = aud.Sound(path).resample(RATE, 3).rechannel(1)
    for _ in range(3):
        if high:
            sound = sound.highpass(high)
        if low:
            sound = sound.lowpass(low)
    return sound.data()[:, 0].copy()


def shape(mono, low=None, high=None):
    """Band limits generated samples."""
    buf = numpy.ascontiguousarray(mono.astype(numpy.float32)[:, None])
    sound = aud.Sound.buffer(buf, RATE)
    for _ in range(3):
        if high:
            sound = sound.highpass(high)
        if low:
            sound = sound.lowpass(low)
    return sound.data()[:, 0].copy()


def clock(seconds):
    return numpy.arange(int(seconds * RATE)) / RATE


def noise(seconds):
    return rng.standard_normal(int(seconds * RATE)).astype(numpy.float32)


def put(track, samples, at, gain=1.0, fade_in=0.01, fade_out=0.03):
    first = int(at * RATE)
    part = samples[:max(0, len(track) - first)].copy()
    ramp = numpy.ones(len(part), dtype=numpy.float32)
    rise = min(len(part), int(fade_in * RATE))
    fall = min(len(part), int(fade_out * RATE))
    ramp[:rise] = numpy.linspace(0, 1, rise)
    ramp[len(part) - fall:] *= numpy.linspace(1, 0, fall)
    track[first:first + len(part)] += part * ramp * gain


def voice(name, start, folder=TRAILER):
    """A DJ line on the radio band, the TTS direction cut off, normalized."""
    samples = load(os.path.join(folder, name), low=3400, high=450)
    samples = samples[int(start * RATE):]
    loud = numpy.nonzero(numpy.abs(samples) > 0.02 * numpy.abs(
        samples).max())[0]
    samples = samples[max(0, loud[0] - 400):loud[-1] + 2400]
    return samples / max(1e-6, numpy.abs(samples).max())


def tuning(seconds=0.8):
    """Static with a whistle sweeping down as the dial turns."""
    time = clock(seconds)
    whistle = numpy.sin(2 * numpy.pi * numpy.cumsum(
        2600 - 2200 * time / seconds) / RATE) * 0.25
    hiss = shape(noise(seconds), low=5000, high=300)
    env = numpy.minimum(1, time / 0.05) * numpy.minimum(
        1, (seconds - time) / 0.25)
    return (hiss * 0.5 + whistle) * env


SONG = load(os.path.join(TRAILER, "song_a.mp3"))
RADIO_SONG = load(os.path.join(TRAILER, "song_a.mp3"), low=3200, high=350)
RADIO_SONG *= numpy.sqrt((SONG[:16 * RATE] ** 2).mean()
                         / (RADIO_SONG[:16 * RATE] ** 2).mean())


def save(name, track):
    """Mono 16-bit WAV (aud's writer fails on long buffers here)."""
    track = track / max(1.0, numpy.abs(track).max() / 0.95)
    pcm = (numpy.clip(track, -1, 1) * 32767).astype('<i2')
    with wave.open(os.path.join(AUDIO, name + ".wav"), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(pcm.tobytes())
    times[name] = times.get(name, {})
    times[name]["length"] = round(len(track) / RATE, 2)


def broadcast(name, lines, length, song_level, open_at=None):
    """Tuning, the song on the radio under the DJ lines (ducked)."""
    track = numpy.zeros(int(length * RATE), dtype=numpy.float32)
    put(track, tuning(), 0.0, 0.6)
    song = RADIO_SONG[:len(track)].copy()
    when = numpy.arange(len(song)) / RATE
    duck = numpy.ones(len(song), dtype=numpy.float32) * song_level
    at = 0.9
    times[name] = {"lines": []}
    for clip, gap in lines:
        end = at + len(clip) / RATE
        duck *= numpy.where((when > at - 0.3) & (when < end + 0.3), 0.3, 1.0)
        put(track, clip, at, 0.9)
        times[name]["lines"].append([round(at, 2), round(end, 2)])
        at = end + gap
    if open_at:
        # The song comes off the radio band into the car, louder
        opened = numpy.interp(when, (open_at, open_at + 2.0), (0, 1))
        full = SONG[:len(song)]
        song = song * (1 - opened) + full * opened
        duck *= 1 + opened * 1.2
    put(track, song * duck, 0.5, 1.0, fade_in=0.4, fade_out=2.0)
    save(name, track)


ad = voice("vo_dj_ad.wav", 7.75)
back = voice("vo_dj_back3.wav", 6.45)
broadcast("SW_Radio_Intro", [(ad, 0.5), (back, 0.0)], 16.0, 0.55)

SOURCE = os.path.join(AUDIO, "Source")
news = voice("vo_dj_news.wav", 0.0, SOURCE)
broadcast("SW_Radio_News", [(news, 0.0)], 8.5, 0.45)
exit_ad = voice("vo_dj_exit.wav", 0.0, SOURCE)
broadcast("SW_Radio_Exit", [(exit_ad, 0.0)], 22.0, 0.5, open_at=9.0)

# Engine: a small four-cylinder drone, whole cycles so it loops
LOOP = 4.0
phase = 2 * numpy.pi * 96.0 * clock(LOOP)
drone = sum(numpy.sin(phase * part) / part for part in range(1, 9))
drone += 0.6 * numpy.sin(phase * 0.5)
drone *= 1 + 0.15 * numpy.sin(phase * 0.25)
hum = shape(drone, low=260) + shape(noise(LOOP), low=320) * 0.6
blend = int(0.2 * RATE)
ramp = numpy.linspace(0, 1, blend)
hum[:blend] = hum[:blend] * ramp + hum[-blend:] * (1 - ramp)
save("SW_Engine", hum[:-blend] * 0.5)

# Gate crash: a thud, a metal clang and the gate rattling down
time = clock(1.6)
body = numpy.sin(2 * numpy.pi * 50 * time * (1 + 0.6 * numpy.exp(
    -time * 30))) * numpy.exp(-time * 7)
clang = sum(numpy.sin(2 * numpy.pi * f * time) * numpy.exp(-time * d)
            for f, d in ((523, 3.0), (1187, 4.0), (1741, 5.5), (2610, 7.0)))
rattle = shape(noise(1.6), low=4000, high=900) * (
    0.5 + 0.5 * numpy.sign(numpy.sin(2 * numpy.pi * 14 * time))) * \
    numpy.exp(-time * 2.5)
crash = shape(body, low=2500) * 1.2 + clang * 0.25 + rattle * 0.5
crash += shape(noise(1.6), low=6000) * numpy.exp(-time * 25)
save("SW_GateCrash", crash)

json.dump(times, open(os.path.join(AUDIO, "radio_times.json"), "w"),
          indent=1)
print("RADIO DONE", json.dumps(times))
