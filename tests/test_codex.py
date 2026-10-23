"""Il Codice del Labirinto e i personaggi ricorrenti: registrazione, pagine, archi narrativi fra le run."""
import copy
import io
import random
import re
import unittest
from contextlib import redirect_stdout
from unittest import mock

import codex
import events
import roguelike
from data_manager import GAME_DATA, PROFILE_MANAGER, RAW_DATA
from entities import Enemy, Player, pick_enemy_name
from rooms import CombatSession

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def quiet():
    return redirect_stdout(io.StringIO())


def plain(lines):
    return [ANSI.sub("", l) for l in lines]


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        PROFILE_MANAGER._data["story"] = {"flags": {}, "counters": {}, "seen_events": {}}
        PROFILE_MANAGER._data["codex"] = {"enemies": {}, "letters": [], "relics": [], "reactions": []}
        self._save = mock.patch.object(PROFILE_MANAGER, "save")
        self._save.start()
        random.seed(3)

    def tearDown(self):
        self._save.stop()
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)

    def hero(self, cls="1"):
        with quiet():
            p = Player(cls, "base", [])
        p.max_hp = p.hp = 400
        return p


class RecordingTest(Sandbox):
    def test_combat_records_seen_and_killed_with_the_base_name(self):
        p = self.hero()
        enemy = Enemy(5, False, [], modifier="hard")
        self.assertIn("(Potenziato)", enemy.name)
        with quiet(), mock.patch("rooms.random.random", return_value=0.99), mock.patch("rooms.interactive_menu", return_value=0), \
             mock.patch("rooms.wait_enter"), mock.patch("rooms.delay_print"), mock.patch("rooms.clear_screen"):
            session = CombatSession(p, 5, enemy)
            session.start()
        rec = PROFILE_MANAGER.codex["enemies"][enemy.base_name]
        self.assertEqual(rec["seen"], 1)
        self.assertLessEqual(enemy.hp, 0)
        self.assertEqual(rec["killed"], 1)

    def test_letters_found_on_the_walls_are_recorded(self):
        p = self.hero()
        with quiet(), mock.patch("rooms.random.random", return_value=0.0), mock.patch("rooms.random.randrange", return_value=3), \
             mock.patch.object(CombatSession, "_combat_loop"), mock.patch("rooms.delay_print"):
            CombatSession(p, 1, Enemy(1, False, [])).start()
        self.assertEqual(PROFILE_MANAGER.codex["letters"], [3])

    def test_relics_obtained_are_recorded_once(self):
        p = self.hero()
        relic = next(r for r in RAW_DATA["relics"] if r["id"] == "tasca_dorata")
        with quiet(): p.add_relic(relic)
        codex.record_relic("tasca_dorata")
        self.assertEqual(PROFILE_MANAGER.codex["relics"], ["tasca_dorata"])


