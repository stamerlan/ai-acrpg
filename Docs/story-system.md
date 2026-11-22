# Story system

Interaction, dialogs and story state: how they work and how to write
content for them. Design goals are in the [GDD](gdd.md#dialogs).

## Overview

| Part | Where | What it does |
|---|---|---|
| Data types | `Source/acrpg/Story/StoryTypes.h` | Conditions, actions, story ids, the saved state |
| Story state | `UStoryStateSubsystem` (C++) | Quests, flags, stamps, items; conditions and actions; console; the `Story` dialog participant |
| Dialogs | `DLG_*` assets, [DlgSystem](https://github.com/NotYetGames/DlgSystem) plugin | Dialog graphs, edited in the plugin's graph editor |
| Interactable | `BPC_Interactable` (BP on `UInteractableComponent`) | Talk, pick up or use; its sphere is the prompt range; the NPC dialog participant |
| Interactor | `BPC_Interactor` on `BP_Protagonist` | Finds the closest interactable, shows the prompt, Interact |
| Dialog runner | `BPC_DialogRunner` on `BP_ProtagonistController` | Plays a dialog, switches to the dialog input context |
| Widgets | `/Game/Story/UI` | `WBP_InteractPrompt`, `WBP_Dialog`, `WBP_DialogChoice` |

C++ holds only what Blueprints can't: the subsystem, the console
commands, the struct and enum types and the dialog participant
interface (Blueprints can't implement it through the editor tools).
Everything else is Blueprint.

DlgSystem (Not Yet, MIT license) is vendored in `Plugins/DlgSystem`,
unmodified upstream `master` at commit `d705231` (version 18.0.8). It
was picked over a home-made format for its graph editor: boxes and
lines for lines, choices, conditions and events. Its text export is
off (Project Settings > Dialogue System > Dialogue Text Format: None):
the `DLG_` assets are the only copy of a dialog.

## Story state

Every quest, flag, stamp and item has an id, defined in an id table
(`DT_StoryIds_Stop0`, listed in Project Settings > Game > Story). Using
an id or a value that isn't defined logs a warning.

The source of an id table is a JSON file next to the asset:
`Content/Story/Stop0/DT_StoryIds_Stop0.json`. Edit the JSON, then press
the reload button of the [id table tool](#id-table-tool). Write every field
of a row (`Kind`, `Values`, `Description`), the importer warns about
missing ones. Don't edit the table in the data table editor: the next
reload overwrites it.

* **Quest:** one current step, None when not started. The table lists
  the steps in order.
* **Flag:** a value from the table's list, or a bool (empty list, value
  `true`). None means not set.
* **Stamp:** a checklist stamp, set or not.
* **Item:** a count. Item definitions with pictures come with the
  backpack (#6); the story state only counts them.

Id prefixes: `q_` quest, `f_` flag, `stamp_` stamp, `item_` item.

Blueprints use the `Story State Subsystem` node: `Get/SetFlag`,
`Get/SetBoolFlag`, `Get/SetQuestStep`, `HasStamp`, `AddStamp`,
`GetItemCount`, `AddItem`, `CheckConditions`, `RunActions`,
`TriggerEvent`, and the events `OnStoryChanged` and `OnStoryEvent`.
Saves store `GetState()` (one `FStoryState` struct) and restore it with
`SetState()`.

## Conditions and actions

Interactables and story gates use these building blocks. Dialogs use
the DlgSystem conditions and events, see [Dialogs](#dialogs).

| Condition | Passes when |
|---|---|
| `FlagIs` / `FlagIsNot` | flag `Id` has / hasn't `Value` (None: not set) |
| `QuestIs` / `QuestIsNot` | quest `Id` is / isn't at step `Value` (None: not started) |
| `HasItem` / `LacksItem` | at least / less than `Count` of item `Id` |

| Action | Does |
|---|---|
| `SetFlag` | sets flag `Id` to `Value`, None clears it |
| `SetQuest` | sets quest `Id` to step `Value` |
| `AddStamp` | adds stamp `Id` |
| `GiveItem` / `TakeItem` | adds / removes `Count` of item `Id` |
| `Event` | broadcasts story event `Id` for level scripts |

## Dialogs

A dialog is a DlgSystem dialogue asset, one per NPC:
`/Game/Story/Stop0/Dialogs/DLG_Kotlet` and so on. Double-click it to
open the graph editor. A dialog has up to two participants:

* the NPC, named by its interactable's `ParticipantName` (`Kotlet`).
  Every node is owned by the NPC; the dialog window shows the
  interactable's `DisplayName` ("Sergeant Kotlet") as the speaker.
* `Story`, the story state. Conditions read it and events change it.
  A dialog that never reads or changes the story (the kantor) has no
  `Story` participant; the dialog runner passes the story state only
  to dialogs that use it.

How a dialog plays:

* A **speech node** is a line of the NPC. Its edges are the
  protagonist's choices: the edge text is what she says. Only choices
  whose conditions pass are shown. A single edge with no text means
  "continue": Advance follows it.
* A **selector node** (type First) isn't shown: it goes to its first
  edge whose conditions pass. Selectors pick a greeting or a reply by
  state, for example the start of Kotlet's dialog.
* An **end node** ends the dialog. A **proxy node** jumps to another
  node, it keeps the graph readable when many choices lead to one line.
* **Enter events** of a node run when the dialog enters it.
* The start node's edges pick where the dialog begins. An NPC with
  more than one way in has an `entry_<name>` condition on those edges,
  see [Entries](#entries).

The graph editor orders the edges of a node by the X position of the
edge boxes, left to right, so choices show in the order they are laid
out. For the same reason the edges of a selector must exclude each
other (add the negated conditions of the edges before), otherwise
moving a box changes which one wins.

### Story participant

`Story` answers DlgSystem conditions and events like this:

| In the graph | Reads or changes |
|---|---|
| Bool call condition | bool flag or stamp: set (Bool Value on) or not set (off) |
| Name call condition | quest step or flag value. DlgSystem ignores the operation here: Bool Value on means equal, off means not equal |
| Int call condition | item count, compared with the operation (`>= 1`: has the item) |
| Event call condition `entry_<name>` | the dialog was started from entry `<name>` |
| Modify Bool event | sets a bool flag or adds a stamp |
| Modify Name event | sets a quest step or a flag value (None clears) |
| Modify Int event | item count; with Delta it adds (negative takes) |
| Event | broadcasts the story event with that name |

The callback name of a condition or event is the story id (`q_`, `f_`,
`stamp_`, `item_`), or the story event name. Unknown ids log a
warning, as everywhere else.

### Entries

An interactable can start its dialog at an entry (its `Entry`
property). Kotlet has one: `weigh`, used by the cargo scale. With no
entry the start node's last edge, the one without `entry_` conditions,
is used.

### Writing dialogs

1. Open the `DLG_` asset and edit the graph: add a node with
   right-click, drag between nodes to connect them, and set the
   text, the edge texts, conditions and enter events in the Details
   panel. The Dialogue Browser (Tools menu) lists every participant,
   condition and event of every dialog.
2. Save.
3. Talk to the NPC in Play. `Story.List` and `Story.Set` help to jump
   into the middle of a dialog.

Ctrl+F finds text, conditions and events in the open dialog,
Ctrl+Shift+F in all of them. Don't use the plugin's **Reload Data**
button: it reloads from a text file, and there is none.

The `DLG_` assets are binary, so git can't merge two changes to the
same dialog: edit a dialog on one branch at a time.

### Id table tool

`/Game/Story/Editor/EUW_StoryIds`, an Editor Utility Widget:
right-click it in the Content Browser and pick Run Editor Utility
Widget (dock the tab where you like, the editor remembers it).

**Reload story id tables from JSON** reloads every id table under
`/Game/Story` from the `.json` next to it and saves it. The status line
says how many tables were reloaded; details of a failed one are in the
Output Log.

## Interaction

`BPC_Interactable` can be added to any actor, including graybox markers.

| Property | Meaning |
|---|---|
| Type | Talk (start the dialog), PickUp (run the actions, remove the actor), Use (run the actions) |
| Prompt | the verb next to the key, for example "Talk" |
| Dialogue, Entry | Talk: the dialog and its [entry](#entries) (None: the default start) |
| ParticipantName, DisplayName | Talk: the NPC's participant name in the dialog and the speaker name shown |
| Conditions | the prompt shows only while all of them pass |
| Actions | run on every interaction, before a dialog starts |
| Sphere Radius | range of the prompt, measured from the component |

Its `OnInteracted` event lets level scripts react to Use.

The prompt shows over the closest interactable in range with the key of
the last used device: `[F]` or `(A)`. Interact is F / A. In a dialog:

* W / S, the arrows, the D-pad, the left stick or the mouse (hover)
  select a choice.
* F, Space, Enter or A confirm the selected choice, or continue when
  the line has no choices. Presses in the first 0.3 s after a line
  appears are ignored, so the press that opened the dialog or a quick
  double press doesn't skip a line.
* The mouse confirms only by clicking a choice itself; when the line
  has no choices, clicking the dialog box continues. A click anywhere
  else does nothing.

## Story gates

`BP_StoryGate` blocks a way until the story allows it: a barrier pole
with an invisible blocker. Fences next to it block the rest of the
line.

| Property | Meaning |
|---|---|
| OpenConditions | the gate opens (pole up, blocker off) once all of them pass |

The gate checks its conditions on BeginPlay and every 0.5 s.

## Story events

Dialog events broadcast these for later issues to pick up:

| Event | From | Meaning |
|---|---|---|
| `border_scale` | Kotlet | sent to the scale: movement hints |
| `tow_civic` | Kotlet | the tow truck takes the Civic |
| `border_done` | Kotlet | journal and checklist open, checkpoint |
| `halina_call` | Halina | the kebab stand fight starts, checkpoint |
| `hint_eat_corn` | corn lady | eat corn tutorial |
| `wait_for_midnight` | Kolya | warning, then fade to night |

## Console

| Command | Does |
|---|---|
| `Story.List` | every defined id with its value and description |
| `Story.Set <id> [value]` | flag (no value: true, `none`: clear), quest step, stamp (`none`: remove), item count |
| `Story.Event <name>` | triggers a story event |
| `Story.Reset` | clears the whole state |
