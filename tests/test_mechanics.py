"""Mechanics described in data/*.json that must actually apply in play.

The profile is changed only in memory and restored after each test; it is never saved.
"""
import copy
import io
import json
import os
import random
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

import data_manager
import roguelike
from data_manager import PROFILE_MANAGER
from entities import Consumable, Enemy, Player
from inventory_menu import _use_consumable
from rooms import CombatSession


class ProfileSandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        PROFILE_MANAGER._data["class_lvl"] = {}
        PROFILE_MANAGER._data["unlocked_ids"] = []
        random.seed(1234)

    def tearDown(self):
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)

    def quiet(self):
        return redirect_stdout(io.StringIO())


class MasteryTest(ProfileSandbox):
    def test_paladin_mastery_hp_bonus_starts_full(self):
        PROFILE_MANAGER.set_class_lvl("4", 4)
        player = Player("1", "base", [])
        self.assertEqual(player.hp, player.max_hp)

    def test_warrior_mastery_gives_defense_not_dodge(self):
        base = Player("2", "base", [])
        PROFILE_MANAGER.set_class_lvl("1", 4)
        player = Player("2", "base", [])
        self.assertEqual(player.bonus_def, 5)
        self.assertEqual(player.base_dodge, base.base_dodge)
        self.assertEqual(player.get_total_def(), base.get_total_def() + 5)

    def test_cursed_trait_bonus_applies_to_level_2_start_weapon(self):
        PROFILE_MANAGER.set_class_lvl("1", 2)
        self.assertGreaterEqual(Player("1", "maledetto", []).weapon.atk, 50)


class PotionTest(ProfileSandbox):
    def drink(self, player, heal=40):
        potion = Consumable("Pozione di prova", 10, heal, "heal")
        player.inventory = [potion]
        player.hp = 1
        with self.quiet(), mock.patch("builtins.input", return_value=""):
            _use_consumable(player, potion, 0, in_combat=False)
        return player.hp - 1

    def test_famine_pact_halves_potions(self):
        self.assertEqual(self.drink(Player("1", "base", ["carestia"])), 20)

    def test_alchemist_mastery_boosts_potions(self):
        PROFILE_MANAGER.set_class_lvl("6", 2)
        self.assertEqual(self.drink(Player("6", "base", [])), 60)

    def test_thief_mastery_can_save_the_potion(self):
        PROFILE_MANAGER.set_class_lvl("2", 2)
        player = Player("2", "base", [])
        with mock.patch("inventory_menu.random.random", return_value=0.0):
            self.drink(player)
        self.assertEqual(len(player.inventory), 1)


class TraitCombatTest(ProfileSandbox):
    def test_aristocrat_gets_no_gold_from_enemies(self):
        player = Player("1", "aristocratico", [])
        gold = player.gold
        session = CombatSession(player, 1, Enemy(1, False, []))
        session.enemy.hp = 0
        with self.quiet(), mock.patch("builtins.input", return_value=""):
            session.on_enemy_death()
        self.assertEqual(player.gold, gold)

    def test_ethereal_hunter_dodges_first_enemy_attack(self):
        player = Player("1", "cacciatore_etereo", [])
        session = CombatSession(player, 1, Enemy(1, False, []))
        session.enemy.base_acc = 1000
        with self.quiet():
            session.enemy_turn()
        self.assertEqual(player.hp, player.max_hp)


class RunRewardTest(ProfileSandbox):
    def test_winning_is_worth_at_least_escaping(self):
        rewards = {}
        for outcome in ("escaped", "won"):
            player = Player("1", "base", [])
            player.gold = 3000
            setattr(player, outcome, True)
            before = PROFILE_MANAGER.essence
            with self.quiet(), mock.patch.object(PROFILE_MANAGER, "save"), \
                 mock.patch("builtins.input", return_value=""), mock.patch("roguelike.delay_print"):
                roguelike.evaluate_run(player, 31 if outcome == "won" else 29, False)
            rewards[outcome] = PROFILE_MANAGER.essence - before
        self.assertGreaterEqual(rewards["won"], rewards["escaped"])


class ProfileFileTest(unittest.TestCase):
    def test_corrupted_profile_is_backed_up_and_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "profile.json")
            with open(path, "w", encoding="utf-8") as f:
                f.write("{ non è json")
            manager = data_manager.ProfileManager.__new__(data_manager.ProfileManager)
            manager.filepath = path
            with redirect_stdout(io.StringIO()):
                loaded = manager._load()
            self.assertEqual(loaded["essence"], 0)
            self.assertTrue(os.path.exists(path + ".corrotto"))
            with open(path, encoding="utf-8") as f:
                self.assertEqual(json.load(f)["essence"], 0)
            self.assertFalse(os.path.exists(path + ".tmp"))


if __name__ == "__main__":
    unittest.main()
