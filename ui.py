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

def display_msg(text: str):
    """
    Funzione centralizzata per l'output dei messaggi del gioco.
    Attualmente mappa su print(), ma potrà essere estesa per una GUI.
    """
    print(text)

def get_choice(prompt: str) -> str:
    while True:
        choice = input(prompt).strip()
        if choice: return choice
        sys.stdout.write("\033[1A\r\033[2K")
        sys.stdout.flush()

def get_key() -> str:
    if os.name == 'nt':
        import msvcrt
        key = msvcrt.getch()
        if key in (b'\xe0', b'\x00'):
            key2 = msvcrt.getch()
            if key2 == b'H': return "UP"
            elif key2 == b'P': return "DOWN"
        elif key == b'\r': return "ENTER"
    else:
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            if ch == '\x1b':
                ch2 = sys.stdin.read(2)
                if ch2 == '[A': return "UP"
                if ch2 == '[B': return "DOWN"
            elif ch == '\r' or ch == '\n': return "ENTER"
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ""

def interactive_menu(options: list, prompt: str = "", cancellable: bool = False) -> int:
    """
    Stampa un menu navigabile con le frecce, con supporto allo scrolling per liste lunghe.
    Restituisce l'indice (0-based) dell'opzione selezionata. 
    Se cancellable è True, aggiunge "Indietro" alla fine e se selezionato restituisce -1.
    """
    import sys
    
    _options = list(options)
    if cancellable:
        _options.append("Indietro")
    
    if prompt:
        print(prompt)
        
    selected_idx = 0
    num_options = len(_options)
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
            
        visible_options = _options[window_start:window_start + MAX_VISIBLE]
        
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
        
        key = get_key()
        
        if key == "UP":
            selected_idx = (selected_idx - 1) % num_options
        elif key == "DOWN":
            selected_idx = (selected_idx + 1) % num_options
        elif key == "ENTER":
            sys.stdout.write('\033[?25h') # Mostra di nuovo il cursore
            if cancellable and selected_idx == num_options - 1:
                return -1
            return selected_idx
