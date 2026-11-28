# Stop 0 - Border town on the Oder

The prologue and tutorial stop: two levels, the border bazaar (day) and
the impound lot (night). This document is the build spec for both
levels. Game-wide systems (controls, combat rules, items, saving) are in
[gdd.md](gdd.md); the overall story is in
[story-and-levels.md](story-and-levels.md).

Status: first draft. All numbers are starting values for tuning.

## Summary

| | |
|---|---|
| Town | Kurnikowo nad Odra (fictional; "kurnik" is Polish for "coop") |
| Levels | 0A Border bazaar (day), 0B Impound lot (night) |
| Play time | 0A: 10-12 min, 0B: 8-10 min |
| Stamp | "CARGO: POULTRY, LIVE, 1 PC" |
| Why stuck | The Civic is impounded and will be auctioned in the morning |
| Teaches | Move, camera, interact, dialog, journal, backpack, peck, |
| | flutter, throwing, healing, sneaking, shotgun, reload, boss |
| Enemies | Shawarman, Skewerman, Grill Sergeant, boss Mr. Kebabski |
| Unlocks | Poznan on the map |
| UE map | `/Game/Maps/Stop0/L0_BorderBazaar` (both levels) |

Stop 0 is linear: once the night level starts, she can't go back to the
bazaar that night. There is no warning before the night: after stop 0
Kurnikowo stays on the map and she can come back to it later.

## Map

Both levels share one UE map, `L0_BorderBazaar`: 0B is the impound lot
behind the bazaar's fence, so the two levels are one space at two times
of day. The lot seen through the fence in 0A is the real 0B, and the
exit drive through the night bazaar needs no extra set.

* **Always loaded:** the shared geometry (bridge, border post, truck
  queue, bazaar, gnome field, impound lot) and the PlayerStart.
* **Data layer `DL_Day`** (starts activated): the sun and the day-only
  content of 0A: NPCs, the first fight, pickups, throwables, the Civic
  at the border, the "BACK AT MIDNIGHT" sign (shown after the first
  fight).
* **Data layer `DL_Night`** (starts unloaded): night lighting (moon,
  fixed night exposure, lamps, grill shack, office) and the content of
  0B: guards, patrols, waves,
  the boss, pickups, lit zones. With `DL_Day` unloaded the bazaar is
  empty and closed.
* **Transition to night:** fade out, unload `DL_Day`, activate
  `DL_Night`, place her inside the lot at the hole (marker
  `MK_Checkpoint_NightStart`), fade in. The fade lasts long enough to
  hide the light change.
* **No way back:** a blocker just outside the hole keeps her out of the
  lot by day and in it at night. The main gate stays locked until the
  exit cutscene.
* **Cleanup:** things spawned during the day (enemies of the first
  fight, thrown gnomes) are not on a data layer, so the transition
  destroys them.
* **Saves** store the phase (day or night) with the checkpoint, see
  the GDD.
* The impound lot geometry is plain L0 actors in `Shared/Lot/<zone>`,
  so the map is self-contained. It exists in both phases.

### Graybox

The graybox follows [graybox.md](graybox.md). Stop 0 specifics:

* Outliner folders: `Shared/` (always loaded geometry by zone, the lot in
  `Shared/Lot/<zone>`), `Day/` (on `DL_Day`), `Night/` (on `DL_Night`).
* World axes: +X is north (river side), +Y is east. The lot fence runs
  along X = 0; the bazaar is north of it, the lot south. One unit of
  the layout is 1 m.
* `NightTransition` (`BP_NightTransition`, `Shared/Story`) does the
  transition on the story event `wait_for_midnight`: a 1.2 s fade, the
  layer swap, the teleport to `MK_Checkpoint_NightStart`, quest
  `q_car_trouble` to `night` and a `NightStart` checkpoint with the
  phase `Night`. On BeginPlay it applies the night without a teleport
  when `q_car_trouble` is `night` or later, so checkpoint reloads come
  back at night. It also shows the actors tagged `ShownAfterFirstFight`
  (the "BACK AT MIDNIGHT" sign) once `f_first_fight` is `done`.
* The event comes from Kolya ("Wake me at midnight") or from the hole
  (`MK_Interact_FenceHole`, Talk "Look", `DLG_FenceHole`, shown once
  the border check is done). Before Halina's call she only says "Too
  bright. They'd see me."; while `q_car_trouble` is `office` she can
  answer "Too bright. They'd see me. I'll wait until midnight." (the
  event) or "Not yet.".
* Cutscenes, radio, the drive out and the map screen are run by
  `StoryDirector` (`BP_StoryDirector`, `Shared/Story`), see
  [story-system.md](story-system.md#cutscenes). `Use_KebabRadio` (by the
  kebab stand, after the first fight while `q_car_trouble` is `office`)
  and `Use_CivicDrive` (the night Civic's driver door, once
  `f_boss_down` is set) are `BP_StoryUse` actors in `Shared/Story`.
* To play the night in the editor: `Story.Set q_car_trouble office`, then
  `Story.Event wait_for_midnight`. Or set `DL_Day` to Unloaded and
  `DL_Night` to Activated (initial runtime state in the Data Layers
  outliner) and start at `MK_Checkpoint_NightStart`; set them back
  before saving.
