"""Mappa del piano (file collegate, percorsi, disegno) e biomi (I Chiostri del Rimpianto)."""
import copy
import io
import random
import re
import unittest
from contextlib import redirect_stdout
from unittest import mock

import events
import floor_map
import roguelike
from data_manager import GAME_DATA, PROFILE_MANAGER, RAW_DATA, get_biome
from entities import Player, pick_enemy_name
from ui import visible_width

ANSI = re.compile(r"\x1b\[[0-9;]*m")
WEIGHTS = GAME_DATA["meta"]["rooms"]["weights"]
COOLDOWNS = GAME_DATA["meta"]["rooms"]["cooldowns"]


def quiet():
    return redirect_stdout(io.StringIO())


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        PROFILE_MANAGER._data["story"] = {"flags": {}, "counters": {}, "seen_events": {}}
        self._save = mock.patch.object(PROFILE_MANAGER, "save")
        self._save.start()
        random.seed(11)

    def tearDown(self):
        self._save.stop()
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)

    def hero(self):
        with quiet():
            return Player("1", "base", [])

    def make(self, floor=8, player=None, weights=None, cooldowns=None):
        w = weights or WEIGHTS
        return floor_map.generate_floor_map(floor, w, COOLDOWNS if cooldowns is None else cooldowns, {k: 0 for k in w}, [], player)


class MapStructureTest(Sandbox):
    def test_rows_alternate_and_end_with_the_boss(self):
        for _ in range(100):
            rows = self.make()
            sizes = [len(r) for r in rows[:-1]]
            self.assertIn(sizes, ([2, 3, 2, 3], [3, 2, 3, 2]))
            self.assertEqual([d["type"] for d in rows[-1]], ["boss"])

    def test_every_room_is_reachable_and_paths_never_cross(self):
        for _ in range(100):
            rows = self.make()
            for r in range(len(rows) - 1):
                incoming = set()
                for d in rows[r]:
                    self.assertTrue(d["links"], "nessun vicolo cieco")
                    incoming |= set(d["links"])
                self.assertEqual(incoming, set(range(len(rows[r + 1]))))
                for a, b in zip(rows[r], rows[r][1:]):
                    self.assertLessEqual(max(a["links"]), min(b["links"]))

    def test_rooms_in_a_row_differ_and_respect_forbidden_pairs(self):
        for _ in range(200):
            for row in self.make()[:-1]:
                types = [d["type"] for d in row if not d.get("fated") and not d.get("signature")]
                others = [t for t in types if t != "combat"]
                self.assertEqual(len(others), len(set(others)), "solo lo scontro può ripetersi")
                for pair in floor_map.FORBIDDEN: self.assertFalse(pair <= set(types))

    def test_cooldowns_hold_across_the_rows_of_a_floor(self):
        for _ in range(100):
            rows = self.make(cooldowns={"vendor": 10, "campfire": 10})
            types = [d["type"] for row in rows for d in row]
            self.assertLessEqual(types.count("vendor"), 1)
            self.assertLessEqual(types.count("campfire"), 1)

    def test_reachable_follows_the_links(self):
        rows = self.make()
        self.assertEqual(floor_map.reachable(rows, 1, None), list(range(len(rows[0]))))
        self.assertEqual(floor_map.reachable(rows, 2, rows[0][0]), rows[0][0]["links"])

    def test_fated_event_takes_a_room_of_the_first_row(self):
        p = self.hero(); p.pending_events = [[8, "cartografa_ritorno"]]
        rows = self.make(player=p)
        fated = [d for d in rows[0] if d.get("fated")]
        self.assertEqual([d["event_id"] for d in fated], ["cartografa_ritorno"])
        self.assertIn("qualcosa ti stava aspettando", floor_map.room_label(fated[0]))


