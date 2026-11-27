# Source art

Source models and animations made outside the editor, kept here so they
can be re-imported. Nothing in this folder is loaded by the game; UE
assets made from it live under `Content/`.

The props were generated with Meshy (issues #12 and #14). The chicken was
regenerated with Meshy on 2026-11-22/23 because the first one had huge
open wing fans rigged as human arms: lowered, they reached her feet and
swept across the belly and legs, and the clips were human mocap. FBX files
are in centimeters with the chicken 60 cm to the comb top and her feet
at 0.

The teaser trailer and everything made for it are in `Trailer/`
([README](Trailer/README.md)).

## Chicken (`Chicken/`)

| File | What |
|---|---|
| `Source/SK_Chicken.blend` | Working file: mesh, glasses, rig, 23 actions |
| `Mesh/SK_Chicken.fbx` | Skeletal mesh for UE, no animation |
| `Mesh/T_Chicken_BaseColor.png` | Texture |
| `Anims/A_Chicken_*.fbx` | One clip per file, skeleton only |
| `Meshy/SK_Chicken.glb` | Raw Meshy mesh |
| `Meshy/SK_Chicken_Rigged.glb` | Raw Meshy auto-rig of that mesh (rig task `01a20587-8bdc-7617-9300-15b5202a3d37`) |
| `Meshy/A_Chicken_TrunkCandidates.glb` | Raw Meshy library clips on that rig (trunk clips) |
| `Reference/geometric-rooster-base.png` | Base model image (see below) |
| `Reference/chicken-tpose-ref.png` | T-pose image the mesh was built from |

How it was made (Meshy, no hand animation):

* Base: "Geometric Rooster" by liorbendahan19 on Meshy (CC0,
  https://www.meshy.ai/posts/01a1735c-2de0-75e6-8cfb-53926cd44158), a
  low-poly rooster with a round back end and the tail built into the body.
* Meshy image-to-image turned it into her: same faceted shape and tail,
  recolored with the turnaround palette, T-pose, bigger wings ending in
  three primary feathers she can grip with. Then image to 3D (meshy-t2.5
  smart topology, 4.1k tris) and the humanoid auto-rig.
* Clips are Meshy text-to-motion prompts written for a chicken (elbows
  tucked, short quick steps, head bobs).
* Blender, scripted, no keys edited by hand: meters to centimeters,
  `root` bone added, the existing sunglasses fitted to the eyes on a
  `Glasses` bone, loops cut where the pose repeats with a 0.25 s
  crossfade into the start, locomotion made in place, right-side clips
  mirrored from the left ones.
* Two fixes to Meshy's output: the auto-rig skinned the tail about 80% to
  the shoulders, so the tail (past a root at 31 cm height) now follows
  `Tail_01`/`Tail_02` under `Hips`, blended into the body over 6 cm. The
  texture came out beige, so low-saturation feather pixels are recolored
  to the palette white #FBF8F0 with their shading kept; comb, wattles,
  beak and legs are untouched.
* The base's tall rooster comb is shrunk to a low hen comb: its height
  scaled to 45% from its base on the skull (top from 65 to 60 cm), the
  top shortened to 70% front to back.

Export settings: unit scale 0.01, Apply Scalings "All Local", scale 1.0,
no leaf bones, all bones, Y primary / X secondary bone axis. She faces -Y
in Blender, so the mesh needs the usual -90 yaw in the character Blueprint.

In UE the assets live in `/Game/Characters/Chicken` and were re-imported
over the old ones, so `ABP_Chicken` and `BP_Chicken` keep their
references. The mesh has two material slots: `M_Chicken` (body) and
`M_Sunglasses`. The UE skeleton still lists the old helper bones (comb,
beak, brows, primaries, ik_foot); the new mesh does not use them.

### Skeleton (28 bones)

Meshy's humanoid bones (Hips to ToeBase, wings are arms) plus:

| Bones | Parent | Use |
|---|---|---|
| `root` | - | Skeleton root at the feet |
| `Glasses` | `Head` | Sunglasses ride it, can slide down the beak |
| `Tail_01`, `Tail_02` | `Hips` | Tail, unkeyed, for jiggle later |

### Clips

24 fps. Loops start and end on the same pose.

| Clip | Length | Notes |
|---|---|---|
| `A_Chicken_Idle` | 3.25 s | Loop, head jerks side to side |
| `A_Chicken_Walk` | 0.58 s | Loop, in place |
| `A_Chicken_Run` | 0.38 s | Loop, in place, leaning sprint |
| `A_Chicken_WalkBack`, `WalkLeft`, `WalkRight` | 0.58 s | Loops, in place |
| `A_Chicken_RunBack`, `RunLeft`, `RunRight` | 0.38 s | Loops, in place |
| `A_Chicken_CarryWalk` | 0.79 s | Loop, in place, object overhead |
| `A_Chicken_ShotgunAim` | 1.2 s | Loop |
| `A_Chicken_Peck` | 0.67 s | Jump-peck, keyed by script (see below) |
| `A_Chicken_Flutter` | 2.0 s | Flapping hop, has root motion |
| `A_Chicken_Throw` | 2.5 s | Overhead two-wing throw |
| `A_Chicken_ShotgunFire` | 0.67 s | Recoil kick out of the aim pose, keyed by script (see below) |
| `A_Chicken_ShotgunPump` | 2.0 s | |
| `A_Chicken_Reload` | 3.0 s | Not used since the procedural reload (see below) |
| `A_Chicken_EatCorn` | 1.17 s | Three pecks at a cob held in the wing tips, keyed by script (see below) |
| `A_Chicken_Kneel` | 4.96 s | Crouch, rummage in the open backpack, stand; keyed by script (see below) |
| `A_Chicken_HitReact` | 1.08 s | First recoil of the Meshy clip (see below) |
| `A_Chicken_KO` | 3.0 s | Ends on her back, feet up |
| `A_Chicken_TrunkOpen` | 0.75 s | Wings flung up, landing squash (see below) |
| `A_Chicken_TrunkRummage` | 2.0 s | Bend into the trunk, rise holding the box |

### Trunk clips

The Civic trunk scene ([combat.md](../Docs/combat.md)) uses two Meshy
library animations applied to her rig task (above), 3 credits each. Six
candidates were made in one task (`A_Chicken_TrunkCandidates.glb`: Jump
with Arms Open, Jump and Slam Back Down, Happy Jump Female, Female Bend
Over Pick Up Inspect, Male Bend Over Pick Up, Collect Object) and judged
as side-view frame strips. They were imported into `SK_Chicken.blend`
(same bones and rest pose, so the curves copy over), retimed from 30 to
24 fps and trimmed:

| Clip | Source | Window |
|---|---|---|
| `A_Chicken_TrunkOpen` | Jump with Arms Open | 0.25-1.0 s, in place (21 cm drift removed) |
| `A_Chicken_TrunkRummage` | Female Bend Over Pick Up Inspect | 0.6-2.6 s |

The close reuses `A_Chicken_TrunkOpen` from 0.3 s.

### Peck clip

`A_Chicken_Peck` is a jump-peck keyed by script
(`Scripts/blender_combat_clips.py`, `build_peck_jump`), 24 fps, 16
frames (0.67 s). The poses come from the earlier scripted peck (kept as
`A_Chicken_PeckOld`: wind-up and neck-stretched strike), the flutter's
wing spreads and the idle, plus bone turns. The `root` bone lifts her,
so the jump is in the clip and the capsule stays on the ground:

| Frame | Pose |
|---|---|
| 0 | Idle |
| 2 | Wind-up, crouched 3 cm |
| 3-5 | Leap: rising, legs tucked, wings beat up then down |
| 6-7 | Strike at the top, root 40 cm up, beak 44 cm ahead at 85-90 cm (a cook's belly) |
| 8 | Push-off: leaning back, neck pulled in, feet kicked forward |
| 9-12 | Falling back, wings beating |
| 13 | Landing squash |
| 16 | Idle |

`BPC_ChickenCombat` moves the capsule out on frames 2-6 and back on
frames 8-13 (see [combat.md](../Docs/combat.md#peck-and-flutter)).

`A_Chicken_HitReact` is the first recoil of the Meshy hit clip (kept as
`A_Chicken_HitReactOld`): frames 0-20, head and body thrown back, wings
flared, then back to the idle pose by frame 26 (1.08 s), same script
(`build_chicken_hit`).

`A_Chicken_EatCorn` is keyed by the same script (`build_eat_corn`), 24
fps, 28 frames (1.17 s), for the `UpperBody` slot. The Meshy clip (kept
as `A_Chicken_EatCornOld`) barely moved the head and held nothing. The
wing tips grip the ends of a cob lying across her chest (center `COB`,
0 / -22 / 37 cm, tips 8.5 cm apart either side); the wing chains are
turned onto those points by `reach`, which follows the skinned tip
vertex, not the hand bone (the tip is 12 cm past it and split between
two bones). Frames 7, 12 and 17 are pecks (Spine02, neck and Head bent,
the beak 15 cm lower, biting the top of the cob, which dips 1.5 cm);
frames 9 and 14 throw the head back; 19-23 chew with head turns. In UE
the cob is `HeldCorn` on `BP_Chicken`, on the `Hips` bone at the
offset of `COB` (see [hud.md](../Docs/hud.md#eating-corn)).

`A_Chicken_Kneel` (`build_kneel_dig`, the Meshy clip kept as
`A_Chicken_KneelOld`): in the Meshy clip she dug at the ground 22 cm in
front of her, short of the bag. The crouch (frames 0-20) and stand-up
(96-119) stay; frames 28-86 lift her upper body out of the frame 75
crouch (Spine02 and neck turned back) so the beak hangs over the bag
mouth (`BAG_MOUTH`, 31 cm ahead, under the 15 cm rim) and the wing tips
reach into it, one up while the other digs. The HUD pauses on frame 75
and closes from frame 86, both that dig pose.

`A_Chicken_ShotgunFire` is keyed by the same script
(`build_shotgun_fire`), 24 fps, 16 frames (0.67 s), for the `UpperBody`
slot at rate 1. The Meshy clip
(kept as `A_Chicken_ShotgunFireOld`) never matched the aim: the gun hung
down, swung up and back and hung down again. The new clip starts and
ends on frame 0 of `A_Chicken_ShotgunAim`, the pose `ABP_Chicken` layers
under the slot, so the gun stays on the aim line:

| Frame | Pose |
|---|---|
| 0 | Aim |
| 1-2 | Kick: wings turned up about the shoulders (right 13, left 10 degrees), wrist 6, chest 5 and head 6 back; in game the muzzle is 22 degrees up, 9 cm higher, 2 cm back |
| 4-6 | Easing back (level at about 0.27 s) |
| 8 | Muzzle 2 degrees below the aim |
| 10-16 | Aim |

`A_Chicken_Reload` (Meshy) is no longer played: its 3 s loop never
matched the 0.5 s shells, and its left wing never came near the gun. The
reload, the pump and the two-wing hold are now procedural (IK on both
wings, driven by `BPC_Shotgun`, see
[combat.md](../Docs/combat.md#shotgun)). In `A_Chicken_ShotgunAim` and
`A_Chicken_ShotgunFire` the wings are overridden by that IK; only the
body, neck and head motion of those clips shows.

### Locomotion

`ABP_Chicken` plays each clip at speed divided by its natural speed (the
sequence player's play rate basis), so the feet match the ground.

| Clip | Natural speed | Basis |
|---|---|---|
| `A_Chicken_Walk` | 18 cm/s forward | 18 |
| `A_Chicken_WalkBack` | 14.7 cm/s back | 14.7 |
| `A_Chicken_WalkLeft`, `WalkRight` | 13 cm/s sideways | 13 |
| `A_Chicken_Run` | 117 cm/s forward | 117.3 |
| `A_Chicken_RunBack` | 37 cm/s back | 60 |
| `A_Chicken_RunLeft`, `RunRight` | 29 cm/s sideways | 60 |

The back and side runs are short, quick steps; their basis is raised to 60
so they play at most 4.5x at the 270 cm/s run speed (feet slide a little)
instead of 7 to 9x.

## Cooks (enemies)

The Shawarman (#13, #15) and the 0B variants Skewerman and Grill
Sergeant (#16) live in `Enemies/<Name>/`, the props of all three in
`Enemies/Source/EnemyProps.blend` and `Enemies/<Name>/Props/`. Same
layout as the chicken:

| Folder | What |
|---|---|
| `Reference/` | T-pose image the mesh was built from |
| `Meshy/` | Raw Meshy mesh, auto-rig and animation GLBs |
| `Source/SK_<Name>.blend` | Working file in centimeters (the Shawarman one holds every clip) |
| `Mesh/` | `SK_<Name>.fbx` and the base color texture(s) |
| `Anims/` | One clip per FBX, skeleton only |
| `Props/` | Prop FBX files |

How they were made (Meshy, no hand animation except one pose):

* T-pose references made from the concept sheets
  (`Docs/shawarman.png`, `Docs/shawarman-variants.png`) with an image
  model, props left out. Image to 3D with meshy-t2.5 smart topology
  (12k triangles) and the meshy-n1 texture, then the Meshy humanoid
  auto-rig. Every rig was checked: each bone owns vertices near its
  head.
* Clips are Meshy library animations applied to the Shawarman rig only.
  The three rigs have the same bone names, so in UE they share one
  skeleton and the clips play on all three.
* Blender, scripted (`Enemies/Scripts/`): `root` bone added at the feet,
  Meshy's stray 2 m icosphere removed, clips trimmed, made in place where
  they loop, crossfaded into their start, and the knife swing retimed.
  The chop and the flinch (#22) come from `Art/Scripts/
  blender_combat_clips.py` (`build_chop`, `build_flinch`): the chop is
  the Grill Sergeant's slam retimed so the knife (tip 25, 8, 38 cm in
  `RightHand` bone space) lands at the chicken at 0.6 s; the flinch is
  keyed on the first idle frame.
* Shawarman extras: a `Cap` bone under `Head` that owns the paper cap
  (split from the head mesh, so it can fly off; `SM_ShawarmanCap` is the
  same geometry as a static mesh) and `Apron_01`/`Apron_02` under `Hips`
  that own 80% of the apron below the belly, so the legs don't drag the
  apron. Three more textures (`_B` darker skin, `_C` fair skin and
  ginger hair, `_D` olive skin and grey hair) recolor the skin and hair
  pixels of the base one.
* Knife pass (`Scripts/blender_knife_fix.py`): the Shawarman rig was
  rigged again on Meshy (task `01a21510-7cd7-72e2-851b-2cda42c0d901`,
  bones within 1 cm of the first rig) because the first rig's task id
  was not kept; `Meshy/Anim_QuickWalk.glb` is its "Quick Walk" library
  clip, trimmed to one cycle from the left foot plant and retimed from
  24 to 30 fps as `A_Cook_Walk`. The doner knife sits in `RightHand`
  with the blade forward, which put it up through the face in the idle
  hand rub and across it in the shout: `RightHand` is rolled over those
  frames (local Y then X, eased in and out) so the blade stays about
  25 cm from the head. Checked per clip by parenting
  `Props/SM_DonerKnife.fbx` to the bone with the Blueprint transform and
  measuring the blade-to-head distance per frame.
* `A_GrillSergeant_ShieldWalk` and `ShieldIdle` are the walk and
  look-around clips with the left arm keyed to one raised pose (the lid
  hand in front of the chest).
* Props are modelled by script from primitives with flat-color materials.

Heights: Shawarman 175 cm, Skewerman 178 cm, Grill Sergeant 180 cm. They
face -Y in Blender, so the mesh needs the usual -90 yaw in the Blueprint.

### Shared skeleton

UE: `/Game/Characters/Cooks`. All three meshes use
`SK_Shawarman_Skeleton` (28 bones: Meshy's 24, `root`, `Cap`,
`Apron_01`, `Apron_02`). Translation retargeting is Skeleton for every
bone except `root` (Animation) and `Hips` (AnimationScaled), so the lanky
Skewerman and the broad sergeant keep their own proportions on the
Shawarman's clips.

### Clips

30 fps. "Source" is the Meshy library animation.

| Clip | Source | Length | Use |
|---|---|---|---|
| `A_Cook_Walk` | Quick Walk | 1.0 s | Loop, 111 cm/s, the patrol walk |
| `A_Cook_Run` | rig run | 0.63 s | Loop, 450 cm/s |
| `A_Cook_WalkBack` | Walk Backward | 0.87 s | Loop, 105 cm/s, Skewerman backing off |
| `A_Shawarman_Idle` | Scheming Hand Rub | 3.3 s | Loop, honing the knife (right hand rolled so the blade leans up and out, not through the face) |
| `A_Shawarman_Search` | Torch Look Around | 9.3 s | Loop, suspicious with the flashlight |
| `A_Shawarman_Shout` | Angry Stomp | 2.0 s | Alerted shout (right hand rolled while the arms are up) |
| `A_Shawarman_Swing` | Charged Slash | 1.2 s | Old attack, a waist-high spin slash: passes over the chicken, unused |
| `A_Shawarman_Chop` | Charged Ground Slam | 1.33 s | The attack: knife up by 0.23 s, chop, blade on the ground 65 cm ahead at 0.6 s, kneel, up by 1.33 s |
| `A_Shawarman_Eat` | Stand and Drink | 8.9 s | Loop, busy, left hand to the mouth |
| `A_Shawarman_Sleep` | Sit and Doze Off | 17.3 s | Loop, sitting on the plastic chair |
| `A_Shawarman_WakeUp` | Sit to Stand | 2.8 s | Waking up |
| `A_Shawarman_HitReact` | Hit Reaction | 1.6 s | Hand to the head, unused |
| `A_Shawarman_Flinch` | (keyed) | 0.8 s | Pecked: hips back, doubled over, hands on the belly |
| `A_Shawarman_Knockdown`, `GetUp` | Knock Down, Stand Up | 2.5 s, 5.3 s | Thrown gnome, played faster |
| `A_Shawarman_Death` | Dying Backwards | 2.2 s | Flat on his back |
| `A_Skewerman_Throw` | Crouch Charge and Throw (end) | 2.8 s | Windup and release |
| `A_Skewerman_KneelThrow` | Crouch Charge and Throw (start) | 1.7 s | Throw from a container |
| `A_Skewerman_Climb` | Climbing Up Wall | 2.0 s | Climbs about 90 cm |
| `A_Skewerman_Death` | Shot and Blown Back | 2.7 s | Lands on his back, travel cut to 30% |
| `A_GrillSergeant_Slam` | Charged Ground Slam | 3.0 s | Windup, slam at about 1.8 s |
| `A_GrillSergeant_ShieldWalk`, `ShieldIdle` | walk, Torch Look Around | | Left arm holds the lid |

The Grill Sergeant's death reuses `A_Shawarman_Death`. Montages
(`AM_*`) wrap the one-shot clips; the death and knockdown ones hold their
last pose.

### Props

| File | Size | Attach |
|---|---|---|
| `SM_DonerKnife` | 59 cm | `RightHand`, grip at the origin, blade +X |
| `SM_SharpeningSteel` | 39 cm | `LeftHand` |
| `SM_Flashlight` | 20 cm | `LeftHand`, lens +X |
| `SM_MiniKebab` | 15 cm | `LeftHand` |
| `SM_Flatbread` | 30 cm | `Head`, on the face after death |
| `SM_PlasticChair` | 87 cm tall | Floor, under the sleeping cook |
| `SM_ShawarmanCap` | | `Head`, thrown off on death |
| `SM_Skewer` | 55 cm | `RightHand`, ring at the origin |
| `SM_SkewerBucket` | 62 cm with skewers | Back strap at the origin |
| `SM_GrillLid` | 56 cm | `LeftHand` (handle), dome forward |
| `SM_CharcoalGrill` | 48 cm | Side handle at the origin; `M_Coals` is emissive |

`BP_Skewerman` and `BP_GrillSergeant` wear these props (see
[enemies.md](../Docs/enemies.md#skewerman-and-grill-sergeant)).

## Props (`Props/`)

FBX at real size with their textures next to them. `Source/Props.blend`
is the working file; `Reference/` holds the images the shotgun and corn
were built from.

| File | Size | Tris | Origin |
|---|---|---|---|
| `Shotgun/SM_Shotgun.fbx` | 0.90 m long | 3067 | Center, muzzle +X |
| `Gnome/SM_Gnome.fbx` | 0.40 m tall | 2600 | Bottom |
| `Gnome/SM_GnomeBroken.fbx` | 0.40 m long | 2576 | Bottom |
| `Corn/SM_CornCob.fbx` | 0.20 m long | 1523 | Center |
| `Backpack/SM_Backpack.fbx` | 0.30 m tall | 2113 | Bottom |
| `Backpack/SM_BackpackOpen.fbx` | 0.15 m rim, 0.24 m with the flap | 3309 | Bottom, pocket toward -Y |
| `Sunglasses/SM_Sunglasses.fbx` | 0.15 m wide | 622 | `Glasses` bone |
| `Shell/SM_ShellCasing.fbx` | 5.6 cm long | 164 | Center, brass end -X |

The backpack flap is closed; the poses sheet shows it open.
`SM_BackpackOpen` is the bag she digs in while the backpack panel is
open, made from it by `Scripts/blender_backpack_open.py` (`build()` in
`Props.blend`): the top cut off at 17 cm and swung back 150 degrees on
the back edge, the opening and the flap underside closed with dark and
leather faces, shoulder straps and cut slivers removed, a corn cob in the
opening (second material slot), scaled 0.9.

`Scripts/ue_props_import.py` (run in the editor with `py "<path>"`)
imports the gnome, the broken gnome, the corn cob, the shotgun and the
open backpack to `/Game/Props/<Name>` with an `M_Env` instance each
(`MI_<Mesh>`, base color texture `T_<Mesh>_D`), without collision:
`BP_Throwable` and `BP_CornPickup` bring their own, `BPC_Shotgun` and
the backpack need none. The open backpack's cob slot uses `MI_CornCob`
and its instance is 1.8x brighter and matte (`MI_LOOK`): the source
texture is dark and glossy and vanished from the gameplay camera. Mesh names
after the path (`py "<path>" SM_Shotgun`) import only those.

`SM_ShellCasing` is the shotgun shell she loads and ejects, built by
`Scripts/blender_shell.py` (run headless: `blender --background --python
blender_shell.py`, writes `Source/Shell.blend`): a red hull and a brass
head, 1.8 cm across (fatter than a real 12 gauge so it reads from the game
camera), colored from a 2-texel texture so it gets an `M_Env` instance
like the other props.

## Item icons (`Items/`)

Flat 256 px backpack pictures of the stop 0 items, drawn as SVG
(`Source/<Name>.svg`) and rendered to `T_Item_<Name>.png` by
`Scripts/make_icons.js` (`node make_icons.js`, needs Microsoft Edge for
the headless render). `Scripts/ue_items_import.py` imports them to
`/Game/Items/Textures` (UI group, no mips) and sets each as the picture
of `DA_Item_<Name>`. To change an icon, edit its SVG in the script and
run both.

## HUD pictures (`UI/`)

The shell and corn cob pictures of the HUD slots
([hud.md](../Docs/hud.md#hud-cluster)).
`HUD/Source/<Name>_gen.png` are the Nano Banana (Gemini image) results,
1024 px, flat icons with a thick dark outline on pure magenta, from the
prompts in Fable's HUD review (issue #7) in the palette of the item icons.
`Scripts/key_icons.ps1` (`powershell -File key_icons.ps1`) keys out the
magenta (partly keyed edge pixels take the outline color), crops to the
picture and scales it to `HUD/T_HUD_<Name>.png` (shell 104x208, cob
107x160), plus `T_HUD_<Name>Empty.png`, the same shape as a white
silhouette for the empty slots. `Scripts/ue_hud_import.py` (`py "<path>"`
in the editor) imports all four to `/Game/UI/Textures` (UI group, no
mips).

## Audio (`Audio/`)

`SW_KebabJingle.wav` (4.2 s, 22.05 kHz mono) is the All-Seeing Doner's
kebab stand jingle, a chiptune written by `Scripts/make_jingle.js`
(`node Art/Audio/Scripts/make_jingle.js`). UE: `/Game/Audio/SW_KebabJingle`.
`SW_CarAlarm.wav` (2.5 s two-tone siren, `Scripts/make_car_alarm.js`) plays
when Mr. Kebabski charges into a car.

The radio broadcasts and car sounds of the stop 0 cutscenes (issue #10)
are built in Blender by `Scripts/blender_radio.py`
(`blender --background --python Art/Audio/Scripts/blender_radio.py`):

| File | What |
|---|---|
| `SW_Radio_Intro.wav` | Radio tuning, the trailer's road song on the radio band under the trailer's DJ: the Kudakhstan ad and "And not one chicken came back!" |
| `SW_Radio_News.wav` | The kebab stand radio: "Breaking news: why did the chicken cross the border?" |
| `SW_Radio_Exit.wav` | The exit ad, then the song comes off the radio band into the car |
| `SW_Engine.wav` | 4 s loop of the Civic's engine |
| `SW_GateCrash.wav` | The Civic through the impound lot's main gate |
| `radio_times.json` | Where each DJ line starts and ends, for the subtitles |

The DJ voice of the intro is the trailer's (Gemini TTS, `Trailer/Audio`).
The news and the exit ad are placeholders in a Windows voice
(`Source/vo_dj_*.wav`, `Scripts/make_placeholder_voices.ps1`) until they
are made with the trailer's DJ voice (`Trailer/Scripts/gen.js`, voice
Fenrir, `GKEY` set). UE: `/Game/Audio/Radio`, imported by the cutscene
script below.

## Cutscenes (`Cutscenes/`)

`Scripts/ue_cutscenes.py` (`py "<path>"` in the editor, with
`L0_BorderBazaar` open) imports the sounds above and rebuilds the stop 0
level sequences in `/Game/Story/Stop0/Cutscenes` from scratch: `LS_Intro`,
`LS_Tow`, `LS_Exit` (gate ram), `LS_Van` and `LS_DriveOff`. Every actor in
them is a spawnable copy of the level's art (the Civic, a queue truck as
the tow truck, a van, Zbyszek's marker), the chicken and cine cameras;
car paths are sampled from waypoints, so change the waypoints, not the
keys. `cutscene_times.json` holds the time of the gate ram for
`BP_StoryDirector`. How they play: [story-system.md](../Docs/story-system.md#cutscenes).

## Map screen (`UI/Map/`)

`T_Map_Poland.jpg` is the map screen's road map (no text on it; the
buttons carry the names), made by Nano Banana (Gemini) from the prompt:
"A hand-drawn road map of western and northern Poland on old cream paper
... a thick winding red road from that border town east to a city dot in
the middle (Poznan), then north-east to a city dot on the Baltic coast at
the top (Gdansk) ... NO text". UE: `/Game/UI/Map/T_Map_Poland`.

## Dialog tools (`Story/Scripts/`)

`mkdlg.js` writes a DlgSystem dialogue as JSON from a short spec
(`dlg_fencehole.js` is the fence hole dialog), `dlgsum.js` prints an
exported dialogue as a list of nodes and edges. See
[story-system.md](../Docs/story-system.md#dialogs-from-scripts).

## Environment (`Environment/`)

Level art for stop 0, placed over the graybox (see
[graybox.md](../Docs/graybox.md#art-over-the-graybox)). The Kenney kits
and the ground textures are CC0; the vehicles, trees, bushes and ferns
are Meshy models made for the trailer ([Trailer/](Trailer/README.md)).

| Folder | What | Source |
|---|---|---|
| `Kenney/<kit>/*.glb` | Car, city (industrial, roads, commercial, suburban), survival, furniture, food and nature kits | [Kenney](https://kenney.nl/assets), CC0, `License.txt` in each kit |
| `Kenney/_fbx/` | The GLBs as FBX, one joined mesh each | `blender_kenney_to_fbx.py` |
| `Kenney/_textures/` | Kit colormaps; `T_car_kit_colormap_<paint>.png` repaint the car body swatch | Kenney, repaints by hand |
| `Textures/T_*_D.jpg`, `_N.jpg` | Ground: grass, asphalt, pavers, dirt, gravel, concrete (1k) | [Poly Haven](https://polyhaven.com/textures), CC0 |
| `Meshy/` | Vehicles (Civic, sedan, SUV, van, reefer truck) and plants (pine, spruce, birch, oak, bush, fern) at real size, 5k to 20k triangles, one texture each; `Paints/` holds sedan and van repaints | `blender_meshy_to_fbx.py`, `blender_car_paints.py` |
| `Civic/` | The Civic cut into a body and a hatch that opens, and its texture | `blender_civic.py` |
| `Buildings/` | Guard booth, veterinary office, the shops (Zigaretten, Kantor, Friseur, Sklep 24, Bar Grill, a row of market units, a WC container; modern and clean, after photos of real border bazaars) the border officer (a static figure) and the 16 market stalls of the main street (`SM_Stall_<Trade>`: canopy, tables and goods in one mesh, smooth shaded) at real size, 10k to 27k triangles, one 2k texture each; `Buildings/Meshy/` holds the raw GLBs | Meshy (2026-11-26: a nano-banana-2 concept image each, then image to 3D with meshy-7.1 remeshed, 36 credits a model), `blender_buildings_to_fbx.py` |
| `Stall/` | Market stall: pipe frame and sloped tarp with a valance, stripe texture | `blender_stall_kit.py` |
| `Source/StallKit.blend` | Working file of the stall | |

Kenney models are tiny and not to one scale; the dressing scripts scale
each placement. The graybox is 0.6 scale in plan and full height, so a
vehicle stretched to its box came out tall and narrow: the Meshy
vehicles are fitted by length only (`natural` in `ue_dress_lot.py`) and
keep their proportions, which leaves them lower than their collision
box (a car is about 95 cm tall over a 140 cm box). The trees are placed
at about 0.55 of real size for the same reason. The Kenney meshes get `MI_Env_<kit>` (colormap, nearest
filter, no mips) or, for the flat-color kits, one `MI_Env_<kit>_<slot>`
per material slot. Leaves and grass are tinted away from Kenney's mint.

### Scripts (`Environment/Scripts/`)

Blender scripts run in Blender 5.3; the `ue_*` scripts run in the editor
with `py "<path>"` in the Cmd box, with the map open and Play stopped.
Each writes `out.json` next to itself. Run order for a clean pass:

| Script | Does |
|---|---|
| `blender_kenney_to_fbx.py` | GLB to FBX (`convert()`) |
| `blender_stall_kit.py` | Builds and exports the stall (`build()`) |
| `blender_meshy_to_fbx.py` | Meshy GLB to FBX at real size (headless) |
| `blender_car_paints.py` | Sedan and van repaints (headless) |
| `blender_civic.py` | The Civic body and hatch (headless) |
| `ue_meshy_import.py` | Imports the Meshy meshes, textures and the Civic, makes `MI_Meshy_*` and `MI_Civic` |
| `ue_kenney_import.py` | Imports the FBX and colormaps, makes the `MI_Env_*` |
| `blender_buildings_to_fbx.py` | Meshy buildings and the officer to FBX: squared to the axes, front to -Y (headless) |
| `ue_buildings_import.py` | Imports them to `/Game/Environment/Buildings`, makes `MI_Bld_*` |
| `ue_layout_border.py` | Graybox layout pass of 2026-11-26: rectangular bazaar, open road, longer truck queue as the map edge, edge lines, night shift seats and climb points |
| `ue_dress_polish.py` | `M_Ground` parameters, ground palette, car liveries, sun direction |
| `ue_dress_nature.py` | Trees, bushes, grass, rocks by region; far bank ground |
| `ue_dress_lot.py` | Cars, trucks, containers fitted to their graybox boxes |
| `ue_fit_trunk.py` | Puts each trunk actor's lid and light on its Civic |
| `ue_dress_stalls.py` | A Meshy model per stall (`SM_<stall label>`) with its name board; the kit frame, tarp and counter goods for a stall without one |
| `ue_dress_props.py` | Bazaar wall panels, lamps, office yard and apron props |
| `ue_dress_border.py` | Shops of the side yards and the road verge with their blocking boxes, booth and veterinary office over the graybox, the officer, yard props |

`ue_dress_lib.py` holds the shared helpers. Each `ue_dress_*` script
deletes what it placed before (by label prefix: `Art_`, `Art_Nature_`,
`ArtStall_`, `ArtProp_`, `ArtWall_`, `ArtBld_` with `Yard_`) and places it again with a fixed
random seed, so a run is repeatable.

Still graybox: the booth, customs shed, office, grill shack, gate arch,
Doner tower and the gnome rows and crates of the gnome field (issue #24;
the throwable gnomes use `SM_Gnome`), and the people (#25 and #18).
