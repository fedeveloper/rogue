"""Identità dei nemici: profili di mosse, boss nativi di ogni bioma, la tecnica di difesa di ogni classe."""
import copy
import io
import random
import re
import unittest
from contextlib import redirect_stdout
from unittest import mock

import codex
from data_manager import GAME_DATA, PROFILE_MANAGER, RAW_DATA
from entities import Armor, Enemy, Player, Weapon, pick_enemy_name
from rooms import CombatSession

ANSI = re.compile(r"\x1b\[[0-9;]*m")
MOVES = GAME_DATA["moves"]
PROFILES = MOVES["profiles"]
DEFENSES = GAME_DATA["defenses"]


def quiet():
    return redirect_stdout(io.StringIO())


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        self._save = mock.patch.object(PROFILE_MANAGER, "save")
        self._save.start()
        random.seed(5)

    def tearDown(self):
        self._save.stop()
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)

    def fight(self, cls="1", weapon="Fuoco", armor="Terra"):
        with quiet():
            p = Player(cls, "base", [])
        p.max_hp, p.hp = 1000, 500
        p.weapon = Weapon("Lama", 10, 30, weapon, 1)
        p.armor = Armor("Corazza", 10, 0, armor, 1)
        with quiet():
            s = CombatSession(p, 5, Enemy(5, False, [], name="Goblin"))
        s.enemy.hp = s.enemy.max_hp = 1000
        s.enemy.element, s.enemy.base_dodge, s.enemy.base_acc = "Normale", 0, 100
        s.def_type, s.def_txt = p.get_defense_action()
        return p, s


class MoveProfileTest(Sandbox):
    def test_profiles_are_valid(self):
        for pid, prof in PROFILES.items():
            with self.subTest(profile=pid):
                self.assertTrue(prof["name"] and prof["desc"])
                self.assertIn("attack", prof["moves"])
                self.assertLessEqual(set(prof["moves"]), set(MOVES["moves"]) - {"unleash"}, "il Colpo caricato arriva solo dopo la Carica")

    def test_every_profile_points_somewhere_and_venom_needs_a_status(self):
        used = set()
        for cat in ("enemies", "bosses"):
            for name, d in RAW_DATA[cat].items():
                if "profile" not in d: continue
                with self.subTest(enemy=name):
                    self.assertIn(d["profile"], PROFILES)
                    self.assertNotIn("moves", d, "o un profilo o mosse proprie")
                    if "venom" in PROFILES[d["profile"]]["moves"]: self.assertTrue(d.get("status_inflict"))
                    used.add(d["profile"])
        self.assertEqual(used, set(PROFILES), "ogni profilo ha almeno un nemico")

    def test_only_the_first_enemies_keep_the_plain_style(self):
        plain = [n for n, d in RAW_DATA["enemies"].items() if "moves" not in d and "profile" not in d]
        self.assertLessEqual(len(plain), 3, plain)
        for n in plain: self.assertLessEqual(RAW_DATA["enemies"][n]["base_hp"] * RAW_DATA["enemies"][n]["base_atk"], 100, n)

    def test_the_enemy_fights_with_its_profile(self):
        for name in ("Orco", "Melma Acida", "Chierico Corrotto"):
            with self.subTest(enemy=name):
                e = Enemy(5, False, [], name=name)
                self.assertEqual(e.moves, PROFILES[RAW_DATA["enemies"][name]["profile"]]["moves"])

    def test_the_bestiary_tells_the_style_once_defeated(self):
        PROFILE_MANAGER._data["codex"]["enemies"] = {"Orco": {"seen": 1, "killed": 0}}
        page = "\n".join(ANSI.sub("", l) for l in codex.bestiary_page())
        self.assertNotIn("Stile:", page)
        PROFILE_MANAGER._data["codex"]["enemies"]["Orco"]["killed"] = 1
        page = "\n".join(ANSI.sub("", l) for l in codex.bestiary_page())
        self.assertIn(f"Stile: {PROFILES['bruto']['name']}. {PROFILES['bruto']['desc']}", page)


