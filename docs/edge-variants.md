# Overworld Edge Variants

`edgeVariants` is a required top-level property of every `Overworld` room in [`z3-room.schema.json`](../schema/z3-room.schema.json). It describes the edge variants that are supported on each edge of a room and a default choice for each segment.

These values are used when determining how overworld rooms can be shuffled while maintaining logic compatibility. They also describe which retilings are supported by the companion project [ALTTPRetiling](https://github.com/kjbranch/ALTTPRetiling).

Each supported variant identifies the local room nodes at its openings. Existing node `transitions` describe vanilla traversal endpoints and geometry; the selected variant's node references describe the endpoints for its retiled edge. Strats still define routing between those nodes inside the room.

All [`exitState` and `entranceState`](strats.md#entrance-and-exit-state) screen transitions require a selected edge variant that includes the relevant endpoint node: the strat's destination node for `exitState`, or its source node for `entranceState`.

## Structure and Ordering

`edgeVariants` directly contains `north`, `south`, `east`, and `west`. Each segment's supported variants, default, and selected choice are shared by Light World and Dark World. All four edges must be defined, including closed edges. Omitting an edge or the entire property is invalid.

The few differences between worlds are represented as distinct specialized variants. For example, `light-only` represents a pathway in the Light World and a closed edge in the Dark World. It is one choice describing both worlds together, and follows the same independence rules as other variants.

Each edge is an array of segments. A normal room with a `size` of 2×2 will have a single segment, a 4×4 room has two per side. For those with more than one segment, the ordering is defined as follows:

- North and south segments are ordered west to east.
- East and west segments are ordered north to south.

Each segment requires:

- `supported`: A nonempty object mapping variant names to ordered arrays of local node references. The order of variant keys has no meaning.
- `default`: One of the keys in `supported`, chosen as the supported option closest to vanilla. It remains a string; node references are defined only in `supported`.

Node arrays run west to east on north/south edges, and north to south on east/west edges, within each segment, except for variants with explicit role ordering below. This is map order, regardless of travel direction. Each entry identifies a local node on this room's side of the connection. Repeat an ID when multiple openings lead to the same node: `"dual-small": [1, 1]` still describes two openings. `"closed": []` has no openings and no node references.

Integer references must identify nodes in the same room. Referenced nodes must exist in both worlds, except for `light-only` and `light-and-mirror`. A `light-only` node must exist in the Light World and may or may not exist in the Dark World; traversal to the neighboring room is only possible while in the Light World. The required worlds for `light-and-mirror` depend on each entry's role, as described below.

For `lake`, references are ordered land then water. The water reference may instead be `"return"`, as in `"lake": [4, "return"]`. This allows entering the room at that opening, but the only available action is to go back to the previous room through the same opening; it does not reference a node in `nodes`. This round trip can reset the previous room, for example for a fake flippers strat.

### Light and Mirror

`light-and-mirror` has exactly three entries, each a local node ID or `null`, ordered by role rather than map position:

1. The ordinary Light World endpoint, used to traverse the edge from the room's accessible Light World area.
2. The Dark World node where Link can use the Mirror to access a blocked area with a transition to the paired room.
3. A blocked area in the Light World which is not accessible through any means except by transitioning from the neighboring room. This is typically an isolated ledge that is only accessible after using the Mirror in the previous room and then transitioning.

For non-null entries, the first and third nodes must exist in the Light World; the second must exist in the Dark World. A node may also exist in the other world, and IDs may repeat when their roles share a node. `null` means there is no local node for that role. Typically, a room used only as a Mirror source for reaching the neighboring room's normally unreachable endpoint will have its third entry null, while the destination room will have its second entry null.

In addition, traversal from entry 2 to the neighboring room's entry 3 implicitly requires use of the Mirror.

The cross-world route is directed: reaching entry 3 does not imply a return to entry 2 in the previous room. Reverse traversal may or may not exist and if it does it needs its own explicit logic.

## Variant Types

| Name | Meaning | Number of node references |
| --- | --- | --- |
| `closed` | No opening. | 0 |
| `wide` | A wide opening. | 1 |
| `dual-small` | Two small openings. | 2 |
| `small-1` | An offset small opening: north on an east/west edge, west on a north/south edge. | 1 |
| `small-2` | The opposite offset: south on an east/west edge, east on a north/south edge. | 1 |
| `light-only` | A transition that only exists in the Light World. | 1 |
| `land-water-land` | Land on both sides with a river in the middle. | 3 |
| `vertical-water-land` | A vertical transition with a river on the left. | 2 |
| `horizonal-water-land` | A horizontal transition with a river on the top. | 2 |
| `horizontal-land-water` | A horizontal transition with a river on the bottom. | 2 |
| `split-house` | A transition with a house split in half and a land walkway south of it. | 1 (For the walkway) |
| `lake` | A wide land opening alongside a lake, matching Great Swamp Lake. | 2 |
| `light-and-mirror` | A Light World traversal plus a one-way traversal only reachable by mirroring from the Dark World in the adjacent room. | 3 |

## Overworld Randomization

To assemble a valid randomized overworld map, every pair of touching edge segments must share at least one supported variant. One shared variant is selected for each touching pair, determining the corresponding edge tilings from ALTTPRetiling. When two large rooms share an entire edge, both pairs of touching segments must match, but each pair can use a different variant.

It is assumed that every supported choice on a segment can be combined with every supported choice on the room's other segments. If a consumer decides to prevent specific combinations, that will be applied outside of this project.

## Examples

These are illustrative fragments showing only the north edge; complete objects must also define `south`, `east`, and `west`:

```json
"edgeVariants": {
  "north": [
    {
      "supported": {"closed": [], "wide": [1], "dual-small": [1, 2], "small-1": [1]},
      "default": "small-1"
    }
  ]
}
```

A large room's north edge has a western segment and an eastern segment, with the eastern segment always closed in this example:

```json
"edgeVariants": {
  "north": [
    {
      "supported": {"closed": [], "wide": [1], "small-1": [1]},
      "default": "small-1"
    },
    {
      "supported": {"closed": []},
      "default": "closed"
    }
  ]
}
```

## Validation

The schema enforces variant names, positive integer node IDs, and the exact reference count for each variant, along with the required object structure. It also permits `"return"` as the second reference for `lake`, and `null` in any of the three entries for `light-and-mirror`. Duplicate node IDs are allowed because separate openings can share a node.

The repository validator checks that each referenced node ID exists in the room and the appropriate worlds, that `default` is a key in `supported`, and that segment counts match room dimensions.
