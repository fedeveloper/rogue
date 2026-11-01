"""La lore: il canone (`STORY.md`) parla di tutto ciò che il gioco nomina, e due testi narrativi non sono mai identici
(`tools/conta_testi.py`)."""
import importlib
import os
import sys
import unittest
from unittest import mock

import events
import texts

from data_manager import RAW_DATA

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
conta_testi = importlib.import_module("conta_testi")  # lo strumento sta in tools/, fuori dai pacchetti del gioco

with open(os.path.join(ROOT, "STORY.md"), encoding="utf-8") as f: CANON = f.read()


class CanonTest(unittest.TestCase):
    def assert_in_canon(self, names, what):
        missing = [n for n in names if n not in CANON]
        self.assertEqual(missing, [], f"{what} che il gioco nomina e il canone (STORY.md) non conosce")

    def test_the_canon_knows_every_character(self):
        story = RAW_DATA["story"]
        self.assert_in_canon([c["name"] for c in story["characters"].values()], "personaggi")
        self.assert_in_canon([n.replace("lo ", "").replace("Lo ", "") for n in story["npcs"].values()], "artigiani")
        camp = [c["name"] for c in story["camp"]["characters"] if c["id"] not in ("alaric", "erede")]  # Alaric come Luce; il posto vuoto
        self.assert_in_canon(camp, "personaggi del Campo")

    def test_the_canon_knows_every_place_boss_and_life(self):
        self.assert_in_canon([b["name"] for b in RAW_DATA["biomes"]], "biomi")
        self.assert_in_canon(list(RAW_DATA["bosses"]), "boss")
        self.assert_in_canon([c["role"] for c in RAW_DATA["classes"].values()], "classi")
        self.assert_in_canon([e["title"] for e in RAW_DATA["story"]["endings"]], "finali")

    def test_the_canon_has_the_writing_guide_and_the_ladder(self):
        for section in ("Come si scrive", "La verità", "La Scala delle rivelazioni", "Contraddizioni risolte"):
            self.assertIn(section, CANON)


# Gli eventi della v5: tutti gli altri sono stati scritti per la v6, e in partita i loro testi sono brevi
V5_EVENTS = {"alaric_porta", "alaric_sigillo", "alaric_stanco", "altare_sangue", "banchetto_morti",
              "biblioteca_cenere", "biblioteca_vuoto", "bilancia_aethelgard", "bisca_goblin", "borek_prigioniero",
              "buio_vivente", "cadavere_saggio", "carrello_abbandonato", "cartografa_perduta", "cartografa_ritorno",
              "cavaliere_caduto", "colata_oro", "coro_spento", "crogiolo_rune", "eco_del_tempo", "eco_madre",
              "elara_prigioniera", "fabbro_cielo", "fontana_fatata", "forgia_abissale", "forgiatore_incatenato",
              "galleria_gas", "giardino_appassito", "giardino_sepolto", "idolo_corrotto", "incudine_cosmica",
              "ingranaggio_fermo", "lavabo_ricordi", "mendicante_ombra", "minatore_cieco", "nido_sanguisughe",
              "nido_tempesta", "oasi_sotterranea", "occhio_chiuso", "osservatorio_vento", "ponte_sospeso",
              "porta_ritorno", "porta_sigillata", "pozzo_desideri", "prima_pietra", "sala_corridoi", "silas_fuoco",
              "silas_soglia", "silas_tracce", "specchio_verita", "speziale_prigioniero", "statua_sale",
              "valerius_prigioniero", "viandante_cieco", "voce_cara", "voce_labirinto", "voce_nel_buio",
              "volto_membrana"}


def v6_events() -> list:
    return sorted(set(RAW_DATA["events"]) - V5_EVENTS)


