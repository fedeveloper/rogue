import json
import os
from ui import Colors, clear_screen, delay_print, get_choice

BOOKS_FILE = "data/books.json"

def load_books():
    if not os.path.exists(BOOKS_FILE): return {}
    with open(BOOKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("books", {})

def show_archive(profile):
    books = load_books()
    
    while True:
        clear_screen()
        print(f"{Colors.MAGENTA}{Colors.BOLD}--- 📜 L'ARCHIVIO DI AETHELGARD ---{Colors.RESET}")
        print("Qui sono custoditi i frammenti di storia che hai recuperato.\n")
        
        available_books = []
        # Logic to check unlock conditions based on profile/stats
        # For now, let's assume they are unlocked by floors_reached or bosses_killed
        max_floor = profile.get("stats", {}).get("max_floor", 0)
        bosses_killed = profile.get("stats", {}).get("bosses_killed", 0)
        runs_completed = profile.get("stats", {}).get("runs_completed", 0)

        for b_id, b_data in books.items():
            unlocked = False
            if b_id == "diario_silas" and max_floor >= 5: unlocked = True
            elif b_id == "bestiario" and bosses_killed >= 3: unlocked = True
            elif b_id == "cronache_ere" and runs_completed >= 1: unlocked = True
            
            if unlocked:
                available_books.append((b_id, b_data))
                print(f"{len(available_books)}. {b_data['title']}")
            else:
                print(f"{Colors.RED}?. [BLOCCATO] - {b_data['unlock_condition']}{Colors.RESET}")
        
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