class BiomeBossTest(Sandbox):
    def test_every_biome_has_its_own_boss(self):
        for b in GAME_DATA["biomes"]:
            with self.subTest(biome=b["id"]):
                bosses = [n for n, d in RAW_DATA["bosses"].items() if d.get("biome") == b["id"]]
                self.assertEqual(len(bosses), 1, bosses)
                d = RAW_DATA["bosses"][bosses[0]]
                self.assertTrue(d["title"] and d["lore"] and d.get("moves"))
                self.assertIn(bosses[0], GAME_DATA["phases"])

    def test_the_boss_waits_only_in_its_biome(self):
        for b in GAME_DATA["biomes"]:
            boss = next(n for n, d in RAW_DATA["bosses"].items() if d.get("biome") == b["id"])
            lo, hi = b["floors"]
            last = min(hi, 29)  # il piano 30 è del DIO ANTICO
            with self.subTest(biome=b["id"]):
                inside = {pick_enemy_name(f, True) for f in range(lo, last + 1) for _ in range(80)}
                outside = {pick_enemy_name(f, True) for f in range(1, 31) if not lo <= f <= hi for _ in range(5)}
                self.assertIn(boss, inside)
                self.assertNotIn(boss, outside)


class DefenseTest(Sandbox):
    def test_every_class_has_a_described_defense(self):
        for cid, c in GAME_DATA["classes"].items():
            with self.subTest(cls=c["role"]):
                self.assertIn(c["defense"], DEFENSES)
        self.assertEqual({c["defense"] for c in GAME_DATA["classes"].values()}, set(DEFENSES), "ogni tecnica ha una classe")
        for did, d in DEFENSES.items():
            with self.subTest(defense=did):
                self.assertTrue(d["name"] and d["short"] and d["desc"])
                for key in ("heal_pct", "drain_pct"):
                    if key in d:
                        self.assertIn(f"{d[key]}%", d["desc"])
                        self.assertIn(f"{d[key]}%", d["short"])

    def test_the_menu_shows_name_and_short_text(self):
        p, s = self.fight("4")
        d = DEFENSES["cleanse"]
        self.assertEqual(s.def_txt, f"{d['name']} ({d['short']})")

    def test_recovery_heals(self):
        p, s = self.fight("3")
        with quiet(): self.assertTrue(s.execute_player_defense())
        self.assertEqual(p.hp, 500 + 1000 * DEFENSES["recovery"]["heal_pct"] // 100)

    def test_the_vow_purifies_and_heals(self):
        p, s = self.fight("4")
        p.statuses.update(poison=3, bleed=2)
        with quiet(): s.execute_player_defense()
        self.assertEqual(p.statuses, {})
        self.assertEqual(p.hp, 500 + 1000 * DEFENSES["cleanse"]["heal_pct"] // 100)
        self.assertTrue(s.is_defending)

    def test_the_mixture_marks_and_the_armor_completes_the_reaction(self):
        p, s = self.fight("6", weapon="Fuoco", armor="Terra")
        with quiet(): s.execute_player_defense()
        self.assertEqual(s.enemy.mark[0], "Fuoco")
        s.intent = "attack"
        with quiet(), mock.patch("rooms.random.randint", side_effect=lambda a, b: a), mock.patch("rooms.wait_enter"):
            s.enemy_turn()
        self.assertEqual(p.run_tracker.get("reactions"), 1)

    def test_the_shroud_steals_life(self):
        p, s = self.fight("8")
        with quiet(): self.assertTrue(s.execute_player_defense())
        stolen = 1000 * DEFENSES["siphon"]["drain_pct"] // 100
        self.assertEqual((s.enemy.hp, p.hp), (1000 - stolen, 500 + stolen))

    def test_the_shroud_can_finish_the_enemy(self):
        p, s = self.fight("8")
        s.enemy.hp = 1
        with quiet(), mock.patch("rooms.wait_enter"): self.assertFalse(s.execute_player_defense())
        self.assertLessEqual(s.enemy.hp, 0)

    def test_the_curse_blocks_the_healing_but_not_the_theft(self):
        p, s = self.fight("8")
        p.cursed = True
        with quiet(): s.execute_player_defense()
        self.assertEqual((s.enemy.hp, p.hp), (1000 - 1000 * DEFENSES["siphon"]["drain_pct"] // 100, 500))


if __name__ == "__main__":
    unittest.main()
