# HUD and debug panel

The in-game HUD (issue #6), corn eating and the developer debug panel. The
HUD design is in the [GDD](gdd.md#ui); health and healing are in
[combat.md](combat.md#health).

## Overview

| Part | Where | What it does |
|---|---|---|
| HUD actor | `/Game/UI/BP_AcrpgHUD` | `HUDClass` of `BP_AcrpgGameMode`; creates the widgets, eats corn, toggles the debug panel, draws the overlays |
| HUD widget | `/Game/UI/WBP_HUD` | Bottom-right cluster: HP bar and corn count |
| Debug panel | `/Game/UI/Debug/WBP_DebugHUD` | Story state, spawn and cheat buttons, overlay toggles |
| Story row | `/Game/UI/Debug/WBP_DebugStoryRow` | One story id: name, value, `<` and `>` |
| Inputs | `IA_EatCorn` (C, gamepad Y), `IA_DebugHUD` (F6) | Mapped in `IMC_Gameplay` |

All of it is Blueprint. `BP_AcrpgHUD` enables input for itself on
BeginPlay, so the two input actions work without touching `BP_Chicken`.

## HUD cluster

`WBP_HUD` polls on Tick: the chicken's `BPC_Health` (`Health /
MaxHealth`) and the story item `item_corn_cob`. It shows "Corn x N" and
the HP bar in the bottom-right corner and fades its render opacity
(interpolation speed 5, about half a second) between hidden and shown:

* Shown for 4 s after HP or the corn count changes: damage, healing,
  eating, picking up corn.
* Always shown below 25% HP.
* Shown while an enemy (`BP_EnemyBase`) within 15 m is alive and not
  unaware (`bUnaware` off on its `BPC_Health`).
* Hidden otherwise, and while there is no pawn with `BPC_Health`.

The first update after the widget is created does not count as a change,
so the cluster starts hidden. The shotgun part comes with #7.

## Eating corn

`IA_EatCorn` (Started) calls `BP_AcrpgHUD.EatCorn`: with at least one
`item_corn_cob`, HP below max, not dead and 1 s since the last bite, it
takes one cob and calls `Heal(35)` on the chicken. At full HP it does
nothing, so a cob is never wasted. There is no eating animation yet
(`A_Chicken_EatCorn` exists but is not played).

## Debug panel

F6 opens and closes the panel at the top left. The game keeps running;
the mouse cursor is shown while it is open and input goes to both the
game and the UI. Closing restores the previous cursor state.

* **Story list**: one row per id of `DT_StoryIds_Stop0`, with its current
  value, refreshed every frame. `<` and `>` step quests and flags with
  values through None and their values; bool flags toggle; stamps can
  only be added (the story system has no remove); items add or take one.
* **Spawn Shawarman**: spawns `BP_Shawarman` 3.5 m in front of the
  chicken, facing her. It is not dormant, so it attacks.
* **+1 corn**, **Full heal**, **God mode** (keeps `bInvulnerable` on the
  chicken while on), **Kill enemies** (10000 damage to every
  `BP_EnemyBase`), **Reset story** (`Story.Reset`).
* **View cones**: a yellow sector per enemy, `SightHalfAngle` to each
  side and `SightRange` long, near the ground.
* **Hit ranges**: a red ring of `AttackReach` under each enemy and a
  green ring of `PeckReach` plus 25 cm (her capsule) under the chicken.

The overlays use debug lines, so they exist only in development builds;
the panel itself is not stripped from shipping builds yet (#26).

## Not done yet (#6)

Throwables and the carry system, corn pickups on the ground (walk over to
pick up, carry up to 5), item data assets, the backpack panel, and
eating from the backpack.
