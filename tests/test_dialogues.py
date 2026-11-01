"""I dialoghi del Campo (`data/dialogues.json`, `camp.py`): ogni argomento è scritto bene, si apre con il progresso e
in ordine, rispetta la Scala delle rivelazioni del canone, e parlare non cambia niente del gioco tranne i flag della
storia."""
import copy
import io
import re
import unittest
from contextlib import redirect_stdout
from unittest import mock

import camp
import events
from data_manager import GAME_DATA, PROFILE_MANAGER

CHARS = GAME_DATA["dialogues"]["characters"]
TOPIC_KEYS = {"id", "title", "after", "requires", "lines", "choices"}
CHOICE_KEYS = {"text", "reply", "flag"}
# Nomi del canone che il giocatore può sentire solo dopo un certo gradino (STORY.md, Scala delle rivelazioni)
LATE_NAMES = {"Sereth": None, "Ardel": {"won": True}}


def quiet():
    return redirect_stdout(io.StringIO())


def words(text: str) -> int:
    return len(text.split())


def all_requirements() -> list:
    return [t.get("requires", {}) for c in CHARS.values() for t in c["topics"]] + [c.get("requires", {}) for c in CHARS.values()]


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        self._save = mock.patch.object(PROFILE_MANAGER, "save")
        self._save.start()
        PROFILE_MANAGER._data["story"] = {"flags": {}, "counters": {}, "seen_events": {}}
        PROFILE_MANAGER._data["npc_unlocked"] = {}
        PROFILE_MANAGER._data["max_floor"], PROFILE_MANAGER._data["won_normal"] = 0, False
        PROFILE_MANAGER._data.setdefault("stats", {})["total_bosses"] = 0

    def tearDown(self):
        self._save.stop()
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)

    def everything(self):
        """Un profilo che ha fatto tutto: ogni flag e contatore nominato dai dialoghi, il piano 30, la vittoria."""
        for req in all_requirements():
            for f in [req.get("flag")] + req.get("flags", []) + req.get("any_flags", []):
                if f: PROFILE_MANAGER.set_flag(f)
            for k, n in req.get("counter", {}).items(): PROFILE_MANAGER.story["counters"][k] = n
            if req.get("npc"): PROFILE_MANAGER._data["npc_unlocked"][req["npc"]] = True
        for c in camp.camp()["characters"]:
            for k, n in c.get("requires", {}).get("counter", {}).items(): PROFILE_MANAGER.story["counters"][k] = max(n, PROFILE_MANAGER.get_counter(k))
        PROFILE_MANAGER._data["max_floor"], PROFILE_MANAGER._data["won_normal"] = 30, True
        PROFILE_MANAGER._data["stats"]["total_bosses"] = 99


class DataTest(Sandbox):
    def test_every_character_is_someone_at_the_camp(self):
        camp_ids = {c["id"] for c in camp.camp()["characters"]}
        for cid, c in CHARS.items():
            with self.subTest(character=cid):
                if cid not in camp_ids:
                    self.assertTrue(c.get("name") and c.get("requires") and c.get("lines"), "chi non è un personaggio del Campo ha nome, condizioni e saluto")
                self.assertGreaterEqual(len(c["topics"]), 6)
        for cid in ("silas", "cartografa", "speziale", "borek"):
            self.assertGreaterEqual(len(CHARS[cid]["topics"]), 10, f"{cid}: il canone prevede un arco lungo")

    def test_topics_are_well_formed(self):
        for cid, c in CHARS.items():
            seen = []
            for t in c["topics"]:
                with self.subTest(character=cid, topic=t["id"]):
                    self.assertLessEqual(set(t), TOPIC_KEYS)
                    self.assertNotIn(t["id"], seen, "id ripetuto")
                    if "after" in t: self.assertIn(t["after"], seen, "after nomina un argomento che viene prima")
                    self.assertLessEqual(set(t.get("requires", {})), events.PROFILE_CONDITIONS, "al Campo non c'è un eroe: solo condizioni del profilo")
                    self.assertTrue(t["title"] and t["lines"])
                    for choice in t.get("choices", []):
                        self.assertLessEqual(set(choice), CHOICE_KEYS, "una risposta lascia solo un flag della storia, nessun effetto di gioco")
                        self.assertTrue(choice["text"] and choice["reply"])
                    seen.append(t["id"])

    def test_lengths_follow_the_writing_guide(self):
        """STORY.md, Parte I: una conversazione al Campo è di 80-250 parole, divisa in battute."""
        for cid, c in CHARS.items():
            for t in c["topics"]:
                with self.subTest(character=cid, topic=t["id"]):
                    total = sum(map(words, t["lines"])) + sum(words(ch["reply"]) for ch in t.get("choices", []))
                    self.assertTrue(70 <= total <= 260, f"{total} parole")
                    for line in t["lines"]: self.assertLessEqual(words(line), 120, "una battuta troppo lunga si spezza")

    def test_late_names_wait_for_their_step(self):
        for cid, c in CHARS.items():
            for t in c["topics"]:
                text = " ".join(t["lines"] + [ch["reply"] + ch["text"] for ch in t.get("choices", [])])
                for name, needs in LATE_NAMES.items():
                    if re.search(rf"\b{name}\b", text):
                        with self.subTest(character=cid, topic=t["id"], name=name):
                            self.assertIsNotNone(needs, f"{name} non si può ancora nominare")
                            self.assertLessEqual(needs.items(), t.get("requires", {}).items())


