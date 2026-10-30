"""Le strutture del Campo a più livelli: Biblioteca dell'Arcano e Sala d'Armi. Costruzione un livello alla volta,
condizioni, effetti per ogni eroe, doni di inizio discesa, etichette, e le strutture di un solo livello di prima."""
import copy
import io
import random
import re
import unittest
from contextlib import redirect_stdout
from unittest import mock

import attributes
import camp
import camp_rules
from data_manager import PROFILE_MANAGER
from entities import Player

ANSI = re.compile(r"\x1b\[[0-9;]*m")
LIB, HALL = camp.structure("biblioteca_arcano"), camp.structure("sala_armi")


def quiet():
    return redirect_stdout(io.StringIO())


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        self._save = mock.patch.object(PROFILE_MANAGER, "save")
        self._save.start()
        PROFILE_MANAGER._data["story"] = {"flags": {}, "counters": {}, "seen_events": {}}
        PROFILE_MANAGER._data["npc_unlocked"] = {}
        random.seed(2)

    def tearDown(self):
        self._save.stop()
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)

    def hero(self):
        with quiet(): return Player("3", "base", [])

    def build_to(self, s, n):
        PROFILE_MANAGER.unlock_npc(s["requires"]["npc"])
        while camp_rules.level(s["id"]) < n:
            PROFILE_MANAGER._data["essence"] = camp.next_level(s)["cost"]
            self.assertTrue(camp.build(s))


class BuildTest(Sandbox):
    def test_one_level_at_a_time_and_only_after_the_rescue(self):
        self.assertFalse(camp.can_build(LIB), "serve Valerius")
        PROFILE_MANAGER.unlock_npc("valerius")
        costs = [lv["cost"] for lv in camp_rules.levels(LIB)]
        for n, cost in enumerate(costs, 1):
            PROFILE_MANAGER._data["essence"] = cost - 1
            self.assertFalse(camp.build(LIB))
            PROFILE_MANAGER._data["essence"] = cost
            self.assertTrue(camp.build(LIB))
            self.assertEqual((camp_rules.level(LIB["id"]), PROFILE_MANAGER.essence), (n, 0))
        PROFILE_MANAGER._data["essence"] = 10 ** 6
        self.assertFalse(camp.build(LIB), "oltre l'ultimo livello non si va")
        self.assertTrue(camp.complete(LIB))

    def test_single_level_structures_still_read_as_built(self):
        PROFILE_MANAGER.set_flag("camp_altare_purificazione")
        self.assertEqual(camp_rules.level("altare_purificazione"), 1)
        self.assertTrue(camp.complete(camp.structure("altare_purificazione")))

    def test_labels_show_the_level_and_the_next_step(self):
        PROFILE_MANAGER.unlock_npc("valerius")
        self.assertIn("Costruisci: La Biblioteca dell'Arcano Lv.1", ANSI.sub("", camp._structure_label(LIB)))
        self.build_to(LIB, 1)
        label = ANSI.sub("", camp._structure_label(LIB))
        self.assertIn("Lv.1/3 → Lv.2", label)
        self.assertIn(camp_rules.levels(LIB)[1]["desc"], label)
        self.build_to(LIB, 3)
        self.assertIn("[COSTRUITO]", camp._structure_label(LIB))


class EffectTest(Sandbox):
    def test_the_library_gives_ether_and_spell_power(self):
        base = self.hero()
        self.build_to(LIB, 1)
        self.assertEqual(self.hero().max_ether(), base.max_ether() + camp_rules.levels(LIB)[0]["effects"]["ether_max"])
        self.build_to(LIB, 3)
        self.assertEqual(self.hero().magic_value("spell_pct") - base.magic_value("spell_pct"), camp_rules.levels(LIB)[2]["effects"]["spell_pct"])

    def test_the_hall_gives_damage_to_every_weapon(self):
        base = self.hero()
        self.build_to(HALL, 2)
        self.assertEqual(attributes.value(self.hero(), "dmg_pct") - attributes.value(base, "dmg_pct"), camp_rules.levels(HALL)[1]["effects"]["dmg_pct"])


class StartGiftTest(Sandbox):
    def start(self, p, pick=0):
        with quiet(), mock.patch("camp.interactive_menu", return_value=pick):
            camp.start_of_run_boon(p)

    def test_nothing_before_building(self):
        p = self.hero(); items = len(p.inventory)
        self.start(p)
        self.assertEqual((len(p.inventory), p.unspent_points, p.talents), (items, 0, []))

    def test_a_scroll_and_the_points_of_every_level(self):
        self.build_to(LIB, 2); self.build_to(HALL, 1)
        p = self.hero(); items = len(p.inventory)
        self.start(p)
        self.assertEqual(sum(i.type == "scroll" for i in p.inventory), 1)
        self.assertEqual(len(p.inventory), items + 1)
        self.assertEqual((p.unspent_points, p.points_offered), (1, False))
        self.build_to(HALL, 3)
        p = self.hero(); self.start(p)
        self.assertEqual(p.unspent_points, sum(lv.get("start", {}).get("points", 0) for lv in camp_rules.levels(HALL)))


if __name__ == "__main__":
    unittest.main()
