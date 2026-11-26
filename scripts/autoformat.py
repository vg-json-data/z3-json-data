#!/usr/bin/env python3
"""Rewrite every JSON file in the project in the standard format.

Object properties are ordered as the file's schema lists them (see schema_order.py), then the result is formatted
as described in format_json.py. Schema files are formatted without reordering.
"""

import json

from format_json import format_json
from schema_order import order_by_schema
from validate import ROOT, SCHEMA_DIR, registry_for


schemas = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(SCHEMA_DIR.glob("*.schema.json"))]
registry = registry_for(schemas)

for path in sorted(ROOT.glob("**/*.json")):
    if ".git" in path.relative_to(ROOT).parts:
        continue
    text = path.read_text(encoding="utf-8")
    document = json.loads(text)
    if path.parent != SCHEMA_DIR:
        schema_name = document["$schema"].split("/")[-1]
        document = order_by_schema(document, registry.contents(schema_name), registry.resolver(schema_name))
    new_text = format_json(document)

    # The output must hold the same data as the input; only formatting and property order may change.
    assert json.loads(new_text) == json.loads(text), path

    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        print("Formatted", path.relative_to(ROOT))
