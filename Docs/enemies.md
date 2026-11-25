# Enemy AI

The enemy base class, the Shawarman and the scripted first fight: how
they work and how to set them up. Design and numbers are in the
[GDD](gdd.md#enemies) and the
[level doc](level0-border-town.md#shawarman). Health and damage are in
[combat.md](combat.md).

## Overview

| Part | Where | What it does |
|---|---|---|
| Base class | `BP_EnemyBase` (BP, Character) | Health, states, sight, patrol, attack, shout, death |
| Shawarman | `BP_Shawarman` (child of the base) | 30 HP, 2.4 m/s, knife chop |
| Skewerman | `BP_Skewerman` (child of the Shawarman) | 20 HP, skewer throw |
| Grill Sergeant | `BP_GrillSergeant` (child of the Shawarman) | 80 HP, 1.8 m/s, grill slam |
| First fight | `BP_FirstFight` (BP, level actor) | Scripted 0A encounter |

Assets are in `/Game/Enemies`. Everything is Blueprint, with a simple
per-tick state machine (no Behavior Tree yet).

## Numbers

The issue and the level doc were written for the 5 m/s draft. Everything
here is in the 3 m/s world scale (x0.6), like the rest of the project.

| Value | Level doc (3 m/s scale) | Variable |
|---|---|---|
| Walk speed | 2.4 m/s | `WalkSpeed` (240) |
| Sight | 70 degree cone, 6 m lit, 3 m dark (busy 1.8 m) | `SightHalfAngle` (35), `SightRange`, `DarkSightRange`, `BusySightRange` |
| Awareness | 0.5 s close up to 1.5 s at the edge, drains in 1.5 s | `AwareTimeNear`, `AwareTimeFar` |
| Knife reach | 0.4 m from the collision edge | `AttackReach` (40) |
| Windup | 0.6 s | `WindupTime` |
| Damage | 15 | `AttackDamage` |
| Shout | 7.2 m | `ShoutRadius` (720) |

Light, the awareness meter and noise are in
[Sneaking](#sneaking-light-awareness-and-noise).

## States

`State` is a Name: `Unaware`, `Suspicious`, `Alerted`, `Dead`, or
`Dormant` (waits hidden for a script).

* **Unaware** has the substates in `UnawareMode`: `Idle`, `Patrol`
  (walks the `PatrolRoute` actors in a loop, waits `PatrolWait` at each
  point), `Busy` (short sight), `Sleeping` (never sees her). While
  unaware, `bUnaware` on the enemy's `BPC_Health` is true, which makes
  the peck a surprise peck (x3). Any other state clears it.
* **Suspicious**: she is in sight. The enemy stops, turns to her and its
  awareness fills; when it is full it becomes alerted, when it drains
  back to 0 it goes back to unaware (see
  [Sneaking](#sneaking-light-awareness-and-noise)).
* **Alerted**: chases (`SimpleMoveToActor` on the nav mesh) and attacks
  until it dies. It never searches or returns to patrol. Being hurt (and
  surviving) alerts it too.
* **Shout**: becoming alerted alerts every other enemy within
  `ShoutRadius`, who shout in turn.
* A bark from `Barks` shows over its head for 2 s when it becomes
  alerted. Bark text is a Text Render placeholder for the barks audio.

## Sneaking: light, awareness and noise

The GDD's detection rules (#8). The shared parts are in C++
(`USneakSubsystem`, `Source/acrpg/Combat`), the enemy side in
`BP_EnemyBase`.

* **Lit or dark.** `USneakSubsystem.IsLit(Location, Ignore)`. While an
  actor tagged `Darkness` exists (the night post process volume
  `NightExposure` on `DL_Night`), she is lit only inside a lit zone or a
  light cone; by day everything is lit.
  * Lit zones are actors tagged `LitZone`: the graybox Lit markers, whose
    disc radius is the zone (up to 4 m above it).
  * Light cones are spot lights tagged `SightLight` (component or actor
    tag) that are visible and on: within the attenuation radius and the
    outer cone angle, with nothing on the Visibility channel in between,
    so cars cast dark shadows. Tagged: the Shawarman's flashlight
    (`Beam`, 9 m, 24 degrees, shown on `Patrol`) and the Doner's beam.
  * Console: `Sneak.Info` lists the zones, cones and darkness.
* **Sight range** (`SightRangeNow`): busy (unaware and `Busy`)
  `BusySightRange` (1.8 m), else `SightRange` (6 m) when she is lit and
  `DarkSightRange` (3 m) in the dark. Sleeping enemies never see her.
  `CanSeeTarget` adds the 70 degree cone and a line of sight trace.
* **Awareness** (`Awareness`, 0 to 1): seeing her makes an unaware enemy
  suspicious. Each tick in sight it fills by Dt / fill time, the fill time
  sliding from `AwareTimeNear` (0.5 s) at 0 m to `AwareTimeFar` (1.5 s) at
  the edge of the current range; out of sight it drains in
  `AwareTimeFar`. Full: alerted. Empty: unaware again.
* **Meter**: `AwareMeter`, a screen space widget component with
  `WBP_AwarenessMeter` (a 46 pt orange "?" over a 48 x 12 px bar) above the
  head, shown while suspicious and for 1.5 s after becoming alerted
  (`AlertShowUntil`), when the mark turns to "!". `UpdateAwareMeter`
  runs every tick and creates the widget when a placed actor has none.
* **Noise.** `USneakSubsystem.ReportNoise(Location, Radius, Tag)` calls
  `HearNoise(Location, Tag)` on every actor within the radius that has
  it; an unaware or suspicious enemy (sleeping ones too) becomes alerted.
  Sources: a peck hit (`PeckNoiseRange`, 3.6 m), a shattered gnome
  (`NoiseRange`, 6 m), a shot (`NoiseRange`, 15 m). The inner gate
  squeak makes no noise.

### All-Seeing Doner

`BP_AllSeeingDoner` (`/Game/Enemies`) is the lookout on the tower in the
middle of the outer lot (L0, `AllSeeingDoner` on `DL_Night`, over the
`AllSeeingDoner_Tower` graybox). Its `Head` (at 19.7 m) turns with an
eye (`Iris` and a vertical `Slit` pupil) and the `Beam` spot light
(tag `SightLight`, 59 degrees down, 10 degree cone, 35 m, unitless
intensity 150000), so in the beam she counts as lit for every guard.
`Shaft` (an engine cone with `M_DonerBeam`: additive, warm and faint,
fading out within 5 to 20 m of the camera) shows where the beam points
from anywhere in the lot; it is hidden while the beam is locked on her.
`EyeGlow` is an orange point light in front of the eye. The tower's fixed
graybox eye (`P6`, `P7`) is hidden in game.

* **Sweep**: `SweepStep` (90 degrees) in `SweepMove` (1.5 s), then a
  `SweepPause` (0.5 s): a full turn in 8 s with four pauses.
* **Awareness**: in the beam it fills in `AwareTime` (1 s), out of it it
  drains as fast. The slit narrows from 40 to 8 cm and the beam goes
  from `BaseIntensity` to `AlertIntensity` as it fills.
* **Spotted** (`Spot`): it locks the head and the beam on her, plays
  `Jingle` (`SW_KebabJingle`, `Art/Audio/Scripts/make_jingle.js`) in 2D
  and alerts every enemy within `AlertRadius` (12 m) of her. It follows
  her until she is out of the beam for `ReleaseTime` (3 s), then sweeps
  again from there.

### 0B night shift

On `DL_Night`, folder `Night/Enemies`, at the Shawarman markers (the
markers, patrol points and lit discs are hidden in game, as are the text
labels of the night markers and the impounded cars):

| Actor | Mode | Notes |
|---|---|---|
| `Shawarman_Night_PatrolA` | Patrol, flashlight | Starts at `MK_Patrol_A_2` and loops A_3, A_4, A_1 (the hole corner, about 13 s in), A_2 |
| `Shawarman_Night_PatrolB` | Patrol, flashlight | Loops B_1 to B_4 through the middle rows |
| `Shawarman_Night_Grill_1` to `_3` | Busy | At the grill shack table, backs to the lot |
| `Shawarman_Night_Sleeping` | Sleeping | In the guard office, wakes only to noise |

All are tagged `NightShift` (the waves in #9 count them).

Checked in PIE (`Story.Set q_car_trouble office`,
`Story.Event wait_for_midnight`): walking the fence lane from the hole
to the office at full speed alerts nobody; standing 1.2 m behind the
eaters is unseen and pecking one alerts the other two; in the dark a
guard notices her at 2.5 m but not at 3.5 m, his meter fills in 1.33 s
there, 0.83 s at 1 m, and stepping back to 6 m at 60 % drains it in
0.9 s; holding her in the Doner beam locks it after 1 s and alerts the
guards within 12 m.

## Attack

When the chicken is within `AttackReach` (plus both capsule radii) and
the cooldown is over, the enemy stops, keeps its facing, raises the knife
and lights the glint. After `WindupTime` the knife swings and hits if she
is still in reach and in the front 90 degrees. The facing is not updated
during the windup, so a sidestep or a flutter avoids it (flutter makes
her invulnerable, so the hit does nothing). Recovery takes 0.5 s, then
`AttackCooldown` (1.2 s). The damage goes through
`BPC_Health.ApplyDamage(AttackDamage, KillerTag, enemy)`, with
`KillerTag` `Shawarman` for the death screen.

With `bAnimatedBody` on (the Shawarman) the attack plays `AttackMontage`
instead of moving the placeholder knife. The Shawarman's is
`AM_Shawarman_Chop`: the knife goes up, then he chops down and kneels,
and the blade reaches the ground about 65 cm in front of him exactly at
`WindupTime` (0.6 s), where she stands. That is why the reach is only
0.4 m: he steps up to her before he chops. The glint is a point light at
the blade. The windup sound is not added yet.

Getting hurt (and surviving) always plays `HitMontage` on an animated
body and cancels a running attack (`CancelAttack`: the strike timer is
cleared, then the usual cooldown), so a peck during the windup saves
her. The Shawarman's is `AM_Shawarman_Flinch`: he doubles over and
clutches his belly for 0.8 s.

## Health bar

An enemy shows no health bar until it is first hurt. The `HealthBar`
widget component (screen space, `WBP_EnemyHealthBar` in `/Game/UI`: a
70 by 8 px red bar on dark red in a black frame) starts hidden.
`OnDamaged` and `OnDied` call `UpdateHealthBar`, which puts the bar
`HealthBarGap` above the capsule top (34 cm on the base and the
Shawarman, so it clears his cap), shows it while health is above 0 and
sets it to health / `MaxHealth`. On death it is hidden. If the component
has no widget (a placed actor loaded before the component existed), the
function creates one.

## Death

`BPC_Health.OnDied` calls `Die`: it stops, loses collision and shows
"Well done!" over it. An animated body plays `DeathMontage` (it holds the
last pose) and is destroyed after 6 s; the placeholder flattens like a
pancake and goes after 4 s. It stays defeated across checkpoint reloads
(`bRemembersDefeat`).

The Shawarman's cap flies off (the `Cap` bone is hidden and the
`CapProp` mesh is thrown with physics) and a flatbread lands on his face
1.1 s later.

## First fight (0A)

`BP_FirstFight` is on `DL_Day` with the three Shawarmen
(`Shawarman_1` to `Shawarman_3`, `bDormant` on, at the old wave markers).

1. The story event `halina_call` sets the flag `f_first_fight` to
   `started` and wakes the `Wave1` enemy: it appears and shouts its
   `ActivateLine`, alerted.
2. When every `Wave1` enemy is dead, the `Wave2` enemies wake up.
3. When they are dead too, the flag becomes `done`.

After a reload with the flag at `started` the fight resumes: defeated
enemies are gone, the others wake up again. Test it with
`Story.Event halina_call`.

## Body and animation

The cooks are skinned meshes in `/Game/Characters/Cooks` (see
[Art/README.md](../Art/README.md#cooks-enemies)). They share one skeleton,
`SK_Shawarman_Skeleton`, and `ABP_Cook`: idle, look-around
(suspicious), eat (busy) and sleep loops picked from `State` and
`UnawareMode`, walk and run blended by speed, and a `DefaultSlot` for the
montages. `ABP_GrillSergeant` is a copy with the shield idle and walk.

Montage variables on `BP_EnemyBase` (category Animation), used when
`bAnimatedBody` is on:

| Variable | When |
|---|---|
| `AttackMontage` | `StartAttack` |
| `ShoutMontage` | Becoming alerted, `Activate` (played at 1.6x) |
| `WakeUpMontage` | Becoming alerted while `Sleeping` (then `Idle`) |
| `HitMontage` | Damaged and still alive (cancels the attack) |
| `DeathMontage` | `Die` |
| `KnockdownMontage`, `GetUpMontage` | `Knockdown`, called by a thrown gnome: 1.5 s down, then up |

While a montage other than the attack plays, an alerted enemy stands
still. The capsule is 78 cm half height (the nav mesh allows agents up to
160 cm) and the head sticks out of it.

`BP_Shawarman` attaches its props on BeginPlay (`SetupBody`): the knife
in the right hand, the flashlight (with a spot light) in the left hand on
`Patrol`, the sharpening steel on `Idle`, a mini kebab on `Busy`, the
plastic chair under him on `Sleeping` (left behind when he wakes). It
picks one of four skin and hair variants (`SkinVariants`) and a random
size of 95 to 105%.

Enemy body parts must not affect navigation: with the dynamic nav mesh a
colliding part carves a hole around the enemy and it can't find a path.

## Skewerman and Grill Sergeant

Both are children of `BP_Shawarman`, so they keep his props code
(`SetupBody`: knife slot, flashlight, steel, kebab, chair, the flatbread on
the face after death) and override only defaults and a few components.
Their own behaviour (the thrown skewer, the lid shield, the hot coals) is
#9; for now they use the base melee attack with their own montages.

| | Skewerman | Grill Sergeant |
|---|---|---|
| Mesh / AnimBP | `SK_Skewerman` / `ABP_Cook` | `SK_GrillSergeant` / `ABP_GrillSergeant` |
| Skin | `MI_Skewerman` | `MI_GrillSergeant` |
| Health | 20 | 80 |
| `WalkSpeed` | 240 | 180 |
| Attack | `AM_Skewerman_Throw`, released at `WindupTime` 1.6 s | `AM_GrillSergeant_Slam`, lands at 1.8 s |
| Reach / damage | 360 cm / 10 (hits at release, no projectile yet) | 60 cm / 25 |
| Death | `AM_Skewerman_Death` | `AM_Shawarman_Death` |
| `KillerTag` | `Skewerman` | `GrillSergeant` |
| Props | `SM_Skewer` in the knife slot, `Bucket` on his back | `Grill` in the right hand, `Lid` in the left, no knife |

The extra props are components under `Mesh`; `AttachProps`, called from
the construction script after the parent's, attaches them to their bones.
The grill and lid sit at the hand bone with no offset (their origin is the
handle). The bucket is placed in mesh space on his back in the reference
pose (0, -11, 100 cm) and then attached to `Spine01` keeping that offset,
so it follows his back. `CapProp` has no mesh on both (no paper cap).
`M_Prop_DarkSteel` (the lid dome and the grill bowl) is two-sided, so the
lid does not show as an empty ring from behind.

## Placing an enemy

Drop a `BP_Shawarman` and set on the instance:

| Property | Meaning |
|---|---|
| `UnawareMode` | `Idle`, `Patrol`, `Busy`, `Sleeping` |
| `PatrolRoute` | Actors to walk between, in order |
| `bDormant` | Hidden until `Activate` is called |
| `ActivateLine` | What it says when it wakes up |

A new enemy type is a child of `BP_EnemyBase` with other numbers, a body
and an attack (override the `StartAttack` and `AttackStrike` functions).