* The All-Seeing Doner was removed from the map after a playtest
  (2026-11-28): the gameplay camera never shows the tower whole, so the
  middle of the lot read as a strange pole with a light. Both actors
  (`AllSeeingDoner` on `DL_Night`, the `AllSeeingDoner_Tower` graybox)
  are gone; `BP_AllSeeingDoner` is kept in `/Game/Enemies`, unused. The
  design text below still describes it. The night shift and the
  sneaking rules are in [enemies.md](enemies.md#all-seeing-doner).
* These markers carry a `BPC_Interactable` and work in Play: the NPCs
  Kotlet, Kolya, Halina, Zbyszek, Krasnal, CornLady, CigaretteSeller
  and KantorClerk (Talk), `MK_Interact_CargoScale` (Kotlet's dialog
  from `weigh`, while `f_border_check` is scale), and the pickups
  `MK_Pickup_Gnomonaut` (while `q_gnomonaut` is started),
  `MK_Pickup_ZbyszekBox` and `MK_Pickup_CarKeys`. The sellers stand
  in front of their stalls; their interactables sit 1.1 m in front of
  them with a 1.5 m radius: she talks to them face to face, not from
  the far side of the street.
* `Road_Border` is the asphalt road from the bridge on east past the
  map edge (with a center line) and its spur to the bazaar gate.
  `Road_West` carries it over the far bank: west of the river is
  Germany, the road east goes into Poland.
* The way north is closed until the border check is done. Past the
  scale, `Fence_BorderExit` runs along the exit line (Y = -1770) from
  the west bound to the east bound, and `Truck_Queue_1` stands across
  it in the queue lane. `Gate_BorderExit` (`BP_StoryGate`) is a pole
  across the road; it opens when `f_border_check` is done.
* The map edges the player can reach are dressed, not walled: the
  bazaar wall, the truck queue and the open road at both ends. The queue
  (`Truck_Queue_1` to `_12`, the last ones stand past the map edge) is
  the north edge: `Bounds_Queue` is an invisible wall along its south
  side from the exit fence to the east bound, so she can't get between
  or behind the trucks. Nothing stands on the road. Where it leaves the
  map a `BP_EdgeReturn` trigger (`Shared/Bounds`) fades out, shows a
  line in `WBP_Toast` and teleports her back to its `ReturnPoint`
  arrow: Edge_BridgeWest (on the bridge) "That way is Germany.
  Co-co-cosmos is the other way.", Edge_QueueEast (Y = 2660) "Poland is
  too far to walk on chicken feet. You need to pick up a car first."
* The trucks wait to leave Poland: their cabs point west, and a border
  officer with a clipboard (`ArtBld_Officer`) checks papers on the
  verge by the first cab. He is a prop with a blocking box.
* The bazaar is a rectangle as wide as the lot (Y from -2700 to 2700).
  The strips beside the stall block are yards with shops (blocking
  boxes `Yard_*` in `Shared/Bazaar/Yards`): a hairdresser (FRISEUR), a
  WC container and a bar with parasol tables in the west yard, which
  opens onto the gnome field; a Sklep 24 and a ZIGARETTEN shop in the
  east yard. A KANTOR and a row of four market units under a canopy
  stand on the south verge of the road east of the gate, facing the
  road. The shops look like today's bazaars on the German border
  (Slubice, Osinow Dolny, Leknica): new, clean, plaster or panel walls,
  red metal tile roofs, huge signs. Nothing here is old or abandoned.
  Shops that are to be read face north, toward the camera.
* Art: Kenney models and Poly Haven ground over the hidden graybox (see
  [graybox.md](graybox.md#art-over-the-graybox)). The sun is in the
  north-west so the faces the camera sees are lit. Tall trees stay at
  least 6 m from walkable ground on the north and west; only bushes
  grow there.

## Story in short

Driving out of Berlin, she hears the Kudakhstan ad and heads east. At
the border the sanitary inspection weighs her and ticks "CARGO:
POULTRY". Cargo can't drive cargo, so the Civic is towed to the impound
lot behind the bazaar. Release needs an owner's ID, a registration and
a fee, and the car goes to auction at nine in the morning. The
impound lot is run by "Kebab & Parking", and tonight's special on its
menu board is "confiscated poultry, 1 pc". She thinks she is the guest
of honour. At midnight she sneaks into the lot, finds the keys, gets the
shotgun from the trunk, sets off her own car alarm, fights the night
shift and its manager, and rams the gate. The checklist says the
vehicle registration is issued only in Poznan.

## Level 0A - Border bazaar (day)

A sunny, crowded border bazaar between the bridge over the Oder and the
impound lot fence. The chicken has no weapon: the shotgun is in the
Civic's trunk. She fights with her beak, flutters and garden gnomes.

### Layout

North is the river side. The player enters from the bridge (west) and
moves south through the bazaar to the impound lot fence.

```
 W                                                          E
 +--------+------------+----------------------------------+
 |  ODER  |  BRIDGE    | 1. BORDER POST   2. TRUCK QUEUE   |
 | (river)|============|  booth, scale,   (officer, road   |
 | Germany|            |  barrier         east to Poland)  |
 +--------+------------+-------+----------+----------------+
                               | 3. GATE  |
         +---------------------+----------+-------------+
         | Socks      | Flowers   | Honey  | CDs         |
         |        4. MAIN STREET (stalls on both sides) |
         | Corn lady | Kebab stand | Gnomes | Zbyszek   |
         +------------------------+---------------------+
         | 5. GNOME FIELD         | 6. IMPOUND OFFICE   |
         |    hole in the fence   |    window, lot gate |
         +========== impound lot fence (Level 0B) ======+
```

Zones:

1. **Border post.** Guard booth, a red-white barrier, and the cargo
   scale of the veterinary border inspection ("LIVE CHICKENS"). Start of
   the level.
2. **Truck queue.** A long line of trucks in the north lane of the road
   that hasn't moved for three days: a border officer checks papers at
   its head. Uncle Kolya's refrigerated truck is in it. The queue is the
   north boundary of the level; the road itself runs on east, open.
3. **Bazaar gate.** An arch: "BAZAR - WITAMY! WILLKOMMEN! WELCOME!" The
   town sign next to it: "KURNIKOWO".
4. **Main street.** A street of stalls: grilled corn, Zbyszek's stamp
   stall, the kebab stand with a radio, the garden gnome seller. The
   kantor (currency exchange) and the cigarettes are shop buildings:
   the KANTOR on the road verge east of the gate, the ZIGARETTEN shop
   in the east yard. Their former stalls sell honey (MIOD) and socks
   (SKARPETY). Background stalls (car parts,
   tracksuits, plastic flowers) are props only. Each stall is an
   open market canopy: a steel tube frame, a plain PVC tarp, tables
   full of its own goods, and a black board with its name on the
   canopy's north edge, toward the camera. The walkway in the middle
   is open to the sky, with string light cables across it. When a stall's
   canopy covers her from the camera, the whole canopy and its name
   board hide; the frame, tables and goods stay. The camera looks
   south: it sees the fronts of the south row and the backs of the
   north row. So every stall with a story seller is in the south row
   (corn at the west end, then the kebab stand, the gnomes, and the
   stamps east of the alley to the office), and the seller stands in
   front of it, in the open, facing north.
5. **Gnome field.** An open yard where the gnome seller keeps his stock:
   hundreds of garden gnomes in rows, making low cover and a loose maze.
   The first fight happens here. A hole in the lot fence is at the far
   end, half hidden behind gnome crates.
6. **Impound office.** A booth built into the lot fence next to the
   locked main gate. Through the fence the player can see the lot and
   the black Civic in the far corner. A menu board hangs on the fence.

The lot itself is visible behind the fence. In 0A it is out of bounds;
it is the same lot she sneaks into in 0B (see [Map](#map)).

### Scale

Graybox sizes (she runs at 3 m/s). Shrunk on 2026-11-24 to cut the
running: the north part moved 5 m south, the yard between the stalls
and the lot fence went from 15.6 to 10.4 m, the queue lost 3 trucks.

| Area | Size |
|---|---|
| Whole level | about 60 x 49 m (W-E x N-S), plus the bridge |
| Bridge and border post | 18 x 12 m |
| Truck queue road | 45 m from the exit to the east edge, 8 trucks along it (4 more past the edge) |
| Bazaar gate arch | 4.8 m wide |
| Main street | 36 m long, 3.6 m walkway, 5-6 stalls per side |
| Side yards | 9 x 15 m each, west and east of the stalls |
| Gnome field | 17 x 9.4 m |
| Impound office front | 9 m of fence |

The main path from the scale to the hole in the fence is about one
minute of walking.

### Walkthrough

**1. Intro (cutscene, about 1 min).** The Civic on a German highway at
sunrise, sunglasses on. The radio plays the Kudakhstan ad (see
[Radio](#radio)). She decides to go east. The car stops at the border
barrier.

**2. The border check (dialog + first movement).** Sergeant Kotlet of
the veterinary border inspection leans out of the booth with a
sandwich.

* Kotlet looks past her into the car: "Where is the driver?" She: "I am
  the driver." Kotlet looks down: "Hm. Documents." Choices: show
  sunglasses / "I am a chicken of the world" / "You need documents to
  cross a border?"
* Kotlet: "Purpose of crossing?" Choices: "To get to the other side." /
  "Cosmos. Via Kudakhstan." / "Tourism. I love Poland. Pierogi!"
  The answer sets `f_border_answer` for later callbacks.
* Kotlet taps the sign: veterinary border inspection, live chickens
  are weighed and registered. She: "I'm not just a chicken. I'm the
  driver!" Kotlet: "Drivers have a license. You have feathers. Step on
  the scale, please." First control prompt: she gets out of the car and
  walks to the scale (move, camera rotate and zoom hints), then
  interacts with it. The barrier and the fence past the scale stay
  closed until the check is done.
* Kotlet reads the scale: "Two point three kilo. Live." He has a form
  with two boxes, DRIVER and CARGO: POULTRY, LIVE, 1 PC. He ticks the
  second one. She: "Why cargo? I drove here!" Kotlet: "A driver weighs
  seventy kilo. You weigh two point three. Two point three kilo of live
  chicken is cargo." She: "Then tick DRIVER and write 'small'." Kotlet:
  "DRIVER needs a license. CARGO needs nothing. CARGO is the only box
  that fits."
* Kotlet shines a flashlight into the trunk: "Something long in there."
  She covers the farmer's shotgun with a wing: "A very long corn cob."
  (the airport X-ray joke from game 1). This is why the shotgun stays
  in the impounded car.
* "Corn is allowed." He waves at a tow truck: "But cargo cannot drive
  cargo. The car has no driver, so it goes to the impound lot behind
  the bazaar." She: "But I AM the driver!" Kotlet: "You are CARGO:
  POULTRY, LIVE, 1 PC. It says so on the form." This is a short
  in-game moment, not a cutscene: the whole border check is playable,
  with the dialogs running in the world.
* Kotlet gives her the transit card and the checklist: "A transit card
  for live cargo, valid in Poland only. And a checklist: one stamp from
  every office. Do not leave the country. Do not leave the cage." "What
  cage?" "...Do not leave." She: "How do I get my car back?" Kotlet:
  "Impound office, at the back of the bazaar. Window of Pani Halina.
  Next."
* The checklist and the journal open for the first time. Main quest
  "Car Trouble" starts. The checklist already holds its first stamp:
  "CARGO: POULTRY". Checkpoint.

**3. The truck queue (optional).** Uncle Kolya sits on a crate on the
road verge, across the lane from his truck, with a thermos. See [Uncle Kolya](#uncle-kolya).

**4. The bazaar.** She walks in under the "WELCOME" arch and reads it
literally. Free exploration of the main street: stalls, joke dialogs,
two side quests, healing tutorial at the corn lady. The kebab stand
Shawarman is neutral for now: he sharpens his knife and stares at her
("Fresh?"). She: "I bet the cooks really like me..." (her first line
in game 1).

**5. The impound office (main).** Pani Halina Blanca sits at the window,
eating a kebab.

* Halina: "Impound office. What?" She: "The border guard took my car.
  A black Honda Civic."
* Halina: "Release of a vehicle requires: owner's ID, registration
  certificate, payment of the fee. Do you have any of these?" She: "I
  have sunglasses." (or, with the transit card: "A transit card is for
  cargo. Cargo does not collect vehicles. Cargo is collected.")
* Halina: "No documents, no car. Registration is issued only in Poznan.
  And the vehicle goes to auction tomorrow at nine. Next."
* The menu board on the fence: "KEBAB & PARKING. Tonight's special:
  confiscated poultry, 1 pc." She: "A special tonight! And they don't
  even know me yet."
* As she leaves, Halina picks up the phone: "Kebab stand? Your special
  is at my window." She: "A special? For me? How nice!" Journal: "Get
  the Civic back before nine. Tonight." Checkpoint.

**6. First fight (gnome field).** The kebab stand Shawarman runs out:
"Tonight's special is walking away!" He comes alone first, so the
player learns the peck and the flutter on one enemy. When he is down,
two more come out of the stand. Gnomes all around are throwables
(tutorial prompt on the first fight). The gnome seller shouts "Hey!
That's twenty zloty!" at every broken gnome. After the fight the kebab
stand is empty, the grill still turning, a sign on the counter: "BACK
AT MIDNIGHT".

**7. Preparing for the night.** She finds the hole in the fence at the
far end of the gnome field. Interacting with it in daylight: "Too
bright. They'd see me. Wait until midnight." Two ways to wait:

* Ask Kolya to rest in his cab ("Queue won't move until morning
  anyway"). He gives the stealth tip if not given yet. He offers this
  once Halina has sent her away (`q_car_trouble` past started).
* Interact with the hole again and choose "Wait for midnight".

Both fade to night (see [Map](#map)) and 0B starts at the hole. There is
no warning: Kurnikowo stays on the map after stop 0.

### NPCs

Kolya, Halina, Zbyszek, Krasnal, the corn lady and the kebab stand cook
are 3D models (`ArtNPC_<Name>`, `BP_NPC`, folder `Day/NPCs`) placed over
their markers by `Art/NPCs/Scripts/ue_dress_npcs.py`; the markers keep
their `BPC_Interactable` and their meshes are hidden. Each plays an idle
loop and blends to a talk loop while its own dialog line is on screen.
Models, clips and props: [Art/README.md](../Art/README.md#stop-0-npcs-npcs).

Placement rule: the camera looks south, so an NPC stands in the open
and faces north, toward the camera. Under a south-row canopy or behind
a north-row counter nobody would see a face.

| NPC | Where | Holds |
|---|---|---|
| Kolya | On a crate on the road verge, across the lane from his truck's cab | Thermos |
| Halina | At her window (a small lamp lights her; `MK_Interact_OfficeWindow` is hidden) | Stamp, kebab |
| Zbyszek | In front of the west corner of his stall, by the alley to the office | A stamp, held up |
| Krasnal | Beside his stall, by the way to the gnome field | "GNOMES 2 FOR 1!" sign, a gnome |
| Corn lady | In front of the west corner of her stall | Tongs with a cob, held out |
| Kebab stand cook | Between the stand's two tables, honing his knife; no dialog; gone (hidden, no collision) from the moment `q_car_trouble` reaches `office`, when the fight starts | Knife, steel |

They block her like any pawn, so she can't walk through them.

#### Sergeant Kotlet

Border guard of the veterinary border inspection. Bored, polite,
always eating. Appears only in the border check. He is the first
official who could prove she isn't food, and he deals in food.

#### Uncle Kolya

First meeting. Big, friendly trucker, stuck in the queue for three
days, drinks tea from a thermos ("A samovar, but for the road").

* Introduces himself in a mix of English and Russian, offers tea and
  asks where she flies. Hearing "Kudakhstan" he teaches her "kudakh":
  "You know what Kudakhstan means? In Russian your 'cluck' is 'kudakh'.
  Good word. Strong."
* Stealth tip with a proverb, once she tells him her car is in the
  impound lot: "Kebab & Parking? Bad people. You want your car, you go
  at night. Quietly. Tishe yedesh - dalshe budesh: go quieter, get
  further. And remember: night guards eat at midnight. Always
  shawarma." The tip is flavour only and doesn't change 0B.
* Gives her 2 corn cobs.
* His truck: "FROZEN GOODS - EXPORT EAST" with a smiling cartoon
  chicken logo. She: "A chicken on the truck! Chicken-friendly company."
  Kolya: "...Yes. Very friendly. Very cold." The rear doors are frosted
  and locked; the player gets a glimpse of white boxes through a gap,
  she doesn't notice.
* Sets `f_kolya_met`. Optional, but the main path walks past him.

#### Pani Halina

The impound clerk, employed by "Kebab & Parking". Speaks only in
regulations. Always eating a kebab.

#### Pan Zbyszek

The stamp seller: "Stamps! For every occasion! Weddings, funerals,
customs!" Starts the side quest
[Stamps for Every Occasion](#stamps-for-every-occasion).

#### Mr. Krasnal

The garden gnome seller ("krasnal" is Polish for "gnome"). He stands
beside his stall, by the way to the gnome field, not under its canopy
(the camera could not see him there). "Gnomes!
Germans love them! Two for one!" Starts the side quest
[The Gnomonaut](#the-gnomonaut).

#### The corn lady

Sells grilled corn on the cob. Gives the chicken a free cob and the
healing tutorial: "Eat, bird. You're too thin for the kebab anyway."
Sets the tone: every seller sizes her up.

#### Joke shops (dialog only)

Nobody is modelled inside a building. She talks through the kantor's
barred window and at the window of Kotlet's booth: the talk point is
half a meter in front of the wall, the NPC is a voice and a portrait in
the dialog. The cigarette seller stands outside, by his shop's door
(`SM_Seller`, a static figure). The markers `MK_NPC_KantorClerk`,
`MK_NPC_CigaretteSeller` and `MK_NPC_Kotlet` are hidden.

* **Cigarette seller:** "Cheap! Ten euro a carton!" She: "Smoking
  kills." He: "So does the kebab stand. Pick your death."
* **Kantor:** "We exchange euro, zloty, rubles. Not poultry." She: "What
  is the rate for one chicken?" "Depends. Grilled or fried?"
* **Kebab stand radio** (after the fight): the DJ news, see
  [Radio](#radio).

### Side quests

#### Stamps for Every Occasion

Spans both levels; unlocks the forgery ending.

1. 0A: she asks Zbyszek for a stamp that says PERSON ("The border
   guard wrote me down as CARGO. Do you have a stamp that says
   PERSON?"). "I have
   everything. Had. Customs took my box. Now it sits in the impound
   lot, same as your car. Bring it back and I make you a stamp so
   official, the office itself will believe it."
2. 0B: the box is on the evidence shelf in the guard office ("EVIDENCE:
   COUNTERFEIT GOODS, 1 BOX").
3. Exit cutscene of 0B: if she has the box, Zbyszek waits with his van
   on the back street. Choice: give the box (she gets the Forged stamp,
   `f_forged_stamp`) or keep it ("Joke's on you, it's all stamps from
   window 7").

#### The Gnomonaut

Short, 0A only.

1. Krasnal mentions it himself ("...Except my best one. He ran
   away."): he lost his best gnome, the Gnomonaut (a gnome in a
   cosmonaut helmet), somewhere in the gnome field, and promises "a
   very good price" for it. If she says she has no money: "Then the
   price is very, very good. Find him!"
2. She searches the field. The Gnomonaut sits on top of a crate in a
   back corner; the helmet glints when the camera faces it.
3. She returns it. Krasnal: "Take him. He wants to go to the cosmos
   too." She gets the Gnomonaut (joke item, `f_gnomonaut`); it rides on
   the Civic's dashboard in every later car scene and ending.

The Gnomonaut can't be thrown (it isn't a world throwable; it goes
straight to the inventory).

### Ambient jokes and props

* The "WELCOME" arch, which she reads as personal.
* The town sign "KURNIKOWO".
* Stall signs in Polish: KUKURYDZA, PIECZATKI, KRASNALE, MIOD,
  SKARPETY. Shop signs for the German customers: ZIGARETTEN, KANTOR,
  FRISEUR.
* The All-Seeing Doner: the kebab stand's giant sign on a tall black
  tower over the lot fence. By day it is unlit, just a cartoon eye on a
  doner with the slogan "WE SEE YOU HUNGRY". She: "A big friendly eye.
  Somebody is watching over me!" At night it becomes the main hazard
  of 0B. (Removed from the map after a playtest, see Graybox above.)

### Checkpoints

* After the border check (level start).
* When leaving the impound office (before the first fight).

## Level 0B - Impound lot (night)

The impound lot of "Kebab & Parking" at midnight. Lit spots, dark rows
of confiscated cars, the night shift eating shawarma at the grill
shack. First part is sneaking with only the beak and gnomes, second
part is the shotgun fight and the boss.

### Layout

```
 N (bazaar side)
 +-[HOLE]-----------------------------[5. OFFICE]-[MAIN GATE]-+
 | 1. Fence corner     2. Outer lot: rows of impounded cars   |
 |    (gnome crates)      (patrol routes, dark gaps)          |
 |                   (*) the All-Seeing Doner on its tower    |
 |    3. Grill shack            4. Container stacks           |
 |       (guards eat)              (shell crate)              |
 +-------------------------[INNER GATE]-----------------------+
 | 6. Inner lot "SPECIAL IMPOUND": the Civic, boss arena      |
 |    containers along the walls, cars as cover               |
 +------------------------------------------------------------+
 S (river meadows, level boundary)
```

Zones:

1. **Fence corner.** She comes in through the hole. Gnome crates behind
   the fence (throwables), a dark, safe spot for a sneaking tutorial.
2. **Outer lot.** Rows of impounded cars with gaps between them. Joke
   cars: a Trabant packed with gnomes (throwables), a German hatchback
   full of cigarette cartons, a tractor with a ticket on it, a
   wedding limousine. Two patrol routes with flashlights.
3. **Grill shack.** A shed with a big grill, plastic chairs and a
   radio. Three Shawarmen eat at midnight, sitting with their backs to
   the lot and facing the grill. Strong light. They are busy, so they
   only see 1.8 m in front, but a peck hit is noise: pecking one of them
   alerts the other two.
4. **Container stacks.** Shipping containers in two levels. A crate of
   shells inside an open container (found before the shotgun; she
   can't use it yet - "Shells. Now I just need something that goes
   bang").
5. **Guard office** (part of zone 2, by the main gate). The other side
   of Halina's booth. A sleeping guard in front of a CCTV monitor, the
   key board, the evidence shelf, the inner gate button.
6. **Inner lot.** A fenced area for "special" confiscations behind a
   locked gate. The Civic is here. This is also the combat arena:
   about 18 x 15 m, containers along the walls (Skewermen climb them),
   4-5 cars as cover, two shell crates. The Civic stands at the south
   end of the arena: its trunk refills shells at any time (see the
   GDD), but it is far from the inner gate where enemies come in, so
   running to it mid-fight is a choice. The shell crates are the closer,
   limited option.

### Scale

Starting sizes for the graybox, to be tuned.

| Area | Size |
|---|---|
| Whole level | about 54 x 41.5 m |
| Outer lot | 54 x 26.5 m to the inner fence, 3 car rows with 1.9-2.6 m dark gaps |
| Grill shack | 6 x 4.8 m |
| Container stacks | 12 x 9 m |
| Guard office | 4.8 x 3.6 m |
| Inner lot (arena) | 18 x 15 m |
| All-Seeing Doner | Center of the outer lot; beam 15 m long, 20 deg wide |

### Lighting and sneaking

Sneaking uses the shared detection rules from the GDD (lit vs dark,
busy enemies, noise). In this level:

* **Lit zones:** lamp posts by the office, the grill shack, and the
  flashlight cones of patrolling guards.
* **The All-Seeing Doner** (removed from the map after a playtest on
  2026-11-28: a tower the camera never shows whole looked like a stray
  pole with a light; the lit zones and the guards' flashlights carry
  the sneaking now). At night the sign is a parody of the Eye of
  Sauron: a giant doner on top of a tall black tower, wrapped in a
  ring of fiery orange neon, with a burning vertical slit pupil in the
  middle. It hums low and ominously, and the slogan "WE SEE YOU
  HUNGRY" flickers under it. Its gaze is a searchlight: a cone of
  orange light that sweeps the outer lot (a full turn in 8 s, with
  short pauses where the pupil "looks around").
  * In the beam she counts as lit for every guard.
  * The Eye itself is a lookout with its own awareness: if she stays in
    the beam, the pupil narrows and the glow grows brighter over 1 s.
    When it is full, the Eye stops on her, plays the kebab stand
    jingle at full volume and alerts every Shawarman within 12 m of
    her. This is a deliberate exception to the 7.2 m enemy shout of the
    GDD. Leaving the beam in time drains it, like any enemy awareness.
  * It is a timing puzzle: move between the car rows while the gaze
    looks away.
* **Dark gaps** between car rows are safe hiding spots.
* **Awareness.** Guards don't spot her instantly: their "?" meter fills
  while she is in sight (see the GDD). A mistake can be fixed by
  stepping back into the dark before the "!".
* Getting spotted is never a fail: alerted guards fight. Sneaking only
  decides how many fights she takes before the shotgun.
* Dark must stay readable from the camera height: the player has to
  see the chicken, the enemies and the lit-zone edges clearly in the
  dark parts, which should still feel dark.

### Walkthrough

**1. Sneak in.** Start at the hole. Prompt: "Stay in the dark. Unaware
enemies take triple damage from a peck." First patrolling guard walks
past the corner: the player can wait or follow him from behind and
surprise-peck him (one peck kills an unaware Shawarman). If he turns
around, his "?" meter starts filling: prompt "Back off before the !".
Checkpoint at level start.

**2. Outer lot.** Cross the rows, avoiding the second patrol and the
gaze of the All-Seeing Doner. She: "The friendly eye! It's looking for
me. How sweet." Optional detour to the Trabant (gnomes) and the
container with the shells.

**3. The guard office.** The night guard sleeps in front of the CCTV.
The monitor shows her on camera: she waves at herself. Inside:

* The key board: the Civic's key has a tag "HONDA CIVIC, BLACK + CARGO:
  POULTRY 1 PC (MISSING)". Takes the Car keys.
* The evidence shelf: Zbyszek's box (optional).
* A big red button "INNER GATE". Pressing it opens the inner gate with
  a loud squeak. Nobody reacts: "Midnight shawarma is sacred." The
  squeak is not a noise event and alerts nobody, the sleeping guard
  included (a deliberate exception to the noise rule).
* The sleeping guard only wakes up from noise (fighting inside the
  office wakes him).

**4. The Civic.** She reaches the car in the inner lot. Pressing the key
fob, she hits the wrong button: "Which one is unlock? ...Oh. That's the
panic button." The car alarm goes off. She opens the trunk anyway: the
farmer's pump-action shotgun, loaded with 8 shells, and a box of 12 more.
She racks it: "Now we talk, Shawarmen." (her line from game 1, when she
found the shotgun in the hay). Shotgun prompts: aim, fire, press reload
while standing still.
Checkpoint.

**5. The night shift (waves).** Every Shawarman in the lot is alerted;
they come through the inner gate.

* Wave 1: the night shift Shawarmen still standing from the sneak part
  (up to 6). If fewer than 2 are left, new ones come from the grill
  shack to make 2, so the shotgun always has targets to practice on.
* Wave 2: 2 Shawarmen, 2 Skewermen who climb the containers, 1 Grill
  Sergeant.
* Shell crates in the arena refill once between the waves.

**6. Boss: Mr. Kebabski, the night manager.** He comes out of the grill
shack carrying a doner spit with the doner still on it. "Tonight's
special does not leave the kitchen." Checkpoint before his intro. See
[Mr. Kebabski](#mr-kebabski-boss).

**7. Exit (cutscene).** She gets into the Civic, puts the sunglasses
on: "I'll be kudakh!" She rams the main gate. Every impounded car alarm
goes off behind her; nobody chases her. She drives through the empty
night bazaar and out through the bazaar arch, where the back street
runs along the frozen truck queue. There:

* If she has Zbyszek's box, he waits by his van (dialog, see the side
  quest).
* She overtakes the queue on the shoulder.
* The radio plays the next Kudakhstan ad.
* The checklist: next stamp "VEHICLE REGISTRATION - issued in Poznan
  only".
* Map screen: Poznan appears. Main quest "Car Trouble" completes.

### Enemy placement (sneak part)

| Enemy | Where | State |
|---|---|---|
| Shawarman | Fence corner to outer lot | Patrol, flashlight |
| Shawarman | Outer lot, between rows | Patrol, flashlight |
| Shawarman x3 | Grill shack | Busy (eating) |
| Shawarman | Guard office | Sleeping (noise only) |

The 6 sneak-part Shawarmen are the same night shift that joins the
waves. Any she defeats while sneaking don't come back.

### Checkpoints

* Level start at the hole.
* Opening the trunk (shotgun picked up).
* Before the boss intro.

## Enemies

Shared AI rules (detection, alert, telegraphs) are in the GDD. Death
lines are in [Death screens](#death-screens).

### Shawarman

The common enemy of the whole game. Melee grunt.

* HP 30. Walks at 2.4 m/s (the chicken runs at 3 m/s, so she can always
  kite).
* Attack: an overhead knife chop down at her feet. 0.6 s windup (raises
  the knife, glint and sound), 0.4 m reach, 15 damage. A peck during the
  windup interrupts it.
* Barks: "Fresh delivery!", "Garlic or spicy?", "Extra chicken!",
  "Tonight's special!"
* In 0B, may drop 2 shells. The chance depends on her reserve shells:
  50% at 0, sliding linearly down to 10% at the full 32.

### Skewerman

Ranged Shawarman, 0B only.

* HP 20. Keeps 3.6-6 m away and backs off when she gets close.
* Attack: throws a skewer, 1.0 s windup, slow visible projectile
  (7.2 m/s) that can be dodged or out-walked, 10 damage.
* Climbs onto low containers in the arena (fixed climb points).

### Grill Sergeant

Heavy Shawarman with a portable grill, 0B only.

* HP 80. Walks at 1.8 m/s.
* The grill lid is a shield: shots and pecks from the front do 25%
  damage. Teaches flanking and flutter.
* Attack: grill slam, 1.0 s windup, 1.2 m radius in front, 25 damage,
  leaves hot coals on the ground for 3 s (10 damage per second).
* Bark: "Drop and give me twenty... wings!"

### Mr. Kebabski (boss)

The night manager of "Kebab & Parking". HP 400. Fought in the inner
lot.

* **Spit Spin.** Holds the doner spit out and spins for 2 s, 1.8 m
  radius, 25 damage. Telegraph: plants his feet and winds up for 0.8 s.
  Counter: flutter out of range.
* **Spit Charge.** Lowers the spit like a lance, 1.0 s windup with a
  visible line on the ground, charges in a straight line, 30 damage.
  If he hits a car or a container he is stuck for 2.5 s and takes
  double damage (that car's alarm goes off - car alarms pile up as
  the fight goes on).
* **Order for Table One!** At 50% HP he calls 2 Shawarmen from the
  grill shack, and both shell crates refill.
* Pattern: Spin when she is close, Charge when she is far; never two
  Charges in a row.
* Defeated: he spins one last time, dizzy, and falls into a pile of
  fries (exact gag for the art doc).

## Items in stop 0

| Item | Type | Where | Notes |
|---|---|---|---|
| Transit card | Key | Kotlet, 0A | "Valid in Poland only" |
| Checklist | Key | Kotlet, 0A | Stamp slots for the whole game |
| Corn cob | Consumable | Corn lady, Kolya, crates | Heals 35 HP |
| Garden gnome | Throwable | 0A gnome field, 0B crates | World object |
| Car keys | Key | 0B guard office | Tag joke |
| Farmer's shotgun | Weapon | 0B Civic trunk | 8 loaded + 12 shells |
| Shells | Ammo | 0B crates, Shawarmen drops | |
| Zbyszek's box | Quest | 0B evidence shelf | Optional |
| Forged stamp | Key | Zbyszek, 0B exit | Forgery ending |
| The Gnomonaut | Joke | Krasnal, 0A | Rides on the dashboard |

The checklist is the main progress item of the game: five slots
(CARGO: POULTRY, VEHICLE REGISTRATION, VETERINARY CERTIFICATE, WILD
BIRD, FINAL RULING). The first slot gets a stamp that is technically
an insult.

Healing budget: 0A has about 5 corn cobs reachable (1 free from the
corn lady, 2 from Kolya, 2 in crates); 0B has 4 in crates (2 in the
arena).

## Quests and story state

| Id | Kind | Values / meaning |
|---|---|---|
| `q_car_trouble` | Main quest | started, office, night, keys, car, done |
| `q_zbyszek_box` | Side quest | started, box_taken, given, kept |
| `q_gnomonaut` | Side quest | started, found, done |
| `f_border_answer` | Flag | other_side, cosmos, tourism |
| `f_border_check` | Flag | scale (sent to the scale), done |
| `f_kolya_met` | Flag | Talked to Kolya |
| `f_kolya_tip` | Flag | Got the stealth tip |
| `f_corn_lady_cob` | Flag | Got the free cob from the corn lady |
| `f_forged_stamp` | Flag | Has the Forged stamp |
| `f_gnomonaut` | Flag | Has the Gnomonaut |
| `f_boss_down` | Flag | Mr. Kebabski is down: the Civic can drive out |
| `stamp_cargo_poultry` | Stamp | Always set in stop 0 |

Item ids: `item_transit_card`, `item_checklist`, `item_corn_cob`,
`item_car_keys`, `item_zbyszek_box`, `item_forged_stamp`,
`item_gnomonaut`. The ids are defined in
`Content/Story/Stop0/DT_StoryIds_Stop0.json` and the dialogs are the
`DLG_` assets in `/Game/Story/Stop0/Dialogs`, see
[story-system.md](story-system.md).

Callbacks for later stops:

* `f_border_answer = other_side`: the radio DJ tells the "why did the
  chicken cross the border" joke in the Poznan intro.
* `f_kolya_met`: Kolya greets her as an old friend at the gas station.
* `f_gnomonaut`: the gnome appears on the dashboard and in the endings.

## Death screens

Each killer has its own picture and lines; one line is picked at
random, mixed with the generic game 1 lines from the GDD. Lines marked
(game 1) come from the first game.
The "killed by" tags are the row names of `DT_DeathScreens`, see
[combat.md](combat.md#death-screen-table). The hot coals use the
`GrillSergeant` tag.

* **Shawarman** - chicken shawarma wrap: "That's a wrap.", "One
  chicken wrap, to go." (game 1), "Extra garlic sauce, hold the
  cosmos." (game 1)
* **Skewerman** - chicken shish kebab: "Shish happens.", "Skewered
  and delivered."
* **Grill Sergeant and hot coals** - grilled chicken: "Grilled. Medium
  rare.", "Drop and give me twenty... minutes per side."
* **Mr. Kebabski** - doner on a spit: "Spit happens.", "You ARE the
  doner." (game 1), "Rotating slowly on the spit of fate." (game 1)

## Radio

The radio DJ lines heard in stop 0:

* **Intro (car):** "KUDAKHSTAN! The place where all chickens go to
  co-co-cosmos! Thousands have already gone. Not one came back!" She:
  "They love it so much they stay!"
* **Kebab stand radio (0A, after the fight):** "Breaking news: why did
  the chicken cross the border? Polish customs are investigating."
* **Exit (car):** "Kudakhstan! Now with more cosmos! Chickens, do not
  bring luggage. You will not need it."

## Tutorial hints

Short contextual prompts, each shown once. Gamepad or keyboard glyphs
depending on the last used device.

| Where | Hint |
|---|---|
| 0A, walking to the scale | Move, rotate camera, zoom |
| 0A, the scale | Interact |
| 0A, after the border | Journal, backpack and checklist |
| 0A, corn lady | Eat corn to heal |
| 0A, first Shawarman | Peck, flutter |
| 0A, first gnome in reach | Pick up and throw |
| 0B, the hole | Stay in the dark; surprise peck |
| 0B, first "?" meter | Back off before the "!" |
| 0B, the All-Seeing Doner | Its gaze is a lookout |
| 0B, the trunk | Fire; press reload, only while standing still |
| 0B, first empty tube | Reload with the button |
| 0B, out of shells | Peck still works; the trunk has more |

## Content to build

Placeholder versions are enough to start; final look comes from the
art style document.

* **Characters:** the chicken (with sunglasses), Sergeant Kotlet,
  Uncle Kolya, Pani Halina Blanca, Pan Zbyszek, Mr. Krasnal, the corn
  lady, the cigarette seller, the kantor clerk, background truckers.
* **Enemies:** Shawarman, Skewerman, Grill Sergeant, Mr. Kebabski.
* **Vehicles:** the black Civic, the tow truck, Kolya's refrigerated
  truck, background trucks, impounded cars (Trabant, hatchback,
  tractor, limousine), Zbyszek's van.
* **Key props:** guard booth, barrier, cargo scale, stalls, the
  "WELCOME" arch, the town sign, the menu board, garden gnomes (intact
  and broken), the Gnomonaut, the All-Seeing Doner (day and night
  look, sweeping light cone), the grill shack, containers, shell and
  corn crates, key board, CCTV monitor, evidence shelf, inner gate
  button, fences and gates.
* **Cutscenes:** intro drive, exit drive with the gate ram and the
  night bazaar.
* **Audio:** radio lines, car alarm, Shawarman barks, bazaar ambience,
  night ambience, the Eye's hum and the kebab stand jingle.
