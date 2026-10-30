"""Motore degli eventi narrativi.

Un evento è una piccola storia a scene (`data/events.json`). Ogni scena ha un testo e delle scelte; ogni scelta
dichiara nei dati le condizioni per comparire (`requires`), gli effetti (`effects`), un'eventuale probabilità
(`chance`, con `fail_effects`) e la scena successiva (`next`). Il riepilogo fra parentesi accanto a una scelta
è generato dagli effetti stessi, quindi il testo mostrato al giocatore non può promettere qualcosa che non accade.

Il Labirinto ricorda: `flag` e `counter` vivono nel profilo e restano fra una run e l'altra, `run_flag` vale
per la sola discesa in corso, `later` fa riaffiorare un evento qualche piano più in basso.
"""
import random
from typing import Callable, Dict, List, Optional

from data_manager import GAME_DATA, PROFILE_MANAGER, RAW_DATA, get_biome
from entities import Enemy, Player, generate_accessory, generate_armor, generate_potion, generate_weapon, get_random_relic
from rooms import combat_room
from ui import Colors, clear_screen, delay_print, display_msg, interactive_menu, wait_enter

# Oro concesso al posto di una reliquia quando il giocatore le possiede già tutte
RELIC_FALLBACK_GOLD = 50
# tipo di scontro -> (riepilogo, nemico)
FIGHTS = {
    "normal": ("Combatti", lambda floor, pacts: Enemy(floor, False, pacts)),
    "hard": ("Combatti un nemico feroce", lambda floor, pacts: Enemy(floor, False, pacts, modifier="hard")),
    "elite": ("Combatti un Elite", lambda floor, pacts: Enemy(floor + 5, True, pacts)),
}


# ------------------------------------------------------------------ memoria (profilo e run)
def _story() -> dict:
    return PROFILE_MANAGER.story


get_flag, set_flag = PROFILE_MANAGER.get_flag, PROFILE_MANAGER.set_flag
get_counter, add_counter = PROFILE_MANAGER.get_counter, PROFILE_MANAGER.add_counter


def letters_complete() -> bool:
    """Tutte le lettere insanguinate sono nel Codice."""
    return set(range(len(GAME_DATA["lore"]["letters"]))) <= set(PROFILE_MANAGER.codex["letters"])


def times_seen(event_id: str) -> int:
    return int(_story()["seen_events"].get(event_id, 0))


def _run_flags(player: Player) -> set:
    if not hasattr(player, "run_flags"): player.run_flags = set()
    return player.run_flags


def item_name(item_id: str) -> str:
    return GAME_DATA["story"]["quest_items"].get(item_id, {}).get("name", item_id)


def npc_name(npc_id: str) -> str:
    return GAME_DATA["story"]["npcs"].get(npc_id, npc_id)


def _relic_name(relic_id: str) -> str:
    return next((r["name"] for r in RAW_DATA["relics"] if r["id"] == relic_id), relic_id)


def _role(class_id: str) -> str:
    return GAME_DATA["classes"][class_id]["role"]


def _attribute_tag(attr: str, points: int) -> str:
    d = GAME_DATA["attributes"]["attributes"][attr]
    return f"{d['icon']} {d['name']} {points}+"


def _as_list(value) -> list:
    return value if isinstance(value, list) else [value]


