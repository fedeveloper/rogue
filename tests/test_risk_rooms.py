"""Stanze a rischio e ricompensa: trappole con bottino, forzieri chiusi o Mimic, scontri d'Élite, Audacia e Mistero.

Ogni stanza deve avere un prezzo e un premio visibili: nessuna è gratuita e nessuna è solo una punizione.
"""
import copy
import io
import random
import re
import statistics as st
import unittest
from contextlib import redirect_stdout
from unittest import mock

import floor_map
import roguelike
import rooms
from data_manager import GAME_DATA, PROFILE_MANAGER, RAW_DATA
from entities import Enemy, Player, pick_enemy_name, typical_enemy

ANSI = re.compile(r"\x1b\[[0-9;]*m")
RULES = GAME_DATA["meta"]["rooms"]


def quiet():
    return redirect_stdout(io.StringIO())


def plain(text):
    return ANSI.sub("", text)


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        self._save = mock.patch.object(PROFILE_MANAGER, "save")
        self._save.start()
        self._ui = [mock.patch(f"rooms.{f}") for f in ("wait_enter", "delay_print")] + [mock.patch("rooms.time.sleep")]
        for p in self._ui: p.start()
        random.seed(3)

    def tearDown(self):
        for p in self._ui: p.stop()
        self._save.stop()
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)

    def hero(self, hp=500):
        with quiet(): p = Player("1", "base", [])
        p.max_hp = p.hp = hp
        p.inventory = []
        return p

    def gear(self, p):
        return [i for i in p.inventory if i.type in ("weapon", "armor", "accessory")]


class TrapTest(Sandbox):
    def run_trap(self, p, choice, roll, floor=5):
        prompts = []
        def menu(options, prompt="", **kw):
            prompts.append((prompt, options)); return choice
        with quiet(), mock.patch("rooms.interactive_menu", side_effect=menu), \
             mock.patch("rooms.random.randint", side_effect=lambda lo, hi: roll if (lo, hi) == (1, 100) else 20):
            braved = rooms.trap_room(p, floor, [])
        return braved, prompts

    def test_turning_back_costs_nothing_and_gives_nothing(self):
        p = self.hero()
        braved, _ = self.run_trap(p, 2, roll=100)
        self.assertFalse(braved)
        self.assertEqual((p.hp, p.inventory), (500, []))

    def test_a_braved_trap_always_pays_and_a_failed_check_costs_hp(self):
        for choice in (0, 1):
            with self.subTest(way=choice):
                p = self.hero()
                braved, _ = self.run_trap(p, choice, roll=100)  # prova fallita
                self.assertTrue(braved)
                self.assertEqual(500 - p.hp, 20 + 5 * 3)
                self.assertEqual(len(self.gear(p)), 1)

    def test_a_passed_check_is_free_and_disarming_also_salvages_gold(self):
        base, per_floor = RULES["trap"]["salvage_gold"]
        for choice, gold in ((0, base + 5 * per_floor), (1, 0)):
            with self.subTest(way=choice):
                p = self.hero(); p.gold = 0
                braved, _ = self.run_trap(p, choice, roll=1)
                self.assertEqual(p.hp, 500)
                self.assertEqual(p.gold, p.calculate_gold_gain(gold) if gold else 0)
                self.assertEqual(len(self.gear(p)), 1)

    def test_the_menu_shows_the_real_chances_and_they_follow_the_stats(self):
        p = self.hero()
        _, prompts = self.run_trap(p, 2, roll=100)
        chances = rooms.trap_chances(p)
        options = " ".join(plain(o) for o in prompts[0][1])
        self.assertIn(f"Precisione: {chances['disarm']}%", options)
        self.assertIn(f"Schivata: {chances['dash']}%", options)
        self.assertIn(f"{15 + 5 * 3}-{30 + 5 * 3} danni", plain(prompts[0][0]))
        p.base_dodge += 10
        self.assertGreater(rooms.trap_chances(p)["dash"], chances["dash"])
        # Senza schivata resta la corsa di base; la precisione ha un tetto e un minimo
        p.base_dodge = -1000; p.base_acc = 1000
        self.assertEqual(rooms.trap_chances(p), {"disarm": RULES["trap"]["max_chance"], "dash": RULES["trap"]["dash"]["base"]})
        p.base_acc = -1000
        self.assertEqual(rooms.trap_chances(p)["disarm"], RULES["trap"]["min_chance"])


