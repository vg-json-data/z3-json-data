# Strats

Strats represent ways to perform one or more actions in a room. A strat may move Link from one node to another, modify logical state, or do both.

Strats are usually presented in an array of strats. Multiple strats with the same link represent alternative ways to accomplish roughly the same result.

## Structure

A `strat` can have the following properties:

- `link`: The IDs of the starting and ending nodes, in that order.
- `name`: The name of the strat.
- `requires`: The logical requirements that must be fulfilled to execute the strat.
- `collectsItems`: The IDs of items in the room that are collected by executing the strat.
- `grantsItems`: Item receipt names granted by executing the strat, without collecting a room-local item location.
- `setsFlags`: Game flags that are set by executing the strat.
- `clearsObstacles`: Room-local obstacles that are cleared by executing the strat.
- `resetsObstacles`: Room-local obstacles that are returned to their reset state by executing the strat.
- `unlocksDoor`: The IDs of locked doors in the room that are unlocked by executing the strat.
- `world`: The world in which an overworld strat can be executed.
- `fromWorld` and `toWorld`: The starting and ending worlds of an overworld strat that changes worlds.
- `isBunny`: Indicates whether the strat can be executed while Link is a bunny.
- `setsFollower`: Sets Link's current follower.
- `FollowerComplete`: Completes the current follower interaction and removes that follower.
- `exitState`: Carries a temporary state out of the room.
- `entranceState`: Requires a matching temporary state when entering the room.
- `note`: Information useful to someone interpreting or performing the strat.
- `detailNote`: An array of strings with additional player-facing detail, such as setup steps, beyond the summary in `note`.
- `devNote`: Information primarily useful while developing the data.

### Example

Here is a simple strat that moves from node 1 to node 2:

```json
{
  "link": [1, 2],
  "name": "Base",
  "requires": [
    "Hammer"
  ]
}
```

## Links

The `link` property is an array containing the starting node ID followed by the ending node ID. Strats are directional: a strat with `"link": [1, 2]` does not imply that the same strat can be executed from node 2 to node 1.

A strat whose link begins and ends at the same node performs its actions without any modeled movement:

```json
{
  "link": [1, 1],
  "name": "Heart Pot",
  "requires": [
    {"refill": {"type": "Health", "limit": 1}}
  ]
}
```

This does not define a special category of actions. A strat that moves between different nodes may collect items, set flags, change obstacles, unlock doors, or produce any other effect that a same-node strat can produce; it also moves Link to the ending node.

## Logical Requirements

Every strat has a `requires` array containing the [logical requirements](logicalRequirements.md) that must be fulfilled to execute it. An empty array means that the strat has no explicit logical requirements.

Requirements are evaluated sequentially in the order in which they appear. In most cases this is equivalent to combining all requirements with logical AND, but the order must be preserved because some requirements consume or restore resources.

After all requirements have been fulfilled, the strat is executed and its effects are applied. An item collected or flag set by a strat cannot satisfy an earlier requirement in that same strat; the resulting state is available to subsequent strats.

An item requirement can include implicit conditions needed to use that item, in addition to requiring that the item be in the inventory. The complete interaction between item use and Link's normal, bunny, superbunny, and lonk states is not yet modeled.

## Notable Strats

A notable is a room-specific technique that consumers can enable or disable individually, like a tech scoped to one room.

Define techniques in the room's optional `notables` array. Each entry has a stable positive integer `id`, a `name`, and a descriptive `note`, with optional `detailNote` and `devNote`. IDs and names must each be unique within the room; other rooms may reuse them. When `notables` is present, `nextNotableId` must also be included and must be greater than all existing notable IDs.

```json
"notables": [
  {
    "id": 1,
    "name": "Icebreaker",
    "note": ["Use the red cane to walk through the barrier in the Ice Palace Big Key Chest Room."]
  }
],
"nextNotableId": 2
```

A strat opts into this technique through its requirements:

```json
"requires": [
  {"notable": "Icebreaker"},
  {"redCane": 1}
]
```

The notable requirement succeeds only when that room's technique is enabled by the consumer. It alone consumes no resources and supplies no implicit item or proficiency requirements. Multiple strats can share a notable, and notable requirements may appear inside `and` or `or`.

## Worlds

Overworld nodes and strats can apply to the Light World, the Dark World, or both worlds.

For a strat that begins and ends in the same world, `world` has one of the following values:

