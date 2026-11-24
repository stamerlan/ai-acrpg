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
`Fire` (throws while carrying, otherwise pecks while `HasShotgun` is
off), Flutter calls `Flutter`. While she carries something
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

The night checkpoints (night start, trunk, before the boss) come with
the night transition, the shotgun and the boss (#10, #7, #9); their
markers are in `Night/Markers/Checkpoint`.

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
