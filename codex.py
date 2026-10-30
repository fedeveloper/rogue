"""Il Codice del Labirinto: ciò che hai visto, incontrato e scoperto, raccolto fra una run e l'altra.

Il gioco registra qui nemici incontrati e sconfitti, lettere lette sulle pareti e reliquie trovate; eventi visti,
flag e contatori dei personaggi vengono dalla memoria del Labirinto (`PROFILE_MANAGER.story`).
Ciò che non hai ancora scoperto compare come "???".
"""
from typing import List, Tuple

from data_manager import GAME_DATA, PROFILE_MANAGER, RAW_DATA, echo_name, get_element_icon
from ui import Colors, clear_screen, display_msg, interactive_menu, wait_enter

UNKNOWN = f"{Colors.RED}???{Colors.RESET}"


# ------------------------------------------------------------------ registrazione
def _enemy(name: str) -> dict:
    return PROFILE_MANAGER.codex["enemies"].setdefault(name, {"seen": 0, "killed": 0})


def record_enemy_seen(name: str):
    _enemy(name)["seen"] += 1


def record_enemy_killed(name: str):
    _enemy(name)["killed"] += 1


def record_phase(name: str, phase: int):
    """Il boss `name` è entrato nella sua fase numero `phase` (da 1)."""
    rec = _enemy(name)
    rec["phases"] = max(rec.get("phases", 0), phase)


def record_rune(rune_id: str):
    found = PROFILE_MANAGER.codex.setdefault("runes", [])
    if rune_id not in found: found.append(rune_id)


def record_runeword(word_id: str):
    found = PROFILE_MANAGER.codex.setdefault("runewords", [])
    if word_id not in found: found.append(word_id)


def record_letter(index: int):
    if index not in PROFILE_MANAGER.codex["letters"]: PROFILE_MANAGER.codex["letters"].append(index)


def record_reaction(key: str):
    found = PROFILE_MANAGER.codex.setdefault("reactions", [])
    if key not in found: found.append(key)


def record_spell(spell_id: str):
    found = PROFILE_MANAGER.codex.setdefault("spells", [])
    if spell_id not in found: found.append(spell_id)


def record_relic(relic_id: str):
    if relic_id not in PROFILE_MANAGER.codex["relics"]: PROFILE_MANAGER.codex["relics"].append(relic_id)


# ------------------------------------------------------------------ capitoli dei personaggi
def character_chapters(char_id: str) -> int:
    """Quanti capitoli della storia del personaggio hai vissuto."""
    char = GAME_DATA["story"]["characters"][char_id]
    return min(len(char["chapters"]), PROFILE_MANAGER.get_counter(char["counter"]))


# ------------------------------------------------------------------ completamento
def sections() -> List[Tuple[str, int, int]]:
    """(nome, scoperti, totale) per ogni sezione del Codice."""
    enemies = PROFILE_MANAGER.codex["enemies"]
    bestiary = list(RAW_DATA["enemies"]) + list(RAW_DATA["bosses"])
    chars = GAME_DATA["story"]["characters"]
    events = [k for k in GAME_DATA["events"]]
    return [
        ("Bestiario", sum(1 for n in bestiary if enemies.get(n, {}).get("killed")), len(bestiary)),
        ("Personaggi", sum(character_chapters(c) for c in chars), sum(len(c["chapters"]) for c in chars.values())),
        ("Eventi", sum(1 for k in events if PROFILE_MANAGER.story["seen_events"].get(k)), len(events)),
        ("Lettere insanguinate", len(set(PROFILE_MANAGER.codex["letters"]) & set(range(len(GAME_DATA["lore"]["letters"])))), len(GAME_DATA["lore"]["letters"])),
        ("Reliquie", len(set(PROFILE_MANAGER.codex["relics"]) & {r["id"] for r in RAW_DATA["relics"]}), len(RAW_DATA["relics"])),
        ("Finali", len(set(PROFILE_MANAGER.story.get("endings", {})) & {e["id"] for e in GAME_DATA["story"]["endings"]}), len(GAME_DATA["story"]["endings"])),
        ("Rune", len(set(PROFILE_MANAGER.codex.get("runes", [])) & set(GAME_DATA["runes"]["runes"])), len(GAME_DATA["runes"]["runes"])),
        ("Parole runiche", len(set(PROFILE_MANAGER.codex.get("runewords", [])) & set(GAME_DATA["runes"]["words"])), len(GAME_DATA["runes"]["words"])),
        ("Nemesi", len(PROFILE_MANAGER._data.get("nemeses_fallen", [])), len(PROFILE_MANAGER._data.get("nemeses_fallen", [])) + len(PROFILE_MANAGER._data.get("nemeses", []))),
        ("Cimitero", len(PROFILE_MANAGER._data.get("cemetery", [])), len(PROFILE_MANAGER._data.get("cemetery", []))),
        ("Fasi dei boss", sum(min(enemies.get(n, {}).get("phases", 0), len(ph)) for n, ph in GAME_DATA["phases"].items()), sum(len(ph) for ph in GAME_DATA["phases"].values())),
        ("Reazioni elementali", len(set(PROFILE_MANAGER.codex.get("reactions", [])) & set(GAME_DATA["elements"]["reactions"])), len(GAME_DATA["elements"]["reactions"])),
        ("Incantesimi", len(set(PROFILE_MANAGER.codex.get("spells", [])) & set(GAME_DATA["spells"]["spells"])), len(GAME_DATA["spells"]["spells"])),
    ]


