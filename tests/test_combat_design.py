"""Resonance changes mid-combat, statuses ending with combat, weapons that inflict statuses.

The profile is changed only in memory and restored after each test; it is never saved.
"""
import copy
import io
import json
import os
import random
import unittest
from contextlib import redirect_stdout
from unittest import mock

from data_manager import PROFILE_MANAGER
from entities import Armor, Enemy, Player, Weapon
from rooms import CombatSession

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


class CombatSandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        PROFILE_MANAGER._data["class_lvl"] = {}
        random.seed(1234)
        self.player = Player("1", "base", [])
        self.player.weapon = Weapon("Spada", 10, 10, "Normale", 1)
        self.player.armor = Armor("Armatura", 10, 0, "Normale", 1)
        self.session = CombatSession(self.player, 1, Enemy(1, False, []))

    def tearDown(self):
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)

    def quiet(self):
        return redirect_stdout(io.StringIO())


class ResonanceTest(CombatSandbox):
    def test_equipping_mid_combat_activates_resonance(self):
        self.assertIsNone(self.session.resonance)
        self.player.weapon.element = self.player.armor.element = "Vento"
        with self.quiet():
            self.session.refresh_resonance()
        self.assertEqual(self.session.resonance, "Vento")
        self.assertEqual(self.player.temp_dodge, 15)

    def test_losing_resonance_removes_its_bonus(self):
        self.player.weapon.element = self.player.armor.element = "Terra"
        with self.quiet():
            self.session.refresh_resonance()
            self.player.weapon.element = "Fuoco"
            self.session.refresh_resonance()
        self.assertIsNone(self.session.resonance)
        self.assertEqual(self.player.temp_def, 0)

    def test_water_reduces_damage_without_changing_enemy_attack(self):
        self.session.enemy.atk = 40
        with mock.patch("rooms.random.randint", return_value=0):
            plain = self.session._calc_enemy_damage(1.0)
            self.player.weapon.element = self.player.armor.element = "Acqua"
            with self.quiet():
                self.session.refresh_resonance()
            reduced = self.session._calc_enemy_damage(1.0)
        self.assertEqual(self.session.enemy.atk, 40)
        self.assertEqual(plain, 40)
        self.assertEqual(reduced, 34)


class StatusTest(CombatSandbox):
    def test_player_statuses_end_with_combat(self):
        self.player.statuses = {"poison": 3, "bleed": 1}
        with self.quiet():
            self.session._end_combat()
        self.assertEqual(self.player.statuses, {})

    def test_weapon_can_inflict_status_on_enemy(self):
        self.player.weapon.status_inflict = {"type": "bleed", "chance": 100, "duration": 3}
        self.session.enemy.hp = 10_000
        self.session.enemy.base_dodge = -1000
        with self.quiet(), mock.patch("builtins.input", return_value=""):
            self.session.execute_player_attack()
        self.assertEqual(self.session.enemy.statuses.get("bleed"), 3)

    def test_status_definitions_are_valid(self):
        def load(name):
            with open(os.path.join(DATA_DIR, name), encoding="utf-8") as f:
                return json.load(f)
        weapons = [(w["name"], w.get("status_inflict")) for w in load("weapons.json")["weapons"]]
        enemies = load("enemies.json")
        foes = [(n, d.get("status_inflict")) for c in ("enemies", "bosses") for n, d in enemies[c].items()]
        self.assertTrue(any(s for _, s in weapons), "nessuna arma infligge status")
        defined = [(n, s) for n, s in weapons + foes if s]
        for name, s in defined:
            with self.subTest(source=name):
                self.assertIn(s["type"], ("poison", "bleed"))
                self.assertTrue(1 <= s["chance"] <= 100)
                self.assertGreater(s["duration"], 0)


if __name__ == "__main__":
    unittest.main()
