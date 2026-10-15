"""Regression checks for special overworld edge references."""

import json
import unittest
from collections import defaultdict

from jsonschema import validators

from validate import ROOT, validate_room


class EdgeReferenceTests(unittest.TestCase):
    def setUp(self):
        schema = json.loads((ROOT / "schema/z3-room.schema.json").read_text(encoding="utf-8"))
        self.validator = validators.validator_for(schema)(
            {"$ref": "#/definitions/edgeVariantSegment", "definitions": schema["definitions"]}
        )

    def room_errors(self, node_ids, world="both", variant="lake", nodes=None):
        document = {
            "roomType": "Overworld",
            "size": [2, 2],
            "nodes": nodes if nodes is not None else [{"id": 1, "name": "Land", "world": world}],
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

    def test_light_and_mirror_schema(self):
        for node_ids, valid in [
            ([1, 2, 3], True), ([1, 1, 1], True),
            ([None, 2, 3], True), ([1, None, 3], True),
            ([1, 2, None], True), ([None, None, None], True),
            ([1], False), ([1, 2], False), ([1, 2, 3, 4], False),
            ([0, 2, 3], False), ([1, 0, 3], False), ([1, 2, 0], False),
            (["return", 2, 3], False), ([1, "return", 3], False),
            ([1, 2, "return"], False),
        ]:
            with self.subTest(node_ids=node_ids):
                segment = {"supported": {"light-and-mirror": node_ids},
                           "default": "light-and-mirror"}
                self.assertEqual(self.validator.is_valid(segment), valid)

    def test_light_and_mirror_worlds_by_role(self):
        for worlds in [("light", "dark", "light"), ("both", "both", "both")]:
            nodes = [{"id": i, "name": str(i), "world": world}
                     for i, world in enumerate(worlds, 1)]
            with self.subTest(worlds=worlds):
                self.assertEqual(self.room_errors([1, 2, 3], variant="light-and-mirror",
                                                  nodes=nodes), [])
        self.assertEqual(self.room_errors([1, 1, 1], variant="light-and-mirror"), [])

        for wrong_index, wrong_world, required_world in [
            (0, "dark", "light"), (1, "light", "dark"), (2, "dark", "light"),
        ]:
            nodes = [{"id": i, "name": str(i), "world": world}
                     for i, world in enumerate(("light", "dark", "light"), 1)]
            nodes[wrong_index]["world"] = wrong_world
            with self.subTest(wrong_index=wrong_index):
                errors = self.room_errors([1, 2, 3], variant="light-and-mirror", nodes=nodes)
                self.assertEqual(len(errors), 1)
                self.assertIn(f"node {wrong_index + 1} is not present in {required_world} world",
                              errors[0])

    def test_light_and_mirror_requires_existing_nodes_at_every_position(self):
        for index in range(3):
            node_ids = [1, 1, 1]
            node_ids[index] = 99
            with self.subTest(index=index):
                errors = self.room_errors(node_ids, variant="light-and-mirror")
                self.assertTrue(any("unknown node" in error for error in errors))

    def test_null_skips_only_missing_light_and_mirror_roles(self):
        for node_ids in ([None, 1, 1], [1, None, 1], [1, 1, None], [None, None, None]):
            with self.subTest(node_ids=node_ids):
                self.assertEqual(self.room_errors(node_ids, variant="light-and-mirror"), [])
        errors = self.room_errors([1, 1, None], world="light", variant="light-and-mirror")
        self.assertEqual(len(errors), 1)
        self.assertIn("node 1 is not present in dark world", errors[0])
        for variant, node_ids in [("wide", [None]), ("lake", [1, None])]:
            with self.subTest(variant=variant):
                segment = {"supported": {variant: node_ids}, "default": variant}
                self.assertFalse(self.validator.is_valid(segment))
                self.assertTrue(any("unknown node" in error
                                    for error in self.room_errors(node_ids, variant=variant)))


if __name__ == "__main__":
    unittest.main()