# Sezioni che raccontano la tua storia invece di elencare scoperte: non contano nel completamento
UNCOUNTED = ("Nemesi", "Cimitero")


def completion() -> int:
    counted = [s for s in sections() if s[0] not in UNCOUNTED]
    found = sum(s[1] for s in counted)
    total = sum(s[2] for s in counted)
    return found * 100 // total if total else 0


# ------------------------------------------------------------------ pagine
def bestiary_page() -> List[str]:
    lines = []
    known = PROFILE_MANAGER.codex["enemies"]
    for title, pool in (("NEMICI", RAW_DATA["enemies"]), ("BOSS", RAW_DATA["bosses"])):
        lines.append(f"{Colors.YELLOW}{Colors.BOLD}{title}{Colors.RESET}")
        for name, data in sorted(pool.items(), key=lambda kv: kv[1]["base_hp"] * kv[1]["base_atk"]):
            rec = known.get(name)
            if not rec or not rec["seen"]:
                lines.append(f"  {UNKNOWN}")
                continue
            head = f"  {Colors.BOLD}{name}{Colors.RESET}" + (f" — {data['title']}" if data.get("title") else "")
            lines.append(f"{head} [{get_element_icon(data['element'])}]  incontri {rec['seen']} · sconfitti {rec['killed']}")
            if rec["killed"] and data.get("lore"): lines.append(f"    {Colors.CYAN}{data['lore']}{Colors.RESET}")
            elif not rec["killed"]: lines.append(f"    {Colors.RED}Sconfiggilo per conoscerne la storia.{Colors.RESET}")
            if rec["killed"] and (style := GAME_DATA["moves"]["profiles"].get(data.get("profile"))):
                lines.append(f"    {Colors.MAGENTA}Stile: {style['name']}. {style['desc']}{Colors.RESET}")
    return lines


def runes_page() -> List[str]:
    found = PROFILE_MANAGER.codex.get("runes", [])
    lines = []
    for rid, r in GAME_DATA["runes"]["runes"].items():
        if rid in found: lines.append(f"  {r['icon']} {Colors.BOLD}{r['name']}{Colors.RESET} [{r['family']}] — {r['desc']}")
        else: lines.append(f"  {UNKNOWN} [{r['family']}]")
    return lines


def runewords_page() -> List[str]:
    """Le parole runiche scoperte; di quelle ignote si vede quante rune servono e, se l'hai già trovata, la prima."""
    found, known_runes = PROFILE_MANAGER.codex.get("runewords", []), PROFILE_MANAGER.codex.get("runes", [])
    runes = GAME_DATA["runes"]["runes"]
    lines = []
    for wid, w in GAME_DATA["runes"]["words"].items():
        icons = "".join(runes[r]["icon"] for r in w["runes"])
        if wid in found:
            lines.append(f"  {Colors.BOLD}«{w['name']}»{Colors.RESET} {icons} — {w['desc']}")
            lines.append(f"    {Colors.CYAN}{' + '.join(runes[r]['name'] for r in w['runes'])}{Colors.RESET}")
        else:
            hint = f", fra cui {runes[w['runes'][0]]['name']}" if w["runes"][0] in known_runes else ""
            lines.append(f"  {UNKNOWN} — {len(w['runes'])} rune{hint}")
    return lines


