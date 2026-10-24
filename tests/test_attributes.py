"""Gli attributi dell'eroe: dati, attributi della classe, punti a ogni livello, effetto di ogni attributo, menu e Statistiche."""
import copy
import io
import random
import re
import unittest
from contextlib import redirect_stdout
from unittest import mock

import attributes
import inventory_menu
import runes
from data_manager import GAME_DATA, PROFILE_MANAGER, RAW_DATA
from entities import Armor, Enemy, Player, Weapon
from rooms import CombatSession

ANSI = re.compile(r"\x1b\[[0-9;]*m")
DATA = GAME_DATA["attributes"]
DEFS, RULES = DATA["attributes"], DATA["rules"]


def quiet():
    return redirect_stdout(io.StringIO())


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        self._save = mock.patch.object(PROFILE_MANAGER, "save")
        self._save.start()
        random.seed(8)

    def tearDown(self):
        self._save.stop()
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)

    def hero(self, cls="1", **points):
        """Un eroe senza attributi (o con quelli indicati), per misurare l'effetto di un punto alla volta."""
        with quiet(): p = Player(cls, "base", [])
        for a in p.attributes: p.attributes[a] = points.get(a, 0)
        return p

    def per(self, attr, key):
        return DEFS[attr]["per_point"][key]


class DataTest(Sandbox):
    def test_six_attributes_and_their_texts_tell_the_numbers(self):
        self.assertEqual(set(DEFS), {"vitalita", "forza", "destrezza", "agilita", "arcano", "fortuna"})
        for a, d in DEFS.items():
            with self.subTest(attribute=a):
                self.assertTrue(d["name"] and d["icon"] and d["desc"])
                for v in d["per_point"].values(): self.assertIn(f"+{v}", d["desc"])
        rule = RULES["desc"]
        self.assertIn(f"+{RULES['per_level']['max_hp']} HP", rule)
        self.assertIn(f"+{RULES['per_level']['acc']}% Precisione", rule)
        self.assertIn(f"+{RULES['per_level']['dodge']}% Schivata", rule)
        self.assertIn(f"{RULES['points_per_level']} punto", rule)
        self.assertIn(f"{RULES['max_points']} punti", rule)

    def test_every_class_starts_with_its_own_attributes(self):
        seen = set()
        for cid, c in RAW_DATA["classes"].items():
            with self.subTest(cls=c["role"]):
                self.assertLessEqual(set(c["attributes"]), set(DEFS))
                self.assertEqual(sum(c["attributes"].values()), 3, "stesso numero di punti per tutte le classi")
                self.assertTrue(all(0 < v <= RULES["max_points"] for v in c["attributes"].values()))
                seen.add(tuple(sorted(c["attributes"].items())))
        self.assertEqual(len(seen), len(RAW_DATA["classes"]), "ogni classe ha una distribuzione diversa")

    def test_the_hero_really_starts_with_them(self):
        for cid, c in RAW_DATA["classes"].items():
            with self.subTest(cls=c["role"]), quiet():
                p = Player(cid, "base", [])
            self.assertEqual({a: v for a, v in p.attributes.items() if v}, c["attributes"])
            self.assertEqual(p.max_hp, c["max_hp"] + PROFILE_MANAGER.get_perk("hp_lvl", 0) * 15 + c["attributes"].get("vitalita", 0) * self.per("vitalita", "max_hp"))
            self.assertEqual(p.unspent_points, 0)


class LevelTest(Sandbox):
    def test_a_level_gives_a_point_and_a_smaller_automatic_growth(self):
        p = self.hero(); p.hp = 1
        hp, acc, dodge = p.max_hp, p.base_acc, p.base_dodge
        with quiet(): p.gain_exp(p.max_exp)
        g = RULES["per_level"]
        self.assertEqual((p.level, p.unspent_points, p.points_offered), (2, RULES["points_per_level"], False))
        self.assertEqual((p.max_hp, p.base_acc, p.base_dodge), (hp + g["max_hp"], acc + g["acc"], dodge + g["dodge"]))
        self.assertEqual(p.hp, p.max_hp, "il livello cura ancora tutto")
        with quiet(): p.gain_exp(p.max_exp * 10)
        self.assertGreater(p.unspent_points, 2, "più livelli insieme, più punti")

    def test_spending_and_its_limits(self):
        p = self.hero()
        self.assertFalse(attributes.raise_attribute(p, "forza"), "senza punti non si sale")
        p.unspent_points = RULES["max_points"] + 3
        for _ in range(RULES["max_points"] + 3): attributes.raise_attribute(p, "forza")
        self.assertEqual((p.attributes["forza"], p.unspent_points), (RULES["max_points"], 3))

    def test_the_menu_spends_one_point_at_a_time_and_can_wait(self):
        p = self.hero(); p.unspent_points, p.points_offered = 3, False
        names = list(DEFS)
        picks = iter([names.index("agilita"), names.index("agilita"), len(names)])
        with quiet(), mock.patch("attributes.interactive_menu", side_effect=lambda o, pr="": next(picks)), mock.patch("attributes.clear_screen"):
            attributes.spend_points(p)
        self.assertEqual((p.attributes["agilita"], p.unspent_points, p.points_offered), (2, 1, True))

    def test_the_tome_keeps_the_attributes_of_the_class(self):
        with quiet(): p = Player("5", "base", [])
        start, hp = dict(p.attributes), p.max_hp
        p.unspent_points = 2
        attributes.raise_attribute(p, "vitalita"); attributes.raise_attribute(p, "forza")
        self.assertEqual(attributes.reset(p), 2)
        self.assertEqual((p.attributes, p.unspent_points, p.max_hp), (start, 2, hp))


