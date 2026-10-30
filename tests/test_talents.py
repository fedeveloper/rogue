"""I talenti: dati e testi, un talento ogni `every` livelli, proposta e scelta, effetto di ogni chiave propria,
il Tomo dell'Oblio, la scelta a fine stanza e le Statistiche."""
import copy
import io
import random
import re
import unittest
from contextlib import redirect_stdout
from unittest import mock

import attributes
import effects
import inventory_menu
import magic
import talents
from data_manager import GAME_DATA, PROFILE_MANAGER
from entities import Armor, Consumable, Enemy, Player, Weapon
from rooms import CombatSession
from rooms_patch import patch_rooms

ANSI = re.compile(r"\x1b\[[0-9;]*m")
TALENTS, RULES = GAME_DATA["talents"]["talents"], GAME_DATA["talents"]["rules"]
ATTRIBUTE_KEYS = {k for a in GAME_DATA["attributes"]["attributes"].values() for k in a["per_point"]} - {"scaled_dmg_pct"}


def quiet():
    return redirect_stdout(io.StringIO())


def fx(tid, key):
    return TALENTS[tid]["effects"][key]


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        self._save = mock.patch.object(PROFILE_MANAGER, "save")
        self._save.start()
        random.seed(5)

    def tearDown(self):
        self._save.stop()
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)

    def hero(self, *owned):
        """Un eroe senza attributi, con i talenti indicati."""
        with quiet(): p = Player("1", "base", [])
        for a in p.attributes: p.attributes[a] = 0
        p.talents = list(owned)
        return p

    def fight(self, p):
        p.weapon, p.armor, p.base_acc = Weapon("Lama", 1, 100, "Normale", 1), Armor("Corazza", 1, 40, "Normale", 1), 1000
        with quiet(): s = CombatSession(p, 3, Enemy(3, False, [], name="Goblin"))
        s.enemy.hp = s.enemy.max_hp = 10 ** 6
        s.enemy.element, s.enemy.base_dodge, s.intent = "Normale", 0, "attack"
        return s

    def strike(self, p):
        s = self.fight(p)
        with quiet(), mock.patch("rooms.random.randint", side_effect=lambda a, b: b if b == 100 else 0), mock.patch("entities.random.randint", return_value=100):
            s.execute_player_attack()
        return s


class DataTest(Sandbox):
    def test_the_texts_tell_the_numbers_and_the_keys_are_known(self):
        self.assertIn(f"Ogni {RULES['every']} livelli", RULES["desc"])
        self.assertIn(f"fra {RULES['offered']} proposti", RULES["desc"])
        self.assertGreaterEqual(len(TALENTS), 3 * RULES["offered"], "abbastanza talenti per più scelte diverse")
        for tid, t in TALENTS.items():
            with self.subTest(talent=tid):
                self.assertTrue(t["name"] and t["icon"] and t["desc"] and t["effects"])
                for key, v in t["effects"].items():
                    self.assertIn(key, ATTRIBUTE_KEYS | set(talents.TALENT_EFFECT_KEYS))
                    self.assertIn(str(v), t["desc"])
        used = {k for t in TALENTS.values() for k in t["effects"]}
        self.assertLessEqual(set(talents.TALENT_EFFECT_KEYS), used, "ogni chiave propria è usata da un talento")


