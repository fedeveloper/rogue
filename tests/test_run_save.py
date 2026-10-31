"""Il salvataggio a metà discesa (`run_save.py`): una discesa salvata e ripresa finisce come se non si fosse mai fermata,
il file si cancella appena caricato, un salvataggio rotto o di un'altra versione non blocca il menu."""
import copy
import hashlib
import importlib
import io
import json
import os
import random
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

import modes
import roguelike
import run_save
from data_manager import CYCLE, GAME_DATA, PROFILE_MANAGER, RAW_DATA, default_profile, set_cycle_seed, update_game_data
import entities
from entities import Player, Rune, generate_weapon
from relic_effects import create_relic_effect

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
bilanciamento = importlib.import_module("bilanciamento")  # il simulatore sta in tools/, fuori dai pacchetti del gioco


# L'impronta degli attributi degli oggetti salvati, per ogni SAVE_VERSION. Se un attributo nasce o sparisce, un
# salvataggio vecchio non sarebbe più giusto: si alza SAVE_VERSION e si aggiunge qui la nuova impronta.
SCHEMA = {1: "d9b9ecd8dc3c2990"}


def schema_hash() -> str:
    """Con un profilo nuovo e tutte le reliquie dei dati, così non dipende dal profilo di chi esegue i test."""
    PROFILE_MANAGER._data.clear(); PROFILE_MANAGER._data.update(default_profile()); update_game_data()
    random.seed(0)
    with redirect_stdout(io.StringIO()):
        objs = [entities.Player("1", "base", []), entities.Enemy(5, False, []), entities.Enemy(5, True, []),
                entities.generate_weapon(5), entities.generate_armor(5), entities.generate_accessory(5), entities.generate_potion(5),
                entities.generate_rune(5), entities.generate_scroll(5)] + [create_relic_effect(r["id"]) for r in RAW_DATA["relics"]]
    attrs = {}
    for o in objs: attrs.setdefault(f"{type(o).__module__}.{type(o).__qualname__}", set()).update(vars(o))
    return hashlib.sha256(repr(sorted((k, sorted(v)) for k, v in attrs.items())).encode("utf-8")).hexdigest()[:16]


def quiet():
    return redirect_stdout(io.StringIO())


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._saved = copy.deepcopy(PROFILE_MANAGER._data)
        self._save = mock.patch.object(PROFILE_MANAGER, "save")
        self._save.start()
        self.tmp = tempfile.mkdtemp()
        self._file = mock.patch.object(run_save, "SAVE_FILE", os.path.join(self.tmp, "run_save.json"))
        self._file.start()

    def tearDown(self):
        self._file.stop()
        self._save.stop()
        shutil.rmtree(self.tmp)
        PROFILE_MANAGER._data.clear()
        PROFILE_MANAGER._data.update(self._saved)
        update_game_data()
        modes.end_run()


class FormatTest(Sandbox):
    def test_a_hero_comes_back_with_everything(self):
        with quiet(): p = Player("3", "base", [])
        p.inventory.append(generate_weapon(5)); p.inventory.append(Rune("eco"))
        p.weapon.sockets, p.weapon.runes = 2, ["eco"]
        p.seen_events, p.run_flags = {"altare_sangue", "fontana_fatata"}, {"patto"}
        p.statuses, p.pending_events = {"poison": 2}, [[7, "mendicante_ombra"]]
        back = run_save.decode(json.loads(json.dumps(run_save.encode(p))))
        self.assertIs(type(back), Player)
        self.assertEqual(vars(back).keys(), vars(p).keys())
        self.assertEqual((back.seen_events, back.run_flags, back.statuses, back.pending_events),
                         (p.seen_events, p.run_flags, p.statuses, p.pending_events))
        self.assertEqual([type(i) for i in back.inventory], [type(i) for i in p.inventory])
        self.assertEqual((back.weapon.name, back.weapon.atk, back.weapon.runes), (p.weapon.name, p.weapon.atk, p.weapon.runes))
        self.assertEqual((back.max_hp, back.get_total_atk(), back.get_total_def(), back.max_ether()),
                         (p.max_hp, p.get_total_atk(), p.get_total_def(), p.max_ether()))

    def test_the_save_version_follows_the_saved_objects(self):
        self.assertEqual(SCHEMA.get(run_save.SAVE_VERSION), schema_hash(),
                         "gli attributi degli oggetti salvati sono cambiati: alza run_save.SAVE_VERSION e aggiungi la nuova "
                         "impronta a SCHEMA, così un salvataggio vecchio viene rifiutato invece di caricarsi a metà")

    def test_tuples_sets_and_other_keys_keep_their_type(self):
        value = {"t": (1, (2, 3)), "s": {"a", "b"}, "k": {1: "uno", (2, 3): "due"}, "__x": 4}
        self.assertEqual(run_save.decode(json.loads(json.dumps(run_save.encode(value)))), value)

    def test_only_game_objects_are_rebuilt(self):
        for name in ("os.system", "subprocess.Popen", "entities.random", "builtins.object"):
            with self.subTest(name=name), self.assertRaises(run_save.SaveError):
                run_save.decode({"__object__": name, "state": {}})
        with self.assertRaises(TypeError):
            run_save.encode(object())


