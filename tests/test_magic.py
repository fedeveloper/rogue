"""La magia: dati e testi degli incantesimi, l'Etere (massimo, guadagni, piano superato), il lancio in combattimento,
ogni effetto, gli elementi (marchio, reazione, Super Efficace, Risonanza), il Codice e le schermate."""
import copy
import io
import random
import re
import unittest
from contextlib import redirect_stdout
from unittest import mock

import codex
import inventory_menu
import magic
from data_manager import GAME_DATA, MULTIPLIERS, PROFILE_MANAGER, RAW_DATA
from entities import Armor, Enemy, Player, Weapon
from rooms import CombatSession

ANSI = re.compile(r"\x1b\[[0-9;]*m")
SPELLS, RULES = GAME_DATA["spells"]["spells"], GAME_DATA["spells"]["rules"]
ARCANO = GAME_DATA["attributes"]["attributes"]["arcano"]["per_point"]


def quiet():
    return redirect_stdout(io.StringIO())


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        self._save = mock.patch.object(PROFILE_MANAGER, "save")
        self._save.start()
        PROFILE_MANAGER._data["codex"]["spells"] = []
        random.seed(6)

    def tearDown(self):
        self._save.stop()
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)

    def fight(self, spells=("dardo_fuoco",), weapon="Normale", armor="Normale", enemy_el="Normale", atk=100):
        """Un eroe senza attributi con gli incantesimi indicati e Etere in abbondanza, contro un nemico neutro e immobile."""
        with quiet(): p = Player("1", "base", [])
        for a in p.attributes: p.attributes[a] = 0
        p.spells, p.base_ether = list(spells), 100
        p.ether = 100
        p.max_hp, p.hp = 1000, 500
        p.weapon = Weapon("Lama", 1, atk, weapon, 1)
        p.armor = Armor("Corazza", 1, 0, armor, 1)
        with quiet(): s = CombatSession(p, 3, Enemy(3, False, [], name="Goblin"))
        s.enemy.hp = s.enemy.max_hp = 10 ** 6
        s.enemy.element, s.enemy.base_dodge, s.intent = enemy_el, 0, "attack"
        return p, s

    def cast(self, s, sid):
        with quiet(), mock.patch("rooms.wait_enter"): return s.cast_spell(sid)


class DataTest(Sandbox):
    def test_every_spell_is_complete_and_its_text_tells_the_numbers(self):
        for sid, sp in SPELLS.items():
            with self.subTest(spell=sid):
                self.assertTrue(sp["name"] and sp["icon"] and sp["desc"])
                self.assertIn(sp["element"], GAME_DATA["elements"]["list"])
                self.assertTrue(2 <= sp["cost"] <= 6)
                self.assertLessEqual(set(sp["effects"]), set(magic.SPELL_EFFECT_KEYS))
                for key in ("damage_pct", "heal_pct", "drain_pct", "detonate_pct", "def_pct", "weaken_pct"):
                    if key in sp["effects"]: self.assertIn(f"{sp['effects'][key]}%", sp["desc"])
                if "status" in sp["effects"]:
                    turns = sp["effects"]["status"]["duration"]
                    self.assertIn("prossimo turno" if turns == 1 else f"{turns} turni", sp["desc"])
                if sp["effects"].get("cleanse"): self.assertIn("Veleno e Sanguinamento", sp["desc"])
                if sp["effects"].get("escape"): self.assertIn("non dai boss", sp["desc"])
                if sp.get("outside"): self.assertTrue(set(sp["effects"]) <= {"heal_pct", "cleanse"}, "fuori dal combattimento solo cure")
                if sp.get("unlock_id"): self.assertGreater(sp["unlock_cost"], 0)
                if "damage_pct" in sp["effects"] and sp["element"] != "Normale": self.assertIn("marchio", sp["desc"])

    def test_every_class_has_ether_and_known_spells(self):
        used = set()
        for cid, c in RAW_DATA["classes"].items():
            with self.subTest(cls=c["role"]):
                self.assertGreater(c["ether"], 0)
                self.assertTrue(c["spells"])
                self.assertLessEqual(set(c["spells"]), set(SPELLS))
                for sid in c["spells"]: self.assertLessEqual(SPELLS[sid]["cost"], c["ether"], "deve poterlo lanciare a Etere pieno")
                for sid in c["spells"]: self.assertNotIn("unlock_id", SPELLS[sid], "gli incantesimi iniziali non vanno sbloccati")
                used |= set(c["spells"])
        # gli altri si trovano in pergamena (subito, o dopo lo sblocco alla Forgia)
        self.assertTrue(set(SPELLS) - used)
        self.assertTrue(all(len(c["spells"]) <= RULES["slots"] for c in RAW_DATA["classes"].values()))
        mage = RAW_DATA["classes"]["3"]
        self.assertEqual(max(c["ether"] for c in RAW_DATA["classes"].values()), mage["ether"], "il Mago ha più Etere di tutti")

    def test_the_rules_text_tells_the_numbers(self):
        g, d = RULES["gain"], RULES["desc"]
        self.assertIn(f"+{g['hit']} a ogni colpo", d)
        self.assertIn(f"+{g['defend']} quando ti difendi", d)
        self.assertIn(f"+{g['reaction']} a ogni reazione", d)
        self.assertIn(f"{g['floor_pct']}% del massimo", d)
        self.assertIn(f"costa {RULES['resonance_discount']} Etere in meno", d)
        for key in ("ether_max", "spell_pct"): self.assertIn(f"+{ARCANO[key]}", GAME_DATA["attributes"]["attributes"]["arcano"]["desc"])


