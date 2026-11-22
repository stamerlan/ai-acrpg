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
  this chick!") and catchphrases ("I'll be kudakh!").
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
* No stats, levels or character build. She gets stronger only through
  items she finds (weapons, consumables) and story progress.

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
| Attack / fire | Left mouse button | Right trigger |
| Interact / talk | F | A / Cross |
| Reload (if used) | R | X / Square |
| Rotate camera | Q / E or middle mouse drag | Bumpers or D-pad |
| Zoom | Mouse wheel | D-pad up / down |
| Inventory | I or Tab | View / Select |
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

* Real-time, Diablo 2 style, but with direct WASD + aim control.
* The protagonist has HP. Enemies have HP.
* Healing: (proposal) food the protagonist can eat safely, like corn
  (collected for points in game 1). Food that is healing for a chicken
  but awkward to explain is joke material.
* Enemies: the Shawarman is the common recurring enemy; each location
  adds its own enemies themed around who wants to eat her there.
* Weapons: to be decided. The shotgun from game 1 is the natural
  starting weapon.
* Death: a comic food death screen that depends on who or what killed
  her (kebab, nuggets, roast, etc.) with a pun line, like game 1
  ("Well done. Too well done."). Then reload the last checkpoint.

## Items, loot and inventory

Loot and inventory exist but are secondary to story and action.

* No random stats, affixes or rarity tiers. Every item is handcrafted
  and has a clear purpose.
* Item types: weapons, ammo, consumables (healing), quest and key
  items, and possibly joke items with funny descriptions.
* Items come from quests, dialogs, containers and some enemies.
* (proposal) A simple list or small grid inventory, no weight or
  tetris-style packing.

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
* The car is only a way to travel between levels: no fuel, upgrades,
  driving gameplay or car combat.
* (proposal) A short driving cutscene or animation between map and
  level, to show off the Civic and sunglasses.

## Saving

* Checkpoint saves only, no save-anywhere.
* (proposal) Checkpoints on arrival at a location, at key story moments
  and before big fights.
* A save stores: current location and checkpoint, story and quest
  state, dialog flags, inventory, HP, unlocked map locations.

## Art direction

* Stylized low-poly 3D.
* Bright, warm, readable colors that support the comedy; danger (knives,
  skewers, ovens) should still read clearly from the top-down view.
* Characters need strong silhouettes from above, since the camera is
  high and can rotate.
* Food is everywhere: signs, menus, props, death screens.
* Asset pipeline: Blender for modeling, export to UE.

## UI

* HUD: HP, current weapon and ammo, interaction prompts.
* Dialog window with speaker name, portrait (proposal) and choices.
* Inventory screen.
* Map screen for choosing locations.
* Journal with quests.
* Death screen with food picture and pun line.
* Pause menu and settings (controls, audio, video).
* All UI must work with both mouse and gamepad.

## Non-goals

These are deliberately out of scope:

* Character stats, levels, experience or skill trees.
* Random loot, item affixes, loot grinding.
* Companions or party members.
* Car mechanics (fuel, upgrades, driving, car combat).
* Random or generated dungeons.
* Disguise system (may return only if the story needs it).
* Multiplayer.

## Technical notes

* Unreal Engine 5.8, C++ with Blueprints where convenient.
* Start from the Top Down template ideas (camera boom, Enhanced
  Input), but with WASD + aim instead of click-to-move.
* (proposal) No Gameplay Ability System: without stats it is likely
  overkill. A health component, a weapon component and data-driven
  dialog and quest assets should be enough.
* Several levels per location, plus a separate map screen (level or
  UI).
* Images and assets in the repo go through Git LFS (already set up).

## Open questions

Story and world (first draft in `story-and-levels.md`: a road story
from Berlin across Poland to Gdansk, heading for Kudakhstan; the cosmos
is never reached; R. Fuchs does not return):

* The protagonist's name.
* Is the Lavash Baron a second villain besides bureaucracy?
* How many endings, and which choices unlock them.

Gameplay:

* Weapons: which ones, and is the shotgun the starting weapon?
* Does the reload-only-while-standing-still rule from game 1 stay?
* Dodge, dash or block action - yes or no?
* Is there melee (pecking, wings) besides weapons?
* How does healing work?
* Is there currency or shops? (Corn as money?)
* Points / score from game 1 (corn) - keep, change or drop?
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
