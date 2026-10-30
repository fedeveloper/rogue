"""Il registro degli effetti (`effects.py`): ogni fonte somma con le altre, ogni chiave dei dati ha qualcuno che la
legge e ogni chiave letta viene da qualche fonte."""
import copy
import glob
import io
import os
import re
import unittest
from contextlib import redirect_stdout
from unittest import mock

import archive
import camp_rules
import effects
import runes
from data_manager import GAME_DATA, PROFILE_MANAGER, RAW_DATA
from entities import Player
from relic_effects import create_relic_effect

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
READ = re.compile(r'effects\.(?:total\([^,]+, "(\w+)"|of\([^,]+, "\w+", "(\w+)")')
# Chiavi che un modulo legge da sé, fuori dal registro: lo scaled_dmg_pct dell'attributo con cui scala l'arma
OWN_READERS = {"scaled_dmg_pct": "attributes.weapon_bonus"}


def data_keys() -> dict:
    """Le chiavi degli effetti nei dati, per fonte."""
    found = {
        "attributi": [k for a in GAME_DATA["attributes"]["attributes"].values() for k in a["per_point"]],
        "talenti": [k for t in GAME_DATA["talents"]["talents"].values() for k in t["effects"]],
        "tratto": [k for t in GAME_DATA["meta"]["traits"].values() for k in t.get("effects", {})],
        "campo": [k for s in camp_rules.structures() for lv in camp_rules.levels(s) for k in lv.get("effects", {})],
        "rune": [k for r in list(GAME_DATA["runes"]["runes"].values()) + list(GAME_DATA["runes"]["words"].values()) for k in r["effects"]]
                + [k for r in RAW_DATA["relics"] for k in getattr(create_relic_effect(r["id"]), "BONUS", {})],
        "maestria": [k for c in RAW_DATA["classes"].values() for m in c["mastery"].values() if m.get("type") == "magic" for k in m["bonus"]],
        "archivio": [k for b in archive.BOOKS.values() for k in b.get("bonus", {})],
    }
    return {source: set(keys) for source, keys in found.items()}


def read_keys() -> set:
    """Le chiavi che il codice del gioco legge dal registro."""
    keys = {key for _, key, _ in runes.ON_HIT_STATUSES}  # lette con una variabile, una per status
    for path in glob.glob(os.path.join(ROOT, "*.py")):
        with open(path, encoding="utf-8") as f:
            keys |= {a or b for a, b in READ.findall(f.read())}
    return keys


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        self._save = mock.patch.object(PROFILE_MANAGER, "save")
        self._save.start()

    def tearDown(self):
        self._save.stop()
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)

    def hero(self):
        with redirect_stdout(io.StringIO()): p = Player("1", "base", [])
        for a in p.attributes: p.attributes[a] = 0
        p.talents, p.trait_effects, p.camp_effects, p.mastery_magic = [], {}, {}, {}
        p.weapon.runes = p.armor.runes = []
        return p


class RegistryTest(Sandbox):
    def test_every_source_of_the_data_is_registered(self):
        self.assertEqual(set(data_keys()), {name for name, _ in effects.SOURCES})

    def test_every_key_in_the_data_is_read(self):
        read = read_keys() | set(OWN_READERS)
        for source, keys in data_keys().items():
            with self.subTest(source=source):
                self.assertEqual(keys - read, set(), "una chiave dei dati che nessuno legge non fa niente in gioco")

    def test_every_key_read_comes_from_some_source(self):
        given = set().union(*data_keys().values())
        self.assertEqual(read_keys() - given, set(), "una chiave letta che nessuna fonte dà vale sempre 0")

    def test_a_key_adds_up_from_every_source(self):
        p, base = self.hero(), self.hero()
        p.attributes["forza"] = 1
        p.talents = ["lama_affilata"]
        p.trait_effects, p.camp_effects, p.mastery_magic = {"dmg_pct": 3}, {"dmg_pct": 4}, {"dmg_pct": 5}
        p.weapon.sockets, p.weapon.runes = 1, ["sapienza"]
        attr = GAME_DATA["attributes"]["attributes"]["forza"]["per_point"].get("dmg_pct", 0)
        talent = GAME_DATA["talents"]["talents"]["lama_affilata"]["effects"]["dmg_pct"]
        self.assertEqual(effects.total(p, "dmg_pct") - effects.total(base, "dmg_pct"), attr + talent + 3 + 4 + 5)
        self.assertEqual(effects.total(p, "spell_pct") - effects.total(base, "spell_pct"), GAME_DATA["runes"]["runes"]["sapienza"]["effects"]["spell_pct"]
                         + GAME_DATA["attributes"]["attributes"]["forza"]["per_point"].get("spell_pct", 0))

    def test_the_total_is_the_sum_of_the_sources_and_skip_leaves_one_out(self):
        p = self.hero()
        p.trait_effects, p.camp_effects = {"gold_pct": 2}, {"gold_pct": 7}
        with mock.patch("effects.get_archive_bonus", return_value=10):
            parts = {name: effects.of(p, name, "gold_pct") for name, _ in effects.SOURCES}
            self.assertEqual(effects.total(p, "gold_pct"), sum(parts.values()))
            self.assertEqual(effects.total(p, "gold_pct", skip=("archivio",)), sum(parts.values()) - 10)
        self.assertEqual((parts["tratto"], parts["campo"], parts["archivio"]), (2, 7, 10))

    def test_the_hero_reads_the_registry(self):
        """Un effetto dato da una fonte qualsiasi arriva alle statistiche dell'eroe."""
        p, base = self.hero(), self.hero()
        p.camp_effects = {"acc": 6, "crit": 4, "dodge": 3, "def": 2, "ether_max": 5}
        self.assertEqual(p.get_hit_chance() - base.get_hit_chance(), 6)
        self.assertEqual(p.get_crit_chance() - base.get_crit_chance(), 4)
        self.assertEqual(p.get_dodge() - base.get_dodge(), 3)
        self.assertEqual(p.get_total_def() - base.get_total_def(), 2)
        self.assertEqual(p.max_ether() - base.max_ether(), 5)


if __name__ == "__main__":
    unittest.main()
