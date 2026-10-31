"""Grimori e magia fuori dal combattimento: pergamene (bottino, Mercante, Forgia), apprendimento e posti,
cure dallo zaino, Medita al Falò e gli effetti nuovi degli incantesimi."""
import copy
import io
import random
import re
import unittest
from contextlib import redirect_stdout
from unittest import mock

import inventory_menu
import magic
import roguelike
import rooms
from data_manager import GAME_DATA, PROFILE_MANAGER, RAW_DATA
from entities import Armor, Enemy, Player, Scroll, Weapon, generate_scroll
from rooms import CombatSession
from rooms_patch import patch_rooms

ANSI = re.compile(r"\x1b\[[0-9;]*m")
SPELLS, RULES = GAME_DATA["spells"]["spells"], GAME_DATA["spells"]["rules"]
LOCKED = {sid for sid, s in SPELLS.items() if s.get("unlock_id")}


def quiet():
    return redirect_stdout(io.StringIO())


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        self._save = mock.patch.object(PROFILE_MANAGER, "save")
        self._save.start()
        PROFILE_MANAGER._data["unlocked_ids"] = [u for u in PROFILE_MANAGER._data["unlocked_ids"] if not u.startswith("pergamena_")]
        random.seed(9)

    def tearDown(self):
        self._save.stop()
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)

    def hero(self, spells=("raffica",), ether=100):
        with quiet(): p = Player("1", "base", [])
        for a in p.attributes: p.attributes[a] = 0
        p.spells, p.base_ether, p.ether = list(spells), 100, ether
        p.max_hp, p.hp = 1000, 500
        return p

    def fight(self, p, boss=False):
        p.weapon, p.armor = Weapon("Lama", 1, 100, "Normale", 1), Armor("Corazza", 1, 40, "Normale", 1)
        with quiet(): s = CombatSession(p, 3, Enemy(3, boss, [], name="Re dei Goblin" if boss else "Goblin"))
        s.enemy.hp = s.enemy.max_hp = 10 ** 6
        s.enemy.element, s.enemy.base_dodge, s.enemy.base_acc, s.intent = "Normale", 0, 1000, "attack"
        return s

    def cast(self, s, sid):
        with quiet(), patch_rooms("wait_enter"): return s.cast_spell(sid)


class DataTest(Sandbox):
    def test_the_rules_text_tells_the_numbers(self):
        d = RULES["scroll_desc"]
        self.assertIn(f"al massimo {RULES['slots']}", d)
        names = {"boss": "boss", "elite": "Élite", "mimic": "Mimic", "mystery_hoard": "Mistero", "trap": "trappole"}
        for source, pct in RULES["drops"].items():
            with self.subTest(source=source):
                self.assertIn(names[source], d)
                self.assertIn(f"({pct}%)", d)
        self.assertIn("Mercante", d)
        self.assertGreaterEqual(len(SPELLS), 18)


class ScrollTest(Sandbox):
    def test_locked_spells_are_not_found_until_the_forge(self):
        self.assertTrue(LOCKED)
        self.assertFalse(LOCKED & set(magic.available()))
        found = {generate_scroll(5).spell_id for _ in range(400)}
        self.assertFalse(found & LOCKED)
        sid = sorted(LOCKED)[0]
        PROFILE_MANAGER.unlocked_ids.append(SPELLS[sid]["unlock_id"])
        self.assertIn(sid, magic.available())

    def test_the_forge_sells_locked_spells(self):
        self.assertEqual({i["name"] for i in roguelike.locked_forge_items("spells")}, {SPELLS[s]["name"] for s in LOCKED})

    def test_sources_drop_scrolls_with_their_chance(self):
        p = self.hero()
        for source, pct in RULES["drops"].items():
            with self.subTest(source=source):
                p.inventory = []
                with quiet(), mock.patch("magic.random.random", return_value=(pct - 0.5) / 100), mock.patch("rooms.rune_rules.roll_drop", return_value=False):
                    rooms.rune_drop(p, 4, source)
                self.assertEqual([i.type for i in p.inventory], ["scroll"])
        p.inventory = []
        with quiet(), mock.patch("magic.random.random", return_value=0.0): rooms.scroll_drop(p, 4, "nessuna_fonte")
        self.assertEqual(p.inventory, [])

    def test_the_vendor_sells_a_scroll(self):
        p = self.hero(); seen = []
        with quiet(), patch_rooms("interactive_menu", side_effect=lambda o, pr="", **k: seen.append(o) or (0 if len(seen) == 1 else -1 if len(seen) == 2 else 2)), \
             patch_rooms("clear_screen"), patch_rooms("delay_print"), patch_rooms("wait_enter"):
            rooms.vendor_room(p, 3)
        self.assertTrue(any("Pergamena" in ANSI.sub("", o) for o in seen[1]))


