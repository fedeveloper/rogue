"""La lore: il canone (`STORY.md`) parla di tutto ciò che il gioco nomina, e due testi narrativi non sono mai identici
(`tools/conta_testi.py`)."""
import importlib
import os
import sys
import unittest

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


# Gli eventi scritti per la v6 (i capitoli degli archi dopo quelli della v5): in partita i testi sono brevi
V5_CHAPTERS = {"alaric": 3, "silas": 3}


def v6_events() -> list:
    out = []
    for cid, char in RAW_DATA["story"]["characters"].items():
        out += [ch["event"] for ch in char["chapters"][V5_CHAPTERS.get(cid, 0):]]
    return out


class InRunLengthTest(unittest.TestCase):
    def test_v6_events_follow_the_writing_guide(self):
        """STORY.md, Parte I: scena di un evento al massimo 55 parole, esito di una scelta al massimo 30."""
        for ev_id in v6_events():
            for sc_id, scene in RAW_DATA["events"][ev_id]["scenes"].items():
                with self.subTest(event=ev_id, scene=sc_id):
                    self.assertLessEqual(len(scene["text"].split()), 55)
                    for c in scene["choices"]: self.assertLessEqual(len(c.get("msg", "").split()), 30, c["text"])


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
