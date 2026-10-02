# Room Data

The `rooms` folder contains the layout and navigation logic for individual areas in *The Legend of Zelda: A Link to the Past*. Each JSON file represents one logical room: an overworld area, an entire cave or house, a dungeon, or a special world area.

Room boundaries are chosen for the needs of the logical model. A room file can contain several in-game rooms, floors, or sub-areas when their state and navigation are most useful to model together.

## Folder Structure

Room files are organized into the following folders:

- `overworld`: Light World and Dark World overworld areas.
- `caves/light` and `caves/dark`: Cave interiors associated with each world.
- `houses/light` and `houses/dark`: House and shop interiors associated with each world.
- `dungeons/light` and `dungeons/dark`: Dungeons associated with each world.
- `special`: Areas that behave internally somewhat like overworld areas but behave similarly to underworld transitions.

`Cave`, `House`, and `Dungeon` are organizational room types. They use the same underworld routing model. A room's folder and filename are conveniences for browsing the repository and are not substitutes for its explicit IDs and properties.

Dungeons and large overworld areas also contain `roomDiagrams`. These images show how nodes are arranged and connected but do not define logical behavior.

## Room Structure

Room files follow [`z3-room.schema.json`](../schema/z3-room.schema.json). A room can contain the following top-level properties:

- `$schema`: The relative path to the room schema.
- `id`: The room's ID within its room-ID space.
- `name`: The room's name.
- `roomType`: `Overworld`, `Cave`, `House`, `Dungeon`, or `Special`.
- `note`: General information about the room.
- `position`: The upper-left position of an overworld room on the 8×8 overworld layout.
- `size`: The width and height of an overworld room measured in screens.
- `nodes`: Logical positions or conditions within the room.
- `items`: Item locations in the room.
- `lockedDoors`: Locks that can change from locked to unlocked.
- `obstacles`: Other mutable state local to the room file.
- `strats`: Actions and traversal logic connecting the room's nodes.

The required properties are `id`, `name`, `roomType`, `nodes`, and `strats`.

### Example

```json
{
  "$schema": "../../../schema/z3-room.schema.json",
  "id": 34,
  "name": "Dam",
  "roomType": "Cave",
  "nodes": [
    {
      "id": 1,
      "name": "Entrance",
      "nodeType": "door"
    },
    {
      "id": 2,
      "name": "Control Room",
      "nodeType": "junction"
    }
  ],
  "strats": [
    {
      "link": [1, 2],
      "name": "Base",
      "requires": []
    }
  ]
}
```

## Room IDs

Overworld and underworld rooms use separate ID spaces.

- Overworld room IDs range from 1 through 40.
- Cave, House, Dungeon, and Special rooms share the underworld room-ID space.
- Special rooms are treated as underworld rooms and currently follow the other underworld rooms at IDs 102 through 104.

Room IDs are unique within their respective ID space, not across both spaces. References to a room must therefore include enough context to distinguish an overworld room from an underworld room.

The hexadecimal prefix on an overworld filename reflects its position in the overworld layout. Similar prefixes on overworld and cave filenames make commonly associated vanilla entrances easier to find, but the filename prefix is not a stable connection identifier. Some caves span or connect through multiple overworld areas.

## Overworld Geometry

Every overworld room defines `position` and `size`.

`position` is an `[x, y]` pair identifying the upper-left location of the room on the 8×8 overworld layout:

```json
"position": [5, 6]
```

`size` is a `[width, height]` pair using the dimensions commonly called screens by the community. A normal overworld room is 2×2, while a large room is 4×4:

```json
"size": [4, 4]
```

## Nodes

A node represents a meaningful position and possibly state within a room file. Nodes are introduced wherever the model needs in order to define routing or state changes. They do not necessarily correspond one-to-one with in-game rooms.

[Strats](strats.md) describe actions that move between nodes or change state while remaining at the same node.

Every node has:

- `id`: An integer unique within the room file.
- `name`: A descriptive name unique within the room file.

Underworld nodes also have `nodeType`. Overworld nodes instead have `world` and can contain properties describing overworld connections.

### Respawn Points

Two node properties, `spawnPoint` and `rememberedSpawnPoint`, identify respawn destinations. They label the node where Link arrives; tracking when these spawn points are usable is up to the implementor.

`spawnPoint` identifies one of the four regular destinations. The unlock requirements below describe normal vanilla progression; availability depends on the current story stage, which out-of-order events can replace.

| Value | Destination | Unlock Requirement |
| --- | --- | --- |
| `house` | Link's house | Completing Zelda's Sanctuary dialogue. |
| `sanctuary` | Sanctuary | Completing Zelda's Sanctuary dialogue. |
| `mountainCave` | Old Man's House | Completing Zelda's Sanctuary dialogue, while Link has the Magic Mirror. |
| `pyramid` | Pyramid | After defeating Agahnim 1. This destination uses the Dark World even though its node has `world: "both"`. |

Link's House is the initial game spawn, but it is not a selectable option until completing Zelda's Sanctuary dialogue.

