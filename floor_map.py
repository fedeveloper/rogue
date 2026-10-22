"""La mappa del piano: quattro file di stanze collegate e il boss in fondo, visibili fin dall'inizio.

Ogni file ha 2 o 3 stanze, alternate (2-3-2-3 o 3-2-3-2), in tre colonne (0 sinistra, 1 centro, 2 destra).
Da una stanza si prosegue verso le stanze della fila successiva che stanno nella stessa colonna o in quella
accanto, così i percorsi non si incrociano e ogni stanza è raggiungibile. Il giocatore vede tutta la mappa e
sceglie di fila in fila; il bioma del piano cambia i pesi delle stanze e aggiunge la sua stanza speciale.
"""
import random
from typing import List, Optional

from constants import INFINITE_MODE_THRESHOLD
from data_manager import GAME_DATA, PROFILE_MANAGER, get_biome, get_element_icon
from entities import Enemy, Player
from events import pick_event, pop_due_event
from ui import Colors, visible_width

ROWS = 4  # file di stanze prima del boss
TALL_MAP_ROWS = 30  # da quest'altezza del terminale i collegamenti occupano due righe
# Solo emoji larghe di natura (senza selettore di variante): le colonne della mappa restano allineate in ogni terminale
ROOM_ICONS = {"combat": "👹", "vendor": "💰", "campfire": "🔥", "treasure": "💎", "trap": "💀", "event": "🎭", "mystery": "❓", "boss": "👑"}
ROOM_NAMES = {"combat": "Scontro", "vendor": "Mercante", "campfire": "Falò", "treasure": "Forziere", "trap": "Trappola",
              "event": "Evento", "mystery": "Mistero", "boss": "Boss"}
SLOTS = {1: [1], 2: [0, 2], 3: [0, 1, 2]}
SIDES = {0: "sinistra", 1: "centro", 2: "destra"}
# Coppie di stanze che non escono mai nella stessa fila
FORBIDDEN = ({"trap", "treasure"}, {"trap", "vendor"})
CELL = 16  # colonne di terminale per ogni colonna della mappa
DIM = "\033[90m"


def generate_row(floor: int, step: int, weights_def: dict, cooldowns_def: dict, room_cooldowns: dict, active_pacts: list,
                 player: Optional[Player] = None, count: int = 2) -> List[dict]:
    """Una fila di stanze di tipo diverso (al passo 5, il boss); solo lo scontro può ripetersi, se mancano tipi
    disponibili. Aggiorna i tempi di ricarica dei tipi."""
    for k in room_cooldowns:
        if room_cooldowns[k] > 0: room_cooldowns[k] -= 1

    if step == ROWS + 1:
        # Il boss finale attende solo all'ultimo piano della discesa standard
        return [{"type": "boss", "enemy": Enemy(floor, True, active_pacts, final=floor == INFINITE_MODE_THRESHOLD)}]

    avail = {rt: w for rt, w in weights_def.items() if room_cooldowns.get(rt, 0) <= 0 and w > 0}
    if len(avail) < 2: avail = {"combat": 100, "mystery": 1}
    while True:
        types = []
        while len(types) < count:
            pool = [rt for rt in avail if rt not in types]
            # Se i tempi di ricarica lasciano pochi tipi, la fila si completa con un altro scontro (un nemico diverso)
            types.append(random.choices(pool, weights=[avail[rt] for rt in pool])[0] if pool else "combat")
        if not any(pair <= set(types) for pair in FORBIDDEN): break

    for rt in types: room_cooldowns[rt] = cooldowns_def.get(rt, 0) + 1
    row = []
    for rt in types:
        d = {"type": rt}
        if rt == "combat": d["enemy"] = Enemy(floor, False, active_pacts)
        if rt == "event": d["event_id"] = pick_event(floor, player)
        row.append(d)
    return row


def _signature_event(biome: dict, player: Optional[Player]) -> Optional[str]:
    ids = [e for e in biome.get("signature_events", []) if e in GAME_DATA["events"]]
    if not ids: return None
    fresh = [e for e in ids if player is None or e not in player.seen_events]
    return random.choice(fresh or ids)


def generate_floor_map(floor: int, weights_def: dict, cooldowns_def: dict, room_cooldowns: dict, active_pacts: list,
                       player: Optional[Player] = None) -> List[List[dict]]:
    biome = get_biome(floor)
    weights = dict(weights_def)
    for rt, mult in (biome or {}).get("room_weights", {}).items():
        if rt in weights: weights[rt] *= mult
    sizes = [2, 3] if random.random() < 0.5 else [3, 2]
    rows = [generate_row(floor, step, weights, cooldowns_def, room_cooldowns, active_pacts, player, count=sizes[(step - 1) % 2])
            for step in range(1, ROWS + 1)]
    rows.append(generate_row(floor, ROWS + 1, weights, cooldowns_def, room_cooldowns, active_pacts, player))

    # Una scelta passata torna a bussare: l'evento richiamato prende il posto di una stanza della prima fila
    if player is not None and (due := pop_due_event(player, floor)):
        rows[0][random.randrange(len(rows[0]))] = {"type": "event", "event_id": due, "fated": True}
    # La stanza speciale del bioma (es. la Nostalgia Letale dei Chiostri), in una delle file centrali
    if biome and (sig := _signature_event(biome, player)):
        row = rows[random.randrange(1, ROWS)]
        events = [i for i, d in enumerate(row) if d["type"] == "event"]
        row[events[0] if events else random.randrange(len(row))] = {"type": "event", "event_id": sig, "signature": True}

    for r, row in enumerate(rows):
        for d, slot in zip(row, SLOTS[len(row)]): d["slot"] = slot
    for r in range(len(rows) - 1):
        for d in rows[r]:
            d["links"] = [j for j, nxt in enumerate(rows[r + 1]) if abs(nxt["slot"] - d["slot"]) <= 1]
    rows[-1][0]["links"] = []
    return rows


