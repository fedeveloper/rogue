"""Motore degli eventi: integrità dei dati, opzioni condizionate, scene a più passi e memoria del Labirinto."""
import copy
import io
import random
import re
import unittest
from contextlib import redirect_stdout
from unittest import mock

import events
import roguelike
from data_manager import GAME_DATA, PROFILE_MANAGER, RAW_DATA
from entities import Player

EVENT_KEYS = {"title", "start", "scenes", "requires", "scripted", "weight"}
SCENE_KEYS = {"text", "choices", "extra"}
CHOICE_KEYS = {"text", "requires", "effects", "chance", "success", "fail_effects", "msg", "fail_msg", "next", "fail_next",
               "hidden", "show_locked", "locked_hint"}
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def quiet():
    return redirect_stdout(io.StringIO())


def all_choices():
    for ev_id, ev in GAME_DATA["events"].items():
        for sc_id, scene in ev["scenes"].items():
            for choice in scene["choices"]:
                yield ev_id, sc_id, choice


def effect_lists(choice):
    return [choice.get("effects", []), choice.get("success", []), choice.get("fail_effects", [])]


def all_effects():
    for ev_id, sc_id, choice in all_choices():
        for effs in effect_lists(choice):
            for eff in effs:
                yield ev_id, eff


def all_requires():
    for ev_id, ev in GAME_DATA["events"].items():
        yield ev_id, ev.get("requires", {})
        for scene in ev["scenes"].values():
            for extra in scene.get("extra", []): yield ev_id, extra.get("requires", {})
            for choice in scene["choices"]: yield ev_id, choice.get("requires", {})


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        PROFILE_MANAGER._data["story"] = {"flags": {}, "counters": {}, "seen_events": {}}
        PROFILE_MANAGER._data["npc_unlocked"] = {}
        self._save = mock.patch.object(PROFILE_MANAGER, "save")
        self.save = self._save.start()
        random.seed(7)

    def tearDown(self):
        self._save.stop()
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)

    def hero(self, cls="1", trait="base"):
        with quiet():
            p = Player(cls, trait, [])
        p.max_hp = p.hp = 300
        p.gold = 300
        return p

    def labels(self, p, ev_id, scene="inizio", floor=10):
        return [(ANSI.sub("", label), ok) for _, label, ok in events.visible_choices(p, GAME_DATA["events"][ev_id]["scenes"][scene], floor)]


