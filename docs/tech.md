# Tech Data

[`tech.json`](../tech.json) defines optional player techniques and proficiency assumptions used by the logical model. Consumers can configure these values to build custom difficulty levels for players or randomizers without rewriting room logic.

Tech requirements are referenced from normal logical requirement lists. A tiered tech uses an object containing its required value, while a general tech is referenced by name:

```json
{"combatProficiency": 2}
```

```json
"canBombBoost"
```

## Difficulty Profiles

The three proficiency settings are intended to represent comparable skill at approximately the following values:

- `combatProficiency`: `X`
- `bossProficiency`: `X`
- `darkProficiency`: `X - 1`

For example, a difficulty profile using combat and boss proficiency 2 would normally use dark proficiency 1. A dark proficiency below 1 enables no tier of dark-room navigation without the Lamp.

This relationship is a guideline for creating cohesive presets, not a requirement that consumers use those combinations. Each proficiency and general tech can be configured independently.

## Structure

The top-level `techCategories` array groups related techs for organization and presentation. Each category has:

- `name`: The category's name.
- `description`: The purpose of the category.
- `techs`: The tech definitions in the category.

Every tech has an integer `id` unique within `tech.json` and a `name` used by logical requirements. Optional `note` and `devNote` arrays provide player-facing explanations and contributor-facing implementation details.

## Tiered Techs

A tiered tech represents proficiency on an ordered scale. Its `tiers` array defines the available values and describes the ability expected at each one:

```json
{
  "id": 1,
  "name": "combatProficiency",
  "tiers": [
    {
      "value": 1,
      "note": [
        "Ability to kill or dodge enemies with a similar level of precision as required in some of the later dungeons in the vanilla game."
      ]
    }
  ]
}
```

A requirement is fulfilled when the configured proficiency is at least its requested value. Higher settings therefore include lower tiers.

Tier notes describe the additional ability expected at that value. Consumers can use them when presenting difficulty settings to a player. 

Tiered requirements begin at 1, which is the minimum supported value in the logic. A value of 9 may be used for any tiered proficiency when a strat is believed to be possible but has not yet been tested or placed precisely on the ordinary difficulty scale.

## General Techs

A general tech is an individually enabled or disabled technique. It has:

- `id`: Its unique numeric identifier.
- `name`: The string used to require the tech.
- `techRequires`: Other technique assumptions that must also be enabled or fulfilled.
- `otherRequires`: Items, resources, health, game state, or other non-tech requirements needed to perform it.
- `note`: A description of the technique and its expected execution.
- `devNote`: Optional implementation or research notes.
- `extensionTechs`: Optional more difficult or specialized forms of the technique.

```json
{
  "id": 5,
  "name": "canBombBoost",
  "techRequires": [],
  "otherRequires": [
    {"bombs": 1},
    {"damage": {"enemy": "Bomb", "count": 1}}
  ],
  "note": [
    "Using a bomb to boost Link over a small pit."
  ]
}
```

Requiring a general tech means that the consumer must allow the technique and that both requirement arrays must be fulfilled. Requirements in these arrays use the same evaluation and resource-consumption rules as requirements in a strat.

## Extension Techs

`extensionTechs` nests a more advanced technique beneath a related parent for organization and presentation. An extension tech is otherwise a complete general tech with its own ID, name, requirements, and notes.

Its requirements stand alone. If the parent technique is also required, the extension explicitly names it in `techRequires`:

```json
{
  "id": 7,
  "name": "canPreciseBombBoost",
  "techRequires": ["canBombBoost"],
  "otherRequires": []
}
```

In this example, the tech `canPreciseBombBoost` inherits the bomb ammo and damage from the base `canBombBoost` tech.

See [Logical Requirements: Tech](logicalRequirements.md#tech) for how tech names and proficiency objects are used within requirement lists.
