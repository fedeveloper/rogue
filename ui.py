import sys
import os
import re
import shutil
import time
import unicodedata

if os.name == 'nt': os.system('')

class Colors:
    RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, RESET, BOLD = '\033[91m', '\033[92m', '\033[93m', '\033[94m', '\033[95m', '\033[96m', '\033[0m', '\033[1m'

def clear_screen(): 
    os.system('cls' if os.name == 'nt' else 'clear')

TEXT_SPEED_MULTIPLIER = 1.0

def set_text_speed(multiplier: float):
    global TEXT_SPEED_MULTIPLIER
    TEXT_SPEED_MULTIPLIER = max(0.0, multiplier)

def delay_print(text: str, delay: float = 0.02):
    delay *= TEXT_SPEED_MULTIPLIER
    if delay <= 0:
        print(text)
        return
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def display_msg(text: str = ""):
    """
    Funzione centralizzata per l'output dei messaggi del gioco.
    Attualmente mappa su print(), ma potrà essere estesa per una GUI.
    """
    print(text)

def wait_enter(prompt: str = "Premi INVIO..."):
    """Attende che il giocatore prema INVIO. Punto unico per l'input di conferma (GUI, test, automazione)."""
    input(prompt)

def get_key() -> str:
    if os.name == 'nt':
        import msvcrt
        key = msvcrt.getch()
        if key in (b'\xe0', b'\x00'):
            key2 = msvcrt.getch()
            if key2 == b'H': return "UP"
            elif key2 == b'P': return "DOWN"
        elif key == b'\r': return "ENTER"
        elif key == b'\x03': raise KeyboardInterrupt
    else:
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            if ch == '\x03': raise KeyboardInterrupt
            if ch == '\x1b':
                ch2 = sys.stdin.read(2)
                if ch2 == '[A': return "UP"
                if ch2 == '[B': return "DOWN"
            elif ch == '\r' or ch == '\n': return "ENTER"
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ""

_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")

def visible_width(text: str) -> int:
    """Colonne occupate a terminale: senza codici ANSI, con emoji e caratteri larghi contati doppi."""
    plain = _ANSI_RE.sub("", text)
    width = 0
    for i, ch in enumerate(plain):
        if unicodedata.combining(ch) or ch in "\ufe0f\u200d": continue
        # Un simbolo seguito dal selettore di variante emoji (es. ❤️) viene disegnato largo
        emoji = i + 1 < len(plain) and plain[i + 1] == "\ufe0f"
        width += 2 if emoji or unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return width

def screen_rows(text: str, columns: int) -> int:
    """Righe di terminale occupate da una riga di testo che può andare a capo."""
    return max(1, -(-visible_width(text) // max(1, columns)))

def interactive_menu(options: list, prompt: str = "", cancellable: bool = False, initial: int = 0) -> int:
    """
    Stampa un menu navigabile con le frecce, con supporto allo scrolling per liste lunghe.
    Restituisce l'indice (0-based) dell'opzione selezionata. 
    Se cancellable è True, aggiunge "Indietro" alla fine e se selezionato restituisce -1.
    """
    _options = list(options)
    if cancellable:
        _options.append("Indietro")
    
    if prompt:
        print(prompt)
        
    selected_idx = initial if 0 <= initial < len(_options) else 0

    # Nasconde il cursore
    sys.stdout.write('\033[?25l')
    try:
        return _menu_loop(_options, cancellable, selected_idx)
    finally:
        sys.stdout.write('\033[?25h')  # Mostra di nuovo il cursore, anche se si esce con Ctrl+C
        sys.stdout.flush()

MAX_VISIBLE = 15

def _menu_loop(_options: list, cancellable: bool, selected_idx: int) -> int:
    num_options = len(_options)
    window_start = 0
    lines_printed = 0
    while True:
        if selected_idx < window_start:
            window_start = selected_idx
        elif selected_idx >= window_start + MAX_VISIBLE:
            window_start = selected_idx - MAX_VISIBLE + 1
            
        visible_options = _options[window_start:window_start + MAX_VISIBLE]
        
        # Torna all'inizio del menu e cancella fino a fine schermo: funziona anche
        # quando un'opzione lunga va a capo e occupa più righe del terminale
        if lines_printed > 0:
            sys.stdout.write(f"\033[{lines_printed}A\r\033[J")

        columns = shutil.get_terminal_size((80, 24)).columns
        lines_printed = 0
        for i, opt in enumerate(visible_options):
            line = f"  > {opt}" if window_start + i == selected_idx else f"    {opt}"
            if window_start + i == selected_idx:
                sys.stdout.write(f"{Colors.CYAN}{Colors.BOLD}{line}{Colors.RESET}\n")
            else:
                sys.stdout.write(f"{line}\n")
            lines_printed += screen_rows(line, columns)

        if num_options > MAX_VISIBLE:
            footer = f"  -- Mostrando {window_start+1}-{window_start+len(visible_options)} di {num_options} --"
            sys.stdout.write(f"{Colors.YELLOW}{footer}{Colors.RESET}\n")
            lines_printed += screen_rows(footer, columns)
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
            if cancellable and selected_idx == num_options - 1:
                return -1
            return selected_idx
