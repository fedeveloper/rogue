"""I fili delle lettere: le discese dimenticate del Ritornante, raccontate in lettere brevi (`data/lettere.json`).

Ogni filo si apre con il progresso del profilo (`requires`) e si legge in ordine: ai falò e accanto ai forzieri, a
volte (`rules.chance`, in %), una pietra porta inciso il prossimo pezzo di un filo già cominciato o appena aperto. Chi
completa un filo ne legge l'epilogo nel Codice (*Discese dimenticate*). Sono solo testo: il caso viene da `texts.RNG`,
quindi trovare una lettera non cambia nessun tiro di dado della discesa, e il profilo registra solo quante lettere di
ogni filo si sono lette (`codex.threads`). Le lettere insanguinate della v5 (`lore.json`) restano a parte, con le loro
regole.
"""
from typing import Optional

import texts
from data_manager import GAME_DATA, PROFILE_MANAGER
from ui import Colors, delay_print, display_msg


def threads() -> list:
    return GAME_DATA["lettere"]["threads"]


def found(thread_id: str) -> int:
    return PROFILE_MANAGER.codex.setdefault("threads", {}).get(thread_id, 0)


def complete(thread: dict) -> bool:
    return found(thread["id"]) >= len(thread["letters"])


def open_threads() -> list:
    """I fili che il profilo ha aperto e non ha ancora finito di leggere."""
    from events import check
    return [t for t in threads() if not complete(t) and check(None, t.get("requires"), 0)]


def next_letter() -> Optional[tuple]:
    """Il prossimo pezzo di un filo aperto, scelto a caso fra i fili, già registrato come letto: (filo, testo)."""
    pool = open_threads()
    if not pool: return None
    thread = pool[texts.index(len(pool))]
    n = found(thread["id"])
    PROFILE_MANAGER.codex["threads"][thread["id"]] = n + 1
    return thread, thread["letters"][n]


def maybe_show():
    """A volte, in una stanza tranquilla (falò, forziere), una lettera di un filo: solo testo."""
    if texts.RNG.random() * 100 >= GAME_DATA["lettere"]["rules"]["chance"]: return
    hit = next_letter()
    if not hit: return
    thread, letter = hit
    display_msg(f"\n{Colors.YELLOW}📜 Su una pietra qualcuno ha inciso, con una calligrafia che ti sembra di conoscere:{Colors.RESET}")
    delay_print(f"\"{letter}\"", 0.04)
    if complete(thread): display_msg(f"{Colors.MAGENTA}Ti sembra di ricordare una discesa intera: «{thread['title']}». (Codice: Discese dimenticate){Colors.RESET}")
