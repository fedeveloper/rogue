"""La grafica a terminale: barre, riquadri e ritratti dei boss (`ui.bar`, `ui.panel`, `texts.portrait`)."""
import random
import re
import unittest

import texts
import ui
from data_manager import RAW_DATA

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def plain(text: str) -> str:
    return ANSI.sub("", text)


class BarTest(unittest.TestCase):
    def test_the_bar_is_always_as_wide_as_asked(self):
        for value, maximum in ((0, 50), (1, 50), (25, 50), (50, 50), (80, 50), (-3, 50), (5, 0)):
            with self.subTest(value=value, maximum=maximum):
                self.assertEqual(len(plain(ui.bar(value, maximum))), ui.BAR_WIDTH)
        self.assertEqual(len(plain(ui.bar(3, 12, width=ui.ETHER_BAR))), ui.ETHER_BAR)

    def test_the_bar_fills_in_proportion(self):
        self.assertEqual(plain(ui.bar(0, 80)).count("█"), 0)
        self.assertEqual(plain(ui.bar(1, 80)).count("█"), 1, "chi ha un solo punto vede ancora una casella")
        self.assertEqual(plain(ui.bar(40, 80)).count("█"), ui.BAR_WIDTH // 2)
        self.assertEqual(plain(ui.bar(80, 80)).count("█"), ui.BAR_WIDTH)
        self.assertLess(plain(ui.bar(79, 80)).count("█"), ui.BAR_WIDTH, "piena solo quando è davvero piena")


class PanelTest(unittest.TestCase):
    def test_every_row_of_a_panel_has_the_same_width(self):
        for lines, title in ((["a", "bbbbbb", ""], "TITOLO"), (["x"], "UN TITOLO PIÙ LARGO DEL CONTENUTO"), (["❤️  HP"], "")):
            with self.subTest(title=title):
                rows = ui.panel(lines, title, ui.Colors.MAGENTA)
                self.assertEqual(len(rows), len(lines) + 2)
                self.assertEqual(len({ui.visible_width(r) for r in rows}), 1)
                if title: self.assertIn(title, plain(rows[0]))

    def test_pad_counts_columns_not_characters(self):
        self.assertEqual(ui.visible_width(ui.pad(f"{ui.Colors.RED}Tu{ui.Colors.RESET}", 9)), 9)


class PortraitTest(unittest.TestCase):
    def test_every_boss_has_a_portrait_that_fits_the_terminal(self):
        self.assertEqual(set(RAW_DATA["ritratti"]["bosses"]), set(RAW_DATA["bosses"]))
        for name in RAW_DATA["bosses"]:
            with self.subTest(boss=name):
                art = texts.portrait(name)
                self.assertTrue(4 <= len(art) <= 10, "un ritratto sta in poche righe")
                self.assertLessEqual(max(map(len, art)), 30, "e in trenta colonne")
                self.assertTrue(all(ch.isascii() for line in art for ch in line), "solo caratteri che ogni terminale disegna larghi uno")
                self.assertTrue(any(line and not line.startswith(" ") for line in art), "senza margine comune a sinistra")

    def test_every_common_enemy_has_the_silhouette_of_its_family(self):
        art = RAW_DATA["ritratti"]
        self.assertEqual(set(art["enemies"]), set(RAW_DATA["enemies"]))
        self.assertEqual(set(art["enemies"].values()), set(art["sagome"]), "ogni sagoma è usata e ogni nemico ne nomina una che esiste")
        for name, lines in art["sagome"].items():
            with self.subTest(sagoma=name):
                self.assertTrue(3 <= len(lines) <= 6, "una sagoma è più piccola di un ritratto")
                self.assertLessEqual(max(map(len, lines)), 22)
                self.assertTrue(all(ch.isascii() for line in lines for ch in line))
        name = next(iter(RAW_DATA["enemies"]))
        self.assertEqual(texts.portrait(name), texts._trim(art["sagome"][art["enemies"][name]]))

    def test_every_biome_has_a_landscape(self):
        self.assertEqual(set(RAW_DATA["ritratti"]["biomes"]), {b["id"] for b in RAW_DATA["biomes"]})
        for b in RAW_DATA["biomes"]:
            with self.subTest(biome=b["id"]):
                view = texts.landscape(b["id"])
                self.assertTrue(3 <= len(view) <= 5)
                self.assertLessEqual(max(map(len, view)), 44, "sta anche in un terminale stretto, cornice compresa")
                self.assertTrue(all(ch.isascii() for line in view for ch in line))
                rows = ui.panel(view, f"{b['icon']}  {b['name'].upper()}", ui.Colors.MAGENTA)
                self.assertEqual(len({ui.visible_width(r) for r in rows}), 1)
        self.assertEqual(texts.landscape("nessuno"), [])

    def test_every_quiet_room_has_an_emblem(self):
        self.assertEqual(set(RAW_DATA["ritratti"]["stanze"]), {"campfire", "vendor", "treasure", "trap", "mystery"})
        for kind in RAW_DATA["ritratti"]["stanze"]:
            with self.subTest(room=kind):
                art = texts.emblem(kind)
                self.assertTrue(3 <= len(art) <= 5)
                self.assertLessEqual(max(map(len, art)), 22)
                self.assertTrue(all(ch.isascii() for line in art for ch in line))
        self.assertEqual(texts.emblem("combat"), [], "le stanze di scontro mostrano il nemico, non un'insegna")

    def test_a_room_draws_its_emblem_before_its_phrase(self):
        import io
        from contextlib import redirect_stdout
        import rooms
        out = io.StringIO()
        with redirect_stdout(out): rooms.show_emblem("campfire", ui.Colors.YELLOW)
        shown = plain(out.getvalue())
        for line in texts.emblem("campfire"): self.assertIn(line, shown)

    def test_who_has_no_portrait_gets_none_and_the_game_dice_are_untouched(self):
        state = random.getstate()
        self.assertEqual(texts.portrait("Goblin qualunque"), [])
        texts.portrait(next(iter(RAW_DATA["bosses"])))
        self.assertEqual(random.getstate(), state)


if __name__ == "__main__":
    unittest.main()
