# Logical Requirements

Logical requirements represent the conditions Link must fulfill to execute a [strat](strats.md). They can require inventory or game state, consume resources, restore resources, or change other logical states.

## Structure

A logical requirement is an array of logical elements. Elements in the array are implicitly combined with a logical AND and are evaluated sequentially in the order in which they appear.

```json
"requires": [
  "Lamp",
  {"unlockDoor": 1},
  {"bombs": 2}
]
```

In most cases, requirement order does not change the result. Order must still be preserved because some elements spend or restore resources. Each successful requirement updates the state that is passed to the next requirement.

An empty requirements array is always fulfilled:

```json
"requires": []
```

Individual logical elements can be bare strings or objects.

## String Requirements

A bare string can name an item or logical inventory state, a helper, or a tech.

### Items and Inventory State

An item name requires Link to possess that item and to be in a state in which it can be used. Item requirements may therefore include implicit usability conditions beyond simple inventory ownership.

```json
"Hookshot"
```

The detailed interaction between item use and Link's normal, bunny, superbunny, and lonk states is not yet fully modeled.

Some names represent a logical category rather than a single concrete item. For example, `"Boomerang"` is a helper that accepts either `"BlueBoomerang"` or `"RedBoomerang"`.

### Helpers

Helpers are defined in [`helpers.json`](../helpers.json). A helper expands to its own requirements, allowing commonly repeated logic or configurable assumptions to be defined in one place.

Each helper has:

- `name`: The string used to require the helper.
- `requires`: The logical requirements that replace the helper when it is evaluated.
- `note`: Optional consumer-facing explanation.
- `devNote`: Optional contributor-facing implementation detail.

```json
{
  "name": "Boomerang",
  "requires": [
    {"or": [
      "RedBoomerang",
      "BlueBoomerang"
    ]}
  ]
}
```

When a helper is required, its `requires` list is evaluated as though it appeared directly at that point in the containing requirement list. Its requirements retain their normal ordering, costs, and effects.

Helpers also centralize assumptions that a randomizer may override, such as a required medallion, prize threshold, or whether a vanilla behavior has been changed. An empty `requires` array makes a helper free, while `["never"]` disables it.

By convention, most helper names begin with `h_`, although a reusable logical category may instead use a natural name such as `Boomerang`.

```json
"h_hitBlueOrangeSwitch"
```

### Tech

Techs are defined in [`tech.json`](../tech.json). A tech represents an in-game technique that consumers may allow or disallow based on their logic configuration. See the [Tech documentation](tech.md) for the complete format and difficulty model.

```json
"canBombBoost"
```

A tech's `techRequires` contains other required techs, while `otherRequires` contains requirements such as items, ammunition, health, or damage. Both groups must be fulfilled when using the tech. Extension techs explicitly include their parent tech among their dependencies.

### Special Values

`"never"` is a requirement that cannot be fulfilled. It is useful for disabling helpers or behavior without removing their definitions.

`"free"` is the conceptual opposite and is always fulfilled. An empty requirements array is the normal way to represent an action with no requirements.

## Structural Logical Elements

### `and`

An `and` object is fulfilled only if all of its elements are fulfilled. Its elements are evaluated sequentially in their listed order.

```json
{"and": [
  {"combatProficiency": 2},
  {"damage": {"enemy": "Deadrock", "count": 1}}
]}
```

### `or`

An `or` object is fulfilled by fulfilling any one of its elements.

```json
{"or": [
  "Hookshot",
  {"bombs": 1},
  {"redCane": 1}
]}
```

Consumers should preserve every meaningful successful result of an `or`. Different branches may leave Link with different amounts of health, magic, ammunition, or other state. Selecting only the first or apparently cheapest successful branch can rarely discard a more useful result, such as a branch that includes a refill.

Only the costs and effects of the selected branch are applied.

## Equipment Requirements

Equipment objects require a level of progressive equipment. They do not consume the equipment, but they include any implicit state needed to use it.

### Sword

`sword` requires the given sword level or higher:

```json
{"sword": 2}
```

Sword levels are:

1. Fighter Sword
2. Master Sword
3. Tempered Sword
4. Golden Sword

`swordExact` requires exactly the specified level. It permits levels 1 through 3; `{"sword": 4}` already has the same meaning as an exact level-4 requirement because no higher sword exists.

```json
{"swordExact": 2}
```

An exact lower-tier requirement can become impossible after Link receives an upgrade, so it should normally be accompanied by `"canRiskPermanentLossOfAccess"`.

### Shield

`shield` requires the given shield level or higher:

```json
{"shield": 2}
```

Shield levels are:

1. Fighter's Shield
2. Fire Shield
3. Mirror Shield

`shieldExact` requires exactly level 1 or 2. `{"shield": 3}` already has exact semantics because no higher shield exists. As with `swordExact`, an exact lower-tier shield requirement should normally be accompanied by `"canRiskPermanentLossOfAccess"`.