Unlocked destinations are not always used. The Light World normally presents a start menu, while the Pyramid is an automatic Dark World destination, never a menu choice.

`rememberedSpawnPoint` identifies a destination for the single remembered checkpoint. Particular events set this checkpoint, replacing the previous one; visiting a marked node does not itself remember it.

Generally:

- If Link dies in a dungeon, he normally respawns at the last entrance he entered from the overworld through a node with `nodeType: "door"` or `nodeType: "drop"`. This can apply before the regular spawn points unlock, though followers and the Opening stage have special rules.
- If Link saves and quits, or dies outside a dungeon, the early game uses the initial house spawn or a remembered checkpoint. Once the regular spawns are enabled, these restarts normally show the Light World menu or automatically use the Pyramid in the Dark World. Before the Post-Agahnim story stage, restarts use Light World rules even if Link was in the Dark World.

This is a simplified description of the vanilla spawn points. Story stage, current followers, and the remembered checkpoint can override these general rules. Randomizer implementors who change early-game progression need to account for these interactions. See [Death and save-and-quit spawn points](respawn-points.md) for the complete rules and exceptions.

### Sub-areas

`subArea` groups nodes within a large cave or dungeon for organizational purposes. It has no direct logical effect.

```json
{
  "id": 1,
  "name": "Main Entrance",
  "subArea": "Tower of Hera (Lower)",
  "nodeType": "door"
}
```

### Notes

`note` contains information useful to consumers or players interpreting the node. `devNote` contains implementation details, known limitations, or unfinished modeling work primarily relevant to contributors.

## Underworld Node Types

Underworld and Special-room nodes require a `nodeType`. Some node types define connection behavior, while others primarily classify interactions.

### Door

A `door` is an endpoint of a two-way connection between the underworld and overworld.

```json
{
  "id": 1,
  "name": "Entrance",
  "nodeType": "door"
}
```

### Drop

A `drop` is the underworld endpoint of a one-way connection from the overworld, such as falling through a hole. It can be used to enter the underworld room but not to return through the same connection.

```json
{
  "id": 1,
  "name": "Drop Entrance",
  "nodeType": "drop"
}
```

### Junction

A `junction` is an internal routing point with no special built-in connection behavior. Junctions represent a physical location and possibly a state worth distinguishing from nearby nodes.

### Boss and Pre-boss

A `boss` represents the final or currently vulnerable phase of a boss fight. A `pre-boss` is basically a junction within a boss fight; it typically represents a distinct preliminary phase, such as breaking Helmasaur's mask or thawing Kholdstare.

If collecting a pendant or crystal immediately exits the dungeon through a dungeon's entrance, the boss node has `killExitNode`. This property identifies the underworld door node through which the automatic exit occurs:

```json
{
  "id": 11,
  "name": "Moldorm Boss",
  "nodeType": "boss",
  "killExitNode": 1
}
```

Link does not arrive at the referenced underworld node. The automatic exit follows that node's external connection and places Link at its overworld endpoint.

Useful one-time boss teleports are modeled explicitly instead. The boss routes through a junction to an `event` node connected to the teleport destination. Normal pendant and crystal exits are also one-time, but are not modeled as events because their movement is not considered useful.

### Event

An `event` represents a special scripted interaction or transition. Current event nodes are used for useful one-time teleports from the underworld to the overworld.

### Interaction Types

The following node types classify specialized interactions but do not by themselves define traversal behavior:

- `shop`: A shop interaction.
- `minigame`: A minigame interaction.
- `fortune`: A fortune-teller interaction.

## Overworld Nodes

Overworld nodes represent logical areas on an overworld screen. They do not use `nodeType`. Every overworld node has a `world` property:

- `"light"`: The node exists in the Light World.
- `"dark"`: The node exists in the Dark World.
- `"both"`: The corresponding logical area exists in both worlds.