# ------------------------------------------------------------------ condizioni
# nome -> (verifica(player, valore, piano), etichetta mostrata accanto alla scelta o None)
# Le etichette sono il segnale "alla Disco Elysium": questa opzione esiste perché sei tu.
CONDITIONS: Dict[str, tuple] = {
    "class": (lambda p, v, f: p.class_id in _as_list(v), lambda v: "/".join(_role(c) for c in _as_list(v))),
    "not_class": (lambda p, v, f: p.class_id not in _as_list(v), None),
    "trait": (lambda p, v, f: p.trait_id in _as_list(v), lambda v: "/".join(GAME_DATA["meta"]["traits"][t]["name"] for t in _as_list(v))),
    "relic": (lambda p, v, f: v in p.relic_ids, lambda v: _relic_name(v)),
    "quest_item": (lambda p, v, f: v in p.quest_items, lambda v: item_name(v)),
    "pact": (lambda p, v, f: v in p.active_pacts, lambda v: GAME_DATA["meta"]["pacts"][v]["name"]),
    "gold": (lambda p, v, f: p.gold >= v, lambda v: f"Oro {v}+"),
    "level": (lambda p, v, f: p.level >= v, lambda v: f"Livello {v}+"),
    "atk": (lambda p, v, f: p.get_total_atk() >= v, lambda v: f"ATK {v}+"),
    "dodge": (lambda p, v, f: p.get_dodge() >= v, lambda v: f"Schivata {v}%+"),
    "hp_pct_below": (lambda p, v, f: p.hp * 100 < p.max_hp * v, lambda v: f"HP sotto il {v}%"),
    "min_floor": (lambda p, v, f: f >= v, None),
    "biome": (lambda p, v, f: (get_biome(f) or {}).get("id") == v, None),
    "max_floor": (lambda p, v, f: f <= v, None),
    "flag": (lambda p, v, f: get_flag(v), None),
    "not_flag": (lambda p, v, f: not get_flag(v), None),
    "run_flag": (lambda p, v, f: v in _run_flags(p), None),
    "not_run_flag": (lambda p, v, f: v not in _run_flags(p), None),
    "counter": (lambda p, v, f: all(get_counter(k) >= n for k, n in v.items()), None),
    "counter_below": (lambda p, v, f: all(get_counter(k) < n for k, n in v.items()), None),
    "npc": (lambda p, v, f: PROFILE_MANAGER.get_npc_unlocked(v), None),
    "flags": (lambda p, v, f: all(get_flag(x) for x in v), None),
    "any_flags": (lambda p, v, f: any(get_flag(x) for x in v), None),
    "letters_complete": (lambda p, v, f: letters_complete() == v, None),
    "corruption": (lambda p, v, f: p.corruption >= v, lambda v: f"Corruzione {v}+"),
    "corruption_below": (lambda p, v, f: p.corruption < v, None),
    "not_npc": (lambda p, v, f: not PROFILE_MANAGER.get_npc_unlocked(v), None),
    "attribute": (lambda p, v, f: all(p.attributes.get(a, 0) >= n for a, n in v.items()), lambda v: ", ".join(_attribute_tag(a, n) for a, n in v.items())),
    "spells": (lambda p, v, f: bool(p.spells) == v, lambda v: "Incantesimi"),
}
# Condizioni che dipendono solo da piano e profilo: valutabili anche senza un eroe (es. nella scelta delle porte)
PROFILE_CONDITIONS = {"flags", "any_flags", "letters_complete", "biome", "min_floor", "max_floor", "flag", "not_flag", "counter", "counter_below", "npc", "not_npc"}


def check(player: Optional[Player], requires: dict, floor: int) -> bool:
    for key, value in (requires or {}).items():
        if player is None and key not in PROFILE_CONDITIONS: continue
        if not CONDITIONS[key][0](player, value, floor): return False
    return True


def tags(requires: dict) -> List[str]:
    return [label(v) for k, v in (requires or {}).items() if (label := CONDITIONS[k][1])]


# ------------------------------------------------------------------ effetti
class _Stop(Exception):
    """Interrompe la catena di effetti: `alive` dice se l'eroe è sopravvissuto."""
    def __init__(self, alive: bool): self.alive = alive


def _gold(p, v, eff, floor):
    if v >= 0:
        g = v * 3 if p.midas else v
        p.gold += g
        display_msg(f"{Colors.YELLOW}+{g} Oro.{Colors.RESET}")
    else:
        p.gold = max(0, p.gold + v)


