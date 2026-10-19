"""Schema and reference checks for repeatable purchase effects."""

import json
import unittest
from collections import defaultdict

from jsonschema import validators

from validate import ROOT, validate_room


class PurchaseSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        schema = json.loads((ROOT / "schema/z3-requirement.schema.json").read_text())
        cls.validator = validators.validator_for(schema)(schema)

    def test_capacity_upgrade_only_accepts_ammunition(self):
        for resource in ["Bombs", "Arrows"]:
            self.assertTrue(self.validator.is_valid({"upgradeCapacity": resource}))
        for resource in ["Health", "Rupee", 5, {"type": "Bombs"}]:
            self.assertFalse(self.validator.is_valid({"upgradeCapacity": resource}))

    def grant_errors(self, receipt):
        document = {
            "roomType": "House",
            "nodes": [{"id": 1}],
            "strats": [{"link": [1, 1], "name": "Buy Shield",
                        "requires": [{"pay": 50}], "grantsItems": [receipt]}],
        }
        errors = defaultdict(list)
        validate_room(ROOT / "rooms/test.json", document,
                      {"items": {"BlueShield": {}}, "flags": {}}, errors)
        return [error for messages in errors.values() for error in messages]

    def test_grant_uses_receipt_without_item_location(self):
        self.assertEqual(self.grant_errors("BlueShield"), [])

    def test_unknown_grant_receipt_is_rejected(self):
        errors = self.grant_errors("TypoShield")
        self.assertEqual(len(errors), 1)
        self.assertIn('/grantsItems/0: unknown item "TypoShield"', errors[0])


if __name__ == "__main__":
    unittest.main()
