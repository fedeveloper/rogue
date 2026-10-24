"""Il Ciclo del Labirinto: oltre il piano 30 i biomi tornano in Eco sempre più dure, con il DIO ANTICO a ogni fine ciclo."""
import copy
import io
import random
import re
import unittest
from contextlib import redirect_stdout
from unittest import mock

import codex
import epitaph
import floor_map
import roguelike
from constants import INFINITE_MODE_ESSENCE_MULTIPLIER, INFINITE_MODE_THRESHOLD as LENGTH
from data_manager import GAME_DATA, PROFILE_MANAGER, RAW_DATA, cycle_of, echo_name, get_biome, hazard_mult, set_cycle_seed
from entities import Enemy, Player, echo_native_base, generic_base, pick_enemy_name

ANSI = re.compile(r"\x1b\[[0-9;]*m")
RULE = GAME_DATA["meta"]["cycle"]
BIOMES = {b["id"]: b for b in GAME_DATA["biomes"]}
LAST = max(GAME_DATA["biomes"], key=lambda b: b["floors"][0])["id"]


def quiet():
    return redirect_stdout(io.StringIO())


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        self._save = mock.patch.object(PROFILE_MANAGER, "save")
        self._save.start()
        set_cycle_seed(11)
        random.seed(3)

    def tearDown(self):
        self._save.stop()
        set_cycle_seed(0)
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)

    def hero(self):
        with quiet(): p = Player("1", "base", [])
        return p


class CycleShapeTest(Sandbox):
    def test_cycles_and_their_echoes(self):
        self.assertEqual([cycle_of(f) for f in (1, 30, 31, 60, 61, 91)], [0, 0, 1, 1, 2, 3])
        self.assertEqual([echo_name(c) for c in (0, 1, 2, 3, 8, 9)], ["", "Eco II", "Eco III", "Eco IV", "Eco IX", "Eco X"])

    def test_the_first_descent_is_untouched(self):
        for f in range(1, LENGTH + 1):
            self.assertIs(get_biome(f), next(b for b in GAME_DATA["biomes"] if b["floors"][0] <= f <= b["floors"][1]))

    def test_every_cycle_crosses_every_biome_once_and_ends_on_the_threshold(self):
        for cycle in range(1, 6):
            floors = range(cycle * LENGTH + 1, (cycle + 1) * LENGTH + 1)
            with self.subTest(cycle=cycle):
                ids = [get_biome(f)["id"] for f in floors]
                runs = [ids[i] for i in range(len(ids)) if i == 0 or ids[i] != ids[i - 1]]
                self.assertEqual(sorted(runs), sorted(BIOMES), "ogni bioma una volta, in un blocco solo")
                self.assertEqual(runs[-1], LAST)
                for f in floors:
                    b = get_biome(f)
                    self.assertTrue(b["floors"][0] <= f <= b["floors"][1])
                    self.assertEqual(b["floors"][1] - b["floors"][0], BIOMES[b["id"]]["floors"][1] - BIOMES[b["id"]]["floors"][0])
                    self.assertEqual((b["cycle"], b["echo"]), (cycle, echo_name(cycle)))
                    self.assertEqual(b["name"], BIOMES[b["id"]]["name"])

    def test_the_order_comes_from_the_seed_of_the_descent(self):
        order = lambda: [get_biome(LENGTH + 1 + 5 * k)["id"] for k in range(6)]
        set_cycle_seed(11); first = order()
        set_cycle_seed(11); self.assertEqual(order(), first, "stesso seme, stesso ordine")
        orders = set()
        for seed in range(30):
            set_cycle_seed(seed); orders.add(tuple(order()))
        self.assertGreater(len(orders), 5, "semi diversi, ordini diversi")

    def test_the_data_is_not_changed(self):
        before = copy.deepcopy(GAME_DATA["biomes"])
        for f in range(LENGTH + 1, 4 * LENGTH + 1): get_biome(f)
        self.assertEqual(GAME_DATA["biomes"], before)


