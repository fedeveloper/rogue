"""I talenti: ogni `rules.every` livelli l'eroe ne sceglie uno fra `rules.offered` proposti a caso (`data/talents.json`).

Ogni talento ha degli effetti (`effects`) con le stesse chiavi degli attributi più alcune proprie (`TALENT_EFFECT_KEYS`).
`value(player, chiave)` li somma e `attributes.value` li aggiunge a quelli degli attributi, così li leggono gli stessi
punti del gioco. Gli HP massimi si aggiungono quando si sceglie il talento. I talenti valgono per una sola discesa e il
Tomo dell'Oblio non li tocca.
"""
import random

from data_manager import GAME_DATA
from ui import Colors, clear_screen, display_msg, interactive_menu

# Le chiavi che solo i talenti usano; le altre sono quelle degli attributi (`attributes.json → per_point`)
TALENT_EFFECT_KEYS = ("dmg_pct", "def_pct", "lifesteal", "kill_heal_pct", "spell_discount", "ether_on_hit", "potion_pct", "exp_pct")


def rules() -> dict:
    return GAME_DATA["talents"]["rules"]


def definitions() -> dict:
    return GAME_DATA["talents"]["talents"]


def value(player, key: str) -> int:
    """La somma di un effetto su tutti i talenti dell'eroe."""
    return sum(definitions()[t]["effects"].get(key, 0) for t in getattr(player, "talents", []))


def earned(level: int, every: int = None) -> bool:
    """Se raggiungere questo livello fa guadagnare un talento (ogni `every` livelli: il tratto Talento Naturale lo cambia)."""
    return level % (every or rules()["every"]) == 0


def offer(player) -> list:
    """I talenti proposti: `offered` a caso fra quelli che l'eroe non ha ancora."""
    pool = [t for t in definitions() if t not in player.talents]
    return random.sample(pool, min(rules()["offered"], len(pool)))


def take(player, talent_id: str):
    player.talents.append(talent_id)
    hp = definitions()[talent_id]["effects"].get("max_hp", 0)
    player.max_hp += hp
    player.hp += hp


def label(talent_id: str) -> str:
    t = definitions()[talent_id]
    return f"{t['icon']} {t['name']}: {t['desc']}"


def summary(player) -> str:
    """I talenti dell'eroe in una riga, per le Statistiche."""
    return " · ".join(f"{definitions()[t]['icon']} {definitions()[t]['name']}" for t in player.talents)


def choose(player):
    """La scelta dei talenti guadagnati: uno per volta, fra quelli proposti. Non si rimanda."""
    while player.pending_talents > 0:
        choices = offer(player)
        if not choices:
            player.pending_talents = 0
            break
        clear_screen()
        prompt = (f"\n{Colors.MAGENTA}{Colors.BOLD}--- TALENTO: livello {player.level} ---{Colors.RESET}\n"
                  f"Scegli un talento. Vale fino alla fine della discesa.\n")
        idx = interactive_menu([label(t) for t in choices], prompt)
        if not 0 <= idx < len(choices): continue
        take(player, choices[idx])
        player.pending_talents -= 1
        display_msg(f"{Colors.GREEN}Hai imparato il talento {definitions()[choices[idx]]['name']}.{Colors.RESET}")
