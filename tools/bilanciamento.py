"""Strumenti di bilanciamento: curve, banco degli oggetti e simulatore di run con il codice vero del gioco.

Uso, dalla radice del repository:
    python tools/bilanciamento.py curve               # difesa e attacco degli oggetti generabili contro i nemici, piano per piano
    python tools/bilanciamento.py oggetti             # ogni arma e armatura: colpi per abbattere un nemico, % del colpo assorbita
    python tools/bilanciamento.py run [N] [profilo]   # N run per classe (predefinito 50); profilo: nuovo (predefinito) o completo
    python tools/bilanciamento.py strategie [N] [profilo]  # le stesse run con diversi modi di scegliere le stanze
    python tools/bilanciamento.py ascensione [N] [gradi]   # profilo completo, N run per classe a ogni grado (es. 0,5,10,15,20)
    python tools/bilanciamento.py infinita [N]        # profilo completo, N run per classe in Modalità Infinita: fin dove arriva nel Ciclo
    python tools/bilanciamento.py attributi [N]       # profilo completo, N run per classe per ogni modo di spendere i punti abilità

Il profilo del giocatore non viene mai letto per le statistiche né salvato: ogni simulazione parte da un profilo
costruito in memoria ("nuovo": nulla di sbloccato; "completo": tutto sbloccato, potenziamenti e Maestrie al massimo).
Il giocatore automatico è ragionevole ma non ottimo: si difende dai colpi pesanti, si cura sotto il 35% degli HP,
riposa ai falò sotto il 70%, equipaggia l'arma e l'armatura con la statistica più alta e sceglie a caso negli eventi.
Sulla mappa sceglie la stanza in base agli HP (strategia "adattiva"); `strategie` lo confronta con chi segue sempre
lo stesso ordine di preferenza. Un buon bilanciamento non premia molto nessun ordine fisso rispetto agli altri.
I risultati vanno letti come confronto fra versioni del gioco, non come la difficoltà vissuta da una persona.
"""
import contextlib
import copy
import os
import random
import re
import statistics as st
import sys
from collections import Counter, defaultdict
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

# Il caricamento riscrive profile.json solo se va migrato da una versione precedente (come all'avvio del gioco);
# da qui in poi nessun salvataggio arriva al file
from data_manager import GAME_DATA, PROFILE_MANAGER, RAW_DATA, cycle_of, echo_name, get_biome, update_game_data
import runes
import data_manager
import magic


def rooms_module():
    import rooms
    return rooms

ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
FLOORS = (1, 5, 10, 15, 20, 25, 30)


def profile(kind: str) -> dict:
    import roguelike
    data = copy.deepcopy(PROFILE_MANAGER._data)
    data.update(essence=0, max_floor=0, won_normal=False, completed_feats=[], class_xp={},
                story={"flags": {}, "counters": {}, "seen_events": {}}, codex={"enemies": {}, "letters": [], "relics": [], "reactions": []})
    for k in ("starting_consumables", "starting_weapons", "starting_armors", "starting_accessories"): data[k] = []
    if kind == "completo":
        data["unlocked_ids"] = sorted({i["unlock_id"] for c in ("weapons", "armors", "accessories", "consumables", "relics")
                                       for i in RAW_DATA[c] if i.get("unlock_id")} | set(GAME_DATA["classes"]) | set(GAME_DATA["meta"]["traits"]))
        data["perks"] = {key: (True if boolean else top) for key, _, _, top, _, boolean in roguelike.PERK_DEFS}
        data["class_lvl"] = {c: max(map(int, GAME_DATA["meta"]["mastery_xp_requirements"])) for c in GAME_DATA["classes"]}
        data["won_normal"] = True
        data["ascension"] = {"best_win": GAME_DATA["modes"]["ascension"]["max"]}
    else:
        data["unlocked_ids"], data["class_lvl"] = [], {}
        data["perks"] = {k: (False if isinstance(v, bool) else 0) for k, v in data["perks"].items()}
    return data


def use_profile(data: dict):
    PROFILE_MANAGER._data.clear()
    PROFILE_MANAGER._data.update(copy.deepcopy(data))
    update_game_data()


