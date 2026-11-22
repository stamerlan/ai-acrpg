# Ambitious Chicken RPG - Story and Levels

The story, stops, levels, characters and endings. Game systems are in
[gdd.md](gdd.md).

Status: first draft from brainstorming. Undecided points are in
[Open questions](#open-questions).

## Premise

After game 1 the Ambitious Chicken has a black Honda Civic, sunglasses
and the farmer's shotgun. Driving out of Berlin, she hears an ad on the
car radio:

> "KUDAKHSTAN! The place where all chickens go to co-co-cosmos!
> Thousands have already gone. Not one came back!"

She hears "they love it so much they stay". The player suspects the
darker meaning. The game never says which one is true: Kudakhstan and
its cosmodrome are the goal of the whole series and are never reached.

She drives east. At the Polish border a guard asks for documents. She
has sunglasses. No driving license, no car registration (the Civic was
"a fee", with no receipt), and nothing that says what she is. The
guard's form has two boxes: DRIVER or CARGO: POULTRY, LIVE, 1 PC. He
ticks the second one.

The central question of the game: **legally, is she a person or
poultry?** As poultry she can't drive and belongs to the food chain. As
a person she needs a license, a registration, a stamp... She gets a
temporary transit card valid only inside Poland, and a checklist of
offices. Every stamp, of course, is issued only in another town.

## The route

Berlin, then the Polish border on the Oder, Poznan, a village, a forest
with a gas station, and Gdansk.

The irony: she wants to go east, but the paperwork keeps sending her
somewhere else ("that stamp is issued only in..."), and she ends up in
the north, on the Baltic shore. Kudakhstan is still far to the east.

## The stop template

Every stop follows the same pattern:

1. **Arrive.** It looks like a refuge; she misreads it as a welcome.
2. **Stuck.** A story reason keeps her there (a closed road, an
   impounded car, an office that is never open). This is a story beat,
   not a car mechanic.
3. **Two levels.** A hub (people, quests, dialogs) and a second area
   (kitchen, archive, farm, lodge) where the menu twist comes out and
   the main fight happens. She can walk between them freely.
4. **Leave.** The stamp is in the checklist, a pun lands, the next stop
   appears on the map.

Core gag for every stop: every official who could prove she isn't food
deals in food.

## Stops and levels

| # | Stop | Stamp | Why she's stuck |
|---|---|---|---|
| 0 | Border town on the Oder | "CARGO: POULTRY" | Car impounded |
| 1 | Poznan | Vehicle registration | The Civic has no owner |
| 2 | Village | Veterinary certificate | The vet is at the poultry farm |
| 3 | Gas station and forest | "WILD BIRD" | Road closed for tree counting |
| 4 | Gdansk (finale) | The final ruling | Office open one hour a day |

10 levels in total, about 6-12 minutes of play each.

### 0. Border town on the Oder (prologue, tutorial)

The drive out of Berlin with the radio ad, then the border check and
the "CARGO: POULTRY" box. The car is impounded and she gets the transit
card and the checklist. Detailed build spec:
[level0-border-town.md](level0-border-town.md).

* **Level A - Border bazaar.** Starts with the border check. Cheap
  cigarettes, kebab stands and a sea of garden gnomes. First dialogs,
  first Shawarmen (fought with the beak and thrown gnomes: the shotgun
  is in the impounded car), a shady stall owner who sells "official"
  stamps (see forgery ending). Uncle Kolya's truck waits in the border
  queue.
* **Level B - Impound lot (night).** She sneaks in, finds the keys and
  the shotgun in the trunk, sets off her own car alarm and fights the
  night shift and its manager, Mr. Kebabski.

### 1. Poznan

The vehicle registration office: the Civic has no owner on paper, and
without a registration it can't leave the city.

* **Level A - Old town square.** The town hall clock with mechanical
  goats that butt heads at noon, cafes, the registration office with
  queue numbers, "not my department, go to window 7" and "come back
  tomorrow".
* **Level B - Records archive.** The basement under the office: lost
  files, shelves to the ceiling, flying paper, a filing-cabinet mimic
  and a paper golem made of unprocessed forms. The office canteen
  upstairs serves chicken cutlets.

### 2. Village

The veterinary certificate of a "live chicken". The vet is on duty at the
poultry farm all week and signs nothing anywhere else.

* **Level A - Village.** Church fair, neighbours, Babcia's house. Babcia
  is kind and feeds everyone, and it's Sunday, the day of chicken soup.
* **Level B - Poultry farm.** The vet's real job here is stamping
  chickens "FIT FOR CONSUMPTION". A coop full of hens who need rescuing
  (optional, feeds into the endings).

### 3. Gas station and forest

The road-movie heart of the game and its calm stop. A lonely forest
road is closed for a forest inventory (the forestry office is counting
every tree). The forestry office rules that she is a "WILD BIRD": a
protected species... except during hunting season, which opens
tomorrow.

* **Level A - Gas station.** One lonely 24-hour station on the forest
  road. A cashier who has seen everything ("A chicken driving a Civic?
  Third one this week."). A roller grill with chicken hot dogs, a
  bulletin board with side quests, a pay phone, a car wash, truckers in
  the parking lot. Uncle Kolya's refrigerated truck parks here for the
  night, so the player sees what it's carrying.
* **Level B - Forest camp and hunting lodge.** A pine forest by a river.
  She pitches a tent and sits at the firepit: sleeping in the tent is
  the checkpoint. Quiet night dialogs by the fire with Uncle Kolya, the
  stars, and the Kudakhstan ad on a small radio; here she says out loud
  why she dreams of the cosmos. Little combat at the camp itself. The
  danger is across the river: the hunting lodge is preparing a game
  dinner, with hunters, their dogs and the lodge cook.

### 4. Gdansk (finale)

The final ruling: Person or Poultry. The ruling office is open one hour
a day.

* **Level A - Old town on the river.** The medieval port crane, the
  Neptune fountain, a fish market, the port where Uncle Kolya unloads.
  Last side quests and the queue for the ruling office.
* **Level B - Office and shipyard.** The upper floors of the ruling
  office (windows, stamps, endless corridors), then a boss fight with
  the Head Clerk on the shipyard cranes.

## Characters

* **The Ambitious Chicken** - the player character (name to be decided). Brave,
  stubborn, a bit naive; misreads every danger as an invitation.
* **Uncle Kolya** - a big trucker with a refrigerated truck and the
  main home for the Russian jokes: proverbs, road songs, tips. He turns
  up at the border queue, the gas station, the campfire and the Gdansk
  port. Friendly and honest, and his truck is full of frozen chickens
  headed east. The player sees it early; she finds out at the end.
* **Babcia** - the village grandmother who feeds everyone. Sunday means
  chicken soup.
* **The vet** - certifies "live chickens" and stamps "FIT FOR
  CONSUMPTION" with the same stamp.
* **The gas station cashier** - has seen everything, impressed by
  nothing.
* **The radio DJ** - the voice of the Kudakhstan ads and the news
  between stops.
* **The Head Clerk** (final boss) - the last office in Gdansk.

R. Fuchs does not appear: he stayed in Berlin.

## Enemies

* **Shawarmen** - the common recurring enemy; there's a kebab stand in
  every Polish town. Variants: Skewermen (ranged) and Grill Sergeants
  (heavy, shield). Mr. Kebabski, the night manager of the border
  impound lot, is the stop 0 boss.
* **Clerks** - rubber stamps as weapons (a stamp counts as a hit),
  flying paper, a filing-cabinet mimic, the paper golem.
* **Hunters and their dogs** - the forest stop.
* **Head Clerk** (final boss). Moves: the "Form Is Incomplete" slam,
  a summons to the back of the queue (teleports her back), lunch break
  (the window shutter slams down).

## The radio thread

The Kudakhstan ad runs through the whole game: in the prologue, on the
map screen between stops, at the campfire and in the ending. Each time
it's a bit stranger ("Kudakhstan: every chicken a cosmonaut. Feathers
optional."). It's cheap to make and keeps the motivation alive.

## Endings

The ruling office in Gdansk decides what she is. Choices during the
game unlock the options.

* **Person.** She gets a license (the photo is just her beak) and
  drives east legally.
* **Poultry.** An export certificate: she leaves east as cargo in Uncle
  Kolya's truck. If she frees the frozen chickens first, they all go
  east together.
* **Wild bird.** The forestry stamp wins: protected, can't be eaten,
  but can't drive either, so she has to "migrate".
* **Forgery.** A fake stamp from the bazaar: "This stamp is from window
  7. Window 7 closed in 1989."

Every ending closes on the Baltic shore with the radio crackling:
"Kudakhstan... where all chickens go..." The road east is still ahead.

## Open questions

* The chicken's name.
* Lavash Baron: a shawarma-chain boss behind the Shawarmen, following
  her east in a giant food truck. Keep him as a second villain, or let
  bureaucracy be the only main antagonist?
* Which endings need which choices, and how many endings to build.
* Side quests per stop.
