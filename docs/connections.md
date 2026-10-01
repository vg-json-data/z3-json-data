# Connection Data

The `connections` folder defines traversal between room files. Room files describe movement within an area and identify possible connection endpoints; connection files pair those endpoints to create edges between rooms.

Connections do not contain logical requirements. All items, resources, techniques, and state needed to reach or use an endpoint are modeled by [strats in the room files](strats.md). Once an endpoint is reachable, the corresponding connection supplies the inter-room traversal described below.

## Folder Structure

Connection data is divided by behavior:

- [`entrances.json`](../connections/entrances.json) connects overworld entrances to underworld doors and drops.
- [`teleports.json`](../connections/teleports.json) defines one-way movement from the underworld to the overworld.
- [`whirlpools.json`](../connections/whirlpools.json) pairs two overworld whirlpools.

Each file contains:

- `$schema`: The connection files do not currently use a JSON schema, so this is `null`.
- `name`: A descriptive name for the collection.
- `connections`: The connections defined by the file.

## Endpoint References

Connection endpoints refer to data in [room files](rooms.md). The fields used depend on whether the endpoint is in the overworld or underworld.

An overworld entrance reference uses:

```json
{
  "roomName": "Lost Woods",
  "roomId": 1,
  "entranceId": 1
}
```

- `roomId` identifies an Overworld room.
- `entranceId` identifies an entrance nested in one of that room's nodes.
- The node containing that entrance is the logical overworld location reached by the connection.

Teleport and whirlpool endpoints use `teleportId` and `whirlpoolId` in the same way. Entrance, teleport, and whirlpool IDs have separate room-local namespaces.

An underworld reference identifies a node directly:

```json
{
  "roomName": "Lost Woods Hideout",
  "roomId": 1,
  "nodeId": 2
}
```

- `roomId` identifies a Cave, House, Dungeon, or Special room in the shared underworld room-ID space.
- `nodeId` identifies a node within that room.

Overworld and underworld rooms use separate room-ID spaces, so the endpoint type determines which space a `roomId` belongs to.

`roomName` is included only for readability. IDs form the actual reference and should be used to resolve an endpoint.

## Entrances

Each entry in `entrances.json` connects one overworld entrance to one underworld node.

```json
{
  "type": "door",
  "world": "light",
  "overworld": {
    "roomName": "Lost Woods",
    "roomId": 1,
    "entranceId": 1
  },
  "underworld": {
    "roomName": "Lost Woods Hideout",
    "roomId": 1,
    "nodeId": 2
  }
}
```

An entrance connection has:

- `type`: `door` or `drop`.
- `world`: The world containing the overworld endpoint: `light` or `dark`.
- `overworld`: A reference to an entrance in an Overworld room.
- `underworld`: A reference to a node in an underworld room.

### Doors and Drops

A `door` is a two-way connection and references an underworld `door` node. A `drop` references an underworld `drop` node and is one-way from the overworld to the underworld.

## Teleports

Each entry in `teleports.json` defines a one-way connection from an underworld node to an overworld teleport destination.

```json
{
  "type": "teleport",
  "fromWorld": "light",
  "toWorld": "dark",
  "underworld": {
    "roomName": "Agahnim's Tower",
    "roomId": 61,
    "nodeId": 12
  },
  "overworld": {
    "roomName": "Hyrule Castle",
    "roomId": 18,
    "teleportId": 1
  }
}
```

A teleport connection has:

- `type`: Always `teleport`.
- `fromWorld`: Link's world state before using the teleport.
- `toWorld`: Link's world state after using the teleport and the world containing the destination.
- `underworld`: A reference to the source node in an underworld room.
- `overworld`: A reference to a teleport destination in an Overworld room.

Underworld rooms do not define a world of their own, but Link's route retains its current world state while inside them. `fromWorld` and `toWorld` therefore make both same-world and world-changing teleports explicit.

## Whirlpools

Each entry in `whirlpools.json` pairs two overworld whirlpool endpoints.

```json
{
  "type": "whirlpool",
  "world": "light",
  "overworld": {
    "roomName": "Waterfall of Wishing",
    "roomId": 7,
    "whirlpoolId": 1
  },
  "overworld2": {
    "roomName": "Lake Hylia",
    "roomId": 35,
    "whirlpoolId": 1
  }
}
```

A whirlpool connection has:

- `type`: Always `whirlpool`.
- `world`: The world containing both endpoints: `light` or `dark`.
- `overworld`: A reference to one overworld whirlpool.
- `overworld2`: A reference to the other overworld whirlpool.

Whirlpools are two-way. The `overworld` and `overworld2` labels distinguish the two stored endpoints but do not give the connection a direction.
