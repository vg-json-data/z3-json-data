#!/usr/bin/env python3
"""Import unique dungeon enemy names from JP1.0: script ../jpdasm [--check]."""

import argparse
import json
from pathlib import Path
import re

from import_indoor_enemies import sprite_lists
from import_overworld_enemies import ROOT, read_json

MAPS = {
    "Hyrule Castle": ["HyruleCastle", "Sewers"],
    "Eastern Palace": ["EasternPalace"], "Desert Palace": ["DesertPalace"],
    "Agahnim's Tower": ["AgahnimsTower"], "Tower of Hera": ["TowerofHera"],
    "Swamp Palace": ["SwampPalace"], "Palace of Darkness": ["PalaceofDarkness"],
    "Misery Mire": ["MiseryMire"], "Skull Woods": ["SkullWoods"],
    "Ice Palace": ["IcePalace"], "Thieves' Town": ["ThievesTown"],
    "Turtle Rock": ["TurtleRock"], "Ganon's Tower": ["GanonsTower"],
    "Pyramid": [],
}
# Non-enemies, pickups, scenery, and boss shells/projectiles.
EXCLUDED = {0x04, 0x06, 0x1C, 0x1E, 0x21, 0x37, 0x38, 0x3B, 0x73,
            0x76, 0x93, 0xA3, 0xA4, 0xAE, 0xAF, 0xB0, 0xB1, 0xB7,
            0xC1, 0xE3, 0xE4, 0xEE}
OVERLORDS = {
    0x02: "Ball", 0x03: "Ball", 0x05: "Head-Detaching Stalfos",
    0x08: "Zol", 0x09: "Wallmaster", 0x10: "Pirogusu",
    0x11: "Pirogusu", 0x12: "Pirogusu", 0x13: "Pirogusu",
    0x14: "Flying Tile", 0x15: "Wizzrobe", 0x16: "Zoro",
    0x18: "Stalfos", 0x19: "Armos Knight",
}
IGNORED_OVERLORDS = {0x07, 0x0A, 0x0B, 0x17, 0x1A}


def catalog():
    sprites = {}
    names = set()
    for path in sorted((ROOT / "enemies").glob("*.json")):
        if path.name == "attacks.json":
            continue
        for enemy in read_json(path)["enemies"]:
            names.update(enemy["names"])
            for sprite in [enemy.get("spriteIndex"), *enemy.get("additionalSpriteIndex", [])]:
                if sprite is not None:
                    sprites.setdefault(sprite, []).append(enemy["names"][0])
    return sprites, names


def resolve(sprite, x, native, dark, catalog):
    if sprite in EXCLUDED:
        return None
    if sprite == 0x26:
        return "Hardhat Beetle (Blue)" if x & 0x10 else "Hardhat Beetle (Red)"
    if sprite in (0x83, 0x84):
        kind = "Goriya" if native in {0x1B, 0x4B, 0x6B} else "Eyegore"
        return f"{kind} ({'Green' if sprite == 0x83 else 'Red'})"
    if sprite == 0x6F and not dark and native in {0xB0, 0xD0}:
        # Agahnim's Tower uses Chasupa graphics with Light World Keese stats.
        return "Chasupa (Light World)"
    if sprite in (0x6D, 0x6E, 0x6F):
        return {0x6D: ("Rat", "Buzz"), 0x6E: ("Rope", "Skullrope"),
                0x6F: ("Keese", "Chasupa")}[sprite][dark]
    if sprite == 0x45:
        # The green spear soldier is a summoned variant, not a placement.
        return "Taros (Red)" if dark else "Spear Soldier (Red)"
    if dark and sprite in (0x41, 0x43):
        return "Taros (Blue)" if sprite == 0x41 else "Taros (Red)"
    if sprite in (0x66, 0x67, 0x68, 0x69):
        return "Wall Turret Cannon Ball"
    special = {0x4F: "Popo", 0x63: "Devalant", 0x8F: "Zol",
               0xC5: "Medusa", 0xC6: "Yomo Medusa", 0xD7: "Ganon"}
    if sprite in special:
        return special[sprite]
    candidates = catalog.get(sprite, [])
    assert len(candidates) == 1, f"Ambiguous/unmapped dungeon sprite {sprite:02X}: {candidates}"
    return candidates[0]


