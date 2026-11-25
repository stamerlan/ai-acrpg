# Teaser trailer

"Ambitious Chicken 2: Kudakh Harder", 78 s, 1080p. Everything is built by
scripts; nothing here is loaded by the game.

| Folder | What |
|---|---|
| `Out/` | `trailer.mp4`, captions (`trailer.en.srt`, `trailer.ru.srt`), `youtube.txt` (title and description), the song with tags and cover |
| `Scripts/` | The shots, the sound mix and the cut (see below) |
| `Models/` | Meshy models (GLB) and the reference pictures they were made from; `tasks.json` holds the Meshy task ids |
| `Stills/` | Painted pictures: the daydreams, the border form, the song cover |
| `Audio/` | The song (Lyria), the voice lines (Gemini TTS) |
| `Requests/` | The prompts sent to the Google models |

## Building it

Blender 5.3, headless, from `Scripts/`. Frames go to
`Saved/Trailer/frames/<shot>/`, test stills to `Saved/Trailer/preview/`.

| Step | Command |
|---|---|
| One shot | `blender --background --python shots_road.py -- s01j` (add `still <frame>` for a half-size test frame) |
| Several shots, one after another | `bash render_queue.sh shots_road:s01j shots_camp:s13f` |
| Sound | `blender --background --python blender_mix.py` writes `Audio/mix.wav` |
| Cut | `blender --background --python blender_edit.py` writes `Out/trailer.mp4` |
| Song tags | `node tag_song.js` |

The shot names the cut uses are in `blender_edit.py`; a letter after the
number is a version (`s01j`), the script reads only the first three
characters.

| Script | Shots |
|---|---|
| `shots_road.py` | `s01` the Civic comes up the road, `s03` behind the car |
| `shots_car.py` | `s02` her at the wheel, `s10` the trunk, `s11` the shotgun |
| `shots_alley.py` | `s08` the Shawarman under the sign, `s12` his cap lands |
| `shots_camp.py` | `s13` the fire, `s14` her close-up, `s15` the truck |

`trailer_lib.py` holds the shared helpers, `shots_props.py` the cook's
hands. `look_*.py` and `frame_diff.py` are test views and measurements.

## Outside sources

* `gen.js` calls Google models (key in the `GKEY` environment variable):
  pictures with `gemini-3-pro-image`, the song with `lyria-3.5`, voices
  with `gemini-3.8-flash-tts`. The voice files start with the spoken
  style direction; `blender_mix.py` skips it.
* `meshy.js` turns `Models/Reference/<name>.jpg` into `Models/<name>.glb`
  (key in `MKEY`).
* The radio tuning at the start is "Radio Tuning Sound Effect [ HD ]" by
  n Beats (https://www.youtube.com/watch?v=b2qShK5lZOs), no license
  stated. Its file is not in the repository: download the audio to
  `Audio/sfx_radio_tuning.m4a` before running the mix.
* Characters, props and the Kenney kits come from the other `Art/` folders.

## Things that bit

* Meshy plants are single flat leaf cards. Any camera pan makes them cover
  and uncover each other, which reads as blinking polygons: keep the
  camera still on forest shots (`s01`), and give foliage a little
  emission (`trees(glow=...)`) so cards turned from the sun are not black.
* A world volume hides the sky in EEVEE; `fog()` uses a box instead.
* Keys made with `linear=True` are made linear in `render()`; without it
  the car eases in and out and seems to stop.