class HazardTest(Sandbox):
    def test_hazards_grow_with_each_echo_up_to_the_cap(self):
        self.assertEqual(hazard_mult(1), 1 + RULE["hazard_pct_per_cycle"] / 100)
        self.assertEqual(hazard_mult(100), RULE["hazard_max_mult"])
        for cycle in (1, 2, 5, 12):
            for f in range(cycle * LENGTH + 1, (cycle + 1) * LENGTH + 1, 5):
                b = get_biome(f)
                with self.subTest(cycle=cycle, biome=b["id"]):
                    for rule, params in b.get("rules", {}).items():
                        for key, value in params.items():
                            old = BIOMES[b["id"]]["rules"][rule][key]
                            self.assertEqual(value, min(RULE["chance_cap"], round(old * hazard_mult(cycle))))

    def test_the_description_tells_the_new_numbers(self):
        for cycle in (1, 3):
            for f in range(cycle * LENGTH + 1, (cycle + 1) * LENGTH + 1, 5):
                b = get_biome(f)
                with self.subTest(cycle=cycle, biome=b["id"]):
                    shown = {int(n) for n in re.findall(r"(?<![\d,])(\d+)%", b["hazard"]["desc"])}
                    for params in b.get("rules", {}).values():
                        for value in params.values(): self.assertIn(value, shown)
                    if not b.get("rules"): self.assertEqual(b["hazard"]["desc"], BIOMES[b["id"]]["hazard"]["desc"])

    def test_the_fight_uses_the_harder_rule(self):
        from rooms import CombatSession
        floor = next(f for f in range(LENGTH + 1, 2 * LENGTH + 1) if get_biome(f)["id"] == "miniere")
        p = self.hero()
        with quiet(), mock.patch("rooms.random.random", return_value=0.0): s = CombatSession(p, floor, Enemy(floor, False, []))
        self.assertEqual(s.rules["silence"]["chance"], round(BIOMES["miniere"]["rules"]["silence"]["chance"] * hazard_mult(1)))


class EnemiesTest(Sandbox):
    def test_natives_come_back_as_strong_as_the_deepest_enemies(self):
        floor = next(f for f in range(LENGTH + 1, 2 * LENGTH + 1) if get_biome(f)["id"] == "chiostri")
        natives = {n for n, d in RAW_DATA["enemies"].items() if d.get("biome") == "chiostri"}
        self.assertTrue(natives & {pick_enemy_name(floor, False) for _ in range(300)}, "i nativi tornano con il loro bioma")
        # rispetto ai generici più profondi ogni nativo è forte quanto lo era rispetto ai generici del suo bioma
        deep_hp, deep_atk = generic_base(LENGTH)
        for name, d in RAW_DATA["enemies"].items():
            if not d.get("biome"): continue
            lo, hi = BIOMES[d["biome"]]["floors"]
            home_hp = (generic_base(lo)[0] + generic_base(hi)[0]) / 2
            home_atk = (generic_base(lo)[1] + generic_base(hi)[1]) / 2
            hp, atk = echo_native_base(d)
            with self.subTest(enemy=name):
                self.assertAlmostEqual(hp / deep_hp, d["base_hp"] / home_hp, delta=0.05)
                self.assertAlmostEqual(atk / deep_atk, d["base_atk"] / home_atk, delta=0.1)
        random.seed(1); echo = Enemy(floor, False, [], name="Eco del Rimpianto")
        random.seed(1); same_floor_generic = Enemy(floor, False, [], name="Goblin")
        self.assertGreater(echo.max_hp, same_floor_generic.max_hp, "nell'Eco non è più il nemico più debole dei Chiostri")

    def test_the_old_god_waits_at_the_end_of_every_cycle(self):
        for floor, final in ((LENGTH, True), (2 * LENGTH, True), (3 * LENGTH, True), (LENGTH + 15, False)):
            with self.subTest(floor=floor):
                boss = Enemy(floor, True, [], final=floor % LENGTH == 0)
                self.assertEqual(bool(RAW_DATA["bosses"][boss.base_name].get("final_boss")), final)
                self.assertEqual("(Eco" in ANSI.sub("", boss.name), final and floor > LENGTH)

    def test_the_map_puts_the_old_god_at_the_bottom_of_each_cycle(self):
        w = GAME_DATA["meta"]["rooms"]["weights"]
        for floor in (LENGTH, 2 * LENGTH):
            with quiet():
                rows = floor_map.generate_floor_map(floor, w, {}, {k: 0 for k in w}, [], self.hero())
            boss = rows[-1][0]["enemy"]
            self.assertTrue(RAW_DATA["bosses"][boss.base_name].get("final_boss"), floor)