def _damage(p, v, eff, floor):
    if not p.take_damage(v):
        display_msg(f"\n{Colors.RED}{Colors.BOLD}{eff.get('death_msg', 'Le ferite ti sono fatali...')}{Colors.RESET}")
        raise _Stop(False)
    display_msg(f"{Colors.RED}-{v} HP. ({p.hp}/{p.max_hp}){Colors.RESET}")


def _heal(p, amount):
    if p.cursed:
        display_msg(f"{Colors.RED}La maledizione blocca la cura.{Colors.RESET}"); return
    healed = p.heal(amount)
    if healed: display_msg(f"{Colors.GREEN}Recuperi {healed} HP. ({p.hp}/{p.max_hp}){Colors.RESET}")
    else: display_msg(f"{Colors.GREEN}Sei già in piena forma. ({p.hp}/{p.max_hp}){Colors.RESET}")


def _max_hp(p, v, eff, floor):
    p.max_hp = max(1, p.max_hp + v)
    p.hp = min(p.hp, p.max_hp)
    display_msg(f"{Colors.GREEN if v > 0 else Colors.RED}{v:+d} HP Max. ({p.hp}/{p.max_hp}){Colors.RESET}")


def _relic(p, v, eff, floor):
    relic = get_random_relic(p) if v == "random" else next((r for r in GAME_DATA["relics"] if r["id"] == v and r["id"] not in p.relic_ids), None)
    if relic: p.add_relic(relic)
    else:
        p.gold += RELIC_FALLBACK_GOLD
        display_msg(f"{Colors.YELLOW}Non c'è nulla che tu non possieda già: trovi {RELIC_FALLBACK_GOLD} Oro.{Colors.RESET}")


def _equipment(generator, epic_arg=True):
    def apply(p, v, eff, floor):
        level = floor + eff.get("level", 0)
        item = generator(level, v == "epic") if epic_arg else generator(level)
        p.inventory.append(item)
        display_msg(f"{Colors.MAGENTA}Ottieni: {item.display_name}!{Colors.RESET}")
    return apply


def _rune(p, v, eff, floor):
    from entities import generate_rune
    from codex import record_rune
    item = generate_rune(floor, "" if v == "random" else v)
    record_rune(item.rune_id)
    p.inventory.append(item)
    display_msg(f"{Colors.MAGENTA}Ottieni: {item.display_name}! (Si incastona al Falò){Colors.RESET}")


def _scroll(p, v, eff, floor):
    from entities import generate_scroll
    item = generate_scroll(floor)
    p.inventory.append(item)
    display_msg(f"{Colors.MAGENTA}Ottieni: {item.display_name}! (La leggi dallo zaino){Colors.RESET}")


def _ether(p, v, eff, floor):
    gained = p.gain_ether(p.max_ether() if v == "full" else v)
    display_msg(f"{Colors.CYAN}+{gained} Etere. ({p.ether}/{p.max_ether()}){Colors.RESET}")


def _potion(p, v, eff, floor):
    for _ in range(v):
        item = generate_potion(floor)
        p.inventory.append(item)
        display_msg(f"{Colors.MAGENTA}Ottieni: {item.display_name}!{Colors.RESET}")


def _fight(p, v, eff, floor):
    enemy = FIGHTS[v][1](floor + eff.get("level", 0), p.active_pacts)
    wait_enter("Premi INVIO per combattere...")
    combat_room(p, floor, enemy)
    if p.hp <= 0: raise _Stop(False)
    if enemy.hp > 0: raise _Stop(True)  # fuggito: le ricompense legate alla vittoria non arrivano


def _quest_item(p, v, eff, floor):
    if v not in p.quest_items: p.quest_items.append(v)
    display_msg(f"{Colors.YELLOW}Ottieni l'oggetto chiave: {item_name(v)}.{Colors.RESET}")


def _take_quest_item(p, v, eff, floor):
    if v in p.quest_items: p.quest_items.remove(v)


