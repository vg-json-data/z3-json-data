# Overworld Edge Variants

`edgeVariants` is a required top-level property of every `Overworld` room in [`z3-room.schema.json`](../schema/z3-room.schema.json). It describes the edge variants that are supported on each edge of a room and a default choice for each segment.

These values are used when determining how overworld rooms can be shuffled while maintaining logic compatibility. They also describe which retilings are supported by the companion project [ALTTPRetiling](https://github.com/kjbranch/ALTTPRetiling).

Existing node `transitions` describe traversal endpoints; `edgeVariants` does not replace those endpoints or define routing through a retiled room. This project still needs a way to define how edgeVariants, nodes, and their transitions correspond.

## Structure and Ordering

`edgeVariants` directly contains `north`, `south`, `east`, and `west`. Each segment's supported variants, default, and selected choice are shared by Light World and Dark World. All four edges must be defined, including closed edges. Omitting an edge or the entire property is invalid.

The few differences between worlds are represented as distinct specialized variants. For example, `light-pathway-dark-closed` represents a pathway in the Light World and a closed edge in the Dark World. It is one choice describing both worlds together, and follows the same independence rules as other variants.

Each edge is an array of segments. A normal room with a `size` of 2×2 will have a single segment, a 4×4 room has two per side. For those with more than one segment, the ordering is defined as follows:

- North and south segments are ordered west to east.
- East and west segments are ordered north to south.

Each segment requires:

- `supported`: A nonempty list of distinct variant names. List order has no meaning.
- `default`: One of the names in `supported`, chosen as the supported option closest to vanilla.

## Variant Types

| Name | Meaning |
| --- | --- |
| `closed` | No opening. |
| `wide` | A wide opening. |
| `dual-small` | Two small openings. |
| `small-1` | An offset small opening: north on an east/west edge, west on a north/south edge. |
| `small-2` | The opposite offset: south on an east/west edge, east on a north/south edge. |

## Overworld Randomization

To assemble a valid randomized overworld map, every pair of touching edge segments must share at least one supported variant. One shared variant is selected for each touching pair, determining the corresponding edge tilings from ALTTPRetiling. When two large rooms share an entire edge, both pairs of touching segments must match, but each pair can use a different variant.

It is assumed that every supported choice on a segment can be combined with every supported choice on the room's other segments. If a consumer decides to prevent specific combinations, that will be applied outside of this project.

## Examples

These are illustrative fragments showing only the north edge; complete objects must also define `south`, `east`, and `west`:

```json
"edgeVariants": {
  "north": [
    {
      "supported": ["closed", "wide", "small-1"],
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
      "supported": ["closed", "wide", "small-1"],
      "default": "small-1"
    },
    {
      "supported": ["closed"],
      "default": "closed"
    }
  ]
}
```

## Validation

The schema enforces much of the object structure.

Required rules that are not currently checked by the schema or repository validator: `default` must occur in its segment's `supported` list, and segment counts must match the corresponding room dimensions. All variant names should be defined in the ## Variant Types section and each specified edge type should be included in the ALTTPRetiling.
