# Graybox conventions

How levels are blocked out before art: placeholder geometry and markers
that later systems replace. Stop-specific notes are in each level
document (stop 0: [level0-border-town.md](level0-border-town.md#graybox)).

## Geometry

* Props are StaticMeshActors built from basic shape components (cube,
  cylinder, cone, sphere). One actor per prop, named after it (stall,
  car, container, fence side).
* Materials are the `MI_GB_*` instances in `/Game/Materials/Graybox`.
  Walls and props use children of `M_Graybox` (screen-space cutout when
  they hide the player); roofs and awnings use children of
  `MI_GrayboxRoof` (the whole mesh fades out).
* Ground: a collision slab with its top at Z = 0, plus colored surface
  patches (road, paving, dirt) 1 cm above it with no collision.
* Level bounds and fence collision are invisible components with
  collision (`Block*` components, `Bounds_Invisible` actors). Fences
  are posts and rails for the look, so the camera sees through them.
* Text signs are Text Render components: flat ones face up, with their
  top toward the default camera direction; wall signs face outward.

## Markers

Placeholders for things that systems will spawn or drive: NPCs,
enemies, pickups. Markers have no collision and cast no shadows; each
has a label with its name.

* Label: `MK_<Kind>_<Name>`, for example `MK_NPC_Kolya`.
* Tags: `Marker`, `Marker.<Kind>`, `<Name>`, plus role tags (for
  example `Shawarman`, `Busy`, `PatrolA`, `CornCob`).
* The small box on NPC and enemy markers and the notch on patrol
  points show the facing.
* NPC, Interact and Pickup markers become playable by adding a
  `BPC_Interactable` component (see
  [story-system.md](story-system.md#interaction)). It brings its own
  overlap sphere, so the marker keeps no collision.

| Kind | Color | Shape | Meaning |
|---|---|---|---|
| NPC | yellow | cylinder | Character with dialog, or background extra |
| Enemy | red | cylinder | Enemy start, spawn point or climb point |
| Patrol | purple | flat disc | Patrol route point, numbered in order |
| Pickup | green | cube | Item or crate she can pick up |
| Throwable | orange | sphere | Throwable source (gnome, crate) |
| Checkpoint | blue | ring and pole | Checkpoint save spot |
| Interact | cyan | diamond on a pole | Object she can use |
| Lit | pale yellow | flat disc | Lit zone, the disc radius is the zone |

## Phases

When a map holds more than one level phase (stop 0: day and night),
each phase has a Runtime data layer, and its actors sit in an outliner
folder of the same name (`Day/`, `Night/`). Geometry that exists in
every phase is always loaded and sits in `Shared/`.
