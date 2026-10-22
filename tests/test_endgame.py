"""Corruzione, finali multipli e Fuoco del Campo (personaggi, strutture, dono dello Scrittoio)."""
import copy
import io
import random
import re
import unittest
from contextlib import redirect_stdout
from unittest import mock

import camp
import codex
import endings
import events
import floor_map
import roguelike
from data_manager import GAME_DATA, PROFILE_MANAGER
from entities import Enemy, Player
from rooms import CombatSession

ANSI = re.compile(r"\x1b\[[0-9;]*m")
CFG = GAME_DATA["meta"]["corruption"]


def quiet():
    return redirect_stdout(io.StringIO())


def plain(text):
    return ANSI.sub("", text)


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        PROFILE_MANAGER._data["story"] = {"flags": {}, "counters": {}, "seen_events": {}}
        PROFILE_MANAGER._data["codex"] = {"enemies": {}, "letters": [], "relics": [], "reactions": []}
        PROFILE_MANAGER._data["essence"] = 1000
        self._save = mock.patch.object(PROFILE_MANAGER, "save")
        self._save.start()
        random.seed(9)

    def tearDown(self):
        self._save.stop()
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)

    def hero(self):
        with quiet():
            p = Player("1", "base", [])
        p.max_hp = p.hp = 400
        return p


class CorruptionTest(Sandbox):
    def test_bounds_and_attack_bonus(self):
        p = self.hero()
        atk = p.get_total_atk()
        self.assertEqual(p.add_corruption(35), 35)
        self.assertEqual(p.get_total_atk(), atk + 3 * CFG["atk_per_10"])
        self.assertEqual(p.add_corruption(500), CFG["max"] - 35)
        self.assertEqual(p.add_corruption(-1000), -CFG["max"])
        self.assertEqual(p.corruption, 0)

    def test_description_matches_the_rules(self):
        desc = CFG["desc"]
        self.assertIn(f"Ogni 10 punti danno +{CFG['atk_per_10']} ATK", desc)
        self.assertIn(f"Da {CFG['veil']['threshold']}", desc)
        self.assertIn(f"il {CFG['veil']['chance']}% delle volte non vedi gli effetti", desc)
        self.assertIn(f"Da {CFG['voice']['threshold']}", desc)
        self.assertIn(f"il {CFG['voice']['chance']}% delle volte non vedi la mossa", desc)

    def test_the_veil_hides_summaries_only_above_the_threshold(self):
        p = self.hero()
        scene = GAME_DATA["events"]["altare_sangue"]["scenes"]["inizio"]
        label = lambda: plain(events.visible_choices(p, scene, 3)[0][1])
        with mock.patch("events.random.random", return_value=0.0):
            p.corruption = CFG["veil"]["threshold"] - 1
            self.assertIn("+100 Oro", label())
            p.corruption = CFG["veil"]["threshold"]
            self.assertIn("il Labirinto ti offusca la vista", label())
        with mock.patch("events.random.random", return_value=0.99):
            self.assertIn("+100 Oro", label())

    def test_the_voice_hides_enemy_intents(self):
        p = self.hero()
        with quiet():
            s = CombatSession(p, 5, Enemy(5, False, []))
        p.corruption = CFG["voice"]["threshold"]
        with mock.patch("rooms.random.random", return_value=0.0):
            s.choose_intent()
        self.assertIn("???", plain(s.intent_text()))
        p.corruption = CFG["voice"]["threshold"] - 1
        with mock.patch("rooms.random.random", return_value=0.0):
            s.choose_intent()
        self.assertNotIn("???", plain(s.intent_text()))

    def test_forbidden_options_need_corruption(self):
        p = self.hero()
        scene = GAME_DATA["events"]["altare_sangue"]["scenes"]["inizio"]
        texts = lambda: [plain(l) for _, l, _ in events.visible_choices(p, scene, 3)]
        self.assertFalse(any("Offri l'anima" in t for t in texts()))
        p.corruption = 30
        with mock.patch("events.random.random", return_value=0.99):
            self.assertTrue(any(t.startswith("[Corruzione 30+] Offri l'anima") for t in texts()))

    def test_dark_and_pure_choices_exist(self):
        deltas = [e["corruption"] for ev in GAME_DATA["events"].values() for sc in ev["scenes"].values() for c in sc["choices"]
                  for effs in (c.get("effects", []), c.get("success", []), c.get("fail_effects", [])) for e in effs if "corruption" in e]
        self.assertGreaterEqual(sum(d > 0 for d in deltas), 10)
        self.assertGreaterEqual(sum(d < 0 for d in deltas), 4)

    def test_stats_show_corruption(self):
        p = self.hero()
        p.corruption = 80
        out = io.StringIO()
        with redirect_stdout(out), mock.patch("inventory_menu.wait_enter"), mock.patch("inventory_menu.clear_screen"):
            from inventory_menu import show_player_stats
            show_player_stats(p)
        text = plain(out.getvalue())
        self.assertIn("Corruzione: 80/100", text)
        self.assertIn("Sguardo Velato", text)
        self.assertIn("Voce del Labirinto", text)