class RenderTest(Sandbox):
    def test_map_drawing(self):
        rows = self.make()
        first = floor_map.render_map(rows, 1, [])
        self.assertEqual(len(first), 9)
        self.assertTrue(first[-1].strip().startswith("★"))
        self.assertTrue(all(visible_width(l) <= 60 for l in first), "la mappa sta in un terminale stretto")
        path = [0, rows[0][0]["links"][0]]
        drawn = floor_map.render_map(rows, 3, path)
        self.assertIn("\033[92m", drawn[0])  # il percorso fatto è verde
        self.assertTrue(any(ch in ANSI.sub("", "".join(drawn)) for ch in "│╱╲"))

    def test_labels_are_centered_and_links_join_the_centers(self):
        for tall in (False, True):
            rows = self.make()
            lines = [ANSI.sub("", l)[5:] for l in floor_map.render_map(rows, 1, [], tall=tall)]
            per_row = 3 if tall else 2
            self.assertEqual(len(lines), 5 + 4 * (per_row - 1))
            for r, row in enumerate(rows):
                text = lines[r * per_row]
                for d in row:
                    label = floor_map._short(d, None)
                    start = text.index(label)
                    width = visible_width(text[:start] + label) - visible_width(text[:start])
                    center = visible_width(text[:start]) + width // 2
                    self.assertLessEqual(abs(center - floor_map._center(d["slot"])), 1, label)
                if r == len(rows) - 1: break
                for d in row:
                    for j in d["links"]:
                        a, b = floor_map._center(d["slot"]), floor_map._center(rows[r + 1][j]["slot"])
                        for k in range(per_row - 1):
                            x = a + (b - a) * (k + 1) // per_row
                            self.assertEqual(lines[r * per_row + 1 + k][x], "│" if a == b else ("╲" if b > a else "╱"))

    def test_sixth_sense_reveals_what_is_behind(self):
        rows = self.make()
        combat = next(d for row in rows for d in row if d["type"] in ("combat", "boss"))
        self.assertIn(combat["enemy"].name, floor_map.room_label(combat, sixth_sense=True))
        self.assertNotIn(combat["enemy"].name, floor_map.room_label(combat))

    def test_real_floor_loop_walks_a_legal_path(self):
        visited = []

        def menu(options, prompt="", **kw):
            visited.append(prompt)
            return 0

        rooms = {n: mock.DEFAULT for n in ("vendor_room", "treasure_room", "trap_room", "campfire_room", "mystery_room", "event_room")}
        bosses = []
        with quiet(), mock.patch("roguelike._hero_selection", return_value=("1", "base", [])), mock.patch("roguelike.interactive_menu", side_effect=menu), \
             mock.patch("roguelike.combat_room", side_effect=lambda p, f, e: bosses.append((f, e.is_boss))), mock.patch.multiple("roguelike", **rooms), \
             mock.patch("roguelike.evaluate_run"), mock.patch("roguelike.wait_enter"), mock.patch("roguelike.clear_screen"), \
             mock.patch("roguelike.delay_print"), mock.patch("roguelike.time.sleep"), mock.patch("roguelike._grant_victory_rewards"), mock.patch("roguelike.choose_ending"), mock.patch("roguelike.start_of_run_boon"), \
             mock.patch("roguelike.reachable", wraps=floor_map.reachable) as reach:
            roguelike.play_game()
        self.assertEqual(len(visited), 30 * 5)
        self.assertEqual(sum(1 for _, boss in bosses if boss), 30)
        self.assertEqual(reach.call_count, 30 * 5)
        self.assertIn("I Chiostri del Rimpianto", ANSI.sub("", visited[0]))
        self.assertIn("★", visited[0])


