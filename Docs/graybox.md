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
  `MI_GrayboxRoof` (the whole mesh fades out). A roof right above the
  player is hidden, even when the camera looks under its edge, so the
  whole room or stall shows from inside: the chicken's `CameraOcclusion`
  traces up (`RoofCheckHeight`) and hides every part of the hit actor
  over the hit primitive that stays `RoofMinHeight` (1 m) above her,
  such as a roof, an art tarp or the signs on a stall. Hidden parts keep
  their shadow. So give a roof its own component (or actor), apart from
  the walls, as the guard office and the open container have.
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