### Glove

`glove` requires the given lifting capability or higher:

```json
{"glove": 1}
```

Glove levels are:

- `0`: Ordinary lifting, primarily bushes and other objects that do not require a glove upgrade.
- `1`: Power Glove lifting capability.
- `2`: Titan's Mitt lifting capability.

`{"glove": 0}` requires Link to be in a state that can lift ordinary objects. The exact interaction with future lonk and superbunny state modeling is not yet settled.

## Ammunition Requirements

Ammunition requirements implicitly require the corresponding weapon and a state in which it can be used. Their value is the number of projectiles consumed.

### Arrows

`arrows` consumes the given number of normal arrows and requires a usable bow:

```json
{"arrows": 3}
```

### Silver Arrows

`silverArrows` consumes the given number of arrows and requires the Silver Arrow capability and a usable bow:

```json
{"silverArrows": 1}
```

### Bombs

`bombs` consumes the given number of bombs:

```json
{"bombs": 2}
```

Using a bomb is not possible with a Super Bomb, so any strat that requires a bomb implicitly applies `{"followerLost": ["Super Bomb"]}`. 

It is possible to use a Super Bomb to break a normally bombable wall, but that is not modeled yet by the logic.

## Magic Requirements

Magic is modeled as a normalized resource pool. Link has a base maximum of 128 magic. With Half Magic, the maximum is instead 256 and all magic refills provide twice their listed amount. Costs are not divided.

Magic uses are applied sequentially. Between required uses, Link may consume a Green Potion or Blue Potion to refill his magic before continuing. The potion is removed from its bottle when consumed.

Link must remain at or above 0 magic at all times. A use may leave Link with exactly 0 magic, after which he may drink a potion before the next use, but a use that would reduce his magic below 0 cannot be performed.

Most magic requirements give a number of uses. The total magic cost is the number of uses multiplied by the base cost:

| Requirement | Item or capability | Base cost per use |
|---|---|---:|
| `lamp` | Lamp | 4 |
| `magicPowder` | Magic Powder | 8 |
| `redCane` | Cane of Somaria | 8 |
| `fireRod` | Fire Rod | 16 |
| `iceRod` | Ice Rod | 16 |
| `rod` | Either rod | 16 |
| `bombos` | Bombos | 32 |
| `ether` | Ether | 32 |
| `quake` | Quake | 32 |

For example, this requirement consumes 48 magic using the Fire Rod:

```json
{"fireRod": 3}
```

`rod` allows the given number of shots from either the Fire Rod or Ice Rod, whichever can perform the interaction.

Using Bombos, Ether, or Quake also implicitly requires `{"sword": 1}`.

### Blue Cane

`blueCane` requires the Cane of Byrna and directly specifies the total modeled magic cost:

```json
{"blueCane": 32}
```

Activating the Cane of Byrna costs 20 magic, after which it drains magic in increments of 4. Values include the full magic usage requires by the strat.

### Cape

`cape` requires the Magic Cape and directly specifies the total modeled magic cost:

```json
{"cape": 28}
```

The Cape has no startup cost but drains magic more quickly than the Cane of Byrna.

## Damage

A `damage` object represents Link taking one or more hits. It has the following properties:

- `enemy`: The enemy or hazard dealing damage.
- `attack`: The named attack dealing damage. This is optional.
- `count`: The number of hits taken.

```json
{"damage": {
  "enemy": "Beamos",
  "attack": "Beamos Laser Beam",
  "count": 2
}}
```

If `attack` is present, each hit uses that attack's `dmgToLink` value. Otherwise, each hit uses the enemy's `dmgToLink` value. The applicable mail reduces each hit according to the values in the [enemy data documentation](enemies.md). Eight damage equals one heart.

Hits are applied one at a time. If a hit reduces Link to zero health or below, a bottled Fairy may be consumed to revive him with 7 hearts before the next hit is applied.

For example, suppose Link has 1 heart and takes two 2-heart hits. The first hit reduces him to zero, a bottled Fairy revives him to 7 hearts, and the second hit leaves him with 5 hearts. Treating the two hits as one combined 4-heart damage event would produce the wrong result.

The requirement fails if Link cannot survive all hits, including any available Fairy revivals.

## Refills

A `refill` object represents gaining a resource from the environment. It contains:

- `type`: The resource or refill being gained.
- `limit`: The maximum amount available.

```json
{"refill": {
  "type": "Health",
  "limit": 4
}}
```

The refill is applied when its requirement is evaluated, up to the listed limit and the applicable carrying capacity.

The unit represented by `limit` depends on the refill type:

