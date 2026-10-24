"""I documenti seguono i dati: il README è quello generato da tools/genera_readme.py, e il Manuale del Giocatore
elenca i gradi di Ascensione e i doni della Sfida del Giorno esattamente come sono in `data/modes.json`."""
import importlib.util
import os
import re
import unittest

from data_manager import GAME_DATA

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f: return f.read()


def it(x: float) -> str:
    return f"{round(x, 2):g}".replace(".", ",")


class ReadmeIsGeneratedTest(unittest.TestCase):
    def test_the_readme_matches_the_generator(self):
        spec = importlib.util.spec_from_file_location("genera_readme", os.path.join(ROOT, "tools", "genera_readme.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(read("README.md"), module.README, "README.md non è aggiornato: esegui python tools/genera_readme.py")


class ManualFollowsTheDataTest(unittest.TestCase):
    def setUp(self):
        self.manual = read("MANUALE_GIOCATORE.md")

    def test_the_ascension_table_lists_every_grade(self):
        mult, rows = 1.0, re.findall(r"^\| (\d+) \| (.+?) \| (.+?) \| ×([\d,]+) \|$", self.manual, re.M)
        grades = GAME_DATA["modes"]["ascension"]["grades"]
        self.assertEqual(len(rows), len(grades))
        for (n, name, desc, essence), (i, g) in zip(rows, enumerate(grades, 1)):
            mult += g["essence_bonus"]
            with self.subTest(grade=i):
                self.assertEqual((int(n), name, desc, essence), (i, g["name"], g["desc"], it(mult)))

    def test_the_rune_table_lists_every_rune(self):
        slot = {"weapon": "Arma", "armor": "Armatura", "any": "Arma o armatura"}
        for r in GAME_DATA["runes"]["runes"].values():
            self.assertIn(f"| {r['icon']} {r['name']} | {r['family']} | {slot[r['slot']]} | {r['desc']} |", self.manual)
        runes = GAME_DATA["runes"]["runes"]
        for w in GAME_DATA["runes"]["words"].values():
            self.assertIn(f"| «{w['name']}» | {' + '.join(runes[r]['name'] for r in w['runes'])} | {w['desc']} |", self.manual)
        rules = GAME_DATA["runes"]["rules"]
        for source, pct in rules["drops"].items(): self.assertIn(f"({pct}%)", self.manual)
        self.assertIn(f"Costa {rules['extract_cost'][0]} Oro più {rules['extract_cost'][1]} per piano", self.manual)

    def test_the_attribute_tables_match_the_data(self):
        attrs = GAME_DATA["attributes"]
        self.assertIn(attrs["rules"]["desc"], self.manual)
        for a in attrs["attributes"].values():
            self.assertIn(f"| {a['icon']} **{a['name']}** | {a['desc']} |", self.manual)
        for c in GAME_DATA["classes"].values():
            start = ", ".join(f"{attrs['attributes'][k]['name']} {v}" for k, v in c["attributes"].items())
            self.assertIn(f"| {c['role']} | {start} |", self.manual)

    def test_the_magic_tables_match_the_data(self):
        spells = GAME_DATA["spells"]
        self.assertIn(spells["rules"]["desc"], self.manual)
        icons = GAME_DATA["elements"]["icons"]
        for s in spells["spells"].values():
            self.assertIn(f"| {s['icon']} **{s['name']}** | {icons[s['element']]} {s['element']} | {s['cost']} | {s['desc']} |", self.manual)
        for c in GAME_DATA["classes"].values():
            names = ", ".join(spells["spells"][x]["name"] for x in c["spells"])
            self.assertIn(f"| {c['role']} | {c['ether']} | {names} |", self.manual)

    def test_the_daily_section_lists_every_boon_and_rule(self):
        daily = GAME_DATA["modes"]["daily"]
        for b in daily["boons"]:
            self.assertIn(f"| {b['name']} | {b['desc']} |", self.manual)
        s = daily["score"]
        self.assertIn(f"{s['per_floor']} per piano raggiunto, {s['per_boss']} per boss, {s['victory']} per la vittoria, più un punto ogni {s['gold_div']} Oro", self.manual)
        self.assertIn(f"Essenza ×{it(daily['first_attempt_essence_mult'])}", self.manual)
        self.assertIn(f"{daily['maluses']} **malus**", self.manual)
        self.assertIn(f"tiene {daily['history']} giorni", self.manual)


if __name__ == "__main__":
    unittest.main()
