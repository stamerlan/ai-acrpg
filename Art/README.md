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

## Chicken (`Chicken/`)

| File | What |
|---|---|
| `Source/SK_Chicken.blend` | Working file: mesh, glasses, rig, 21 actions |
| `Mesh/SK_Chicken.fbx` | Skeletal mesh for UE, no animation |
| `Mesh/T_Chicken_BaseColor.png` | Texture |
| `Anims/A_Chicken_*.fbx` | One clip per file, skeleton only |
| `Meshy/SK_Chicken.glb` | Raw Meshy mesh |
| `Meshy/SK_Chicken_Rigged.glb` | Raw Meshy auto-rig of that mesh |
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
| `A_Chicken_ShotgunFire` | 2.0 s | Recoil |
| `A_Chicken_ShotgunPump` | 2.0 s | |
| `A_Chicken_Reload` | 3.0 s | Shells one by one |
| `A_Chicken_EatCorn` | 2.5 s | Pecks at a cob held in the wings |
| `A_Chicken_Kneel` | 5.0 s | Crouch, dig in a bag, stand |
| `A_Chicken_HitReact` | 1.08 s | First recoil of the Meshy clip (see below) |
| `A_Chicken_KO` | 3.0 s | Ends on her back, feet up |

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
| `A_Cook_Walk` | rig walk | 1.0 s | Loop, 117 cm/s |
| `A_Cook_Run` | rig run | 0.63 s | Loop, 450 cm/s |
| `A_Cook_WalkBack` | Walk Backward | 0.87 s | Loop, 105 cm/s, Skewerman backing off |
| `A_Shawarman_Idle` | Scheming Hand Rub | 3.3 s | Loop, honing the knife |
| `A_Shawarman_Search` | Torch Look Around | 9.3 s | Loop, suspicious with the flashlight |
| `A_Shawarman_Shout` | Angry Stomp | 2.0 s | Alerted shout |
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

The Skewerman and Grill Sergeant have no Blueprints yet (#9). Their props
attach the same way as the Shawarman's (see `SetupBody` in
`BP_Shawarman` and [enemies.md](../Docs/enemies.md#body-and-animation)).

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
| `Sunglasses/SM_Sunglasses.fbx` | 0.15 m wide | 622 | `Glasses` bone |

The backpack flap is closed; the poses sheet shows it open.
