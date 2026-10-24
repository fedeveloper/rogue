import json
import os
from ui import Colors, clear_screen, delay_print, interactive_menu, display_msg, wait_enter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOOKS_FILE = os.path.join(BASE_DIR, "data", "books.json")

def load_books():
    if not os.path.exists(BOOKS_FILE): return {}
    with open(BOOKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("books", {})

# Letto una volta: i bonus dell'Archivio si consultano a ogni colpo
BOOKS = load_books()

def is_book_unlocked(b_id: str, profile: dict) -> bool:
    unlock = BOOKS.get(b_id, {}).get("unlock")
    if not unlock: return False
    progress = {
        "max_floor": profile.get("max_floor", 0),
        "total_bosses": profile.get("stats", {}).get("total_bosses", 0),
        "won_normal": 1 if profile.get("won_normal", False) else 0,
        "spells_seen": len(profile.get("codex", {}).get("spells", [])),
        "ascension": profile.get("ascension", {}).get("best_win", 0),
        "best_echo": profile.get("best_echo", 0),
    }
    return progress.get(unlock["type"], 0) >= unlock["value"]

def get_archive_bonus(stat: str, profile: dict) -> float:
    """Somma un bonus (es. "def", "gold_pct", "escape", "boss_dmg_pct", "ether_max", "spell_pct") su tutti i tomi sbloccati."""
    return sum(b.get("bonus", {}).get(stat, 0) for b_id, b in BOOKS.items() if is_book_unlocked(b_id, profile))

def unlocked_archive_bonuses(profile: dict) -> list:
    return [(b["title"], b.get("bonus_desc", "")) for b_id, b in BOOKS.items() if is_book_unlocked(b_id, profile)]

def show_archive(profile):
    books = BOOKS
    
    while True:
        clear_screen()
        prompt = f"{Colors.MAGENTA}{Colors.BOLD}--- 📜 L'ARCHIVIO DI AETHELGARD ---{Colors.RESET}\nQui sono custoditi i frammenti di storia che hai recuperato.\nLa conoscenza è potere: decifrare questi tomi ti conferisce bonus in combattimento.\n"
        
        available_books = []
        options = []

        for b_id, b_data in books.items():
            unlocked = is_book_unlocked(b_id, profile)
            buff = b_data.get("bonus_desc", "")
            
            if unlocked:
                available_books.append((b_id, b_data))
                options.append(f"{Colors.GREEN}{b_data['title']}{Colors.RESET} (Bonus: {buff})")
            else:
                prompt += f"\n{Colors.RED}?. [BLOCCATO] - {b_data['unlock_condition']}{Colors.RESET}\n   {Colors.YELLOW}↳ Ricompensa: {buff}{Colors.RESET}"
        
        options.append("Torna al Campo Base")
        idx = interactive_menu(options, prompt)
        
        if idx == len(options) - 1: break
        if 0 <= idx < len(available_books):
            read_book(available_books[idx][1])

def read_book(book):
    while True:
        clear_screen()
        prompt = f"{Colors.MAGENTA}{Colors.BOLD}--- {book['title']} ---{Colors.RESET}\n"
        
        options = [ch['title'] for ch in book['chapters']]
        options.append("Indietro")
        
        idx = interactive_menu(options, prompt)
        
        if idx == len(options) - 1: break
        if 0 <= idx < len(book['chapters']):
            clear_screen()
            ch = book['chapters'][idx]
            display_msg(f"{Colors.YELLOW}{Colors.BOLD}--- {ch['title']} ---{Colors.RESET}\n")
            delay_print(ch['text'], 0.03)
            wait_enter("\n\nPremi INVIO per tornare all'indice...")