def _unlock_npc(p, v, eff, floor):
    PROFILE_MANAGER.unlock_npc(v)
    display_msg(f"{Colors.GREEN}Hai liberato {npc_name(v)}: ti aspetta al Campo Base.{Colors.RESET}")


def _atk(p, v, eff, floor):
    p.bonus_atk_relic += v
    display_msg(f"{Colors.RED}{v:+d} ATK per il resto della discesa.{Colors.RESET}")


def _def(p, v, eff, floor):
    p.bonus_def += v
    display_msg(f"{Colors.CYAN}{v:+d} DIF per il resto della discesa.{Colors.RESET}")


def _essence(p, v, eff, floor):
    p.essence_gathered += v
    display_msg(f"{Colors.MAGENTA}+{v} Essenza a fine run.{Colors.RESET}")


def _fall(p, v, eff, floor):
    """Caduta Astrale: si precipita al piano successivo, perdendo parte dell'Oro. Chiude l'evento."""
    lost = p.gold * eff.get("gold_pct", 0) // 100
    p.gold -= lost
    p.fallen = True
    display_msg(f"{Colors.RED}Precipiti nelle nubi... perdi {lost} Oro nella caduta.{Colors.RESET}")
    raise _Stop(True)


def _corruption(p, v, eff, floor):
    delta = p.add_corruption(v)
    if delta: display_msg(f"{Colors.MAGENTA if delta > 0 else Colors.CYAN}🩸 Corruzione {delta:+d} ({p.corruption}).{Colors.RESET}")


def _later(p, v, eff, floor):
    p.pending_events.append([floor + eff.get("floors", 1), v])


def _plural(n: int, one: str, many: str) -> str:
    return one if n == 1 else f"{n} {many}"


