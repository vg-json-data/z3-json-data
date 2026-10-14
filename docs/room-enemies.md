# Room enemies

Room files use `enemySpawns` to list enemies, with names matching the definitions
in [`enemies/`](../enemies/). Overworld rooms, caves, houses, and special areas include per-enemy
counts; dungeons list unique enemy types without counts.

## Overworld

Overworld lists are separated by world and story stage:

| Profile | When it applies |
| --- | --- |
| `light.beforeZeldaRescue` | Before rescuing Zelda |
| `light.afterZeldaRescue` | After rescuing Zelda, before defeating Agahnim |
| `light.afterAgahnim` | After defeating Agahnim for the first time |
| `dark` | Dark World |

Each profile contains an `enemies` list:

```json
{
  "enemies": [
    {"name": "Crow", "count": 3},
    {"name": "Buzz Blob", "count": 1}
  ]
}
```

`count` is the number of placed enemies of that type. `null` means recurring
spawns with no fixed count, such as Falling Boulder. An optional `note` explains
conditional appearances.

Hidden or dormant enemies and placed hazards are included. Bee hives and extra
enemies generated during play, such as Cucco swarms and summoned guards, are
omitted. Land Mine counts cover fixed placements, not additional random mines.

## Caves, houses, and special areas

Caves, houses, and special areas use the same names-and-counts format, without world or
story-stage profiles:

```json
"enemySpawns": {
  "enemies": [
    {"name": "Rat", "count": 2}
  ]
}
```

Counts cover placed enemies throughout the area. Extra enemies generated
by interactions and environmental hazards such as floor spikes are not
comprehensively included.

## Dungeons

Dungeons list each enemy type once, without counts:

```json
"enemySpawns": {
  "enemies": ["Ganon"]
}
```

Lists include bosses, regular enemies, and cataloged hazards.

Spawned enemies such as Wallmasters and Flying Tiles are included. Ordinary
projectiles, enemies created by item transformations, and environmental hazards
such as floor spikes are omitted.

## Damage requirements

Validation checks that each strat's `damage.enemy` occurs in its room's
`enemySpawns`. Overworld checks use the strat's world, or both worlds for `world: "any"`
and world-changing strats. A Light World enemy must appear in at least one story-stage.

`Fall`, `Ground Spikes`, and Link's own `Bomb` damage are exempt because these
sources are not placed enemies.
