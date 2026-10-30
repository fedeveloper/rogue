"""La Nemesi: chi ti uccide se ne ricorda, sale di rango, torna vicino al piano della tua morte e paga se la sconfiggi."""
import copy
import io
import random
import re
import unittest
from contextlib import redirect_stdout
from unittest import mock

import codex
import floor_map
import nemesis
import roguelike
import rooms
from data_manager import GAME_DATA, PROFILE_MANAGER
from entities import Enemy, Player
from rooms import CombatSession

ANSI = re.compile(r"\x1b\[[0-9;]*m")
DATA = GAME_DATA["nemesis"]
RULES = DATA["rules"]


def quiet():
    return redirect_stdout(io.StringIO())


def plain(text):
    return ANSI.sub("", text)


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        PROFILE_MANAGER._data.update(nemeses=[], nemeses_fallen=[], boss_grudges={})
        self._save = mock.patch.object(PROFILE_MANAGER, "save")
        self._save.start()
        random.seed(2)

    def tearDown(self):
        self._save.stop()
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)

    def hero(self, gold=400):
        with quiet(): p = Player("1", "base", [])
        p.gold, p.hp = gold, 0
        return p

    def die_to(self, p, name="Goblin", boss=False, nemesis_id=None, floor=7):
        p.run_tracker["killer"] = {"name": name, "is_boss": boss, "nemesis_id": nemesis_id, "player_element": "Fuoco"}
        return nemesis.on_death(p, floor)


class NemesisDataTest(unittest.TestCase):
    def test_data_is_complete(self):
        self.assertGreaterEqual(len(DATA["names"]), RULES["max_active"])
        self.assertEqual(len(DATA["ranks"]), RULES["max_rank"])
        for tid, t in DATA["traits"].items():
            with self.subTest(trait=tid):
                self.assertIn(str(t["value"]), t["desc"])
        for key in ("born", "returns", "rank_up", "defeated", "boss_grudge"): self.assertIn(key, DATA["text"])


