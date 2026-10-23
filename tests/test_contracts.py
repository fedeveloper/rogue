"""Contratti fra descrizioni ed effetti: ogni asset del gioco deve fare ciò che la sua descrizione promette.

Ogni famiglia di asset ha un controllo di completezza: aggiungere una reliquia, una categoria di consumabile,
un tratto, un patto o un'impresa senza il relativo contratto fa fallire i test.
Il profilo viene modificato solo in memoria e ripristinato; non viene mai salvato.
"""
import copy
import io
import random
import re
import unittest
from contextlib import redirect_stdout
from unittest import mock

import events
import inventory_menu
import roguelike
import rooms
from data_manager import GAME_DATA, PROFILE_MANAGER, RAW_DATA, update_game_data
from entities import Accessory, Armor, Consumable, Enemy, Player, Weapon, generate_accessory, generate_armor, generate_weapon
from rooms import CombatSession

ALL_UNLOCKS = sorted({i["unlock_id"] for cat in ("weapons", "armors", "accessories", "consumables", "relics")
                      for i in RAW_DATA[cat] if i.get("unlock_id")})
NUM = re.compile(r"\d+")


def quiet():
    return redirect_stdout(io.StringIO())


class Sandbox(unittest.TestCase):
    """Profilo pulito: tutto sbloccato, nessun potenziamento, nessuna Maestria, nessun bonus dell'Archivio."""

    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        data = PROFILE_MANAGER._data
        data.update(unlocked_ids=list(ALL_UNLOCKS), class_lvl={}, completed_feats=[], max_floor=0, won_normal=False)
        data["stats"] = {"total_deaths": 0, "total_gold": 0, "total_bosses": 0}
        data["story"] = {"flags": {}, "counters": {}, "seen_events": {}}  # nessuna struttura del campo (es. l'Altare)
        data["perks"] = {k: (False if isinstance(v, bool) else 0) for k, v in data["perks"].items()}
        for k in ("starting_consumables", "starting_weapons", "starting_armors", "starting_accessories"): data[k] = []
        update_game_data()
        random.seed(1234)

    def tearDown(self):
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)
        update_game_data()

    def hero(self, cls="1", trait="base", pacts=()):
        with quiet():
            p = Player(cls, trait, list(pacts))
        p.weapon = Weapon("Spada di prova", 10, 10, "Normale", 1)
        p.armor = Armor("Armatura di prova", 10, 0, "Normale", 1)
        return p

    def session(self, p, floor=1, boss=False):
        with quiet():
            return CombatSession(p, floor, Enemy(floor, boss, []))

    def relic(self, p, rid):
        data = next(r for r in RAW_DATA["relics"] if r["id"] == rid)
        with quiet():
            p.add_relic(data)
        return p.relic_effects[-1]

    def drink(self, p, item, in_combat=False):
        p.inventory = [item]
        with quiet(), mock.patch("builtins.input", return_value=""), mock.patch("inventory_menu.random.random", return_value=0.99):
            return inventory_menu._use_consumable(p, item, 0, in_combat)


