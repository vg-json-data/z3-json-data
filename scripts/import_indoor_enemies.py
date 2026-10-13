#!/usr/bin/env python3
"""Import cave and house placements: python scripts/import_indoor_enemies.py ../jpdasm [--check]."""

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re

from import_overworld_enemies import ROOT, catalog, read_json

# These native rooms contain independent interiors on their left/right sides.
# Match the entrance's side instead of assigning the whole native sprite list.
SPLIT_X = {0x101, 0x103, 0x106, 0x107, 0x10C, 0x10E, 0x112,
           0x114, 0x115, 0x11B, 0x11C, 0x11E, 0x11F, 0x122,
           0x124, 0x125, 0x126}
# NPCs, scenery, switches, pickups, fairies, bumpers, and the catchable Good Bee.
EXCLUDED = {0x04, 0x06, 0x16, 0x1A, 0x1E, 0x1F, 0x28, 0x29, 0x31,
            0x32, 0x33, 0x35, 0x3A, 0x3B, 0x65, 0x72, 0x73, 0x78,
            0x93, 0xAD, 0xB2, 0xB5, 0xBB, 0xBC, 0xC8, 0xE3, 0xE9, 0xEB}


def entrance_mapping(disassembly):
    text = (disassembly / "bank_02.asm").read_text(encoding="utf-8").split("EntranceData:\n", 1)[1]
    def table(name):
        section = text.split(f".{name}\n", 1)[1].split("\n.", 1)[0]
        return [int(v, 16) for v in re.findall(r"dw \$([0-9A-F]+)", section)]
    native = table("room_id")
    xs = table("x_coordinate")
    assert len(native) == len(xs) == 133
    overworld = {}
    for path in (ROOT / "rooms/overworld").glob("*.json"):
        room = read_json(path)
        for node in room["nodes"]:
            for entrance in node.get("entrances", []):
                overworld[room["id"], entrance["id"]] = entrance.get("romEntranceId")
    mapping = defaultdict(set)
    for connection in read_json(ROOT / "connections/entrances.json")["connections"]:
        if connection["type"] != "door":
            continue
        source = connection["overworld"]
        entrance = overworld.get((source["roomId"], source["entranceId"]))
        if entrance is not None:
            room = native[entrance]
            side = (xs[entrance] & 0x100) if room in SPLIT_X else None
            mapping[connection["underworld"]["roomId"]].add((room, side))
    # Houlihan's room has no ordinary entrance record; it shares native room 104
    # with Link's house, whose only sprite is Uncle in the bottom-right quadrant.
    mapping[20] = {(0x104, None)}
    return mapping


def sprite_lists(disassembly):
    text = (disassembly / "bank_09.asm").read_text(encoding="utf-8")
    pointer_section = text.split("RoomData_SpritePointers:\n", 1)[1].split("RoomData_Sprites_Room0000:", 1)[0]
    pointers = re.findall(r"dw (RoomData_Sprites_\w+)", pointer_section)
    result = {}
    for label, body in re.findall(r"^(RoomData_Sprites_\w+):\n(.*?db \$FF ; END)", text, re.M | re.S):
        # Comment coordinates decode layer/aux bits. Only actual SPRITE records
        # are included, not overlord controllers or key-assignment markers.
        result[label] = [(int(s, 16), int(x, 16), int(y, 16)) for s, x, y in re.findall(
            r"; SPRITE ([0-9A-F]{2})\s+\| xy: \{ 0x([0-9A-F]+), 0x([0-9A-F]+),", body)]
    assert len(pointers) == 384, len(pointers)
    assert set(pointers) <= result.keys()
    return [result[label] for label in pointers]


def enemy_name(sprite, x, dark, by_sprite):
    if sprite in EXCLUDED:
        return None
    if sprite == 0x26:
        return "Hardhat Beetle (Blue)" if x & 0x10 else "Hardhat Beetle (Red)"
    if sprite in (0x5B, 0x5C):
        return "Spark"
    if sprite == 0x83:
        return "Goriya (Green)"  # The cave placement is in Mimic Cave.
    if sprite == 0x6D:
        return "Buzz" if dark else "Rat"
    if sprite == 0x6F:
        return "Chasupa" if dark else "Keese"
    candidates = by_sprite.get(sprite, [])
    assert len(candidates) == 1, f"Unclassified indoor sprite {sprite:02X}: {candidates}"
    return candidates[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("disassembly", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    mapping = entrance_mapping(args.disassembly)
    sprites = sprite_lists(args.disassembly)
    by_sprite, names = catalog()
    files = sorted(path for folder in ("caves", "houses")
                   for path in (ROOT / "rooms" / folder).rglob("*.json"))
    changed = 0
    for path in files:
        original = path.read_text(encoding="utf-8")
        room = json.loads(original)
        assert room["id"] in mapping, f"No native room mapping: {path}"
        counts = Counter()
        for native, side in mapping[room["id"]]:
            for sprite, x, y in sprites[native]:
                if side is not None and x & 0x100 != side:
                    continue
                if room["id"] == 20 and y >= 0x100:
                    continue
                name = enemy_name(sprite, x, path.parent.name == "dark", by_sprite)
                if name is not None:
                    assert name in names
                    counts[name] += 1
        enemies = [{"name": name, "count": count} for name, count in sorted(counts.items())]
        for enemy in enemies:
            if enemy["name"] == "Cucco":
                enemy["note"] = "Conditional threat; retaliation is not included in the placement count."
        inventory = {"enemies": enemies}
        if room.get("enemySpawns") == inventory:
            continue
        changed += 1
        if not args.check:
            replacement = json.dumps(inventory, indent=2).replace("\n", "\n  ")
            if "enemySpawns" in room:
                start = original.index('"enemySpawns":') + len('"enemySpawns":')
                start += len(original[start:]) - len(original[start:].lstrip())
                _, length = json.JSONDecoder().raw_decode(original[start:])
                updated = original[:start] + replacement + original[start + length:]
            else:
                updated = original.replace('  "nodes": [', '  "enemySpawns": ' + replacement + ',\n  "nodes": [', 1)
            assert json.loads(updated)["enemySpawns"] == inventory
            path.write_text(updated, encoding="utf-8")
    print(f"{'CHECK' if args.check else 'IMPORT'}: {len(files)} rooms; {changed} {'stale' if args.check else 'updated'}")
    return int(args.check and bool(changed))


if __name__ == "__main__":
    raise SystemExit(main())