class BirthTest(Sandbox):
    def test_a_common_killer_becomes_a_nemesis_and_takes_gold(self):
        p = self.hero(400)
        story = self.die_to(p)
        [nem] = nemesis.active()
        self.assertEqual((nem["enemy"], nem["rank"], nem["kills"], nem["floor"]), ("Goblin", 1, 1, 7))
        self.assertEqual(nem["gold"], 400 * RULES["gold_taken_pct"] // 100)
        self.assertIn(nem["trait"], DATA["traits"])
        self.assertIn(nem["name"], story)

    def test_bosses_and_mimics_only_remember(self):
        p = self.hero()
        self.assertIsNone(self.die_to(p, "Re dei Goblin", boss=True))
        self.assertIsNone(self.die_to(p, "Mimic"))
        self.assertEqual(nemesis.active(), [])
        self.assertEqual(PROFILE_MANAGER._data["boss_grudges"], {"Re dei Goblin": 1})
        self.assertIn("Re dei Goblin", nemesis.boss_grudge("Re dei Goblin"))
        self.assertIsNone(nemesis.boss_grudge("Drago di Zaffiro"))

    def test_a_death_outside_combat_makes_no_nemesis(self):
        p = self.hero()
        self.assertIsNone(nemesis.on_death(p, 5))
        self.assertEqual(nemesis.active(), [])

    def test_killing_you_again_raises_the_rank(self):
        p = self.hero(200)
        self.die_to(p)
        nem = nemesis.active()[0]
        for i in range(RULES["max_rank"] + 2):
            story = self.die_to(self.hero(100), nemesis_id=nem["id"], floor=9)
        self.assertEqual(len(nemesis.active()), 1, "la stessa Nemesi, non una nuova")
        self.assertEqual(nem["rank"], RULES["max_rank"])
        self.assertEqual(nem["kills"], RULES["max_rank"] + 3)
        self.assertEqual(nem["floor"], 9)
        self.assertEqual(nem["gold"], 100 + (RULES["max_rank"] + 2) * 50)
        self.assertIn(DATA["ranks"][-1], story)

    def test_only_the_newest_nemeses_stay(self):
        for _ in range(RULES["max_active"] + 2): self.die_to(self.hero())
        self.assertEqual(len(nemesis.active()), RULES["max_active"])


class ReturnTest(Sandbox):
    def make(self, trait="hp_bonus_pct", rank=1, floor=7):
        self.die_to(self.hero(), floor=floor)
        nem = nemesis.active()[0]
        nem.update(trait=trait, rank=rank)
        return nem

    def test_it_waits_near_the_floor_of_your_death(self):
        nem = self.make(floor=7)
        lo, hi = RULES["floor_window"]
        self.assertIs(nemesis.waiting_on(7 + lo, set()), nem)
        self.assertIs(nemesis.waiting_on(7 + hi, set()), nem)
        self.assertIsNone(nemesis.waiting_on(7 + hi + 1, set()))
        self.assertIsNone(nemesis.waiting_on(7, {nem["id"]}), "una volta per discesa")

    def test_the_map_places_it_once_per_descent(self):
        nem = self.make(floor=7)
        p = self.hero(); p.hp = 100
        w = GAME_DATA["meta"]["rooms"]["weights"]
        rooms_ = lambda: [d for row in floor_map.generate_floor_map(7, w, {}, {k: 0 for k in w}, [], p) for d in row if d["type"] == "nemesis"]
        with quiet(): first = rooms_()
        self.assertEqual(len(first), 1)
        self.assertIn(nem["name"], plain(floor_map.room_label(first[0])))
        self.assertIn(f"{nem['gold']} Oro", plain(floor_map.room_label(first[0])))
        with quiet(): self.assertEqual(rooms_(), [])

    def test_it_grows_with_its_rank_and_trait(self):
        random.seed(3); base = Enemy(7, False, [], name="Goblin")
        for trait, rank in (("hp_bonus_pct", 1), ("atk_bonus_pct", 3), ("acc_add", 2)):
            nem = self.make(trait, rank)
            random.seed(3)
            e = nemesis.build_enemy(nem, 7, [])
            mult = 1 + RULES["stats_pct_per_rank"] * rank / 100
            v = DATA["traits"][trait]["value"]
            with self.subTest(trait=trait):
                self.assertEqual(e.hp, int(base.hp * mult * (1 + v / 100 if trait == "hp_bonus_pct" else 1)))
                self.assertEqual(e.atk, int(base.atk * mult * (1 + v / 100 if trait == "atk_bonus_pct" else 1)))
                self.assertEqual(e.base_acc, base.base_acc + (v if trait == "acc_add" else 0))
                self.assertIn("Nemesi", plain(e.name))
            PROFILE_MANAGER._data["nemeses"] = []

    def test_it_resists_the_element_that_killed_you(self):
        nem = self.make("resist_element")
        v = DATA["traits"]["resist_element"]["value"]
        self.assertEqual(nemesis.resisted(nem, "Fuoco"), 1 - v / 100)
        self.assertEqual(nemesis.resisted(nem, "Acqua"), 1.0)
        nem["trait"] = "acc_add"
        self.assertEqual(nemesis.resisted(nem, "Fuoco"), 1.0)


class FightTest(Sandbox):
    def session(self, nem):
        p = self.hero(0); p.hp = p.max_hp = 1000
        with quiet(): s = CombatSession(p, 7, nemesis.build_enemy(nem, 7, []))
        return p, s

    def test_a_death_in_combat_names_the_killer(self):
        p = self.hero(); p.hp = 0
        with quiet(): s = CombatSession(p, 5, Enemy(5, False, [], name="Goblin"))
        s._end_combat()
        self.assertEqual(p.run_tracker["killer"]["name"], "Goblin")
        self.assertFalse(p.run_tracker["killer"]["is_boss"])

    def test_defeating_it_returns_the_gold_and_leaves_a_trophy(self):
        self.die_to(self.hero(400))
        nem = nemesis.active()[0]
        p, s = self.session(nem)
        with quiet(), mock.patch("rooms.wait_enter"): s.on_enemy_death()
        self.assertEqual(nemesis.active(), [])
        self.assertEqual(nemesis.fallen()[-1]["name"], nem["name"])
        self.assertGreaterEqual(p.gold, nem["gold"])
        self.assertTrue(any(i.name.startswith("Trofeo:") for i in p.inventory))

    def test_the_resisted_element_shows_in_combat(self):
        self.die_to(self.hero())
        nem = nemesis.active()[0]; nem["trait"] = "resist_element"
        dealt = []
        for element in ("Fuoco", "Normale"):
            p, s = self.session(nem)
            p.weapon.element = element
            s.enemy.element, s.enemy.hp = "Normale", 10 ** 6
            with quiet(), mock.patch.object(s, "attack_multiplier", return_value=1.0), mock.patch("rooms.random.randint", return_value=1):
                s.execute_player_attack()
            dealt.append(10 ** 6 - s.enemy.hp)
        self.assertEqual(dealt[0], int(dealt[1] * nemesis.resisted(nem, "Fuoco")))

    def test_the_end_of_a_fatal_run_announces_the_nemesis(self):
        p = self.hero(300); p.hp = 0
        p.run_tracker["killer"] = {"name": "Goblin", "is_boss": False, "nemesis_id": None, "player_element": "Normale"}
        out = io.StringIO()
        with redirect_stdout(out), mock.patch("roguelike.wait_enter"), mock.patch("roguelike.delay_print"):
            roguelike.evaluate_run(p, 6, False)
        self.assertIn(nemesis.active()[0]["name"], plain(out.getvalue()))

    def test_the_codex_tells_their_story(self):
        self.die_to(self.hero())
        nem = nemesis.active()[0]
        page = "\n".join(plain(l) for l in codex.nemeses_page())
        self.assertIn(nemesis.full_name(nem), page)
        nemesis.defeat(nem)
        page = "\n".join(plain(l) for l in codex.nemeses_page())
        self.assertIn("Nessuno. Per ora.", page)
        self.assertIn(nem["name"], page.split("SCONFITTE")[1])
        before = codex.completion()
        self.die_to(self.hero())
        self.assertEqual(codex.completion(), before, "le Nemesi non cambiano il completamento del Codice")


if __name__ == "__main__":
    unittest.main()
