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
| Grill Sergeant | `BP_GrillSergeant` (child of the Shawarman) | 80 HP, 1.8 m/s, lid shield, grill slam, hot coals |
| Mr. Kebabski | `BP_MrKebabski` (child of the Shawarman) | 400 HP boss: Spit Spin, Spit Charge, Order for Table One |
| Projectiles, hazards | `BP_SkewerProjectile`, `BP_HotCoals` | The thrown skewer, the coals after a slam |
| Night fight | `BP_NightShiftFight` (BP, level actor) | 0B waves, crate refill, boss intro |
| First fight | `BP_FirstFight` (BP, level actor) | Scripted 0A encounter |

Assets are in `/Game/Enemies`. Everything is Blueprint, with a simple
per-tick state machine (no Behavior Tree yet).

## Numbers

The issue and the level doc were written for the 5 m/s draft. Everything
here is in the 3 m/s world scale (x0.6), like the rest of the project.

| Value | Level doc (3 m/s scale) | Variable |
|---|---|---|
| Walk speed | 2.4 m/s | `WalkSpeed` (240) |
| Patrol speed | 1.3 m/s | `PatrolSpeed` (130, the sergeant 120); `SetAwareState` sets `MaxWalkSpeed` to it while unaware on `Patrol`, else `WalkSpeed`, so patrols play the walk clip (111 cm/s) instead of the run |
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
* **Getting unstuck** (`UpdateStuck`, every tick while alerted, after
  `UpdateAlerted`, not during an attack, a montage or a climb, and only
  out of reach). Before it an alerted cook could stand still in his idle
  pose for good, which read as "idle after being shot": she shoots from
  a gap between parked cars or next to a prop, where the nav mesh has no
  room, so the path to her fails; or he walks into something that blocks
  pawns but is not in the nav mesh. Now:
  * no move running (`GetMoveStatus` is not `Moving`): he walks to her
    location projected on the nav mesh (300 cm query extent), and if
    that does not start a move either, he steers straight at her
    (`AddMovementInput`);
  * slower than 20 cm/s for 0.5 s (`StuckTime`): for 0.8 s
    (`UnstickUntil`) the path following is stopped and he steers at her
    and sideways (about 63 degrees, the side flips each time,
    `UnstickSide`).
* While unaware, suspicious or alerted, `Tick` first calls
  `EnsureController`: an enemy without an AI controller spawns its
  default one. Re-instancing in PIE (a Blueprint compile, Live Coding)
  leaves the pawns without one, and every move call then logged
  "Accessed None" each frame.
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
    (`Beam`, 9 m, 24 degrees, shown on `Patrol`) and the (removed)
    Doner's beam.
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

Not in the game: the tower and its lookout were removed from L0 after a
playtest (2026-11-28), since the gameplay camera never shows the tower
whole and the middle of the lot read as a stray pole with a light. The
Blueprint is kept, unused, and works as described below if placed again.

`BP_AllSeeingDoner` (`/Game/Enemies`) was the lookout on the tower in the
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

### 0B night shift (sneak part)

On `DL_Night`, folder `Night/Enemies`, at the Shawarman markers (the
markers, patrol points and lit discs are hidden in game, as are the text
labels of the night markers and the impounded cars):

| Actor | Mode | Notes |
|---|---|---|
| `Shawarman_Night_PatrolA` | Patrol, flashlight | Starts at `MK_Patrol_A_2` and loops A_3, A_4, A_1 (the hole corner, about 24 s in at `PatrolSpeed`), A_2 |
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
0.9 s; holding her in the Doner beam (before it was removed) locks it
after 1 s and alerts the guards within 12 m.

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

