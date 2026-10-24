"""L'Elementalista, la nona classe: dati, equipaggiamento che reagisce con i suoi incantesimi, difesa Prisma Elementale,
Catena Elementale (Maestria Lv.2), sblocco con l'impresa Alchimia degli Elementi."""
import copy
import io
import random
import unittest
from contextlib import redirect_stdout
from unittest import mock

import magic
import roguelike
from constants import ELEMENTAL_CHAIN_ETHER
from data_manager import GAME_DATA, PROFILE_MANAGER
from entities import Enemy, Player
from rooms import CombatSession, reaction_key

CLS = GAME_DATA["classes"]["9"]
PRISM = GAME_DATA["defenses"]["prism"]


def quiet():
    return redirect_stdout(io.StringIO())


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        self._save = mock.patch.object(PROFILE_MANAGER, "save")
        self._save.start()
        random.seed(3)

    def tearDown(self):
        self._save.stop()
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)

    def hero(self, lvl=1):
        PROFILE_MANAGER.set_class_lvl("9", lvl)
        with quiet(): p = Player("9", "base", [])
        p.base_ether, p.ether = 100, 0
        return p

    def session(self, p):
        with quiet(): s = CombatSession(p, 3, Enemy(3, False, [], name="Goblin"))
        s.enemy.hp = s.enemy.max_hp = 10 ** 6
        return s


class KitTest(Sandbox):
    def test_the_spells_react_with_the_mark_of_the_staff(self):
        staff = CLS["weapon"]["element"]
        self.assertIsNotNone(reaction_key(staff, CLS["armor"]["element"]))
        for sid in CLS["spells"]:
            with self.subTest(spell=sid):
                self.assertIsNotNone(reaction_key(staff, magic.spell(sid)["element"]))

    def test_the_hero_starts_with_the_kit(self):
        with quiet(): p = Player("9", "base", [])
        self.assertEqual((p.role, p.spells, p.weapon.scaling, p.max_ether()), ("Elementalista", CLS["spells"], "arcano", p.base_ether + p.magic_value("ether_max")))


class DefenseTest(Sandbox):
    def test_the_prism_halves_and_gives_ether(self):
        self.assertIn(f"{PRISM['ether_gain']} Etere", PRISM["desc"])
        p = self.hero(); s = self.session(p)
        s.def_type, _ = p.get_defense_action()
        self.assertEqual(s.def_type, "prism")
        with quiet(): s.execute_player_defense()
        self.assertTrue(s.is_defending)
        self.assertEqual(p.ether, GAME_DATA["spells"]["rules"]["gain"]["defend"] + PRISM["ether_gain"])


class MasteryTest(Sandbox):
    def test_the_elemental_chain_gives_ether_on_every_reaction(self):
        self.assertIn(f"{ELEMENTAL_CHAIN_ETHER} Etere", CLS["mastery"]["2"]["desc"])
        key = next(iter(GAME_DATA["elements"]["reactions"]))
        gained = []
        for lvl in (1, 2):
            p = self.hero(lvl); s = self.session(p)
            with quiet(): s._trigger_reaction(key)
            gained.append(p.ether)
        self.assertEqual(gained[1] - gained[0], ELEMENTAL_CHAIN_ETHER)


class UnlockTest(Sandbox):
    def test_the_feat_unlocks_the_class(self):
        feat = GAME_DATA["meta"]["feats"]["feat_alchimia"]
        self.assertEqual((feat["reward_type"], feat["reward_id"]), ("class", "9"))
        PROFILE_MANAGER._data["completed_feats"] = []
        PROFILE_MANAGER._data["unlocked_ids"] = [u for u in PROFILE_MANAGER._data["unlocked_ids"] if u != "9"]
        with quiet(): p = Player("1", "base", [])
        p.run_tracker = {"escapes": 0, "fusions": 0, "reactions": feat["target"]}
        with quiet(): roguelike._check_feats(p, 5, False)
        self.assertIn("9", PROFILE_MANAGER.unlocked_ids)


if __name__ == "__main__":
    unittest.main()