class LearnTest(Sandbox):
    def read(self, p, scroll, pick=None):
        with quiet(), mock.patch("inventory_menu.wait_enter"), mock.patch("inventory_menu.interactive_menu", return_value=pick):
            inventory_menu.learn_scroll(p, scroll)

    def test_a_free_slot_learns_and_a_known_spell_stays(self):
        p = self.hero(("raffica",)); s = Scroll("frana"); p.inventory = [s]
        self.read(p, s)
        self.assertEqual((p.spells, p.inventory), (["raffica", "frana"], []))
        s2 = Scroll("frana"); p.inventory = [s2]
        self.read(p, s2)
        self.assertEqual(p.inventory, [s2], "la conosci già: la pergamena resta")

    def test_full_slots_ask_what_to_forget(self):
        p = self.hero(("raffica", "frana", "dardo_fuoco")); s = Scroll("lancia_luce"); p.inventory = [s]
        self.read(p, s, pick=3)
        self.assertEqual((p.spells, p.inventory), (["raffica", "frana", "dardo_fuoco"], [s]), "tenerla per dopo non cambia niente")
        self.read(p, s, pick=1)
        self.assertEqual((p.spells, p.inventory), (["raffica", "lancia_luce", "dardo_fuoco"], []))

    def test_scrolls_are_not_read_in_combat(self):
        p = self.hero(); s = Scroll("frana"); p.inventory = [s]
        picks = iter([0, 1])
        with quiet(), mock.patch("inventory_menu.interactive_menu", side_effect=lambda *a, **k: next(picks)), \
             mock.patch("inventory_menu.clear_screen"), mock.patch("inventory_menu.wait_enter"):
            inventory_menu.show_inventory_menu(p, in_combat=True)
        self.assertEqual((p.spells, p.inventory), (["raffica"], [s]))


