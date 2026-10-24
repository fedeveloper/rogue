"""Combat menu loop, menu redraw with wrapped lines, bonuses read from data, output routed through ui.

The profile is changed only in memory and restored after each test; it is never saved.
"""
import ast
import copy
import io
import json
import os
import random
import unittest
from contextlib import redirect_stdout
from unittest import mock

import ui
from archive import get_archive_bonus
from data_manager import GAME_DATA, PROFILE_MANAGER
from entities import Enemy, Player
from rooms import CombatSession
from constants import BERSERKER_FURY_PCT

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return json.load(f)


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        PROFILE_MANAGER._data["class_lvl"] = {}
        random.seed(1234)

    def tearDown(self):
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)


class CombatLoopTest(Sandbox):
    def test_free_actions_do_not_recurse(self):
        player = Player("1", "base", [])
        session = CombatSession(player, 1, Enemy(1, True, []))
        session.enemy.hp, session.enemy.base_dodge = 10_000, -1000
        # Molte più aperture delle statistiche del limite di ricorsione, poi fuga dal boss, poi attacco
        menu = [4] * 1500 + [5, 0]  # Statistiche e Fuga vengono dopo Attacca, Difesa, Incantesimi, Inventario
        with redirect_stdout(io.StringIO()), mock.patch("rooms.interactive_menu", side_effect=menu), \
             mock.patch("rooms.clear_screen"), mock.patch("inventory_menu.show_player_stats"), \
             mock.patch("builtins.input", return_value=""):
            self.assertTrue(session.player_turn())
        self.assertLess(session.enemy.hp, 10_000)


class MenuRedrawTest(unittest.TestCase):
    def test_visible_width_ignores_colors_and_counts_wide_glyphs(self):
        self.assertEqual(ui.visible_width(f"{ui.Colors.GREEN}ciao{ui.Colors.RESET}"), 4)
        self.assertEqual(ui.visible_width("❤️  HP"), 6)
        self.assertEqual(ui.screen_rows("x" * 200, 80), 3)

    def test_redraw_moves_up_by_the_wrapped_rows(self):
        options = ["x" * 50, "breve"]
        out = io.StringIO()
        with redirect_stdout(out), mock.patch("ui.get_key", side_effect=["DOWN", "ENTER"]), \
             mock.patch("ui.shutil.get_terminal_size", return_value=os.terminal_size((20, 24))):
            self.assertEqual(ui.interactive_menu(options), 1)
        # "    " + 50 caratteri = 54 colonne -> 3 righe; "    breve" -> 1; riga vuota finale -> 1
        self.assertIn("\x1b[5A\r\x1b[J", out.getvalue())
        self.assertTrue(out.getvalue().endswith("\x1b[?25h"))


class DataDrivenBonusTest(Sandbox):
    STATS = {"def", "dodge", "exp", "max_hp", "weapon_atk", "acc", "crit", "lifesteal"}

    def test_every_class_has_data_driven_mastery(self):
        for c_id, c in load("classes.json").items():
            with self.subTest(class_id=c_id):
                self.assertTrue(c["mastery"]["2"].get("effect"))
                self.assertIn(c["mastery"]["4"]["bonus"]["stat"], self.STATS)

    def test_global_mastery_bonuses_keep_their_values(self):
        base = Player("1", "base", [])
        for c_id in GAME_DATA["classes"]: PROFILE_MANAGER.set_class_lvl(c_id, 4)
        boosted = Player("1", "base", [])
        self.assertEqual(boosted.bonus_def - base.bonus_def, 5)
        self.assertEqual(boosted.base_dodge - base.base_dodge, 10)
        self.assertAlmostEqual(boosted.exp_multiplier - base.exp_multiplier, 0.15)
        self.assertEqual(boosted.max_hp - base.max_hp, 15 + 10)  # Paladino ed Elementalista
        self.assertEqual(boosted.base_acc - base.base_acc, 5)
        self.assertEqual(boosted.base_crit - base.base_crit, 5)
        self.assertEqual(boosted.base_lifesteal - base.base_lifesteal, 1)

    def test_personal_mastery_effects(self):
        PROFILE_MANAGER.set_class_lvl("1", 2)
        self.assertEqual(Player("1", "base", []).weapon.level, 2)
        PROFILE_MANAGER.set_class_lvl("5", 2)
        berserker = Player("5", "base", [])
        berserker.hp = 1
        self.assertEqual(berserker.get_dodge(), 0)
        self.assertEqual(berserker.get_class_damage_multiplier(), 1 + BERSERKER_FURY_PCT / 100)
        self.assertFalse(Player("1", "base", []).has_mastery_effect("berserker_fury"))

    def test_resonance_defined_for_every_element(self):
        elements = load("elements.json")
        for el in elements["list"]:
            if el != "Normale":
                with self.subTest(element=el):
                    self.assertIn("value", elements["resonance"][el])
                    self.assertTrue(elements["resonance"][el]["announce"])

    def test_archive_bonuses_come_from_books(self):
        profile = {"max_floor": 5, "stats": {"total_bosses": 5}, "won_normal": True}
        self.assertEqual(get_archive_bonus("gold_pct", profile), 5)
        self.assertEqual(get_archive_bonus("escape", profile), 5)
        self.assertEqual(get_archive_bonus("boss_dmg_pct", profile), 10)
        self.assertEqual(get_archive_bonus("def", profile), 5)
        self.assertEqual(get_archive_bonus("def", {"max_floor": 0, "stats": {}, "won_normal": False}), 0)


class ConsumableLabelTest(unittest.TestCase):
    def test_only_healing_items_show_a_cure_amount(self):
        from entities import HEALING_CATEGORIES, generate_potion
        random.seed(1234)
        for _ in range(300):
            item = generate_potion(5)
            with self.subTest(item=item.name):
                if item.category in HEALING_CATEGORIES:
                    self.assertEqual(item.name.endswith(f"(Cura {item.heal_amount})"), item.heal_amount > 0)
                else:
                    self.assertNotIn("Cura", item.name)
                    self.assertEqual(item.heal_amount, 0)


class OutputThroughUiTest(unittest.TestCase):
    def test_game_modules_do_not_call_print_or_input_directly(self):
        for name in ("rooms.py", "inventory_menu.py", "roguelike.py", "archive.py"):
            with open(os.path.join(ROOT, name), encoding="utf-8") as f:
                tree = ast.parse(f.read())
            direct = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Call)
                      and isinstance(n.func, ast.Name) and n.func.id in ("print", "input")]
            with self.subTest(module=name):
                self.assertEqual(direct, [])


if __name__ == "__main__":
    unittest.main()
