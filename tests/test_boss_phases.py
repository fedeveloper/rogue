"""Boss con fasi: a ogni soglia di HP il boss cambia regole e mosse, lo annuncia e lo registra nel Codice.

Ogni effetto di fase ha un contratto; i dati sono controllati per intero (ogni boss ha almeno una fase).
"""
import copy
import io
import random
import re
import unittest
from contextlib import redirect_stdout
from unittest import mock

import codex
from data_manager import GAME_DATA, MULTIPLIERS, PROFILE_MANAGER, RAW_DATA
from entities import STATUS_NAMES, Armor, Enemy, Player
from rooms import CombatSession
from rooms_patch import patch_rooms

ANSI = re.compile(r"\x1b\[[0-9;]*m")
PHASES = GAME_DATA["phases"]
EFFECT_KEYS = {"at_pct", "name", "text", "element", "atk_mult", "heal_pct", "shield_pct", "ward", "status_inflict", "moves"}


def quiet():
    return redirect_stdout(io.StringIO())


def plain(text):
    return ANSI.sub("", text)


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

    def fight(self, boss, phases=None):
        """Uno scontro con `boss`; `phases` sostituisce le sue fasi (per provare un effetto alla volta)."""
        with quiet():
            p = Player("1", "base", [])
            enemy = Enemy(10, True, [])
        enemy.name = enemy.base_name = boss
        enemy.phases = phases if phases is not None else sorted(PHASES[boss], key=lambda ph: -ph["at_pct"])
        enemy.hp = enemy.max_hp = 1000
        p.max_hp = p.hp = 1000
        s = CombatSession(p, 10, enemy)
        return p, s

    def cross(self, s, pct):
        s.enemy.hp = s.enemy.max_hp * pct // 100
        with quiet(): return s.check_phase()


class PhaseDataTest(unittest.TestCase):
    def test_every_boss_has_phases_and_valid_data(self):
        self.assertEqual(set(PHASES), set(RAW_DATA["bosses"]))
        moves, elements = set(GAME_DATA["moves"]["moves"]), set(GAME_DATA["elements"]["list"])
        for boss, phases in PHASES.items():
            pcts = [ph["at_pct"] for ph in phases]
            with self.subTest(boss=boss):
                self.assertEqual(pcts, sorted(pcts, reverse=True))
                for ph in phases:
                    self.assertLessEqual(set(ph), EFFECT_KEYS)
                    self.assertTrue(0 < ph["at_pct"] < 100)
                    self.assertTrue(ph["name"] and ph["text"])
                    self.assertGreater(len(set(ph) - {"at_pct", "name", "text"}), 0, "una fase cambia almeno una cosa")
                    if "element" in ph: self.assertIn(ph["element"], elements | {"counter"})
                    if "moves" in ph:
                        self.assertLessEqual(set(ph["moves"]), moves - {"unleash"}, "il Colpo caricato arriva solo dopo la Carica")
                        self.assertIn("attack", ph["moves"])
                    if "status_inflict" in ph: self.assertIn(ph["status_inflict"]["type"], STATUS_NAMES)
                    if "ward" in ph: self.assertTrue(0 < ph["ward"] < 1)

    def test_the_final_boss_has_more_phases(self):
        final = next(n for n, d in RAW_DATA["bosses"].items() if d.get("final_boss"))
        self.assertGreater(len(PHASES[final]), 1)


