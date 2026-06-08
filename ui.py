import sys
import os
import time

if os.name == 'nt': os.system('')

class Colors:
    RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, RESET, BOLD = '\033[91m', '\033[92m', '\033[93m', '\033[94m', '\033[95m', '\033[96m', '\033[0m', '\033[1m'

def clear_screen(): 
    os.system('cls' if os.name == 'nt' else 'clear')

def delay_print(text: str, delay: float = 0.02):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def get_choice(prompt: str) -> str:
    while True:
        choice = input(prompt).strip()
        if choice: return choice
        sys.stdout.write("\033[1A\r\033[2K")
        sys.stdout.flush()

def interactive_menu(options: list, prompt: str = "") -> int:
    """
    Stampa un menu navigabile con le frecce, con supporto allo scrolling per liste lunghe.
    Restituisce l'indice (0-based) dell'opzione selezionata.
    """
    import msvcrt
    import sys
    
    if prompt:
        print(prompt)
        
    selected_idx = 0
    num_options = len(options)
    MAX_VISIBLE = 15
    window_start = 0
    
    # Nasconde il cursore
    sys.stdout.write('\033[?25l')
    
    lines_printed = 0
    
    while True:
        if selected_idx < window_start:
            window_start = selected_idx
        elif selected_idx >= window_start + MAX_VISIBLE:
            window_start = selected_idx - MAX_VISIBLE + 1
            
        visible_options = options[window_start:window_start + MAX_VISIBLE]
        
        if lines_printed > 0:
            sys.stdout.write(f"\033[{lines_printed}A\r")
            
        lines_printed = 0
        for i, opt in enumerate(visible_options):
            sys.stdout.write("\033[2K")
            if window_start + i == selected_idx:
                sys.stdout.write(f"{Colors.CYAN}{Colors.BOLD}  > {opt}{Colors.RESET}\n")
            else:
                sys.stdout.write(f"    {opt}\n")
            lines_printed += 1
            
        sys.stdout.write("\033[2K")
        if num_options > MAX_VISIBLE:
            sys.stdout.write(f"{Colors.YELLOW}  -- Mostrando {window_start+1}-{window_start+len(visible_options)} di {num_options} --{Colors.RESET}\n")
        else:
            sys.stdout.write("\n")
        lines_printed += 1
        
        sys.stdout.flush()
        
        key = msvcrt.getch()
        
        if key in (b'\xe0', b'\x00'): # Frecce direzionali
            key2 = msvcrt.getch()
            if key2 == b'H': # Su
                selected_idx = (selected_idx - 1) % num_options
            elif key2 == b'P': # Giù
                selected_idx = (selected_idx + 1) % num_options
        elif key == b'\r': # Invio
            sys.stdout.write('\033[?25h') # Mostra di nuovo il cursore
            return selected_idx
