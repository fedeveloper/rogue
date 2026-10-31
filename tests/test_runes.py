"""Rune e Incastoni: ogni effetto fa ciò che dice la sua descrizione, gli incastoni seguono la rarità dell'oggetto,
il Falò incastona ed estrae, la fusione non distrugge rune e ogni fonte ne lascia cadere con la sua probabilità."""
import copy
import io
import random
import re
import unittest
from contextlib import redirect_stdout
from unittest import mock

import effects
import codex
import magic
import roguelike
import rooms
import runes
from data_manager import GAME_DATA, PROFILE_MANAGER
from entities import Armor, Enemy, Player, Rune, Weapon, generate_armor, generate_rune, generate_weapon
from rooms import CombatSession
from rooms_patch import patch_rooms

ANSI = re.compile(r"\x1b\[[0-9;]*m")
RUNES = GAME_DATA["runes"]["runes"]
RULES = GAME_DATA["runes"]["rules"]


def quiet():
    return redirect_stdout(io.StringIO())


def plain(text):
    return ANSI.sub("", text)


WORDS = GAME_DATA["runes"]["words"]


def source_of(key):
    """(rune da incastonare, valore) per provare un effetto: una runa che lo ha, o le rune di una parola runica."""
    rid = next((rid for rid, r in RUNES.items() if key in r["effects"]), None)
    if rid: return [rid], RUNES[rid]["effects"][key]
    w = next(w for w in WORDS.values() if key in w["effects"])
    return list(w["runes"]), w["effects"][key]


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        self._save = mock.patch.object(PROFILE_MANAGER, "save")
        self._save.start()
        self._ui = [patch_rooms(f) for f in ("wait_enter", "delay_print", "clear_screen")] + [mock.patch("rooms.time.sleep")]
        for p in self._ui: p.start()
        random.seed(8)

    def tearDown(self):
        for p in self._ui: p.stop()
        self._save.stop()
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)

    def hero(self, *rune_ids):
        """Un eroe con arma e armatura di prova (Normale, nessuna reazione) e le rune date incastonate dove vanno."""
        with quiet(): p = Player("1", "base", [])
        p.weapon = Weapon("Prova", 1, 50, "Normale", 1)
        p.armor = Armor("Prova", 1, 20, "Normale", 1)
        p.weapon.sockets = p.armor.sockets = 3
        for rid in rune_ids:
            (p.weapon if runes.fits(rid, "weapon") else p.armor).runes.append(rid)
        p.max_hp = p.hp = 1000
        p.inventory = []
        return p

    def session(self, p):
        with quiet(): s = CombatSession(p, 10, Enemy(10, False, []))
        s.enemy.hp = s.enemy.max_hp = 1000
        s.enemy.atk, s.enemy.element, s.enemy.base_acc, s.enemy.base_dodge = 40, "Normale", 100, -1000
        return s


class RuneDataTest(unittest.TestCase):
    def test_every_rune_is_well_formed(self):
        self.assertGreaterEqual(len(RUNES), 15)
        for rid, r in RUNES.items():
            with self.subTest(rune=rid):
                self.assertTrue(r["name"] and r["icon"] and r["desc"] and r["family"])
                self.assertIn(r["slot"], runes.SLOT_NAMES)
                self.assertGreater(r["weight"], 0)
                self.assertTrue(r["effects"])
                self.assertLessEqual(set(r["effects"]), set(runes.RUNE_EFFECT_KEYS))
                for v in r["effects"].values(): self.assertIn(str(v), r["desc"], "la descrizione dice il numero dell'effetto")
                self.assertTrue(all(ord(c) != 0xFE0F for c in r["icon"]), "niente selettori di variante: rompono gli allineamenti")

    def test_every_effect_key_is_used_and_has_a_contract(self):
        used = {k for r in list(RUNES.values()) + list(WORDS.values()) for k in r["effects"]}
        self.assertEqual(used, set(runes.RUNE_EFFECT_KEYS))
        self.assertEqual(set(EffectContractTest.CHECKS), set(runes.RUNE_EFFECT_KEYS))


