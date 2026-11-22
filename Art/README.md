# Source art

Source models and animations made outside the editor, kept here so they
can be re-imported. Nothing in this folder is loaded by the game; UE
assets made from it live under `Content/`.

The chicken and props were generated with Meshy (issues #12 and #14) and
finished in Blender 5.3 on 2026-11-22. FBX files are in centimeters with
the chicken 65 cm to the comb top and her feet at 0.

## Chicken (`Chicken/`)

| File | What |
|---|---|
| `Source/SK_Chicken.blend` | Working file: mesh, rig, all 15 actions |
| `Mesh/SK_Chicken.fbx` | Skeletal mesh for UE, no animation |
| `Mesh/T_Chicken_BaseColor.png` | Body texture |
| `Anims/A_Chicken_*.fbx` | One clip per file, skeleton only |
| `Meshy/` | Raw Meshy output the .blend was built from |
| `Reference/chicken-tpose-ref.png` | T-pose image the mesh was built from |

Import `SK_Chicken.fbx` first, then the clips onto its skeleton. Every
FBX in `Mesh/` and `Anims/` comes from the .blend, so they share one
skeleton; re-export from there after changes.

Both .blend files work in centimeters (unit scale 0.01), because UE
ignores the FBX unit scale and reads values as centimeters. Export
settings: Apply Scalings "All Local", scale 1.0, no leaf bones, all
bones, Y primary / X secondary bone axis.

In UE the assets live in `/Game/Characters/Chicken`. `ABP_Chicken`
blends Idle, Walk (from 0 to 150 cm/s) and Run (150 to 450 cm/s) by
speed and has a `DefaultSlot` for montages; `BP_Protagonist` uses it
with a 25 cm x 33 cm capsule. The MCP import tool cannot import a
skeleton-only FBX, so the clips were imported from one temporary FBX
with the mesh and all 15 actions.

The mesh has two parts: the body (8423 tris, `M_Chicken`) and the
sunglasses (622 tris, `M_Sunglasses`), skinned 100% to the `Glasses`
bone. Her eyes are modeled under the lenses. She faces -Y in Blender,
like the UE mannequin, so the mesh needs the usual -90 yaw in the
character Blueprint.

Meshy put the tail fan on a thin stalk behind the body. In the .blend the
fan was moved 13 cm forward and tilted 4 degrees up so it grows out of
the rump as on the turnaround; the stalk now sits inside the body. The
tail tip is at 63 cm, under the comb top.

### Skeleton (49 bones)

The armature object is named `Armature`, which UE drops; `root` is the
skeleton root. The Meshy humanoid bones (Hips to ToeBase) are kept, so
wings are arms and work as hands.

| Bones | Parent | Use |
|---|---|---|
| `root` | - | Skeleton root at the feet |
| `ik_foot_root`, `ik_foot_l/r` | `root` | Baked to the feet in all clips |
| `Left/RightPrimary1..3` | `Left/RightHand` | 3 primary feathers = fingers |
| `Tail_01`, `Tail_02` | `Hips` | Tail fan, jiggle |
| `Comb_01`, `Comb_02` | `Head` | Comb, jiggle and flop |
| `Wattle` | `Head` | Wattles, jiggle |
| `Hackle` | `neck` | Neck cape, jiggle (40% weight) |
| `BeakUpper`, `BeakLower` | `Head` | Hinged beak |
| `Brow_L/R` | `Head` | Brow tufts, her eyebrows |
| `Eye_L/R` | `Head` | Eyes under the lenses |
| `Glasses` | `Head` | Glasses slide down the beak or push up |
| `Left/RightToeBack` | `Left/RightFoot` | Back toe; `ToeBase` curls front |

Apart from the ik bones, the new bones have no keys in the clips (they
stay at rest); jiggle is meant for AnimDynamics or Control Rig in UE.

### Clips for #14

Lengths are as generated, at 24 fps; the GDD timings are set in UE (play
rate, trimming, montage sections). The custom clips came from Meshy
text-to-motion, the rest from the Meshy animation library.

| #14 item | Clip | Length | Notes |
|---|---|---|---|
| Idle loop | `A_Chicken_Idle` | 4.0 s | GDD wants 2 s |
| Walk | `A_Chicken_Walk` | 1.0 s | Loop |
| Run | `A_Chicken_Run` | 0.6 s | Loop |
| Peck windup and strike | `A_Chicken_Peck` | 2.0 s | Split in a montage |
| Flutter dodge | `A_Chicken_Flutter` | 2.0 s | GDD: 0.25 s |
| Carry gnome | `A_Chicken_CarryWalk` | 6.5 s | Loop, in place |
| Throw | `A_Chicken_Throw` | 4.3 s | |
| Shotgun aim | `A_Chicken_ShotgunAim` | 2.5 s | Loop |
| Shotgun fire | `A_Chicken_ShotgunFire` | 2.0 s | Recoil |
| Shotgun pump | `A_Chicken_ShotgunPump` | 2.0 s | GDD: 0.7 s |
| Reload loop | `A_Chicken_Reload` | 3.3 s | GDD: 0.5 s/shell |
| Eat corn | `A_Chicken_EatCorn` | 2.0 s | GDD: 1 s |
| Kneel at backpack | `A_Chicken_Kneel` | 9.5 s | Use the crouch part |
| Hit react | `A_Chicken_HitReact` | 1.6 s | GDD: 0.2 s |
| KO | `A_Chicken_KO` | 2.2 s | Ends on her back |

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