class EventDataTest(Sandbox):
    def test_structure_uses_only_known_keys(self):
        for ev_id, ev in GAME_DATA["events"].items():
            with self.subTest(event=ev_id):
                self.assertLessEqual(set(ev), EVENT_KEYS)
                self.assertIn(ev["start"], ev["scenes"])
                for scene in ev["scenes"].values():
                    self.assertLessEqual(set(scene), SCENE_KEYS)
                    self.assertTrue(scene["choices"])
                    for choice in scene["choices"]: self.assertLessEqual(set(choice), CHOICE_KEYS, choice["text"])

    def test_conditions_and_effects_are_known_and_valid(self):
        relics = {r["id"] for r in RAW_DATA["relics"]}
        story = GAME_DATA["story"]
        for ev_id, req in all_requires():
            with self.subTest(event=ev_id, requires=req):
                self.assertLessEqual(set(req), set(events.CONDITIONS))
                for c in events._as_list(req.get("class", [])): self.assertIn(c, GAME_DATA["classes"])
                for t in events._as_list(req.get("trait", [])): self.assertIn(t, GAME_DATA["meta"]["traits"])
                if "relic" in req: self.assertIn(req["relic"], relics)
                if "quest_item" in req: self.assertIn(req["quest_item"], story["quest_items"])
                if "pact" in req: self.assertIn(req["pact"], GAME_DATA["meta"]["pacts"])
                if "biome" in req: self.assertIn(req["biome"], {b["id"] for b in GAME_DATA["biomes"]})
                for k in ("npc", "not_npc"):
                    if k in req: self.assertIn(req[k], story["npcs"])
        for ev_id, eff in all_effects():
            with self.subTest(event=ev_id, effect=eff):
                key = events.effect_key(eff)
                self.assertIn(key, events.EFFECTS)
                self.assertEqual([k for k in eff if k not in events.EFFECT_PARAMS], [key], "un solo effetto per voce")
                v = eff[key]
                if key == "relic": self.assertTrue(v == "random" or v in relics)
                if key in ("weapon", "armor"): self.assertIn(v, ("epic", "normal"))
                if key == "fight": self.assertIn(v, events.FIGHTS)
                if key in ("quest_item", "take_quest_item"): self.assertIn(v, story["quest_items"])
                if key == "unlock_npc": self.assertIn(v, story["npcs"])
                if key == "later": self.assertTrue(GAME_DATA["events"][v].get("scripted"), f"{v} deve essere scripted")
                if key in ("gold", "damage", "heal", "heal_pct", "max_hp", "atk", "def", "exp", "essence", "potion"):
                    self.assertIsInstance(v, int)
                if key in ("damage", "heal", "heal_pct", "exp", "essence", "potion"): self.assertGreater(v, 0)

    def test_every_scene_is_reachable_and_every_link_exists(self):
        for ev_id, ev in GAME_DATA["events"].items():
            seen, todo = set(), [ev["start"]]
            while todo:
                sc = todo.pop()
                if sc in seen: continue
                seen.add(sc)
                for choice in ev["scenes"][sc]["choices"]:
                    for link in (choice.get("next"), choice.get("fail_next")):
                        if link:
                            self.assertIn(link, ev["scenes"], f"{ev_id}: scena inesistente {link}")
                            todo.append(link)
            self.assertEqual(seen, set(ev["scenes"]), f"{ev_id}: scene irraggiungibili")

    def test_every_scene_always_offers_a_way_forward(self):
        # Nessun vicolo cieco: almeno una scelta senza requisiti e senza costo in oro
        for ev_id, ev in GAME_DATA["events"].items():
            for sc_id, scene in ev["scenes"].items():
                with self.subTest(scene=f"{ev_id}/{sc_id}"):
                    self.assertTrue(any(not c.get("requires") and not events.gold_cost(c) for c in scene["choices"]))

    def test_every_key_item_flag_and_scripted_event_is_reachable(self):
        given = {eff["quest_item"] for _, eff in all_effects() if "quest_item" in eff}
        flags = {eff["flag"] for _, eff in all_effects() if "flag" in eff}
        counters = {eff["counter"] for _, eff in all_effects() if "counter" in eff}
        called = {eff["later"] for _, eff in all_effects() if "later" in eff}
        called |= {e for b in GAME_DATA["biomes"] for e in b.get("signature_events", [])}  # stanze speciali dei biomi
        for ev_id, req in all_requires():
            with self.subTest(event=ev_id, requires=req):
                if "quest_item" in req: self.assertIn(req["quest_item"], given)
                for k in ("flag", "not_flag"):
                    if k in req: self.assertIn(req[k], flags)
                for name in req.get("counter", {}): self.assertIn(name, counters)
        for ev_id, ev in GAME_DATA["events"].items():
            if ev.get("scripted"): self.assertIn(ev_id, called, f"{ev_id} non viene mai richiamato")
        used = {req["quest_item"] for _, req in all_requires() if "quest_item" in req}
        self.assertEqual(used, set(GAME_DATA["story"]["quest_items"]), "ogni oggetto chiave deve servire a qualcosa")


