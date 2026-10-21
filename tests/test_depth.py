"""Enemies and bosses follow the depth; trait name, antidote and settings menu shown truthfully.

The profile is changed only in memory and restored after each test; it is never saved.
"""
import copy
import io
import random
import unittest
from contextlib import redirect_stdout
from unittest import mock

import roguelike
from constants import INFINITE_MODE_THRESHOLD
from data_manager import GAME_DATA, PROFILE_MANAGER
from entities import Consumable, Enemy, Player, pick_enemy_name
from inventory_menu import _use_consumable, show_player_stats


def power(category, name):
    d = GAME_DATA[category][name]
    return d["base_hp"] * d["base_atk"]


def pool(floor, is_boss, draws=300):
    return {pick_enemy_name(floor, is_boss) for _ in range(draws)}


class DepthTest(unittest.TestCase):
    def setUp(self):
        random.seed(1234)

    def test_final_boss_never_appears_before_the_last_floor(self):
        finals = {n for n, d in GAME_DATA["bosses"].items() if d.get("final_boss")}
        self.assertEqual(finals, {"DIO ANTICO"})
        for floor in range(1, INFINITE_MODE_THRESHOLD + 10):
            with self.subTest(floor=floor):
                self.assertFalse(pool(floor, True, 100) & finals)

    def test_last_standard_floor_has_the_final_boss(self):
        self.assertEqual(Enemy(INFINITE_MODE_THRESHOLD, True, [], final=True).name, "DIO ANTICO")

    def test_first_floor_only_offers_the_weakest_enemies(self):
        ranked = sorted(GAME_DATA["enemies"], key=lambda n: power("enemies", n))
        self.assertTrue(pool(1, False) <= set(ranked[:len(ranked) // 3]))

    def test_enemies_get_stronger_with_depth(self):
        for category, is_boss in (("enemies", False), ("bosses", True)):
            avg = [sum(power(category, n) for n in pool(f, is_boss)) / len(pool(f, is_boss)) for f in (1, 10, 20, 30)]
            with self.subTest(category=category):
                self.assertEqual(avg, sorted(avg))
                self.assertLess(avg[0] * 3, avg[-1])

    def test_last_door_of_floor_30_is_the_final_boss(self):
        doors = roguelike._generate_doors(INFINITE_MODE_THRESHOLD, 5, {"combat": 1}, {}, {}, [])
        self.assertEqual(doors[0]["enemy"].name, "DIO ANTICO")


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)

    def tearDown(self):
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)


class TruthfulUiTest(Sandbox):
    def test_stats_show_the_chosen_trait(self):
        player = Player("1", "maledetto", [])
        with redirect_stdout(io.StringIO()) as out, mock.patch("builtins.input", return_value=""), \
             mock.patch("inventory_menu.clear_screen"):
            show_player_stats(player)
        self.assertIn(f"Tratto: \x1b[95m{GAME_DATA['meta']['traits']['maledetto']['name']}", out.getvalue())

    def test_antidote_heals_what_its_label_says(self):
        player = Player("1", "base", [])
        antidote = Consumable("Antidoto Universale (Cura 25)", 10, 25, "antidote")
        player.inventory, player.hp = [antidote], 1
        player.statuses = {"poison": 2}
        with redirect_stdout(io.StringIO()), mock.patch("builtins.input", return_value=""):
            _use_consumable(player, antidote, 0, in_combat=False)
        self.assertEqual(player.hp, 26)
        self.assertEqual(player.statuses, {})

    def test_settings_menu_starts_on_current_speed(self):
        PROFILE_MANAGER._data["settings"]["text_speed"] = "veloce"
        with redirect_stdout(io.StringIO()), mock.patch("roguelike.clear_screen"), \
             mock.patch("roguelike.interactive_menu", return_value=-1) as menu:
            roguelike.settings_menu()
        self.assertEqual(menu.call_args.kwargs["initial"], 2)


if __name__ == "__main__":
    unittest.main()