class EffectTest(Sandbox):
    def test_vitality(self):
        p = self.hero(); p.unspent_points = 1; hp, cur = p.max_hp, p.hp
        attributes.raise_attribute(p, "vitalita")
        self.assertEqual((p.max_hp, p.hp), (hp + self.per("vitalita", "max_hp"), cur + self.per("vitalita", "max_hp")))

    def test_dexterity_and_agility(self):
        base, dex, agi = self.hero(), self.hero(destrezza=2), self.hero(agilita=2)
        for p in (base, dex, agi): p.base_acc, p.base_dodge = -40, 10
        self.assertEqual(dex.get_hit_chance() - base.get_hit_chance(), 2 * self.per("destrezza", "acc"))
        self.assertEqual(dex.get_crit_chance() - base.get_crit_chance(), 2 * self.per("destrezza", "crit"))
        self.assertEqual(agi.get_dodge() - base.get_dodge(), 2 * self.per("agilita", "dodge"))
        escape = []
        for p in (base, agi):
            p.base_dodge = 0
            with quiet(): s = CombatSession(p, 3, Enemy(3, False, [], name="Goblin"))
            s.enemy.base_dodge = 0
            escape.append(s._calc_escape_chance())
        self.assertEqual(escape[1] - escape[0], 2 * self.per("agilita", "escape") + 2 * self.per("agilita", "dodge"),
                         "la fuga cresce con la Schivata e, in più, con l'Agilità")

    def strike(self, p):
        p.weapon = Weapon("Lama", 1, 100, "Normale", 1); p.base_acc = 1000
        with quiet(): s = CombatSession(p, 3, Enemy(3, False, [], name="Goblin"))
        s.enemy.hp = s.enemy.max_hp = 10 ** 6; s.enemy.element, s.enemy.base_dodge, s.intent = "Normale", 0, "attack"
        with quiet(), mock.patch("rooms.random.randint", side_effect=lambda a, b: b if b == 100 else 0), mock.patch("entities.random.randint", return_value=100):
            s.execute_player_attack()
        return 10 ** 6 - s.enemy.hp

    def test_strength_makes_weapons_hit_harder(self):
        plain, strong = self.strike(self.hero()), self.strike(self.hero(forza=3))
        self.assertEqual(strong, plain * (100 + 3 * self.per("forza", "weapon_dmg_pct")) // 100)

    def test_arcane_makes_reactions_hit_harder(self):
        dealt = []
        for p in (self.hero(), self.hero(arcano=2)):
            p.weapon = Weapon("Lama", 1, 100, "Fuoco", 1)
            with quiet(): s = CombatSession(p, 3, Enemy(3, False, [], name="Goblin"))
            s.enemy.hp = s.enemy.max_hp = 10 ** 6; s.enemy.mark = ["Vento", 2]
            with quiet(): s._trigger_reaction("Fuoco+Vento")
            dealt.append(10 ** 6 - s.enemy.hp)
        self.assertEqual(dealt[1], dealt[0] * (100 + 2 * self.per("arcano", "reaction_dmg_pct")) // 100)

    def test_luck_brings_gold_and_runes(self):
        base, lucky = self.hero(), self.hero(fortuna=2)
        self.assertEqual(lucky.calculate_gold_gain(1000), base.calculate_gold_gain(1000) * (100 + 2 * self.per("fortuna", "gold_pct")) // 100)
        chance = GAME_DATA["runes"]["rules"]["drops"]["elite"]
        bonus = 2 * self.per("fortuna", "rune_drop_add")
        with mock.patch("runes.random.random", return_value=(chance + bonus - 0.5) / 100):
            self.assertFalse(runes.roll_drop("elite"))
            self.assertTrue(runes.roll_drop("elite", bonus))
        with mock.patch("runes.random.random", return_value=0.0):
            self.assertFalse(runes.roll_drop("nessuna_fonte", bonus), "la Fortuna non crea rune dove non ce ne sono")


class ScreenTest(Sandbox):
    def test_the_stats_show_attributes_and_points(self):
        p = self.hero(forza=2); p.unspent_points = 1
        out = io.StringIO()
        with redirect_stdout(out), mock.patch("inventory_menu.clear_screen"), mock.patch("inventory_menu.wait_enter"):
            inventory_menu.show_player_stats(p)
        text = ANSI.sub("", out.getvalue())
        self.assertIn(f"{DEFS['forza']['name']} 2", text)
        self.assertIn("Punti da spendere: 1", text)


if __name__ == "__main__":
    unittest.main()
