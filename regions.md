This is just a rough set of notes for now:

# Overworld

## ids

id 1-42 are reserved for overworld rooms. Other rooms need to be reindexed.

## nodes

All entrances on all nodes within an overworld room need to have unique ids, but they do not need to be unique across rooms
All nodes must specify `world` with values `light`, `dark`, or `both`.

## strats

All strats must specify either `world` with values `light`, `dark`, or `any`, or they must specify both a `fromWorld` and a `toWorld` with values `light` or `dark`.
For all nodes with a `"world": "both"`, there is an implicit strat to use the Magic Mirror, for example with Node 1:

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