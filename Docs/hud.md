# HUD, items, backpack and debug panel

The in-game HUD (issue #6), items and corn pickups, corn eating, the
backpack and the developer debug panel. The design is in the GDD
([UI](gdd.md#ui), [Items](gdd.md#items-loot-and-inventory),
[Backpack](gdd.md#backpack)); health and healing are in
[combat.md](combat.md#health), throwables in
[combat.md](combat.md#throwables).

## Overview

| Part | Where | What it does |
|---|---|---|
| HUD actor | `/Game/UI/BP_AcrpgHUD` | `HUDClass` of `BP_AcrpgGameMode`; creates the widgets, eats corn, toggles the debug panel, draws the overlays |
| HUD widget | `/Game/UI/WBP_HUD` | Bottom-right cluster: HP bar and corn count |
| Debug panel | `/Game/UI/Debug/WBP_DebugHUD` | Story state, spawn and cheat buttons, overlay toggles |
| Story row | `/Game/UI/Debug/WBP_DebugStoryRow` | One story id: name, value, `<` and `>` |
| Backpack | `/Game/UI/Backpack/WBP_Backpack`, `WBP_BackpackItem` | The panel and one item row |
| Item definitions | `/Game/Items/DA_Item_*` (`UItemDefinition`, C++) | Name, picture, description, section of a story item |
| Corn pickup | `/Game/Items/BP_CornPickup` | A cob on the ground, picked up by walking over it |
| Inputs | `IA_EatCorn` (C, gamepad Y), `IA_Backpack` (I, Tab, gamepad View), `IA_DebugHUD` (F6) | Mapped in `IMC_Gameplay` |

All of it is Blueprint except the item definition class.
`BP_AcrpgHUD` enables input for itself on BeginPlay, so its input actions
work without touching `BP_Chicken`.

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
nothing, so a cob is never wasted. She plays `A_Chicken_EatCorn` at 2.2x
(about 1 s) in the `UpperBody` slot of `ABP_Chicken`, so she can keep
running while she eats. The backpack's Eat button calls the same
function.

`UpperBody` is a second `Slot` node blended over the spine and up
(`Layered blend per bone` from `Spine02`, weight = the slot's montage
weight). One-shot clips that should leave the legs alone go there;
`DefaultSlot` is the full body.

## Items

The story state only counts items by id (`item_corn_cob`). What the
backpack needs to show them is an item definition, a data asset of the
C++ class `UItemDefinition` (`Source/acrpg/Story/ItemDefinition.h`), one
per item in `/Game/Items` named `DA_Item_<Name>`:

| Field | Meaning |
|---|---|
| `Id` | The story item id |
| `DisplayName`, `Description` | Shown in the backpack; the description is the joke |
| `Picture` | Square texture, `/Game/Items/Textures/T_Item_<Name>` |
| `Section` | `Gear`, `KeyItem` or `Joke`: the backpack section |
| `SortOrder` | Fixed place in the section, lower first |
| `MaxCount` | Most she can carry, 0 for no limit |

`MaxCount` is enforced by the story state: `AddItem` never raises a
count past it, so a gift past the limit is lost (corn: 5). Blueprints get
the list with `Get All Items` (sorted by section and order) and one
definition with `Find Item`. The asset manager cooks everything in
`/Game/Items` (`DefaultGame.ini`), so the list also works in packaged
builds. To add an item: add its id to the story id table, then create a
`DA_Item_` asset (Miscellaneous > Data Asset > Item Definition) in
`/Game/Items`.

The stop 0 items: corn cob (Gear), checklist, transit card, car keys,
Zbyszek's box, forged stamp (Key items) and the Gnomonaut (Joke items).
The pictures are flat icons drawn as SVG in `Art/Items/Source` and
rendered by `Art/Items/Scripts/make_icons.js`; `ue_items_import.py`
imports them and sets them on the definitions.

## Corn pickups

`BP_CornPickup` is a spinning cob (`SM_CornCob`) with a 45 cm trigger.
While she stands in it and has fewer than its `Item`'s `MaxCount`, she
takes `Count` (1) of `Item` (`DA_Item_CornCob`) and the cob disappears;
with full pockets it stays on the ground until she has room. A picked
cob is remembered by the checkpoint subsystem like a defeated enemy, so
a reload does not bring it back.

Placed in `L0_BorderBazaar` at the corn pickup markers: two in 0A (the
alley crate and the gnome field crate, `Day/Pickups`) and four in 0B
(fence corner, containers, two in the arena, `Night/Pickups`). Corn from
NPCs (the corn lady, Kolya) comes from their dialogs.

## Backpack

I, Tab or the gamepad View button (`IA_Backpack`) open and close it
(`BP_AcrpgHUD.ToggleBackpack`). It only opens during gameplay (not in a
dialog or a menu) and not while she carries something, pecks, flutters
or reels from a hit.

* The game is not paused. She stops, ignores move input and kneels
  (`A_Chicken_Kneel` at 1.2x, paused once she is down); the panel slides
  in from the right. Closing plays the stand-up part of the clip.
* A peck, a flutter, a hit or her death closes it at once (checked every
  0.05 s while it is open), so opening it in a fight is a risk.
* Three fixed sections: Gear, Key items and Joke items. Each owned item
  is a row (`WBP_BackpackItem`) in its section, in the definition order;
  counted items show "2 / 5" or "x 2". Items she no longer has disappear;
  the rows are rebuilt when the number of owned items changes.
* Clicking, hovering or focusing a row (D-pad) selects it: the right side
  shows its picture, name and description. The corn cob has an Eat
  button there.
* The mouse cursor shows and input goes to both the game and the UI
  while it is open, as with the debug panel. Closing restores the
  cursor.

The panel is created the first time it opens (`Backpack` on the HUD).
The shotgun and shells rows come with #7.

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