# ------------------------------------------------------------------ curve e oggetti
def only(data_key, entry):
    import entities
    real = entities.random.choice
    return mock.patch("entities.random.choice", side_effect=lambda seq: entry if seq is GAME_DATA[data_key] else real(seq))


def cmd_curve():
    import entities
    use_profile(profile("completo"))
    random.seed(1)
    print(f"{'piano':>5} | {'nemico HP/ATK (tipico)':>22} | {'arma: colpi per nemico':>23} | {'armatura: % assorbita p50/p90':>30}")
    for f in FLOORS:
        hp, atk = entities.typical_enemy(f)
        w = st.median(entities.generate_weapon(f).atk for _ in range(1000))
        defs = sorted(entities.generate_armor(f).defense for _ in range(1000))
        print(f"{f:>5} | {hp:>10.0f} / {atk:<9.1f} | {hp / w:>23.1f} | {defs[500] / atk * 100:>14.0f}% / {defs[900] / atk * 100:.0f}%")


def cmd_oggetti():
    import entities
    use_profile(profile("completo"))
    random.seed(3)
    print("ARMI: colpi per abbattere il nemico tipico (mediana)")
    print(f"{'':30}" + "".join(f"{'p' + str(f):>8}" for f in FLOORS))
    for w in sorted(RAW_DATA["weapons"], key=lambda x: x["base_atk"]):
        with only("weapons", w):
            cells = [entities.typical_enemy(f)[0] / st.median(entities.generate_weapon(f).atk for _ in range(200)) for f in FLOORS]
        print(f"{w['name'][:29]:<30}" + "".join(f"{c:>8.1f}" for c in cells))
    print("\nARMATURE: % del colpo tipico assorbita (mediana)")
    print(f"{'':30}" + "".join(f"{'p' + str(f):>8}" for f in FLOORS))
    for a in sorted(RAW_DATA["armors"], key=lambda x: x["base_def"]):
        with only("armors", a):
            cells = [st.median(entities.generate_armor(f).defense for _ in range(200)) / entities.typical_enemy(f)[1] * 100 for f in FLOORS]
        print(f"{a['name'][:29]:<30}" + "".join(f"{c:>7.0f}%" for c in cells))


# ------------------------------------------------------------------ simulatore di run
class Stuck(Exception):
    pass


def plain(text):
    return ANSI.sub("", text or "")


# Ordini di preferenza fissi delle stanze (falò e mercante restano scelte di necessità); None: sceglie in base agli HP
STRATEGIES = {
    "adattiva": None,
    "prudente": ["Forziere", "Evento", "Mistero", "Scontro", "Élite", "Trappola"],
    "aggressiva": ["Élite", "Scontro", "Mistero", "Trappola", "Forziere", "Evento"],
    "trappole": ["Trappola", "Mistero", "Forziere", "Evento", "Scontro", "Élite"],
}


# Come il giocatore automatico spende i punti abilità. "classe": a turno gli attributi con cui parte la classe,
# dal più alto, e la Vitalità; "equilibrata": a turno Vitalità, Forza, Destrezza e Agilità; un nome: tutto lì
# (finché si può, poi Vitalità).
POINT_PLANS = ("classe", "equilibrata", "vitalita", "forza", "destrezza", "agilita", "arcano", "fortuna")


def point_order(cls, plan):
    if plan == "classe":
        start = RAW_DATA["classes"][cls].get("attributes", {})
        return sorted(start, key=lambda a: -start[a]) + ([] if "vitalita" in start else ["vitalita"])
    if plan == "equilibrata": return ["vitalita", "forza", "destrezza", "agilita"]
    return [plan]


