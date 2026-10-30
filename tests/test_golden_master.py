"""Golden master: un gruppo fisso di run del simulatore, con semi fissi, deve dare sempre lo stesso esito.

Serve alle rifattorizzazioni, che non devono cambiare il gioco: se una modifica cambia anche una sola di queste
run, il comportamento è cambiato. Quando il cambiamento è voluto (regole, dati, bilanciamento), si rigenera
l'impronta con `python tools/bilanciamento.py golden` e si spiega nella PR perché è cambiata.
"""
import copy
import json
import os
import sys
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import bilanciamento  # noqa: E402
from data_manager import PROFILE_MANAGER, update_game_data  # noqa: E402


class GoldenMasterTest(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        self._save = mock.patch.object(PROFILE_MANAGER, "save")
        self._save.start()

    def tearDown(self):
        self._save.stop()
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)
        update_game_data()

    def test_the_reference_runs_do_not_change(self):
        with open(bilanciamento.GOLDEN_FILE, encoding="utf-8") as f: expected = json.load(f)
        actual = bilanciamento.golden_runs()
        self.assertEqual(len(actual), len(expected), "il gruppo di run è cambiato: rigenera con `python tools/bilanciamento.py golden`")
        for want, got in zip(expected, actual):
            with self.subTest(run=want["run"]):
                self.assertEqual(got, want, "questa run non dà più lo stesso esito. Se il cambiamento è voluto, rigenera "
                                            "con `python tools/bilanciamento.py golden` e spiega nella PR perché")

    def test_the_runs_do_not_depend_on_the_local_profile(self):
        PROFILE_MANAGER._data["best_echo"] = 9
        PROFILE_MANAGER._data["nemeses"] = [{"id": "x", "enemy": "Goblin", "name": "Morsa", "rank": 5, "kills": 9, "gold": 0, "floor": 3,
                                             "trait": "atk_bonus_pct", "element": "Normale", "class": "Guerriero"}]
        first = bilanciamento.golden_runs(limit=1)
        PROFILE_MANAGER._data.clear(); PROFILE_MANAGER._data.update(copy.deepcopy(self._saved))
        self.assertEqual(first, bilanciamento.golden_runs(limit=1))


if __name__ == "__main__":
    unittest.main()