class PhaseEffectContractTest(Sandbox):
    BOSS = "Re dei Goblin"

    def one(self, **effects):
        ph = {"at_pct": 50, "name": "Prova", "text": "Cambia.", **effects}
        p, s = self.fight(self.BOSS, [ph])
        return p, s

    def test_the_phase_starts_at_its_threshold_once(self):
        p, s = self.one(atk_mult=2.0)
        atk = s.enemy.atk
        self.assertFalse(self.cross(s, 51))
        self.assertTrue(self.cross(s, 50))
        self.assertEqual((s.enemy.phase, s.enemy.atk), (1, atk * 2))
        self.assertFalse(self.cross(s, 10), "ogni fase scatta una volta sola")
        self.assertEqual(s.enemy.atk, atk * 2)

    def test_element(self):
        p, s = self.one(element="Fuoco")
        s.enemy.mark = ["Acqua", 2]
        self.cross(s, 50)
        self.assertEqual((s.enemy.element, s.enemy.mark), ("Fuoco", None))

    def test_counter_element_beats_your_armor(self):
        for armor in ("Fuoco", "Acqua", "Terra", "Vento"):
            p, s = self.one(element="counter")
            p.armor = Armor("Prova", 1, 1, armor, 1)
            self.cross(s, 50)
            best = max(MULTIPLIERS[el].get(armor, 1.0) for el in GAME_DATA["elements"]["list"])
            with self.subTest(armor=armor):
                self.assertEqual(MULTIPLIERS[s.enemy.element].get(armor, 1.0), best)
                self.assertGreater(best, 1.0)

    def test_heal(self):
        p, s = self.one(heal_pct=20)
        self.cross(s, 50)
        self.assertEqual(s.enemy.hp, 500 + 200)

    def test_shield_absorbs_attacks_until_broken(self):
        p, s = self.one(shield_pct=25)
        self.cross(s, 50)
        self.assertEqual(s.enemy.shield, 250)
        self.assertEqual(s._absorb(100, "")[0], 0)
        self.assertEqual(s.enemy.shield, 150)
        dmg, eff = s._absorb(200, "")
        self.assertEqual((dmg, s.enemy.shield), (50, 0))
        self.assertIn("infranto", plain(eff))

    def test_ward_halves_attacks_until_a_reaction(self):
        p, s = self.one(ward=0.5)
        self.cross(s, 50)
        self.assertEqual(s._absorb(100, "")[0], 50)
        self.assertIn("scaglie", s.enemy_status_text())
        with quiet(): s._trigger_reaction(next(iter(GAME_DATA["elements"]["reactions"])))
        self.assertIsNone(s.enemy.ward)
        self.assertEqual(s._absorb(100, "")[0], 100)

    def test_status(self):
        p, s = self.one(status_inflict={"type": "bleed", "chance": 50, "duration": 3})
        self.cross(s, 50)
        self.assertEqual(s.enemy.status_inflict, {"type": "bleed", "chance": 50, "duration": 3})

    def test_moves(self):
        p, s = self.one(moves={"attack": 1, "seal": 99})
        self.cross(s, 50)
        self.assertEqual(s.enemy.moves, {"attack": 1, "seal": 99})
        random.seed(1)
        picks = {s.enemy.choose_move() for _ in range(20)}
        self.assertIn("seal", picks)

    def test_the_announcement_lists_what_changed(self):
        p, s = self.one(atk_mult=1.25, ward=0.5, moves={"attack": 50, "drain": 50})
        s.enemy.hp = 500
        out = io.StringIO()
        with redirect_stdout(out): s.check_phase()
        text = plain(out.getvalue())
        for piece in ("PROVA", "Cambia.", "Attacco +25%", "50% dei danni", "Prosciugamento"):
            self.assertIn(piece, text)


class PhaseInCombatTest(Sandbox):
    def test_a_phase_change_after_your_turn_uses_the_boss_turn(self):
        p, s = self.fight("Cavaliere Oscuro")
        turns = iter([True, False])
        def your_turn():
            s.intent = "heavy"          # il boss aveva annunciato un colpo pesante...
            s.enemy.hp = 400            # ...ma il tuo attacco lo porta sotto la soglia
            return next(turns)
        with quiet(), mock.patch.object(s, "player_turn", side_effect=your_turn), patch_rooms("wait_enter"):
            s._combat_loop()
        self.assertEqual(p.hp, 1000, "il turno del boss serve a trasformarsi: niente colpo pesante")
        self.assertEqual(s.enemy.phase, 1)

    def test_the_codex_records_the_phases_seen(self):
        p, s = self.fight("DIO ANTICO")
        self.cross(s, 60)
        self.assertEqual(PROFILE_MANAGER.codex["enemies"]["DIO ANTICO"]["phases"], 1)
        text = "\n".join(plain(l) for l in codex.phases_page())
        self.assertIn(PHASES["DIO ANTICO"][0]["name"], text)
        self.assertNotIn(PHASES["DIO ANTICO"][1]["name"], text)
        self.cross(s, 20)
        self.assertEqual(PROFILE_MANAGER.codex["enemies"]["DIO ANTICO"]["phases"], 2)
        found = dict((n, f) for n, f, _ in codex.sections())["Fasi dei boss"]
        self.assertGreaterEqual(found, 2)

    def test_a_deep_blow_crosses_every_threshold_in_order(self):
        p, s = self.fight("DIO ANTICO")
        self.cross(s, 10)
        self.assertEqual(s.enemy.phase, 2)
        self.assertIsNotNone(s.enemy.ward)

    def test_a_killing_blow_skips_the_phase(self):
        p, s = self.fight("Re dei Goblin")
        s.enemy.hp = 0
        with quiet(): self.assertFalse(s.check_phase())
        self.assertEqual(s.enemy.phase, 0)

    def test_normal_enemies_have_no_phases(self):
        with quiet(): self.assertEqual(Enemy(10, False, []).phases, [])
        with quiet(): self.assertEqual(Enemy(10, False, [], modifier="elite").phases, [])

    def test_real_bosses_load_their_phases(self):
        for _ in range(30):
            with quiet(): boss = Enemy(random.randint(1, 30), True, [])
            self.assertEqual([ph["name"] for ph in boss.phases], [ph["name"] for ph in sorted(PHASES[boss.base_name], key=lambda ph: -ph["at_pct"])])


if __name__ == "__main__":
    unittest.main()