class Bot:
    def __init__(self, cls, strategy="adattiva", grade=0, points="classe"):
        self.cls, self.player, self.calls, self.state, self.order, self.grade = cls, None, 0, {}, STRATEGIES[strategy], grade
        self.points = point_order(cls, points)

    def pick_spell(self):
        """L'incantesimo che conviene lanciare adesso (indice in player.spells), o None.

        Cura sotto il 40% degli HP; altrimenti un incantesimo che completa una reazione con il marchio del nemico,
        che lo colpisce Super Efficace, che fa esplodere un marchio o che infrange scudo e Scaglie."""
        p, s = self.player, self.state.get("session")
        if not s or not p.spells or s.spells_muted(): return None
        for i, sid in enumerate(p.spells):
            if p.ether < magic.cost(p, sid): continue
            fx, el = magic.spell(sid)["effects"], magic.spell(sid)["element"]
            if fx.get("heal_pct") and p.hp < p.max_hp * 0.4: return i
            if "damage_pct" not in fx: continue
            mark = s.enemy.mark[0] if s.enemy.mark else None
            if mark and el != "Normale" and mark != el and rooms_module().reaction_key(mark, el): return i
            if el != "Normale" and data_manager.MULTIPLIERS.get(el, {}).get(s.enemy.element, 1.0) > 1.0: return i
            if fx.get("detonate_pct") and mark: return i
            if fx.get("dispel") and (s.enemy.shield or s.enemy.ward is not None): return i
        return None

    def spend_point(self, opts):
        """Il prossimo attributo del piano che può ancora salire (altrimenti la Vitalità, poi qualunque)."""
        p, names = self.player, list(GAME_DATA["attributes"]["attributes"])
        k = self.state.get("point", 0)
        self.state["point"] = k + 1
        wanted = [self.points[(k + i) % len(self.points)] for i in range(len(self.points))] + ["vitalita"] + names
        cap = GAME_DATA["attributes"]["rules"]["max_points"]
        return names.index(next(a for a in wanted if p.attributes[a] < cap))

    def equip(self):
        p = self.player
        # Le armi valgono il loro ATK più il bonus dell'attributo con cui scalano
        scaled = lambda w: w.atk * (100 + p.attributes.get(w.scaling, 0) * GAME_DATA["attributes"]["attributes"][w.scaling]["per_point"].get("scaled_dmg_pct", 0))
        for kind, value, slot in (("weapon", scaled, "weapon"), ("armor", lambda a: a.defense, "armor")):
            best = max((i for i in p.inventory if i.type == kind), key=value, default=None)
            if best and value(best) > value(getattr(p, slot)):
                p.inventory.remove(best); p.inventory.append(getattr(p, slot)); setattr(p, slot, best)
        if p.accessory is None:
            acc = next((i for i in p.inventory if i.type == "accessory"), None)
            if acc: p.inventory.remove(acc); p.accessory = acc
        # Rune: le incastona dove c'è posto (come al Falò, ma senza passare dal menu)
        for r in [i for i in p.inventory if i.type == "rune"]:
            target = next((it for it in (p.weapon, p.armor) if runes.free_sockets(it) > 0 and runes.fits(r.rune_id, it.type)), None)
            if target:
                p.inventory.remove(r); target.runes.append(r.rune_id); target.refresh_display_name()
        # Pergamene: impara l'incantesimo se c'è posto, altrimenti sostituisce il primo d'attacco più debole
        for sc in [i for i in p.inventory if i.type == "scroll"]:
            p.inventory.remove(sc)
            if sc.spell_id in p.spells: continue
            if len(p.spells) < magic.rules()["slots"]: p.spells.append(sc.spell_id); continue
            power = lambda sid: magic.spell(sid)["effects"].get("damage_pct", 0)
            weakest = min(range(len(p.spells)), key=lambda k: (bool(magic.spell(p.spells[k]).get("outside")), power(p.spells[k])))
            if power(sc.spell_id) > power(p.spells[weakest]): p.spells[weakest] = sc.spell_id
        gear = [i for i in p.inventory if i.type in ("weapon", "armor", "accessory")]
        p.inventory = [i for i in p.inventory if i.type in ("consumable", "rune")] + gear[:4]

    def menu(self, options, prompt="", cancellable=False, initial=0):
        self.calls += 1
        opts, pr, p = [plain(o) for o in options], plain(prompt), self.player
        if self.calls > 20000: raise Stuck(pr[-200:] + " || " + " | ".join(opts))
        find = lambda *ws: next((i for i, o in enumerate(opts) if any(w in o for w in ws)), None)
        if "Scegli il tuo Eroe" in pr: return find(GAME_DATA["classes"][self.cls]["role"].upper())
        if "Scegli un Tratto" in pr: return find("Nessun Tratto") or 0
        if "ASCENSIONE" in pr: return self.grade
        if "Scrittoio di Silas" in pr or "Quale reliquia vuoi scartare" in pr: return len(opts) - 1
        if "Il Dio Antico è caduto" in pr: return 0
        if "Scegli dove proseguire" in pr:
            self.equip()
            low, high = p.hp < p.max_hp * 0.5, p.hp > p.max_hp * 0.75
            def score(i):
                o = opts[i]
                if "Falò" in o: return 10 if low else 3
                if "Mercante" in o: return 6 if p.gold > 120 else 1
                if self.order:
                    return next((len(self.order) - k for k, w in enumerate(self.order) if w in o), 0)
                if "Élite" in o: return 7 if high else 0
                if "Forziere" in o: return 5
                if "Evento" in o: return 4
                if "Trappola" in o: return 0 if low else 6 if high else 3
                if "Mistero" in o: return 1 if low else 6
                return 2 if low else 5
            return max((i for i, o in enumerate(opts) if o.startswith("Entra:")), key=lambda i: (score(i), random.random()))
        if "Come affronti la trappola" in pr:
            if p.hp < p.max_hp * 0.35: return 2
            chances = [int(re.search(r"(\d+)%", o).group(1)) for o in opts[:2]]
            return chances.index(max(chances))
        if find("Forza la serratura") is not None: return 0 if p.hp > p.max_hp * 0.4 else 1
        if find("Aprilo comunque") is not None: return 0 if p.hp > p.max_hp * 0.6 else 1
        if "PUNTI ABILITÀ" in pr: return self.spend_point(opts)
        if "TALENTO" in pr: return 0  # i talenti sono proposti a caso: il primo è una scelta qualunque
        if "INCANTESIMI" in pr: return self.state.pop("spell", len(opts) - 1)
        if "Intento del nemico" in pr:
            potion = any(i.type == "consumable" and i.category == "heal" for i in p.inventory)
            spell = self.pick_spell()
            if spell is not None and magic.spell(p.spells[spell])["effects"].get("heal_pct"):
                self.state["spell"] = spell; return find("Lancia un incantesimo")
            if p.hp < p.max_hp * 0.35 and potion: self.state["potion"] = True; return find("Apri Inventario")
            if "sigillata" in opts[1]: return 0
            if "Colpo pesante" in pr or "Colpo caricato" in pr or "Incantesimo (≈" in pr: return 1
            if spell is not None: self.state["spell"] = spell; return find("Lancia un incantesimo")
            return 0
        if "ZAINO E INVENTARIO" in pr:
            if self.state.pop("potion", False):
                i = next((i for i, o in enumerate(opts) if "(Cura" in o and "Antidoto" not in o), None)
                if i is not None: return i
            return len(opts) - 1
        if "FALÒ" in pr:
            if p.hp < p.max_hp * 0.7 and find("Riposa") is not None: return find("Riposa")
            if p.spells and p.ether < p.max_ether() // 2 and find("Medita") is not None: return find("Medita")
            if p.gold >= 50 and find("Affila") is not None: return find("Affila")
            return find("Prosegui")
        if find("Guarda Merce") is not None:
            self.state["shop"] = not self.state.get("shop")
            return find("Guarda Merce") if self.state["shop"] else find("Saluta ed esci")
        if any("Prezzo" in o for o in opts):
            cheap = [i for i, o in enumerate(opts) if "(Cura" in o and int(re.search(r"Prezzo: (\d+)", o).group(1)) <= p.gold]
            return cheap[0] if cheap else -1
        if "Scegli:" in pr: return random.randrange(len(opts))
        return -1 if cancellable else 0


