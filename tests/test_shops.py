"""Artisan shops at base camp, the Forge listing and the Dragon Heart relic.

The profile is changed only in memory and restored after each test; it is never saved.
"""
import copy
import io
import unittest
from contextlib import redirect_stdout

import roguelike
from data_manager import GAME_DATA, PROFILE_MANAGER, RAW_DATA, update_game_data
from entities import Player
from relic_effects import create_relic_effect

ALL_UNLOCKS = sorted({i["unlock_id"] for cat in ("weapons", "armors", "accessories", "consumables", "relics")
                      for i in RAW_DATA[cat] if i.get("unlock_id")})


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        PROFILE_MANAGER._data["unlocked_ids"] = list(ALL_UNLOCKS)
        PROFILE_MANAGER._data["class_lvl"] = {}
        update_game_data()

    def tearDown(self):
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)
        update_game_data()

    def new_player(self, trait="base"):
        with redirect_stdout(io.StringIO()):
            return Player("1", trait, [])


class ShopTest(Sandbox):
    def test_every_item_sold_by_the_artisans_reaches_the_next_run(self):
        for npc, (cat, defaults, key) in roguelike.NPC_SHOPS.items():
            for name, _cost in roguelike.npc_shop_items(cat, defaults):
                with self.subTest(npc=npc, item=name):
                    for k in ("starting_consumables", "starting_weapons", "starting_armors", "starting_accessories"):
                        PROFILE_MANAGER._data[k] = []
                    PROFILE_MANAGER._data[key] = [name]
                    player = self.new_player()
                    self.assertTrue(any(it.name.startswith(name) for it in player.inventory))
                    self.assertEqual(PROFILE_MANAGER._data[key], [])

    def test_a_broken_purchase_never_blocks_later_runs(self):
        GAME_DATA["weapons"].append({"name": "Arma Rotta"})  # manca base_atk
        try:
            PROFILE_MANAGER._data["starting_weapons"] = ["Arma Rotta"]
            player = self.new_player()
        finally:
            GAME_DATA["weapons"].pop()
        self.assertFalse(any(it.name == "Arma Rotta" for it in player.inventory))
        self.assertEqual(PROFILE_MANAGER._data["starting_weapons"], [])


class ForgeTest(Sandbox):
    def test_everything_unlocked_means_nothing_left_in_the_forge(self):
        for cat in ("relics", "weapons", "armors", "consumables", "accessories"):
            with self.subTest(category=cat):
                self.assertEqual(roguelike.locked_forge_items(cat), [])

    def test_items_without_unlock_id_are_never_listed(self):
        PROFILE_MANAGER._data["unlocked_ids"] = []
        listed = {i["name"] for i in roguelike.locked_forge_items("accessories")}
        base = {i["name"] for i in RAW_DATA["accessories"] if not i.get("unlock_id")}
        self.assertTrue(base)
        self.assertFalse(listed & base)


class DragonHeartTest(Sandbox):
    def test_hit_points_arrive_together_with_the_maximum(self):
        for trait in ("base", "maledetto"):
            with self.subTest(trait=trait):
                player = self.new_player(trait)
                before_hp, before_max = player.hp, player.max_hp
                effect = create_relic_effect("cuore_drago")
                effect.on_equip(player)
                self.assertEqual(player.max_hp, before_max + 50)
                self.assertEqual(player.hp, before_hp + 50)
                effect.on_unequip(player)
                self.assertEqual(player.max_hp, before_max)
                self.assertLessEqual(player.hp, player.max_hp)


if __name__ == "__main__":
    unittest.main()
