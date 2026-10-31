"""Contenuti della v5: esiti nuovi del Mistero (Fonte d'Etere, Pergamena, Runa), tomi dell'Archivio che si sbloccano
con incantesimi, Ascensione ed Eco e danno bonus magici, tratti nuovi (Sordo all'Arcano, Erudito, Talento Naturale)
e i loro sblocchi."""
import copy
import io
import random
import unittest
from contextlib import redirect_stdout
from unittest import mock

import archive
import inventory_menu
import roguelike
import rooms
from data_manager import GAME_DATA, PROFILE_MANAGER
from entities import Player, Scroll
from rooms_patch import patch_rooms

MYSTERY = GAME_DATA["meta"]["rooms"]["mystery"]


def quiet():
    return redirect_stdout(io.StringIO())


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        self._save = mock.patch.object(PROFILE_MANAGER, "save")
        self._save.start()
        self._ui = [patch_rooms(f) for f in ("wait_enter", "delay_print", "clear_screen")] + [mock.patch("rooms.time.sleep")]
        for p in self._ui: p.start()
        random.seed(4)

    def tearDown(self):
        for p in self._ui: p.stop()
        self._save.stop()
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)

    def hero(self, cls="1", trait="base"):
        with quiet(): return Player(cls, trait, [])

    def mystery(self, p, outcome):
        """La stanza del Mistero con l'esito dato: solo la prima estrazione è sostituita, le altre (es. la runa) restano vere."""
        real, calls = random.choices, []
        def choices(*a, **k):
            calls.append(1)
            return [outcome] if len(calls) == 1 else real(*a, **k)
        with quiet(), mock.patch("rooms.random.choices", side_effect=choices):
            rooms.mystery_room(p, 5, [])


class MysteryTest(Sandbox):
    def test_the_spring_fills_ether_or_heals_who_has_no_spells(self):
        p = self.hero(); p.base_ether, p.ether = 30, 0
        self.mystery(p, "spring")
        self.assertEqual(p.ether, p.max_ether())
        p = self.hero(); p.spells = []; p.max_hp, p.hp = 1000, 100
        self.mystery(p, "spring")
        self.assertEqual(p.hp, 100 + 1000 * MYSTERY["spring_heal_pct"] // 100)

    def test_a_scroll_and_a_rune(self):
        for outcome, kind in (("scroll", "scroll"), ("rune", "rune")):
            with self.subTest(outcome=outcome):
                p = self.hero(); p.inventory = []
                self.mystery(p, outcome)
                self.assertEqual([i.type for i in p.inventory], [kind])

    def test_every_outcome_has_a_name_for_the_sixth_sense(self):
        self.assertEqual(set(rooms.MYSTERY_NAMES), set(MYSTERY["outcomes"]))


class ArchiveTest(Sandbox):
    def unlocked(self, book_id, **profile):
        data = copy.deepcopy(PROFILE_MANAGER._data); data.update(profile)
        return archive.is_book_unlocked(book_id, data)

    def test_the_new_tomes_unlock_with_their_progress(self):
        spells = list(GAME_DATA["spells"]["spells"])
        self.assertFalse(self.unlocked("grimorio_valerius", codex={"spells": spells[:9]}))
        self.assertTrue(self.unlocked("grimorio_valerius", codex={"spells": spells[:10]}))
        self.assertFalse(self.unlocked("cronache_ascesa", ascension={"best_win": 4}))
        self.assertTrue(self.unlocked("cronache_ascesa", ascension={"best_win": 5}))
        self.assertFalse(self.unlocked("canto_eco", best_echo=1))
        self.assertTrue(self.unlocked("canto_eco", best_echo=2))

    def test_the_grimoire_gives_ether_to_every_hero(self):
        PROFILE_MANAGER._data.setdefault("codex", {})["spells"] = []
        before = self.hero().max_ether()
        PROFILE_MANAGER._data["codex"]["spells"] = list(GAME_DATA["spells"]["spells"])
        self.assertEqual(self.hero().max_ether(), before + archive.BOOKS["grimorio_valerius"]["bonus"]["ether_max"])

    def test_every_tome_bonus_number_is_in_its_text(self):
        for bid, b in archive.BOOKS.items():
            with self.subTest(book=bid):
                self.assertTrue(b["chapters"])
                for v in b["bonus"].values(): self.assertIn(str(v), b["bonus_desc"])


class TraitTest(Sandbox):
    def test_the_deaf_hero_cannot_learn_scrolls(self):
        p = self.hero("3", "sordo_arcano"); p.inventory = [Scroll("frana")]
        with quiet(), mock.patch("inventory_menu.wait_enter"):
            inventory_menu.learn_scroll(p, p.inventory[0])
        self.assertEqual((p.spells, len(p.inventory)), ([], 1))
        self.assertEqual(p.max_ether(), 0, "nemmeno l'Arcano gli dà Etere")

    def test_the_scholar_learns_a_spell_he_did_not_know(self):
        base = self.hero("3")
        p = self.hero("3", "erudito")
        self.assertEqual(p.spells[:len(base.spells)], base.spells)
        self.assertNotIn(p.spells[-1], base.spells)

    def test_natural_talent_earns_a_talent_every_four_levels(self):
        p = self.hero("1", "talento_naturale")
        while p.level < 8:
            with quiet(): p.gain_exp(p.max_exp - p.exp)
        self.assertEqual(p.pending_talents, 2)

    def test_new_traits_unlock_with_their_feat(self):
        feats = {"sordo_arcano": "feat_asceta", "erudito": "feat_arcimago", "talento_naturale": "feat_talenti"}
        for tid, fid in feats.items():
            with self.subTest(trait=tid):
                self.assertEqual(GAME_DATA["meta"]["traits"][tid]["unlock_req"], fid)
                self.assertEqual(GAME_DATA["meta"]["feats"][fid]["reward_id"], tid)
        PROFILE_MANAGER._data["completed_feats"] = ["feat_arcimago"]
        with quiet(), mock.patch("roguelike.interactive_menu", return_value=0) as menu:
            roguelike._hero_selection()
        shown = " ".join(menu.call_args_list[-1][0][0])
        self.assertIn(GAME_DATA["meta"]["traits"]["erudito"]["name"], shown)
        self.assertNotIn(GAME_DATA["meta"]["traits"]["sordo_arcano"]["name"], shown)


if __name__ == "__main__":
    unittest.main()
