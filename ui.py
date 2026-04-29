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