def nemeses_page() -> List[str]:
    """Le Nemesi: chi ti ha ucciso e ti aspetta ancora, e chi hai già sconfitto."""
    import nemesis
    lines = [f"{Colors.YELLOW}{Colors.BOLD}TI ASPETTANO{Colors.RESET}"]
    for nem in nemesis.active():
        trait = GAME_DATA["nemesis"]["traits"][nem["trait"]]
        lines.append(f"  {Colors.MAGENTA}{Colors.BOLD}{nemesis.full_name(nem)}{Colors.RESET} ({nem['enemy']}) — ti ha ucciso {nem['kills']} volte, l'ultima al piano {nem['floor']}")
        lines.append(f"    {trait['name']}: {trait['desc']} Ha con sé {nem['gold']} Oro.")
    if not nemesis.active(): lines.append("  Nessuno. Per ora.")
    lines.append(f"\n{Colors.YELLOW}{Colors.BOLD}SCONFITTE{Colors.RESET}")
    for nem in reversed(nemesis.fallen()):
        lines.append(f"  {nem['name']} {GAME_DATA['nemesis']['ranks'][nem['rank'] - 1]} ({nem['enemy']}), che aveva ucciso {nem['kills']} volte")
    if not nemesis.fallen(): lines.append("  Nessuna.")
    return lines


CEMETERY_PAGE = 10
OUTCOME_ICONS = {"death": "🪦", "escape": "🏃", "victory": "🏆"}


def cemetery_page() -> List[str]:
    """Gli epitaffi delle ultime discese, dalla più recente."""
    graves = PROFILE_MANAGER._data.get("cemetery", [])
    if not graves: return ["  Nessuno. Il Labirinto non ha ancora storie da raccontare su di te."]
    lines = []
    for g in reversed(graves[-CEMETERY_PAGE:]):
        lines.append(f"  {OUTCOME_ICONS.get(g['outcome'], '')} {Colors.BOLD}{g['date']} · {g['class']} · piano {g['floor']}{Colors.RESET}")
        lines.append(f"    {Colors.CYAN}{' '.join(g['epitaph'])}{Colors.RESET}")
    return lines


def phases_page() -> List[str]:
    """Le fasi dei boss che hai visto: ogni boss cambia a una soglia di HP, e lo scopri solo portandolo fin lì."""
    lines, known = [], PROFILE_MANAGER.codex["enemies"]
    for name, data in sorted(RAW_DATA["bosses"].items(), key=lambda kv: kv[1]["base_hp"] * kv[1]["base_atk"]):
        phases, seen = GAME_DATA["phases"].get(name, []), known.get(name, {}).get("phases", 0)
        if not phases: continue
        lines.append(f"  {Colors.BOLD}{name if known.get(name, {}).get('seen') else UNKNOWN}{Colors.RESET}")
        for i, ph in enumerate(phases):
            if i < seen: lines.append(f"    {ph['at_pct']}% HP — {Colors.MAGENTA}{ph['name']}{Colors.RESET}: {Colors.CYAN}{ph['text']}{Colors.RESET}")
            else: lines.append(f"    {ph['at_pct']}% HP — {UNKNOWN}")
    return lines


def characters_page() -> List[str]:
    lines = []
    for char_id, char in GAME_DATA["story"]["characters"].items():
        done = character_chapters(char_id)
        if not done:
            lines += [f"{UNKNOWN} — {Colors.RED}{char['hint']}{Colors.RESET}", ""]
            continue
        lines.append(f"{Colors.MAGENTA}{Colors.BOLD}{char['name']}{Colors.RESET}, {char['epithet']}  ({done}/{len(char['chapters'])})")
        for i, chapter in enumerate(char["chapters"]):
            lines.append(f"  {i + 1}. {chapter['text']}" if i < done else f"  {i + 1}. {UNKNOWN}")
        for note in char.get("notes", []):
            if PROFILE_MANAGER.get_flag(note["flag"]): lines.append(f"  {Colors.YELLOW}✦ {note['text']}{Colors.RESET}")
        lines.append("")
    return lines


def events_page() -> List[str]:
    seen = PROFILE_MANAGER.story["seen_events"]
    lines = []
    for ev_id, ev in GAME_DATA["events"].items():
        n = seen.get(ev_id, 0)
        lines.append(f"  {ev['title']}  {Colors.CYAN}(visto {n} {'volta' if n == 1 else 'volte'}){Colors.RESET}" if n else f"  {UNKNOWN}")
    return lines