class EarnTest(Sandbox):
    def test_a_talent_every_few_levels(self):
        p = self.hero()
        while p.level < 2 * RULES["every"] + 1:
            with quiet(): p.gain_exp(p.max_exp - p.exp)
            self.assertEqual(p.pending_talents, p.level // RULES["every"], f"livello {p.level}")

    def test_the_offer_never_repeats_what_the_hero_has(self):
        owned = list(TALENTS)[:-2]
        p = self.hero(*owned)
        self.assertEqual(sorted(talents.offer(p)), sorted(list(TALENTS)[-2:]))
        offer = talents.offer(self.hero())
        self.assertEqual(len(offer), RULES["offered"])
        self.assertEqual(len(set(offer)), len(offer))

    def test_choosing_takes_the_picked_talent(self):
        p = self.hero(); p.pending_talents, hp = 1, p.max_hp
        with quiet(), mock.patch("talents.offer", return_value=["lama_affilata", "cuore_saldo", "flusso"]), \
             mock.patch("talents.interactive_menu", return_value=1), mock.patch("talents.clear_screen"):
            talents.choose(p)
        self.assertEqual((p.talents, p.pending_talents, p.max_hp), (["cuore_saldo"], 0, hp + fx("cuore_saldo", "max_hp")))

    def test_with_every_talent_taken_nothing_is_asked(self):
        p = self.hero(*TALENTS); p.pending_talents = 1
        with quiet(), mock.patch("talents.interactive_menu") as menu:
            talents.choose(p)
        menu.assert_not_called()
        self.assertEqual(p.pending_talents, 0)

    def test_the_tome_of_oblivion_keeps_talents(self):
        p = self.hero("cuore_saldo"); p.unspent_points = 1
        attributes.raise_attribute(p, "forza")
        attributes.reset(p)
        self.assertEqual(p.talents, ["cuore_saldo"])

    def test_the_choice_comes_at_the_end_of_the_room_before_the_points(self):
        """In una discesa vera, giocata dal bot del simulatore: ogni volta che si spendono i punti, i talenti guadagnati
        sono già stati scelti."""
        import os, sys
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
        import bilanciamento
        real_choose, real_spend, seen = talents.choose, attributes.spend_points, []
        def choose(player):
            seen.append(("talento", player.level)); return real_choose(player)
        def spend(player):
            seen.append(("punti", player.level, player.pending_talents)); return real_spend(player)
        with mock.patch.object(talents, "choose", side_effect=choose), mock.patch.object(attributes, "spend_points", side_effect=spend):
            bilanciamento.play("1", 100003, bilanciamento.profile("completo"))
        self.assertIn("talento", [e[0] for e in seen], "la discesa arriva a un talento")
        for e in seen:
            if e[0] == "punti": self.assertEqual(e[2], 0, f"punti spesi al livello {e[1]} con un talento ancora da scegliere")


class EffectTest(Sandbox):
    def test_attribute_keys_add_up_with_the_attributes(self):
        base, hawk = self.hero(), self.hero("occhio_falco")
        self.assertEqual(hawk.get_crit_chance() - base.get_crit_chance(), fx("occhio_falco", "crit"))
        self.assertEqual(effects.total(hawk, "acc"), fx("occhio_falco", "acc"))
        self.assertEqual(self.hero("pozzo_etere").max_ether() - base.max_ether(), fx("pozzo_etere", "ether_max"))

    def test_damage_for_any_weapon(self):
        plain = 10 ** 6 - self.strike(self.hero()).enemy.hp
        sharp = 10 ** 6 - self.strike(self.hero("lama_affilata")).enemy.hp
        self.assertEqual(sharp, plain * (100 + fx("lama_affilata", "dmg_pct")) // 100)

    def test_defense_lifesteal_and_exp(self):
        base = self.hero(); base.armor = Armor("Corazza", 1, 40, "Normale", 1)
        iron = self.hero("pelle_ferro"); iron.armor = Armor("Corazza", 1, 40, "Normale", 1)
        self.assertEqual(iron.get_total_def() - base.get_total_def(), 40 * fx("pelle_ferro", "def_pct") // 100)
        self.assertEqual(self.hero("sete_sangue").get_lifesteal() - base.get_lifesteal(), fx("sete_sangue", "lifesteal"))
        scholar = self.hero("studioso")
        with quiet(): base.gain_exp(50); scholar.gain_exp(50)
        self.assertEqual(scholar.exp, int(50 * (base.exp_multiplier + fx("studioso", "exp_pct") / 100)))

    def test_ether_on_hit(self):
        base, flow = self.hero(), self.hero("flusso")
        for p in (base, flow): p.base_ether, p.ether = 100, 0
        self.assertEqual(self.strike(flow).player.ether - self.strike(base).player.ether, fx("flusso", "ether_on_hit"))

    def test_spells_cost_less_but_never_nothing(self):
        p = self.hero("parsimonia")
        for sid, s in GAME_DATA["spells"]["spells"].items():
            with self.subTest(spell=sid):
                self.assertEqual(magic.cost(p, sid), max(1, s["cost"] - fx("parsimonia", "spell_discount") - (GAME_DATA["spells"]["rules"]["resonance_discount"] if s["element"] == p._get_resonance_element() else 0)))
        sid = next(sid for sid, s in GAME_DATA["spells"]["spells"].items() if s["cost"] > 2)
        self.assertIn("sconto", ANSI.sub("", magic.label(p, sid)))

    def test_harvest_heals_on_every_kill(self):
        p = self.hero("raccolto"); p.max_hp, p.hp = 1000, 100
        s = self.fight(p); s.enemy.exp_drop = s.enemy.gold_drop = 0
        with quiet(), patch_rooms("wait_enter"), patch_rooms("get_random_relic", return_value=None):
            s.on_enemy_death()
        self.assertEqual(p.hp, 100 + 1000 * fx("raccolto", "kill_heal_pct") // 100)

    def test_potions_heal_more(self):
        healed = []
        for owned in ((), ("erborista",)):
            p = self.hero(*owned); p.max_hp, p.hp, p.alchemist_potions = 1000, 100, False
            potion = Consumable("Pozione", 1, 100); p.inventory = [potion]
            with quiet(), mock.patch("inventory_menu.wait_enter"):
                inventory_menu._use_consumable(p, potion, 0, False)
            healed.append(p.hp - 100)
        self.assertEqual(healed[1], healed[0] * (100 + fx("erborista", "potion_pct")) // 100)

    def test_the_stats_show_the_talents(self):
        p = self.hero("flusso", "raccolto")
        out = io.StringIO()
        with redirect_stdout(out), mock.patch("inventory_menu.wait_enter"), mock.patch("inventory_menu.clear_screen"):
            inventory_menu.show_player_stats(p)
        text = ANSI.sub("", out.getvalue())
        self.assertIn(TALENTS["flusso"]["name"], text)
        self.assertIn(TALENTS["raccolto"]["name"], text)


if __name__ == "__main__":
    unittest.main()
