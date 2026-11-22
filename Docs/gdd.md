# Ambitious Chicken RPG - Game Design Document

Working title: **Ambitious Chicken RPG** (project name `acrpg`).

This document covers the game as a whole: concept, systems, controls,
art and tech direction. The main story, quests and per-level content
live in [story-and-levels.md](story-and-levels.md).

Status: early draft. Items marked **(proposal)** are suggestions that
are not decided yet. All undecided points are collected in
[Open questions](#open-questions).

## Overview

| | |
|---|---|
| Genre | Story-driven top-down action RPG |
| Inspirations | Diablo 2 (real-time combat), Fallout 2 (world map, dialogs) |
| Engine | Unreal Engine 5.8 |
| View | 3D, top-down / isometric camera, rotate and zoom |
| Play time | 60-120 minutes |
| Team | Solo developer |
| Language | English, with some Russian jokes |
| Platform | PC (keyboard + mouse and gamepad) |

## High concept

The Ambitious Chicken, a small hen who dreams of flying to the
"co-co-cosmos", escaped the Shawarmen, a cafe, Berlin and a fox lawyer
in game 1. Now she has a car, sunglasses and the farmer's old shotgun.
She drives from place to place looking for safety and a way to the
stars, and every refuge she finds wants to serve her for dinner.

The game is about story, comedy, dialog choices and short, punchy
fights - not about grinding, stats or loot.

## Relation to game 1

The sequel follows "Ambitions Chicken" (game 1), a short 2D DOS-style
platformer. Things carried over from its ending:

* The protagonist, her motto ("To co-co-cosmos I will fly - shawarma? Not
  this chick!") and catchphrases: "I'll be kudakh!" (her line as she
  drives off at the end of game 1) and "Now we talk, Shawarmen." (when
  she finds the shotgun).
* Her naive misreading of danger, as in the first line of game 1: "I
  bet the cooks really like me..."
* "Out of the frying pan, into the oven" (game 1, the Thanksgiving
  diner), now the first design pillar.
* The death screen: a food picture and a pun line (see
  [Death](#death)).
* The black Honda Civic and sunglasses (a lawyer's fee from R. Fuchs).
* The farmer's shotgun.
* R. Fuchs, attorney at law, who escaped and promised to appeal.
* The Shawarmen, still everywhere.
* The cosmos dream, still not reached.

## Design pillars

1. **Out of the frying pan, into the oven.** Every place that looks safe
   turns out to have chicken on the menu. Being the main course on a
   dinner table is the protagonist's core problem in every location.
2. **Story and comedy first.** Dialogs, choices and jokes are the main
   content. Systems exist to support the story, not the other way
   around.
3. **Short, punchy action.** Real-time fights that are fast, readable
   and funny (comic food deaths), with no grinding.
4. **Small and handcrafted.** A few dense, hand-built locations instead
   of large or generated worlds. Scope must fit a solo developer.

## Tone and humor

* Absurd, warm, food-pun comedy, same as game 1.
* Food puns in names, signs, dialogs and death screens.
* Some Russian jokes (like "kudakh" = "cluck"); they should still be
  funny or at least readable for English-only players.
* The protagonist is brave, stubborn and a bit naive: she often misreads
  danger as an invitation, and the player sees the trap before she does.

## The protagonist

* Name: to be decided (still "the Ambitious Chicken" for now).
* Solo protagonist, no companions or party.
* No stats, levels or character build. Her whole arsenal is her beak,
  the farmer's shotgun and whatever she can throw. Progress comes from
  the story, not from power growth.

## Core loop

1. Pick a location on the map and drive there.
2. Explore the location hub, talk to characters, find out what is
   wrong (usually: they want to eat her).
3. Take quests, make dialog choices, fight enemies, collect items.
4. Progress the story; new locations appear on the map.
5. Checkpoint is saved; drive to the next location.

## Camera

* 3D world viewed from above at an isometric-style angle.
* The player can rotate the camera around the protagonist and zoom in and
  out within limits.
* Walls, roofs and other objects between the camera and the protagonist
  must fade or cut away so she is always visible.
* (proposal) Rotation in fixed steps (for example 45 degrees) or free
  rotation - to be tested.

## Controls

WASD movement with mouse aim, plus full gamepad support (twin-stick
style). The bindings below are a first draft.

| Action | Keyboard + mouse | Gamepad |
|---|---|---|
| Move | WASD | Left stick |
| Aim | Mouse cursor | Right stick |
| Fire / throw | Left mouse button | Right trigger |
| Peck (melee) | Right mouse button | Left trigger |
| Flutter (dodge) | Space | B / Circle |
| Interact / talk / pick up | F | A / Cross |
| Reload | R | X / Square |
| Eat corn (heal) | C | Y / Triangle |
| Rotate camera | Q / E or middle mouse drag | Bumpers |
| Zoom | Mouse wheel | D-pad up / down |
| Backpack (inventory) | I or Tab | View / Select |
| Map / journal | M / J | Menu sub-pages |
| Pause / menu | Esc | Menu / Start |

Notes:

* Movement is relative to the camera, so rotating the camera does not
  flip the controls.
* With a gamepad, aim follows the right stick; when the right stick is
  released, the protagonist faces her movement direction. (proposal) Light
  aim assist toward the nearest enemy in the aim direction.
* UE implementation: Enhanced Input with separate mapping contexts for
  gameplay, dialog and menus.

## Combat

Real-time, Diablo 2 style, but with direct WASD + aim control. The
protagonist's tools are her beak, a dodge, things she can throw and the
shotgun. All numbers below are starting values for tuning;
the first stop ([stop 0](level0-border-town.md)) is the test
bed for all of them.

### Health and healing

* The protagonist has 100 HP and no regeneration.
* Healing is corn: a corn cob heals 35 HP instantly. She carries up to
  5 and eats one with a button (1 s cooldown). Corn was the score item
  of game 1; here it is only healing.
* Corn comes from NPCs, crates and level placement, so the healing
  budget of every level is designed by hand.

### Peck

* Always available melee: a short frontal arc (1.5 m, 90 degrees),
  10 damage, one peck per 0.4 s, small knockback.
* **Surprise peck:** the first hit on an enemy that hasn't noticed her
  does triple damage. That kills a basic Shawarman in one peck and is
  the reward for sneaking.
* Before she has the shotgun, Fire also pecks.

### Flutter

* The dodge: a short flapping hop, the closest she gets to flying.
* 4 m in 0.25 s in the movement direction (aim direction when standing
  still). Invulnerable during the hop. 0.8 s cooldown.
* It does not cross gaps or obstacles. It drops a carried object.

### Throwables

* Some world objects can be picked up with Interact and thrown with
  Fire. Garden gnomes in stop 0; later stops can reuse the system
  (paper stacks, logs, cabbages).
* One at a time, carried above her head: 30% slower movement, no peck
  while carrying.
* Thrown in an arc toward the aim point, up to 10 m. 25 damage, knocks
  the target down for 1.5 s, the object shatters.

### Shotgun

The farmer's pump-action shotgun from game 1, and the only weapon in
the game. She gets it back from the Civic's trunk in stop 0 and keeps
it to the end. There are no other weapons and no upgrades; variety
comes from enemies, throwables and level design.

* Holds 8 shells. One shot fires 8 pellets of 6 damage in a cone. Full
  damage up to 4 m, half at 8 m, nothing past 12 m. A pump between
  shots: 0.7 s per shot.
* Reload only on a button press (R / X), never automatic. The reload
  rule from game 1 stays: she reloads only while standing still, one
  shell per 0.5 s, until the tube is full. Moving, firing, pecking or
  fluttering interrupts the reload but keeps the shells already loaded.
* Ammo is limited (32 shells in reserve max) and placed by hand: crates
  and some enemy drops. The peck is always the fallback.
* **The Civic's trunk** is a refill that never runs out, so the player
  can never get stuck without ammo. Every level where she has the car
  has it parked in a fixed, reachable spot (usually the level entry).
  Interacting with the trunk refills the reserve to 32. It takes 1.5 s
  standing still, and taking damage interrupts it, so using it in a
  fight is a risk. When the reserve is empty, a hint reminds her of it
  ("The trunk has more").
* A shot is loud (see noise below).

### Enemies

The Shawarman is the common recurring enemy; each stop adds enemies
themed around who wants to eat her there. Shared rules for all of them:

* No stats or levels. A stronger enemy is a separate enemy type.
* **States:** unaware (idle, patrol, busy, sleeping), suspicious and
  alerted. In the first pass an alerted enemy fights until it dies; no
  searching or returning to patrol.
* **Sight:** a 70 degree cone in front of the enemy. Range 10 m when
  the protagonist is lit, 5 m when she is in the dark (dark exists only in
  night levels).
* **Busy** enemies (eating, working) see only 3 m, still only in their
  front cone, so she can sneak up from behind or the side and peck.
  **Sleeping** enemies react only to noise.
* **Spotting is not instant.** While she is in sight, the enemy's
  awareness fills up; a meter above its head goes from "?" to "!".
  Full awareness takes 1.5 s at the edge of sight range and 0.5 s
  close up, and the enemy turns toward her and becomes suspicious
  while it fills. When it is full, the enemy is alerted. Out of sight,
  awareness drains at the same speed, so the player has time to back
  off after a mistake. Suspicious enemies stop and look but don't
  move toward her in the first pass.
* **Noise** alerts every enemy in range at once: peck hit 6 m,
  shattered throwable 10 m, shotgun 25 m.
* **Shout:** an enemy that becomes alerted alerts others within 12 m.
* **Telegraphs:** every attack has a readable windup (pose, glint,
  sound), at least 0.5 s for melee. Ranged projectiles are slow enough
  to dodge.
* Enemies have comic food deaths too. Defeated enemies stay defeated;
  reloading a checkpoint restores the state saved in it.

### Lights and sneaking

Not a stealth system, just the detection rules above used in dark
places. Lit areas are marked in the level (lamp light volumes, moving
light cones like flashlights and searchlights). Being spotted is never
a fail; it only starts a fight, and awareness gives time to retreat
before that.

### Death

A comic food death screen: a full screen food picture and a pun line,
then reload the last checkpoint.

* In game 1 every death showed a random picture and a random line from
  one pool. Here every damage source carries a "killed by" tag that
  picks the picture (wrap, kebab, grill, doner, etc.) and a small pool
  of lines for that killer. Each level document lists them.
* The generic lines from game 1 are mixed into every killer's pool:
  * "Well done. Too well done."
  * "Back on the menu."
  * "Ambitions: 0. Kebab: 1."
  * "That's not the cosmos..."
  * "Table for one. You're the special."
* Game 1 lines tied to food that fits a specific killer go to that
  killer: "One chicken wrap, to go.", "You ARE the doner.", "Extra
  garlic sauce, hold the cosmos.", "Rotating slowly on the spit of
  fate." (all used in stop 0).
* Game 1 lines tied to its own enemies wait for a stop where they fit:
  "Today's special: chicken nuggets.", "Delivered in under ten
  minutes. Five stars!", "Served with cranberry sauce."

## Items, loot and inventory

Loot and inventory exist but are secondary to story and action.

* No random stats, affixes or rarity tiers. Every item is handcrafted
  and has a clear purpose.
* Item types: the shotgun, shells, corn cobs, key and quest items, and
  joke items with funny descriptions (for example the Gnomonaut).
* Throwables are world objects, not inventory items.
* Items come from quests, dialogs, containers and some enemies.
  Picking up is automatic on walking over ammo and corn; key items are
  picked up with Interact.
* No currency and no shops. Trades are barter, favours and dialog
  choices. She is officially cargo, and cargo has no wallet.
* The checklist is a special key item: one stamp slot per stop, shown
  as a document page in the backpack.

### Backpack

Very simple and direct, in the style of The Last of Us: no grid, no
slots to manage, no weight, no sorting, no dropping, no crafting.

* Opening the backpack does not pause the game. The protagonist kneels and
  the panel slides in; the world keeps running, so opening it in a
  fight is a risk.
* One panel with three fixed sections:
  * **Gear:** the shotgun (loaded / reserve shells) and corn cobs
    (count of max 5). Corn can be eaten from here.
  * **Key items:** the checklist, the transit card, keys, quest items.
    Selecting one shows a picture and a funny description.
  * **Joke items:** collectibles like the Gnomonaut, with descriptions.
* Every item has a fixed place in its section, so the panel never needs
  managing. Items that are used up or handed over simply disappear.

## Dialogs

* Branching dialogs with player choices.
* Choices can change quest outcomes, how characters react later and
  which ending the player gets.
* Dialogs need to read and set story state: quest progress, flags
  ("lied to the chef"), items in inventory.
* Optional funny lines and dead-end jokes are encouraged; they cost
  little and carry the comedy.
* The tool and data format for writing dialogs is an important early
  tech decision (see open questions), because dialogs are most of the
  game's content.

## Quests and endings

* Main quest line that drives the story between locations.
* (proposal) A few side quests per hub location, each with a joke
  payoff.
* A few distinct endings, decided by choices made during the game.
* A simple journal shows active and finished quests.
* The actual story, quests and endings are in `story-and-levels.md`.

## World and travel

* The world is a set of separate locations (stops on the map). Each
  location has several hand-built levels, usually a hub with
  characters and quests plus a second area with the main fight. The
  player can walk freely between the levels of one location.
* Travel happens on a map screen: the story reveals new locations on
  the map, and the player picks where to drive.
* Exception: stop 0 (the prologue) is linear. Its night level can't be
  left back to the day level.
* The car is only a way to travel between levels: no fuel, upgrades,
  driving gameplay or car combat.
* (proposal) A short driving cutscene or animation between map and
  level, to show off the Civic and sunglasses.

## Saving

* Checkpoint saves only, no save-anywhere.
* Checkpoints on arrival at a level, at key story moments and before
  big fights. Each level document lists its checkpoints.
* A save stores: current location and checkpoint, the level phase
  when a map holds more than one (stop 0: day or night), story and
  quest state, dialog flags, inventory, HP, unlocked map locations.

## Art direction

* Stylized low-poly 3D.
* Bright, warm, readable colors that support the comedy; danger (knives,
  skewers, ovens) should still read clearly from the top-down view.
* Characters need strong silhouettes from above, since the camera is
  high and can rotate.
* Food is everywhere: signs, menus, props, death screens.
* Asset pipeline: Blender for modeling, export to UE.

## UI

* HUD, minimal and contextual like The Last of Us:
  * One cluster in the bottom-right corner: the HP bar, the shotgun
    icon with loaded shells (as shell pips) and reserve count, and the
    corn count.
  * The cluster hides during exploration and fades in when she takes
    damage, heals, picks up ammo or corn, draws or fires the shotgun,
    reloads, or an enemy becomes suspicious or alerted. HP below 25%
    keeps it visible.
  * Before she has the shotgun, only the HP bar and corn are shown.
  * Enemy awareness meters ("?" to "!") above enemy heads.
  * Interaction prompts next to the object, and one-time tutorial
    hints with gamepad or keyboard glyphs (whichever was used last).
  * No minimap, no quest markers on screen.
* Dialog window with speaker name, portrait (proposal) and choices.
* Backpack panel (see [Backpack](#backpack)).
* Map screen for choosing locations.
* Journal with quests.
* Death screen with food picture and pun line.
* Pause menu and settings (controls, audio, video).
* All UI must work with both mouse and gamepad.

## Non-goals

These are deliberately out of scope:

* Character stats, levels, experience or skill trees.
* Weapons other than the shotgun, and weapon upgrades.
* Crafting.
* Random loot, item affixes, loot grinding.
* Companions or party members.
* Car mechanics (fuel, upgrades, driving, car combat).
* Random or generated dungeons.
* Disguise system (may return only if the story needs it).
* A full stealth system (search behaviour, hiding spots, light
  meters). Only the simple detection rules from Combat.
* Multiplayer.

## Technical notes

* Unreal Engine 5.8, C++ with Blueprints where convenient.
* Start from the Top Down template ideas (camera boom, Enhanced
  Input), but with WASD + aim instead of click-to-move.
* (proposal) No Gameplay Ability System: without stats it is likely
  overkill. A health component, a weapon component and data-driven
  dialog and quest assets should be enough.
* Several levels per location, plus a separate map screen (level or
  UI). Levels that share ground share one World Partition map, with a
  data layer per level phase (stop 0: day and night); levels apart from
  each other are separate maps.
* Levels are blocked out first with placeholder geometry and markers,
  see [graybox.md](graybox.md).
* Images and assets in the repo go through Git LFS (already set up).
* (proposal) Main building blocks: a health component shared by the
  protagonist and enemies (with the "killed by" tag), a weapon component
  (peck, shotgun), an interactable component (talk, pick up, use), a
  throwable actor, a story state subsystem (quests, flags, stamps) used
  by dialogs, quests and saves, and lit zone volumes plus light cones
  for enemy sight.

## First playable

Stop 0 is the first playable, because it needs every core system. The
work is tracked as GitHub issues in the
[First playable](https://github.com/stamerlan/ai-acrpg/milestone/1)
milestone.

## Open questions

Story and world (first draft in `story-and-levels.md`: a road story
from Berlin across Poland to Gdansk, heading for Kudakhstan; the cosmos
is never reached; R. Fuchs does not return):

* The protagonist's name.
* Is the Lavash Baron a second villain besides bureaucracy?
* How many endings, and which choices unlock them.

Gameplay:

* Tuning of all combat numbers (first pass in stop 0).
* Final control bindings and camera rotation style (steps or free).

Tech:

* Dialog tool: data tables, a custom dialog graph asset, or a
  third-party plugin.
* Quest and story state format, shared by dialogs, quests and saves.
* Map screen: a separate level or a UI widget.

Other:

* Audio and music direction.
* Voice acting: none, gibberish clucking, or full voice.
* Platforms besides PC (Steam Deck, consoles)?
* Russian jokes: how to keep them readable for English-only players.