- `Health`: Hearts.
- `Magic`: Normalized magic points. Half Magic doubles the amount received.
- `Arrows`: Individual arrows.
- `Bombs`: Individual bombs.
- `Rupee`: Individual rupees.
- `Fairy`, `Bee`, `GoldBee`, `RedPotion`, `GreenPotion`, and `BluePotion`: Number of instances available.

Bottle contents require an empty bottle to collect. A Fairy can instead be used immediately to restore 7 hearts, or it can be caught in an empty bottle if Link has and is in a state where he can use the Bug-Catching Net.

## Rupees

A `pay` object consumes the given number of rupees:

```json
{"pay": 110}
```

The requirement fails if Link does not have enough rupees.

## Resource-State Checks

`resourceMissingAtMost` checks how much of one or more resources Link is missing relative to their current maximum. It does not consume or restore anything.

Each entry has the following properties:

- `type`: The resource to check.
- `count`: The maximum amount of that resource that may be missing.

```json
{"resourceMissingAtMost": [
  {"type": "Health", "count": 0}
]}
```

This example requires Link to be at full health.

## Proficiency Requirements

Proficiency requirements compare a strat's expected difficulty against the consumer's configured skill assumptions. The configured proficiency must be at least the specified value.

The available proficiencies are:

- `combatProficiency`: Fighting or avoiding normal enemies.
- `bossProficiency`: Fighting bosses.
- `darkProficiency`: Navigating dark rooms without the Lamp.

```json
{"combatProficiency": 3}
```

The meanings of individual tiers are defined in [`tech.json`](../tech.json).

## Flags

`flag` requires a persistent game flag to be set:

```json
{"flag": "OpenedSkullWoods"}
```

`notFlag` requires a persistent game flag not to be set, and should normally be accompanied by `"canRiskPermanentLossOfAccess"`:

```json
{"notFlag": "DefeatedAgahnim1"}
```

Flags are defined in [`items.json`](../items.json).

## Pendants

`pendants` requires Link to have at least the given number of distinct pendants:

```json
{"pendants": 3}
```

The value can range from 0 through 3.

## Crystals

`crystals` requires Link to have at least the given number of distinct crystals:

```json
{"crystals": 7}
```

The value can range from 0 through 7.

## Followers

Link can have at most one follower at a time. The modeled follower values are `"Zelda"`, `"Old Man"`, `"Blind"`, `"Dwarf"`, `"Purple Chest"`, and `"Super Bomb"`. The Frog is represented as `"Dwarf"`; his transformation does not create a separate follower state. Area-local characters such as Kiki and the sign-cutting NPC are handled by their room logic rather than the general follower state.

A `follower` object checks Link's current follower:

```json
{"follower": "Dwarf"}
```

The special value `"None"` requires Link to have no follower.

`followerLost` represents an action that causes any of the listed followers to stop following Link:

```json
{"followerLost": ["Zelda", "Purple Chest"]}
```

This requirement is always fulfilled. If Link's current follower is in the array, that follower is removed before the next requirement is evaluated. If Link has no follower or his current follower is not listed, his follower state is unchanged.

### Implicit Follower Behavior

Consumers apply the following follower behavior implicitly; room data does not need to repeat these requirements on every affected strat:

- A `bombs` requirement is not valid with a Super Bomb follower, see [Bombs](#bombs).
- Entering caves, houses, and dungeons applies the follower rules defined for [entrance connections](connections.md#follower-behavior-at-entrances). A drop entrance bypasses the follower restrictions of an ordinary door entrance for every follower except the Super Bomb.
- Collecting a crystal implicitly requires that Zelda is not the current follower; Zelda can collect a pendant.
- Death or save-and-quit removes Blind or the Super Bomb if either is Link's current follower.

Death and save-and-quit transitions are outside the current route-state model. Consumers implementing them should apply the follower loss above; see [Death and save-and-quit spawn points](respawn-points.md) for restart destination rules.

## Obstacles

`obstaclesCleared` requires every named room-local obstacle to be in its cleared state:

```json
{"obstaclesCleared": ["Blue Pegs Down"]}
```

`obstaclesNotCleared` requires every named obstacle to be in its reset state:

```json
{"obstaclesNotCleared": ["Blue Pegs Down"]}
```

Obstacle state persists while Link remains anywhere within the same room file and resets upon exiting that file. See [Strats: Obstacles](strats.md#obstacles) for the complete state model.

## Unlocking Doors

`unlockDoor` refers to one entry in the room's `lockedDoors` array:

```json
{"unlockDoor": 1}
```

If the door is already unlocked, the requirement succeeds without further cost. Otherwise:

- A `"big"` lock requires the Big Key, does not consume it, and becomes unlocked.
- A `"small"` lock requires and consumes one Small Key, and becomes unlocked.
- Every other lock type must have been unlocked previously by a strat's `unlocksDoor` effect.

See [Strats: Unlocking Doors](strats.md#unlocking-doors) for more detail.