class EtherTest(Sandbox):
    def test_the_hero_starts_full_and_arcane_raises_the_maximum(self):
        for cid, c in RAW_DATA["classes"].items():
            with self.subTest(cls=c["role"]), quiet():
                p = Player(cid, "base", [])
            arc = c["attributes"].get("arcano", 0)
            self.assertEqual((p.ether, p.max_ether(), p.spells), (c["ether"] + arc * ARCANO["ether_max"],) * 2 + (c["spells"],))

    def test_ether_is_earned_by_acting(self):
        p, s = self.fight(); p.ether = 0; p.base_acc = 1000
        with quiet(), mock.patch("rooms.random.randint", return_value=1): s.execute_player_attack()
        self.assertEqual(p.ether, RULES["gain"]["hit"])
        s.def_type, s.def_txt = p.get_defense_action()
        with quiet(): s.execute_player_defense()
        self.assertEqual(p.ether, RULES["gain"]["hit"] + RULES["gain"]["defend"])
        with quiet(): s._trigger_reaction("Fuoco+Vento")
        self.assertEqual(p.ether, RULES["gain"]["hit"] + RULES["gain"]["defend"] + RULES["gain"]["reaction"])
        p.ether = p.max_ether()
        self.assertEqual(p.gain_ether(5), 0, "mai oltre il massimo")


