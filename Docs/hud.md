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
| HUD widget | `/Game/UI/WBP_HUD` | Bottom-center block: shotgun row, HP bar and corn slots |
| Debug panel | `/Game/UI/Debug/WBP_DebugHUD` | Story state, spawn and cheat buttons, overlay toggles |
| Story row | `/Game/UI/Debug/WBP_DebugStoryRow` | One story id: name, value, `<` and `>` |
| Backpack | `/Game/UI/Backpack/WBP_Backpack`, `WBP_BackpackItem` | The panel and one item row |
| Item definitions | `/Game/Items/DA_Item_*` (`UItemDefinition`, C++) | Name, picture, description, section of a story item |
| Corn pickup | `/Game/Items/BP_CornPickup` | A cob on the ground, picked up by walking over it; `BP_ShellPickup` is its shell crate child |
| Inputs | `IA_EatCorn` (C, gamepad Y), `IA_Backpack` (I, Tab, gamepad View), `IA_DebugHUD` (F6) | Mapped in `IMC_Gameplay` |

All of it is Blueprint except the item definition class.
`BP_AcrpgHUD` enables input for itself on BeginPlay, so its input actions
work without touching `BP_Chicken`.

## HUD cluster

`WBP_HUD` is one block at the bottom center of the screen (`Plate`, a
dark rounded plate 28 px above the bottom edge), close to the hen in the
middle of the screen. It is always visible while there is a pawn with
`BPC_Health` (hidden otherwise), so the shell count can always be read.
The layout follows a design review by Fable (issue #7).

* **Row 1, the gun** (`GunRow`, only once she has the shotgun): the
  shotgun tile (`GunTile`: `T_Item_Shotgun` at 56 px with an amber
  frame `GunFrame` over it), eight shell slots (`Pips`, 24x48 px, 4 px
  apart) and the reserve as "+N" (26 px bold, outlined). A loaded slot
  shows `T_HUD_Shell`; an empty one shows `T_HUD_ShellEmpty` (the same
  shape as a white silhouette) tinted gray at 45 %, so the eight slots
  always read as "this many of eight".
* **Row 2:** the HP bar (200x20, green, red below 25 %) and five corn
  slots (`CornRow`, `T_HUD_Corn` / `T_HUD_CornEmpty` at 26x39), one per
  cob she can carry (`MaxCount` 5).
* **Next shot not ready:** `UpdateGun` reads `BPC_Shotgun`. During the
  pump (`NextShotTime` in the future) the frame is solid amber and the
  next shell to fire (the rightmost loaded one) is darkened and
  brightens back up as the pump ends. During a reload the frame pulses
  (2 Hz) and the slot being loaded blinks amber.

`UpdateGun` runs first on every Tick, then the corn slots and the HP bar.
The ammo itself is described in [combat.md](combat.md#shotgun). The
pictures are made by Nano Banana and keyed by
`Art/UI/Scripts/key_icons.ps1` (see
[Art/README.md](../Art/README.md#hud-pictures-ui)).

## Eating corn

`IA_EatCorn` (Started) calls `BP_AcrpgHUD.EatCorn`: with at least one
`item_corn_cob`, HP below max, not dead and 1 s since the last bite, it
takes one cob and calls `Heal(35)` on the chicken. At full HP it does
nothing, so a cob is never wasted. She plays `A_Chicken_EatCorn`
(1.17 s, three pecks at a cob held across her chest) in the `UpperBody`
slot of `ABP_Chicken`, so she can keep running while she eats. The cob
is `HeldCorn` on `BP_Chicken` (`SM_CornCob`, hidden): `EatCorn` attaches
it to the `Hips` bone, where it sits between her wing tips in that clip,
and shows it; `UpdateHeldCorn` (every 0.05 s) hides it once the clip
passes 1.0 s or stops. The backpack's Eat button calls the same
function, so she eats kneeling at the bag.

`UpperBody` is a second `Slot` node layered over the spine and up
(`Layered blend per bone` from `Spine02`, weight 1). Its source and
the base pose are the same cached pose (`BodyPose`, the output of
`DefaultSlot`), so with no montage on `UpperBody` the layer changes
nothing. Do not drive that weight with `GetSlotLocalWeight`: a layer
at weight 0 is not updated, so the slot weight never rises above 0 and
the clip never shows (that was the case until the eating fix). The
slot is in its own group, `UpperBodyGroup`, on `SK_Chicken_Skeleton`,
so its montages (eating, shotgun fire and reload) do not stop the
`DefaultSlot` ones (the kneel) and the other way round. The Anim Slot
Manager can't be scripted; `Acrpg.SetSlotGroup <skeleton> <slot>
<group>` (editor console) does it, save the skeleton after. One-shot
clips that should leave the legs alone go to `UpperBody`;
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

The stop 0 items: shotgun, shells, corn cob (Gear), checklist, transit
card, car keys, Zbyszek's box, forged stamp (Key items) and the
Gnomonaut (Joke items).
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
  (`A_Chicken_Kneel` at 1.2x; `HoldKneel` pauses that montage, and only
  that one, once she is down); the panel slides in from the right.
  Closing plays the stand-up part of the clip.
* Her facing is locked while it is open (`bFacingLocked` on
  `AChickenCharacter`): she neither turns to the mouse or right stick
  nor to her movement. Closing unlocks it and she turns to the aim
  again.
* The camera moves in while it is open (`SetCameraFocus` on
  `AChickenPlayerController`, values under Camera > Focus on
  `BP_ChickenPlayerController`): the boom eases from the player's zoom
  to `FocusArmLength` (850 cm, or the player's zoom if that is closer)
  over `FocusInTime` (0.45 s) and the camera shifts `FocusSideOffset`
  (250 cm) to the right, so she sits in the middle of the screen left of
  the panel. Closing eases back over `FocusOutTime` (0.4 s); a hit or
  death that closes it snaps back in `FocusSnapOutTime` (0.2 s), so the
  threat is in view. Motion blur is off while the camera moves in or
  out. Zoom input is ignored meanwhile and the player's
  own zoom comes back as it was.
* The bag: `BackpackProp` on `BP_Chicken` (`SM_BackpackOpen`, an open
  backpack with a cob sticking out, hidden). 0.5 s after opening
  `PutBagOut` places it on the ground 31 cm in front of her, under her
  beak and wings in the dig pose of the kneel clip, detaches it so it stays in the world, and
  `UpdateBag` pops it in (scale 0 to 1 in about 0.17 s with a small
  overshoot). `PutBagAway` shrinks it away 0.1 s after closing, 0.15 s
  after a hit or death closes it; the bag stays where it was meanwhile.
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
Gear lists the shotgun and the reserve shells ("12 / 32") before the
corn; the loaded shells (`item_shells_loaded`) have no definition and
show only on the HUD.

## Debug panel

F6 opens and closes the panel at the top left. The game keeps running;
the mouse cursor is shown while it is open and input goes to both the
game and the UI. Closing restores the previous cursor state.

* **Story list**: one row per id of `DT_StoryIds_Stop0`, with its current
  value, refreshed every frame. `<` and `>` step quests and flags with
  values through None and their values; bool flags toggle; stamps can
  only be added (the story system has no remove); items add or take one.
* **Spawn Shawarman**, **Spawn Skewerman**, **Spawn Grill Sergeant** (their
  own row): spawn `BP_Shawarman`, `BP_Skewerman` or `BP_GrillSergeant`
  3.5 m in front of the chicken, facing her. They are not dormant, so they
  attack; turn on God mode to watch their animations.
* **+1 corn**, **Full heal**, **God mode** (keeps `bInvulnerable` on the
  chicken while on), **Kill enemies** (10000 damage to every
  `BP_EnemyBase`), **Reset story** (`Story.Reset`).
* **View cones**: a yellow sector per enemy, `SightHalfAngle` to each
  side and `SightRange` long, near the ground.
* **Hit ranges**: a red ring of `AttackReach` under each enemy and a
  green ring of `PeckReach` plus 25 cm (her capsule) under the chicken.

The overlays use debug lines, so they exist only in development builds;
the panel itself is not stripped from shipping builds yet (#26).