def reachable(rows: List[List[dict]], step: int, current: Optional[dict]) -> List[int]:
    """Indici delle stanze della fila `step` (da 1) raggiungibili dalla stanza attuale."""
    if current is None: return list(range(len(rows[step - 1])))
    return list(current["links"])


# ------------------------------------------------------------------ descrizioni e disegno
def room_label(d: dict, sixth_sense: bool = False, biome: Optional[dict] = None) -> str:
    """Testo della stanza per il menu: icona, nome e ciò che si sa in anticipo."""
    label = f"{ROOM_ICONS[d['type']]} {ROOM_NAMES[d['type']]}"
    if d.get("fated"): label += f" {Colors.MAGENTA}✦ qualcosa ti stava aspettando{Colors.RESET}"
    if d.get("signature") and biome: label += f" {biome['icon']} {Colors.MAGENTA}{biome['hazard']['name']}{Colors.RESET}"
    if sixth_sense:
        if d["type"] in ("combat", "boss"): label += f" ({d['enemy'].name} {get_element_icon(d['enemy'].element)})"
        elif d["type"] == "event": label += f" ({GAME_DATA['events'][d['event_id']]['title']})"
        elif d["type"] == "mystery": label += f" ({Colors.MAGENTA}Aura illeggibile{Colors.RESET})"
    return label


def _short(d: dict, biome: Optional[dict]) -> str:
    mark = "✦" if d.get("fated") else (biome["icon"] if d.get("signature") and biome else "")
    return f"{ROOM_ICONS[d['type']]} {ROOM_NAMES[d['type']]}{mark}"


def _place(cells: List[tuple]) -> str:
    """Una riga con i testi centrati sulle colonne: cells = [(centro, testo)]."""
    line, col = "", 0
    for center, text in sorted(cells):
        start = max(col, center - visible_width(text) // 2)
        line += " " * (start - col) + text
        col = start + visible_width(text)
    return line


def render_map(rows: List[List[dict]], step: int, path: List[int], biome: Optional[dict] = None, tall: bool = False) -> List[str]:
    """Righe della mappa. `path` sono gli indici scelti nelle file già superate; `step` è la fila da scegliere.

    Verde: il percorso fatto. Giallo: le stanze raggiungibili ora. Grigio: ciò che resta fuori dal percorso.
    Le etichette sono centrate sulla loro colonna e i collegamenti uniscono i centri; con `tall` ogni collegamento
    occupa due righe, così le diagonali si leggono come linee continue.
    """
    current = rows[len(path) - 1][path[-1]] if path else None
    options = set(reachable(rows, step, current)) if step <= len(rows) else set()
    future = _future(rows, step, current)
    lines = []
    for r, row in enumerate(rows):
        cells = []
        for i, d in enumerate(row):
            if r < len(path): color = Colors.GREEN + Colors.BOLD if path[r] == i else DIM
            elif r == step - 1: color = Colors.YELLOW + Colors.BOLD if i in options else DIM
            else: color = "" if (r, i) in future else DIM
            cells.append((_center(d["slot"]), f"{color}{_short(d, biome)}{Colors.RESET}"))
        marker = "★" if r == len(rows) - 1 else str(r + 1)
        lines.append(f"  {marker}  " + _place(cells))
        if r < len(rows) - 1: lines += ["     " + l for l in _connectors(row, rows[r + 1], 2 if tall else 1)]
    return lines


def _future(rows, step, current) -> set:
    """(fila, indice) delle stanze ancora raggiungibili dopo la fila da scegliere."""
    frontier = {(step - 1, i) for i in reachable(rows, step, current)} if step <= len(rows) else set()
    seen = set(frontier)
    while frontier:
        nxt = set()
        for r, i in frontier:
            for j in rows[r][i].get("links", []): nxt.add((r + 1, j))
        seen |= nxt
        frontier = nxt
    return seen


def _center(slot: int) -> int:
    return slot * CELL + CELL // 2


def _connectors(row: List[dict], nxt: List[dict], height: int = 1) -> List[str]:
    """Linee fra una fila e la successiva: verticali sotto il centro, diagonali divise in `height` tratti."""
    lines = [[" "] * (3 * CELL) for _ in range(height)]
    for d in row:
        for j in d["links"]:
            a, b = _center(d["slot"]), _center(nxt[j]["slot"])
            for k in range(height):
                x = a + (b - a) * (k + 1) // (height + 1)
                lines[k][x] = "│" if a == b else ("╲" if b > a else "╱")
    return ["".join(l).rstrip() for l in lines]
