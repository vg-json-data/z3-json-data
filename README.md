# z3-json-data

A comprehensive, machine-readable JSON representation of game data and routing logic for *The Legend of Zelda: A Link to the Past* (ALTTP). 

## Aim of the Project

The goal of this repository is to encode ALTTP's game data and routing logic in a standardized JSON format, which can be adopted into randomizers, trackers, or other tools:
*   Progress is currently driven by the needs of an [ALTTP Map Rando](https://github.com/blkerby/z3-map-rando) project that is under development.

This project is the sister repository to [sm-json-data](https://github.com/vg-json-data/sm-json-data), applying the same node-based logical mapping principles from Zebes to Hyrule.

---

## Project Structure

The data is broken down into modular directories and files representing different aspects of the game. 

### [`/Rooms`](docs/rooms.md)
The core of the map data. Hyrule is broken down into distinct "Rooms" representing each overworld area, dungeon, cave, and house. Every room file contains a list of **nodes** and **strats** for moving between nodes.
*   **Nodes:** Represent a location or freely traversable area within a room.
*   **Strats:** Represent actions that can be done to traverse between nodes, or actions that can be executed at a specific node.
*   **Requirements:** A wide range of conditions that dictate if a strat is possible, including items, health/consumables, Link's current state, and the player's skill assumptions.

### [`/Connections`](docs/connections.md)
Defines edges representing transitions between rooms. `entrances.json` contains the main entrance connections, while `teleports.json` and `whirlpools.json` describe those specialized connection types.

### [`/Items`](docs/items.md)
Contains the definitions for both permanent and temporary items in the game.
Item receipt records omit the `vanilla` field when the receipt ID is defined by the original game. Randomizer-defined receipt IDs include `"vanilla": false`, with an optional `note` when their behavior needs explanation.

### `/Enemies`
Detailed information on enemy vulnerabilities, attacks, and damage values. This includes standard enemies, bosses, and environmental hazards.

### [`/Tech`](docs/tech.md)
A set of skill assumptions which the player may toggle to adjust the expected difficulty and logic paths.
* **Proficiency:** Skills modeled with a range of values, allowing the player to specify their level of ability.
* **General:** Specific tricks, sequence breaks, and glitches that a player can toggle on or off based on what they are willing to execute.

### [`/Helpers`](docs/logicalRequirements.md#helpers)
Sets of logical requirements that are summarized into reusable logic blocks. These are called within a strat's requirements to prevent repetition and provide a centralized place for a randomizer to edit or override core assumptions.

---

## Important Concepts

### Rooms

[Room files define areas, nodes, item locations, locks, obstacles, and the strats connecting them.](docs/rooms.md)

### Connections

[Connection files define traversal between overworld and underworld rooms and pair specialized overworld endpoints.](docs/connections.md)

### Items

[Item data defines item receipts, dungeon-prize patch values, and persistent game flags.](docs/items.md)

### Logical Requirements

[Logical requirements represent the inventory, resources, game state, and player proficiency needed to perform actions.](docs/logicalRequirements.md)

### Strats

[Strats represent ways to perform actions within a room, including traversal and changes to logical state.](docs/strats.md)