class EffectContractTest(Sandbox):
    def test_every_effect_does_what_it_says(self):
        for key in runes.RUNE_EFFECT_KEYS:
            ids, value = source_of(key)
            if len(ids) > 1: continue  # gli effetti che esistono solo nelle parole runiche hanno il loro test qui sotto
            with self.subTest(rune=ids[0], key=key):
                self.CHECKS[key](self, ids[0], value)

    def test_effects_only_in_runewords(self):
        for key in ("scorch_on_hit", "stun_on_hit"):
            ids, v = source_of(key)
            status = {"scorch_on_hit": "scorch", "stun_on_hit": "stun"}[key]
            with self.subTest(key=key):
                s, _ = self.attack(self.hero(*ids), rolls=v)
                self.assertIn(status, s.enemy.statuses)
                s, _ = self.attack(self.hero(*ids), rolls=v + 1)
                self.assertNotIn(status, s.enemy.statuses)

    def test_a_word_makes_spells_cheaper(self):
        ids, v = source_of("spell_discount")
        base, word = self.hero(), self.hero(*ids)
        for sid, s in GAME_DATA["spells"]["spells"].items():
            with self.subTest(spell=sid):
                self.assertEqual(magic.cost(word, sid), max(1, magic.cost(base, sid) - v))

    def attack(self, p, multiplier=1.0, rolls=1):
        s = self.session(p)
        with quiet(), mock.patch.object(s, "attack_multiplier", return_value=multiplier), mock.patch("rooms.random.randint", return_value=rolls):
            s.execute_player_attack()
        return s, 1000 - s.enemy.hp

    def _mark(self, rid, v):
        s = self.session(self.hero(rid))
        with quiet(): s.apply_element("Fuoco")
        self.assertEqual(s.enemy.mark[1], GAME_DATA["elements"]["marks"]["duration"] + v)

    def _reaction(self, rid, v):
        key = next(iter(GAME_DATA["elements"]["reactions"]))
        dealt = []
        for p in (self.hero(), self.hero(rid)):
            s = self.session(p)
            with quiet(): s._trigger_reaction(key)
            dealt.append(1000 - s.enemy.hp)
        self.assertEqual(dealt[1], dealt[0] * (100 + v) // 100)

    def _super_effective(self, rid, v):
        base, boosted = self.attack(self.hero(), 1.5)[1], self.attack(self.hero(rid), 1.5)[1]
        self.assertEqual(boosted, base * (100 + v) // 100)
        self.assertEqual(self.attack(self.hero(rid))[1], self.attack(self.hero())[1], "solo sui colpi Super Efficaci")

    def _status_on_hit(self, status):
        def check(self, rid, v):
            s, _ = self.attack(self.hero(rid), rolls=v)
            self.assertIn(status, s.enemy.statuses)
            s, _ = self.attack(self.hero(rid), rolls=v + 1)
            self.assertNotIn(status, s.enemy.statuses)
        return check

    def _crit(self, rid, v):
        self.assertEqual(self.hero(rid).get_crit_chance(), self.hero().get_crit_chance() + v)

    def _atk(self, rid, v):
        self.assertEqual(self.hero(rid).get_total_atk(), self.hero().get_total_atk() + 50 * v // 100)

    def _lifesteal(self, rid, v):
        p = self.hero(rid); p.hp = 1
        s, dealt = self.attack(p)
        self.assertEqual(p.hp, 1 + dealt * v // 100)

    def _first_strike(self, rid, v):
        p = self.hero(rid)
        s = self.session(p)
        hits = []
        for _ in range(2):
            before = s.enemy.hp
            with quiet(), mock.patch("rooms.random.randint", return_value=1): s.execute_player_attack()
            hits.append(before - s.enemy.hp)
        self.assertEqual(hits[0], hits[1] * (100 + v) // 100)

    def _def(self, rid, v):
        self.assertEqual(self.hero(rid).get_total_def(), self.hero().get_total_def() + 20 * v // 100)

    def _dodge(self, rid, v):
        self.assertEqual(self.hero(rid).get_dodge(), self.hero().get_dodge() + v)

    def _thorns(self, rid, v):
        p = self.hero(rid); p.base_dodge = -1000
        s = self.session(p)
        with quiet(), mock.patch("rooms.random.randint", side_effect=lambda a, b: a), patch_rooms("wait_enter"):
            s.enemy_turn()
        self.assertEqual(1000 - s.enemy.hp, (1000 - p.hp) * v // 100)

    def _defend_heal(self, rid, v):
        p = self.hero(rid); p.hp = 1
        s = self.session(p)
        with quiet(): s.execute_player_defense()
        self.assertEqual(p.hp, 1 + 1000 * v // 100)

    def _gold(self, rid, v):
        self.assertEqual(self.hero(rid).calculate_gold_gain(1000), self.hero().calculate_gold_gain(1000) * (100 + v) // 100)

    def _exp(self, rid, v):
        gains = []
        for p in (self.hero(), self.hero(rid)):
            p.exp, p.max_exp = 0, 10 ** 6
            with quiet(): p.gain_exp(1000)
            gains.append(p.exp)
        self.assertEqual(gains[1], int(1000 * (p.exp_multiplier + v / 100)))

    def _audacity(self, rid, v):
        self.assertEqual(effects.total(self.hero(rid), "audacity_start"), v)
        seen = []
        def menu(options, prompt="", **kw):
            seen.append(plain(prompt)); return len(options) - 1  # Fuga dal Labirinto
        with quiet(), mock.patch("roguelike._hero_selection", return_value=("1", "base", [])), mock.patch("roguelike._choose_ascension", return_value=0), \
             mock.patch("roguelike.Player", side_effect=lambda *a: self.hero(rid)), mock.patch("roguelike.interactive_menu", side_effect=menu), \
             mock.patch("roguelike.evaluate_run"), mock.patch("roguelike.wait_enter"), mock.patch("roguelike.clear_screen"), mock.patch("roguelike.delay_print"), \
             mock.patch("roguelike.time.sleep"), mock.patch("roguelike.start_of_run_boon"):
            roguelike.play_game()
        self.assertIn(f"Audacia: {v}", seen[0])

    def _trap(self, rid, v):
        base, boosted = rooms.trap_chances(self.hero()), rooms.trap_chances(self.hero(rid))
        cap = GAME_DATA["meta"]["rooms"]["trap"]["max_chance"]
        for k in base: self.assertEqual(boosted[k], min(cap, base[k] + v))

    def _ether_max(self, rid, v):
        self.assertEqual(self.hero(rid).max_ether(), self.hero().max_ether() + v)

    def _spell_pct(self, rid, v):
        dealt = []
        for p in (self.hero(), self.hero(rid)):
            s = self.session(p)
            dealt.append(s.spell_damage("raffica", 100))
        self.assertEqual(dealt[1], dealt[0] * (100 + v) // 100)

    def _ether_on_hit(self, rid, v):
        gained = []
        for p in (self.hero(), self.hero(rid)):
            p.base_ether, p.ether = 100, 0
            s = self.session(p)
            with quiet(), mock.patch("rooms.random.randint", return_value=1): s.execute_player_attack()
            gained.append(p.ether)
        self.assertEqual(gained[1], gained[0] + v)

    CHECKS = {
        "mark_duration_add": _mark, "reaction_dmg_pct": _reaction, "super_effective_pct": _super_effective,
        "bleed_on_hit": _status_on_hit(None, "bleed"), "poison_on_hit": _status_on_hit(None, "poison"),
        "crit_chance_add": _crit, "atk_pct": _atk, "lifesteal_pct": _lifesteal, "first_strike_pct": _first_strike,
        "def_pct": _def, "dodge_add": _dodge, "thorns_pct": _thorns, "defend_heal_pct": _defend_heal,
        "gold_pct": _gold, "exp_pct": _exp, "audacity_start": _audacity, "trap_chance_add": _trap,
        "scorch_on_hit": None, "stun_on_hit": None,  # solo nelle parole runiche: test_effects_only_in_runewords
        "ether_max": _ether_max, "spell_pct": _spell_pct, "ether_on_hit": _ether_on_hit,
        "spell_discount": None,  # solo nella parola Mente Arcana: test_a_word_makes_spells_cheaper
    }


class RunewordTest(Sandbox):
    def test_every_word_is_well_formed(self):
        combos = set()
        for wid, w in WORDS.items():
            with self.subTest(word=wid):
                self.assertTrue(2 <= len(w["runes"]) <= RULES["sockets"]["boss"])
                self.assertLessEqual(set(w["runes"]), set(RUNES))
                slots = {RUNES[r]["slot"] for r in w["runes"]} - {"any"}
                self.assertLessEqual(len(slots), 1, "tutte le rune di una parola stanno sullo stesso oggetto")
                self.assertLessEqual(set(w["effects"]), set(runes.RUNE_EFFECT_KEYS))
                for v in w["effects"].values(): self.assertIn(str(v), w["desc"])
                combos.add(tuple(sorted(w["runes"])))
        self.assertEqual(len(combos), len(WORDS), "ogni parola ha una combinazione diversa")

    def test_a_word_needs_all_its_runes_on_the_same_item(self):
        w = WORDS["boia"]
        p = self.hero(*w["runes"])
        self.assertEqual(runes.active_words(p.weapon), ["boia"])
        self.assertEqual(p.get_crit_chance(), self.hero().get_crit_chance() + RUNES["occhio"]["effects"]["crit_chance_add"] + w["effects"]["crit_chance_add"])
        p = self.hero("forza")
        self.assertEqual(runes.active_words(p.weapon), [])
        p = self.hero(*w["runes"]); p.weapon.refresh_display_name()
        self.assertIn("«Colpo del Boia»", p.weapon.display_name)

    def test_longer_words_win_and_each_rune_counts_once(self):
        p = self.hero("eco", "catalisi", "contrasto")
        self.assertEqual(runes.active_words(p.weapon), ["prisma"], "Prisma usa Catalisi e Contrasto: niente Tempesta in più")
        p = self.hero("pietra", "vento", "quiete")
        self.assertEqual(runes.active_words(p.armor), ["egida"])
        p = self.hero("pietra", "rovo")
        self.assertEqual(runes.active_words(p.armor), ["fortezza"])

    def test_socketing_the_last_rune_announces_and_records_the_word(self):
        PROFILE_MANAGER.codex["runewords"] = []
        p = self.hero("forza"); p.weapon.sockets = 2
        p.inventory = [Rune("occhio")]
        out = io.StringIO()
        picks = iter([0, 0, 0, -1])
        with redirect_stdout(out), patch_rooms("interactive_menu", side_effect=lambda *a, **k: next(picks)):
            rooms.rune_workshop(p, 5)
        self.assertIn("PAROLA RUNICA «Colpo del Boia»", plain(out.getvalue()))
        self.assertEqual(PROFILE_MANAGER.codex["runewords"], ["boia"])
        page = "\n".join(plain(l) for l in codex.runewords_page())
        self.assertIn("«Colpo del Boia»", page)
        self.assertIn("??? — 2 rune", page)


class SocketTest(Sandbox):
    def test_sockets_follow_rarity(self):
        s = RULES["sockets"]
        self.assertEqual(generate_weapon(5).sockets, s["normal"])
        self.assertEqual(generate_armor(5, True).sockets, s["epic"])
        self.assertEqual(self.hero().weapon.sockets, 3)
        with quiet(): p = Player("1", "base", [])
        self.assertEqual((p.weapon.sockets, p.armor.sockets), (s["normal"], s["normal"]), "anche l'equipaggiamento iniziale ha un incastone")

    def test_the_name_shows_runes_and_free_sockets(self):
        w = Weapon("Spada", 1, 10, "Normale", 1); w.sockets = 2; w.runes = ["forza"]; w.refresh_display_name()
        self.assertTrue(w.display_name.endswith(f" [Incastoni: {RUNES['forza']['icon']}◇]"))

    def test_boss_gear_drops_with_three_sockets(self):
        p = self.hero()
        with quiet(): s = CombatSession(p, 10, Enemy(10, True, []))
        with quiet(), patch_rooms("get_random_relic", return_value=None): s.on_enemy_death()
        gear = [i for i in p.inventory if i.type in ("weapon", "armor")]
        self.assertEqual([g.sockets for g in gear], [RULES["sockets"]["boss"]])

    def test_only_equipped_items_count(self):
        p = self.hero()
        spare = Weapon("Riserva", 1, 10, "Normale", 1); spare.runes = ["forza"]
        p.inventory.append(spare)
        self.assertEqual(effects.total(p, "atk_pct"), 0)


class WorkshopTest(Sandbox):
    def run_workshop(self, p, picks, floor=5):
        it = iter(picks)
        with quiet(), patch_rooms("interactive_menu", side_effect=lambda *a, **k: next(it)):
            rooms.rune_workshop(p, floor)

    def test_socketing_is_free_and_respects_the_slot(self):
        p = self.hero(); p.weapon.sockets, p.armor.sockets = 1, 1
        p.inventory = [Rune("pietra")]
        p.gold = 0
        self.run_workshop(p, [0, 0, 0, -1])  # incastona → la runa → l'unico oggetto adatto (l'armatura)
        self.assertEqual((p.armor.runes, p.weapon.runes, p.gold), (["pietra"], [], 0))
        self.assertEqual([i for i in p.inventory if i.type == "rune"], [])

    def test_a_full_item_cannot_take_more_runes(self):
        p = self.hero(); p.weapon.sockets, p.weapon.runes = 1, ["forza"]
        p.inventory = [Rune("occhio")]
        self.run_workshop(p, [0, 0, -1])
        self.assertEqual(p.weapon.runes, ["forza"])
        self.assertEqual(len(p.inventory), 1)

    def test_extracting_costs_gold_and_returns_the_rune(self):
        p = self.hero("forza"); p.gold = 1000
        self.run_workshop(p, [1, 0, 0, -1])
        self.assertEqual(p.weapon.runes, [])
        self.assertEqual(p.gold, 1000 - runes.extract_cost(5))
        self.assertEqual([i.rune_id for i in p.inventory], ["forza"])
        p = self.hero("forza"); p.gold = 0
        self.run_workshop(p, [1, -1])
        self.assertEqual(p.weapon.runes, ["forza"], "senza Oro la runa resta dov'è")

    def test_the_campfire_offers_the_workshop_without_putting_out_the_fire(self):
        p = self.hero()
        menus = []
        def menu(options, prompt="", **kw):
            menus.append(options)
            if len(menus) == 1: return options.index(rooms.RUNE_WORKSHOP)
            if len(menus) == 2: return -1                 # esce dal laboratorio
            return options.index("Prosegui")
        with quiet(), patch_rooms("interactive_menu", side_effect=menu):
            rooms.campfire_room(p, 5)
        self.assertEqual(len(menus), 3, "dopo il laboratorio il falò è ancora acceso")

    def test_fusion_keeps_the_base_runes_and_frees_the_others(self):
        p = self.hero()
        a, b = Weapon("Base", 1, 10, "Normale", 1), Weapon("Sacrificio", 1, 10, "Normale", 1)
        a.runes, b.runes = ["forza"], ["occhio"]
        p.inventory = [a, b]
        picks = iter([2, 0, 1])  # Altare → base → sacrificio
        with quiet(), patch_rooms("interactive_menu", side_effect=lambda options, *x, **k: next(picks, options.index("Prosegui") if "Prosegui" in options else -1)):
            rooms.campfire_room(p, 5)
        self.assertEqual(a.runes, ["forza"])
        self.assertIn("occhio", [i.rune_id for i in p.inventory if i.type == "rune"])


class DropTest(Sandbox):
    def test_every_source_drops_runes_with_its_chance(self):
        for source, chance in RULES["drops"].items():
            with self.subTest(source=source):
                # random.random() è sempre < 1: con probabilità 100 la runa cade sempre
                for roll, expected in ((chance - 0.01, 1), (chance + 0.01, 0)):
                    if roll >= 100: continue
                    p = self.hero()
                    with quiet(), mock.patch("runes.random.random", return_value=roll / 100): rooms.rune_drop(p, 5, source)
                    self.assertEqual(len(p.inventory), expected)

    def test_each_source_calls_its_drop(self):
        sources = set()
        with patch_rooms("rune_drop", side_effect=lambda p, f, src: sources.add(src)):
            p = self.hero()
            for modifier, boss in (("elite", False), ("normal", True)):
                with quiet(): s = CombatSession(p, 10, Enemy(10, boss, [], modifier=modifier))
                with quiet(): s.on_enemy_death()
            with quiet(), patch_rooms("interactive_menu", return_value=1), mock.patch("rooms.random.randint", return_value=1): rooms.trap_room(p, 5, [])
            with quiet(), mock.patch("rooms.random.choices", return_value=["hoard"]): rooms.mystery_room(p, 5, [])
            with quiet(), mock.patch("rooms.chest_risks", return_value={"mimic": 100.0, "locked": 0.0}), mock.patch("rooms.random.random", return_value=0.99), \
                 mock.patch("rooms.combat_room", side_effect=lambda pl, f, e: setattr(e, "hp", 0)):
                rooms.treasure_room(p, 5)
        self.assertEqual(sources, set(RULES["drops"]))

    def test_the_vendor_sells_runes(self):
        stock = []
        def menu(options, prompt="", **kw):
            if "COMPRA" in prompt: stock.extend(plain(o) for o in options); return -1
            return 0 if not stock else 2
        p = self.hero()
        with quiet(), patch_rooms("interactive_menu", side_effect=menu):
            rooms.vendor_room(p, 5)
        self.assertEqual(sum(o.startswith("[Runa]") for o in stock), RULES["vendor_stock"])

    def test_found_runes_enter_the_codex(self):
        PROFILE_MANAGER.codex["runes"] = []
        p = self.hero()
        with quiet(), mock.patch("runes.random.random", return_value=0.0), patch_rooms("generate_rune", return_value=Rune("eco")):
            rooms.rune_drop(p, 5, "boss")
        self.assertEqual(PROFILE_MANAGER.codex["runes"], ["eco"])
        page = "\n".join(plain(l) for l in codex.runes_page())
        self.assertIn(RUNES["eco"]["name"], page)
        self.assertNotIn(RUNES["forza"]["name"], page)


if __name__ == "__main__":
    unittest.main()