class BiomeTest(Sandbox):
    def test_biomes_cover_the_descent(self):
        ids = [get_biome(f)["id"] for f in range(1, 31)]
        self.assertEqual(ids[:5], ["chiostri"] * 5)
        self.assertEqual(len(set(ids)), len(GAME_DATA["biomes"]))
        self.assertIsNone(get_biome(31))

    def test_biome_data_is_consistent(self):
        biome_ids = {b["id"] for b in GAME_DATA["biomes"]}
        for b in GAME_DATA["biomes"]:
            with self.subTest(biome=b["id"]):
                self.assertTrue(b["intro"])
                for ev in b.get("signature_events", []):
                    self.assertTrue(GAME_DATA["events"][ev].get("scripted"), ev)
                if b.get("signature_events"): self.assertIn("name", b["hazard"])
                self.assertLessEqual(set(b.get("room_weights", {})), set(WEIGHTS))
                self.assertLessEqual(set(b.get("enemy_elements", {})), set(GAME_DATA["elements"]["list"]))
        for cat in ("enemies", "bosses"):
            for name, d in RAW_DATA[cat].items():
                if "biome" in d: self.assertIn(d["biome"], biome_ids, name)

    def test_natives_live_only_in_their_biome(self):
        early = {pick_enemy_name(f, False) for f in range(1, 6) for _ in range(80)}
        late = {pick_enemy_name(f, False) for f in range(6, 31) for _ in range(40)}
        self.assertTrue({"Eco del Rimpianto", "Statua di Sale"} <= early)
        self.assertFalse({"Eco del Rimpianto", "Statua di Sale"} & late)
        self.assertIn("La Badessa del Silenzio", {pick_enemy_name(f, True) for f in range(1, 6) for _ in range(60)})
        self.assertNotIn("La Badessa del Silenzio", {pick_enemy_name(f, True) for f in range(6, 31) for _ in range(20)})

    def test_elements_of_the_biome_are_more_common(self):
        def share(biome):
            with mock.patch("entities.get_biome", return_value=biome):
                picks = [pick_enemy_name(3, False) for _ in range(3000)]
            elements = [RAW_DATA["enemies"][n]["element"] for n in picks]
            return sum(e in ("Luce", "Tenebra") for e in elements) / len(elements)
        chiostri = get_biome(3)
        self.assertGreater(share(chiostri), share({"id": "nessuno"}) + 0.1)

    def test_room_weights_of_the_biome(self):
        def traps(floor):
            return sum(d["type"] == "trap" for _ in range(300) for row in self.make(floor, weights=WEIGHTS, cooldowns={})[:-1] for d in row)
        self.assertLess(traps(3), traps(8) * 0.8)

    def test_every_floor_has_the_special_room_of_its_biome(self):
        for floor in range(1, 31):
            biome = get_biome(floor)
            with self.subTest(floor=floor):
                rows = self.make(floor, player=self.hero())
                special = [(r, d) for r, row in enumerate(rows) for d in row if d.get("signature")]
                self.assertEqual(len(special), 1)
                r, d = special[0]
                self.assertIn(r, (1, 2, 3))
                self.assertIn(d["event_id"], biome["signature_events"])
                self.assertIn(biome["hazard"]["name"], floor_map.room_label(d, biome=biome))
        self.assertFalse(any(d.get("signature") for row in self.make(31) for d in row))

    def test_special_rooms_rotate_within_a_run(self):
        p = self.hero()
        p.seen_events = {"voce_cara", "statua_sale"}
        rows = self.make(2, player=p)
        self.assertEqual([d["event_id"] for row in rows for d in row if d.get("signature")], ["biblioteca_cenere"])

    def test_the_first_stone_is_on_floor_three_and_remembered(self):
        self.assertTrue(events.is_available("prima_pietra", 3))
        self.assertFalse(events.is_available("prima_pietra", 2))
        self.assertFalse(events.is_available("prima_pietra", 8))
        p = self.hero()
        scene = GAME_DATA["events"]["prima_pietra"]["scenes"]["inizio"]
        texts = lambda: [c["text"] for c, _, _ in events.visible_choices(p, scene, 3)]
        self.assertIn("Solleva la lastra", texts())
        PROFILE_MANAGER.set_flag("prima_pietra")
        self.assertNotIn("Solleva la lastra", texts())
        self.assertIn("Posa la mano dove c'era la pietra", texts())
        self.assertIn("Da te.", events.scene_text(p, scene, 3))

    def test_entering_a_biome_announces_its_hazard(self):
        out = io.StringIO()
        with redirect_stdout(out), mock.patch("roguelike._hero_selection", return_value=("1", "base", [])), \
             mock.patch("roguelike.interactive_menu", side_effect=lambda o, p="", **k: len(o) - 1), \
             mock.patch("roguelike.evaluate_run"), mock.patch("roguelike.wait_enter"), mock.patch("roguelike.clear_screen"), \
             mock.patch("roguelike.delay_print", side_effect=lambda t, d=0: print(t)), mock.patch("roguelike.time.sleep"):
            roguelike.play_game()  # al primo bivio si fugge
        text = ANSI.sub("", out.getvalue())
        self.assertIn("I CHIOSTRI DEL RIMPIANTO", text)
        self.assertIn("Pericolo: Nostalgia Letale.", text)


if __name__ == "__main__":
    unittest.main()