class RecordTest(Sandbox):
    def test_entering_a_cycle_announces_it_and_keeps_the_record(self):
        PROFILE_MANAGER._data["best_echo"] = 0
        p = self.hero()
        with quiet(), mock.patch("roguelike.delay_print"):
            self.assertFalse(roguelike.enter_cycle(p, LENGTH))
            self.assertFalse(roguelike.enter_cycle(p, LENGTH + 2))
            self.assertTrue(roguelike.enter_cycle(p, LENGTH + 1))
        self.assertEqual(PROFILE_MANAGER._data["best_echo"], 2)
        self.assertEqual(p.chronicle[-1], {"kind": "echo", "echo": "Eco II"})
        with quiet(), mock.patch("roguelike.delay_print"): roguelike.enter_cycle(p, 2 * LENGTH + 1)
        self.assertEqual(PROFILE_MANAGER._data["best_echo"], 3)
        PROFILE_MANAGER._data["best_echo"] = 5
        with quiet(), mock.patch("roguelike.delay_print"): roguelike.enter_cycle(p, LENGTH + 1)
        self.assertEqual(PROFILE_MANAGER._data["best_echo"], 5, "il record non scende")

    def test_the_epitaph_remembers_the_deepest_echo(self):
        p = self.hero(); p.hp = 0
        epitaph.note(p, "echo", echo="Eco II"); epitaph.note(p, "echo", echo="Eco III")
        lines = epitaph.compose(p, 70)
        self.assertIn(GAME_DATA["epitaph"]["middle"]["echo"].format(echo="Eco III"), lines)

    def test_essence_grows_with_each_echo(self):
        self.assertEqual(roguelike.cycle_essence_mult(LENGTH + 1), INFINITE_MODE_ESSENCE_MULTIPLIER)
        self.assertEqual(roguelike.cycle_essence_mult(2 * LENGTH + 1), INFINITE_MODE_ESSENCE_MULTIPLIER * (1 + RULE["essence_pct_per_cycle"] / 100))

    def test_the_codex_shows_the_record(self):
        prompts = []
        PROFILE_MANAGER._data["best_echo"] = 3
        with quiet(), mock.patch("codex.clear_screen"), mock.patch("codex.interactive_menu", side_effect=lambda o, pr="", **k: prompts.append(pr) or -1):
            codex.show_codex()
        self.assertIn("Eco III", ANSI.sub("", prompts[0]))

    def test_the_rules_text_tells_the_real_numbers(self):
        d = RULE["desc"]
        self.assertIn(f"{RULE['hazard_pct_per_cycle']}%", d)
        self.assertIn(f"{RULE['chance_cap']}%", d)
        self.assertEqual(RULE["hazard_max_mult"], 2.0); self.assertIn("doppio", d)
        self.assertIn(f"×{INFINITE_MODE_ESSENCE_MULTIPLIER:g}".replace(".", ","), d)
        self.assertIn(f"{RULE['essence_pct_per_cycle']}%", d)
        self.assertIn("{echo}", RULE["intro"])


if __name__ == "__main__":
    unittest.main()
