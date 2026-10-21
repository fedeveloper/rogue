"""Consistency checks on the game data in data/*.json."""
import json
import os
import unittest

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def load(name):
    with open(os.path.join(DATA_DIR, name), encoding="utf-8") as f:
        return json.load(f)


class DataFilesTest(unittest.TestCase):
    def test_every_data_file_is_valid_json(self):
        for name in sorted(os.listdir(DATA_DIR)):
            if name.endswith(".json"):
                with self.subTest(file=name):
                    load(name)

    def test_elements_have_icons_and_known_multipliers(self):
        elements = load("elements.json")
        names = set(elements["list"])
        self.assertIn("Normale", names)
        self.assertEqual(set(elements["icons"]), names)
        for attacker, row in elements["multipliers"].items():
            self.assertIn(attacker, names)
            for defender, value in row.items():
                self.assertIn(defender, names, f"{attacker} -> {defender}")
                self.assertGreater(value, 0)

    def test_enemies_and_bosses_use_known_elements(self):
        names = set(load("elements.json")["list"])
        enemies = load("enemies.json")
        for category in ("enemies", "bosses"):
            self.assertTrue(enemies[category], category)
            for name, data in enemies[category].items():
                with self.subTest(enemy=name):
                    self.assertIn(data["element"], names)
                    self.assertGreater(data["base_hp"], 0)
                    self.assertGreater(data["base_atk"], 0)

    def test_classes_have_starting_equipment(self):
        names = set(load("elements.json")["list"])
        for class_id, data in load("classes.json").items():
            with self.subTest(class_id=class_id):
                self.assertGreater(data["max_hp"], 0)
                self.assertIn(data["weapon"].get("element", "Normale"), names)
                self.assertIn(data["armor"].get("element", "Normale"), names)
                self.assertGreaterEqual(data["potions"], 0)

    def test_mastery_requirements_increase(self):
        reqs = load("meta.json")["mastery_xp_requirements"]
        values = [reqs[str(level)] for level in range(2, 6)]
        self.assertEqual(values, sorted(values))
        self.assertEqual(len(set(values)), len(values))

    def test_relic_ids_are_unique(self):
        ids = [r["id"] for r in load("relics.json")["relics"]]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
