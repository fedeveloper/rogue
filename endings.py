"""I finali: dopo il Dio Antico si sceglie fra quelli che la storia della discesa (e del profilo) ha aperto.

Ogni finale ha condizioni come quelle degli eventi (flag del profilo, Corruzione della run, lettere del Codice),
un testo, e un premio in Essenza. Il primo, "Il Sonno Spezzato", è sempre disponibile.
"""
from data_manager import GAME_DATA, PROFILE_MANAGER
from events import check
from ui import Colors, clear_screen, delay_print, display_msg, interactive_menu, wait_enter

FINAL_FLOOR = 30


def endings() -> list:
    return GAME_DATA["story"]["endings"]


def seen_endings() -> dict:
    return PROFILE_MANAGER.story.setdefault("endings", {})


def available_endings(player) -> list:
    return [e for e in endings() if check(player, e.get("requires"), FINAL_FLOOR)]


def choose_ending(player) -> dict:
    options = available_endings(player)
    labels = [f"{e['choice']}" + (f" {Colors.CYAN}(già visto){Colors.RESET}" if e["id"] in seen_endings() else "") for e in options]
    idx = interactive_menu(labels, f"\n{Colors.MAGENTA}{Colors.BOLD}Il Dio Antico è caduto. Davanti a te si aprono {len(options)} strade.{Colors.RESET}")
    ending = options[idx]
    clear_screen()
    display_msg(f"{Colors.YELLOW}{Colors.BOLD}=== {ending['title'].upper()} ==={Colors.RESET}\n")
    for paragraph in ending["text"]:
        delay_print(paragraph, 0.03)
        display_msg()
    first = ending["id"] not in seen_endings()
    seen_endings()[ending["id"]] = seen_endings().get(ending["id"], 0) + 1
    if ending["reward"]["essence"]:
        player.essence_gathered += ending["reward"]["essence"]
        display_msg(f"{Colors.CYAN}+{ending['reward']['essence']} Essenza per questo finale.{Colors.RESET}")
    if first: display_msg(f"{Colors.MAGENTA}Nuovo finale nel Codice: {ending['title']} ({len(seen_endings())}/{len(endings())}).{Colors.RESET}")
    wait_enter("\nPremi INVIO...")
    return ending