class InRunLengthTest(unittest.TestCase):
    def test_v6_events_follow_the_writing_guide(self):
        """STORY.md, Parte I: scena di un evento al massimo 55 parole, esito di una scelta al massimo 30."""
        for ev_id in v6_events():
            for sc_id, scene in RAW_DATA["events"][ev_id]["scenes"].items():
                with self.subTest(event=ev_id, scene=sc_id):
                    self.assertLessEqual(len(scene["text"].split()), 55)
                    for c in scene["choices"]: self.assertLessEqual(len(c.get("msg", "").split()), 30, c["text"])


class BiomeTextsTest(unittest.TestCase):
    def test_room_phrases_and_atlas_follow_the_writing_guide(self):
        for biome, rooms in RAW_DATA["atmosfere"]["biomes"].items():
            self.assertIn(biome, {b["id"] for b in RAW_DATA["biomes"]})
            for kind, phrases in rooms.items():
                with self.subTest(biome=biome, kind=kind):
                    self.assertIn(kind, RAW_DATA["lore"], "lo stesso tipo di stanza delle frasi generiche")
                    self.assertGreaterEqual(len(phrases), 3)
                    for p in phrases: self.assertLessEqual(len(p.split()), 30)
        self.assertLessEqual(set(RAW_DATA["atlante"]["biomes"]), {b["id"] for b in RAW_DATA["biomes"]} | {"eco"})
        for biome, pages in RAW_DATA["atlante"]["biomes"].items():
            for page in pages:
                with self.subTest(biome=biome, page=page["title"]):
                    self.assertTrue(80 <= len(page["text"].split()) <= 200, "STORY.md, Parte I: una pagina dell'Atlante è di 80-200 parole")
                    self.assertLessEqual(set(page.get("requires", {})), events.PROFILE_CONDITIONS)

    def test_a_room_speaks_with_the_voice_of_its_biome(self):
        own = RAW_DATA["atmosfere"]["biomes"]["chiostri"]["vendor"]
        self.assertIn(texts.room("vendor", 2), own)
        with mock.patch("texts.get_biome", return_value={"id": "nessuno"}):
            self.assertIn(texts.room("vendor", 2), RAW_DATA["lore"]["vendor"], "senza frasi del bioma, quelle generiche")

    def test_the_atlas_opens_page_by_page(self):
        import codex
        from data_manager import PROFILE_MANAGER
        saved = PROFILE_MANAGER._data["max_floor"]
        try:
            PROFILE_MANAGER._data["max_floor"] = 0
            self.assertEqual(codex.atlas_open("chiostri"), [])
            PROFILE_MANAGER._data["max_floor"] = 3
            opened = codex.atlas_open("chiostri")
            self.assertTrue(0 < len(opened) < len(RAW_DATA["atlante"]["biomes"]["chiostri"]))
            self.assertTrue(any(p["title"] in "\n".join(codex.atlas_page()) for p in opened))
        finally:
            PROFILE_MANAGER._data["max_floor"] = saved


def gated_texts():
    """(testo, condizioni) di ogni testo della v6 che si apre con il progresso del profilo."""
    for pages in RAW_DATA["atlante"]["biomes"].values():
        for p in pages: yield p["text"], p.get("requires", {})
    for t in RAW_DATA["lettere"]["threads"]:
        for x in t["letters"] + [t["epilogue"]]: yield x, t.get("requires", {})
    for ev_id in v6_events():
        ev = RAW_DATA["events"][ev_id]
        for sc in ev["scenes"].values():
            yield sc["text"], ev.get("requires", {})
            for c in sc["choices"]: yield c.get("msg", ""), ev.get("requires", {})
    for e in RAW_DATA["bestiario"]["creatures"].values():
        yield e["vista"], {}
    for b in v6_books().values():
        won = {"won": True} if b["unlock"]["type"] in ("won_normal", "ascension") else {}
        for ch in b["chapters"]: yield ch["title"] + " " + ch["text"], {**won, **ch.get("requires", {})}
    for life in RAW_DATA["vite"]["classes"].values():
        for m in life["memories"]: yield m["text"], m.get("requires", {})
    for b in RAW_DATA["voci_boss"]["bosses"].values():
        for lines in b.values():
            for t in lines: yield t, {}
    for e in RAW_DATA["epiloghi"]["endings"].values():
        for t in e.values(): yield t, {"won": True}
    for group in RAW_DATA["armeria"].values():
        for t in group.values(): yield t, {}