class UnlockTest(Sandbox):
    def test_every_topic_opens_for_someone_who_did_everything(self):
        self.everything()
        for cid, c in CHARS.items():
            with self.subTest(character=cid):
                # si legge un argomento alla volta, come al Campo, finché se ne aprono di nuovi
                while camp.unread(cid):
                    for t in camp.unread(cid): PROFILE_MANAGER.set_flag(camp.topic_flag(cid, t["id"]))
                self.assertEqual([t["id"] for t in camp.topics(cid)], [t["id"] for t in c["topics"]])

    def test_topics_open_with_progress_and_in_order(self):
        PROFILE_MANAGER.add_counter("silas", 2)
        first = [t["id"] for t in camp.topics("silas")]
        self.assertIn("fuoco_azzurro", first)
        self.assertNotIn("nerea", first, "Nerea viene dopo il diario e dopo il piano 6")
        PROFILE_MANAGER._data["max_floor"] = 6
        self.assertNotIn("nerea", [t["id"] for t in camp.topics("silas")])
        PROFILE_MANAGER.set_flag(camp.topic_flag("silas", "diario"))
        self.assertIn("nerea", [t["id"] for t in camp.topics("silas")])

    def test_craftsmen_sit_at_the_fire_once_freed(self):
        names = lambda: [c["name"] for c in camp.present_characters()]
        self.assertNotIn("Borek", names())
        PROFILE_MANAGER._data["npc_unlocked"]["borek"] = True
        self.assertIn("Borek", names())

    def test_new_conditions_read_the_profile(self):
        self.assertFalse(events.check(None, {"reached_floor": 10}, 0))
        PROFILE_MANAGER._data["max_floor"] = 10
        self.assertTrue(events.check(None, {"reached_floor": 10}, 0))
        self.assertFalse(events.check(None, {"bosses_total": 3}, 0))
        PROFILE_MANAGER._data["stats"]["total_bosses"] = 3
        self.assertTrue(events.check(None, {"bosses_total": 3}, 0))
        self.assertTrue(events.check(None, {"won": False}, 0))
        PROFILE_MANAGER._data["won_normal"] = True
        self.assertTrue(events.check(None, {"won": True}, 0))


class TalkTest(Sandbox):
    def test_reading_marks_the_topic_and_a_choice_leaves_only_its_flag(self):
        self.everything()
        PROFILE_MANAGER.set_flag("camp_dono_silas")  # il dono è già stato ricevuto: qui conta solo il dialogo
        silas = next(c for c in camp.present_characters() if c["id"] == "silas")
        topic = next(t for t in CHARS["silas"]["topics"] if t["id"] == "diario")
        idx = [t["id"] for t in camp.topics("silas")].index("diario")
        self.assertTrue(camp.news(silas))
        before = (PROFILE_MANAGER.essence, copy.deepcopy(PROFILE_MANAGER._data["perks"]), list(PROFILE_MANAGER.unlocked_ids))
        menus = iter([idx, 0, -1])  # l'argomento, la prima risposta, poi via
        with quiet(), mock.patch("camp.wait_enter"), mock.patch("camp.clear_screen"), mock.patch("camp.delay_print"), \
             mock.patch("camp.interactive_menu", side_effect=lambda *a, **k: next(menus)):
            camp.talk(silas)
        self.assertTrue(PROFILE_MANAGER.get_flag(camp.topic_flag("silas", "diario")))
        self.assertTrue(PROFILE_MANAGER.get_flag(topic["choices"][0]["flag"]))
        self.assertNotIn("diario", [t["id"] for t in camp.unread("silas")])
        self.assertEqual((PROFILE_MANAGER.essence, PROFILE_MANAGER._data["perks"], PROFILE_MANAGER.unlocked_ids), before,
                         "parlare non cambia Essenza, potenziamenti né sblocchi")

    def test_the_menu_marks_what_is_new(self):
        PROFILE_MANAGER._data["npc_unlocked"]["borek"] = True
        seen = []
        def menu(options, prompt="", **kw):
            seen.append(list(options)); return -1
        with quiet(), mock.patch("camp.clear_screen"), mock.patch("camp.interactive_menu", side_effect=menu):
            camp.show_camp_fire()
        self.assertTrue(any("Parla con Borek" in o and "✦" in o for o in seen[0]))


if __name__ == "__main__":
    unittest.main()
