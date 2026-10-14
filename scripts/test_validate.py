"""Regression checks for special overworld edge references."""

import json
import unittest
from collections import defaultdict

from jsonschema import validators

from validate import ROOT, validate_room


class LakeReferenceTests(unittest.TestCase):
    def setUp(self):
        schema = json.loads((ROOT / "schema/z3-room.schema.json").read_text(encoding="utf-8"))
        self.validator = validators.validator_for(schema)(
            {"$ref": "#/definitions/edgeVariantSegment", "definitions": schema["definitions"]}
        )

    def room_errors(self, node_ids, world="both", variant="lake"):
        document = {
            "roomType": "Overworld",
            "size": [2, 2],
            "nodes": [{"id": 1, "name": "Land", "world": world}],
            "strats": [],
            "edgeVariants": {
                "west": [{"supported": {variant: node_ids}, "default": variant}]
            },
        }
        errors = defaultdict(list)
        validate_room(ROOT / "rooms/test.json", document, {}, errors)
        return [error for messages in errors.values() for error in messages]

    def test_lake_schema(self):
        for node_ids, valid in [
            ([1, "return"], True), ([1, 2], True),
            (["return", 1], False), ([1, "typo"], False),
            ([0, "return"], False), ([1, 0], False),
            ([1], False), ([1, 2, "return"], False),
        ]:
            with self.subTest(node_ids=node_ids):
                segment = {"supported": {"lake": node_ids}, "default": "lake"}
                self.assertEqual(self.validator.is_valid(segment), valid)

    def test_return_skips_node_lookup_only_at_lake_water_opening(self):
        self.assertEqual(self.room_errors([1, "return"]), [])
        self.assertEqual(self.room_errors([1, 1]), [])
        for node_ids, variant in [
            (["return", 1], "lake"), ([1, "typo"], "lake"),
            (["return"], "wide"), ([1, 99], "lake"),
        ]:
            with self.subTest(node_ids=node_ids, variant=variant):
                self.assertTrue(any("unknown node" in error
                                    for error in self.room_errors(node_ids, variant=variant)))

    def test_return_preserves_world_checks_for_real_nodes(self):
        errors = self.room_errors([1, "return"], world="light")
        self.assertEqual(len(errors), 1)
        self.assertIn("node 1 is not present in dark world", errors[0])


if __name__ == "__main__":
    unittest.main()
