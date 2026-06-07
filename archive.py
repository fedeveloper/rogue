import json
import os
from ui import Colors, clear_screen, delay_print, get_choice

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
        print(f"{Colors.MAGENTA}{Colors.BOLD}--- 📜 L'ARCHIVIO DI AETHELGARD ---{Colors.RESET}")
        print("Qui sono custoditi i frammenti di storia che hai recuperato.")
        print("La conoscenza è potere: decifrare questi tomi ti conferisce bonus in combattimento.\n")
        
        available_books = []

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
                print(f"{Colors.GREEN}{len(available_books)}. {b_data['title']}{Colors.RESET}")
                print(f"   {Colors.YELLOW}↳ Bonus Attivo: {buff}{Colors.RESET}")
            else:
                print(f"{Colors.RED}?. [BLOCCATO] - {b_data['unlock_condition']}{Colors.RESET}")
                print(f"   {Colors.YELLOW}↳ Ricompensa: {buff}{Colors.RESET}")
        
        print("\n0. Torna al Campo Base")
        choice = get_choice("Seleziona un volume > ")
        
        if choice == '0': break
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(available_books):
                read_book(available_books[idx][1])
        except ValueError: pass

def read_book(book):
    while True:
        clear_screen()
        print(f"{Colors.MAGENTA}{Colors.BOLD}--- {book['title']} ---{Colors.RESET}\n")
        for i, ch in enumerate(book['chapters']):
            print(f"{i+1}. {ch['title']}")
        print("0. Indietro")
        
        choice = get_choice("Seleziona un capitolo > ")
        if choice == '0': break
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(book['chapters']):
                clear_screen()
                ch = book['chapters'][idx]
                print(f"{Colors.YELLOW}{Colors.BOLD}--- {ch['title']} ---{Colors.RESET}\n")
                delay_print(ch['text'], 0.03)
                input("\n\nPremi INVIO per tornare all'indice...")
        except ValueError: pass