def v6_books() -> dict:
    """I libri dell'Archivio della v6: solo lettura, senza bonus."""
    import archive
    return {k: b for k, b in archive.BOOKS.items() if "bonus" not in b}


class LadderTest(unittest.TestCase):
    """La Scala delle rivelazioni (STORY.md): il nome del Rinnegato non compare ancora nel gioco, quello del Fuoco
    solo dal terzo gradino (piano 20 o vittoria)."""

    def test_late_names_wait_for_their_step(self):
        for text, req in gated_texts():
            with self.subTest(text=text[:50]):
                self.assertNotIn("Sereth", text)
                if "Ardel" in text:
                    self.assertTrue(req.get("won") or req.get("reached_floor", 0) >= 20 or req.get("min_floor", 0) >= 20)


class ThreadsAndBestiaryTest(unittest.TestCase):
    def setUp(self):
        import copy
        from data_manager import PROFILE_MANAGER
        self.pm, self._saved = PROFILE_MANAGER, copy.deepcopy(PROFILE_MANAGER._data)
        self._save = mock.patch.object(PROFILE_MANAGER, "save"); self._save.start()
        PROFILE_MANAGER.codex["threads"] = {}

    def tearDown(self):
        self._save.stop()
        self.pm._data.clear(); self.pm._data.update(self._saved)

    def test_letters_and_bestiary_follow_the_writing_guide(self):
        ids = [t["id"] for t in RAW_DATA["lettere"]["threads"]]
        self.assertEqual(len(ids), len(set(ids)))
        for t in RAW_DATA["lettere"]["threads"]:
            with self.subTest(thread=t["id"]):
                self.assertGreaterEqual(len(t["letters"]), 8)
                for x in t["letters"]: self.assertLessEqual(len(x.split()), 25, "una lettera è al massimo 25 parole")
                self.assertTrue(60 <= len(t["epilogue"].split()) <= 200)
                self.assertLessEqual(set(t.get("requires", {})), events.PROFILE_CONDITIONS)
        self.assertEqual(set(RAW_DATA["bestiario"]["creatures"]), set(RAW_DATA["enemies"]) | set(RAW_DATA["bosses"]))
        for name, e in RAW_DATA["bestiario"]["creatures"].items():
            with self.subTest(creature=name):
                self.assertEqual(set(e), {"vista", "abitudini", "storia"})
                for v in e.values(): self.assertTrue(20 <= len(v.split()) <= 90, f"{len(v.split())} parole")

    def test_a_thread_is_read_in_order_without_touching_the_game_dice(self):
        import random
        import threads
        state = random.getstate()
        first = RAW_DATA["lettere"]["threads"][0]
        with mock.patch("threads.open_threads", return_value=[first]):
            got = [threads.next_letter()[1] for _ in first["letters"]]
        self.assertEqual(got, first["letters"])
        self.assertTrue(threads.complete(first))
        with mock.patch("texts.RNG.random", return_value=0.0), mock.patch("threads.delay_print"), mock.patch("threads.display_msg"):
            threads.maybe_show()
        self.assertEqual(random.getstate(), state, "le lettere usano il caso dei testi, non quello del gioco")

    def test_the_bestiary_opens_tier_by_tier(self):
        import codex
        name = next(iter(RAW_DATA["enemies"]))
        rules = RAW_DATA["bestiario"]["rules"]
        tiers = lambda killed: [t for t in codex.bestiary_tiers(name, {"seen": 1, "killed": killed}, False) if codex.UNKNOWN not in t[1]]
        self.assertEqual(len(tiers(0)), 1)
        self.assertEqual(len(tiers(rules["habits"])), 2)
        self.assertEqual(len(tiers(rules["story"])), 3)


