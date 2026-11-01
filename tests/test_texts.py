"""I testi d'atmosfera (`texts.py`) non toccano il caso del gioco: con più frasi nei dati le discese restano identiche.

È la garanzia che permette di espandere la lore senza ribilanciare: frasi delle stanze, atmosfere dei biomi e
lettere insanguinate si possono aggiungere senza cambiare mappe, nemici, bottino ed esiti.
"""
import copy
import importlib
import os
import sys
import unittest
from unittest import mock

import texts
from data_manager import GAME_DATA, PROFILE_MANAGER, RAW_DATA, update_game_data

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
bilanciamento = importlib.import_module("bilanciamento")  # il simulatore sta in tools/, fuori dai pacchetti del gioco


class TextRandomnessTest(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        self._save = mock.patch.object(PROFILE_MANAGER, "save")
        self._save.start()

    def tearDown(self):
        self._save.stop()
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)
        update_game_data()

    def test_more_texts_do_not_change_the_descent(self):
        before = bilanciamento.golden_runs(limit=3)
        lore = {k: v + [f"Frase nuova {i} per {k}." for i in range(7)] for k, v in RAW_DATA["lore"].items()}
        biomes = [dict(b, intro=b["intro"] + ["Un'atmosfera nuova.", "Un'altra ancora."]) for b in RAW_DATA["biomes"]]
        with mock.patch.dict(RAW_DATA, lore=lore, biomes=biomes):
            update_game_data()
            self.assertEqual(len(GAME_DATA["lore"]["combat"]), len(RAW_DATA["lore"]["combat"]))
            after = bilanciamento.golden_runs(limit=3)
        self.assertEqual(after, before, "una frase in più ha cambiato una discesa: un testo usa il caso del gioco")

    def test_texts_have_their_own_generator(self):
        import random
        state = random.getstate()
        for _ in range(20): texts.pick(["a", "b", "c"]); texts.index(9)
        self.assertEqual(random.getstate(), state)


if __name__ == "__main__":
    unittest.main()
