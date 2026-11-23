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
| `A_Chicken_Peck` | 2.0 s | Wind-up and head strike |
| `A_Chicken_Flutter` | 2.0 s | Flapping hop, has root motion |
| `A_Chicken_Throw` | 2.5 s | Overhead two-wing throw |
| `A_Chicken_ShotgunFire` | 2.0 s | Recoil |
| `A_Chicken_ShotgunPump` | 2.0 s | |
| `A_Chicken_Reload` | 3.0 s | Shells one by one |
| `A_Chicken_EatCorn` | 2.5 s | Pecks at a cob held in the wings |
| `A_Chicken_Kneel` | 5.0 s | Crouch, dig in a bag, stand |
| `A_Chicken_HitReact` | 2.0 s | |
| `A_Chicken_KO` | 3.0 s | Ends on her back, feet up |

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
