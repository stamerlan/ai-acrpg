# Source art

Source models and animations made outside the editor, kept here so they
can be re-imported. Nothing in this folder is loaded by the game; UE
assets made from it live under `Content/`.

All assets below were generated with Meshy (issues #12 and #14) on
2026-11-22. Units are meters in GLB and centimeters in FBX; the chicken
is 0.65 m to the comb top with her feet at 0.

## Chicken (`Chicken/`)

| File | What |
|---|---|
| `Reference/chicken-tpose-ref.png` | T-pose image the mesh was built from |
| `Mesh/SK_Chicken.fbx`, `.glb` | Textured, rigged mesh, 8423 tris |
| `Anims/A_Chicken_*.glb` | One clip per file, skin included |
| `Anims/A_Chicken_LibrarySet.*` | 7 library clips in one file |
| `Anims/A_Chicken_Walk.fbx`, `Run.fbx` | Same clips as the GLBs |

Wings are the arms of a humanoid rig, so the wings work as hands. The
eyes are visible: the sunglasses are a separate prop.

Skeleton (24 bones, Meshy humanoid): Hips, Spine02, Spine01, Spine,
neck, Head, head_end, headfront, Left/Right Shoulder, Arm, ForeArm,
Hand, Left/Right UpLeg, Leg, Foot, ToeBase.

### Import format

Import animations from the GLB files. Every GLB shares the same armature
frame. Meshy's FBX export of the custom (text-to-motion) clips uses a
different root frame than `SK_Chicken.fbx`, which tips the chicken onto
her back, so those FBX files are not kept. The walk, run and library FBX
files match `SK_Chicken.fbx` and are safe to use.

### Clips for #14

Lengths are as generated; the GDD timings are set in UE (play rate,
trimming, montage sections). Names in backticks without a file are
clips inside `A_Chicken_LibrarySet`.

| #14 item | Clip | Length | Notes |
|---|---|---|---|
| Idle loop | `Idle` | 4.0 s | GDD wants 2 s |
| Walk | `A_Chicken_Walk` | 1.07 s | Meshy walk |
| Run | `A_Chicken_Run` | 0.67 s | Meshy run |
| Peck windup and strike | `A_Chicken_Peck` | 2.0 s | Split in a montage |
| Flutter dodge | `A_Chicken_Flutter` | 2.0 s | GDD: 0.25 s |
| Carry gnome | `Carry_Heavy_Object_Walk_inplace` | 6.5 s | In place |
| Throw | `Over_Shoulder_Throw` | 4.3 s | |
| Shotgun aim | `A_Chicken_ShotgunAim` | 2.5 s | Loop |
| Shotgun fire | `A_Chicken_ShotgunFire` | 2.0 s | Recoil |
| Shotgun pump | `A_Chicken_ShotgunPump` | 2.0 s | GDD: 0.7 s |
| Reload loop | `Standing_Reload` | 3.3 s | GDD: 0.5 s/shell |
| Eat corn | `A_Chicken_EatCorn` | 2.0 s | GDD: 1 s |
| Kneel at backpack | `Female_Crouch_Pick_Up_Place_Side` | 9.5 s | Crouch |
| Hit react | `Hit_Reaction` | 1.6 s | GDD: 0.2 s |
| KO | `dying_backwards` | 2.2 s | Ends on her back |

The custom clips came from Meshy text-to-motion and were retargeted to
this rig; the rest are from the Meshy animation library.

### Not done yet (from #12)

Meshy only builds the 24-bone humanoid rig above. Still missing:

* Finger bones for the 3 primary feathers per wing.
* Jiggle bones for comb, wattles, tail and hackle.
* A `glasses` bone that slides down the beak; for now the glasses go on
  a socket on `Head` or `headfront`.
* Hinged beak (upper / lower), brow tufts, eye meshes, toe curl.
* Comb, wattles and beak as separate meshes.

These need a Blender pass on `SK_Chicken`, or UE-side work (virtual
bones, Control Rig, AnimDynamics for the jiggle).

## Props (`Props/`)

FBX with their textures next to them. `Reference/` holds the images the
shotgun and corn were built from.

| File | What | Target tris |
|---|---|---|
| `Shotgun/SM_Shotgun.fbx` | Pump-action shotgun | 3000 |
| `Gnome/SM_Gnome.fbx` | Garden gnome | 2500 |
| `Gnome/SM_GnomeBroken.fbx` | Broken gnome with shards | 2500 |
| `Corn/SM_CornCob.fbx` | Corn cob | 1500 |
| `Backpack/SM_Backpack.fbx` | Green backpack, flap closed | 2500 |
| `Sunglasses/SM_Sunglasses.fbx` | Wayfarers, rivets, gold plate | 1500 |

Prop sizes are not set yet: scale them on import (shotgun 0.9 m long,
gnome 0.4 m tall).
