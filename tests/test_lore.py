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