# nome -> (applica(player, valore, effetto, piano), riepilogo(valore, effetto) o None se l'effetto è nascosto)
EFFECTS: Dict[str, tuple] = {
    "gold": (_gold, lambda v, e: f"{v:+d} Oro"),
    "damage": (_damage, lambda v, e: f"-{v} HP"),
    "heal_pct": (lambda p, v, e, f: _heal(p, p.max_hp * v // 100), lambda v, e: f"Cura {v}% HP"),
    "heal": (lambda p, v, e, f: _heal(p, v), lambda v, e: f"Cura {v} HP"),
    "max_hp": (_max_hp, lambda v, e: f"{v:+d} HP Max"),
    "relic": (_relic, lambda v, e: "Reliquia" if v == "random" else f"Reliquia: {_relic_name(v)}"),
    "weapon": (_equipment(generate_weapon), lambda v, e: "Arma Epica" if v == "epic" else "Arma"),
    "armor": (_equipment(generate_armor), lambda v, e: "Armatura Epica" if v == "epic" else "Armatura"),
    "accessory": (_equipment(generate_accessory, epic_arg=False), lambda v, e: "Monile"),
    "potion": (_potion, lambda v, e: _plural(v, "Pozione", "Pozioni")),
    "rune": (_rune, lambda v, e: "Runa" if v == "random" else f"Runa: {GAME_DATA['runes']['runes'][v]['name']}"),
    "scroll": (_scroll, lambda v, e: "Pergamena"),
    "ether": (_ether, lambda v, e: "Tutto l'Etere" if v == "full" else f"+{v} Etere"),
    "fight": (_fight, lambda v, e: FIGHTS[v][0]),
    "quest_item": (_quest_item, lambda v, e: f"Oggetto chiave: {item_name(v)}"),
    "take_quest_item": (_take_quest_item, lambda v, e: f"Consuma: {item_name(v)}"),
    "unlock_npc": (_unlock_npc, lambda v, e: f"Libera {npc_name(v)}"),
    "atk": (_atk, lambda v, e: f"{v:+d} ATK"),
    "def": (_def, lambda v, e: f"{v:+d} DIF"),
    "exp": (lambda p, v, e, f: p.gain_exp(v), lambda v, e: f"+{v} EXP"),
    "essence": (_essence, lambda v, e: f"+{v} Essenza"),
    "flag": (lambda p, v, e, f: set_flag(v, e.get("value", True)), None),
    "run_flag": (lambda p, v, e, f: _run_flags(p).add(v), None),
    "counter": (lambda p, v, e, f: add_counter(v, e.get("add", 1)), None),
    "later": (_later, None),
    "corruption": (_corruption, lambda v, e: f"{v:+d} Corruzione"),
    "fall": (_fall, lambda v, e: f"Precipiti al piano successivo, -{e.get('gold_pct', 0)}% Oro"),
}
# Parametri accessori ammessi accanto alla chiave principale di un effetto
EFFECT_PARAMS = {"level", "floors", "value", "add", "death_msg", "gold_pct"}


def effect_key(effect: dict) -> str:
    return next(k for k in effect if k not in EFFECT_PARAMS)


def summarize(effects: List[dict]) -> List[str]:
    parts = []
    for eff in effects or []:
        key = effect_key(eff)
        text = EFFECTS[key][1]
        if text: parts.append(text(eff[key], eff))
    return parts


def gold_cost(choice: dict) -> int:
    return -sum(e["gold"] for e in choice.get("effects", []) if "gold" in e and e["gold"] < 0)


def choice_summary(choice: dict) -> str:
    if choice.get("hidden"): return ""
    parts = summarize(choice.get("effects"))
    if "chance" in choice:
        win, fail = ", ".join(summarize(choice.get("success"))), ", ".join(summarize(choice.get("fail_effects")))
        if win: parts.append(f"{choice['chance']}%: {win}" + (f", altrimenti {fail}" if fail else ""))
        elif fail: parts.append(f"{100 - choice['chance']}%: {fail}")
    return f" ({'; '.join(parts)})" if parts else ""


def apply_effects(player: Player, effects: List[dict], floor: int) -> bool:
    """Applica gli effetti in ordine. False se l'eroe muore; una fuga da uno scontro interrompe la catena."""
    try:
        for eff in effects or []:
            key = effect_key(eff)
            EFFECTS[key][0](player, eff[key], eff, floor)
    except _Stop as stop:
        if not stop.alive: return False
        raise
    return True


# ------------------------------------------------------------------ scelta degli eventi
def is_available(event_id: str, floor: int, player: Optional[Player] = None) -> bool:
    ev = GAME_DATA["events"][event_id]
    if ev.get("scripted"): return False  # compare solo quando lo richiama una scelta (`later`) o un bioma
    return check(player, ev.get("requires"), floor)


def pick_event(floor: int, player: Optional[Player] = None) -> str:
    ids = [k for k in GAME_DATA["events"] if is_available(k, floor, player)]
    fresh = [k for k in ids if player is None or k not in getattr(player, "seen_events", set())]
    pool = fresh or ids or [k for k in GAME_DATA["events"] if not GAME_DATA["events"][k].get("scripted")]
    return random.choices(pool, weights=[GAME_DATA["events"][k].get("weight", 1) for k in pool])[0]


def pop_due_event(player: Player, floor: int) -> Optional[str]:
    """Il primo evento richiamato da una scelta passata che è arrivato a scadenza, se c'è."""
    for i, (due, event_id) in enumerate(player.pending_events):
        if floor >= due:
            player.pending_events.pop(i)
            return event_id
    return None


# ------------------------------------------------------------------ stanza dell'evento
def scene_text(player: Player, scene: dict, floor: int) -> str:
    text = scene["text"]
    for extra in scene.get("extra", []):
        if check(player, extra.get("requires"), floor): text += " " + extra["text"]
    return text


def veiled(player: Player) -> bool:
    """Sguardo Velato: con molta Corruzione, a volte il Labirinto nasconde gli effetti di una scelta."""
    veil = GAME_DATA["meta"]["corruption"]["veil"]
    return player.corruption >= veil["threshold"] and random.random() * 100 < veil["chance"]


def _choice_label(player: Player, choice: dict, floor: int) -> tuple:
    """Etichetta della scelta e se è selezionabile."""
    tag = "".join(f"{Colors.CYAN}[{t}]{Colors.RESET} " for t in tags(choice.get("requires")))
    summary = choice_summary(choice)
    if summary and veiled(player): summary = f" {Colors.MAGENTA}(il Labirinto ti offusca la vista){Colors.RESET}"
    label = f"{tag}{choice['text']}{summary}"
    cost = gold_cost(choice)
    if cost and player.gold < cost: return f"{Colors.RED}{choice['text']}{choice_summary(choice)} (Oro insufficiente){Colors.RESET}", False
    return label, True


def visible_choices(player: Player, scene: dict, floor: int) -> list:
    """(scelta, etichetta, selezionabile) per le scelte da mostrare."""
    out = []
    for choice in scene["choices"]:
        if check(player, choice.get("requires"), floor):
            out.append((choice, *_choice_label(player, choice, floor)))
        elif choice.get("show_locked"):
            hint = choice.get("locked_hint", "Non soddisfi i requisiti")
            out.append((choice, f"{Colors.RED}{choice['text']} ({hint}){Colors.RESET}", False))
    return out


def run_choice(player: Player, choice: dict, floor: int) -> tuple:
    """Esegue una scelta. Ritorna (vivo, prossima scena o None).

    Senza `chance`: prima il racconto (`msg`), poi gli effetti. Con `chance`: prima gli effetti certi (il costo),
    poi il tiro, il racconto dell'esito (`msg` o `fail_msg`) e gli effetti di quell'esito.
    """
    try:
        if "chance" not in choice:
            if choice.get("msg"): display_msg(f"{Colors.CYAN}{choice['msg']}{Colors.RESET}")
            if not apply_effects(player, choice.get("effects"), floor): return False, None
            return True, choice.get("next")
        if not apply_effects(player, choice.get("effects"), floor): return False, None
        success = random.random() * 100 < choice["chance"]
        msg = choice.get("msg") if success else choice.get("fail_msg")
        if msg: display_msg(f"{Colors.YELLOW if success else Colors.RED}{msg}{Colors.RESET}")
        if not apply_effects(player, choice.get("success") if success else choice.get("fail_effects"), floor): return False, None
        return True, choice.get("next") if success else choice.get("fail_next")
    except _Stop:
        return True, None  # fuga da uno scontro: l'evento si chiude senza le ricompense della vittoria


def _header(ev: dict, player: Player) -> str:
    return (f"\n{Colors.MAGENTA}{Colors.BOLD}--- {ev['title']} ---{Colors.RESET}\n"
            f"❤️  HP: {Colors.GREEN}{player.hp}/{player.max_hp}{Colors.RESET} | 💰 Oro: {Colors.YELLOW}{player.gold}{Colors.RESET}\n")


def event_room(player: Player, event_id: str, floor: int):
    ev = GAME_DATA["events"][event_id]
    player.seen_events.add(event_id)
    player.chronicle.append({"kind": "event", "title": ev["title"]})
    seen = _story()["seen_events"]
    seen[event_id] = seen.get(event_id, 0) + 1
    scene_id = ev["start"]
    alive = True
    while scene_id:
        scene = ev["scenes"][scene_id]
        text = scene_text(player, scene, floor)
        clear_screen()
        display_msg(_header(ev, player))
        delay_print(text, 0.03)
        choices = visible_choices(player, scene, floor)
        while True:
            idx = interactive_menu([label for _, label, _ in choices], "\nScegli:")
            if choices[idx][2]: break
        alive, scene_id = run_choice(player, choices[idx][0], floor)
        if not alive: break
        if scene_id: wait_enter("\nPremi INVIO per continuare...")
    PROFILE_MANAGER.save()  # il Labirinto ricorda: flag, contatori e artigiani liberati restano nel profilo
    if alive: wait_enter("\nPremi INVIO per proseguire...")
