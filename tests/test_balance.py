"""Invarianti di bilanciamento: nessuna immunità, nessun muro iniziale, oggetti e boss che crescono con i nemici.

I numeri non sono fissati qui: i test controllano proporzioni rispetto al nemico tipico del piano,
così un'arma, un'armatura o un boss aggiunti ai dati devono rispettare le stesse regole.
"""
import io
import random
import statistics as st
import unittest
from contextlib import redirect_stdout
from unittest import mock

import entities
from constants import CURSE_HP_DRAIN_PCT, MIN_DAMAGE_PCT, POISON_MIN, POISON_PCT
from data_manager import GAME_DATA, RAW_DATA
from entities import Armor, Enemy, Player, typical_enemy
from rooms import CombatSession

FLOORS = (1, 3, 5, 8, 10, 15, 20, 25, 30)


def quiet():
    return redirect_stdout(io.StringIO())


def sample(generator, data_key, entry, level, n=150):
    """Oggetti generati di un solo tipo (es. solo l'Egida del Titano) a un livello."""
    real = entities.random.choice
    with mock.patch("entities.random.choice", side_effect=lambda seq: entry if seq is GAME_DATA[data_key] else real(seq)):
        return [generator(level) for _ in range(n)]


class ItemCurveTest(unittest.TestCase):
    def setUp(self):
        random.seed(5)

    def test_weapons_never_one_shot_and_never_drag(self):
        for w in RAW_DATA["weapons"]:
            for f in FLOORS:
                with self.subTest(weapon=w["name"], floor=f):
                    hits = typical_enemy(f)[0] / st.median(x.atk for x in sample(entities.generate_weapon, "weapons", w, f))
                    self.assertGreater(hits, 1.5, "un'arma comune non abbatte un nemico tipico al primo colpo")
                    self.assertLess(hits, 5.0)

    def test_armors_never_absorb_everything(self):
        for a in RAW_DATA["armors"]:
            for f in FLOORS:
                with self.subTest(armor=a["name"], floor=f):
                    atk = typical_enemy(f)[1]
                    absorbed = st.median(x.defense for x in sample(entities.generate_armor, "armors", a, f)) / atk
                    self.assertGreater(absorbed, 0.1)
                    self.assertLess(absorbed, 0.75, "nessuna armatura comune annulla il colpo tipico")

    def test_quality_keeps_its_rank_on_every_floor(self):
        weapons = sorted(RAW_DATA["weapons"], key=lambda w: w["base_atk"])
        for f in (1, 15, 30):
            low = st.median(x.atk for x in sample(entities.generate_weapon, "weapons", weapons[0], f, 300))
            high = st.median(x.atk for x in sample(entities.generate_weapon, "weapons", weapons[-1], f, 300))
            with self.subTest(floor=f):
                self.assertGreater(high / low, 1.3)
                self.assertLess(high / low, 1.8)

    def test_the_typical_enemy_follows_the_real_enemies(self):
        for f in (1, 10, 20, 30):
            with self.subTest(floor=f):
                hp, atk = typical_enemy(f)
                with mock.patch("entities.get_biome", return_value=None):
                    real = [Enemy(f, False, []) for _ in range(400)]
                self.assertAlmostEqual(st.mean(e.hp for e in real) / hp, 1, delta=0.2)
                self.assertAlmostEqual(st.mean(e.atk for e in real) / atk, 1, delta=0.2)


class BossCurveTest(unittest.TestCase):
    def test_bosses_scale_with_their_floor(self):
        random.seed(6)
        ratios = []
        for f in FLOORS:
            hp, atk = typical_enemy(f)
            bosses = [Enemy(f, True, []) for _ in range(200)]
            r_hp, r_atk = st.median(b.hp for b in bosses) / hp, st.median(b.atk for b in bosses) / atk
            ratios.append(r_hp)
            with self.subTest(floor=f):
                self.assertGreater(r_hp, 1.5)
                self.assertLess(r_hp, 3.5, "niente muro: i primi boss non sono molto più duri degli ultimi")
                self.assertLess(r_atk, 3.0)
        self.assertLess(max(ratios) / min(ratios), 1.8)


class DamageRulesTest(unittest.TestCase):
    def session(self, defense=10_000):
        with quiet():
            p = Player("1", "base", [])
            s = CombatSession(p, 10, Enemy(10, False, []))
        p.armor = Armor("Prova", 0, defense, "Normale", 1)
        s.enemy.atk, s.enemy.element = 50, "Normale"
        return p, s

    def test_defense_never_blocks_a_hit_entirely(self):
        p, s = self.session()
        with mock.patch("rooms.random.randint", return_value=0):
            dmg = s._calc_enemy_damage(1.0)
            self.assertEqual(dmg, -(-50 * MIN_DAMAGE_PCT // 100))
            self.assertEqual(s.estimate_enemy_damage(), dmg)

    def test_defense_still_matters_below_the_floor(self):
        p, s = self.session(defense=20)
        with mock.patch("rooms.random.randint", return_value=0):
            self.assertEqual(s._calc_enemy_damage(1.0), 30)

    def test_curse_drain_and_poison_scale_with_max_hp(self):
        p, s = self.session()
        p.max_hp = p.hp = 1000
        p.weapon.is_cursed, p.weapon.curse_effect = True, "hp_drain"
        p.statuses = {"poison": 3}
        with quiet(): s.process_statuses_and_curses(is_player_turn=True)
        self.assertEqual(1000 - p.hp, 1000 * CURSE_HP_DRAIN_PCT // 100 + max(POISON_MIN, 1000 * POISON_PCT // 100))


if __name__ == "__main__":
    unittest.main()
