"""I biomi oltre i Chiostri e l'equipaggiamento iniziale: pericoli (contratti e meccaniche), nativi, Caduta Astrale."""
import copy
import io
import random
import re
import unittest
from contextlib import redirect_stdout
from unittest import mock

import floor_map
import roguelike
from data_manager import GAME_DATA, PROFILE_MANAGER, RAW_DATA, get_biome
from entities import Armor, Enemy, Player, Weapon
from rooms import CombatSession, reaction_key

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def quiet():
    return redirect_stdout(io.StringIO())


def biome(bid):
    return next(b for b in GAME_DATA["biomes"] if b["id"] == bid)


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        self._save = mock.patch.object(PROFILE_MANAGER, "save")
        self._save.start()
        random.seed(4)

    def tearDown(self):
        self._save.stop()
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)

    def hero(self, cls="1"):
        with quiet():
            p = Player(cls, "base", [])
        p.max_hp = p.hp = 500
        return p

    def session(self, floor, p=None, silence_roll=0.99):
        p = p or self.hero()
        with quiet(), mock.patch("rooms.random.random", return_value=silence_roll):
            s = CombatSession(p, floor, Enemy(floor, False, []))
        s.enemy.hp = s.enemy.max_hp = 5000
        s.enemy.atk, s.enemy.element, s.enemy.base_acc = 40, "Normale", 100
        p.armor = Armor("Nessuna", 0, 0, "Normale", 1)
        return p, s


class StartingGearTest(Sandbox):
    def test_classes_start_with_a_reaction_or_a_resonance(self):
        reactions = {"1", "2", "3", "6", "7"}
        resonance = {"4", "8"}
        for cid, c in GAME_DATA["classes"].items():
            w, a = c["weapon"]["element"], c["armor"]["element"]
            with self.subTest(cls=c["role"]):
                if cid in reactions: self.assertIsNotNone(reaction_key(w, a), f"{w} + {a}")
                elif cid in resonance: self.assertEqual(w, a)
                else: self.assertEqual(a, "Normale")  # il Berserker combatte a petto nudo
        self.assertEqual(reactions | resonance | {"5"}, set(GAME_DATA["classes"]))

    def test_the_hero_really_wears_it(self):
        p = self.hero("2")
        self.assertEqual((p.weapon.element, p.armor.element), ("Vento", "Acqua"))


class BiomeDataTest(Sandbox):
    PATTERNS = {"silence": ("chance",), "dissolve": ("max_hp_pct",), "boil": ("chance", "gold_pct"), "paradox": ("player_repeat", "enemy_double")}

    def test_every_biome_is_complete(self):
        for b in GAME_DATA["biomes"]:
            with self.subTest(biome=b["id"]):
                self.assertTrue(b["hazard"]["name"] and b["hazard"]["desc"])
                self.assertGreaterEqual(len(b["signature_events"]), 2)
                self.assertTrue(b.get("room_weights") and b.get("enemy_elements"))
                natives = [n for cat in ("enemies", "bosses") for n, d in RAW_DATA[cat].items() if d.get("biome") == b["id"]]
                self.assertGreaterEqual(len(natives), 2)
                self.assertGreaterEqual(len(b["intro"]), 2)

    def test_hazard_descriptions_match_the_rules(self):
        for b in GAME_DATA["biomes"]:
            for rule, params in b.get("rules", {}).items():
                with self.subTest(biome=b["id"], rule=rule):
                    self.assertEqual(set(params), set(self.PATTERNS[rule]))
                    for key in self.PATTERNS[rule]: self.assertIn(f"{params[key]}%", b["hazard"]["desc"])
        fall = [eff["gold_pct"] for ev in biome("guglie")["signature_events"] for sc in GAME_DATA["events"][ev]["scenes"].values()
                for c in sc["choices"] for effs in (c.get("effects", []), c.get("fail_effects", [])) for eff in effs if "fall" in eff]
        self.assertTrue(fall)
        for pct in fall: self.assertIn(f"{pct}% dell'Oro", biome("guglie")["hazard"]["desc"])

    def test_a_fall_is_always_the_last_effect(self):
        for ev_id, ev in GAME_DATA["events"].items():
            for sc in ev["scenes"].values():
                for c in sc["choices"]:
                    for effs in (c.get("effects", []), c.get("success", []), c.get("fail_effects", [])):
                        if any("fall" in e for e in effs):
                            self.assertIn("fall", effs[-1], ev_id)
                            self.assertNotIn("next", c)