- `"light"`: The strat can be executed in the Light World.
- `"dark"`: The strat can be executed in the Dark World.
- `"any"`: The strat can be executed in either world.

`"any"` does not allow the strat to move from one world to the other. A strat that changes worlds instead uses `fromWorld` and `toWorld`:

```json
{
  "link": [1, 1],
  "fromWorld": "dark",
  "toWorld": "light",
  "name": "Base",
  "requires": [
    "MagicMirror"
  ]
}
```

For every overworld node with `"world": "both"`, there is an implicit strat to use the Magic Mirror from the Dark World to the Light World, as in the example above.

The underworld is represented differently from the two overworlds. Cave, house, dungeon, and special-room strats do not use `world`, `fromWorld`, or `toWorld`; these properties are incompatible with underworld strats.

## Bunny Compatibility

The `isBunny` property describes whether a strat is compatible with bunny state:

- `"yes"`: The strat requires bunny state.
- `"no"`: The strat requires non-bunny state.
- `"any"`: The strat is known to work in either state.

If `isBunny` is omitted, bunny compatibility has not been tested. Consumers should conservatively treat an omitted value as `"no"`.

This is currently a coarse model. Detailed interactions between normal Link, bunny, superbunny, and lonk states have not yet been fully represented.

## Collecting Items

The `collectsItems` property is an array of IDs referencing entries in the room's `items` array. Each referenced item is collected when the strat is completed.

```json
{
  "link": [8, 8],
  "name": "Base - Collect Item",
  "requires": [],
  "collectsItems": [1]
}
```

Collected items become available after the strat is complete and can satisfy requirements in subsequent strats.

Alternatively, `grantsItems` is used on a repeatable strat that grants an item without using a room-local item location:

```json
{
  "link": [2, 2],
  "name": "Buy Blue Shield",
  "requires": [
    {"pay": 50}
  ],
  "grantsItems": ["BlueShield"]
}
```

## Setting Flags

The `setsFlags` property contains game flags that are set when the strat is completed. Flags are defined in [`items.json`](../items.json) and represent persistent game events.

```json
{
  "link": [10, 9],
  "name": "Open Skull Woods",
  "requires": [
    {"fireRod": 1}
  ],
  "setsFlags": ["OpenedSkullWoods"]
}
```

## Obstacles

Obstacles represent mutable state local to a room file. A strat may clear obstacles with `clearsObstacles` or return them to their reset state with `resetsObstacles`.

```json
{
  "link": [2, 2],
  "name": "Open The Floodgates",
  "requires": [],
  "clearsObstacles": ["Drained Floodgate"]
}
```

Obstacle state persists while Link moves among any of the nodes and sub-areas represented by the same room file. When Link exits that file, its obstacle state is discarded. Entering another file, including moving to another overworld screen, initializes that file's obstacles in their reset state.

An entrance-state strat can use state carried from the previous room to reproduce a corresponding effect in the newly entered room. This does not make the obstacle itself global; each room file still has its own local obstacle state.

Logical requirements can test obstacle state with `obstaclesCleared` and `obstaclesNotCleared`.

## Unlocking Doors

Locked doors are defined in the room's `lockedDoors` array. The `unlockDoor` logical requirement and the `unlocksDoor` strat property have related but distinct purposes.

An `unlockDoor` requirement refers to one locked-door ID:

```json
{"unlockDoor": 1}
```

If the door is already unlocked, the requirement is fulfilled without an additional cost. Otherwise, behavior depends on the door's `keyType`:

- `"big"`: Requires the Big Key. The Big Key is not consumed, and the door becomes unlocked.
- `"small"`: Requires and consumes one Small Key, and the door becomes unlocked.
- Any other lock type: The requirement cannot unlock the door. A previous strat must already have unlocked it.

After a door is unlocked, it remains unlocked permanently.

The `unlocksDoor` property is a post-strat effect containing one or more locked-door IDs:

```json
{
  "link": [1, 1],
  "name": "Base - Bomb North Wall",
  "requires": [
    {"bombs": 1}
  ],
  "unlocksDoor": [1]
}
```

Because `unlocksDoor` is applied after a strat is completed, it cannot unlock a non-key door in time for an `unlockDoor` requirement in that same strat. The unlocking action and subsequent traversal must be represented by separate strats unless the interaction is modeled another way.

## Followers

