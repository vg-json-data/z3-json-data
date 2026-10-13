#!/usr/bin/env python3
"""Reproduce vanilla placed-enemy inventories from the JP1.0 disassembly.

Usage: python scripts/import_overworld_enemies.py ../jpdasm [--check]
No ROM or third-party packages required. Only the enemySpawns field is edited.
"""

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGES = ("beforeZeldaRescue", "afterZeldaRescue", "afterAgahnim")
# Explicitly reviewed non-enemy placements. Fail on new/unclassified sprite IDs.
EXCLUDED = {
    0x14, 0x1A, 0x1D, 0x25, 0x2A, 0x2B, 0x2C, 0x2E, 0x2F, 0x30,
    0x33, 0x34, 0x36, 0x37, 0x39, 0x3B, 0x3C, 0x3D, 0x3F, 0x52,
    0x57, 0x59, 0x5A, 0x62, 0x74, 0x75, 0x9E, 0x9F, 0xA0, 0xAC,
    0xB3, 0xB4, 0xB6, 0xB9, 0xBA, 0xC0, 0xD1, 0xD2, 0xD5,
    0xD8, 0xDA, 0xDB, 0xDC, 0xDD, 0xDE, 0xE0, 0xE3, 0xE7, 0xE8,
    0xEB, 0xF2, 0xF3,
    0x79,  # Dormant bee hives, intentionally omitted from room enemy lists.
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def extract(disassembly):
    text = (disassembly / "bank_09.asm").read_text(encoding="utf-8")
    pointer_text = text.split("Overworld_SpritePointers:\n", 1)[1].split(
        "Overworld_Sprites_EMPTY:", 1)[0]
    tables = []
    for stage in range(3):
        section = pointer_text.split(f".state_{stage}\n", 1)[1].split(".state_", 1)[0]
        tables.append(re.findall(r"dw (Overworld_Sprites_\w+)", section))
    assert list(map(len, tables)) == [64, 144, 144], "Unexpected pointer table sizes"
    assert tables[1][64:] == tables[2][64:], "Dark World/special tables differ"
    lists = {}
    pattern = r"^(Overworld_Sprites_\w+):\n(.*?^#_[0-9A-F]{6}: db \$FF ; END)"
    for match in re.finditer(pattern, text, re.M | re.S):
        rows = re.findall(
            r"#_([0-9A-F]{6}): db \$([0-9A-F]{2}), \$([0-9A-F]{2}), \$([0-9A-F]{2})",
            match[2])
        lists[match[1]] = [(address, int(y, 16), int(x, 16), int(sprite, 16))
                           for address, y, x, sprite in rows]
    assert set(sum(tables, [])) <= lists.keys(), "Missing sprite list"
    values = (disassembly / "values.asm").read_text(encoding="utf-8")
    values = values.split("; Sprites\n", 1)[1].split("; Overlords", 1)[0]
    labels = {int(i, 16): name for i, name in re.findall(r"; ([0-9A-F]{2}) - (.*)", values)}
    return tables, lists, labels


def catalog():
    by_sprite = {}
    names = set()
    for path in sorted((ROOT / "enemies").glob("*.json")):
        if path.name == "attacks.json":
            continue
        for enemy in read_json(path)["enemies"]:
            names.update(enemy["names"])
            if enemy.get("spriteIndex") is not None:
                by_sprite.setdefault(enemy["spriteIndex"], []).append(enemy["names"][0])
    return by_sprite, names


def resolve(sprite, x, dark, by_sprite):
    if sprite in EXCLUDED:
        return None, None
    if sprite == 0xF4:
        return None, "boulders"
    if sprite == 0xC5:
        return "Poe", "Grave trigger: becomes sprite 0x19 (Poe) when the grave is disturbed; not a Medusa outdoors."
    if sprite in (0, 8, 10):
        return {0: ("Crow", "Dacto"), 8: ("Octorok", "Slarok"),
                10: ("4-way Octorok", "4-way Slarok")}[sprite][dark], None
    if sprite == 0xC9:
        return ("Tektite (Red)" if x & 1 else "Tektite (Blue)"), None
    if sprite == 0x0B:
        return ("Cucco Skeleton" if dark else "Cucco"), "Conditional threat; retaliation is not included in the placement count."
    if sprite == 0x55:
        return ("Ku" if dark else "Fireball Zora"), None
    if sprite in (0x41, 0x43) and dark:
        return ("Taros (Blue)" if sprite == 0x41 else "Taros (Red)"), None
    candidates = by_sprite.get(sprite, [])
    assert len(candidates) == 1, f"Unclassified/ambiguous sprite {sprite:02X}: {candidates}"
    return candidates[0], None


def profile(screen, label, lists, labels, by_sprite, names, *, dark=None):
    grouped = {}
    for address, y, x, sprite in lists[label]:
        name, note = resolve(sprite, x, screen >= 64 if dark is None else dark, by_sprite)
        if note == "boulders":
            grouped["Falling Boulder"] = {"name": "Falling Boulder", "count": None,
                                         "note": "Recurring spawns; no fixed count."}
            continue
        if name is None and note is None:
            continue
        assert name is None or name in names, f"Unknown enemy name: {name}"
        if name not in grouped:
            grouped[name] = {"name": name, "count": 0}
        grouped[name]["count"] += 1
        if note:
            grouped[name]["note"] = (
                "Includes a Poe released by disturbing a grave." if sprite == 0xC5 else note)
    return {"enemies": sorted(grouped.values(), key=lambda e: e["name"] or "")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("disassembly", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    tables, lists, labels = extract(args.disassembly)
    by_sprite, names = catalog()
    changed = []
    files = sorted((ROOT / "rooms" / "overworld").glob("*.json"))
    files += sorted((ROOT / "rooms" / "special").glob("*.json"))
    special_screens = {"Sacred Grove": 0x80, "Under the Bridge": 0x80, "Zora's Waterfall": 0x81}
    for path in files:
        original = path.read_text(encoding="utf-8")
        room = json.loads(original)
        if room["roomType"] == "Special":
            screen = special_screens[room["name"]]
            label = tables[1][screen]
            rows = lists[label]
            # Grove and bridge share a native screen, separated horizontally.
            if room["name"] == "Sacred Grove":
                rows = [row for row in rows if row[2] < 0x10]
            elif room["name"] == "Under the Bridge":
                rows = [row for row in rows if row[2] >= 0x10]
            inventory = profile(screen, label, {label: rows}, labels, by_sprite, names, dark=False)
        else:
            # Explicit room position is authoritative, not the room id or filename.
            x, y = room["position"]
            screen = y * 8 + x
            assert screen == int(path.name[:2], 16), f"Screen/filename mismatch: {path}"
            inventory = {
                "light": {stage: profile(screen, tables[i][screen], lists, labels, by_sprite, names)
                          for i, stage in enumerate(STAGES)},
                "dark": profile(screen + 64, tables[2][screen + 64], lists, labels, by_sprite, names),
            }
        if room.get("enemySpawns") == inventory:
            continue
        changed.append(path.name)
        if not args.check:
            # Preserve formatting and all other fields in existing hand-authored rooms.
            if "enemySpawns" in room:
                decoder = json.JSONDecoder()
                start = original.index('"enemySpawns":') + len('"enemySpawns":')
                start += len(original[start:]) - len(original[start:].lstrip())
                _, length = decoder.raw_decode(original[start:])
                replacement = json.dumps(inventory, indent=2, ensure_ascii=False).replace("\n", "\n  ")
                updated = original[:start] + replacement + original[start + length:]
            else:
                addition = json.dumps(inventory, indent=2, ensure_ascii=False).replace("\n", "\n  ")
                updated = original.replace('  "nodes": [', '  "enemySpawns": ' + addition + ',\n  "nodes": [', 1)
            assert json.loads(updated)["enemySpawns"] == inventory
            with path.open("w", encoding="utf-8", newline="\n") as output:
                output.write(updated)
    print(f"{'CHECK' if args.check else 'IMPORT'}: {len(files)} rooms; {len(changed)} {'stale' if args.check else 'updated'}")
    return int(args.check and bool(changed))


if __name__ == "__main__":
    raise SystemExit(main())
