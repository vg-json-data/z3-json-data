#!/usr/bin/env python3
"""Assign IDs to strats that lack them, in source order, and update each room's nextStratId.

Strat IDs are stable: existing IDs are never changed, and new ones continue from nextStratId, so IDs of deleted
strats are not reused.
"""

import json

from format_json import format_json
from validate import ROOT


for path in sorted((ROOT / "rooms").glob("**/*.json")):
    text = path.read_text(encoding="utf-8")
    room = json.loads(text)
    next_id = room.get("nextStratId", 1)
    added = 0
    for i, strat in enumerate(room["strats"]):
        if "id" not in strat:
            room["strats"][i] = {"id": next_id, **strat}
            next_id += 1
            added += 1
    room["nextStratId"] = next_id
    new_text = format_json(room)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        print(f"Added {added} strat IDs in {path.relative_to(ROOT)}")
