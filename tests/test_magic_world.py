"""La magia nel mondo: nemici che combattono la magia (Arcanista, nativi, fasi dei boss, Eco del Ciclo), Nemesi
Antimagia, scelte degli eventi per attributo e per chi conosce incantesimi, Maestria Lv.6 e l'effetto magico condiviso
da attributi, talenti, rune, reliquie e Maestria (`Player.magic_value`)."""
import copy
import io
import random
import unittest
from contextlib import redirect_stdout
from unittest import mock

import events
import magic
import nemesis
import roguelike
from data_manager import GAME_DATA, PROFILE_MANAGER, RAW_DATA, cycle_of
from entities import Armor, Enemy, Player, Weapon
from rooms import CombatSession

MOVES = GAME_DATA["moves"]
ARCANE = ("silence", "ether_drain", "spellcast")


def quiet():
    return redirect_stdout(io.StringIO())


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        self._save = mock.patch.object(PROFILE_MANAGER, "save")
        self._save.start()
        random.seed(6)

    def tearDown(self):
        self._save.stop()
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)

    def hero(self, cls="1"):
        with quiet(): p = Player(cls, "base", [])
        for a in p.attributes: p.attributes[a] = 0
        p.weapon, p.armor = Weapon("Lama", 1, 100, "Normale", 1), Armor("Corazza", 1, 10, "Normale", 1)
        return p


class EnemiesTest(Sandbox):
    def test_the_arcanist_style_and_who_uses_it(self):
        style = MOVES["profiles"]["arcanista"]["moves"]
        self.assertTrue({"silence", "ether_drain"} <= set(style))
        users = [n for n, e in RAW_DATA["enemies"].items() if e.get("profile") == "arcanista"]
        self.assertTrue(users)
        self.assertIn("silence", RAW_DATA["enemies"]["Novizia del Silenzio"]["moves"])
        self.assertIn("ether_drain", RAW_DATA["enemies"]["Bibliotecario di Cenere"]["moves"])

    def test_some_bosses_cast_spells_in_a_phase(self):
        casters = {b for b, phases in GAME_DATA["phases"].items() for ph in phases if set(ph.get("moves", {})) & set(ARCANE)}
        self.assertGreaterEqual(len(casters), 5)
        self.assertIn("La Badessa del Silenzio", casters)
        self.assertIn("DIO ANTICO", casters)

    def test_echoes_teach_every_enemy_to_fight_magic(self):
        extra = GAME_DATA["meta"]["cycle"]["arcane_moves"]
        self.assertIn("Risucchio d'Etere", GAME_DATA["meta"]["cycle"]["desc"])
        floor = next(f for f in range(31, 61) if cycle_of(f))
        for boss, name in ((False, "Goblin"), (True, "Re dei Goblin")):
            with self.subTest(boss=boss):
                with quiet(): before, after = Enemy(10, boss, [], name=name), Enemy(floor, boss, [], name=name)
                for move, w in extra.items(): self.assertEqual(after.moves.get(move, 0), before.moves.get(move, 0) + w)
                self.assertEqual(before.extra_moves, {}, "fuori dalle Eco niente mosse in più")

    def test_echo_moves_survive_a_boss_phase(self):
        floor = next(f for f in range(31, 61) if cycle_of(f))
        with quiet(): e = Enemy(floor, True, [], name="La Badessa del Silenzio")
        p = self.hero()
        with quiet(): s = CombatSession(p, floor, e)
        e.hp = e.max_hp // 4
        with quiet(), mock.patch("rooms.wait_enter"): s.check_phase()
        for move, w in GAME_DATA["meta"]["cycle"]["arcane_moves"].items():
            self.assertGreaterEqual(e.moves.get(move, 0), w)


class NemesisTest(Sandbox):
    def test_antimagic_is_learned_only_from_casters(self):
        caster, fighter = self.hero(), self.hero()
        caster.spells, fighter.spells = ["raffica"], []
        self.assertIn("antimagia", nemesis.traits_for(caster))
        self.assertNotIn("antimagia", nemesis.traits_for(fighter))

    def test_antimagic_resists_spells_and_fights_with_silence(self):
        trait = GAME_DATA["nemesis"]["traits"]["antimagia"]
        self.assertIn(f"{trait['value']}%", trait["desc"])
        nem = {"id": "n1", "enemy": "Goblin", "name": "Morsa", "rank": 1, "kills": 1, "gold": 0, "floor": 5, "trait": "antimagia", "element": "Normale", "class": "Mago"}
        with quiet(): e = nemesis.build_enemy(nem, 5, [])
        for move, w in trait["moves"].items(): self.assertGreaterEqual(e.moves[move], w)
        dealt = []
        for enemy in (Enemy(5, False, [], name="Goblin"), e):
            enemy.element = "Normale"
            with quiet(): s = CombatSession(self.hero(), 5, enemy)
            dealt.append(s.spell_damage("raffica", 100))
        self.assertEqual(dealt[1], max(1, int(self.hero().get_total_atk() * MULT(e) * (1 - trait["value"] / 100))))

    def test_a_resisting_nemesis_resists_spells_of_its_element(self):
        nem = {"trait": "resist_element", "element": "Fuoco"}
        self.assertEqual(nemesis.spell_resisted(nem, "Fuoco"), nemesis.resisted(nem, "Fuoco"))
        self.assertLess(nemesis.spell_resisted(nem, "Fuoco"), 1)
        self.assertEqual(nemesis.spell_resisted(nem, "Acqua"), 1.0)


