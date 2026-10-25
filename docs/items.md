# Item Data

[`items.json`](../items.json) defines items and persistent flags used by *The Legend of Zelda: A Link to the Past* logic.

Item definitions describe what a room item represents and how it is encoded by the game. A room item's `item` property names one of these definitions. Its location, ROM address, and the strat that collects it are defined separately in the [room data](rooms.md#items) and [strat data](strats.md#collecting-items).

## Item Receipt Records

Most categories contain item receipt records with the following properties:

- `name`: The name used to identify the item in room data and logic.
- `itemReceiptId`: The byte passed to the game's item-receipt handler.
- `note`: Additional behavior or implementation details.

```json
{
  "name": "Hookshot",
  "itemReceiptId": "0x0A"
}
```

```json
{
  "name": "ProgressiveSword",
  "itemReceiptId": "0x5E",
  "note": "A randomizer variant that upgrades the player's current sword by one level."
}
```

Names identify items across the data model. Receipt IDs are implementation values and are not necessarily unique; for example, all seven crystals use the same vanilla receipt ID and are distinguished by their names.

## Non-vanilla Items

The original game defines many receipt IDs, but randomizers add others to make normally event-based upgrades work as ordinary shuffled items, provide safer progressive behavior, or support new game modes.

Examples include receipts that:

- Grant the Master Sword, Half Magic, or Silver Arrow upgrade without reproducing the original event or its unwanted side effects.
- Upgrade the current sword, shield, armor, or glove level instead of potentially replacing a higher level with a lower one.

These records are grouped in `nonVanilla`, which replaces per-item vanilla markers. The section includes both upgrades obtainable through vanilla events and items with new behavior; their receipt IDs require a compatible randomizer ROM patch. When their behavior needs explanation, `note` describes what a randomizer must implement. Publishing their receipt-ID assignments provides a shared convention that randomizers, trackers, and other tools can adopt for improved compatibility.

## Inventory

`inventory` contains vanilla inventory and equipment, including ordinary items and specific equipment levels. Randomizer-defined progressive items are listed in `nonVanilla`.

Fixed equipment-level receipts and progressive items have different effects: a fixed receipt grants its specified level, while a progressive item upgrades the current level.

## Refills

`refills` contains collectible item receipts that immediately add a resource, such as arrows, bombs, health, or magic. These are items placed at item locations such as chests; they are not enemy drops. The amount and behavior are part of the receipt represented by `itemReceiptId`.

These item receipts are also distinct from [enemy prize-pack drops](enemies.md#prize-packs) and from a [`refill` logical requirement](logicalRequirements.md#refills), which models a source of resources during route evaluation.

## Bottle Contents

`bottleContents` contains filled-bottle items. In addition to the common item receipt properties, a bottle-content record may define:

- `refillReceiptId`: A receipt that puts the content into an existing empty bottle.

```json
{
  "name": "GreenPotion",
  "itemReceiptId": "0x2C",
  "refillReceiptId": "0x2F"
}
```

`itemReceiptId` grants the filled bottle as an item. `refillReceiptId` instead fills an existing empty bottle. Its omission means that the original game does not define a corresponding refill receipt; a randomizer may define its own if needed.

## Currency

`currency` contains rupee receipts. Each record's name communicates the denomination, while `itemReceiptId` identifies the receipt that awards it.

## Dungeon Items

`dungeonItems` contains the vanilla receipts for a Small Key, Compass, Big Key, and Map.

These receipt IDs operate on the currently loaded dungeon. A Small Key receipt increases that dungeon's key count, while the other receipts set the corresponding dungeon-specific inventory bit. Dungeon-specific randomizer receipts would be separate non-vanilla definitions if they are added in the future.

## Dungeon Prizes

`dungeonPrizes.items` contains pendants and crystals. Each record has:

- `name`: The specific pendant or crystal.
- `itemReceiptId`: The receipt used when the prize is collected.

```json
{
  "name": "Crystal1",
  "itemReceiptId": "0x20"
}
```

All seven crystals use receipt `0x20`; their names identify the specific crystals.

## Health Upgrades

`healthUpgrades` contains heart pieces and heart containers that increase maximum health. Randomizer bomb- and arrow-capacity upgrades are listed in `nonVanilla`.

Some health-upgrade receipts have specialized vanilla behavior. Their `note` describes relevant differences such as whether receiving the item also restores health.

## Flags

`flags` lists persistent game events used by the logical model. Unlike item records, flags are represented directly by strings and do not have item receipt IDs.

A strat sets a flag with `setsFlags`, and later logical requirements can test it with `flag`. See [Strats: Setting Flags](strats.md#setting-flags) and [Logical Requirements: Flags](logicalRequirements.md#flags).