class FileTest(Sandbox):
    def run_state(self):
        with quiet(): p = Player("1", "base", [])
        return {"player": p, "floor": 4, "room_cooldowns": {}, "floor_state": None, "infinite_mode": False, "grade": 0,
                "daily": None, "active_pacts": []}

    def test_saving_restores_rules_cycle_and_random(self):
        modes.start_run(modes.ascension_rules(3)); set_cycle_seed(777); random.seed(5)
        run_save.save(self.run_state())
        rules, expected = dict(modes.RUN), [random.random() for _ in range(3)]
        modes.end_run(); set_cycle_seed(1); random.seed(99)
        run = run_save.load()
        self.assertEqual((dict(modes.RUN), CYCLE["seed"], [random.random() for _ in range(3)]), (rules, 777, expected))
        self.assertEqual(run["floor"], 4)

    def test_the_save_is_gone_once_loaded(self):
        run_save.save(self.run_state())
        self.assertEqual(run_save.peek(), {"role": GAME_DATA["classes"]["1"]["role"], "floor": 4})
        run_save.load()
        self.assertFalse(run_save.exists(), "non si ricarica per ritentare")
        with self.assertRaises(run_save.SaveError): run_save.load()

    def test_a_broken_or_old_save_is_refused_and_removed(self):
        for text in ("{ non è json", json.dumps({"version": run_save.SAVE_VERSION + 1, "run": {}}), json.dumps({"version": run_save.SAVE_VERSION})):
            with self.subTest(text=text[:20]):
                with open(run_save.SAVE_FILE, "w", encoding="utf-8") as f: f.write(text)
                with self.assertRaises(run_save.SaveError): run_save.load()
                self.assertFalse(run_save.exists())

    def test_resume_from_the_menu_reports_a_broken_save(self):
        with open(run_save.SAVE_FILE, "w", encoding="utf-8") as f: f.write("{ rotto")
        out = io.StringIO()
        with redirect_stdout(out), mock.patch("roguelike.wait_enter"), mock.patch("roguelike.clear_screen"), \
             mock.patch("roguelike.play_game") as play:
            roguelike.resume_game()
        play.assert_not_called()
        self.assertIn("Non si può riprendere", out.getvalue())

    def test_the_main_menu_offers_to_resume(self):
        menus = []
        def menu(options, prompt="", **kw):
            menus.append([bilanciamento.plain(o) for o in options]); return len(options) - 1  # Esci dal gioco
        for saved in (False, True):
            if saved: run_save.save(self.run_state())
            with quiet(), mock.patch("roguelike.interactive_menu", side_effect=menu), mock.patch("roguelike.clear_screen"), \
                 mock.patch("roguelike.delay_print"):
                roguelike.main()
        self.assertFalse(any("Riprendi" in o for o in menus[0]))
        self.assertEqual(menus[1][0], f"Riprendi la discesa ({GAME_DATA['classes']['1']['role']}, piano 4)")

    def test_a_new_descent_asks_before_losing_the_saved_one(self):
        run_save.save(self.run_state())
        with quiet(), mock.patch("roguelike.clear_screen"), mock.patch("roguelike.interactive_menu", return_value=1), \
             mock.patch("roguelike.play_game") as play:
            roguelike.new_game(infinite_mode=False)
        play.assert_not_called(); self.assertTrue(run_save.exists())
        with quiet(), mock.patch("roguelike.clear_screen"), mock.patch("roguelike.interactive_menu", return_value=0), \
             mock.patch("roguelike.play_game") as play:
            roguelike.new_game(infinite_mode=False)
        play.assert_called_once_with(infinite_mode=False); self.assertFalse(run_save.exists())


class ResumeTest(Sandbox):
    """La prova vera: il bot del simulatore gioca una discesa; alla n-esima scelta di una porta salva ed esce, il
    salvataggio passa dal disco, lo stato in memoria viene sporcato, e la discesa riprende. Deve finire uguale."""

    def play(self, cls, seed, save_at=None):
        real_menu, real_save, seen = bilanciamento.Bot.menu, roguelike._save_and_exit, {"maps": 0, "bot": None, "saved": 0}

        def menu(bot, options, prompt="", cancellable=False, initial=0):
            seen["bot"] = bot
            if "Scegli dove proseguire" in bilanciamento.plain(prompt):
                seen["maps"] += 1
                if seen["maps"] == save_at:
                    return [bilanciamento.plain(o) for o in options].index(roguelike.SAVE_AND_EXIT)
            return real_menu(bot, options, prompt, cancellable, initial)

        def save_and_exit(*args):
            real_save(*args)
            seen["saved"] += 1
            modes.end_run(); set_cycle_seed(0); random.random()  # dopo il salvataggio lo stato in memoria non conta più
            run = run_save.load()
            seen["bot"].player = run["player"]
            roguelike._descent(None, None, run["active_pacts"], run["infinite_mode"], run["grade"], run["daily"], run)

        with mock.patch.object(bilanciamento.Bot, "menu", menu), mock.patch("roguelike._save_and_exit", side_effect=save_and_exit):
            log = bilanciamento.play(cls, seed, bilanciamento.profile("completo"))
        hero = json.dumps(run_save.encode(seen["bot"].player), sort_keys=True)  # l'eroe a fine discesa, attributo per attributo
        return {**{k: log[k] for k in bilanciamento.GOLDEN_KEYS}, "hero": hero}, seen["saved"]

    def test_a_resumed_descent_ends_as_if_it_never_stopped(self):
        for cls, seed, save_at in (("1", 11, 1), ("3", 23, 5), ("5", 37, 12), ("9", 41, 20)):
            with self.subTest(cls=cls, save_at=save_at):
                straight, _ = self.play(cls, seed)
                resumed, saved = self.play(cls, seed, save_at)
                self.assertEqual(saved, 1 if straight["floor"] * 5 >= save_at else 0)
                self.assertEqual(resumed["hero"], straight["hero"])
                self.assertEqual(resumed, straight)
                self.assertFalse(run_save.exists(), "finita la discesa non resta nessun salvataggio")


if __name__ == "__main__":
    unittest.main()
