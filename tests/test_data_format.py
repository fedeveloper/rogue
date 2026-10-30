"""I file di data/ sono nel formato unico di tools/formatta_dati.py: chi li modifica li riformatta con
`python tools/formatta_dati.py`, così il testo dei dati non dipende da chi li ha scritti."""
import importlib
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
formatta_dati = importlib.import_module("formatta_dati")  # lo strumento sta in tools/, fuori dai pacchetti del gioco


class DataFormatTest(unittest.TestCase):
    def test_every_data_file_is_in_the_canonical_format(self):
        self.assertTrue(formatta_dati.files())
        self.assertEqual(formatta_dati.out_of_format(), [], "riformatta con `python tools/formatta_dati.py`")

    def test_the_format_keeps_the_content_and_is_stable(self):
        sample = {"a": [1, 2, {"b": "é 🔥"}], "lunga": {"chiave_" + str(i): "valore lungo " * 3 for i in range(6)}, "vuoto": {}}
        text = formatta_dati.format_json(sample)
        self.assertEqual(json.loads(text), sample)
        self.assertEqual(formatta_dati.format_json(json.loads(text)), text, "riformattare non cambia più nulla")
        self.assertIn("é 🔥", text)
        self.assertTrue(all(len(line) <= formatta_dati.WIDTH or line.strip().startswith('"') for line in text.splitlines()))
        self.assertTrue(text.endswith("}\n"))


if __name__ == "__main__":
    unittest.main()