class ChoiceVisibilityTest(Sandbox):
    def test_class_option_is_tagged_and_only_for_that_class(self):
        mage = self.labels(self.hero("3"), "viandante_cieco")
        warrior = self.labels(self.hero("1"), "viandante_cieco")
        self.assertIn(("[Mago] Riaccendi la lanterna con un incantesimo", True), mage)
        self.assertFalse(any("lanterna" in label for label, _ in warrior))

    def test_trait_and_relic_options(self):
        midas = self.hero(trait="midas")
        self.assertTrue(any(l.startswith("[Tocco di Mida]") for l, _ in self.labels(midas, "pozzo_desideri")))
        self.assertFalse(any("Mida" in l for l, _ in self.labels(self.hero(), "pozzo_desideri")))
        p = self.hero()
        with quiet(): p.add_relic(next(r for r in RAW_DATA["relics"] if r["id"] == "occhio_cacciatore"))
        self.assertTrue(any(l.startswith("[Occhio del Cacciatore]") for l, _ in self.labels(p, "voce_nel_buio")))

    def test_locked_options_are_shown_but_not_selectable(self):
        p = self.hero()
        self.assertIn(("Apri la porta (Ti serve una chiave)", False), self.labels(p, "porta_sigillata"))
        p.quest_items.append("chiave_arrugginita")
        self.assertIn(("[Chiave Arrugginita] Apri la porta (Arma Epica; +200 Oro)", True), self.labels(p, "porta_sigillata"))
        p.gold = 10
        self.assertIn(("Lancia una moneta (-20 Oro; 50%: Reliquia) (Oro insufficiente)", False), self.labels(p, "fontana_fatata"))

    def test_summary_is_generated_from_effects(self):
        p = self.hero()
        self.assertIn(("Prega l'Oscurità (+100 Oro; -40 HP; +10 Corruzione)", True), self.labels(p, "altare_sangue"))
        self.assertIn(("Arretra lentamente (50%: -25 HP)", True), self.labels(p, "voce_nel_buio", "tana"))
        self.assertIn(("Ricchezza (50%: +120 Oro)", True), self.labels(p, "pozzo_desideri", "desiderio"))


class EventRoomTest(Sandbox):
    def play(self, p, ev_id, picks, floor=10, combat=None):
        with quiet(), mock.patch("events.interactive_menu", side_effect=picks), mock.patch("events.wait_enter"), \
             mock.patch("events.clear_screen"), mock.patch("events.delay_print"), \
             mock.patch("events.combat_room", side_effect=combat or (lambda pl, f, e: setattr(e, "hp", 0))):
            events.event_room(p, ev_id, floor)

    def test_multi_step_event(self):
        p = self.hero()
        self.play(p, "pozzo_desideri", [0, 0])  # getta la moneta -> chiedi forza
        self.assertEqual(p.gold, 270)
        self.assertEqual(p.bonus_atk_relic, 3)
        self.assertIn("pozzo_desideri", p.seen_events)
        self.assertEqual(events.times_seen("pozzo_desideri"), 1)
        self.save.assert_called()

    def test_locked_pick_is_ignored_until_a_valid_one(self):
        p = self.hero(); items = len(p.inventory)
        self.play(p, "porta_sigillata", [0, 2])  # la porta chiusa non si apre: si sceglie "Ignora"
        self.assertEqual((len(p.inventory), p.gold), (items, 300))

    def test_fleeing_a_fight_forfeits_the_reward(self):
        p = self.hero()
        self.play(p, "speziale_prigioniero", [1], combat=lambda pl, f, e: None)  # il nemico resta vivo: fuga
        self.assertFalse(PROFILE_MANAGER.get_npc_unlocked("speziale"))
        self.play(p, "speziale_prigioniero", [1])
        self.assertTrue(PROFILE_MANAGER.get_npc_unlocked("speziale"))

    def test_death_stops_the_event(self):
        p = self.hero(); p.hp = 10
        self.play(p, "speziale_prigioniero", [0])
        self.assertLessEqual(p.hp, 0)
        self.assertFalse(PROFILE_MANAGER.get_npc_unlocked("speziale"))

    def test_relic_fallback_when_all_owned(self):
        p = self.hero()
        with mock.patch("events.get_random_relic", return_value=None):
            self.play(p, "forgia_abissale", [1])
        self.assertEqual(p.gold, 300 + events.RELIC_FALLBACK_GOLD)