# ---------------------------------------------------------------- reliquie
class RelicContractTest(Sandbox):
    def contracts(self):
        return {
            "artiglio_vampiro": self.c_artiglio, "lente_prismatica": self.c_lente, "scudo_cristallo": self.c_scudo,
            "tasca_dorata": self.c_tasca, "idolo_guerra": self.c_idolo_guerra, "calice_alchimista": self.c_calice,
            "mantello_nebbioso": self.c_mantello, "bussola_perfetta": self.c_bussola, "occhio_cacciatore": self.c_occhio,
            "spallacci_rovo": self.c_rovo, "cuore_troll": self.c_troll, "tomo_conoscenza": self.c_tomo,
            "idolo_avidita": self.c_avidita, "lama_sangue": self.c_lama, "corona_re_folle": self.c_corona,
            "anello_vampiro_max": self.c_anello, "clessidra_destino": self.c_clessidra, "armatura_spilli": self.c_spilli,
            "pergamena_oro": self.c_pergamena, "campanella_spiriti": self.c_campanella, "pietra_luna": self.c_luna,
            "contratto_demoniaco": self.c_contratto, "pozione_infinita": self.c_pozione, "bussola_dimensionale": self.c_dimensionale,
            "cuore_drago": self.c_drago, "sigillo_elementale": self.c_sigillo, "spirito_spada": self.c_spirito,
            "maschera_antigas": self.c_maschera, "teschio_sangue": self.c_teschio, "pietra_filosofale": self.c_filosofale,
        }

    def test_every_relic_has_a_contract(self):
        self.assertEqual(set(self.contracts()), {r["id"] for r in RAW_DATA["relics"]})

    def test_every_relic_does_what_it_says(self):
        for rid, check in self.contracts().items():
            with self.subTest(relic=rid), quiet():
                self.setUp()
                check()

    def c_artiglio(self):
        p = self.hero(); p.hp = 10; e = self.relic(p, "artiglio_vampiro")
        e.on_attack_landed(self.session(p), 1.0); self.assertEqual(p.hp, 15)

    def c_lente(self):
        e = self.relic(self.hero(), "lente_prismatica")
        self.assertEqual([e.modify_multiplier(m) for m in (1.5, 1.0, 0.5)], [2.0, 1.0, 0.25])

    def c_scudo(self):
        p = self.hero(); s = self.session(p); e = self.relic(p, "scudo_cristallo"); e.on_combat_start(s)
        self.assertEqual([e.on_take_damage(s, 10, 1) for _ in range(2)], [0, 10])
        e.on_combat_start(s); self.assertEqual(e.on_take_damage(s, 10, 1), 0)

    def c_tasca(self):
        p = self.hero(); self.relic(p, "tasca_dorata"); self.assertEqual(p.calculate_gold_gain(100), 125)

    def c_idolo_guerra(self):
        p = self.hero(); before = p.get_total_atk(); self.relic(p, "idolo_guerra"); self.assertEqual(p.get_total_atk(), before + 5)

    def c_calice(self):
        p = self.hero(); self.relic(p, "calice_alchimista"); p.hp = 1
        self.drink(p, Consumable("Pozione", 10, 40, "heal")); self.assertEqual(p.hp, 61)
        p.hp = 1; p.heal(10); self.assertEqual(p.hp, 11, "le cure che non vengono da consumabili non cambiano")

    def c_mantello(self):
        p = self.hero(); before = p.get_dodge(); self.relic(p, "mantello_nebbioso"); self.assertEqual(p.get_dodge(), before + 15)

    def c_bussola(self):
        p = self.hero(); s = self.session(p); self.relic(p, "bussola_perfetta"); self.assertEqual(s._calc_escape_chance(), 100)

    def c_occhio(self):
        p = self.hero(); p.base_acc = -60; before = p.get_hit_chance(); self.relic(p, "occhio_cacciatore")
        self.assertEqual(p.get_hit_chance(), before + 20)

    def c_rovo(self):
        p = self.hero(); s = self.session(p); s.enemy.hp = 100; e = self.relic(p, "spallacci_rovo")
        with quiet(): self.assertEqual(e.on_take_damage(s, 10, 1), 10)
        self.assertEqual(s.enemy.hp, 95)

    def c_troll(self):
        p = self.hero(); before = p.max_hp; e = self.relic(p, "cuore_troll")
        with quiet(): e.on_enemy_death(self.session(p))
        self.assertEqual(p.max_hp, before + 2)

    def c_tomo(self):
        p = self.hero(); self.relic(p, "tomo_conoscenza"); p.exp = 0
        with quiet(): p.gain_exp(50)
        self.assertEqual(p.exp, 65)

    def c_avidita(self):
        p = self.hero(); p.base_dodge = 50; self.relic(p, "idolo_avidita")
        self.assertEqual(p.calculate_gold_gain(100), 200); self.assertEqual(p.get_dodge(), 0)

    def c_lama(self):
        p = self.hero(); before = p.get_total_atk(); e = self.relic(p, "lama_sangue"); hp = p.hp
        self.assertEqual(p.get_total_atk(), before + 10)
        with quiet(): self.assertTrue(e.on_before_attack(self.session(p)))
        self.assertEqual(p.hp, hp - 3)

    def c_corona(self):
        p = self.hero(); s = self.session(p); e = self.relic(p, "corona_re_folle")
        self.assertEqual(e.on_attack(s, 10, 1.5, "")[0], 15)
        self.assertEqual(e.on_attack(s, 10, 1.0, "[CRITICO!]")[0], 15)
        self.assertEqual(e.on_attack(s, 10, 1.0, "")[0], 10)
        _, weapon_crit = Weapon("Ascia", 1, 10, "Normale", 1, traits={"crit_chance": 100}).on_attack(10, "")
        self.assertIn("[CRITICO!]", weapon_crit, "i critici delle armi devono attivare la Corona")

    def c_anello(self):
        p = self.hero(); p.hp = 10; e = self.relic(p, "anello_vampiro_max")
        with quiet(): e.on_attack_landed(self.session(p), 1.0)
        self.assertEqual(p.hp, 12)

    def c_clessidra(self):
        p = self.hero(); s = self.session(p); s.enemy.base_dodge = 30; self.relic(p, "clessidra_destino").on_combat_start(s)
        self.assertEqual(s.enemy.base_dodge, 10)

    def c_spilli(self):
        p = self.hero(); s = self.session(p); s.enemy.hp = 100; e = self.relic(p, "armatura_spilli")
        with quiet(): e.on_take_damage(s, 10, 1)
        self.assertEqual(s.enemy.hp, 97)

    def c_pergamena(self):
        p = self.hero(); p.hp = 10; self.relic(p, "pergamena_oro")
        with quiet(): self.assertEqual(p.calculate_gold_gain(10), 10)
        self.assertEqual(p.hp, 12)

    def c_campanella(self):
        p = self.hero(); s = self.session(p); e = self.relic(p, "campanella_spiriti")
        with quiet(), mock.patch("relic_effects.random.random", return_value=0.10): self.assertEqual(e.on_take_damage(s, 10, 1), 0)
        with quiet(), mock.patch("relic_effects.random.random", return_value=0.20): self.assertEqual(e.on_take_damage(s, 10, 1), 10)

    def c_luna(self):
        p = self.hero(); p.armor.defense = 10; s = self.session(p); s.enemy.atk = 40; s.is_defending = True
        with mock.patch("rooms.random.randint", return_value=0):
            plain = s._calc_enemy_damage(1.0)
            self.relic(p, "pietra_luna"); boosted = s._calc_enemy_damage(1.0)
        self.assertEqual((plain, boosted), ((40 - 10) // 2, (40 - 15) // 2))

    def c_contratto(self):
        p = self.hero(); s = self.session(p); e = self.relic(p, "contratto_demoniaco")
        self.assertEqual(e.on_attack(s, 10, 1.0, "")[0], 20)
        p.hp = 20
        with quiet(): e.on_enemy_death(s)
        self.assertEqual(p.hp, 15)
        p.hp = 3
        with quiet(): e.on_enemy_death(s)
        self.assertEqual(p.hp, 1, "il tributo non può uccidere")

    def c_pozione(self):
        p = self.hero(); e = self.relic(p, "pozione_infinita")
        with quiet(), mock.patch("relic_effects.random.random", return_value=0.0):
            self.assertFalse(e.on_item_use(p, Consumable("Elisir degli Dei", 1, 300, "heal")))
            self.assertTrue(e.on_item_use(p, Consumable("Fiala del Caos", 1, 0, "chaos_vial")), "solo le pozioni curative")

    def c_dimensionale(self):
        w = {"combat": 60.0, "treasure": 5.0, "mystery": 10.0}
        self.relic(self.hero(), "bussola_dimensionale").modify_room_weights(w)
        self.assertEqual(w, {"combat": 60.0, "treasure": 20.0, "mystery": 25.0})

    def c_drago(self):
        p = self.hero("1", "maledetto"); hp, mx = p.hp, p.max_hp; self.relic(p, "cuore_drago")
        self.assertEqual((p.hp, p.max_hp), (hp + 50, mx + 50))

    def c_sigillo(self):
        e = self.relic(self.hero(), "sigillo_elementale")
        self.assertEqual([e.modify_multiplier(1.5, True), e.modify_multiplier(1.5, False), e.modify_multiplier(0.5, True)], [1.0, 1.5, 0.5])

    def c_spirito(self):
        p = self.hero(); p.weapon.level = 2; base = p.get_total_atk(); self.relic(p, "spirito_spada")
        self.assertEqual(p.get_total_atk(), base)
        p.weapon.level = 1; self.assertEqual(p.get_total_atk(), base + 15, "il bonus segue l'arma impugnata")

    def c_maschera(self):
        with quiet(): self.assertEqual(self.relic(self.hero(), "maschera_antigas").modify_trap_damage(30), 0)

    def c_teschio(self):
        p = self.hero(); before = p.max_hp; e = self.relic(p, "teschio_sangue")
        with quiet(): e.on_enemy_death(self.session(p))
        self.assertEqual(p.max_hp, before + 1)

    def c_filosofale(self):
        p = self.hero(); s = self.session(p); s.enemy.exp_drop = 50; gold = p.gold; e = self.relic(p, "pietra_filosofale")
        with quiet(), mock.patch("relic_effects.random.random", return_value=0.10): e.on_enemy_death(s)
        self.assertEqual((p.gold, s.enemy.exp_drop), (gold + 50, 0))


# ---------------------------------------------------------------- armi, armature, monili
class EquipmentContractTest(Sandbox):
    def test_numbers_in_weapon_descriptions_come_from_the_data(self):
        for w in RAW_DATA["weapons"]:
            st = w.get("status_inflict") or {}
            allowed = {st.get("chance"), -w.get("hit_modifier", 0), w.get("crit_chance"), w.get("gold_atk_per"), w.get("gold_atk_max")}
            if w.get("gold_atk_per"): allowed.add(1)  # "+1 ATK ogni ... Oro"
            with self.subTest(weapon=w["name"]):
                for n in NUM.findall(w.get("desc", "")):
                    self.assertIn(int(n), allowed, f"numero {n} nella descrizione senza un effetto corrispondente")
                if w.get("element"): self.assertIn(w["element"], w["desc"])

    def test_weapon_traits_behave_as_described(self):
        p = self.hero()
        p.base_acc = -60
        base_hit = p.get_hit_chance()
        for w in RAW_DATA["weapons"]:
            with self.subTest(weapon=w["name"]), mock.patch("entities.random.choice", side_effect=lambda seq: w if isinstance(seq, list) and w in seq else seq[0]):
                weapon = generate_weapon(1, True)
                if w.get("element"): self.assertEqual(weapon.element, w["element"])
                p.weapon = weapon
                self.assertEqual(p.get_hit_chance(), base_hit + w.get("hit_modifier", 0))
                if w.get("crit_chance"):
                    with mock.patch("entities.random.randint", return_value=w["crit_chance"]):
                        self.assertEqual(weapon.on_attack(10, "")[0], 20)
                    with mock.patch("entities.random.randint", return_value=w["crit_chance"] + 1):
                        self.assertEqual(weapon.on_attack(10, "")[0], 10)
                if w.get("gold_atk_per"):
                    p.gold = 0; plain = p.get_total_atk()
                    p.gold = w["gold_atk_per"] * 3; self.assertEqual(p.get_total_atk(), plain + 3)
                    p.gold = 10 ** 9; self.assertEqual(p.get_total_atk(), plain + w["gold_atk_max"])
                    p.gold = 0

    def test_numbers_in_armor_descriptions_come_from_the_data(self):
        for a in RAW_DATA["armors"]:
            with self.subTest(armor=a["name"]):
                for n in NUM.findall(a.get("desc", "")):
                    self.assertIn(int(n), {abs(a.get("dodge_bonus", 0)), a["base_def"], a.get("sockets")})
                if a.get("element"): self.assertIn(a["element"], a["desc"])

    def test_armor_data_traits_behave_as_described(self):
        for a in RAW_DATA["armors"]:
            with self.subTest(armor=a["name"]), mock.patch("entities.random.choice", side_effect=lambda seq: a if isinstance(seq, list) and a in seq else seq[0]):
                armor = generate_armor(5)
                if a.get("element"): self.assertEqual(armor.element, a["element"])
                self.assertEqual(armor.dodge_bonus, a.get("dodge_bonus", 0))
                if a.get("dodge_bonus"): self.assertIn(f"{a['dodge_bonus']:+d}% Schivata", a["desc"])
                if a.get("sockets"):
                    self.assertEqual(armor.sockets, a["sockets"])
                    self.assertIn(f"{a['sockets']} incastoni", a["desc"])

    def test_armor_dodge_bonus(self):
        veste = next(a for a in RAW_DATA["armors"] if a["name"] == "Veste Eterea")
        p = self.hero(); before = p.get_dodge()
        p.armor = Armor(veste["name"], 1, veste["base_def"], "Normale", 1, dodge_bonus=veste["dodge_bonus"])
        self.assertEqual(p.get_dodge(), before + veste["dodge_bonus"])
        self.assertIn(f"+{veste['dodge_bonus']}% Schivata", veste["desc"])

    def equip(self, p, acc):
        p.inventory = [acc]
        with quiet(), mock.patch("inventory_menu.interactive_menu", side_effect=[0, 0]), mock.patch("inventory_menu.clear_screen"), \
             mock.patch("builtins.input", return_value=""):
            inventory_menu.show_inventory_menu(p)
        self.assertIs(p.accessory, acc)

    def test_every_accessory_gives_the_bonus_in_its_description(self):
        for a in RAW_DATA["accessories"]:
            with self.subTest(accessory=a["name"]):
                self.assertEqual([int(n) for n in NUM.findall(a["desc"])], [a["bonus_value"]])
                p = self.hero(); p.base_acc = -60
                before = {"max_hp": p.max_hp, "dodge": p.get_dodge(), "acc": p.get_hit_chance(), "crit_chance": p.get_crit_chance(), "lifesteal": p.get_lifesteal()}
                acc = Accessory(a["name"], 1, "Normale", a["bonus_type"], a["bonus_value"], a["desc"])
                self.equip(p, acc)
                after = {"max_hp": p.max_hp, "dodge": p.get_dodge(), "acc": p.get_hit_chance(), "crit_chance": p.get_crit_chance(), "lifesteal": p.get_lifesteal()}
                if a["bonus_type"] == "reflect":
                    s = self.session(p); s.enemy.hp, s.enemy.base_acc, s.enemy.atk = 1000, 1000, 50
                    with quiet(), mock.patch("rooms.random.randint", side_effect=lambda lo, hi: 0 if lo == -1 else 1):
                        s.enemy_turn()
                    self.assertEqual(s.enemy.hp, 1000 - a["bonus_value"])
                else:
                    self.assertEqual(after[a["bonus_type"]] - before[a["bonus_type"]], a["bonus_value"])

    def test_cursed_accessories_show_their_real_bonus(self):
        seen = 0
        for seed in range(400):
            random.seed(seed)
            acc = generate_accessory(1)
            if acc.is_cursed:
                seen += 1
                with self.subTest(accessory=acc.name, seed=seed):
                    self.assertEqual([int(n) for n in NUM.findall(acc.desc)], [acc.bonus_value])
        self.assertGreater(seen, 0)


# ---------------------------------------------------------------- consumabili
class ConsumableContractTest(Sandbox):
    def contracts(self):
        return {"heal": self.c_heal, "antidote": self.c_antidote, "whetstone": self.c_whetstone, "smoke_bomb": self.c_smoke,
                "chaos_tome": self.c_tome, "accuracy_potion": self.c_accuracy, "holy_water": self.c_holy, "chaos_vial": self.c_vial,
                "rune_solvent": self.c_solvent, "socket_chisel": self.c_chisel}

    def item(self, category):
        d = next(c for c in RAW_DATA["consumables"] if c.get("category", "heal") == category)
        return d, Consumable(d["name"], 1, d["base_heal"] if category in ("heal", "antidote") else 0, category)

    def test_every_category_has_a_contract(self):
        self.assertEqual(set(self.contracts()), {c.get("category", "heal") for c in RAW_DATA["consumables"]})

    def test_every_consumable_does_what_it_says(self):
        for cat, check in self.contracts().items():
            with self.subTest(category=cat), quiet():
                self.setUp()
                check(*self.item(cat))

    def c_heal(self, d, item):
        p = self.hero(); p.max_hp, p.hp = 1000, 1; self.drink(p, item); self.assertEqual(p.hp, 1 + item.heal_amount)

    def c_antidote(self, d, item):
        p = self.hero(); p.max_hp, p.hp = 1000, 1; p.statuses = {"poison": 3, "bleed": 2}
        self.drink(p, item); self.assertEqual((p.statuses, p.hp), ({}, 1 + item.heal_amount))

    def c_whetstone(self, d, item):
        p = self.hero(); before = p.weapon.atk; self.drink(p, item)
        self.assertEqual(p.weapon.atk - before, int(NUM.findall(d["desc"])[0]))

    def c_smoke(self, d, item):
        p = self.hero(); self.assertEqual(self.drink(p, item, in_combat=True), "smoke_bomb")
        self.assertIn("Boss", d["desc"])
        s = self.session(p, boss=True)
        with quiet(), mock.patch("rooms.interactive_menu", return_value=2), mock.patch("rooms.clear_screen"), \
             mock.patch("rooms.show_inventory_menu", return_value="smoke_bomb"):
            self.assertTrue(s.player_turn(), "contro i Boss la fuga non riesce")

    def c_tome(self, d, item):
        p = self.hero()
        with mock.patch("inventory_menu.generate_random_element", return_value="Vento"): self.drink(p, item, in_combat=True)
        self.assertEqual(p.weapon.element, "Vento")

    def c_accuracy(self, d, item):
        p = self.hero(); p.base_acc = -500; s = self.session(p); self.drink(p, item, in_combat=True)
        self.assertEqual(p.get_hit_chance(s.enemy.base_dodge), 100)
        with quiet(): s._end_combat()
        self.assertLess(p.get_hit_chance(), 100, "vale solo per questo combattimento")

    def c_solvent(self, d, item):
        p = self.hero(); p.weapon.runes = ["forza"]; gold = p.gold
        self.drink(p, item)
        self.assertEqual(p.weapon.runes, [])
        self.assertEqual([i.rune_id for i in p.inventory if i.type == "rune"], ["forza"])
        self.assertEqual(p.gold, gold, "gratis: la descrizione lo promette")
        self.assertIn("gratis", d["desc"])
        p = self.hero(); p.inventory = [item]
        with quiet(), mock.patch("builtins.input", return_value=""): inventory_menu._use_consumable(p, item, 0, False)
        self.assertEqual(p.inventory, [item], "senza rune incastonate non si consuma")

    def c_chisel(self, d, item):
        top = GAME_DATA["runes"]["rules"]["sockets"]["boss"]
        self.assertIn(f"al massimo {top}", d["desc"])
        p = self.hero(); p.armor.sockets = top; before = p.weapon.sockets
        self.drink(p, item)
        self.assertEqual(p.weapon.sockets, before + 1)
        p = self.hero(); p.weapon.sockets = p.armor.sockets = top; p.inventory = [item]
        with quiet(), mock.patch("builtins.input", return_value=""): inventory_menu._use_consumable(p, item, 0, False)
        self.assertEqual((p.weapon.sockets, p.inventory), (top, [item]))

    def c_holy(self, d, item):
        p = self.hero(); p.weapon.is_cursed, p.weapon.curse_effect = True, "hp_drain"; self.drink(p, item)
        self.assertFalse(p.weapon.is_cursed); self.assertEqual(d["base_heal"], 0, "non cura: la descrizione non lo promette")

    def c_vial(self, d, item):
        for effect, check in {
            "heal_full": lambda p: self.assertEqual(p.hp, p.max_hp),
            "dmg": lambda p: self.assertEqual(p.hp, 1, "l'ustione non è letale"),
            "gold": lambda p: self.assertTrue(50 <= p.gold - 1000 <= 150),
            "max_hp": lambda p: self.assertEqual(p.max_hp, 210),
            "element": lambda p: self.assertEqual(p.weapon.element, "Luce"),
        }.items():
            with self.subTest(effetto=effect):
                p = self.hero(); p.max_hp, p.hp, p.gold = 200, (1 if effect in ("heal_full", "dmg") else 200), 1000
                with mock.patch("inventory_menu.random.choice", return_value=effect), mock.patch("inventory_menu.generate_random_element", return_value="Luce"):
                    self.assertEqual(self.drink(p, item, in_combat=True), "fiala_caos")
                check(p)
        p = self.hero(); s = self.session(p); s.enemy.hp = 1000
        with quiet(), mock.patch("rooms.interactive_menu", return_value=2), mock.patch("rooms.clear_screen"), \
             mock.patch("rooms.show_inventory_menu", return_value="fiala_caos"), mock.patch("rooms.random.randint", return_value=37):
            s.player_turn()
        self.assertEqual(s.enemy.hp, 963)
        self.assertIn("10-100", d["desc"])


# ---------------------------------------------------------------- eventi
class EventContractTest(Sandbox):
    """Il riepilogo accanto a ogni scelta è generato dagli effetti: qui si verifica che gli effetti facciano davvero
    ciò che dichiarano, per ogni scelta di ogni scena e per entrambi gli esiti delle scelte a probabilità."""

    def choices(self):
        for ev_id, ev in GAME_DATA["events"].items():
            for sc_id, scene in ev["scenes"].items():
                for i, choice in enumerate(scene["choices"]):
                    yield f"{ev_id}/{sc_id}/{i}", choice

    def snapshot(self, p):
        story = PROFILE_MANAGER._data["story"]
        return {"gold": p.gold, "hp": p.hp, "max_hp": p.max_hp, "atk": p.bonus_atk_relic, "def": p.bonus_def,
                "relics": len(p.relic_ids), "items": len(p.inventory), "quest": sorted(p.quest_items),
                "essence": p.essence_gathered, "exp": 0, "flags": dict(story["flags"]), "counters": dict(story["counters"]),
                "npcs": dict(PROFILE_MANAGER._data.get("npc_unlocked", {})), "pending": [list(x) for x in p.pending_events],
                "run_flags": sorted(p.run_flags), "fallen": p.fallen, "corruption": p.corruption}

    def expected(self, before, effects, floor):
        """Ciò che gli effetti dichiarano, calcolato senza passare dal motore degli eventi."""
        e = copy.deepcopy(before)
        for eff in effects:
            key = events.effect_key(eff); v = eff[key]
            if key == "gold": e["gold"] = max(0, e["gold"] + v)
            elif key == "damage": e["hp"] -= v
            elif key in ("heal", "heal_pct"): e["hp"] += min(v if key == "heal" else e["max_hp"] * v // 100, e["max_hp"] - e["hp"])
            elif key == "max_hp": e["max_hp"] += v; e["hp"] = min(e["hp"], e["max_hp"])
            elif key == "relic": e["relics"] += 1
            elif key in ("weapon", "armor", "accessory"): e["items"] += 1
            elif key == "potion": e["items"] += v
            elif key == "quest_item": e["quest"] = sorted(set(e["quest"]) | {v})
            elif key == "take_quest_item": e["quest"] = sorted(set(e["quest"]) - {v})
            elif key == "unlock_npc": e["npcs"][v] = True
            elif key in ("atk", "def"): e[key] += v
            elif key == "exp": e["exp"] += v
            elif key == "essence": e["essence"] += v
            elif key == "flag": e["flags"][v] = eff.get("value", True)
            elif key == "counter": e["counters"][v] = e["counters"].get(v, 0) + eff.get("add", 1)
            elif key == "later": e["pending"].append([floor + eff.get("floors", 1), v])
            elif key == "run_flag": e["run_flags"] = sorted(set(e["run_flags"]) | {v})
            elif key == "fall": e["gold"] -= e["gold"] * eff["gold_pct"] // 100; e["fallen"] = True
            elif key == "corruption": e["corruption"] = max(0, min(GAME_DATA["meta"]["corruption"]["max"], e["corruption"] + v))
            elif key != "fight": self.fail(f"effetto senza contratto: {key}")
        return e

    def play(self, choice, success):
        p = self.hero(); p.max_hp = 500; p.hp = 250; p.gold = 500
        p.corruption = 80  # sopra ogni soglia delle opzioni proibite, e con margine per misurare aumenti e cali
        p.quest_items = list(GAME_DATA["story"]["quest_items"])
        before = self.snapshot(p)
        exp = []
        won = lambda player, floor, enemy: setattr(enemy, "hp", 0)
        with quiet(), mock.patch("events.random.random", return_value=0.0 if success else 0.9999), \
             mock.patch("events.combat_room", side_effect=won), mock.patch("events.wait_enter"), \
             mock.patch.object(p, "gain_exp", side_effect=exp.append), \
             mock.patch("events.get_random_relic", return_value=next(r for r in RAW_DATA["relics"] if r["id"] == "tasca_dorata")):
            alive, nxt = events.run_choice(p, choice, 10)
        after = self.snapshot(p); after["exp"] = sum(exp)
        return before, after, alive, nxt

    def test_every_choice_does_what_its_text_says(self):
        for name, choice in self.choices():
            for success in ((True, False) if "chance" in choice else (True,)):
                with self.subTest(choice=name, success=success):
                    before, after, alive, nxt = self.play(choice, success)
                    outcome = choice.get("success" if success else "fail_effects", []) if "chance" in choice else []
                    self.assertTrue(alive)
                    self.assertEqual(after, self.expected(before, choice.get("effects", []) + outcome, 10))
                    self.assertEqual(nxt, choice.get("next") if success else choice.get("fail_next"))
                    label = events.choice_summary(choice)
                    for part in events.summarize(choice.get("effects", []) + outcome):
                        self.assertIn(part, label)

    def test_every_number_in_a_choice_is_checked(self):
        # I numeri compaiono solo nel riepilogo generato dagli effetti, mai scritti a mano nel testo della scelta
        for name, choice in self.choices():
            with self.subTest(choice=name):
                self.assertFalse(NUM.search(choice["text"]), f"numero scritto a mano in: {choice['text']}")
                if "chance" in choice:
                    self.assertTrue(0 < choice["chance"] < 100)
                    self.assertIn(f"{choice['chance']}%" if choice.get("success") else f"{100 - choice['chance']}%", events.choice_summary(choice))


# ---------------------------------------------------------------- tratti, patti, potenziamenti, Maestrie, imprese
class ObtainableTest(Sandbox):
    def test_every_unlockable_can_actually_be_obtained(self):
        granted = {f["reward_id"] for f in GAME_DATA["meta"]["feats"].values()}
        granted |= {m.get("id") for c in GAME_DATA["classes"].values() for m in c["mastery"].values()}
        granted |= set(roguelike.VICTORY_UNLOCKS)
        for cat in ("weapons", "armors", "accessories", "consumables", "relics"):
            for item in RAW_DATA[cat]:
                if item.get("unlock_id") and not item.get("unlock_cost"):
                    with self.subTest(item=item["name"]):
                        self.assertIn(item["unlock_id"], granted, "né in vendita alla Forgia né premio di imprese, Maestrie o vittoria")

    def test_a_fifth_relic_is_chosen_with_the_arrow_menu(self):
        p = self.hero()
        relics = [r for r in RAW_DATA["relics"] if r["id"] in ("tasca_dorata", "mantello_nebbioso", "tomo_conoscenza", "idolo_guerra", "occhio_cacciatore")]
        for r in relics[:4]: self.relic(p, r["id"])
        atk = p.get_total_atk()
        with quiet(), mock.patch("entities.interactive_menu", return_value=[r["id"] for r in p.relics].index("idolo_guerra")) as menu:
            p.add_relic(relics[4])
        self.assertEqual(len(menu.call_args.args[0]), 5, "4 reliquie da scartare + rinuncia")
        self.assertNotIn("idolo_guerra", p.relic_ids)
        self.assertIn(relics[4]["id"], p.relic_ids)
        self.assertEqual(p.get_total_atk(), atk - 5, "la reliquia scartata perde il suo effetto")
        with quiet(), mock.patch("entities.interactive_menu", side_effect=lambda options, prompt="": len(options) - 1):
            p.add_relic(next(r for r in RAW_DATA["relics"] if r["id"] == "lama_sangue"))
        self.assertNotIn("lama_sangue", p.relic_ids)

    def test_victory_unlocks_the_legendary_blade(self):
        PROFILE_MANAGER._data["unlocked_ids"] = []
        with quiet(): roguelike._grant_victory_rewards()
        self.assertIn("lama_creatore", PROFILE_MANAGER.unlocked_ids)
        self.assertIn("Lama del Creatore", [w["name"] for w in GAME_DATA["weapons"]])


class RulesContractTest(Sandbox):
    def test_every_trait_does_what_it_says(self):
        base = self.hero("1", "base")
        checks = {
            "base": lambda p: self.assertEqual((p.max_hp, p.gold), (base.max_hp, base.gold)),
            "maledetto": lambda p: (self.assertEqual(p.max_hp, base.max_hp // 2), self.assertEqual(p.heal(10), 0)),
            "midas": lambda p: (self.assertEqual(p.calculate_gold_gain(100), 300), self.assertEqual(self.exp_after(p, 50), 0)),
            "aristocratico": lambda p: self.assertEqual(p.gold, base.gold + 500),
            "cacciatore_etereo": lambda p: self.assertEqual(p.base_dodge, base.base_dodge - 20),
            "titano": lambda p: self.assertEqual((p.max_hp, p.base_acc, p.base_dodge), (base.max_hp + 100, base.base_acc // 2, base.base_dodge // 2)),
            "benedetto": lambda p: (self.assertIn("scudo_cristallo", p.relic_ids), self.assertTrue(p.take_damage(10 ** 6)), self.assertEqual(p.hp, 1)),
        }
        self.assertEqual(set(checks), set(GAME_DATA["meta"]["traits"]))
        for tid, check in checks.items():
            with self.subTest(trait=tid):
                with quiet(): p = Player("1", tid, [])
                check(p)
        self.assertIn("dimezzati", GAME_DATA["meta"]["traits"]["maledetto"]["desc"])

    def exp_after(self, p, amount):
        p.exp = 0
        with quiet(): p.gain_exp(amount)
        return p.exp

    def test_every_pact_does_what_it_says(self):
        def enemy(pacts):
            random.seed(7); return Enemy(10, False, pacts)
        def trap(pacts):
            p = self.hero(pacts=pacts); p.base_dodge = -100; p.max_hp = p.hp = 1000
            # Attraversa di corsa e fallisce la prova: il patto raddoppia il danno del meccanismo
            with quiet(), mock.patch("rooms.delay_print"), mock.patch("builtins.input", return_value=""), mock.patch("rooms.interactive_menu", return_value=1), \
                 mock.patch("rooms.random.randint", side_effect=lambda lo, hi: 100 if (lo, hi) == (1, 100) else 20):
                rooms.trap_room(p, 1, pacts)
            return 1000 - p.hp
        def potion(pacts):
            p = self.hero(pacts=pacts); p.max_hp, p.hp = 1000, 1
            self.drink(p, Consumable("Pozione", 1, 40, "heal")); return p.hp - 1
        checks = {
            "carestia": lambda: self.assertEqual(potion(["carestia"]), potion([]) // 2),
            "inflazione": lambda: self.assertEqual(self.vendor_prices(["inflazione"]), [v * 2 for v in self.vendor_prices([])]),
            "trappole": lambda: self.assertEqual(trap(["trappole"]), trap([]) * 2),
        }
        self.assertEqual(set(checks), set(GAME_DATA["meta"]["pacts"]))
        for pid, check in checks.items():
            with self.subTest(pact=pid): check()

    def vendor_prices(self, pacts):
        captured = []
        def menu(options, prompt="", cancellable=False, initial=0):
            if "COMPRA" in prompt: captured.extend(int(re.search(r"Prezzo: (?:\x1b\[[0-9;]*m)?(\d+) Oro", o).group(1)) for o in options); return -1
            return 0 if not captured else 2
        p = self.hero(pacts=pacts)
        random.seed(99)
        with quiet(), mock.patch("rooms.interactive_menu", side_effect=menu), mock.patch("rooms.clear_screen"), mock.patch("rooms.delay_print"):
            rooms.vendor_room(p, 3)
        return captured

    def test_every_numeric_perk_does_what_it_says(self):
        def gain(key, measure):
            PROFILE_MANAGER.set_perk(key, 0); before = measure()
            PROFILE_MANAGER.set_perk(key, 1); after = measure()
            PROFILE_MANAGER.set_perk(key, 0); return after - before
        new = lambda: Player("1", "base", [])
        def built(attr):
            def m():
                with quiet(): p = new()
                return attr(p)
            return m
        def regen():
            with quiet(): p = new()
            p.max_hp, p.hp = 200, 1
            with quiet(): return roguelike._apply_floor_regen(p)
        measured = {
            "hp_lvl": built(lambda p: p.max_hp), "gold_lvl": built(lambda p: p.gold),
            "dodge_lvl": built(lambda p: p.base_dodge), "acc_lvl": built(lambda p: p.base_acc),
            "exp_lvl": built(lambda p: round(p.exp_multiplier * 100)), "banca_anima_lvl": built(lambda p: p.calculate_gold_gain(100)),
            "artigiano_lvl": built(lambda p: p.weapon.atk), "pelle_dura_lvl": built(lambda p: p.armor.defense),
            "farmacista": built(lambda p: sum(1 for i in p.inventory if i.type == "consumable")),
            "speranza_luce_lvl": lambda: round(regen() * 100 / 200),
            # Lo sconto che, troncato all'Oro intero come fa il mercante, dà esattamente i prezzi visti
            "discount_lvl": lambda: -next(p for p in range(100) if [max(1, int(b * (1.0 - p / 100))) for b in self.base_prices] == self.vendor_prices([])),
        }
        not_numeric = {"sesto_senso", "altare_benedizione", "riciclatore_lvl"}
        PROFILE_MANAGER.set_perk("discount_lvl", 0); self.base_prices = self.vendor_prices([])
        for key, name, desc, *_ in roguelike.PERK_DEFS:
            if key in not_numeric: continue
            with self.subTest(perk=name):
                number = int(NUM.findall(desc)[0]) * (-1 if desc.startswith("-") else 1)
                self.assertEqual(gain(key, measured[key]), number)
        self.assertEqual(set(measured) | not_numeric, {k for k, *_ in roguelike.PERK_DEFS})

    def test_altar_and_recycler(self):
        PROFILE_MANAGER.set_perk("altare_benedizione", True)
        with quiet(): self.assertEqual(len(Player("1", "base", []).relic_ids), 1)
        PROFILE_MANAGER.set_perk("altare_benedizione", False)
        sold = {}
        for lvl in (0, 1):
            PROFILE_MANAGER.set_perk("riciclatore_lvl", lvl)
            p = self.hero(); p.inventory = [Weapon("Spada", 100, 1, "Normale", 1)]; gold = p.gold
            with quiet(), mock.patch("rooms.interactive_menu", side_effect=[1, 0, -1, 2]), mock.patch("rooms.clear_screen"), \
                 mock.patch("rooms.delay_print"), mock.patch("rooms.time.sleep"):
                rooms.vendor_room(p, 1)
            sold[lvl] = p.gold - gold
        self.assertEqual(sold[1], int(sold[0] * 1.10))

    def test_mastery_descriptions_match_their_bonuses(self):
        for cid, c in GAME_DATA["classes"].items():
            bonus = c["mastery"]["4"]["bonus"]
            value = round(bonus["value"] * 100) if bonus["value"] < 1 else bonus["value"]
            with self.subTest(class_id=cid):
                self.assertIn(str(value), c["mastery"]["4"]["desc"])
        PROFILE_MANAGER.set_class_lvl("5", 2)
        with quiet(): berserker = Player("5", "base", [])
        berserker.base_dodge = 50; berserker.hp = 1
        self.assertEqual((berserker.get_dodge(), berserker.get_class_damage_multiplier()), (0, 1.5))
        self.assertIn("Schivata scende a 0", GAME_DATA["classes"]["5"]["mastery"]["2"]["desc"])

    def test_every_feat_has_the_threshold_its_text_says(self):
        def run(setup, floor=5):
            PROFILE_MANAGER._data["completed_feats"] = []
            PROFILE_MANAGER._data["stats"]["total_bosses"] = 0
            p = self.hero(); p.run_tracker = {"escapes": 0, "fusions": 0}; p.escaped = False
            setup(p)
            with quiet(): roguelike._check_feats(p, getattr(p, "_floor", floor), False)
            return PROFILE_MANAGER._data["completed_feats"]
        def tr(**kv): return lambda p: p.run_tracker.update(kv)
        def at_floor(n, **kv): return lambda p: (setattr(p, "_floor", n), p.run_tracker.update(kv))
        def escaped_with(gold): return lambda p: (setattr(p, "escaped", True), setattr(p, "gold", gold))
        def bosses(n): return lambda p: (PROFILE_MANAGER._data["stats"].update(total_bosses=n - 1), setattr(p, "bosses_killed", 1))
        def elements(w, a): return lambda p: (setattr(p, "escaped", True), setattr(p.weapon, "element", w), setattr(p.armor, "element", a))
        table = {   # impresa: (numero nel testo o None, setup che la completa, setup appena sotto la soglia)
            "feat_pacifista": (10, tr(escapes=10), tr(escapes=9)),
            "feat_fabbro": (3, tr(fusions=3), tr(fusions=2)),
            "feat_vetro": (None, tr(no_hit_boss_done=True), tr()),
            "feat_suicida": (1, tr(kill_1_hp_done=True), tr()),
            "feat_avaro": (2000, escaped_with(2000), escaped_with(1999)),
            "feat_genio_elementale": (5, tr(max_fused_weapon_lvl=5), tr(max_fused_weapon_lvl=4)),
            "feat_sopravvissuto": (10, at_floor(11), at_floor(10)),
            "feat_epuratore": (10, bosses(10), bosses(9)),
            "feat_mani_bucate": (2000, tr(gold_spent=2000), tr(gold_spent=1999)),
            "feat_equilibrista": (None, elements("Fuoco", "Acqua"), elements("Fuoco", "Fuoco")),
            "feat_lama_cristallo": (15, at_floor(15), at_floor(14)),
            "feat_furia_cieca": (None, tr(blind_fury_done=True), tr()),
            "feat_tiratore_scelto": (5, tr(super_effective_hits=5), tr(super_effective_hits=4)),
            "feat_assaggiatore": (1, tr(**{"1_hp_survive": True}), tr()),
        }
        self.assertEqual(set(table), set(GAME_DATA["meta"]["feats"]))
        for fid, (number, done, below) in table.items():
            with self.subTest(feat=fid):
                if number is not None: self.assertIn(str(number), GAME_DATA["meta"]["feats"][fid]["desc"])
                self.assertIn(fid, run(done))
                self.assertNotIn(fid, run(below))


if __name__ == "__main__":
    unittest.main()


# ---------------------------------------------------------------- mosse dei nemici e reazioni elementali
class MoveContractTest(Sandbox):
    """Ogni mossa annunciata fa ciò che dice la sua descrizione."""

    def setup_fight(self, intent, defending=False):
        p = self.hero(); p.max_hp = p.hp = 1000
        p.armor = Armor("Nessuna", 0, 0, "Normale", 1)
        p.bonus_def = 0
        s = self.session(p, 10)
        self.assertEqual(p.get_total_def(), 0)
        s.enemy.hp = s.enemy.max_hp = 500
        s.enemy.atk, s.enemy.element, s.enemy.base_acc = 20, "Normale", 50
        s.enemy.status_inflict = {"type": "poison", "chance": 0, "duration": 3}
        s.intent, s.is_defending = intent, defending
        return p, s

    def enemy_hit(self, intent, defending=False):
        p, s = self.setup_fight(intent, defending)
        # Ogni tiro al minimo: il colpo va a segno, il danno è il più basso, lo status a probabilità 0 non scatta
        with quiet(), mock.patch("rooms.random.randint", side_effect=lambda a, b: a), mock.patch("rooms.wait_enter"):
            s.enemy_turn()
        return p, s

    def test_every_move_has_a_contract(self):
        self.assertEqual(set(GAME_DATA["moves"]["moves"]), {"attack", "heavy", "guard", "heal", "venom", "drain", "seal", "charge", "unleash", "shield"})

    def test_drain_heals_as_much_as_it_hurts(self):
        m = GAME_DATA["moves"]["moves"]["drain"]
        self.assertEqual(m["heal_ratio"], 1)
        self.assertIn("tanti HP quanti te ne toglie", m["desc"])
        normal = 1000 - self.enemy_hit("attack")[0].hp
        p, s = self.setup_fight("drain"); s.enemy.hp = 100
        with quiet(), mock.patch("rooms.random.randint", side_effect=lambda a, b: a), mock.patch("rooms.wait_enter"):
            s.enemy_turn()
        self.assertEqual(1000 - p.hp, normal)
        self.assertEqual(s.enemy.hp, 100 + normal)

    def test_seal_forbids_defending_for_one_turn(self):
        self.assertIn("non potrai difenderti", GAME_DATA["moves"]["moves"]["seal"]["desc"])
        p, s = self.enemy_hit("seal")
        self.assertEqual(p.hp, 1000, "il Sigillo non attacca")
        self.assertTrue(s.sealed)
        picks = iter([1, 0])  # prova a difendersi, poi attacca
        with quiet(), mock.patch("rooms.interactive_menu", side_effect=lambda *a, **k: next(picks)), mock.patch("rooms.clear_screen"), \
             mock.patch("rooms.random.randint", return_value=100):
            s.player_turn()
        self.assertFalse(s.is_defending)
        self.assertEqual(next(picks, "finito"), "finito", "la difesa sigillata non consuma il turno")

    def test_charge_announces_the_unleashed_blow(self):
        charge, unleash = GAME_DATA["moves"]["moves"]["charge"], GAME_DATA["moves"]["moves"]["unleash"]
        self.assertIn("Colpo caricato", charge["desc"])
        self.assertIn(f"×{unleash['damage_mult']}", unleash["desc"])
        p, s = self.enemy_hit("charge")
        self.assertEqual(p.hp, 1000, "la Carica non attacca")
        self.assertEqual(s.enemy.choose_move(), "unleash")
        self.assertNotEqual(s.enemy.choose_move(), "unleash", "il Colpo caricato arriva una volta sola")
        normal = 1000 - self.enemy_hit("attack")[0].hp
        self.assertEqual(1000 - self.enemy_hit("unleash")[0].hp, normal * unleash["damage_mult"])
        self.assertIn("Difenditi per dimezzare", unleash["desc"])
        self.assertEqual(1000 - self.enemy_hit("unleash", defending=True)[0].hp, normal * unleash["damage_mult"] // 2)
        p, s = self.setup_fight("charge")
        self.assertIn(f"≈{s.estimate_enemy_damage(unleash['damage_mult'])} danni", s.intent_text())

    def test_shield_absorbs_attacks(self):
        m = GAME_DATA["moves"]["moves"]["shield"]
        self.assertIn(f"{m['shield_pct']}% degli HP massimi", m["desc"])
        p, s = self.enemy_hit("shield")
        self.assertEqual(p.hp, 1000)
        self.assertEqual(s.enemy.shield, 500 * m["shield_pct"] // 100)
        dealt = {}
        for shield in (0, 30):
            p, s = self.setup_fight("attack"); s.enemy.shield = shield
            p.weapon.element = "Normale"
            with quiet(), mock.patch("rooms.random.randint", return_value=1):
                s.execute_player_attack()
            dealt[shield] = 500 - s.enemy.hp
        self.assertEqual(dealt[30], max(0, dealt[0] - 30))

    def test_heavy_blow(self):
        desc = GAME_DATA["moves"]["moves"]["heavy"]["desc"]
        mult = GAME_DATA["moves"]["moves"]["heavy"]["damage_mult"]
        self.assertIn(f"×{mult}", desc)
        normal = 1000 - self.enemy_hit("attack")[0].hp
        heavy = 1000 - self.enemy_hit("heavy")[0].hp
        self.assertEqual(heavy, normal * mult)
        self.assertIn("Difenditi per dimezzare", desc)
        self.assertEqual(1000 - self.enemy_hit("heavy", defending=True)[0].hp, heavy // 2)

    def test_guard(self):
        m = GAME_DATA["moves"]["moves"]["guard"]
        self.assertIn(f"{int(m['damage_taken_mult'] * 100)}% dei danni", m["desc"])
        p, s = self.enemy_hit("guard")
        self.assertEqual(p.hp, 1000, "la guardia non attacca")
        dealt = {}
        for intent in ("attack", "guard"):
            p, s = self.setup_fight(intent)
            p.weapon.element = "Normale"
            with quiet(), mock.patch("rooms.random.randint", return_value=1):
                s.execute_player_attack()
            dealt[intent] = 500 - s.enemy.hp
        self.assertEqual(dealt["guard"], int(dealt["attack"] * m["damage_taken_mult"]))

    def test_heal(self):
        m = GAME_DATA["moves"]["moves"]["heal"]
        self.assertIn(f"{m['heal_pct']}% degli HP massimi", m["desc"])
        p, s = self.setup_fight("heal")
        s.enemy.hp = 100
        with quiet(): s.enemy_turn()
        self.assertEqual(s.enemy.hp, 100 + 500 * m["heal_pct"] // 100)
        self.assertEqual(p.hp, 1000)

    def test_venom_always_inflicts_its_status(self):
        self.assertIn("se ti ferisce", GAME_DATA["moves"]["moves"]["venom"]["desc"])
        p, s = self.enemy_hit("venom")
        self.assertIn("poison", p.statuses)
        p, s = self.enemy_hit("attack")
        self.assertNotIn("poison", p.statuses)
        p, s = self.setup_fight("venom")
        # Nessuna armatura annulla più un colpo; lo fa lo Scudo di Cristallo, e senza ferita niente status
        with quiet(): p.add_relic(next(r for r in RAW_DATA["relics"] if r["id"] == "scudo_cristallo"))
        s = self.session(p, 10); s.enemy.atk, s.enemy.base_acc, s.intent = 20, 100, "venom"
        s.enemy.status_inflict = {"type": "poison", "chance": 0, "duration": 3}
        with quiet(), mock.patch("rooms.random.randint", side_effect=lambda a, b: a), mock.patch("rooms.wait_enter"):
            s.enemy_turn()
        self.assertNotIn("poison", p.statuses)

    def test_intent_estimate_is_the_real_damage(self):
        for intent in ("attack", "heavy"):
            p, s = self.setup_fight(intent)
            estimate = s.estimate_enemy_damage(GAME_DATA["moves"]["moves"][intent].get("damage_mult", 1))
            self.assertIn(f"≈{estimate} danni", s.intent_text())
            with quiet(), mock.patch("rooms.random.randint", return_value=0), mock.patch("rooms.wait_enter"):
                s.enemy_turn()
            self.assertEqual(1000 - p.hp, estimate)


class ReactionContractTest(Sandbox):
    """Ogni reazione elementale fa ciò che dice la sua descrizione."""
    PATTERN = re.compile(r"(\d+)% del tuo ATK|(-\d+)% (Precisione|Schivata)|(\d+)% degli HP massimi|per (\d+) turni|prossimo turno")

    def react(self, key):
        a, b = key.split("+")
        p = self.hero(); p.weapon.atk = 40
        s = self.session(p, 10)
        s.enemy.hp = s.enemy.max_hp = 1000
        s.enemy.mark = [a, 2]
        with quiet(): s.apply_element(b)
        return p, s

    def test_every_reaction_has_a_contract(self):
        statuses = {"stun", "blind", "slow", "scorch"}
        for key, r in GAME_DATA["elements"]["reactions"].items():
            with self.subTest(reaction=key):
                a, b = key.split("+")
                self.assertTrue({a, b} <= set(GAME_DATA["elements"]["list"]) - {"Normale"})
                self.assertTrue(r.get("bonus_pct") or r.get("status"))
                if r.get("status"): self.assertIn(r["status"]["type"], statuses)
                rest = self.PATTERN.sub("", r["desc"])
                self.assertFalse(NUM.search(rest), f"numero non verificato: {r['desc']}")

    def test_every_reaction_does_what_it_says(self):
        cond = GAME_DATA["elements"]["conditions"]
        for key, r in GAME_DATA["elements"]["reactions"].items():
            with self.subTest(reaction=key):
                p, s = self.react(key)
                desc = r["desc"]
                self.assertIsNone(s.enemy.mark, "la reazione consuma il marchio")
                bonus = r.get("bonus_pct", 0)
                if bonus: self.assertIn(f"{bonus}% del tuo ATK", desc)
                self.assertEqual(1000 - s.enemy.hp, p.get_total_atk() * bonus // 100)
                st = r.get("status")
                if not st:
                    self.assertEqual(s.enemy.statuses, {})
                    continue
                self.assertEqual(s.enemy.statuses, {st["type"]: st["duration"]})
                if st["type"] == "stun": self.assertIn("perde il suo prossimo turno", desc)
                else: self.assertIn(f"per {st['duration']} turni", desc)
                if st["type"] == "blind": self.assertIn(f"-{cond['blind']}% Precisione", desc)
                if st["type"] == "slow": self.assertIn(f"-{cond['slow']}% Schivata", desc)
                if st["type"] == "scorch": self.assertIn(f"{cond['scorch_pct']}% degli HP massimi", desc)

    def test_conditions_do_what_the_descriptions_say(self):
        cond = GAME_DATA["elements"]["conditions"]
        p = self.hero()
        s = self.session(p, 10)
        s.enemy.base_acc, s.enemy.base_dodge = 0, 30
        hit, chance = s._calc_enemy_hit_chance(1.0), s._calc_hit_chance(1.0)
        s.enemy.statuses = {"blind": 2, "slow": 2}
        self.assertEqual(s._calc_enemy_hit_chance(1.0), max(10, hit - cond["blind"]))
        self.assertEqual(s._calc_hit_chance(1.0), min(100, chance + cond["slow"]) if chance + cond["slow"] <= 100 else s._calc_hit_chance(1.0))
        # Magma: il 5% degli HP massimi a ogni turno, per 3 turni
        s.enemy.statuses = {"scorch": 3}
        s.enemy.hp = s.enemy.max_hp = 400
        with quiet():
            for _ in range(4): s.process_statuses_and_curses(is_player_turn=False)
        self.assertEqual(400 - s.enemy.hp, 3 * 400 * cond["scorch_pct"] // 100)
        # Gelo: il nemico perde il turno
        s.enemy.statuses = {"stun": 1}
        p.hp = 100
        with quiet(): s.enemy_turn()
        self.assertEqual(p.hp, 100)
        self.assertNotIn("stun", s.enemy.statuses)
