"""Intenti dei nemici e reazioni elementali: regole delle mosse, marchi, combinazioni, prompt del combattimento."""
import copy
import io
import random
import re
import unittest
from collections import Counter
from contextlib import redirect_stdout
from unittest import mock

import codex
from data_manager import GAME_DATA, PROFILE_MANAGER
from entities import Armor, Enemy, Player, Weapon
from rooms import CombatSession, reaction_key

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def quiet():
    return redirect_stdout(io.StringIO())


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        PROFILE_MANAGER._data["codex"] = {"enemies": {}, "letters": [], "relics": [], "reactions": []}
        random.seed(2)

    def tearDown(self):
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)

    def fight(self, weapon="Acqua", armor="Vento", boss=False):
        with quiet():
            p = Player("1", "base", [])
        p.max_hp = p.hp = 1000
        p.weapon = Weapon("Lama", 10, 30, weapon, 1)
        p.armor = Armor("Corazza", 10, 0, armor, 1)
        with quiet():
            s = CombatSession(p, 5, Enemy(5, boss, []))
        s.enemy.hp = s.enemy.max_hp = 5000
        s.enemy.element, s.enemy.base_dodge, s.enemy.base_acc = "Normale", 0, 100
        return p, s

    def hit(self, s):
        with quiet(), mock.patch("rooms.random.randint", side_effect=lambda a, b: a):
            s.execute_player_attack()

    def enemy(self, s, intent="attack"):
        s.intent = intent
        with quiet(), mock.patch("rooms.random.randint", side_effect=lambda a, b: a), mock.patch("rooms.wait_enter"):
            s.enemy_turn()


class MoveChoiceTest(Sandbox):
    def test_defaults_and_overrides(self):
        moves = GAME_DATA["moves"]["defaults"]
        self.assertLessEqual(set(moves["boss"]), set(Enemy(1, True, []).moves))
        vampire = GAME_DATA["enemies"]["Vampiro Minore"]
        with mock.patch("entities.pick_enemy_name", return_value="Vampiro Minore"):
            self.assertEqual(Enemy(5, False, []).moves, vampire["moves"])
        with mock.patch("entities.pick_enemy_name", return_value="Melma Acida"):
            self.assertIn("venom", Enemy(5, False, []).moves)
        with mock.patch("entities.pick_enemy_name", return_value="Goblin"):
            self.assertEqual(Enemy(5, False, []).moves, moves["enemy"])

    def test_rules_of_the_moves(self):
        boss = Enemy(5, True, [])
        boss.status_inflict = None
        counts = Counter()
        last = None
        for _ in range(3000):
            move = boss.choose_move()
            counts[move] += 1
            if last in ("heavy", "guard"): self.assertNotEqual(move, last, "niente colpo pesante o guardia due volte di fila")
            last = move
        self.assertEqual(counts["heal"], 0, "a vita piena non si cura")
        self.assertEqual(counts["venom"], 0, "senza status niente colpo infetto")
        boss.hp = boss.max_hp // 2
        self.assertIn("heal", {boss.choose_move() for _ in range(300)})
        boss.heals_used = GAME_DATA["moves"]["rules"]["max_heals"]
        self.assertNotIn("heal", {boss.choose_move() for _ in range(300)})

    def test_prompt_shows_intent_and_conditions(self):
        p, s = self.fight()
        s.enemy.mark = ["Acqua", 2]
        s.enemy.statuses = {"blind": 2}
        prompts = []
        with quiet(), mock.patch("rooms.interactive_menu", side_effect=lambda o, pr="": prompts.append(pr) or 4), \
             mock.patch("rooms.clear_screen"), mock.patch("inventory_menu.show_player_stats", side_effect=KeyError):
            with self.assertRaises(KeyError): s.player_turn()
        text = ANSI.sub("", prompts[0])
        self.assertIn("Intento del nemico:", text)
        self.assertIn(f"{s.enemy.hp}/{s.enemy.max_hp} HP", text)
        self.assertIn("marchio 💧 Acqua", text)
        self.assertIn("Accecato", text)

    def test_stunned_enemy_announces_it(self):
        p, s = self.fight()
        s.enemy.statuses = {"stun": 1}
        s.choose_intent()
        self.assertIn("Congelato", ANSI.sub("", s.intent_text()))


class ReactionTest(Sandbox):
    def test_weapon_marks_and_defending_armor_reacts(self):
        p, s = self.fight("Acqua", "Vento")
        self.hit(s)
        self.assertEqual(s.enemy.mark, ["Acqua", 2])
        s.is_defending = True
        self.enemy(s)  # in guardia l'armatura di Vento colpisce il marchio d'Acqua: Gelo
        self.assertIsNone(s.enemy.mark)
        self.assertEqual(s.enemy.statuses.get("stun"), 1)
        self.assertEqual(PROFILE_MANAGER.codex["reactions"], ["Acqua+Vento"])
        before = p.hp
        s.is_defending = False
        self.enemy(s, "heavy")
        self.assertEqual(p.hp, before, "congelato, perde il turno: anche il colpo pesante")

    def test_armor_mark_then_weapon_reacts(self):
        p, s = self.fight("Fuoco", "Vento")
        s.is_defending = True
        self.enemy(s)
        self.assertEqual(s.enemy.mark, ["Vento", 1])  # marchiato e già passato un turno del nemico
        hp = s.enemy.hp
        self.hit(s)
        bonus = p.get_total_atk() * GAME_DATA["elements"]["reactions"]["Fuoco+Vento"]["bonus_pct"] // 100
        self.assertGreaterEqual(hp - s.enemy.hp, bonus)
        self.assertIsNone(s.enemy.mark)

    def test_armor_marks_only_while_defending(self):
        p, s = self.fight("Acqua", "Vento")
        self.enemy(s)
        self.assertIsNone(s.enemy.mark)

    def test_same_element_refreshes_and_resonance_never_reacts(self):
        p, s = self.fight("Fuoco", "Fuoco")
        self.hit(s)
        s.is_defending = True
        self.enemy(s)
        self.assertEqual(s.enemy.mark, ["Fuoco", 1])
        self.assertEqual(s.enemy.statuses, {})

    def test_elements_without_a_reaction_replace_the_mark(self):
        self.assertIsNone(reaction_key("Luce", "Acqua"))
        p, s = self.fight("Luce", "Acqua")
        self.hit(s)
        s.is_defending = True
        self.enemy(s)
        self.assertEqual(s.enemy.mark, ["Acqua", 1])

    def test_marks_fade_after_two_enemy_turns(self):
        p, s = self.fight("Acqua", "Normale")
        self.hit(s)
        self.enemy(s)
        self.assertEqual(s.enemy.mark, ["Acqua", 1])
        self.enemy(s)
        self.assertIsNone(s.enemy.mark)

    def test_normal_element_never_marks(self):
        p, s = self.fight("Normale", "Normale")
        self.hit(s)
        self.assertIsNone(s.enemy.mark)

    def test_codex_shows_discovered_reactions(self):
        text = "\n".join(ANSI.sub("", l) for l in codex.reactions_page())
        self.assertNotIn("Vapore", text)
        codex.record_reaction("Fuoco+Acqua")
        text = "\n".join(ANSI.sub("", l) for l in codex.reactions_page())
        self.assertIn("Vapore", text)
        self.assertIn("Reazioni elementali", [name for name, _, _ in codex.sections()])


if __name__ == "__main__":
    unittest.main()