class MemoryTest(Sandbox):
    def test_the_labyrinth_remembers_between_runs(self):
        first = self.hero("3")
        EventRoomTest.play(self, first, "viandante_cieco", [0, 1])  # [Mago] lanterna -> rifiuta
        second = self.hero("1")  # nuova run, altra classe
        text = events.scene_text(second, GAME_DATA["events"]["viandante_cieco"]["scenes"]["inizio"], 1)
        self.assertIn("ci siamo già incontrati", text)

    def test_delayed_consequence_comes_back_floors_later(self):
        p = self.hero()
        EventRoomTest.play(self, p, "cartografa_perduta", [0], floor=4)
        self.assertEqual(p.pending_events, [[7, "cartografa_ritorno"]])
        self.assertIsNone(events.pop_due_event(p, 6))
        self.assertEqual(events.pop_due_event(p, 7), "cartografa_ritorno")
        self.assertEqual(p.pending_events, [])

    def test_delayed_event_takes_a_door_in_the_real_floor_loop(self):
        heroes, visited = [], []

        def hero(*args):
            p = Player(*args); p.pending_events = [[2, "cartografa_ritorno"]]; heroes.append(p); return p

        def menu(options, prompt="", **kw):
            # Al piano 2 entra nella porta dell'evento richiamato; altrove sempre nella prima porta
            return next((i for i, o in enumerate(options) if "qualcosa ti stava aspettando" in o), 0)

        rooms = {n: mock.DEFAULT for n in ("combat_room", "vendor_room", "treasure_room", "trap_room", "campfire_room", "mystery_room")}
        with quiet(), mock.patch("roguelike._hero_selection", return_value=("1", "base", [])), mock.patch("roguelike.Player", side_effect=hero), \
             mock.patch("roguelike.interactive_menu", side_effect=menu), mock.patch("roguelike.event_room", side_effect=lambda p, e, f: visited.append((f, e))), \
             mock.patch.multiple("roguelike", **rooms), mock.patch("roguelike.evaluate_run"), mock.patch("roguelike.wait_enter"), \
             mock.patch("roguelike.clear_screen"), mock.patch("roguelike.delay_print"), mock.patch("roguelike.time.sleep"), \
             mock.patch("roguelike._grant_victory_rewards"), mock.patch("roguelike.choose_ending"), mock.patch("roguelike.start_of_run_boon"):
            roguelike.play_game()
        self.assertIn((2, "cartografa_ritorno"), visited)
        self.assertEqual([e for _, e in visited].count("cartografa_ritorno"), 1)
        self.assertEqual(heroes[0].pending_events, [])


class EventSelectionTest(Sandbox):
    def test_scripted_and_gated_events_are_not_picked_at_random(self):
        picked = {events.pick_event(1, self.hero()) for _ in range(400)}
        self.assertNotIn("cartografa_ritorno", picked)
        self.assertNotIn("voce_labirinto", picked)  # dal piano 12
        self.assertTrue(events.is_available("voce_labirinto", 12))

    def test_freed_artisans_do_not_reappear(self):
        PROFILE_MANAGER.unlock_npc("borek")
        self.assertFalse(events.is_available("borek_prigioniero", 5))
        self.assertTrue(events.is_available("elara_prigioniera", 5))

    def test_events_already_seen_in_this_run_are_avoided(self):
        p = self.hero()
        avail = [k for k in GAME_DATA["events"] if events.is_available(k, 10, p)]
        p.seen_events = set(avail[1:])
        self.assertEqual(events.pick_event(10, p), avail[0])
        p.seen_events = set(avail)
        self.assertIn(events.pick_event(10, p), avail)  # visti tutti: si ricomincia


if __name__ == "__main__":
    unittest.main()