class EndingsTest(Sandbox):
    def ids(self, p):
        return [e["id"] for e in endings.available_endings(p)]

    def test_endings_data(self):
        all_flags = {e["flag"] for ev in GAME_DATA["events"].values() for sc in ev["scenes"].values() for c in sc["choices"]
                     for effs in (c.get("effects", []), c.get("success", [])) for e in effs if "flag" in e}
        self.assertTrue(any(not e["requires"] for e in endings.endings()), "un finale è sempre disponibile")
        for e in endings.endings():
            with self.subTest(ending=e["id"]):
                self.assertTrue(e["title"] and e["hint"] and e["choice"] and e["text"])
                self.assertFalse(re.search(r"\d", e["choice"]))
                self.assertLessEqual(set(e["requires"]), set(events.CONDITIONS))
                for f in [e["requires"].get("flag")] + e["requires"].get("flags", []):
                    if f: self.assertIn(f, all_flags)

    def test_each_ending_opens_with_its_condition(self):
        p = self.hero()
        self.assertEqual(self.ids(p), ["sonno_spezzato"])
        p.corruption = 75
        self.assertIn("nuovo_dio", self.ids(p))
        PROFILE_MANAGER.set_flag("silas_verita")
        self.assertNotIn("aethelgard_rinasce", self.ids(p))
        PROFILE_MANAGER.set_flag("alaric_liberato")
        self.assertIn("aethelgard_rinasce", self.ids(p))
        PROFILE_MANAGER.set_flag("alaric_erede")
        self.assertIn("custode", self.ids(p))
        PROFILE_MANAGER.codex["letters"] = list(range(len(GAME_DATA["lore"]["letters"])))
        self.assertIn("lettera_mai_scritta", self.ids(p))
        self.assertEqual(len(self.ids(p)), len(endings.endings()))

    def test_choosing_an_ending_records_and_rewards_it(self):
        p = self.hero(); p.corruption = 80
        with quiet(), mock.patch("endings.interactive_menu", return_value=1), mock.patch("endings.wait_enter"), \
             mock.patch("endings.clear_screen"), mock.patch("endings.delay_print"):
            chosen = endings.choose_ending(p)
        self.assertEqual(chosen["id"], "nuovo_dio")
        self.assertEqual(p.essence_gathered, chosen["reward"]["essence"])
        self.assertEqual(PROFILE_MANAGER.story["endings"], {"nuovo_dio": 1})
        self.assertIn(("Finali", 1, len(endings.endings())), codex.sections())
        page = "\n".join(plain(l) for l in codex.endings_page())
        self.assertIn("Il Nuovo Dio", page)
        self.assertIn("??? — " + endings.endings()[0]["hint"], page)

    def test_victory_leads_to_the_ending(self):
        rooms = {n: mock.DEFAULT for n in ("combat_room", "vendor_room", "treasure_room", "trap_room", "campfire_room", "mystery_room", "event_room")}
        with quiet(), mock.patch("roguelike._hero_selection", return_value=("1", "base", [])), mock.patch("roguelike.interactive_menu", return_value=0), \
             mock.patch.multiple("roguelike", **rooms), mock.patch("roguelike.evaluate_run"), mock.patch("roguelike.wait_enter"), \
             mock.patch("roguelike.clear_screen"), mock.patch("roguelike.delay_print"), mock.patch("roguelike.time.sleep"), \
             mock.patch("roguelike._grant_victory_rewards"), mock.patch("roguelike.start_of_run_boon"), mock.patch("roguelike.choose_ending") as ending:
            roguelike.play_game()
        ending.assert_called_once()


