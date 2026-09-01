# z3-json-data

A comprehensive, machine-readable JSON representation of game data and routing logic for *The Legend of Zelda: A Link to the Past* (ALTTP). 

## Aim of the Project

The goal of this repository is to encode ALTTP's game data and routing logic in a standardized JSON format, which can be adopted into randomizers, trackers, or other tools:
*   Progress is currently driven by the needs of an [ALTTP Map Rando](https://github.com/blkerby/z3-map-rando) project that is under development.

This project is the sister repository to [sm-json-data](https://github.com/vg-json-data/sm-json-data), applying the same node-based logical mapping principles from Zebes to Hyrule.

---

## Project Structure

The data is broken down into modular directories and files representing different aspects of the game. 

### `/Rooms`
The core of the map data. Hyrule is broken down into distinct "Rooms" representing each overworld area, dungeon, cave, and house. Every room file contains a list of **nodes** and **strats** for moving between nodes.
*   **Nodes:** Represent a location or freely traversable area within a room.
*   **Strats:** Represent actions that can be done to traverse between nodes, or actions that can be executed at a specific node.
*   **Requirements:** A wide range of conditions that dictate if a strat is possible, including items, health/consumables, Link's current state, and the player's skill assumptions.

### `/Entrances`
Defines edges representing transitions between overworld and underworld rooms.

### `/Items`
Contains the definitions for both permanent and temporary items in the game.

### `/Enemies`
Detailed information on enemy vulnerabilities, attacks, and damage values. This includes standard enemies, bosses, and environmental hazards.

### `/Tech`
A set of skill assumptions which the player may toggle to adjust the expected difficulty and logic paths.
* **Proficiency:** Skills modeled with a range of values, allowing the player to specify their level of ability.
* **General:** Specific tricks, sequence breaks, and glitches that a player can toggle on or off based on what they are willing to execute.

### `/Helpers`
Sets of logical requirements that are summarized into reusable logic blocks. These are called within a strat's requirements to prevent repetition and provide a centralized place for a randomizer to edit or override core assumptions.