def letters_page() -> List[str]:
    found = set(PROFILE_MANAGER.codex["letters"])
    return [f"  {i + 1:2d}. \"{text}\"" if i in found else f"  {i + 1:2d}. {UNKNOWN}" for i, text in enumerate(GAME_DATA["lore"]["letters"])]


def relics_page() -> List[str]:
    found = set(PROFILE_MANAGER.codex["relics"])
    lines = []
    for r in RAW_DATA["relics"]:
        if r["id"] in found:
            lines.append(f"  {Colors.MAGENTA}{r['name']}{Colors.RESET} — {r['desc']}")
            if r.get("lore"): lines.append(f"    {Colors.YELLOW}{r['lore']}{Colors.RESET}")
        else:
            lines.append(f"  {UNKNOWN}")
    return lines


def spells_page() -> List[str]:
    """Gli incantesimi lanciati almeno una volta, con elemento, costo e descrizione."""
    found = set(PROFILE_MANAGER.codex.get("spells", []))
    lines = []
    for sid, s in GAME_DATA["spells"]["spells"].items():
        if sid in found: lines.append(f"  {s['icon']} {Colors.BOLD}{s['name']}{Colors.RESET} [{get_element_icon(s['element'])}] · {s['cost']} Etere\n    {Colors.CYAN}{s['desc']}{Colors.RESET}")
        else: lines.append(f"  {UNKNOWN}")
    return lines


def reactions_page() -> List[str]:
    found = set(PROFILE_MANAGER.codex.get("reactions", []))
    lines = [f"  {Colors.CYAN}L'arma marchia il nemico con il suo elemento; in guardia, anche l'armatura marchia chi ti colpisce.",
             f"  Due elementi diversi sullo stesso nemico possono reagire.{Colors.RESET}", ""]
    for key, r in GAME_DATA["elements"]["reactions"].items():
        a, b = key.split("+")
        if key in found: lines.append(f"  {r['icon']} {Colors.MAGENTA}{r['name']}{Colors.RESET} ({get_element_icon(a)} + {get_element_icon(b)}) — {r['desc']}")
        else: lines.append(f"  {UNKNOWN}")
    return lines


def endings_page() -> List[str]:
    seen = PROFILE_MANAGER.story.get("endings", {})
    lines = []
    for e in GAME_DATA["story"]["endings"]:
        if e["id"] in seen:
            n = seen[e["id"]]
            lines.append(f"  {Colors.MAGENTA}{e['title']}{Colors.RESET}  {Colors.CYAN}(visto {n} {'volta' if n == 1 else 'volte'}){Colors.RESET}")
            lines.append(f"    {e['text'][-1]}")
        else:
            lines.append(f"  {UNKNOWN} — {Colors.RED}{e['hint']}{Colors.RESET}")
    return lines


PAGES = {"Bestiario": bestiary_page, "Personaggi": characters_page, "Eventi": events_page,
         "Lettere insanguinate": letters_page, "Reliquie": relics_page, "Finali": endings_page,
         "Rune": runes_page, "Parole runiche": runewords_page, "Nemesi": nemeses_page, "Cimitero": cemetery_page, "Fasi dei boss": phases_page, "Reazioni elementali": reactions_page, "Incantesimi": spells_page}


def show_codex():
    while True:
        clear_screen()
        stats = sections()
        options = [f"{name} ({found}/{total})" for name, found, total in stats]
        prompt = (f"{Colors.MAGENTA}{Colors.BOLD}=== 📖 IL CODICE DEL LABIRINTO ==={Colors.RESET}\n"
                  f"Completato al {Colors.CYAN}{completion()}%{Colors.RESET}. Ciò che non hai ancora scoperto è segnato con ???"
                  + (f"\nNel Ciclo del Labirinto sei arrivato fino all'{Colors.MAGENTA}{echo_name(best - 1)}{Colors.RESET}." if (best := PROFILE_MANAGER._data.get("best_echo", 0)) >= 2 else ""))
        idx = interactive_menu(options, prompt, cancellable=True)
        if idx == -1: break  # "Indietro", aggiunto dal menu
        name = stats[idx][0]
        clear_screen()
        display_msg(f"{Colors.MAGENTA}{Colors.BOLD}--- {name.upper()} ({stats[idx][1]}/{stats[idx][2]}) ---{Colors.RESET}\n")
        for line in PAGES[name](): display_msg(line)
        wait_enter("\nPremi INVIO per tornare al Codice...")
