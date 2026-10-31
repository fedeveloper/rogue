"""Un salvataggio di una versione precedente si carica e si gioca: `tests/profilo_v2.json` è un profilo della v2 (mappa e
biomi, prima dell'Ascensione), con le sole voci che quella versione scriveva, e non va mai aggiornato a mano."""
import copy
import importlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

import codex
import data_manager
import modes
import roguelike
from data_manager import PROFILE_MANAGER, default_profile, update_game_data
from entities import Player

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V2 = os.path.join(ROOT, "tests", "profilo_v2.json")
sys.path.insert(0, os.path.join(ROOT, "tools"))
bilanciamento = importlib.import_module("bilanciamento")  # il simulatore sta in tools/, fuori dai pacchetti del gioco


def load(path: str) -> dict:
    manager = data_manager.ProfileManager.__new__(data_manager.ProfileManager)
    manager.filepath = path
    with redirect_stdout(io.StringIO()): return manager._load()


def missing(default: dict, loaded: dict, prefix: str = "") -> list:
    """Le voci del profilo nuovo che mancano in quello caricato (anche dentro le sezioni)."""
    out = []
    for key, val in default.items():
        if key not in loaded: out.append(prefix + key)
        elif isinstance(val, dict) and isinstance(loaded[key], dict): out += missing(val, loaded[key], f"{prefix}{key}.")
    return out


class MigrationTest(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        self._save = mock.patch.object(PROFILE_MANAGER, "save")
        self._save.start()
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, "profile.json")
        shutil.copy(V2, self.path)
        with open(V2, encoding="utf-8") as f: self.old = json.load(f)

    def tearDown(self):
        self._save.stop()
        shutil.rmtree(self.tmp)
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)
        update_game_data()

    def test_the_old_profile_gets_every_new_entry_and_keeps_its_own(self):
        loaded = load(self.path)
        self.assertEqual(missing(default_profile(), loaded), [])
        for key in ("essence", "max_floor", "won_normal", "unlocked_ids", "class_xp", "class_lvl", "completed_feats", "perks"):
            with self.subTest(key=key): self.assertEqual(loaded[key], self.old[key])
        self.assertEqual(loaded["story"]["flags"], self.old["story"]["flags"])
        self.assertEqual(loaded["codex"]["enemies"], self.old["codex"]["enemies"])
        with open(self.path, encoding="utf-8") as f: self.assertEqual(json.load(f), loaded, "il profilo migrato è salvato")
        with mock.patch.object(data_manager.ProfileManager, "_write") as write:
            self.assertEqual(load(self.path), loaded)
        write.assert_not_called()

    def test_the_old_profile_opens_every_screen(self):
        PROFILE_MANAGER._data.clear(); PROFILE_MANAGER._data.update(load(self.path)); update_game_data()
        self.assertEqual(modes.max_grade(), 1, "vinta la discesa standard, il primo grado di Ascensione è aperto")
        self.assertIn("SFIDA DEL GIORNO", roguelike.daily_page(modes.daily_setup(modes.today())))
        self.assertGreaterEqual(codex.completion(), 0)
        for page in [getattr(codex, n) for n in dir(codex) if n.endswith("_page")]:
            with self.subTest(page=page.__name__): self.assertIsInstance(page(), list)
        for cls in ["1"] + [c for c in self.old["unlocked_ids"] if c.isdigit()]:
            with self.subTest(cls=cls), redirect_stdout(io.StringIO()):
                self.assertGreater(Player(cls, "base", []).max_hp, 0)

    def test_the_old_profile_plays_a_descent(self):
        log = bilanciamento.play("1", 4242, load(self.path))
        self.assertGreaterEqual(log["floor"], 1)


if __name__ == "__main__":
    unittest.main()