class CastTest(Sandbox):
    def test_damage_is_a_share_of_atk_and_leaves_the_mark(self):
        p, s = self.fight(("dardo_fuoco",))
        self.assertTrue(self.cast(s, "dardo_fuoco"))
        self.assertEqual(10 ** 6 - s.enemy.hp, 100 * SPELLS["dardo_fuoco"]["effects"]["damage_pct"] // 100)
        self.assertEqual(s.enemy.mark[0], "Fuoco")
        self.assertEqual(p.ether, 100 - SPELLS["dardo_fuoco"]["cost"])
        self.assertIn("dardo_fuoco", PROFILE_MANAGER._data["codex"]["spells"])

    def test_the_enemy_element_and_arcane_count(self):
        weak = next(e for e, m in MULTIPLIERS["Fuoco"].items() if m > 1)
        p, s = self.fight(("dardo_fuoco",), enemy_el=weak)
        self.cast(s, "dardo_fuoco")
        self.assertEqual(10 ** 6 - s.enemy.hp, int(100 * MULTIPLIERS["Fuoco"][weak]))
        p, s = self.fight(("dardo_fuoco",)); p.attributes["arcano"] = 2
        self.cast(s, "dardo_fuoco")
        self.assertEqual(10 ** 6 - s.enemy.hp, 100 * (100 + 2 * ARCANO["spell_pct"]) // 100)

    def test_a_spell_completes_the_reaction_of_the_weapon(self):
        p, s = self.fight(("lama_acqua",))
        s.enemy.mark = ["Fuoco", 2]
        self.cast(s, "lama_acqua")
        self.assertEqual(p.run_tracker.get("reactions"), 1)
        self.assertIn("Fuoco+Acqua", PROFILE_MANAGER._data["codex"]["reactions"])

    def test_guard_shield_and_dispel(self):
        p, s = self.fight(("dardo_fuoco", "dissolvi")); s.intent = "guard"
        self.cast(s, "dardo_fuoco")
        self.assertEqual(10 ** 6 - s.enemy.hp, 100 // 2, "la Guardia dimezza anche la magia")
        p, s = self.fight(("dissolvi",)); s.enemy.shield, s.enemy.ward = 500, 0.5
        self.cast(s, "dissolvi")
        self.assertEqual((s.enemy.shield, s.enemy.ward), (0, None))
        self.assertEqual(10 ** 6 - s.enemy.hp, 100 * SPELLS["dissolvi"]["effects"]["damage_pct"] // 100, "dopo la dissoluzione colpisce pieno")

    def test_heal_drain_status_and_detonation(self):
        p, s = self.fight(("luce_guaritrice",))
        self.cast(s, "luce_guaritrice")
        self.assertEqual(p.hp, 500 + 1000 * SPELLS["luce_guaritrice"]["effects"]["heal_pct"] // 100)
        p, s = self.fight(("sifone_ombra",))
        self.cast(s, "sifone_ombra")
        dealt = 10 ** 6 - s.enemy.hp
        self.assertEqual(p.hp, 500 + dealt * SPELLS["sifone_ombra"]["effects"]["drain_pct"] // 100)
        p, s = self.fight(("frana",))
        self.cast(s, "frana")
        self.assertEqual(s.enemy.statuses["slow"], SPELLS["frana"]["effects"]["status"]["duration"])
        for mark, pct in ((["Vento", 2], "detonate_pct"), (None, "damage_pct")):
            p, s = self.fight(("detonazione",)); s.enemy.mark = mark
            self.cast(s, "detonazione")
            self.assertEqual(10 ** 6 - s.enemy.hp, 100 * SPELLS["detonazione"]["effects"][pct] // 100)
            self.assertIsNone(s.enemy.mark)

    def test_resonance_makes_spells_cheaper(self):
        p, s = self.fight(("sifone_ombra",), weapon="Tenebra", armor="Tenebra")
        self.assertEqual(magic.cost(p, "sifone_ombra"), SPELLS["sifone_ombra"]["cost"] - RULES["resonance_discount"])
        self.assertIn("Risonanza", magic.label(p, "sifone_ombra"))
        p, s = self.fight(("sifone_ombra",))
        self.assertEqual(magic.cost(p, "sifone_ombra"), SPELLS["sifone_ombra"]["cost"])

    def test_the_spell_can_finish_the_enemy(self):
        p, s = self.fight(("dardo_fuoco",)); s.enemy.hp = 1
        self.assertFalse(self.cast(s, "dardo_fuoco"))


class MenuTest(Sandbox):
    def turn(self, s, picks):
        it = iter(picks)
        with quiet(), mock.patch("rooms.interactive_menu", side_effect=lambda o, pr="": next(it)), mock.patch("rooms.clear_screen"), \
             mock.patch("rooms.wait_enter"):
            return s.player_turn()

    def test_the_spell_is_the_third_action_and_back_costs_nothing(self):
        p, s = self.fight(("dardo_fuoco",))
        prompts = []
        with quiet(), mock.patch("rooms.interactive_menu", side_effect=lambda o, pr="": prompts.append(o) or [2, 1, 0][len(prompts) - 1]), \
             mock.patch("rooms.clear_screen"), mock.patch("rooms.random.randint", return_value=1):
            s.player_turn()
        self.assertTrue(prompts[0][2].startswith("Lancia un incantesimo"))
        self.assertEqual(prompts[1][-1], "Indietro")
        self.assertEqual(p.ether, 100, "tornare indietro non costa Etere né turno")

    def test_without_ether_the_spell_does_not_start(self):
        p, s = self.fight(("dardo_fuoco",)); p.ether = 1
        self.assertIn("Etere insufficiente", magic.label(p, "dardo_fuoco"))
        p.base_acc = 1000
        with quiet(), mock.patch("rooms.random.randint", return_value=1):
            self.turn(s, [2, 0, 0])  # Incantesimi, l'incantesimo che costa troppo (rifiutato), poi Attacca
        self.assertNotIn("dardo_fuoco", PROFILE_MANAGER._data["codex"]["spells"], "l'incantesimo non parte")
        self.assertEqual(p.ether, 1 + RULES["gain"]["hit"], "il turno va all'attacco, che a segno dà Etere")

    def test_a_hero_without_spells_has_no_spell_action(self):
        p, s = self.fight(()); options = []
        with quiet(), mock.patch("rooms.interactive_menu", side_effect=lambda o, pr="": options.append(o) or 0), mock.patch("rooms.clear_screen"), \
             mock.patch("rooms.random.randint", return_value=1):
            s.player_turn()
        self.assertFalse(any(o.startswith("Lancia") for o in options[0]))


class ScreenTest(Sandbox):
    def test_stats_and_codex(self):
        p, s = self.fight(("dardo_fuoco", "lama_acqua"))
        out = io.StringIO()
        with redirect_stdout(out), mock.patch("inventory_menu.clear_screen"), mock.patch("inventory_menu.wait_enter"):
            inventory_menu.show_player_stats(p)
        self.assertIn("Etere: 100/100", ANSI.sub("", out.getvalue()))
        self.assertIn(SPELLS["lama_acqua"]["name"], ANSI.sub("", out.getvalue()))
        page = "\n".join(ANSI.sub("", l) for l in codex.spells_page())
        self.assertNotIn(SPELLS["dardo_fuoco"]["desc"], page)
        codex.record_spell("dardo_fuoco")
        page = "\n".join(ANSI.sub("", l) for l in codex.spells_page())
        self.assertIn(SPELLS["dardo_fuoco"]["desc"], page)


if __name__ == "__main__":
    unittest.main()
