"""Modalità: i gradi di Ascensione e la Sfida del Giorno.

Ogni effetto dei dati ha il suo contratto (fa ciò che dice la descrizione) e una regola di testo che la descrizione
deve contenere, così un grado o un dono nuovo non può promettere un numero diverso da quello che applica.
"""
import copy
import datetime
import io
import random
import re
import unittest
from contextlib import redirect_stdout
from unittest import mock

import modes
import roguelike
import rooms
from constants import CAMPFIRE_REST_PCT, CURSE_CHANCE
from data_manager import GAME_DATA, PROFILE_MANAGER
from entities import Enemy, Player, generate_weapon
from rooms_patch import patch_rooms

ANSI = re.compile(r"\x1b\[[0-9;]*m")
GRADES = GAME_DATA["modes"]["ascension"]["grades"]
BOONS = GAME_DATA["modes"]["daily"]["boons"]
GRADE, BOON = {g["id"]: g for g in GRADES}, {b["id"]: b for b in BOONS}


def quiet():
    return redirect_stdout(io.StringIO())


def plain(text):
    return ANSI.sub("", text)


def all_effects():
    """(nome, descrizione, effetti) di ogni grado e di ogni dono."""
    return [(g["name"], g["desc"], g["effects"]) for g in GRADES] + [(b["name"], b["desc"], b["effects"]) for b in BOONS]


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        self._save = mock.patch.object(PROFILE_MANAGER, "save")
        self._save.start()
        random.seed(5)

    def tearDown(self):
        modes.end_run()
        self._save.stop()
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)

    def hero(self):
        with quiet(): p = Player("1", "base", [])
        return p

    def with_rules(self, effects):
        modes.start_run(modes.combine([effects]))


def fragment(key, value):
    """Il testo che la descrizione di un effetto deve contenere."""
    def pct(m):
        if m == 2: return "doppio"
        if m == 0.5: return "metà"
        return f"{round(abs(m - 1) * 100)}%"
    if key == "room_weights": return pct(next(iter(value.values())))
    if key == "campfire_heal_mult": return f"{round(CAMPFIRE_REST_PCT * value)}%"
    if key in modes.MULT_KEYS: return pct(value)
    if key == "enemy_acc_add": return f"+{value}"
    if key == "start_relic": return "una Reliquia"
    if key == "start_potions_add": return f"{value} pozioni"
    if key in modes.ADD_KEYS: return str(value)
    if key == "pact": return GAME_DATA["meta"]["pacts"][value]["desc"].lower().rstrip(".")
    if key == "enemy_moves": return GAME_DATA["moves"]["moves"][next(iter(value))]["name"]
    raise KeyError(key)