class TreasureTest(Sandbox):
    def open_chest(self, p, kind, choice=0, floor=10, sixth=False):
        risks = {"mimic": 100.0, "locked": 0.0} if kind == "mimic" else {"mimic": 0.0, "locked": 100.0} if kind == "locked" else {"mimic": 0.0, "locked": 0.0}
        fights, menus = [], []
        def fight(player, f, enemy):
            fights.append(enemy); enemy.hp = 0
        def menu(options, prompt="", **kw):
            menus.append(plain(prompt)); return choice
        with quiet(), mock.patch("rooms.chest_risks", return_value=risks), mock.patch("rooms.combat_room", side_effect=fight), \
             mock.patch("rooms.interactive_menu", side_effect=menu), mock.patch.object(PROFILE_MANAGER, "get_perk", side_effect=lambda k, d=None: sixth if k == "sesto_senso" else d):
            rooms.treasure_room(p, floor)
        return fights, menus

    def test_chests_get_riskier_with_depth(self):
        self.assertEqual(rooms.chest_risks(1), {"mimic": 0.0, "locked": 0.0})
        values = [sum(rooms.chest_risks(f).values()) for f in (1, 5, 10, 20, 30)]
        self.assertEqual(values, sorted(values))
        self.assertLess(values[0], values[-1])
        for k, v in rooms.chest_risks(100).items(): self.assertEqual(v, RULES["treasure"][k]["max"])

    def test_forcing_a_lock_costs_hp_and_guarantees_loot(self):
        p = self.hero(); p.gold = 0
        self.open_chest(p, "locked", choice=0)
        self.assertEqual(500 - p.hp, 500 * RULES["treasure"]["locked"]["hp_cost_pct"] // 100)
        self.assertGreater(p.gold, 0)
        self.assertEqual(len(p.inventory), 1)
        p = self.hero(); p.gold = 0
        self.open_chest(p, "locked", choice=1)
        self.assertEqual((p.hp, p.gold, p.inventory), (500, 0, []))

    def test_a_mimic_fights_and_pays_double(self):
        p = self.hero(); p.gold = 0
        with mock.patch("rooms.random.random", return_value=0.99):  # nessun indizio: il Mimic si apre a sorpresa
            fights, _ = self.open_chest(p, "mimic")
        self.assertEqual([e.base_name for e in fights], ["Mimic"])
        self.assertEqual(len(self.gear(p)), 1)
        self.assertGreater(p.gold, 0)

    def test_the_sixth_sense_unmasks_the_mimic_and_never_cries_wolf(self):
        p = self.hero()
        fights, menus = self.open_chest(p, "mimic", choice=1, sixth=True)
        self.assertEqual(fights, [])
        self.assertIn("Sesto Senso", menus[0])
        p = self.hero()
        with mock.patch("rooms.random.random", return_value=0.0):
            _, menus = self.open_chest(p, "open", sixth=True)
        self.assertEqual(menus, [])

    def test_the_mimic_lives_only_in_chests_and_matches_the_floor(self):
        self.assertTrue(all(pick_enemy_name(f, False) != "Mimic" for f in range(1, 31) for _ in range(30)))
        data = RAW_DATA["enemies"]["Mimic"]
        for f in (3, 15, 28):
            with self.subTest(floor=f):
                hp, atk = typical_enemy(f)
                mimics = [Enemy(f, False, [], name="Mimic") for _ in range(100)]
                self.assertAlmostEqual(st.mean(m.hp for m in mimics) / (hp * data["hp_mult"]), 1, delta=0.1)
                self.assertAlmostEqual(st.mean(m.atk for m in mimics) / (atk * data["atk_mult"]), 1, delta=0.15)


class EliteTest(Sandbox):
    def test_elites_appear_from_their_floor_and_are_tougher(self):
        weights = {"combat": 1, "elite": 100}
        first = {d["type"] for _ in range(50) for row in floor_map.generate_floor_map(1, weights, {}, {}, [])[:-1] for d in row}
        self.assertNotIn("elite", first)
        later = [d for _ in range(20) for row in floor_map.generate_floor_map(8, weights, {}, {}, [])[:-1] for d in row if d["type"] == "elite"]
        self.assertTrue(later)
        random.seed(1); normal = Enemy(8, False, [])
        random.seed(1); elite = Enemy(8, False, [], modifier="elite")
        rule = RULES["elite"]
        self.assertEqual(elite.hp, int(normal.hp * rule["hp_mult"]))
        self.assertEqual(elite.exp_drop, normal.exp_drop * rule["reward_mult"])

    def test_an_elite_always_leaves_a_relic_or_gear(self):
        for roll in (0.0, 0.999):
            with self.subTest(roll=roll):
                p = self.hero()
                with quiet(): session = rooms.CombatSession(p, 8, Enemy(8, False, [], modifier="elite"))
                with quiet(), mock.patch("rooms.random.random", return_value=roll):
                    session.on_enemy_death()
                self.assertEqual(len(p.relic_ids) + len(self.gear(p)), 1)

    def test_the_map_label_promises_the_reward(self):
        elite = {"type": "elite", "enemy": Enemy(8, False, [], modifier="elite")}
        combat = {"type": "combat", "enemy": Enemy(8, False, [])}
        self.assertIn(f"+{elite['enemy'].exp_drop} EXP", plain(floor_map.room_label(elite)))
        self.assertIn("reliquia", plain(floor_map.room_label(elite)))
        self.assertIn(f"+{combat['enemy'].exp_drop} EXP", plain(floor_map.room_label(combat)))
        self.assertIn("oggetto", plain(floor_map.room_label({"type": "trap"})))
        chest = next(d for _ in range(200) for row in floor_map.generate_floor_map(20, {"treasure": 1, "combat": 1}, {}, {}, [])[:-1] for d in row if d["type"] == "treasure")
        self.assertEqual(chest["risk"], round(sum(rooms.chest_risks(20).values())))
        self.assertIn(f"{chest['risk']}% chiuso o Mimic", plain(floor_map.room_label(chest)))
        self.assertNotIn("%", plain(floor_map.room_label({"type": "treasure", "risk": 0})))


class AudacityTest(Sandbox):
    def test_risky_rooms_build_audacity(self):
        p = self.hero()
        for rt in ("combat", "elite", "nemesis", "trap", "mystery", "treasure", "event"): rooms.gain_audacity(p, rt)
        self.assertEqual(p.audacity, sum(RULES["audacity"]["points"].values()))

    def test_the_boss_pays_for_the_risks_taken(self):
        rule = RULES["audacity"]
        for audacity, items in ((0, 0), (rule["item_at"] - 1, 0), (rule["item_at"], 1)):
            with self.subTest(audacity=audacity):
                p = self.hero(); p.gold, p.audacity = 0, audacity
                with quiet(): rooms.audacity_reward(p, 10, 200)
                self.assertEqual(p.gold, p.calculate_gold_gain(200 * audacity * rule["gold_pct_per_point"] // 100))
                self.assertEqual(len(self.gear(p)), items)
        self.assertTrue(rooms.audacity_bonus(rule["epic_at"])["epic"])
        self.assertIn("oggetto epico", rooms.audacity_text(rule["epic_at"]))

    def test_the_floor_loop_counts_audacity_and_resets_it(self):
        seen = []
        def menu(options, prompt="", **kw):
            seen.append(plain(prompt)); return 0
        rows = [[{"type": "combat", "enemy": None, "slot": 1, "links": [0]}], [{"type": "trap", "slot": 1, "links": [0]}],
                [{"type": "mystery", "slot": 1, "links": [0]}], [{"type": "treasure", "slot": 1, "links": [0]}],
                [{"type": "boss", "enemy": None, "slot": 1, "links": []}]]
        with quiet(), mock.patch("roguelike._hero_selection", return_value=("1", "base", [])), mock.patch("roguelike.interactive_menu", side_effect=menu), \
             mock.patch("roguelike.generate_floor_map", side_effect=lambda *a, **k: copy.deepcopy(rows)), mock.patch("roguelike.render_map", return_value=[]), \
             mock.patch("roguelike.room_label", return_value="stanza"), mock.patch("roguelike.combat_room"), mock.patch("roguelike.trap_room", return_value=True), \
             mock.patch("roguelike.mystery_room"), mock.patch("roguelike.treasure_room"), mock.patch("roguelike.evaluate_run"), mock.patch("roguelike.wait_enter"), \
             mock.patch("roguelike.clear_screen"), mock.patch("roguelike.delay_print"), mock.patch("roguelike.time.sleep"), mock.patch("roguelike._grant_victory_rewards"), \
             mock.patch("roguelike.choose_ending"), mock.patch("roguelike.start_of_run_boon"):
            roguelike.play_game()
        points = RULES["audacity"]["points"]
        audacity = [int(re.search(r"Audacia: (\d+)", s).group(1)) for s in seen if "Audacia:" in s]
        c, t, m = points["combat"], points["trap"], points["mystery"]
        # Prima di ogni scelta del primo piano: scontro, trappola affrontata e mistero contano, il forziere no
        self.assertEqual(audacity[:5], [0, c, c + t, c + t + m, c + t + m])
        self.assertEqual(audacity[5], 0, "ogni piano riparte da zero")


class MysteryTest(Sandbox):
    def test_the_odds_come_from_the_data_and_the_sixth_sense_reveals_them(self):
        odds = rooms.mystery_odds()
        self.assertEqual(set(odds), set(RULES["mystery"]["outcomes"]))
        self.assertAlmostEqual(sum(odds.values()), 100, delta=len(odds))
        label = plain(floor_map.room_label({"type": "mystery"}, sixth_sense=True))
        for k, v in odds.items(): self.assertIn(f"{rooms.MYSTERY_NAMES[k]} {v}%", label)
        self.assertNotIn("%", plain(floor_map.room_label({"type": "mystery"})))

    def test_a_relic_outcome_without_relics_left_becomes_a_hoard(self):
        p = self.hero(); p.gold = 0
        with quiet(), mock.patch("rooms.random.choices", return_value=["relic"]), mock.patch("rooms.get_random_relic", return_value=None):
            rooms.mystery_room(p, 5, [])
        self.assertGreater(p.gold, 0)
        self.assertEqual(len(self.gear(p)), 1)


if __name__ == "__main__":
    unittest.main()