def MULT(enemy):
    from data_manager import MULTIPLIERS
    return MULTIPLIERS.get(magic.spell("raffica")["element"], {}).get(enemy.element, 1.0)


class EventTest(Sandbox):
    def choices(self, key):
        return [c for e in GAME_DATA["events"].values() for sc in e["scenes"].values() for c in sc["choices"] if key in c.get("requires", {})]

    def test_every_attribute_opens_a_choice(self):
        seen = {a for c in self.choices("attribute") for a in c["requires"]["attribute"]}
        self.assertEqual(seen, set(GAME_DATA["attributes"]["attributes"]))
        self.assertGreaterEqual(len(self.choices("spells")), 2)

    def test_attribute_and_spell_conditions(self):
        p = self.hero()
        req = {"attribute": {"forza": 4}}
        self.assertFalse(events.check(p, req, 5))
        p.attributes["forza"] = 4
        self.assertTrue(events.check(p, req, 5))
        self.assertEqual(events.tags(req), ["💪 Forza 4+"])
        p.spells = []
        self.assertFalse(events.check(p, {"spells": True}, 5))
        p.spells = ["raffica"]
        self.assertTrue(events.check(p, {"spells": True}, 5))
        self.assertEqual(events.tags({"spells": True}), ["Incantesimi"])


class MasteryTest(Sandbox):
    def test_every_class_has_an_arcane_sixth_level(self):
        reqs = GAME_DATA["meta"]["mastery_xp_requirements"]
        self.assertGreater(reqs["6"], reqs["5"])
        keys = {"ether_max", "spell_pct", "ether_on_hit", "spell_discount"}
        for cid, c in GAME_DATA["classes"].items():
            with self.subTest(cls=c["role"]):
                m = c["mastery"]["6"]
                self.assertEqual(m["type"], "magic")
                self.assertLessEqual(set(m["bonus"]), keys)
                for v in m["bonus"].values(): self.assertIn(str(v), m["desc"])

    def test_the_sixth_level_counts_only_for_its_class_once_reached(self):
        PROFILE_MANAGER._data["class_lvl"] = {"3": 5}
        base = self.hero("3")
        PROFILE_MANAGER._data["class_lvl"] = {"3": 6}
        mage, warrior = self.hero("3"), self.hero("1")
        bonus = GAME_DATA["classes"]["3"]["mastery"]["6"]["bonus"]
        self.assertEqual(mage.max_ether() - base.max_ether(), bonus.get("ether_max", 0))
        self.assertEqual(mage.magic_value("spell_pct") - base.magic_value("spell_pct"), bonus.get("spell_pct", 0))
        self.assertEqual(warrior.mastery_magic, {}, "la Maestria del Mago vale solo per il Mago")

    def test_mastery_climbs_to_the_sixth_level(self):
        p = self.hero("3")
        PROFILE_MANAGER._data.setdefault("class_xp", {})["3"] = GAME_DATA["meta"]["mastery_xp_requirements"]["6"]
        PROFILE_MANAGER._data.setdefault("class_lvl", {})["3"] = 5
        with quiet(): roguelike._update_class_mastery(p, 1)
        self.assertEqual(PROFILE_MANAGER.get_class_lvl("3", 1), 6)


class MagicValueTest(Sandbox):
    def test_every_source_adds_up(self):
        p = self.hero()
        p.talents = ["mente_affilata"]
        p.weapon.sockets, p.weapon.runes = 1, ["sapienza"]
        p.mastery_magic = {"spell_pct": 7}
        expected = (GAME_DATA["talents"]["talents"]["mente_affilata"]["effects"]["spell_pct"]
                    + GAME_DATA["runes"]["runes"]["sapienza"]["effects"]["spell_pct"] + 7)
        self.assertEqual(p.magic_value("spell_pct"), expected)

    def test_the_hero_starts_with_full_ether_even_with_a_relic_that_raises_it(self):
        PROFILE_MANAGER._data.setdefault("perks", {})["altare_benedizione"] = True
        relic = next(r for r in RAW_DATA["relics"] if r["id"] == "cristallo_etere")
        with quiet(), mock.patch("entities.get_random_relic", return_value=relic):
            p = Player("3", "base", [])
        self.assertIn("cristallo_etere", p.relic_ids)
        self.assertEqual(p.ether, p.max_ether())


if __name__ == "__main__":
    unittest.main()
