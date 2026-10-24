"""Il Fuoco del Campo: i personaggi incontrati nel Labirinto e le strutture da costruire con l'Essenza.

I personaggi compaiono al campo quando la loro storia è andata abbastanza avanti (condizioni del profilo,
come negli eventi); la prima frase le cui condizioni sono vere è quella che dicono, e il loro dono si riceve
una volta sola. Le strutture costruite restano nel profilo come flag `camp_<id>`; quelle a più livelli
(vedi `camp_rules`) si costruiscono un livello alla volta.
"""
from typing import Optional

import camp_rules
from data_manager import GAME_DATA, PROFILE_MANAGER
from events import apply_effects, check, choice_summary
from ui import Colors, clear_screen, delay_print, display_msg, interactive_menu, wait_enter


def camp() -> dict:
    return GAME_DATA["story"]["camp"]


def present_characters() -> list:
    return [c for c in camp()["characters"] if check(None, c.get("requires"), 0)]


def current_line(character: dict) -> str:
    return next(l["text"] for l in character["lines"] if check(None, l.get("requires"), 0))


def gift_pending(character: dict) -> bool:
    return bool(character.get("gift")) and not PROFILE_MANAGER.get_flag(f"camp_dono_{character['id']}")


def talk(character: dict):
    clear_screen()
    display_msg(f"{Colors.MAGENTA}{Colors.BOLD}--- {character['name']} ---{Colors.RESET}\n")
    delay_print(current_line(character), 0.03)
    if gift_pending(character):
        gift = character["gift"]
        PROFILE_MANAGER.essence += gift["essence"]
        PROFILE_MANAGER.set_flag(f"camp_dono_{character['id']}")
        display_msg(f"\n{Colors.YELLOW}{gift['text']}{Colors.RESET}")
        display_msg(f"{Colors.CYAN}+{gift['essence']} Essenza.{Colors.RESET}")
        PROFILE_MANAGER.save()
    wait_enter("\nPremi INVIO per tornare al fuoco...")


def structure(structure_id: str) -> Optional[dict]:
    return next((s for s in camp()["structures"] if s["id"] == structure_id), None)


def built(structure_id: str) -> bool:
    return PROFILE_MANAGER.get_flag(f"camp_{structure_id}")


def complete(s: dict) -> bool:
    """Tutti i livelli della struttura sono costruiti."""
    return camp_rules.level(s["id"]) >= len(camp_rules.levels(s))


def next_level(s: dict) -> Optional[dict]:
    return None if complete(s) else camp_rules.levels(s)[camp_rules.level(s["id"])]


def can_build(s: dict) -> bool:
    return not complete(s) and check(None, s.get("requires"), 0)


def build(s: dict) -> bool:
    """Costruisce la struttura, o il suo livello successivo."""
    if not can_build(s) or PROFILE_MANAGER.essence < next_level(s)["cost"]: return False
    PROFILE_MANAGER.essence -= next_level(s)["cost"]
    camp_rules.set_level(s["id"], camp_rules.level(s["id"]) + 1)
    PROFILE_MANAGER.save()
    return True


def _structure_label(s: dict) -> str:
    many, lvl = len(camp_rules.levels(s)) > 1, camp_rules.level(s["id"])
    tag = f" Lv.{lvl}/{len(camp_rules.levels(s))}" if many and lvl else ""
    if complete(s):
        done = " ".join(lv["desc"] for lv in camp_rules.built_levels(s))
        return f"{Colors.GREEN}{s['name']}{tag} [COSTRUITO]{Colors.RESET} — {done}"
    if not check(None, s.get("requires"), 0): return f"{Colors.RED}??? ({s.get('locked_hint', 'Non ancora disponibile')}){Colors.RESET}"
    nxt = next_level(s)
    verb = f"Migliora: {s['name']}{tag} → Lv.{lvl + 1}" if lvl else (f"Costruisci: {s['name']}" + (" Lv.1" if many else ""))
    return f"{verb} (✨{nxt['cost']}) — {nxt['desc']}"


def show_camp_fire():
    while True:
        clear_screen()
        people = present_characters()
        options = [f"Parla con {c['name']}" + (f" {Colors.YELLOW}✦{Colors.RESET}" if gift_pending(c) else "") for c in people]
        options += [_structure_label(s) for s in camp()["structures"]]
        intro = "Intorno al fuoco siede chi hai salvato, ascoltato o tradito nel Labirinto." if people else \
                "Intorno al fuoco non c'è ancora nessuno. Chi incontrerai nel Labirinto potrebbe venire a scaldarsi qui."
        prompt = (f"{Colors.MAGENTA}{Colors.BOLD}=== 🔥 IL FUOCO DEL CAMPO ==={Colors.RESET}\nEssenza: {Colors.CYAN}✨ {PROFILE_MANAGER.essence}{Colors.RESET}\n"
                  f"{intro}")
        idx = interactive_menu(options, prompt, cancellable=True)
        if idx == -1: break
        if idx < len(people):
            talk(people[idx])
            continue
        s = camp()["structures"][idx - len(people)]
        if not can_build(s): continue
        if build(s):
            lvl = camp_rules.level(s["id"])
            display_msg(f"\n{Colors.GREEN}Hai costruito {s['name']}" + (f" (Lv.{lvl})" if len(camp_rules.levels(s)) > 1 else "") + f"!{Colors.RESET}")
        else: display_msg(f"\n{Colors.RED}Essenza insufficiente.{Colors.RESET}")
        wait_enter()


def start_of_run_boon(player):
    """I doni del Campo a inizio discesa: quelli dei livelli costruiti (`start`), poi lo Scrittoio di Silas,
    dove si sceglie un dono dalle pagine del diario."""
    gifts = camp_rules.total("start")
    if gifts.get("scroll"):
        from entities import generate_scroll
        for _ in range(gifts["scroll"]):
            item = generate_scroll(1)
            player.inventory.append(item)
            display_msg(f"{Colors.CYAN}📚 Dalla Biblioteca dell'Arcano porti con te: {item.display_name}.{Colors.RESET}")
    if gifts.get("points"):
        player.unspent_points += gifts["points"]; player.points_offered = False
        display_msg(f"{Colors.YELLOW}⚔️ Dalla Sala d'Armi: {gifts['points']} punti abilità da spendere.{Colors.RESET}")
    s = structure("scrittoio_silas")
    if not s or not built(s["id"]): return
    boons = s["boons"]
    options = [f"{b['text']}{choice_summary(b)}" for b in boons] + ["Lascia il diario chiuso"]
    idx = interactive_menu(options, f"\n{Colors.MAGENTA}📖 Lo Scrittoio di Silas: quale pagina leggi prima di scendere?{Colors.RESET}")
    if idx < len(boons): apply_effects(player, boons[idx]["effects"], 1)