def extract(disassembly):
    maps = (disassembly / "bank_0A.asm").read_text(encoding="utf-8")
    room_sets = {}
    for name, body in re.findall(r"^DungeonMapRoomData_(\w+):\n(.*?)(?=^\w+:)", maps, re.M | re.S):
        room_sets[name] = {int(v, 16) for line in body.splitlines() if ": db " in line
                           for v in re.findall(r"\$([0-9A-F]{2})", line)} - {0x0F}
    text = (disassembly / "bank_09.asm").read_text(encoding="utf-8")
    pointer_text = text.split("RoomData_SpritePointers:\n", 1)[1].split("RoomData_Sprites_Room0000:", 1)[0]
    pointers = re.findall(r"dw (RoomData_Sprites_\w+)", pointer_text)
    controllers = {label: {int(v, 16) for v in re.findall(r"OVERLORD ([0-9A-F]{2})", body)}
                   for label, body in re.findall(r"^(RoomData_Sprites_\w+):\n(.*?db \$FF ; END)", text, re.M | re.S)}
    return room_sets, sprite_lists(disassembly), [controllers[p] for p in pointers]


def grouped_inventory(names):
    """Use the catalog files as presentation groups, retaining a flat JSON list."""
    groups = []
    remaining = set(names)
    for filename in ("bosses.json", "enemies.json"):
        category = {name for enemy in read_json(ROOT / "enemies" / filename)["enemies"]
                    for name in enemy["names"]}
        groups.append(sorted(remaining & category))
        remaining -= category
    groups.append(sorted(remaining))
    groups = [group for group in groups if group]
    ordered = [name for group in groups for name in group]
    lines = ["{", '    "enemies": [']
    index = 0
    for group_index, group in enumerate(groups):
        if group_index:
            lines.append("")
        for name in group:
            index += 1
            comma = "," if index < len(ordered) else ""
            lines.append("      " + json.dumps(name) + comma)
    lines.extend(["    ]", "  }"])
    return {"enemies": ordered}, "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("disassembly", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    maps, sprites, overlords = extract(args.disassembly)
    by_sprite, catalog_names = catalog()
    files = sorted((ROOT / "rooms/dungeons").rglob("*.json"))
    changed = 0
    for path in files:
        original = path.read_text(encoding="utf-8")
        room = json.loads(original)
        native_rooms = set().union(*(maps[name] for name in MAPS[room["name"]]))
        if room["name"] == "Pyramid":
            native_rooms = {0x00, 0x10}  # Ganon arena and the room below it.
        dark = path.parent.name == "dark"
        names = set()
        for native in native_rooms:
            for sprite, x, y in sprites[native]:
                name = resolve(sprite, x, native, dark, by_sprite)
                if name:
                    names.add(name)
            for controller in overlords[native]:
                if controller == 0x06:
                    names.add("Skullrope" if dark else "Rope")
                elif controller in OVERLORDS:
                    names.add(OVERLORDS[controller])
                else:
                    assert controller in IGNORED_OVERLORDS, f"Unknown controller {controller:02X}"
        # Prominent boss companions and cluster outputs not necessarily placed separately.
        if "Vitreous" in names:
            names.add("Vitreous (Small Eye)")
        if "Arrghus" in names:
            names.add("Arrghus Fuzz")
        if "Bubble Cluster" in names:
            names.add("Invincible Bubble")
        if room["name"] == "Ice Palace":
            # Static gray spike blocks on the 8 -> 9 route are not sprite placements.
            names.add("Spike Block")
        assert names <= catalog_names, names - catalog_names
        inventory, replacement = grouped_inventory(names)
        if "enemySpawns" in room:
            start = original.index('"enemySpawns":') + len('"enemySpawns":')
            start += len(original[start:]) - len(original[start:].lstrip())
            _, length = json.JSONDecoder().raw_decode(original[start:])
            updated = original[:start] + replacement + original[start + length:]
        else:
            updated = original.replace('  "nodes": [', '  "enemySpawns": ' + replacement + ',\n  "nodes": [', 1)
        if original == updated:
            continue
        changed += 1
        if not args.check:
            assert json.loads(updated)["enemySpawns"] == inventory
            path.write_text(updated, encoding="utf-8")
    print(f"{'CHECK' if args.check else 'IMPORT'}: {len(files)} dungeons; {changed} {'stale' if args.check else 'updated'}")
    return int(args.check and bool(changed))


if __name__ == "__main__":
    raise SystemExit(main())