For every node with `"world": "both"`, there is an implicit strat to use the Magic Mirror from the Dark World to the Light World. See [Strats: Worlds](strats.md#worlds).

An overworld node can also contain transitions, entrances, whirlpools, teleports, or a flute destination.

### Transitions

`transitions` describes places where Link can cross an edge of the overworld room. Each transition can have:

- `edge`: `north`, `south`, `east`, or `west`.
- `span`: The start and end of the usable interval along that edge, measured in 16×16 tiles. Half-tile precision is used when needed.
- `terrain`: Additional terrain information, defined if the terrain is not land.
- `world`: A Light World or Dark World restriction, defined if the transition is not in both worlds.

```json
{"edge": "east", "span": [50.5, 53.5], "terrain": "water"}
```

Transition geometry may or may not be useful to overworld randomizer projects. Consumers may use it for overworld matching, teleport placement, visualization, camera positioning, etc.

### Entrances

`entrances` identifies endpoints used by [`connections/entrances.json`](../connections/entrances.json). Each entrance has:

- `id`: An entrance ID unique within the overworld room.
- `name`: A descriptive name.
- `world`: The world containing the endpoint.

An entrance connects an overworld node to an underworld `door` or `drop`. Door connections are two-way; drop connections go only from the overworld to the underworld.

### Whirlpools

`whirlpools` identifies endpoints paired by [`connections/whirlpools.json`](../connections/whirlpools.json). Each endpoint has a room-local whirlpool ID, descriptive name, and world. Whirlpool connections are two-way and connect one overworld node to another.

### Teleports

`teleports` identifies overworld destinations for special one-way connections from the underworld. Each destination has a room-local teleport ID, descriptive name, and world. The corresponding connections are defined in [`connections/teleports.json`](../connections/teleports.json).

### Flute Locations

`fluteLocation` identifies one of the eight flute destinations and is a property of the node where Link arrives:

```json
{
  "id": 1,
  "name": "Link's House",
  "world": "both",
  "entrances": [
    {
      "id": 1,
      "name": "Link's House",
      "world": "light"
    },
    {
      "id": 2,
      "name": "Big Bomb Shop",
      "world": "dark"
    }
  ],
  "fluteLocation": 4
}
```

Using a flute destination requires an active flute and must begin on a Light World overworld screen.

Entrance, whirlpool, and teleport IDs each use their own room-local namespace. For example, `entranceId: 1` and `teleportId: 1` may coexist in the same overworld room.

## Items

The optional `items` array defines item locations within a room. Each item has:

- `id`: An item-location ID unique within the room and referenced by a strat's `collectsItems`.
- `locationName`: A descriptive name for the location.
- `itemLocation`: The node most naturally associated with collecting the item.
- `item`: The vanilla item or item receipt at the location.
- `itemAddress`: One or more ROM addresses involved in encoding the item at the location.
- `subArea`: Organizational context within an underworld room.
- `world`: The world containing an overworld item.
- `devNote`: Contributor-facing implementation detail.

```json
{
  "id": 1,
  "locationName": "Five Chest Room - Far Left",
  "itemLocation": 4,
  "item": "TwentyRupees",
  "itemAddress": "0xEB2A"
}
```

`itemLocation` is the node where the item is most likely or natural to collect. It is not a routing constraint; a strat associated with another nearby link may collect the item.

Items are never collected automatically by reaching their `itemLocation`. A strat must explicitly include the item's ID in `collectsItems`. See [Strats: Collecting Items](strats.md#collecting-items).

Most item locations have one `itemAddress`. Dungeon-prize locations have six addresses; the six `prizePatchBytes` from the selected [dungeon-prize definition](items.md#dungeon-prizes) are written to those addresses in order.

## Locked Doors

The optional `lockedDoors` array defines doors, walls, or other locks whose state can change from locked to unlocked. Each locked door has:

- `id`: A locked-door ID unique within the room and referenced by `unlockDoor` or `unlocksDoor`.
- `locationName`: A descriptive name.
- `doorLocation`: The node most naturally associated with the door.
- `doorPosition`: The wall orientation: `north`, `south`, `east`, `west`, or `middle`.
- `keyType`: The normal unlocking method.
- `subArea`: Organizational context within an underworld room.
- `world`: The world containing an overworld lock.
- `devNote`: Contributor-facing implementation detail.

Like `itemLocation`, `doorLocation` identifies the most natural associated node. It does not require every interaction with the door to occur from that node.

`doorPosition` describes the wall the door occupies, not the door's broad location within the room. A door on a north-facing wall remains `"north"` even if the wall is near the southern end of a room. Paired doors usually use opposite orientations, with the recorded orientation chosen from the perspective of the `doorLocation` reference.

The available `keyType` values are:

- `"big"`: Big Key door.
- `"small"`: Small Key door.
- `"bomb"`: Bombable wall.
- `"bomb, boots"`: Can be opened with either Bombs or Pegasus Boots.
- `"boots"`: Opened with Pegasus Boots.
- `"glove"`: Opened by lifting an obstacle.

Some bombable walls can also be broken with the Pegasus Boots, often denoted by a larger crack pattern. Because these are not inherently intuitive, a Boots strat for these locks should include the `canBreakDashableWall` tech.

For locks other than `"big"` and `"small"`, the actual unlocking method and costs are defined by the strat that applies `unlocksDoor`; `keyType` alone is not a complete logical requirement. See [Strats: Unlocking Doors](strats.md#unlocking-doors).

## Obstacles

The optional `obstacles` array declares mutable state local to the room file. Each obstacle has a string `id` and a `note` explaining what its cleared state means.

```json
{
  "id": "Drained Floodgate",
  "note": [
    "The Floodgate has been drained."
  ]
}
```

Obstacle state persists across every node in the file and resets when Link exits the file. Strats clear or reset obstacles, while logical requirements test their current state. See [Strats: Obstacles](strats.md#obstacles).

## Strats

Every room contains a `strats` array defining its actions and traversal logic. A strat's `link` refers to node IDs in the same room file. See the [Strats documentation](strats.md) for the complete format.