Variants without new code (category Attack on `BP_EnemyBase`; every
default is 0, which keeps the Shawarman's knife chop):

* `AttackRate`: play rate of `AttackMontage` (0 means 1), so a long clip
  lands on a short `WindupTime`.
* `AttackRadius` and `AttackCenterOffset`: the strike hits her when she is
  within the radius (plus 25 cm) of a point that far in front of him,
  instead of the reach and front check. During the windup a red disc of
  that radius (`AttackArea`) marks the spot on the ground.
* `StrikeSpawnClass`: an actor spawned on the ground at that point when
  the strike lands (the Grill Sergeant's coals).
* `ProjectileClass`: the strike throws this actor from the `RightHand`
  socket at her chest instead of hitting, and hides the held `Knife` slot
  until `AttackEnd` (the Skewerman's skewer).
* `KeepAway`: while she is closer than this (and he is not on a
  container) he backs off instead of attacking.
* `ClimbFrom`, `ClimbTop`, `ClimbMontage`: when `ClimbTop` is set, the
  alerted enemy first walks to `ClimbFrom`, plays the climb montage and
  after 1.2 s is set onto `ClimbTop` (`FinishClimb`); once on top he never
  moves again, he only attacks. Without a `ClimbMontage` `FinishClimb`
  does not move him: `ClimbFrom` is then a ground perch he holds (the
  Skewerman, see below).

`BPC_Health` has two damage modifiers (category Armor, 0 = off):
`DamageBonus` (damage x (1 + bonus), the stunned boss uses 1) and
`FrontReduction` with `FrontArmorCos` (the share of damage stopped when
the causer is inside the front cone, the Grill Sergeant's lid). Every
`ApplyDamage` goes through them.

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
(`Shawarman_1` to `Shawarman_3`, `bDormant` on). They wait close to the
impound office but off screen (`ue_layout_border.py` step
`first_fight`): `Shawarman_1` at (1450, 1950), in the gap between the
tools stall and the Zigaretten shop, about 13 m of path from her at
Halina's window; `Shawarman_2` and `_3` at (1600, 560) and (1600, 700) on
the main street behind the toys stall, about 20 m away. From her spot
when `halina_call` fires (about (120, 1860)) and from the `CP_LeaveOffice`
checkpoint, all three are below the bottom edge of the gameplay camera
(arm 1600, pitch -50, FOV 55), also at the 2400 maximum zoom out and on a
4:3 screen. They used to come from the kebab stand, 30 m away.

1. The story event `halina_call` sets the flag `f_first_fight` to
   `started` and wakes the `Wave1` enemy: it appears and shouts its
   `ActivateLine`, alerted.
2. When every `Wave1` enemy is dead, the `Wave2` enemies wake up.
3. When they are dead too, the flag becomes `done`.

After a reload with the flag at `started` the fight resumes: defeated
enemies are gone, the others wake up again. Test it with
`Story.Event halina_call`. The 0B rule that only alerted enemies count
(below) changes nothing here: `Activate` alerts every enemy it wakes.

Checked in PIE (2026-11-28): she at the window, `Shawarman_1` came round
the stall into view about 5 m from her and reached her 6.5 s after the
event; when he died the other two came into view from the bottom right.

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
The other way round, a level prop that blocks pawns must affect
navigation, or the path leads through it and the cook walks into it: the
art props of `ue_dress_props.py` (parasols, chairs, boxes, the dumpster)
do since 2026-11-28. Their meshes' own collision blocks pawns although
`camera_only` (`ue_dress_lib.py`) meant them for the camera only; the
same holds for the other art (cars, stalls, buildings), which mostly
sits on graybox that is in the nav mesh, but the art cars are wider than
their graybox, so the gaps between parked cars are narrower than the nav
mesh thinks.

## Skewerman and Grill Sergeant

Both are children of `BP_Shawarman`, so they keep his props code
(`SetupBody`: knife slot, flashlight, steel, kebab, chair, the flatbread on
the face after death) and override only defaults and a few components;
their attacks are the variants in [Attack](#attack). The child health
templates have `Health` -1, so `BeginPlay` starts them at `MaxHealth`.

* **Skewerman**: stays 3.6 to 6 m away (`KeepAway` 360, `AttackReach`
  600) and backs off when she comes closer. The throw (`AttackRate` 1.6,
  so the release of the 2.8 s clip is at `WindupTime` 1.0 s) launches
  `BP_SkewerProjectile`: a 1.3x `SM_Skewer` flying straight at `Speed`
  720 cm/s; a Visibility hit (wall, car, ground) sticks it for 1.5 s, coming
  within 55 cm of her does `Damage` 10 (`Skewerman`) and removes it. It
  never turns, so stepping aside dodges it. The wave 2 Skewermen hold
  ground perches by the middle container of each side wall of the arena,
  between two cars (`ClimbFrom` (-3420, -650) and (-3420, 650), set by
  `ue_layout_border.py` step `night_shift`; `BP_Skewerman` has no
  `ClimbMontage`). They used to climb onto the containers (3.5 m), where
  she could not shoot them: the pellets fly level at her height into the
  container wall, and the mouse aim, projected on the ground, misses a
  target that high by meters. `AM_Skewerman_Climb` is unused now.
* **Grill Sergeant**: the lid stops 75 % of the damage from the front 60
  degrees (`FrontReduction` 0.75, `FrontArmorCos` 0.5); from behind he
  takes it all. The slam (`AttackRate` 1.8, lands at `WindupTime` 1.0 s)
  hits a 1.2 m area 1.1 m in front of him for 25 and leaves `BP_HotCoals`:
  a glowing `M_Coals` disc of `Radius` 1.2 m with an orange light for
  `Lifetime` 3 s that does `Damage` 10 every `HurtEvery` 1 s to her
  while she stands in it (killer `GrillSergeant`, the "Grilled chicken"
  death screen).

Checked in PIE: the Skewerman backed from 3.7 to 4.6 m and his skewers hit
a standing target every 3 s for 10; the slam took 25 and the coals 10 a
second; 10 damage to the Grill Sergeant from in front took 2.5, from
behind 10. On their perches (2026-11-28) one shot from about 4.1 m took
the west Skewerman from 20 to 2.6 and the east one from 20 to 1.6.

| | Skewerman | Grill Sergeant |
|---|---|---|
| Mesh / AnimBP | `SK_Skewerman` / `ABP_Cook` | `SK_GrillSergeant` / `ABP_GrillSergeant` |
| Skin | `MI_Skewerman` | `MI_GrillSergeant` |
| Health | 20 | 80 |
| `WalkSpeed` / `PatrolSpeed` | 240 / 130 | 180 / 120 |
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

## Mr. Kebabski

`BP_MrKebabski` is a child of `BP_Shawarman` with the Grill Sergeant's
body (placeholder until his own model), 400 HP, `KillerTag` `MrKebabski`,
no hit flinch, and a spit in his right hand (`SpitRod`, a steel rod with a
doner cone, attached in `AttachSpit` from the construction script). His
`Tick` replaces the base one: when he becomes alerted (the night fight
calls `WakeUp`) he switches to the state `Boss` ("Tonight's special
does not leave the kitchen.") and runs his own phases (`Phase`,
`SetPhase` keeps the timers, the telegraphs, the walk speed and the
stun bonus in one place):

| Phase | What |
|---|---|
| Recover | `RecoverTime` 0.8 s, then: close (`SpinRange` 1.5 m) spin, else charge unless the last attack was a charge, else chase |
| Chase | Walks to her until she is within `SpinRange` |
| SpinWind | `SpinWindup` 0.8 s, red disc `SpinRing` (1.8 m) on the ground, glint |
| Spin | `SpinTime` 2 s turning at `SpinRate`; once per spin 25 if she is within `SpinRadius` 1.8 m |
| ChargeWind | `ChargeWindup` 1 s facing her, red strip `ChargeLine` (12 m) on the ground |
| Charge | Runs along the line at `ChargeSpeed` 9 m/s for up to `ChargeLength` 12 m; 30 if he reaches her (the charge ends there) |
| Stunned | Hit a car (`ImpoundedCar`) or a container (`Container`): `StunTime` 2.5 s, double damage (`DamageBonus` 1), `SW_CarAlarm` at the impact, "WEE-OO! WEE-OO!" |

Never two charges in a row: after a charge he chases until he can spin.
At half health (`OrderForTableOne`, once) he shouts "ORDER FOR TABLE
ONE!", two Shawarmen come from the first two `WaveSpawn` markers and the
arena crates refill (a `BP_ShellPickup` with `Remember` off at every
`Refill` marker). The charge trace is the Visibility channel, so a body
lying in his path also ends a charge.

Checked in PIE: spins hit for 25, a charge hit her for 30, a charge into an
arena car stunned him for 2.5 s and 10 damage took 20; damage no longer
resets his phase; the order spawned the two cooks.

Shell budget: at 2.4 m and closer a shot does 48 (96 while stunned), so
400 HP is 9 close shots or fewer. The arena gives the two crates (16),
their refill between the waves (16), the refill at half health (16), cook
drops and the Civic's trunk, which refills at any time.

## 0B night fight

`NightShiftFight` (`BP_NightShiftFight`, `DL_Night`, `Night/Story`) checks
every 0.5 s:

1. When `q_car_trouble` is `car` (the trunk was opened): wave 1 is the
   night shift that is alerted (`CountAlerted` counts the living `Wave1`
   enemies in the state `Alerted`). Nobody else is alerted by the trunk:
   the sleeper, the eaters and a far patrol she sneaked past stay as they
   are until they notice her (or a shot, 15 m). If fewer than `MinWave1`
   (3) are alerted, the rest come from `GrillSpawn` (the grill shack wave
   marker), woken with `Activate`: they do not shout, so they do not wake
   the eaters next to the marker, and their `BPC_Health` has
   `bRemembersDefeat` off (a spawned cook gets the name of one killed
   before a reload, `BP_Shawarman0`, and a remembered name destroyed the
   new one on spawn).
2. When every alerted wave 1 enemy (and every extra) is dead, the
   unaware ones are ignored: the arena crates refill (`RefillMarkers`),
   and 3 s later `Wave2` wakes up (`WakeUp`): `Shawarman_Wave2_1`/`_2`
   and `Skewerman_Wave2_1`/`_2` at the inner gate (the Skewermen go to
   their perches), `GrillSergeant_Wave2`. They are dormant (hidden, no
   collision) until then.
3. When wave 2 is dead: a `BeforeBoss` checkpoint (phase `Night`), and 2 s
   later `MrKebabski` (dormant at the grill shack) wakes up.

`WakeUp` on `BP_EnemyBase` clears `bDormant`, shows the actor, turns
collision on and alerts it (`BecomeAlerted`). The fight does not resume
from the middle after a reload; a reload restarts it from wave 1 with the
defeated enemies staying defeated.

Checked in PIE: the trunk state started wave 1, killing it refilled two
crates and woke wave 2, killing that woke the boss. Again on 2026-11-28
with only `PatrolA` alerted at the trunk: two extras came, killing the
three started wave 2 while the eaters, `PatrolB` and the sleeper stayed
unaware; the `BeforeBoss` checkpoint saved and the boss woke. His shout
(7.2 m) then alerts the eaters beside him at the grill shack, who join
the boss fight. `Checkpoint.Reload` restarted at wave 1 with three
extras and the survivors unaware.

## Placing an enemy

Drop a `BP_Shawarman` and set on the instance:

| Property | Meaning |
|---|---|
| `UnawareMode` | `Idle`, `Patrol`, `Busy`, `Sleeping` |
| `PatrolRoute` | Actors to walk between, in order (at `PatrolSpeed`) |
| `bDormant` | Hidden until `Activate` is called |
| `ActivateLine` | What it says when it wakes up |

A new enemy type is a child of `BP_EnemyBase` with other numbers, a body
and an attack (override the `StartAttack` and `AttackStrike` functions).