Link can have at most one follower at a time. `setsFollower` sets the named follower when the current state permits it, while `FollowerComplete` completes the named follower interaction and removes that follower.

```json
{
  "link": [1, 1],
  "name": "Return Blacksmith",
  "requires": [
    {"follower": "Dwarf"}
  ],
  "setsFlags": ["RescuedBlacksmith"],
  "followerComplete": "Dwarf"
}
```

Followers persist until an explicit completion or loss effect removes them. A [`followerLost`](logicalRequirements.md#followers) logical element removes the current follower when it is one of the followers named by that element. Standard interactions such as dashing, bombing, collecting crystals, and traversing entrances also have [implicit follower behavior](logicalRequirements.md#implicit-follower-behavior), so individual strats do not repeat those requirements.

Blind and the Super Bomb are also lost on death or save-and-quit.

## Entrance and Exit State

The `exitState` and `entranceState` properties connect special behavior across room-file boundaries, through either an overworld-underworld entrance or an overworld-overworld screen transition. An exit-state strat leaves through an entrance or transition on the `"to"` node of its `link` with a named temporary state. A compatible entrance-state strat receives that state through an entrance or transition on the `"from"` node of its `link` in the next room. The state type determines which kind of connection it uses, as described below.

For example, the Dam can be left with the floodgate drained:

```json
{
  "link": [1, 1],
  "name": "Exit Dam with Water Drained",
  "requires": [
    {"obstaclesCleared": ["Drained Floodgate"]}
  ],
  "exitState": {
    "state": "event",
    "type": "DrainedFloodgate"
  }
}
```

The matching entrance-state strat in Swamp Ruins recreates the effect as room-local obstacle state:

```json
{
  "link": [2, 2],
  "name": "Enter Overworld with Water Drained",
  "world": "light",
  "entranceState": {
    "state": "event",
    "entranceID": 1,
    "type": "DrainedFloodgate"
  },
  "requires": [],
  "clearsObstacles": ["Drained Floodgate"]
}
```

The connection used depends on the state. For `"state": "event"`, an `entranceState` uses an entrance on the `"from"` node of the strat's `link`, and an `exitState` uses an entrance on the `"to"` node. On the overworld side, these event states require `entranceID` to identify that entrance. For `"state": "overhead"`, the corresponding endpoints are overworld screen transitions on those nodes, and no `entranceID` is used; see below.

### Objects Held Overhead

Overworld screen-edge transitions can carry an object held overhead using `"state": "overhead"`. The `type` identifies its thrown-object damage class:

| Type | Objects | Typical damage |
|---|---|---|
| `class1` | Green or purple bushes | 2 |
| `class3` | Brown/yellow bushes, rocks, and signs | 8 |

For overhead-state matching, `class3` is strictly stronger than `class1`: a `class1` entrance requirement can be fulfilled by either type, while a `class3` entrance requirement requires `class3`. When a strat can leave with either strength under the same requirements, only the `class3` exit needs to be listed. Actual damage follows the target enemy's `dmgFromLink` entry for the held object's class. This state describes an object already held overhead; any lifting requirement needed to obtain it belongs in the pickup strat.

An overhead `exitState` leaves through an overworld screen edge at the `"to"` node. An overhead `entranceState` enters through a screen edge at the `"from"` node. Any screen-edge opening on the relevant node can be used, as long as the selected edge variant is valid on that world.

### Implicit Overhead Transition Strats

At every overworld screen transition, consumers must include an implicit same-node strat with both entrance and exit states for each overhead type. Entry and exit may use the same transition or different usable transitions at that node. These implicit strats require `canCrossRoomOverheadPickups` and look like the following example:

```json
[
  {
    "link": [1, 1],
    "name": "Return with Weak Overhead Object",
    "world": "any",
    "entranceState": {"state": "overhead", "type": "class1"},
    "requires": ["canCrossRoomOverheadPickups"],
    "exitState": {"state": "overhead", "type": "class1"}
  },
  {
    "link": [1, 1],
    "name": "Return with Strong Overhead Object",
    "world": "any",
    "entranceState": {"state": "overhead", "type": "class3"},
    "requires": ["canCrossRoomOverheadPickups"],
    "exitState": {"state": "overhead", "type": "class3"}
  }
]
```

## Notes

`note` contains information useful to consumers or players interpreting the strat. `devNote` contains implementation details, known limitations, or unfinished modeling work that is primarily relevant to contributors.
