"""Text speed setting, Speranza di Luce, the Assassino and Negromante classes, real hit chance.

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

import roguelike
import ui
from constants import AMBUSH_DMG_PCT, NECRO_HARVEST_PCT, TEXT_SPEEDS
from data_manager import GAME_DATA, PROFILE_MANAGER, RAW_DATA, update_game_data
from entities import Enemy, Player
from inventory_menu import show_player_stats
from rooms import CombatSession

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        PROFILE_MANAGER._data["class_lvl"] = {}
        PROFILE_MANAGER._data["unlocked_ids"] = []
        random.seed(1234)

    def tearDown(self):
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)
        ui.set_text_speed(TEXT_SPEEDS[PROFILE_MANAGER.text_speed])
        update_game_data()

    def quiet(self):
        return redirect_stdout(io.StringIO())


class TextSpeedTest(Sandbox):
    def test_instant_text_never_sleeps(self):
        PROFILE_MANAGER.text_speed = "istantanea"
        with self.quiet(), mock.patch("ui.time.sleep") as sleep:
            ui.delay_print("ciao", 0.05)
        sleep.assert_not_called()

    def test_slow_text_scales_the_delay(self):
        PROFILE_MANAGER.text_speed = "lenta"
        with self.quiet(), mock.patch("ui.time.sleep") as sleep:
            ui.delay_print("ab", 0.02)
        self.assertEqual(sleep.call_count, 2)
        self.assertAlmostEqual(sleep.call_args[0][0], 0.03)

    def test_unknown_saved_speed_falls_back_to_default(self):
        PROFILE_MANAGER._data["settings"]["text_speed"] = "turbo"
        self.assertEqual(PROFILE_MANAGER.text_speed, "normale")


class FloorRegenTest(Sandbox):
    def test_regen_is_a_percentage_of_max_hp(self):
        PROFILE_MANAGER.set_perk("speranza_luce_lvl", 2)
        player = Player("1", "base", [])
        player.max_hp, player.hp = 200, 50
        with self.quiet():
            self.assertEqual(roguelike._apply_floor_regen(player), 20)
        self.assertEqual(player.hp, 70)

    def test_no_regen_without_the_perk(self):
        PROFILE_MANAGER.set_perk("speranza_luce_lvl", 0)
        player = Player("1", "base", [])
        player.hp = 1
        self.assertEqual(roguelike._apply_floor_regen(player), 0)


class NewClassesTest(Sandbox):
    def attack(self, session):
        # Nessuna variazione di danno, nessun critico, colpo sempre a segno
        roll = lambda low, high: 0 if low == -1 else 100
        before = session.enemy.hp
        with self.quiet(), mock.patch("rooms.random.randint", side_effect=roll):
            session.execute_player_attack()
        return before - session.enemy.hp

    def test_mastery_level_5_unlocks_the_new_classes(self):
        PROFILE_MANAGER.set_class_lvl("2", 5)
        PROFILE_MANAGER.set_class_lvl("3", 5)
        with mock.patch.object(PROFILE_MANAGER, "save"):
            roguelike._grant_retroactive_mastery_unlocks()
        self.assertIn("7", PROFILE_MANAGER.unlocked_ids)
        self.assertIn("8", PROFILE_MANAGER.unlocked_ids)

    def test_every_class_reward_points_to_an_existing_class(self):
        with open(os.path.join(DATA_DIR, "classes.json"), encoding="utf-8") as f:
            classes = json.load(f)
        for c_id, c in classes.items():
            for lvl, reward in c["mastery"].items():
                if reward["type"] == "class":
                    with self.subTest(class_id=c_id, level=lvl):
                        self.assertIn(reward["id"], classes)

    def test_assassin_ambush_boosts_only_the_first_attack(self):
        PROFILE_MANAGER.set_class_lvl("7", 2)
        player = Player("7", "base", [])
        player.attributes = dict.fromkeys(player.attributes, 0)  # solo l'Imboscata: gli attributi hanno i loro test
        session = CombatSession(player, 1, Enemy(1, False, []))
        session.enemy.hp, session.enemy.base_dodge = 10_000, -1000
        first, second = self.attack(session), self.attack(session)
        self.assertEqual(first, second * AMBUSH_DMG_PCT // 100)

    def test_ambush_does_not_stack_with_focused_attack(self):
        PROFILE_MANAGER.set_class_lvl("7", 2)
        player = Player("7", "base", [])
        player.attributes = dict.fromkeys(player.attributes, 0)  # solo l'Imboscata: gli attributi hanno i loro test
        session = CombatSession(player, 1, Enemy(1, False, []))
        session.enemy.hp, session.enemy.base_dodge = 10_000, -1000
        session.focused_attack = True
        focused = self.attack(session)
        self.assertEqual(focused, 2 * self.attack(session))
        self.assertFalse(session.first_player_attack)

    def test_assassin_has_innate_crit(self):
        crit = GAME_DATA["classes"]["7"]["crit"]
        self.assertGreater(crit, 0)
        # Al critico innato si aggiunge quello della Destrezza con cui parte la classe
        dex = GAME_DATA["classes"]["7"]["attributes"].get("destrezza", 0) * GAME_DATA["attributes"]["attributes"]["destrezza"]["per_point"]["crit"]
        self.assertEqual(Player("7", "base", []).get_crit_chance(), crit + dex)

    def test_necromancer_starts_with_dark_resonance_and_harvests_souls(self):
        PROFILE_MANAGER.set_class_lvl("8", 2)
        player = Player("8", "base", [])
        self.assertEqual(player._get_resonance_element(), "Tenebra")
        player.hp = 1
        session = CombatSession(player, 1, Enemy(1, False, []))
        session.enemy.hp = 0
        with self.quiet(), mock.patch("builtins.input", return_value=""):
            session.on_enemy_death()
        self.assertGreaterEqual(player.hp, 1 + player.max_hp * NECRO_HARVEST_PCT // 100)

    def test_global_mastery_bonuses(self):
        PROFILE_MANAGER.set_class_lvl("7", 4)
        PROFILE_MANAGER.set_class_lvl("8", 4)
        player = Player("1", "base", [])
        self.assertEqual(player.get_crit_chance(), 5)
        self.assertEqual(player.get_lifesteal(), 1)


class HitChanceTest(Sandbox):
    def test_stats_show_real_hit_chance(self):
        player = Player("3", "base", [])
        expected = min(100, 85 + player.base_acc)
        self.assertEqual(player.get_hit_chance(), expected)
        with self.quiet() as out, mock.patch("builtins.input", return_value=""), mock.patch("inventory_menu.clear_screen"):
            show_player_stats(player)
        self.assertIn(f"Probabilità di colpire: {expected}%", out.getvalue())

    def test_combat_stats_use_the_current_enemy(self):
        player = Player("3", "base", [])
        session = CombatSession(player, 1, Enemy(1, False, []))
        session.enemy.base_dodge = 60
        expected = session._calc_hit_chance(session.attack_multiplier())
        with self.quiet() as out, mock.patch("builtins.input", return_value=""), mock.patch("inventory_menu.clear_screen"):
            show_player_stats(player, session)
        self.assertIn(f"Probabilità di colpire: {expected}%", out.getvalue())
        self.assertLess(expected, player.get_hit_chance())


if __name__ == "__main__":
    unittest.main()
