import json
import os
from ui import Colors, clear_screen, delay_print, interactive_menu

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOOKS_FILE = os.path.join(BASE_DIR, "data", "books.json")

def load_books():
    if not os.path.exists(BOOKS_FILE): return {}
    with open(BOOKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("books", {})

def is_book_unlocked(b_id: str, profile: dict) -> bool:
    max_floor = profile.get("max_floor", 0)
    bosses_killed = profile.get("stats", {}).get("total_bosses", 0)
    has_won = profile.get("won_normal", False)
    
    if b_id == "diario_silas" and max_floor >= 5: return True
    elif b_id == "bestiario" and bosses_killed >= 5: return True
    elif b_id == "cronache_ere" and has_won: return True
    return False

def show_archive(profile):
    books = load_books()
    
    while True:
        clear_screen()
        prompt = f"{Colors.MAGENTA}{Colors.BOLD}--- 📜 L'ARCHIVIO DI AETHELGARD ---{Colors.RESET}\nQui sono custoditi i frammenti di storia che hai recuperato.\nLa conoscenza è potere: decifrare questi tomi ti conferisce bonus in combattimento.\n"
        
        available_books = []
        options = []

        buff_desc = {
            "diario_silas": "+5% Probabilità di Fuga e +5% Oro trovato",
            "bestiario": "+10% Danni inflitti contro i Boss",
            "cronache_ere": "+5 Difesa fissa globale"
        }

        for b_id, b_data in books.items():
            unlocked = is_book_unlocked(b_id, profile)
            buff = buff_desc.get(b_id, "")
            
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
            print(f"{Colors.YELLOW}{Colors.BOLD}--- {ch['title']} ---{Colors.RESET}\n")
            delay_print(ch['text'], 0.03)
            input("\n\nPremi INVIO per tornare all'indice...")
