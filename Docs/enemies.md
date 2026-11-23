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
| Shawarman | `BP_Shawarman` (child of the base) | 30 HP, 2.4 m/s, knife swing |
| First fight | `BP_FirstFight` (BP, level actor) | Scripted 0A encounter |

Assets are in `/Game/Enemies`. Everything is Blueprint, with a simple
per-tick state machine (no Behavior Tree yet).

## Numbers

The issue and the level doc were written for the 5 m/s draft. Everything
here is in the 3 m/s world scale (x0.6), like the rest of the project.

| Value | Level doc (3 m/s scale) | Variable |
|---|---|---|
| Walk speed | 2.4 m/s | `WalkSpeed` (240) |
| Sight | 70 degree cone, 6 m (busy 1.8 m) | `SightHalfAngle` (35), `SightRange`, `BusySightRange` |
| Knife reach | 0.9 m from the collision edge | `AttackReach` (90) |
| Windup | 0.6 s | `WindupTime` |
| Damage | 15 | `AttackDamage` |
| Shout | 7.2 m | `ShoutRadius` (720) |

Light and dark sight ranges, the awareness meter and noise hearing
belong to #8; the sight here is the first pass.

## States

`State` is a Name: `Unaware`, `Suspicious`, `Alerted`, `Dead`, or
`Dormant` (waits hidden for a script).

* **Unaware** has the substates in `UnawareMode`: `Idle`, `Patrol`
  (walks the `PatrolRoute` actors in a loop, waits `PatrolWait` at each
  point), `Busy` (short sight), `Sleeping` (never sees her). While
  unaware, `bUnaware` on the enemy's `BPC_Health` is true, which makes
  the peck a surprise peck (x3). Any other state clears it.
* **Suspicious**: she is in the sight cone. The enemy stops, turns to
  her and shows "?" over its head. After `SuspicionTime` (0.5 s) in sight
  it becomes alerted; if she is out of sight for 1 s it goes back to
  unaware.
* **Alerted**: chases (`SimpleMoveToActor` on the nav mesh) and attacks
  until it dies. It never searches or returns to patrol. Being hurt (and
  surviving) alerts it too.
* **Shout**: becoming alerted alerts every other enemy within
  `ShoutRadius`, who shout in turn.
* A bark from `Barks` shows over its head for 2 s when it becomes
  alerted. Bark text is a Text Render placeholder for the barks audio.

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

The knife, the glint and the body are placeholders (cylinder, cube,
point light). The windup sound is not added yet.

## Death

`BPC_Health.OnDied` calls `Die`: it stops, loses collision, flattens
like a pancake with "Well done!" over it and is destroyed after 4 s. It
stays defeated across checkpoint reloads (`bRemembersDefeat`).

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