class LivesAndBooksTest(unittest.TestCase):
    def setUp(self):
        import copy
        from data_manager import PROFILE_MANAGER
        self.pm, self._saved = PROFILE_MANAGER, copy.deepcopy(PROFILE_MANAGER._data)
        self._save = mock.patch.object(PROFILE_MANAGER, "save"); self._save.start()
        PROFILE_MANAGER._data.update(class_xp={}, class_lvl={}, max_floor=0, won_normal=False)
        PROFILE_MANAGER.stats["total_bosses"] = 0

    def tearDown(self):
        self._save.stop()
        self.pm._data.clear(); self.pm._data.update(self._saved)

    def test_lives_and_books_follow_the_writing_guide(self):
        self.assertEqual(set(RAW_DATA["vite"]["classes"]), set(RAW_DATA["classes"]), "ogni classe ha la sua vita prestata")
        levels = [str(n) for n in range(2, 7)]
        for cid, life in RAW_DATA["vite"]["classes"].items():
            with self.subTest(life=cid):
                self.assertIn(life["name"], CANON)
                self.assertEqual([m["level"] for m in life["memories"]], [1] + [int(n) for n in levels], "un ricordo per livello di Maestria")
                for m in life["memories"]: self.assertTrue(70 <= len(m["text"].split()) <= 250, f"{len(m['text'].split())} parole")
        for bid, b in v6_books().items():
            with self.subTest(book=bid):
                self.assertGreaterEqual(len(b["chapters"]), 4)
                for ch in b["chapters"]:
                    self.assertTrue(80 <= len(ch["text"].split()) <= 400, f"{len(ch['text'].split())} parole")
                    self.assertLessEqual(set(ch.get("requires", {})), events.PROFILE_CONDITIONS)

    def test_a_memory_returns_with_each_mastery_level(self):
        import codex
        self.assertEqual(codex.lives_open("1"), [], "una classe mai giocata non ricorda niente")
        self.pm.set_class_xp("1", 10)
        self.assertEqual([m["level"] for m in codex.lives_open("1")], [1])
        self.pm.set_class_lvl("1", 3)
        self.assertEqual([m["title"] for m in codex.new_memories("1", 1, 3)], [m["title"] for m in RAW_DATA["vite"]["classes"]["1"]["memories"][1:3]])
        self.pm.set_class_xp("9", 10); self.pm.set_class_lvl("9", 6)
        gated = [m for m in RAW_DATA["vite"]["classes"]["9"]["memories"] if m.get("requires")]
        self.assertTrue(gated)
        self.assertEqual(len(codex.lives_open("9")), 6 - len(gated), "i ricordi più vicini alla verità aspettano il progresso")
        self.assertIn(codex.UNKNOWN, "\n".join(codex.lives_page()))

    def test_a_late_chapter_stays_unreadable(self):
        import archive
        book = archive.BOOKS["quaderno_orvin"]
        self.assertNotIn("bonus", book)
        self.assertLess(len(archive.open_chapters(book)), len(book["chapters"]))
        with mock.patch.object(events, "check", return_value=True):
            self.assertEqual(len(archive.open_chapters(book)), len(book["chapters"]))
        self.assertNotIn(book["title"], [t for t, _ in archive.unlocked_archive_bonuses({"max_floor": 30})])


