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
  `MI_GrayboxRoof` (the whole mesh fades out). A roof that covers the
  player is hidden whole instead, so the whole room or stall shows. The
  chicken's `CameraOcclusion` takes every primitive between the camera
  and her, plus every one right above her (`RoofCheckHeight`, for when
  the camera looks under a roof edge). Of each, it hides every part of
  the same actor over it that stays `RoofMinHeight` (1 m) above her,
  such as a roof, an art tarp, the signs on a stall or the wall strip
  over a door. Walls and posts reach the ground, so they only get the
  cutout. Hidden parts keep their shadow. So give a roof its own
  component (or actor), apart from the walls, as the guard office and
  the open container have; a market stall's canopy is its own mesh and
  actor for this (`SM_Stall_<Trade>_Top`). An actor tagged `HideWhole`
  is hidden whole, every visible part, as soon as any of its primitives
  is hit: the roofs of the shops she walks into (`ArtBld_<Shop>_Roof`,
  with a camera-only box over the room, see
  [level0-border-town.md](level0-border-town.md#layout)).
* Never cut: actors tagged `NoOcclusionCutout` (her Civic and its
  trunk lid, the lot's lamp posts) and art placed without camera
  collision (the shop shells, the booth and the veterinary office, the
  road lamps). Behind those she shows as a
  silhouette: her mesh renders custom depth and `M_PP_Silhouette` on
  the unbound volume `PP_Silhouette` tints the pixels where she is
  behind the scene a saturated orange with a dark 3 px outline (custom
  depth sampled at 8 offsets), so she stands out on clutter, trees and
  yellow tents
  (`Art/Environment/Scripts/ue_silhouette.py`).
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
| Throwable | orange | sphere | Throwable source (gnome, crate); hidden in game where real gnomes stand |
| Checkpoint | blue | ring and pole | Checkpoint save spot |
| Interact | cyan | diamond on a pole | Object she can use |
| Lit | pale yellow | flat disc | Lit zone, the disc radius is the zone |

## Phases

When a map holds more than one level phase (stop 0: day and night),
each phase has a Runtime data layer, and its actors sit in an outliner
folder of the same name (`Day/`, `Night/`). Geometry that exists in
every phase is always loaded and sits in `Shared/`.

## Art over the graybox

Art replaces the look of the graybox, not its collision. An art pass
hides a graybox mesh (`Visible` and `Hidden in Game` off) and keeps it as
the blocking collision, then places the art mesh over it in an `Art/`
outliner folder that mirrors the graybox folder (`Art/Shared/Lot/...`).
So the layout, the navigation and the camera stay the same as the
graybox that was playtested.

* Art meshes block only the `Camera` channel (query only, every other
  channel ignored, no navigation), so the camera occlusion still finds
  them and they never change the walkable space. Small props have no
  collision at all.
* Art materials are instances of `M_Env` (`Content/Environment/
  Materials`), which keeps the occlusion cutout of `M_Graybox`. A mesh
  with another material does not fade when it hides the player.
* Ground is a thin cube per zone with an `MI_Ground_*` instance of
  `M_Ground`: world-aligned photo texture (`TileSize` cm), pulled toward
  a flat color (`Flat`, `Detail`) so it sits under flat-shaded props.
* Repeated meshes (trees, wall panels, container stacks) go into one
  holder actor per zone with an instanced static mesh component per
  mesh.
* The art is placed by scripts (`Art/Environment/Scripts/ue_dress_*.py`,
  see [Art/README.md](../Art/README.md#environment-environment)). Hand
  edits are lost when a script runs again: change the script instead.
* Labels, markers and trigger volumes stay visible as before.
