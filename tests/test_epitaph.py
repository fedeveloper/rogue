"""L'Epitaffio e il Cimitero: la discesa annota i suoi momenti, la fine li racconta in poche frasi vere."""
import copy
import io
import re
import unittest
from contextlib import redirect_stdout
from unittest import mock

import codex
import epitaph
import roguelike
from data_manager import GAME_DATA, PROFILE_MANAGER, RAW_DATA
from entities import Enemy, Player
from rooms import CombatSession
from rooms_patch import patch_rooms

ANSI = re.compile(r"\x1b\[[0-9;]*m")
DATA = GAME_DATA["epitaph"]


def quiet():
    return redirect_stdout(io.StringIO())


def plain(text):
    return ANSI.sub("", text)


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        PROFILE_MANAGER._data.update(cemetery=[], nemeses=[], nemeses_fallen=[])
        self._save = mock.patch.object(PROFILE_MANAGER, "save")
        self._save.start()

    def tearDown(self):
        self._save.stop()
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)

    def hero(self):
        with quiet(): p = Player("3", "base", [])
        return p


class TemplateTest(unittest.TestCase):
    def test_every_fact_has_a_sentence(self):
        self.assertEqual(set(DATA["priority"]), set(DATA["middle"]))
        self.assertEqual(set(DATA["opening"]), {"death", "escape", "victory"})
        self.assertEqual(set(DATA["cause"]), {"nemesis", "boss", "enemy", "trap", "other"})


class ComposeTest(Sandbox):
    def test_a_death_opens_with_class_and_floor_and_ends_with_the_cause(self):
        p = self.hero(); p.hp = 0
        p.run_tracker["killer"] = {"name": "Goblin", "display": "Goblin", "is_boss": False}
        lines = epitaph.compose(p, 7)
        self.assertIn("Mago", lines[0]); self.assertIn("7", lines[0])
        self.assertEqual(lines[-1], DATA["cause"]["enemy"].format(killer="Goblin"))
        self.assertTrue(2 <= len(lines) <= 2 + DATA["max_middle"] + 1)

    def test_the_cause_of_death(self):
        cases = {"nemesis": {"name": "Goblin", "display": "Grugno il Fortunato", "is_boss": False, "nemesis_id": "x"},
                 "boss": {"name": "Re dei Goblin", "display": "Re dei Goblin", "is_boss": True}}
        for kind, killer in cases.items():
            p = self.hero(); p.hp = 0; p.run_tracker["killer"] = killer
            self.assertEqual(epitaph.compose(p, 5)[-1], DATA["cause"][kind].format(killer=killer["display"]))
        p = self.hero(); p.hp = 0; p.run_tracker["death_cause"] = "trap"
        self.assertEqual(epitaph.compose(p, 5)[-1], DATA["cause"]["trap"])
        p = self.hero(); p.hp = 0
        self.assertEqual(epitaph.compose(p, 5)[-1], DATA["cause"]["other"])

    def test_the_middle_follows_the_priority_and_the_limit(self):
        p = self.hero(); p.hp = 0; p.ascension = 4; p.corruption = 60
        for name in ("Re dei Goblin", "Cavaliere Oscuro"): epitaph.note(p, "boss", name=name)
        epitaph.note(p, "relic", name="Tasca Dorata"); epitaph.note(p, "event", title="Il Pozzo dei Desideri")
        lines = epitaph.compose(p, 9)
        middle = lines[1:-1]
        self.assertEqual(len(middle), DATA["max_middle"])
        self.assertEqual(middle[0], DATA["middle"]["ascension"].format(grade=4))
        self.assertEqual(middle[1], DATA["middle"]["bosses"].format(bosses=2, last_boss="Cavaliere Oscuro"))
        self.assertIn("Tasca Dorata", middle[2])

    def test_victory_and_escape_have_their_own_opening_and_no_cause(self):
        p = self.hero(); p.won = True
        epitaph.note(p, "ending", title="Il Nuovo Dio")
        lines = epitaph.compose(p, 31)
        self.assertIn(lines[0], [o.format(cls="Mago", floor=31, gold=p.gold) for o in DATA["opening"]["victory"]])
        self.assertEqual(lines[-1], DATA["ending"].format(ending="Il Nuovo Dio"))
        p = self.hero(); p.escaped = True
        self.assertIn(epitaph.compose(p, 4)[0], [o.format(cls="Mago", floor=4, gold=p.gold) for o in DATA["opening"]["escape"]])

    def test_the_same_story_gives_the_same_epitaph(self):
        a, b = self.hero(), self.hero()
        for p in (a, b): p.hp = 0; epitaph.note(p, "boss", name="Re dei Goblin")
        self.assertEqual(epitaph.compose(a, 6), epitaph.compose(b, 6))

    def test_a_new_nemesis_closes_the_story(self):
        p = self.hero(); p.hp = 0
        self.assertEqual(epitaph.compose(p, 6, born_nemesis="Grugno il Fortunato")[-1], DATA["born"].format(nemesis="Grugno il Fortunato"))


class ChronicleTest(Sandbox):
    def test_the_descent_takes_notes(self):
        p = self.hero()
        relic = next(r for r in RAW_DATA["relics"] if r["id"] == "tasca_dorata")
        with quiet(): p.add_relic(relic)
        with quiet(): s = CombatSession(p, 5, Enemy(5, True, []))
        with quiet(), patch_rooms("wait_enter"): s.on_enemy_death()
        kinds = [e["kind"] for e in p.chronicle]
        self.assertIn("relic", kinds)
        self.assertIn("boss", kinds)

    def test_the_end_of_a_run_shows_and_buries_the_epitaph(self):
        p = self.hero(); p.hp = 0
        out = io.StringIO()
        with redirect_stdout(out), mock.patch("roguelike.wait_enter"), mock.patch("roguelike.delay_print"):
            roguelike.evaluate_run(p, 6, False)
        [grave] = epitaph.cemetery()
        self.assertEqual((grave["class"], grave["floor"], grave["outcome"]), ("Mago", 6, "death"))
        self.assertIn(grave["epitaph"][0], plain(out.getvalue()))

    def test_the_cemetery_keeps_the_latest_and_shows_in_the_codex(self):
        for i in range(DATA["cemetery_size"] + 3):
            p = self.hero(); p.hp = 0
            epitaph.record(p, i + 1, [f"Riga {i}."])
        self.assertEqual(len(epitaph.cemetery()), DATA["cemetery_size"])
        page = "\n".join(plain(l) for l in codex.cemetery_page())
        self.assertIn(f"Riga {DATA['cemetery_size'] + 2}.", page)
        self.assertNotIn("Riga 0.", page)
        before = codex.completion()
        epitaph.record(self.hero(), 1, ["Altra."])
        self.assertEqual(codex.completion(), before, "il Cimitero non conta nel completamento")


if __name__ == "__main__":
    unittest.main()
