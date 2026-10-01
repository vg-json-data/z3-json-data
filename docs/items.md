# Item Data

[`items.json`](../items.json) defines item receipts, dungeon-prize patch data, and persistent flags used by *The Legend of Zelda: A Link to the Past* logic.

Item definitions describe what a room item represents and how it is encoded by the game. A room item's `item` property names one of these definitions. Its location, ROM address, and the strat that collects it are defined separately in the [room data](rooms.md#items) and [strat data](strats.md#collecting-items).

## Item Receipt Records

Most categories contain item receipt records with the following properties:

- `name`: The name used to identify the item in room data and logic.
- `itemReceiptId`: The byte passed to the game's item-receipt handler.
- `vanilla`: Omitted for receipts defined by the original game. Randomizer-defined receipts use `false`.
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
  "vanilla": false,
  "note": "A randomizer variant that upgrades the player's current sword by one level."
}
```

Names identify items across the data model. Receipt IDs are implementation values and are not necessarily unique; for example, all seven crystals use the same vanilla receipt ID and are distinguished by their dungeon-prize patch bytes.

## Vanilla and Non-vanilla Receipts

The original game defines many receipt IDs, but randomizers add others to make normally event-based upgrades work as ordinary shuffled items, provide safer progressive behavior, or support new game modes.

Examples include receipts that:

- Grant the Master Sword, Half Magic, or Silver Arrow upgrade without reproducing the original event or its unwanted side effects.
- Upgrade the current sword, shield, armor, or glove level instead of potentially replacing a higher level with a lower one.
- Add new goal items such as the Triforce and Triforce Pieces.

These records use `"vanilla": false`. When their behavior needs explanation, `note` describes what a randomizer must implement. Publishing their receipt-ID assignments provides a shared convention that randomizers, trackers, and other tools can adopt for improved compatibility.

## Inventory

`inventory` contains lasting inventory and equipment. It includes ordinary items, specific equipment levels, and randomizer-defined progressive receipts.

The category does not imply that every record behaves progressively. For example, a fixed sword-level receipt and `ProgressiveSword` are both inventory receipts, but their effects differ.

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

`dungeonPrizes` contains pendants and crystals. Each record has:

- `name`: The specific pendant or crystal.
- `itemReceiptId`: The receipt used when the prize is collected.
- `prizePatchBytes`: Six bytes written positionally to the six `itemAddress` values of a dungeon-prize location.

```json
{
  "name": "Crystal1",
  "itemReceiptId": "0x20",
  "prizePatchBytes": ["0x02", "0x34", "0x64", "0x40", "0x7F", "0x06"]
}
```

The first patch byte is written to the first address, the second byte to the second address, and so on. All seven crystals use receipt `0x20`; their individual identities are encoded by `prizePatchBytes`.

## Goal Items

`goalItems` contains randomizer receipts used to complete or advance a game goal rather than ordinary inventory or dungeon prizes.

The effect of an individual goal receipt is described by its `note`. For example, receiving the Triforce completes the game, while a Triforce Piece contributes toward a separately configured collection goal.

## Expansions

`expansions` contains receipts that increase health or resource capacity. This includes heart pieces and containers, bomb-capacity upgrades, and arrow-capacity upgrades.

Some expansion receipts have specialized vanilla behavior. Their `note` describes relevant differences such as whether receiving the item also restores health.

## Flags

`flags` lists persistent game events used by the logical model. Unlike item records, flags are represented directly by strings and do not have item receipt IDs.

A strat sets a flag with `setsFlags`, and later logical requirements can test it with `flag`. See [Strats: Setting Flags](strats.md#setting-flags) and [Logical Requirements: Flags](logicalRequirements.md#flags).