class EffectContractTest(Sandbox):
    def enemy(self, effects, floor=10, **kw):
        modes.end_run(); random.seed(9); before = Enemy(floor, **kw)
        self.with_rules(effects); random.seed(9); after = Enemy(floor, **kw)
        return before, after

    def test_every_effect_key_has_a_contract(self):
        used = {k for _, _, effects in all_effects() for k in effects}
        self.assertLessEqual(used, set(self.CHECKS))
        self.assertEqual(set(self.CHECKS), set(modes.MULT_KEYS) | set(modes.ADD_KEYS) | {"room_weights", "pact", "enemy_moves"})

    def test_every_description_matches_its_numbers(self):
        for name, desc, effects in all_effects():
            for key, value in effects.items():
                with self.subTest(effect=name, key=key):
                    self.assertIn(fragment(key, value), desc.lower() if key == "pact" else desc)
                    # Un Patto del Caos diventato grado ne porta il nome
                    if key == "pact": self.assertEqual(name, GAME_DATA["meta"]["pacts"][value]["name"])

    def test_every_effect_does_what_it_says(self):
        for name, _, effects in all_effects():
            for key, value in effects.items():
                with self.subTest(effect=name, key=key):
                    self.CHECKS[key](self, value)

    # ------------------------------------------------------------- contratti dei singoli effetti
    def _room_weights(self, value):
        self.with_rules({"room_weights": value})
        weights = roguelike.floor_room_weights(GAME_DATA["meta"]["rooms"]["weights"], self.hero())
        for room, mult in value.items(): self.assertAlmostEqual(weights[room], GAME_DATA["meta"]["rooms"]["weights"][room] * mult)

    def _rest(self, value):
        base = roguelike.rest_heal(10)
        self.with_rules({"rest_heal_mult": value})
        self.assertEqual(roguelike.rest_heal(10), int(base * value))

    def _campfire(self, value):
        self.with_rules({"campfire_heal_mult": value})
        p = self.hero(); p.max_hp, p.hp = 1000, 1
        menus = []
        with quiet(), patch_rooms("interactive_menu", side_effect=lambda o, pr="", **k: menus.append(o) or 0), \
             patch_rooms("wait_enter"), patch_rooms("delay_print"), patch_rooms("clear_screen"):
            rooms.campfire_room(p, 5)
        pct = round(CAMPFIRE_REST_PCT * value)
        self.assertEqual(p.hp, 1 + 1000 * pct // 100)
        self.assertIn(f"{pct}%", menus[0][0])

    def _boss_hp(self, value):
        b, a = self.enemy({"boss_hp_mult": value}, is_boss=True, active_pacts=[])
        self.assertEqual(a.hp, int(b.hp * value))

    def _boss_atk(self, value):
        b, a = self.enemy({"boss_atk_mult": value}, is_boss=True, active_pacts=[])
        self.assertEqual(a.atk, int(b.atk * value))

    def _final_boss(self, value):
        b, a = self.enemy({"final_boss_hp_mult": value}, floor=30, is_boss=True, active_pacts=[], final=True)
        self.assertEqual(a.hp, int(b.hp * value))
        b, a = self.enemy({"final_boss_hp_mult": value}, is_boss=True, active_pacts=[])
        self.assertEqual(a.hp, b.hp, "vale solo per il DIO ANTICO")

    def _elite_hp(self, value):
        b, a = self.enemy({"elite_hp_mult": value}, is_boss=False, active_pacts=[], modifier="elite")
        self.assertEqual(a.hp, int(b.hp * value))
        b, a = self.enemy({"elite_hp_mult": value}, is_boss=False, active_pacts=[])
        self.assertEqual(a.hp, b.hp)

    def _enemy_hp(self, value):
        b, a = self.enemy({"enemy_hp_mult": value}, is_boss=False, active_pacts=[])
        self.assertEqual(a.hp, int(b.hp * value))

    def _enemy_atk(self, value):
        for boss in (False, True):
            b, a = self.enemy({"enemy_atk_mult": value}, is_boss=boss, active_pacts=[])
            self.assertEqual(a.atk, int(b.atk * value))

    def _enemy_acc(self, value):
        b, a = self.enemy({"enemy_acc_add": value}, is_boss=False, active_pacts=[])
        self.assertEqual(a.base_acc, b.base_acc + value)

    def _enemy_gold(self, value):
        b, a = self.enemy({"enemy_gold_mult": value}, is_boss=False, active_pacts=[])
        self.assertEqual(a.gold_drop, int(b.gold_drop * value))

    def _chest(self, value):
        base = rooms.chest_risks(8)
        self.with_rules({"chest_risk_mult": value})
        for k, v in rooms.chest_risks(8).items(): self.assertAlmostEqual(v, min(50.0, base[k] * value))

    def _curse(self, value):
        roll = CURSE_CHANCE * (1 + value) / 2  # fra la probabilità normale e quella moltiplicata
        with mock.patch("entities.random.random", return_value=roll):
            self.assertFalse(generate_weapon(5).is_cursed)
            self.with_rules({"curse_chance_mult": value})
            self.assertTrue(generate_weapon(5).is_cursed)

    def _start(self, key, value, measure):
        modes.end_run(); random.seed(3); p = self.hero(); before = measure(p)
        with quiet(): roguelike._apply_mode_start(p)
        self.with_rules({key: value}); random.seed(3); q = self.hero()
        with quiet(): roguelike._apply_mode_start(q)
        return before, measure(q)

    def _start_gold_mult(self, value):
        before, after = self._start("start_gold_mult", value, lambda p: p.gold)
        self.assertEqual(after, int(before * value))

    def _start_gold_add(self, value):
        before, after = self._start("start_gold_add", value, lambda p: p.gold)
        self.assertEqual(after, before + value)

    def _start_corruption(self, value):
        before, after = self._start("start_corruption", value, lambda p: p.corruption)
        self.assertEqual(after, before + value)

    def _start_relic(self, value):
        before, after = self._start("start_relic", value, lambda p: len(p.relic_ids))
        self.assertEqual(after, before + value)

    def _start_potions(self, value):
        before, after = self._start("start_potions_add", value, lambda p: sum(i.type == "consumable" for i in p.inventory))
        self.assertEqual(after, before + value)

    def _start_ether(self, value):
        before, after = self._start("start_ether_add", value, lambda p: (p.max_ether(), p.ether))
        self.assertEqual(after, (before[0] + value, before[1] + value))

    def _floor_ether(self, value):
        gained = []
        for rules in ({}, {"floor_ether_mult": value}):
            modes.end_run(); self.with_rules(rules)
            p = self.hero(); p.base_ether, p.ether = 100, 0
            gained.append(roguelike.rest_ether(p))
        self.assertEqual(gained[1], int(gained[0] * value))

    def _enemy_moves(self, value):
        b, a = self.enemy({"enemy_moves": value}, is_boss=False, active_pacts=[])
        for move, w in value.items(): self.assertEqual(a.moves[move], b.moves.get(move, 0) + w)
        b, a = self.enemy({"enemy_moves": value}, is_boss=True, active_pacts=[])
        self.assertEqual(a.moves, b.moves, "i boss restano come sono")

    def _pact(self, value):
        self.assertIn(value, GAME_DATA["meta"]["pacts"])
        self.assertIn(value, modes.combine([{"pact": value}])["pacts"])

    CHECKS = {
        "room_weights": _room_weights, "rest_heal_mult": _rest, "campfire_heal_mult": _campfire,
        "boss_hp_mult": _boss_hp, "boss_atk_mult": _boss_atk, "final_boss_hp_mult": _final_boss,
        "elite_hp_mult": _elite_hp, "enemy_hp_mult": _enemy_hp, "enemy_atk_mult": _enemy_atk,
        "enemy_acc_add": _enemy_acc, "enemy_gold_mult": _enemy_gold, "chest_risk_mult": _chest,
        "curse_chance_mult": _curse, "start_gold_mult": _start_gold_mult, "start_gold_add": _start_gold_add,
        "start_corruption": _start_corruption, "start_relic": _start_relic, "start_potions_add": _start_potions,
        "pact": _pact, "start_ether_add": _start_ether, "floor_ether_mult": _floor_ether, "enemy_moves": _enemy_moves,
    }


class AscensionTest(Sandbox):
    def test_twenty_cumulative_grades(self):
        self.assertEqual(len(GRADES), GAME_DATA["modes"]["ascension"]["max"])
        self.assertEqual(modes.ascension_rules(0), modes.combine([]))
        r = modes.ascension_rules(len(GRADES))
        self.assertEqual(sorted(r["pacts"]), sorted(GAME_DATA["meta"]["pacts"]), "i Patti del Caos sono tutti diventati gradi")
        mults = [modes.ascension_essence_mult(g) for g in range(len(GRADES) + 1)]
        self.assertEqual(mults, sorted(mults))
        self.assertEqual(mults[0], 1.0)

    def test_grades_unlock_one_by_one_after_the_first_win(self):
        PROFILE_MANAGER._data["won_normal"] = False
        PROFILE_MANAGER._data["ascension"] = {"best_win": 0}
        self.assertEqual(modes.max_grade(), 0)
        PROFILE_MANAGER._data["won_normal"] = True
        self.assertEqual(modes.max_grade(), 1)
        self.assertFalse(modes.record_ascension_win(0))
        self.assertTrue(modes.record_ascension_win(1))
        self.assertEqual(modes.max_grade(), 2)
        modes.record_ascension_win(40)
        self.assertEqual(modes.max_grade(), GAME_DATA["modes"]["ascension"]["max"])

    def test_the_grade_menu_appears_only_after_a_win(self):
        PROFILE_MANAGER._data["won_normal"] = False
        with mock.patch("roguelike.interactive_menu") as menu:
            self.assertEqual(roguelike._choose_ascension(), 0)
        menu.assert_not_called()
        PROFILE_MANAGER._data["won_normal"] = True
        PROFILE_MANAGER._data["ascension"] = {"best_win": 2}
        with mock.patch("roguelike.interactive_menu", return_value=3) as menu:
            self.assertEqual(roguelike._choose_ascension(), 3)
        options = [plain(o) for o in menu.call_args[0][0]]
        self.assertEqual(len(options), 4)
        self.assertIn(GRADES[2]["name"], options[3])
        self.assertEqual(menu.call_args[1]["initial"], 3)

    def test_the_essence_follows_the_grade(self):
        rewards = {}
        for grade in (0, 5):
            p = self.hero(); p.ascension, p.hp, p.essence_gathered, p.gold = grade, 0, 100, 0
            before = PROFILE_MANAGER.essence
            with quiet(), mock.patch("roguelike.wait_enter"), mock.patch("roguelike.delay_print"): roguelike.evaluate_run(p, 5, False)
            rewards[grade] = PROFILE_MANAGER.essence - before
        self.assertEqual(rewards[5], int(rewards[0] * modes.ascension_essence_mult(5)))

    def test_a_run_uses_the_chosen_grade_and_cleans_up(self):
        seen = {}
        def descent(c, t, pacts, infinite, grade, daily):
            seen.update(pacts=pacts, grade=grade, rules=dict(modes.RUN))
        with mock.patch("roguelike._hero_selection", return_value=("1", "base", [])), mock.patch("roguelike._choose_ascension", return_value=20), \
             mock.patch("roguelike._descent", side_effect=descent):
            roguelike.play_game()
        self.assertEqual(seen["grade"], 20)
        self.assertEqual(sorted(seen["pacts"]), sorted(GAME_DATA["meta"]["pacts"]))
        self.assertEqual(seen["rules"]["enemy_atk_mult"], modes.ascension_rules(20)["enemy_atk_mult"])
        self.assertEqual(modes.rule("enemy_atk_mult"), 1.0, "finita la discesa le regole tornano neutre")


class DailyTest(Sandbox):
    DAY = datetime.date(2026, 10, 23)

    def test_the_same_day_gives_the_same_challenge(self):
        self.assertEqual(modes.daily_setup(self.DAY), modes.daily_setup(self.DAY))
        days = [modes.daily_setup(self.DAY + datetime.timedelta(days=i)) for i in range(10)]
        self.assertGreater(len({(d["class_id"], d["trait_id"], tuple(d["maluses"]), d["boon"]) for d in days}), 5)
        for d in days:
            self.assertIn(d["class_id"], GAME_DATA["classes"])
            self.assertIn(d["trait_id"], GAME_DATA["meta"]["traits"])
            self.assertEqual(len(set(d["maluses"])), GAME_DATA["modes"]["daily"]["maluses"])

    def test_the_rules_are_the_maluses_plus_the_boon(self):
        setup = modes.daily_setup(self.DAY)
        effects = [GRADE[g]["effects"] for g in setup["maluses"]] + [BOON[setup["boon"]]["effects"]]
        self.assertEqual(modes.daily_rules(setup), modes.combine(effects))

    def test_every_grade_and_boon_has_its_own_id(self):
        ids = [g["id"] for g in GRADES] + [b["id"] for b in BOONS]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(isinstance(i, str) and i for i in ids))

    def test_the_order_of_the_data_does_not_change_the_challenge(self):
        days = [self.DAY + datetime.timedelta(days=i) for i in range(30)]
        before = [modes.daily_setup(d) for d in days]
        shuffled = {"grades": list(reversed(GRADES)), "boons": list(reversed(BOONS)),
                    "classes": dict(reversed(list(GAME_DATA["classes"].items()))),
                    "traits": dict(reversed(list(GAME_DATA["meta"]["traits"].items())))}
        with mock.patch.dict(GAME_DATA["modes"]["ascension"], grades=shuffled["grades"]), \
             mock.patch.dict(GAME_DATA["modes"]["daily"], boons=shuffled["boons"]), \
             mock.patch.dict(GAME_DATA, classes=shuffled["classes"]), mock.patch.dict(GAME_DATA["meta"], traits=shuffled["traits"]):
            after = [modes.daily_setup(d) for d in days]
        for a, b in zip(before, after):
            self.assertEqual({**a, "maluses": set(a["maluses"])}, {**b, "maluses": set(b["maluses"])})

    def test_new_content_changes_only_the_days_it_wins(self):
        days = [self.DAY + datetime.timedelta(days=i) for i in range(60)]
        before = [modes.daily_setup(d) for d in days]
        new_boon = {"id": "dono_nuovo", "name": "Dono Nuovo", "desc": "", "effects": {"start_gold_add": 1}}
        new_class = dict(GAME_DATA["classes"]["1"], role="Classe Nuova")
        with mock.patch.dict(GAME_DATA["modes"]["daily"], boons=BOONS + [new_boon]), mock.patch.dict(GAME_DATA["classes"], {"99": new_class}):
            after = [modes.daily_setup(d) for d in days]
        changed = [(a, b) for a, b in zip(before, after) if a != b]
        self.assertTrue(changed, "il contenuto nuovo arriva in qualche giorno")
        self.assertLess(len(changed), len(days) // 2)
        for a, b in changed:
            self.assertTrue(b["boon"] == "dono_nuovo" or b["class_id"] == "99", "cambia solo dove vince il nuovo")
            self.assertEqual(a["maluses"], b["maluses"])
            self.assertEqual(a["trait_id"], b["trait_id"])

    def test_only_the_first_attempt_counts(self):
        PROFILE_MANAGER._data["daily"] = {}
        setup = modes.daily_setup(self.DAY)
        score = modes.record_daily(setup, 12, 2, False, 300, "Mago")
        s = GAME_DATA["modes"]["daily"]["score"]
        self.assertEqual(score, 12 * s["per_floor"] + 2 * s["per_boss"] + 300 // s["gold_div"])
        self.assertIsNone(modes.record_daily(setup, 30, 6, True, 999, "Mago"))
        self.assertEqual(modes.daily_history()[setup["date"]]["score"], score)
        self.assertEqual(modes.daily_history()[setup["date"]]["setup"],
                         {k: setup[k] for k in ("class_id", "trait_id", "maluses", "boon")}, "lo storico ricorda la sfida giocata")

    def test_history_is_trimmed_and_streaks_count_consecutive_days(self):
        PROFILE_MANAGER._data["daily"] = {}
        keep = GAME_DATA["modes"]["daily"]["history"]
        for i in range(keep + 5):
            modes.record_daily(modes.daily_setup(self.DAY - datetime.timedelta(days=i)), 1, 0, False, 0, "Guerriero")
        self.assertEqual(len(modes.daily_history()), keep)
        self.assertEqual(modes.daily_streak(self.DAY), keep)
        del modes.daily_history()[(self.DAY - datetime.timedelta(days=3)).isoformat()]
        self.assertEqual(modes.daily_streak(self.DAY), 3)
        self.assertEqual(modes.daily_streak(self.DAY + datetime.timedelta(days=1)), 3, "oggi non ancora giocato: conta da ieri")

    def test_the_first_attempt_pays_more_essence(self):
        PROFILE_MANAGER._data["daily"] = {}
        setup, rewards = modes.daily_setup(self.DAY), []
        for _ in range(2):
            p = self.hero(); p.daily, p.hp, p.essence_gathered, p.gold = setup, 0, 100, 0
            before = PROFILE_MANAGER.essence
            with quiet(), mock.patch("roguelike.wait_enter"), mock.patch("roguelike.delay_print"): roguelike.evaluate_run(p, 5, False)
            rewards.append(PROFILE_MANAGER.essence - before)
        self.assertEqual(rewards[0], int(rewards[1] * GAME_DATA["modes"]["daily"]["first_attempt_essence_mult"]))

    def play_daily(self, setup, choice):
        """Una Sfida del Giorno nel vero ciclo dei piani: scelte sempre uguali (`choice`), stanze simulate."""
        maps, heroes = [], []
        real_map = roguelike.generate_floor_map
        def make_map(floor, *a, **k):
            rows = real_map(floor, *a, **k)
            maps.append((floor, [[(d["type"], d.get("enemy").base_name if d.get("enemy") else None) for d in row] for row in rows]))
            return rows
        def menu(options, prompt="", **kw):
            doors = sum(o.startswith("Entra:") for o in options)  # le porte vengono prima delle altre voci
            return min(choice, doors - 1) if "Scegli dove proseguire" in prompt else 0
        rooms_ = {n: mock.DEFAULT for n in ("combat_room", "vendor_room", "treasure_room", "campfire_room", "mystery_room", "event_room")}
        with quiet(), mock.patch("roguelike._hero_selection") as hero_sel, mock.patch("roguelike.interactive_menu", side_effect=menu), \
             mock.patch("roguelike.generate_floor_map", side_effect=make_map), mock.patch.multiple("roguelike", **rooms_), \
             mock.patch("roguelike.trap_room", return_value=False), mock.patch("roguelike.evaluate_run", side_effect=lambda p, f, i: heroes.append(p)), \
             mock.patch("roguelike.wait_enter"), mock.patch("roguelike.clear_screen"), mock.patch("roguelike.delay_print"), mock.patch("roguelike.time.sleep"), \
             mock.patch("roguelike._grant_victory_rewards"), mock.patch("roguelike.choose_ending"), mock.patch("roguelike.start_of_run_boon"):
            roguelike.play_game(daily=setup)
        hero_sel.assert_not_called()
        return maps, heroes[0]

    def test_every_floor_is_the_same_whatever_path_was_taken(self):
        setup = modes.daily_setup(self.DAY)
        maps_left, hero = self.play_daily(setup, 0)
        maps_right, _ = self.play_daily(setup, 2)
        self.assertEqual(hero.class_id, setup["class_id"])
        self.assertIs(hero.daily, setup)
        self.assertEqual(len(maps_left), 30)
        self.assertEqual(maps_left, maps_right)
        self.assertEqual(modes.rule("start_gold_add"), 0, "finita la sfida le regole tornano neutre")

    def test_the_hero_stats_list_the_rules_of_the_descent(self):
        import inventory_menu
        p = self.hero(); p.ascension = 3
        self.assertEqual(inventory_menu.mode_rule_lines(p), [f"{g['name']}: {g['desc']}" for g in GRADES[:3]])
        p.ascension, p.daily = 0, modes.daily_setup(self.DAY)
        lines = inventory_menu.mode_rule_lines(p)
        self.assertEqual(len(lines), GAME_DATA["modes"]["daily"]["maluses"] + 1)
        self.assertIn(BOON[p.daily["boon"]]["name"], lines[-1])

    def test_the_daily_page_shows_hero_rules_and_record(self):
        PROFILE_MANAGER._data["daily"] = {}
        setup = modes.daily_setup(self.DAY)
        page = plain(roguelike.daily_page(setup))
        self.assertIn(GAME_DATA["classes"][setup["class_id"]]["role"], page)
        for g in setup["maluses"]: self.assertIn(GRADE[g]["name"], page)
        self.assertIn(BOON[setup["boon"]]["name"], page)
        modes.record_daily(setup, 9, 1, False, 0, "Ladro")
        self.assertIn(f"{modes.daily_history()[setup['date']]['score']} punti", plain(roguelike.daily_page(setup)))


if __name__ == "__main__":
    unittest.main()