def play(cls, seed, base, strategy="adattiva", grade=0, infinite=False, points="classe"):
    import attributes, camp, endings, entities, events, inventory_menu, roguelike, rooms
    random.seed(seed)
    use_profile(base)
    bot, log = Bot(cls, strategy, grade, points), {"cls": cls, "hits": 0, "zero": 0, "bosses": [], "killer": None}
    real_player, real_damage, real_start, real_evaluate = entities.Player, rooms.CombatSession._calc_enemy_damage, rooms.CombatSession.start, roguelike.evaluate_run

    def make_player(*a):
        bot.player = real_player(*a)
        return bot.player

    def damage(self, *a, **k):
        d = real_damage(self, *a, **k)
        log["hits"] += 1; log["zero"] += d == 0
        return d

    def start(self):
        bot.state["session"] = self
        if self.enemy.is_boss: log["bosses"].append(self.enemy.base_name)
        log["killer"] = self.enemy.base_name
        return real_start(self)

    def evaluate(p, floor, infinite):
        before = PROFILE_MANAGER.essence
        real_evaluate(p, floor, infinite)
        log.update(floor=floor, won=p.won, essence=PROFILE_MANAGER.essence - before)

    modules = ("roguelike", "rooms", "events", "entities", "inventory_menu", "camp", "endings", "attributes", "talents")
    patches = [mock.patch(f"{m}.interactive_menu", side_effect=bot.menu) for m in modules]
    patches += [mock.patch(f"{m}.{f}") for m in modules for f in ("wait_enter", "clear_screen", "delay_print") if hasattr(sys.modules[m], f)]
    patches += [mock.patch("roguelike.Player", side_effect=make_player), mock.patch("roguelike.evaluate_run", side_effect=evaluate),
                mock.patch("roguelike.time.sleep"), mock.patch("rooms.time.sleep"), mock.patch.object(PROFILE_MANAGER, "save"),
                mock.patch("builtins.input", return_value=""), mock.patch.object(rooms.CombatSession, "_calc_enemy_damage", damage),
                mock.patch.object(rooms.CombatSession, "start", start)]
    with contextlib.ExitStack() as stack, contextlib.redirect_stdout(open(os.devnull, "w")):
        for pt in patches: stack.enter_context(pt)
        try:
            roguelike.play_game(infinite_mode=infinite)
        except Stuck as e:
            log.update(stuck=str(e), floor=0, won=False, essence=0)
    log["level"] = bot.player.level if bot.player else 1
    if not log["won"]:
        b = get_biome(log["floor"])
        log["biome"] = b["id"] if b else "oltre"
        log["echo"] = cycle_of(log["floor"])
    return log