class CampTest(Sandbox):
    def test_camp_data(self):
        for c in camp.camp()["characters"]:
            with self.subTest(character=c["id"]):
                self.assertLessEqual(set(c["requires"]), events.PROFILE_CONDITIONS)
                self.assertFalse(c["lines"][-1].get("requires"), "l'ultima frase è quella di riserva")
                for line in c["lines"]: self.assertLessEqual(set(line.get("requires", {})), events.PROFILE_CONDITIONS)
        for s in camp.camp()["structures"]:
            with self.subTest(structure=s["id"]):
                self.assertGreater(s["cost"], 0)
                self.assertLessEqual(set(s.get("requires", {})), events.PROFILE_CONDITIONS)
        altar = camp.structure("altare_purificazione")
        self.assertIn(f"{100 - altar['corruption_gain_pct']}% in meno", altar["desc"])

    def test_characters_arrive_with_the_story_and_give_once(self):
        self.assertEqual(camp.present_characters(), [])
        PROFILE_MANAGER.add_counter("silas", 2)
        silas = camp.present_characters()[0]
        self.assertIn("Silas scrive, come sempre", camp.current_line(silas))
        PROFILE_MANAGER.set_flag("silas_abbandonato")
        self.assertIn("Non ti devo niente", camp.current_line(silas))
        PROFILE_MANAGER.set_flag("silas_compagno")
        self.assertIn("ultima pagina", camp.current_line(silas))
        with quiet(), mock.patch("camp.wait_enter"), mock.patch("camp.clear_screen"), mock.patch("camp.delay_print"):
            camp.talk(silas)
            camp.talk(silas)
        self.assertEqual(PROFILE_MANAGER.essence, 1000 + silas["gift"]["essence"])

    def test_structures(self):
        tavolo = camp.structure("tavolo_cartografa")
        self.assertFalse(camp.can_build(tavolo))
        PROFILE_MANAGER.add_counter("cartografa_aiutata")
        self.assertTrue(camp.can_build(tavolo))
        PROFILE_MANAGER._data["essence"] = tavolo["cost"] - 1
        self.assertFalse(camp.build(tavolo))
        PROFILE_MANAGER._data["essence"] = tavolo["cost"]
        self.assertTrue(camp.build(tavolo))
        self.assertEqual(PROFILE_MANAGER.essence, 0)
        self.assertTrue(camp.built("tavolo_cartografa"))
        self.assertFalse(camp.build(tavolo), "si costruisce una volta sola")

    def test_cartographer_table_reveals_special_rooms(self):
        room = {"type": "event", "event_id": "voce_cara", "signature": True}
        biome = GAME_DATA["biomes"][0]
        self.assertNotIn("La Voce Cara", floor_map.room_label(room, biome=biome))
        PROFILE_MANAGER.set_flag("camp_tavolo_cartografa")
        self.assertIn("La Voce Cara", floor_map.room_label(room, biome=biome))
        self.assertNotIn("(", floor_map.room_label({"type": "event", "event_id": "voce_cara"}, biome=biome))

    def test_silas_desk_offers_a_boon(self):
        p = self.hero()
        with quiet(), mock.patch("camp.interactive_menu") as menu:
            camp.start_of_run_boon(p)
        menu.assert_not_called()
        PROFILE_MANAGER.set_flag("camp_scrittoio_silas")
        atk = p.bonus_atk_relic
        labels = []
        with quiet(), mock.patch("camp.interactive_menu", side_effect=lambda o, pr="": labels.extend(o) or 1):
            camp.start_of_run_boon(p)
        self.assertEqual(p.bonus_atk_relic, atk + 3)
        self.assertIn("La pagina della lama (+3 ATK)", [plain(l) for l in labels])

    def test_altar_reduces_corruption_gains(self):
        p = self.hero()
        PROFILE_MANAGER.set_flag("camp_altare_purificazione")
        pct = camp.structure("altare_purificazione")["corruption_gain_pct"]
        self.assertEqual(p.add_corruption(20), 20 * pct // 100)
        self.assertEqual(p.add_corruption(-5), -5, "i cali non vengono ridotti")

    def test_base_camp_opens_the_camp_fire(self):
        called = []
        with quiet(), mock.patch("roguelike.interactive_menu", side_effect=lambda o, p="", **k: 6 if not called else len(o) - 1), \
             mock.patch("roguelike.show_camp_fire", side_effect=lambda: called.append(1)), mock.patch("roguelike.clear_screen"):
            roguelike.base_camp()
        self.assertEqual(called, [1])

    def test_camp_fire_menu(self):
        PROFILE_MANAGER.add_counter("cartografa_aiutata")
        prompts = []
        with quiet(), mock.patch("camp.interactive_menu", side_effect=lambda o, p="", **k: prompts.append(o) or (1 if len(prompts) == 1 else -1)), \
             mock.patch("camp.wait_enter"), mock.patch("camp.clear_screen"):
            camp.show_camp_fire()
        self.assertTrue(plain(prompts[0][0]).startswith("Parla con La Cartografa"))
        self.assertTrue(camp.built("tavolo_cartografa"))


if __name__ == "__main__":
    unittest.main()
