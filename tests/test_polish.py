"""Messages and menu flow around combat, the campfire and the Soul Fire perks.

The profile is changed only in memory and restored after each test; it is never saved.
"""
import copy
import io
import random
import unittest
from constants import MIN_DAMAGE_PCT
from contextlib import redirect_stdout
from unittest import mock

import roguelike
from data_manager import PROFILE_MANAGER
from entities import Armor, Enemy, Player, Weapon
from relic_effects import create_relic_effect
from rooms import CombatSession, campfire_room


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        PROFILE_MANAGER._data["class_lvl"] = {}
        random.seed(1234)
        self.player = Player("1", "base", [])
        self.player.armor = Armor("Armatura", 10, 0, "Normale", 1)

    def tearDown(self):
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)

    def run_quietly(self, func, *args, menu=None):
        out = io.StringIO()
        patches = [mock.patch("builtins.input", return_value=""), mock.patch("time.sleep"),
                   mock.patch("rooms.delay_print"), mock.patch("rooms.clear_screen"),
                   mock.patch("roguelike.clear_screen")]
        if menu is not None:
            patches.append(mock.patch("rooms.interactive_menu", side_effect=menu))
            patches.append(mock.patch("roguelike.interactive_menu", side_effect=menu))
        with redirect_stdout(out):
            for p in patches: p.start()
            try:
                func(*args)
            finally:
                for p in patches: p.stop()
        return out.getvalue()


class CombatMessageTest(Sandbox):
    def test_relic_negated_hit_does_not_claim_armor_blocked_it(self):
        self.player.relic_effects.append(create_relic_effect("scudo_cristallo"))
        session = CombatSession(self.player, 1, Enemy(1, False, []))
        session.enemy.atk, session.enemy.base_acc = 50, 1000
        output = self.run_quietly(session.enemy_turn)
        self.assertIn("Scudo di Cristallo", output)
        self.assertNotIn("blocca TUTTO", output)
        self.assertEqual(self.player.hp, self.player.max_hp)

    def test_armor_reduces_but_never_blocks_everything(self):
        # Prima una difesa altissima annullava ogni colpo; ora resta sempre MIN_DAMAGE_PCT del danno grezzo
        self.player.armor.defense = 1000
        session = CombatSession(self.player, 1, Enemy(1, False, []))
        session.enemy.atk, session.enemy.element, session.enemy.base_acc = 50, "Normale", 1000
        with mock.patch("rooms.random.randint", side_effect=lambda a, b: a if a == -1 else 1):
            output = self.run_quietly(session.enemy_turn)
        self.assertNotIn("blocca TUTTO", output)
        raw = 50 - 1
        self.assertEqual(self.player.max_hp - self.player.hp, -(-raw * MIN_DAMAGE_PCT // 100))

    def test_escape_chance_stays_within_cap(self):
        self.player.base_dodge = 500
        session = CombatSession(self.player, 1, Enemy(1, False, []))
        # Diario di Silas sbloccato: +5% di fuga, che non deve superare il limite del 90%
        with mock.patch("rooms.get_archive_bonus", side_effect=lambda stat, profile: 5 if stat == "escape" else 0):
            self.assertEqual(session._calc_escape_chance(), 90)

    def test_compass_relic_still_guarantees_escape(self):
        self.player.relic_effects.append(create_relic_effect("bussola_perfetta"))
        session = CombatSession(self.player, 1, Enemy(1, False, []))
        self.assertEqual(session._calc_escape_chance(), 100)


class CampfireTest(Sandbox):
    def test_fusion_returns_to_campfire_menu(self):
        self.player.inventory = [Weapon("Spada A", 10, 10, "Normale", 1), Weapon("Spada B", 10, 6, "Normale", 1)]
        # Altare -> primo oggetto -> secondo oggetto -> di nuovo al Falò: Riposa
        menu = [2, 0, 1, 0]
        self.player.hp = 1
        self.run_quietly(campfire_room, self.player, 1, menu=menu)
        self.assertEqual(len(self.player.inventory), 1)
        self.assertEqual(self.player.inventory[0].atk, 13)
        self.assertGreater(self.player.hp, 1, "dopo la fusione si deve poter ancora riposare")

    def test_purification_returns_to_campfire_menu(self):
        self.player.weapon = Weapon("Spada", 10, 10, "Normale", 1, is_cursed=True, curse_effect="gold_drain")
        self.player.gold = 100
        self.player.hp = 1
        # Purifica (indice 3) -> primo oggetto maledetto -> di nuovo al Falò: Riposa
        self.run_quietly(campfire_room, self.player, 1, menu=[3, 0, 0])
        self.assertFalse(self.player.weapon.is_cursed)
        self.assertEqual(self.player.gold, 0)
        self.assertGreater(self.player.hp, 1, "dopo la purificazione si deve poter ancora riposare")


class SoulFireTest(Sandbox):
    def test_insufficient_essence_is_reported(self):
        PROFILE_MANAGER.essence = 0
        with mock.patch.object(PROFILE_MANAGER, "save"):
            output = self.run_quietly(roguelike.base_camp_fire, menu=[0, -1])
        self.assertIn("Essenza insufficiente", output)
        self.assertEqual(PROFILE_MANAGER.get_perk("hp_lvl", 0), self._saved["perks"].get("hp_lvl", 0))


if __name__ == "__main__":
    unittest.main()
