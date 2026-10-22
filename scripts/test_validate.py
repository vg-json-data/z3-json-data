"""Regression checks for special overworld edge references."""

import json
import unittest
from collections import defaultdict

from jsonschema import validators

from validate import ROOT, collect_references, registry_for, validate_requirements, validate_room


class ItemCategoryTests(unittest.TestCase):
    def test_section_notes_and_nested_items_are_indexed(self):
        document = {
            "$schema": "./schema/z3-items.schema.json",
            "inventory": {"note": "Equipment", "items": [{"name": "Bow"}]},
            "refills": {"note": "Rewards", "items": [{"name": "OneArrow"}]},
            "nonVanilla": {"items": [{"name": "Bow"}]},
            "flags": {"note": "Events", "items": ["DefeatedGanon"]},
        }
        path = ROOT / "items.json"
        errors = defaultdict(list)
        references = collect_references({path: document}, errors)
        self.assertEqual(set(references["items"]), {"Bow", "OneArrow"})
        self.assertEqual(set(references["flags"]), {"DefeatedGanon"})
        self.assertEqual(len(errors[path]), 1)
        self.assertIn('/nonVanilla/items/0:"Bow"/name', errors[path][0])
        self.assertIn('/inventory/items/0:"Bow"/name', errors[path][0])


class DetailNoteTests(unittest.TestCase):
    def test_detail_note_format_at_every_supported_location(self):
        schemas = [json.loads(path.read_text(encoding="utf-8"))
                   for path in (ROOT / "schema").glob("*.schema.json")]
        registry = registry_for(schemas)
        locations = []

        def walk(value):
            if isinstance(value, dict):
                properties = value.get("properties", {})
                if "note" in properties:
                    self.assertIn("detailNote", properties)
                    locations.append(properties["detailNote"])
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        for schema in schemas:
            walk(schema)
        self.assertTrue(locations)
        for location in locations:
            validator = validators.Draft7Validator(location, registry=registry)
            for value in [["Step one", "Step two"], []]:
                self.assertTrue(validator.is_valid(value))
            for value in ["Extra detail", "", 1, True, None, {}, ["Step one", 2]]:
                self.assertFalse(validator.is_valid(value))


class NotableTests(unittest.TestCase):
    def room_errors(self, notables, requires, **extra):
        document = {
            "id": 1, "name": "Test", "roomType": "Dungeon",
            "nodes": [{"id": 1, "name": "Boss", "nodeType": "boss"}],
            "notables": notables,
            "strats": [{"link": [1, 1], "name": "Fight", "requires": requires}],
            **extra,
        }
        errors = defaultdict(list)
        references = {"items": {}, "flags": {}, "named": {}}
        validate_room(ROOT / "rooms/test.json", document, references, errors)
        return [error for messages in errors.values() for error in messages]

    def test_room_scope_and_nested_requirements(self):
        notable = {"id": 1, "name": "Trick", "note": []}
        requirement = {"or": [{"and": [{"notable": "Trick"}, "free"]}, "never"]}
        self.assertEqual(self.room_errors([notable], [requirement], nextNotableId=2), [])
        errors = self.room_errors([], [requirement])
        self.assertEqual(len(errors), 1)
        self.assertIn('unknown room-local notable "Trick"', errors[0])
        self.assertEqual(self.room_errors([notable], [{"notable": "Trick"}]), [])

    def test_unique_ids_and_names(self):
        for second in [{"id": 1, "name": "Other", "note": []},
                       {"id": 2, "name": "Trick", "note": []}]:
            with self.subTest(second=second):
                errors = self.room_errors([{"id": 1, "name": "Trick", "note": []}, second], [])
                self.assertEqual(len(errors), 1)
                self.assertIn("duplicates definition", errors[0])

    def test_next_id_must_exceed_existing_ids(self):
        errors = self.room_errors([{"id": 3, "name": "Trick", "note": []}], [], nextNotableId=3)
        self.assertEqual(len(errors), 1)
        self.assertIn("/nextNotableId", errors[0])

    def test_notables_rejected_outside_rooms(self):
        document = [{"notable": "Trick"}]
        errors = defaultdict(list)
        validate_requirements(ROOT / "helpers.json", document, document, [], {}, errors)
        self.assertIn('unknown room-local notable "Trick"', next(iter(errors.values()))[0])

    def test_schema_validates_notable_definitions_and_requirements(self):
        schemas = [json.loads(path.read_text(encoding="utf-8"))
                   for path in (ROOT / "schema").glob("*.schema.json")]
        room_schema = next(schema for schema in schemas if schema["$id"] == "z3-room.schema.json")
        validator = validators.validator_for(room_schema)(room_schema, registry=registry_for(schemas))
        document = {
            "id": 1, "name": "Test", "roomType": "Dungeon", "nodes": [],
            "notables": [{"id": 1, "name": "Trick", "note": ["Description"]}],
            "nextNotableId": 2,
            "strats": [{"link": [1, 1], "name": "Test", "requires": [{"notable": "Trick"}]}],
        }
        self.assertEqual(list(validator.iter_errors(document)), [])
        without_next_id = {key: value for key, value in document.items() if key != "nextNotableId"}
        self.assertFalse(validator.is_valid(without_next_id))
        self.assertFalse(validator.is_valid({**without_next_id, "notables": []}))
        without_notables = {key: value for key, value in without_next_id.items() if key != "notables"}
        self.assertTrue(validator.is_valid(without_notables))
        for field, value in [("id", 0), ("name", ""), ("note", "Description")]:
            with self.subTest(field=field):
                invalid = {**document, "notables": [{**document["notables"][0], field: value}]}
                self.assertFalse(validator.is_valid(invalid))
        for value in [1, "", True]:
            document["strats"][0]["requires"] = [{"notable": value}]
            self.assertFalse(validator.is_valid(document))