class HazardMechanicsTest(Sandbox):
    def test_gas_of_silence_removes_the_class_technique(self):
        for cls, check in (("1", "counter"), ("2", "focus"), ("3", "recovery")):
            with self.subTest(cls=cls):
                p, s = self.session(8, self.hero(cls), silence_roll=0.0)
                self.assertTrue(s.silenced)
                prompts = []
                with quiet(), mock.patch("rooms.interactive_menu", side_effect=lambda o, pr="": prompts.append(o) or 1), mock.patch("rooms.clear_screen"):
                    s.player_turn()
                self.assertTrue(prompts[0][1].startswith("Difesa (Dimezza danni; il gas soffoca la tecnica)"))
                self.assertTrue(s.is_defending)
                self.assertFalse(s.focused_attack)
                p.hp = 400
                with quiet(), mock.patch("rooms.random.randint", side_effect=lambda a, b: a), mock.patch("rooms.random.random", return_value=0.99):
                    s.enemy_turn()
                self.assertEqual(s.enemy.hp, 5000, "niente contrattacco")
                self.assertLess(p.hp, 400, "niente riparo magico, il colpo arriva dimezzato")

    def test_gas_only_in_the_mines(self):
        self.assertFalse(self.session(3, silence_roll=0.0)[1].silenced)
        self.assertFalse(self.session(8, silence_roll=0.99)[1].silenced)

    def test_astral_boiling_burns_gold_on_hits(self):
        rule = biome("forgia")["rules"]["boil"]
        for floor, roll, lost in ((22, 0.0, True), (22, 0.99, False), (8, 0.0, False)):
            with self.subTest(floor=floor, roll=roll):
                p, s = self.session(floor)
                p.gold = 1000
                with quiet(), mock.patch("rooms.random.randint", side_effect=lambda a, b: a), mock.patch("rooms.random.random", return_value=roll):
                    s.enemy_turn()
                self.assertEqual(p.gold, 1000 - (1000 * rule["gold_pct"] // 100 if lost else 0))

    def test_temporal_paradox(self):
        for key, expected in (("player_repeat", (2, 1)), ("enemy_double", (1, 2)), (None, (1, 1))):
            with self.subTest(rule=key):
                p, s = self.session(28)
                calls = {"player": 0, "enemy": 0}

                def player_turn():
                    calls["player"] += 1
                    return True

                def enemy_turn():
                    calls["enemy"] += 1
                    s.enemy.hp = 0 if calls["enemy"] >= expected[1] else s.enemy.hp
                    return True

                rolls = lambda k: k == key
                with quiet(), mock.patch.object(s, "player_turn", side_effect=player_turn), mock.patch.object(s, "enemy_turn", side_effect=enemy_turn), \
                     mock.patch.object(s, "_paradox", side_effect=rolls), mock.patch.object(s, "process_statuses_and_curses"):
                    s._combat_loop()
                self.assertEqual((calls["player"], calls["enemy"]), expected)
        p, s = self.session(3)
        self.assertFalse(s._paradox("enemy_double"))

    def test_dissolution_of_the_self(self):
        p = self.hero()
        start = p.max_hp
        pct = biome("ventre")["rules"]["dissolve"]["max_hp_pct"]
        expected = start
        with quiet():
            for floor in range(15, 22):
                floor_map.apply_biome_on_floor(p, get_biome(floor))
                if 16 <= floor <= 20:
                    expected -= max(1, expected * pct // 100)
                    self.assertEqual(p.max_hp, expected)
        self.assertEqual(p.max_hp, start, "uscendo dal Ventre si ritrova tutto")
        self.assertEqual(p.dissolved, 0)

    def test_astral_fall_skips_to_the_next_floor(self):
        bosses, rests, floors = [], [], []

        def fall_on_11(p, f):
            if f == 11: p.fallen = True  # qualunque stanza del piano 11 fa da ponte sospeso

        def combat(p, f, e):
            if e.is_boss: bosses.append(f)
            else: fall_on_11(p, f)

        def menu(options, prompt="", **kw):
            floors.append(int(re.search(r"Piano (\d+)", ANSI.sub("", prompt)).group(1)))
            return 0

        rooms = {"vendor_room": lambda p, f: fall_on_11(p, f), "treasure_room": lambda p, f: fall_on_11(p, f),
                 "campfire_room": lambda p, f: fall_on_11(p, f), "trap_room": lambda p, f, a: fall_on_11(p, f),
                 "mystery_room": lambda p, f, a: fall_on_11(p, f), "event_room": lambda p, e, f: fall_on_11(p, f)}
        rooms = {k: mock.MagicMock(side_effect=v) for k, v in rooms.items()}
        out = io.StringIO()
        with redirect_stdout(out), mock.patch("roguelike._hero_selection", return_value=("1", "base", [])), mock.patch("roguelike.interactive_menu", side_effect=menu), \
             mock.patch("roguelike.combat_room", side_effect=combat), mock.patch.multiple("roguelike", **rooms), \
             mock.patch("roguelike.evaluate_run"), mock.patch("roguelike.wait_enter"), \
             mock.patch("roguelike.clear_screen"), mock.patch("roguelike.delay_print", side_effect=lambda t, d=0: print(t)), \
             mock.patch("roguelike.time.sleep"), mock.patch("roguelike._grant_victory_rewards"), mock.patch("roguelike.choose_ending"), mock.patch("roguelike.start_of_run_boon"):
            roguelike.play_game()
        self.assertNotIn(11, bosses, "chi precipita salta il boss")
        self.assertIn(10, bosses)
        self.assertIn(12, bosses)
        self.assertIn("PRECIPITI AL PIANO 12", ANSI.sub("", out.getvalue()))
        self.assertNotIn("PIANO 11 SUPERATO", ANSI.sub("", out.getvalue()))
        self.assertEqual(floors.count(11), 1, "il piano finisce alla prima stanza da cui si cade")


if __name__ == "__main__":
    unittest.main()