def cmd_run(n, kind):
    base = profile(kind)
    use_profile(base)
    classes = list(GAME_DATA["classes"]) if kind == "completo" else [c for c, d in RAW_DATA["classes"].items() if d.get("unlocked_by_default", True)]
    logs = [play(c, int(c) * 100003 + i * 7919, base) for c in classes for i in range(n)]
    print(f"profilo {kind}: {len(logs)} run")
    print(f"{'classe':<11} {'vittorie':>8} {'piano mediano':>13} {'Essenza mediana':>15}")
    for c in classes:
        ls = [l for l in logs if l["cls"] == c]
        print(f"{GAME_DATA['classes'][c]['role']:<11} {sum(l['won'] for l in ls) / len(ls) * 100:>7.0f}% "
              f"{st.median(l['floor'] for l in ls):>13} {st.median(l['essence'] for l in ls):>15}")
    print("colpi nemici annullati del tutto:", f"{sum(l['zero'] for l in logs) / max(1, sum(l['hits'] for l in logs)) * 100:.0f}%")
    print("morti per bioma:", dict(Counter(l["biome"] for l in logs if not l["won"]).most_common()))
    killers, met = Counter(l["killer"] for l in logs if not l["won"]), Counter(b for l in logs for b in l["bosses"])
    rates = sorted(((killers[b] / k * 100, b) for b, k in met.items() if k >= 20), reverse=True)
    print("boss più letali (morti/incontri):", ", ".join(f"{b} {r:.0f}%" for r, b in rates[:5]))
    stuck = [l for l in logs if l.get("stuck")]
    if stuck: print(f"ATTENZIONE: {len(stuck)} run bloccate, es.: {stuck[0]['stuck'][:300]}")