class SecondaryItemReferenceTests(unittest.TestCase):
    def room_errors(self, secondary):
        document = {
            "roomType": "House",
            "nodes": [{"id": 1}],
            "items": [{"id": 1, "itemLocation": 1, "item": "BlueBoomerang",
                       "secondaryItem": secondary}],
            "strats": [],
        }
        names = {name: {} for name in ["BlueBoomerang", "RedBoomerang", "TenArrows"]}
        errors = defaultdict(list)
        validate_room(ROOT / "rooms/test.json", document,
                      {"items": names, "named": names}, errors)
        return [error for messages in errors.values() for error in messages]

    def test_known_secondary_item(self):
        self.assertEqual(self.room_errors("TenArrows"), [])

    def test_unknown_secondary_item(self):
        errors = self.room_errors("TypoArrows")
        self.assertEqual(len(errors), 1)
        self.assertIn('/secondaryItem: unknown item "TypoArrows"', errors[0])


class OverheadStateTests(unittest.TestCase):
    def setUp(self):
        schemas = [json.loads(path.read_text(encoding="utf-8"))
                   for path in (ROOT / "schema").glob("*.schema.json")]
        schema = next(schema for schema in schemas if schema["$id"] == "z3-room.schema.json")
        self.validator = validators.validator_for(schema)(schema, registry=registry_for(schemas))
        self.room = {
            "id": 1, "name": "Test", "roomType": "Overworld", "size": [2, 2],
            "edgeVariants": {
                edge: [{"supported": {"wide": [1]}, "default": "wide"}]
                for edge in ["north", "south", "east", "west"]
            },
            "nodes": [{"id": 1, "name": "Edge", "world": "both"},
                      {"id": 2, "name": "Interior", "world": "both"}],
            "strats": [{"link": [1, 1], "name": "Carry", "world": "dark", "requires": []}],
        }

    def errors(self):
        errors = defaultdict(list)
        validate_room(ROOT / "rooms/test.json", self.room, {"items": {}, "flags": {}}, errors)
        return [error for messages in errors.values() for error in messages]

    def test_both_strengths_and_implicit_round_trip(self):
        strat = self.room["strats"][0]
        for strength in ["class1", "class3"]:
            state = {"state": "overhead", "type": strength}
            strat.update(entranceState=state, exitState=state)
            with self.subTest(strength=strength):
                self.assertTrue(self.validator.is_valid(self.room))
                self.assertEqual(self.errors(), [])

    def test_invalid_overhead_states(self):
        for field in ["entranceState", "exitState"]:
            for state in [
                {"state": "overhead"},
                {"state": "overhead", "type": "class2"},
                {"state": "overhead", "type": "pot"},
                {"state": "overhead", "type": "class3", "entranceID": 1},
            ]:
                with self.subTest(field=field, state=state):
                    self.room["strats"][0] = {
                        "link": [1, 1], "name": "Carry", "world": "dark", "requires": [], field: state
                    }
                    self.assertFalse(self.validator.is_valid(self.room))

    def test_underworld_and_world_changes_rejected(self):
        for field in ["entranceState", "exitState"]:
            state = {"state": "overhead", "type": "class3"}
            self.room["strats"][0] = {
                "link": [1, 1], "name": "Carry", "fromWorld": "dark", "toWorld": "light",
                "requires": [], field: state,
            }
            self.assertFalse(self.validator.is_valid(self.room))
            interior = {
                "id": 1, "name": "Interior", "roomType": "Cave",
                "nodes": [{"id": 1, "name": "Door", "nodeType": "door"}],
                "strats": [{"link": [1, 1], "name": "Carry", "requires": [], field: state}],
            }
            self.assertFalse(self.validator.is_valid(interior))
            interior["strats"][0][field] = {"state": "event", "type": "DrainedFloodgate"}
            self.assertTrue(self.validator.is_valid(interior))

    def test_event_entrance_id_rule_is_preserved(self):
        for field in ["entranceState", "exitState"]:
            strat = {"link": [1, 1], "name": "Event", "world": "light", "requires": [],
                     field: {"state": "event", "type": "DrainedFloodgate"}}
            self.room["strats"] = [strat]
            self.assertFalse(self.validator.is_valid(self.room))
            strat[field]["entranceID"] = 1
            self.assertTrue(self.validator.is_valid(self.room))

    def test_state_checks_the_correct_endpoint(self):
        strat = self.room["strats"][0]
        for field, valid_link, invalid_link in [
            ("entranceState", [1, 2], [2, 1]),
            ("exitState", [2, 1], [1, 2]),
        ]:
            strat.pop("entranceState", None)
            strat.pop("exitState", None)
            strat[field] = {"state": "overhead", "type": "class3"}
            strat["link"] = valid_link
            self.assertEqual(self.errors(), [])
            strat["link"] = invalid_link
            errors = self.errors()
            self.assertEqual(len(errors), 1)
            self.assertIn("overhead state endpoint node has no overworld screen transition", errors[0])


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