class OutsideTest(Sandbox):
    def test_only_healing_spells_from_the_backpack_and_never_in_combat(self):
        p = self.hero(("luce_guaritrice", "raffica", "purificazione"))
        self.assertEqual(magic.castable_outside(p), ["luce_guaritrice", "purificazione"])
        seen = []
        for in_combat in (False, True):
            with quiet(), mock.patch("inventory_menu.interactive_menu", side_effect=lambda o, pr="": seen.append(o) or len(o) - 1), \
                 mock.patch("inventory_menu.clear_screen"):
                inventory_menu.show_inventory_menu(p, in_combat=in_combat)
        self.assertEqual(sum(o.startswith("[Incantesimo]") for o in seen[0]), 2)
        self.assertFalse(any(o.startswith("[Incantesimo]") for o in seen[1]))

    def test_casting_outside_heals_cleanses_and_costs_ether(self):
        p = self.hero(("purificazione",)); p.statuses.update(poison=3, bleed=2)
        msg = magic.cast_outside(p, "purificazione")
        self.assertEqual((p.statuses, p.hp, p.ether), ({}, 500 + 1000 * SPELLS["purificazione"]["effects"]["heal_pct"] // 100, 100 - SPELLS["purificazione"]["cost"]))
        self.assertIn("Veleno", msg)
        p.ether = 0
        self.assertIn("Non hai abbastanza Etere", magic.cast_outside(p, "purificazione"))
        self.assertEqual(p.ether, 0)

    def test_meditating_at_the_campfire(self):
        p = self.hero(ether=0); seen = []
        with quiet(), patch_rooms("interactive_menu", side_effect=lambda o, pr="": seen.append(o) or next(i for i, x in enumerate(o) if "Medita" in x)), \
             patch_rooms("clear_screen"), patch_rooms("delay_print"), patch_rooms("wait_enter"):
            rooms.campfire_room(p, 3)
        self.assertEqual(p.ether, p.max_ether())
        self.assertEqual(len(seen), 1, "il falò si spegne")
        p = self.hero(spells=()); seen = []
        with quiet(), patch_rooms("interactive_menu", side_effect=lambda o, pr="": seen.append(o) or len(o) - 1), \
             patch_rooms("clear_screen"), patch_rooms("delay_print"), patch_rooms("wait_enter"):
            rooms.campfire_room(p, 3)
        self.assertFalse(any("Medita" in x for x in seen[0]), "senza incantesimi non si medita")


class NewEffectsTest(Sandbox):
    def hit(self, s):
        with quiet(), mock.patch("rooms.random.randint", side_effect=lambda a, b: a), patch_rooms("wait_enter"):
            s.enemy_turn()

    def test_stone_skin_and_curse(self):
        p = self.hero(("pelle_pietra", "maledizione")); s = self.fight(p)
        s.enemy.atk = 200
        before = s.estimate_enemy_damage()
        self.cast(s, "pelle_pietra")
        self.assertEqual(s.spell_def, 40 * SPELLS["pelle_pietra"]["effects"]["def_pct"] // 100)
        self.assertEqual(s.estimate_enemy_damage(), max(1, before - s.spell_def))
        self.cast(s, "maledizione")
        self.assertEqual(s.enemy.atk, 200 * (100 - SPELLS["maledizione"]["effects"]["weaken_pct"]) // 100)
        with quiet(), patch_rooms("interactive_menu", return_value=1), patch_rooms("clear_screen"):
            self.assertIsNone(s.choose_spell(), "una sola Maledizione per nemico")

    def test_wind_step_flees_but_not_from_bosses(self):
        p = self.hero(("passo_vento",)); s = self.fight(p)
        self.assertFalse(self.cast(s, "passo_vento"))
        self.assertEqual(p.run_tracker["escapes"], 1)
        p = self.hero(("passo_vento",)); s = self.fight(p, boss=True)
        with quiet(), patch_rooms("interactive_menu", return_value=0), patch_rooms("clear_screen"):
            self.assertIsNone(s.choose_spell())
        self.assertEqual(p.ether, 100, "rifiutato senza spendere Etere")

    def test_frost_grip_and_blaze(self):
        p = self.hero(("morsa_ghiaccio", "vampa")); s = self.fight(p)
        self.cast(s, "morsa_ghiaccio")
        self.assertEqual(s.enemy.statuses.get("stun"), 1)
        s.enemy.mark = None
        self.cast(s, "vampa")
        self.assertEqual(s.enemy.statuses.get("scorch"), SPELLS["vampa"]["effects"]["status"]["duration"])

    def test_cleansing_in_combat(self):
        p = self.hero(("marea_curativa",)); s = self.fight(p); p.statuses.update(poison=2)
        self.cast(s, "marea_curativa")
        self.assertNotIn("poison", p.statuses)
        self.assertEqual(p.hp, 500 + 1000 * SPELLS["marea_curativa"]["effects"]["heal_pct"] // 100)


if __name__ == "__main__":
    unittest.main()
