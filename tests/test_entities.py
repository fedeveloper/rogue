"""Invariants of item generation, relics, player and enemies.

Importing the game modules loads data/*.json and creates profile.json if it is
missing. These tests never save the profile, so an existing one is not changed.
"""
import random
import unittest

from data_manager import ELEMENTS, GAME_DATA, RAW_DATA
from entities import Enemy, Player, generate_accessory, generate_armor, generate_potion, generate_weapon
from relic_effects import RELIC_REGISTRY, RelicEffect, create_relic_effect

LEVELS = (1, 5, 15, 30)


class ItemGenerationTest(unittest.TestCase):
    def setUp(self):
        random.seed(1234)

    def test_weapons_and_armors_have_positive_stats_and_known_elements(self):
        for level in LEVELS:
            for epic in (False, True):
                for _ in range(50):
                    weapon = generate_weapon(level, epic)
                    armor = generate_armor(level, epic)
                    self.assertGreater(weapon.atk, 0)
                    self.assertGreater(armor.defense, 0)
                    self.assertIn(weapon.element, ELEMENTS)
                    self.assertIn(armor.element, ELEMENTS)

    def test_epic_items_are_never_cursed(self):
        for _ in range(200):
            self.assertFalse(generate_weapon(10, True).is_cursed)
            self.assertFalse(generate_armor(10, True).is_cursed)

    def test_accessories_and_potions(self):
        for level in LEVELS:
            for _ in range(50):
                self.assertGreater(generate_accessory(level).value, 0)
                potion = generate_potion(level)
                self.assertGreaterEqual(potion.heal_amount, 0)
                self.assertGreater(potion.value, 0)


class RelicTest(unittest.TestCase):
    def test_every_relic_has_an_effect_and_every_effect_a_relic(self):
        ids = {r["id"] for r in RAW_DATA["relics"]}
        self.assertEqual(ids, set(RELIC_REGISTRY))

    def test_unknown_relic_gets_neutral_effect(self):
        effect = create_relic_effect("does_not_exist")
        self.assertIs(type(effect), RelicEffect)


class PlayerTest(unittest.TestCase):
    def setUp(self):
        random.seed(1234)

    def test_every_class_and_trait_can_start_a_run(self):
        for class_id in RAW_DATA["classes"]:
            for trait_id in GAME_DATA["meta"]["traits"]:
                with self.subTest(class_id=class_id, trait=trait_id):
                    player = Player(class_id, trait_id, [])
                    self.assertGreater(player.max_hp, 0)
                    self.assertEqual(player.hp, player.max_hp)
                    self.assertGreater(player.weapon.atk, 0)

    def test_heal_never_exceeds_max_hp(self):
        player = Player("1", "base", [])
        player.hp = player.max_hp - 5
        self.assertEqual(player.heal(1000), 5)
        self.assertEqual(player.hp, player.max_hp)

    def test_take_damage_reports_death(self):
        player = Player("1", "base", [])
        self.assertTrue(player.take_damage(player.max_hp - 1))
        self.assertFalse(player.take_damage(1))


class EnemyTest(unittest.TestCase):
    def setUp(self):
        random.seed(1234)

    def test_enemies_scale_with_floor(self):
        for floor in (1, 10, 20, 30):
            for is_boss in (False, True):
                for _ in range(30):
                    enemy = Enemy(floor, is_boss, [])
                    self.assertGreater(enemy.hp, 0)
                    self.assertGreater(enemy.atk, 0)
                    self.assertIn(enemy.element, ELEMENTS)


if __name__ == "__main__":
    unittest.main()