def cmd_strategie(n, kind):
    base = profile(kind)
    use_profile(base)
    classes = list(GAME_DATA["classes"]) if kind == "completo" else [c for c, d in RAW_DATA["classes"].items() if d.get("unlocked_by_default", True)]
    print(f"profilo {kind}: {n} run per classe e per strategia")
    print(f"{'strategia':<11} {'vittorie':>8} {'piano mediano':>13} {'livello mediano':>15}")
    for strategy in STRATEGIES:
        logs = [play(c, int(c) * 100003 + i * 7919, base, strategy) for c in classes for i in range(n)]
        print(f"{strategy:<11} {sum(l['won'] for l in logs) / len(logs) * 100:>7.0f}% {st.median(l['floor'] for l in logs):>13} "
              f"{st.median(l['level'] for l in logs):>15}")


def cmd_ascensione(n, grades):
    base = profile("completo")
    use_profile(base)
    print(f"profilo completo: {n} run per classe e per grado")
    print(f"{'grado':>5} {'vittorie':>8} {'piano mediano':>13}")
    for g in grades:
        logs = [play(c, int(c) * 100003 + i * 7919, base, grade=g) for c in GAME_DATA["classes"] for i in range(n)]
        print(f"{g:>5} {sum(l['won'] for l in logs) / len(logs) * 100:>7.0f}% {st.median(l['floor'] for l in logs):>13}")


def cmd_attributi(n):
    base = profile("completo")
    use_profile(base)
    print(f"profilo completo: {n} run per classe per ogni modo di spendere i punti")
    print(f"{'punti':<12} {'vittorie':>8} {'piano mediano':>13} {'livello mediano':>15}")
    for plan in POINT_PLANS:
        logs = [play(c, int(c) * 100003 + i * 7919, base, points=plan) for c in GAME_DATA["classes"] for i in range(n)]
        print(f"{plan:<12} {sum(l['won'] for l in logs) / len(logs) * 100:>7.0f}% {st.median(l['floor'] for l in logs):>13} {st.median(l['level'] for l in logs):>15}")


def cmd_infinita(n):
    base = profile("completo")
    use_profile(base)
    logs = [play(c, int(c) * 100003 + i * 7919, base, infinite=True) for c in GAME_DATA["classes"] for i in range(n)]
    print(f"profilo completo, Modalità Infinita: {len(logs)} run")
    print(f"{'classe':<11} {'piano mediano':>13} {'oltre il 30':>11} {'oltre il 60':>11} {'piano max':>9} {'Essenza mediana':>15}")
    for c in GAME_DATA["classes"]:
        ls = [l for l in logs if l["cls"] == c]
        print(f"{GAME_DATA['classes'][c]['role']:<11} {st.median(l['floor'] for l in ls):>13} {sum(l['floor'] > 30 for l in ls) / len(ls) * 100:>10.0f}% "
              f"{sum(l['floor'] > 60 for l in ls) / len(ls) * 100:>10.0f}% {max(l['floor'] for l in ls):>9} {st.median(l['essence'] for l in ls):>15}")
    deep = [l for l in logs if l["floor"] > 30]
    print("morti oltre il 30 per Eco e bioma:", dict(Counter(f"{echo_name(l['echo'])} {l['biome']}" for l in deep).most_common(8)))
    print("chi uccide oltre il 30:", dict(Counter(l["killer"] for l in deep).most_common(6)))
    stuck = [l for l in logs if l.get("stuck")]
    if stuck: print(f"ATTENZIONE: {len(stuck)} run bloccate, es.: {stuck[0]['stuck'][:300]}")


if __name__ == "__main__":
    args = sys.argv[1:] or ["curve"]
    if args[0] == "curve": cmd_curve()
    elif args[0] == "oggetti": cmd_oggetti()
    elif args[0] == "run": cmd_run(int(args[1]) if len(args) > 1 else 50, args[2] if len(args) > 2 else "nuovo")
    elif args[0] == "ascensione": cmd_ascensione(int(args[1]) if len(args) > 1 else 20, [int(g) for g in (args[2] if len(args) > 2 else "0,5,10,15,20").split(",")])
    elif args[0] == "attributi": cmd_attributi(int(args[1]) if len(args) > 1 else 20)
    elif args[0] == "infinita": cmd_infinita(int(args[1]) if len(args) > 1 else 20)
    elif args[0] == "strategie": cmd_strategie(int(args[1]) if len(args) > 1 else 30, args[2] if len(args) > 2 else "nuovo")
    else: print(__doc__)