class PagesTest(Sandbox):
    def test_unknown_entries_are_hidden(self):
        for page in codex.PAGES.values():
            lines = plain(page())
            self.assertTrue(any("???" in l for l in lines))
        self.assertEqual(codex.completion(), 0)

    def test_bestiary_reveals_lore_only_after_a_kill(self):
        codex.record_enemy_seen("Goblin")
        lines = plain(codex.bestiary_page())
        self.assertTrue(any(l.strip().startswith("Goblin") and "incontri 1 · sconfitti 0" in l for l in lines))
        self.assertNotIn("  " + RAW_DATA["enemies"]["Goblin"]["lore"], "\n".join(lines))
        codex.record_enemy_killed("Goblin")
        self.assertIn(RAW_DATA["enemies"]["Goblin"]["lore"], "\n".join(plain(codex.bestiary_page())))

    def test_letters_events_and_relics_pages(self):
        codex.record_letter(0)
        self.assertIn(GAME_DATA["lore"]["letters"][0], "\n".join(codex.letters_page()))
        PROFILE_MANAGER.story["seen_events"]["pozzo_desideri"] = 2
        self.assertIn("Il Pozzo dei Desideri  (visto 2 volte)", "\n".join(plain(codex.events_page())))
        codex.record_relic("tasca_dorata")
        self.assertIn("Tasca Dorata", "\n".join(plain(codex.relics_page())))

    def test_completion_counts_every_section(self):
        total = sum(t for _, _, t in codex.sections())
        codex.record_relic("tasca_dorata")
        codex.record_letter(0)
        codex.record_reaction("Fuoco+Acqua")
        self.assertEqual([s[1] for s in codex.sections()], [0, 0, 0, 1, 1, 0, 0, 0, 0, 1])
        self.assertEqual(codex.completion(), 3 * 100 // total)

    def test_characters_page_follows_the_arc(self):
        text = "\n".join(plain(codex.characters_page()))
        self.assertIn("??? — " + GAME_DATA["story"]["characters"]["alaric"]["hint"], text)
        PROFILE_MANAGER.add_counter("alaric")
        PROFILE_MANAGER.set_flag("alaric_lavanda")
        text = "\n".join(plain(codex.characters_page()))
        chapters = GAME_DATA["story"]["characters"]["alaric"]["chapters"]
        self.assertIn("Sir Alaric, il Primo Paladino  (1/3)", text)
        self.assertIn(chapters[0]["text"], text)
        self.assertNotIn(chapters[1]["text"], text)
        self.assertIn("✦ Il fiore di lavanda", text)

    def test_codex_menu_opens_every_page(self):
        picks = list(range(len(codex.PAGES))) + [-1]
        with quiet(), mock.patch("codex.interactive_menu", side_effect=picks), mock.patch("codex.wait_enter"), mock.patch("codex.clear_screen"):
            codex.show_codex()

    def test_base_camp_has_the_codex(self):
        called = []
        with quiet(), mock.patch("roguelike.interactive_menu", side_effect=lambda o, p="", **k: 5 if not called else len(o) - 1), \
             mock.patch("roguelike.show_codex", side_effect=lambda: called.append(1)), mock.patch("roguelike.clear_screen"):
            roguelike.base_camp()
        self.assertEqual(called, [1])


class CharacterArcTest(Sandbox):
    def chapter_events(self, char_id):
        return [ch["event"] for ch in GAME_DATA["story"]["characters"][char_id]["chapters"]]

    def test_chapters_form_a_chain(self):
        for char_id, char in GAME_DATA["story"]["characters"].items():
            name = char["counter"]
            for k, ev_id in enumerate(self.chapter_events(char_id)):
                with self.subTest(character=char_id, chapter=k + 1):
                    ev = GAME_DATA["events"][ev_id]
                    req = ev["requires"]
                    self.assertEqual(req.get("counter", {}).get(name, 0), k)
                    self.assertEqual(req["counter_below"][name], k + 1)
                    if k: self.assertIn("not_run_flag", req, "un capitolo per run")
                    advancing = [eff for sc in ev["scenes"].values() for c in sc["choices"] for effs in (c.get("effects", []), c.get("success", []))
                                 for eff in effs if eff.get("counter") == name]
                    self.assertTrue(advancing, "il capitolo deve poter avanzare")
                    self.assertTrue(all(eff.get("add", 1) == 1 for eff in advancing))
                    self.assertIn("text", char["chapters"][k])
            for note in char.get("notes", []):
                written = {eff["flag"] for _, _, c in self.all_choices() for effs in (c.get("effects", []), c.get("success", [])) for eff in effs if "flag" in eff}
                self.assertIn(note["flag"], written)

    def all_choices(self):
        for ev_id, ev in GAME_DATA["events"].items():
            for sc_id, sc in ev["scenes"].items():
                for c in sc["choices"]: yield ev_id, sc_id, c

    def test_one_chapter_per_run_and_in_order(self):
        p = self.hero()
        self.assertTrue(events.is_available("alaric_porta", 5, p))
        self.assertFalse(events.is_available("alaric_stanco", 10, p))
        with quiet(), mock.patch("events.interactive_menu", side_effect=[0, 0]), mock.patch("events.wait_enter"), \
             mock.patch("events.clear_screen"), mock.patch("events.delay_print"):
            events.event_room(p, "alaric_porta", 5)
        self.assertEqual(PROFILE_MANAGER.get_counter("alaric"), 1)
        self.assertFalse(events.is_available("alaric_porta", 5, p))
        self.assertFalse(events.is_available("alaric_stanco", 10, p))  # già un capitolo in questa run
        self.assertTrue(events.is_available("alaric_stanco", 10, self.hero()))  # run successiva

    def test_freeing_alaric_retires_the_dark_knight(self):
        floors = range(1, 31)
        self.assertIn("Cavaliere Oscuro", {pick_enemy_name(f, True) for f in floors for _ in range(30)})
        PROFILE_MANAGER.set_flag("alaric_liberato")
        self.assertNotIn("Cavaliere Oscuro", {pick_enemy_name(f, True) for f in floors for _ in range(30)})

    def test_retired_bosses_point_to_a_real_flag(self):
        written = {eff["flag"] for _, _, c in self.all_choices() for effs in (c.get("effects", []), c.get("success", [])) for eff in effs if "flag" in eff}
        for name, boss in RAW_DATA["bosses"].items():
            if "retired_by_flag" in boss: self.assertIn(boss["retired_by_flag"], written, name)

    def test_lavender_letter_leads_to_the_flower(self):
        self.assertTrue(any("lavanda" in l for l in GAME_DATA["lore"]["letters"]))
        p = self.hero()
        with quiet(), mock.patch("events.interactive_menu", side_effect=[0]), mock.patch("events.wait_enter"), \
             mock.patch("events.clear_screen"), mock.patch("events.delay_print"):
            events.event_room(p, "giardino_sepolto", 3)
        self.assertIn("fiore_lavanda", p.quest_items)


if __name__ == "__main__":
    unittest.main()
