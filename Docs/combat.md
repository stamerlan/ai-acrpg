# Combat, death and checkpoints

Health, peck, flutter, death screens and checkpoints: how they work and
how to set them up. Design and numbers are in the
[GDD](gdd.md#combat), the stop 0 killers in the
[level doc](level0-border-town.md#death-screens).

## Overview

| Part | Where | What it does |
|---|---|---|
| Health | `BPC_Health` (BP) | HP, "killed by" tag, invulnerable and unaware flags, death |
| Chicken combat | `BPC_ChickenCombat` (BP) on `BP_Chicken` | Peck, surprise peck, flutter, death flow |
| Carry | `BPC_Carry` (BP) on `BP_Chicken` | Picking up, carrying and throwing throwables |
| Throwable | `/Game/Throwables/BP_Throwable` | The garden gnome: carried, thrown, shatters |
| Shotgun | `BPC_Shotgun` (BP) on `BP_Chicken` | Shots, pellets, reload, gun mesh, aim pose |
| Ammo | `BP_ShellPickup`, `BP_CivicTrunk` (`/Game/Items`) | Shell crates and drops, the Civic's trunk |
| Death screen | `WBP_DeathScreen`, `DT_DeathScreens` | Food plate, dish, pun line, "Try again" |
| Checkpoint | `BP_Checkpoint` (BP) | Saves on overlap or on a story event |
| Checkpoint state | `UCheckpointSubsystem` (C++) | The last snapshot in memory, reload, defeated actors |
| Data types | `Source/acrpg/Combat/CombatTypes.h` | `FDeathScreenRow`, `FCheckpointSnapshot` |
| Test content | `/Game/Combat/Test` | `BP_TestDummy`, `BP_DamageZone` |

Assets are in `/Game/Combat`. As in the story system, C++ holds only
the subsystem, the console commands and the struct types.

## Health

`BPC_Health` goes on every actor that can be hurt: the chicken and the
enemies. Instance settings:

* `MaxHealth`: 100 for the chicken, per enemy type otherwise.
* `bUnaware`: the owner hasn't noticed her. Enemy AI (#5) keeps it up
  to date; any hit clears it.
* `bRemembersDefeat`: on by default. A defeated actor is remembered by
  the checkpoint subsystem and destroyed on BeginPlay after a reload.
  The chicken has it off.

Every damage source calls `ApplyDamage(Amount, KilledBy, Causer)`.
`KilledBy` is the "killed by" tag, a row name of `DT_DeathScreens`
(`Shawarman`, `Skewerman`, `GrillSergeant`, `MrKebabski`). The hot
coals of the Grill Sergeant use `GrillSergeant`. The chicken's own
hits use `Chicken`.

Damage does nothing while `bInvulnerable` or after death. Events:
`OnDamaged(Amount, KilledBy, Causer)` and `OnDied(KilledBy)`. Other
functions: `Heal`, `RestoreHealth` (sets HP, used by reloads).

## Peck and flutter

`BPC_ChickenCombat` holds the numbers as defaults (GDD values, 3 m/s
scale). `BP_Chicken` binds the inputs: Peck calls `Peck`, Fire calls
`Fire` (throws while carrying, pecks while `HasShotgun` is off,
otherwise shoots, see [Shotgun](#shotgun)), Reload calls
`BPC_Shotgun.Reload`, Flutter calls `Flutter`. While she carries something
(`Carrying`) the peck does nothing.

* **Peck** is a jump at the enemy and back. It picks the nearest living,
  visible pawn with `BPC_Health` whose capsule is at most `PeckReach`
  (1 m) from hers, in a `PeckArc` (120 degree) arc toward the aim point
  (the facing direction without one). The strike point is in front of
  the target: capsules touching plus `PeckGap` (12 cm), so the beak
  stops at a cook's belly instead of inside it. She lands back at the
  start, at least `PeckRetreat` (50 cm) from the strike point. With no
  target she jumps `PeckLungeIdle` (30 cm) forward and back.
* The capsule moves on `Tick` (`UpdatePeck`, swept, on the ground), on
  the beats of the `A_Chicken_Peck` clip, which does the jump itself (40
  cm up at the strike): wind-up until `PeckLaunchTime` (0.083 s), out to
  the strike point by `PeckStrikeDelay` (0.25 s), held, pushes off at
  `PeckPushTime` (0.333 s), back by `PeckLandTime` (0.542 s), done at
  `PeckDuration` (0.667 s, `EndPeck`). She faces the target, ignores
  move input and is invulnerable the whole time; flutter waits for the
  end. One peck per 0.75 s (`PeckCooldown`).
* `PeckStrike` runs on a timer at the strike frame: the target takes 10
  damage (x3 if unaware), a small shove `KnockbackSpeed` (150) and plays
  its hit montage (the Shawarman doubles over, see
  [enemies.md](enemies.md#attack)), which also cancels its attack. A hit
  makes a peck noise (3.6 m, AI perception).
* **Getting hit** (`HandleHurt`, from `BP_Chicken`'s `OnDamaged`): she
  is knocked away from the attacker (`HitKnockback` 350), plays
  `A_Chicken_HitReact` at `HitReactRate` (1.3) and ignores move input
  for `HitStunTime` (0.4 s), after which the clip blends out so she can
  run. Peck and flutter still work during the stun.
* **Flutter** goes 2.4 m in 0.25 s in the movement direction (the
  facing direction when standing still). She is invulnerable, ignores
  move input and can't walk off ledges during the hop. 0.8 s cooldown
  after it ends. A flutter drops a carried object (see below).

## Throwables

Garden gnomes are the stop 0 throwables (GDD: one at a time, 30%
slower, no peck, up to 6 m, 25 damage, 1.5 s knockdown, shatters, 6 m
noise). `BP_Throwable` is the gnome; a later throwable (paper stack,
cabbage) can be a child Blueprint with other meshes and numbers.

* **Pick up:** its `Interactable` (`BPC_Interactable`, type `Carry`,
  prompt "Pick up", 90 cm) calls `BPC_Carry.PickUp` on the chicken. The
  gnome turns off its collision and sits above her head (`CarryOffset`,
  58 cm over the capsule center), her walk speed drops to `SpeedFactor`
  (0.7) of `NormalSpeed`, and `ABP_Chicken` blends `A_Chicken_CarryWalk`
  onto her upper body (from `Spine02`, weight `CarryAlpha`).
* **Carrying:** no interaction prompts show, and Interact puts the
  gnome down in front of her. A flutter or her death drops it at her
  feet.
* **Throw:** Fire. She turns to the aim point (the facing direction
  without one) and plays `A_Chicken_Throw` from `ThrowStartTime` (1.2 s)
  at `ThrowRate` (1.5). After `ReleaseDelay` (0.27 s, the release frame)
  the gnome flies in an arc (`ThrowArc` 0.5) to the aim point on the
  ground, at least 1.5 m and at most `ThrowRange` (6 m) away.
* **Hit:** it flies with its `Projectile` movement and stops at the
  first thing it hits (never her). Then it shatters (`Shatter`): every
  living pawn with `BPC_Health` within `HitRadius` (1 m, center to
  center, flat) takes `Damage` (25, killer tag `Chicken`), enemies play
  `Knockdown` (1.5 s down, then up), and a noise event of `NoiseRange`
  (6 m, tag `Shatter`) goes off for the hearing in #8. The broken gnome
  (`BrokenMesh`) lies on the ground for `LieTime` (10 s).

The gnome's collision (a 14 by 20 cm capsule) blocks pawns, so gnome
rows are low cover, and it carves the dynamic nav mesh.

Placed in `L0_BorderBazaar`: two gnomes at each day gnome marker of the
gnome field (`Day/Throwables`, 12) and three at each night source (the
fence corner crates and next to the Trabant, `Night/Throwables`). The
markers stay in the editor and are hidden in game.

## Shotgun

The farmer's pump-action shotgun ([GDD](gdd.md#shotgun), GDD 3 m/s
scale). `BPC_Shotgun` is a component on `BP_Chicken` (`Shotgun`); its
numbers are defaults on the component.

* **Ammo lives in the story state**, so checkpoints and saves keep it:
  `item_shotgun` (she has it), `item_shells_loaded` (the tube, up to
  `TubeSize` 8) and `item_shells` (the reserve, `MaxCount` 32 on
  `DA_Item_Shells`). Shells picked up before the shotgun are kept.
* **The gun:** on BeginPlay the component adds a static mesh component
  with `SM_Shotgun` (scale `GunScale` 0.75) on the `RightHand` bone at
  `GunOffset` / `GunRotation` (fitted to the aim pose), and a point light
  at the muzzle for the flash. The gun shows while she has it and is
  hidden while she carries something. `ABP_Chicken` blends
  `A_Chicken_ShotgunAim` onto the upper body (third layered blend, from
  `Spine02`) with `ShotgunAlpha`, which the component eases to 1 while
  she has the gun and isn't carrying, pecking or fluttering.
* **Fire:** `BPC_ChickenCombat.Fire` calls `BPC_Shotgun.Fire` once she has
  the gun. With an empty tube Fire pecks, so running dry is never a
  dead end. Otherwise one shot per `ShotInterval` (0.7 s, the pump): she
  turns to the aim point, `A_Chicken_ShotgunFire` plays on `UpperBody`
  at `FireAnimRate` (2.9), the muzzle flashes, and a noise of
  `NoiseRange` (15 m, tag `Shotgun`) goes off for the hearing in #8.
* **Pellets:** `PelletCount` (8) rays fan out over `ConeAngle` (16
  degrees), one per equal slice with a random spot inside it. Each ray is
  traced on the Visibility channel up to `MaxRange` (7.2 m), so walls,
  cars and gnomes stop it; pawns don't block that channel, so a pellet
  hits the nearest living pawn with `BPC_Health` whose capsule the ray
  passes through in front of the wall. Damage per pellet is
  `PelletDamage` (6) times the falloff on the distance to the target's
  capsule: full up to `FullRange` (2.4 m), half at `HalfRange` (4.8 m),
  nothing at 7.2 m, linear in between. All pellets on one target add up
  to one `ApplyDamage` (killer tag `Chicken`) and a small shove
  (`ShoveSpeed` 250 for all 8 pellets).
* **Reload:** only on the Reload button (R / gamepad X), never
  automatic, and only while she stands still (no move input, speed below
  20 cm/s), isn't pecking, fluttering or carrying, and the pump is done.
  It loads one shell every `ShellLoadTime` (0.5 s) from the reserve and
  plays `A_Chicken_Reload` on `UpperBody` until the tube is full or the
  reserve is empty. Moving, firing, a peck, a flutter or picking
  something up stops it; loaded shells stay.

Measured in `Lvl_Dev_Movement` against `Shawarman_Test` (30 HP): at 1.5 m
one shot kills him, at 5 m a shot does about 10 damage (four shots).

### Shells and the trunk

* **Shell crates** are `BP_ShellPickup`, a child of `BP_CornPickup`
  (an open Kenney ammo box, `Item` `DA_Item_Shells`, `Count` 8). Walking
  over one takes the shells while the reserve is below 32; the count is
  capped at 32 (the rest is lost). Picked crates are remembered by the
  checkpoint like corn. `BP_CornPickup` got a `Remember` flag (on by
  default) for pickups that are spawned at runtime.
* **Drops:** `BP_EnemyBase.Die` calls `DropShells`. An enemy with
  `ShellDrop` above 0 whose `DropConditions` pass drops a shell pickup of
  `ShellDrop` shells with a chance that slides from `DropChanceEmpty`
  (50%) at an empty reserve to `DropChanceFull` (10%) at 32, as in the
  [level doc](level0-border-town.md#shawarman). `BP_Shawarman` drops 2
  while `q_car_trouble` is `night`, `keys` or `car` (stop 0B).
* **The Civic's trunk** is `BP_CivicTrunk`, an interactable (Use, 120 cm)
  placed at the Civic in every level where she has the car. The first
  interaction gives the shotgun with `FirstLoaded` (8) shells loaded and
  `FirstReserve` (12) in reserve, moves `q_car_trouble` from `night` or
  `keys` to `car`, fires the story event `trunk_opened` (for the trunk
  checkpoint, #21) and shows the controls in a toast. After that the
  prompt reads "Refill shells" and refills the reserve to 32, any number
  of times. Both run the same scene:
  1. She walks to `StandPoint` behind the bumper (`WalkToSpeed` 150,
     input blocked, gun stowed via `BPC_Shotgun.Stowed`).
  2. She hops onto the bumper (`BumperDepth` in, `BumperRise` up, with
     `HopArc`) while the lid (`Hinge` > `Lid`) swings open to
     `LidOpenAngle` (75 degrees), playing `ClipOpen`.
  3. `ClipRummage` from `RummageStart`; she leans over the rim
     (`RimIn` 15 cm forward, `RimLift` 20 cm up) until just before
     `CloseStart`. The shells (or the shotgun) are given at `GrantTime`.
     `TrunkLight` inside the trunk fades with the lid (`TrunkLightMax`).
  4. `ClipClose` from `CloseStart`, the lid closes, she hops down; input
     and the gun come back at `SceneEnd` (3.4 s).
  Taking damage or dying cancels the scene at once (nothing is given if
  it happens before `GrantTime`). The three clips are variables, so new
  clips only need their rates and start times set.
* **The Civic** with an opening trunk is `SM_CivicBody` and
  `SM_CivicTrunkLid` in `/Game/Environment/Civic`, made by
  `Art/Environment/Scripts/blender_civic.py` from the Kenney sedan (lid
  pivot on its hinge, dark cavity, a red shell box inside). The trunk
  actor's `Hinge`, `Lid` and `StandPoint` are fitted to the car actor
  next to it by a fitting script; `BumperRise` is the bumper top above
  the ground (50 cm in L0, 32.5 cm in the dev map). The lid underside
  and the trunk interior are lighter so the open trunk reads at night.
* **Hint:** the first time the reserve is empty while she has the gun and
  a trunk is in the level, a toast says "No spare shells. The trunk has
  more." (flag `f_hint_trunk`).

In `L0_BorderBazaar` the Civic at the south end of the arena faces north,
so its trunk opens toward the arena and the camera. The trunk
(`CivicTrunk`, needs `item_car_keys`)
and three shell crates (`Shells_Night_*`, at the arena and container
markers) are on `DL_Night`. `Lvl_Dev_Movement` has a test Civic with a
trunk (no key needed) and a crate in `CombatTest`.

## Death

When the chicken's health runs out, `BPC_ChickenCombat.HandleDeath`
switches input to the menu context, stops her, plays the KO clip and
after 1.2 s shows `WBP_DeathScreen` for the `KilledBy` tag. The
"Try again" button appears after 1 s and takes keyboard and gamepad
focus; it reloads the last checkpoint.

### Death screen table

`DT_DeathScreens` (row struct `FDeathScreenRow`) has one row per
killer:

| Column | Meaning |
|---|---|
| `Dish` | What she became, the big title |
| `Picture` | Full screen food picture; without one the plate color shows |
| `PlateColor` | Background color |
| `Lines` | Pun lines of this killer |

The `Generic` row holds the game 1 lines that are mixed into every
killer's pool, and is the screen for unknown tags. To add a killer, add
a row named after its tag.

Pictures are 16:9 textures in `/Game/Combat/UI/DeathScreens`
(`T_Death_<Row>`, UI texture group, no mips), imported from
`Art/DeathScreens`. Keep the lower third of a picture calm: the dish and
the pun line sit there, with a dark outline and shadow so they read on
bright pictures too. `PlateColor` is the picture's average tone. Spare
pictures for new killers are in `Art/DeathScreens/Game1` (game 1
screens redrawn) and `Art/DeathScreens/Ideas`.

## Checkpoints

`BP_Checkpoint` saves a snapshot of the game state in memory: map,
checkpoint id, phase, her spawn point and health, the story state and
the defeated actors. Disk saves (#11) will store
`GetLastCheckpoint()` and restore it with `SetLastCheckpoint()`.

Instance settings:

| Property | Meaning |
|---|---|
| `CheckpointId` | Name shown in `Checkpoint.Info` |
| `Phase` | Level phase saved with it (`Day`, `Night`) |
| `StoryEvent` | Saves when this story event fires |
| `SaveOnOverlap` | Saves when she walks in (off for story checkpoints) |

The arrow (`SpawnPoint`) is where she starts after a reload. Walking
into the checkpoint that was saved last does nothing.

A reload restores the story state and the defeated actors, reopens the
map and puts her at the spawn point with the saved health. Arriving in
a map without a checkpoint saves a `LevelStart` snapshot at her start.
The phase is stored but not applied yet: the night transition (#10)
applies it.

Stop 0 checkpoints placed so far (on `DL_Day`):

| Actor | Saves on |
|---|---|
| `CP_AfterBorderCheck` | story event `border_done` |
| `CP_LeaveOffice` | story event `halina_call` |

The night checkpoints (night start, trunk, before the boss) are #21;
their markers are in `Night/Markers/Checkpoint`. The trunk checkpoint can
save on the story event `trunk_opened`, which `BP_CivicTrunk` fires when
it gives her the shotgun.

## Testing

`Lvl_Dev_Movement` has a `CombatTest` folder: two dummies (30 HP, one
unaware), a Shawarman (`Shawarman_Test`, busy, so he only sees her up
close), a damage zone per stop 0 killer (40 HP per second), two
checkpoints, three gnomes in front of the Shawarman and two corn
pickups. `BP_DamageZone` can also serve as hot coals.

| Command | Does |
|---|---|
| `Checkpoint.Info` | shows the last checkpoint |
| `Checkpoint.Reload` | reloads it |
| `ke * DebugDamage <amount> <killer>` | hurts the chicken, e.g. `ke * DebugDamage 500 Skewerman` |