class EndingsBossesArmoryTest(unittest.TestCase):
    def test_every_boss_has_a_voice_for_each_moment(self):
        self.assertEqual(set(RAW_DATA["voci_boss"]["bosses"]), set(RAW_DATA["bosses"]))
        for name, b in RAW_DATA["voci_boss"]["bosses"].items():
            with self.subTest(boss=name):
                self.assertEqual(set(b), {"intro", "phase", "death"})
                for lines in b.values():
                    self.assertTrue(lines)
                    for t in lines: self.assertLessEqual(len(t.split()), 25, "una battuta di un boss è al massimo 25 parole")

    def test_a_boss_voice_does_not_touch_the_game_dice(self):
        import random
        state = random.getstate()
        name = next(iter(RAW_DATA["bosses"]))
        for moment in ("intro", "phase", "death"): self.assertIn(texts.boss_voice(name, moment), RAW_DATA["voci_boss"]["bosses"][name][moment])
        self.assertEqual(texts.boss_voice("Nessuno", "intro"), "")
        self.assertEqual(random.getstate(), state)

    def test_every_ending_has_an_epilogue_for_every_life(self):
        endings = {e["id"] for e in RAW_DATA["story"]["endings"]}
        self.assertEqual(set(RAW_DATA["epiloghi"]["endings"]), endings)
        for eid, lives in RAW_DATA["epiloghi"]["endings"].items():
            with self.subTest(ending=eid):
                self.assertEqual(set(lives), set(RAW_DATA["classes"]))
                for t in lives.values(): self.assertTrue(40 <= len(t.split()) <= 120, f"{len(t.split())} parole")

    def test_an_epilogue_is_remembered_in_the_codex(self):
        import copy
        import codex
        import endings
        from data_manager import PROFILE_MANAGER
        saved = copy.deepcopy(PROFILE_MANAGER._data)
        try:
            PROFILE_MANAGER.story["endings"] = {"custode": 1}
            PROFILE_MANAGER.story["epilogues"] = []
            text = endings.record_epilogue("custode", "4")
            self.assertEqual(text, RAW_DATA["epiloghi"]["endings"]["custode"]["4"])
            endings.record_epilogue("custode", "4")
            self.assertEqual(PROFILE_MANAGER.story["epilogues"], ["custode:4"])
            self.assertIn(text, "\n".join(codex.endings_page()))
        finally:
            PROFILE_MANAGER._data.clear(); PROFILE_MANAGER._data.update(saved)

    def test_the_armory_tells_every_item(self):
        a = RAW_DATA["armeria"]
        self.assertEqual(set(a["weapons"]), {w["name"] for w in RAW_DATA["weapons"]})
        self.assertEqual(set(a["armors"]), {w["name"] for w in RAW_DATA["armors"]})
        self.assertEqual(set(a["accessories"]), {w["name"] for w in RAW_DATA["accessories"]})
        self.assertEqual(set(a["relics"]), {r["id"] for r in RAW_DATA["relics"]})
        for group in a.values():
            for name, t in group.items():
                with self.subTest(item=name): self.assertTrue(40 <= len(t.split()) <= 80, f"{len(t.split())} parole")

    def test_the_armory_opens_with_the_forge_and_the_codex(self):
        import copy
        import codex
        from data_manager import PROFILE_MANAGER
        saved = copy.deepcopy(PROFILE_MANAGER._data)
        try:
            PROFILE_MANAGER._data["unlocked_ids"] = []
            PROFILE_MANAGER.codex["relics"] = []
            known = dict(codex.armory_open())
            self.assertIn("Spada Corta", known)
            self.assertNotIn("Spada del Carnefice", known, "un'arma della Forgia si legge quando la sblocchi")
            PROFILE_MANAGER._data["unlocked_ids"] = ["spada_carnefice"]
            PROFILE_MANAGER.codex["relics"] = ["tasca_dorata"]
            known = dict(codex.armory_open())
            self.assertIn("Spada del Carnefice", known)
            self.assertIn("Tasca Dorata", known)
            self.assertIn("Armeria", codex.UNCOUNTED)
        finally:
            PROFILE_MANAGER._data.clear(); PROFILE_MANAGER._data.update(saved)


class TextsTest(unittest.TestCase):
    def test_no_two_narrative_texts_are_the_same(self):
        self.assertEqual(conta_testi.duplicates(conta_testi.blocks()), [], "un testo narrativo è ripetuto identico")

    def test_the_count_covers_every_block(self):
        counted = conta_testi.blocks()
        self.assertEqual(set(counted), set(conta_testi.BASELINE), "ogni blocco ha il suo valore della v5")
        for name, items in counted.items():
            with self.subTest(block=name): self.assertTrue(items)


if __name__ == "__main__":
    unittest.main()
