import random
import time
import sys
import os
import json
from typing import List, Dict, Any

# --- SETUP TERMINALE E COLORI ---
if os.name == 'nt':
    os.system('')

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def delay_print(text: str, delay: float = 0.02):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

# --- NUOVA FUNZIONE: INPUT ANTI-GLITCH ---
def get_choice(prompt: str) -> str:
    """Richiede un input al giocatore. Ignora gli invii a vuoto senza spammare il terminale."""
    while True:
        choice = input(prompt).strip()
        if choice:  # Se la stringa non è vuota, la restituisce normalmente
            return choice
        # Se l'input è vuoto, sposta il cursore in su di 1 riga (\033[1A) e cancella la riga (\033[2K)
        sys.stdout.write("\033[1A\r\033[2K")
        sys.stdout.flush()

# --- CARICAMENTO DATI (DATA-DRIVEN DESIGN) ---
def load_json_file(filename: str) -> Dict[str, Any]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(base_dir, "data", filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"{Colors.RED}ERRORE FATALE:{Colors.RESET} Impossibile trovare '{filepath}'.")
        input("\nPremi INVIO per uscire...")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"{Colors.RED}ERRORE FATALE:{Colors.RESET} Il file '{filepath}' è corrotto.")
        print(f"Dettaglio: {e}")
        input("\nPremi INVIO per uscire...")
        sys.exit(1)

# Carichiamo l'intero database di gioco nella RAM all'avvio
ENEMIES_JSON = load_json_file("enemies.json")
GAME_DATA = {
    "enemies": ENEMIES_JSON["enemies"],
    "bosses": ENEMIES_JSON["bosses"],
    "weapons": load_json_file("weapons.json")["weapons"],
    "armors": load_json_file("armors.json")["armors"],
    "consumables": load_json_file("consumables.json")["consumables"],
    "classes": load_json_file("classes.json"),
    "lore": load_json_file("lore.json"),
    "elements": load_json_file("elements.json")
}

# --- SISTEMA ELEMENTALE DINAMICO ---
ELEMENTS = GAME_DATA["elements"]["list"]
E_ICONS = GAME_DATA["elements"]["icons"]
MULTIPLIERS = GAME_DATA["elements"]["multipliers"]

def get_element_icon(el_name: str) -> str:
    return f"{E_ICONS.get(el_name, '')} {el_name}"

# --- SISTEMA OGGETTI ---
class Item:
    def __init__(self, name: str, value: int, item_type: str):
        self.name = name
        self.value = value
        self.type = item_type 

class Weapon(Item):
    def __init__(self, name: str, value: int, atk: int, element: str = "Normale"):
        super().__init__(name, value, "weapon")
        self.atk = atk
        self.element = element
        self.display_name = f"{name}[{get_element_icon(element)}]"

class Armor(Item):
    def __init__(self, name: str, value: int, defense: int, element: str = "Normale"):
        super().__init__(name, value, "armor")
        self.defense = defense
        self.element = element
        self.display_name = f"{name} [{get_element_icon(element)}]"

class Consumable(Item):
    def __init__(self, name: str, value: int, heal_amount: int):
        super().__init__(name, value, "consumable")
        self.heal_amount = heal_amount
        self.display_name = name

# --- GENERAZIONE OGGETTI ---
def generate_random_element() -> str:
    if random.random() < 0.4: return "Normale"
    return random.choice([e for e in ELEMENTS if e != "Normale"])

def generate_weapon(level: int, is_epic: bool = False) -> Weapon:
    w_data = random.choice(GAME_DATA["weapons"])
    name = w_data["name"]
    atk = w_data["base_atk"] + (level * 2) + random.randint(0, 3)
    element = generate_random_element()
    
    if element == "Normale": atk = int(atk * 1.2) + 1
    if is_epic:
        atk = int(atk * 1.5) + 2
        name = f"EPICO {name}"
        
    return Weapon(f"{name} (lv.{level})", atk * 5, atk, element)

def generate_armor(level: int, is_epic: bool = False) -> Armor:
    a_data = random.choice(GAME_DATA["armors"])
    name = a_data["name"]
    defense = a_data["base_def"] + int(level * 1.5) + random.randint(0, 2)
    element = generate_random_element()
    
    if element == "Normale": defense = int(defense * 1.2) + 1
    if is_epic:
        defense = int(defense * 1.5) + 2
        name = f"EPICO {name}"
        
    return Armor(f"{name} (lv.{level})", defense * 8, defense, element)

def generate_potion(level: int) -> Consumable:
    c_data = random.choice(GAME_DATA["consumables"])
    name = c_data["name"]
    heal = c_data["base_heal"] + (level * 5)
    val = c_data["val_base"] + (level * 5)
    return Consumable(f"{name} (Cura {heal})", val, heal)

# --- CLASSI PERSONAGGIO E NEMICI ---
class Player:
    def __init__(self, class_choice: str):
        data = GAME_DATA["classes"].get(class_choice, GAME_DATA["classes"]["1"])
        
        self.role = data["role"]
        self.max_hp = data["max_hp"]
        self.hp = self.max_hp
        self.gold = data["gold"]
        self.base_acc = data["acc"]
        self.base_dodge = data["dodge"]
        
        self.level = 1
        self.exp = 0
        self.max_exp = 100
        self.escaped = False
        
        w_data = data["weapon"]
        self.weapon = Weapon(w_data["name"], w_data["value"], w_data["atk"], w_data["element"])
        
        a_data = data["armor"]
        self.armor = Armor(a_data["name"], a_data["value"], a_data["def"], a_data["element"])
        
        self.inventory = [generate_potion(1) for _ in range(data["potions"])]

    def gain_exp(self, amount: int):
        self.exp += amount
        print(f"{Colors.CYAN}Ottieni {amount} EXP! ({self.exp}/{self.max_exp}){Colors.RESET}")
        while self.exp >= self.max_exp:
            self.exp -= self.max_exp
            self.level += 1
            self.max_exp = int(self.max_exp * 1.5)
            self.max_hp += 15
            self.hp = self.max_hp
            self.base_acc += 2
            self.base_dodge += 2
            print(f"\n{Colors.YELLOW}{Colors.BOLD}*** LEVEL UP! Sei salito al livello {self.level}! ***{Colors.RESET}")
            print(f"{Colors.GREEN}HP Massimi aumentati, precisione e schivata migliorate. Salute ripristinata!{Colors.RESET}\n")

    def print_stats(self):
        print(f"\n{Colors.CYAN}=== SCHEDA: {self.role.upper()} (Lv. {self.level}) ==={Colors.RESET}")
        print(f"HP: {Colors.GREEN}{self.hp}/{self.max_hp}{Colors.RESET} | Oro: {Colors.YELLOW}{self.gold}💰{Colors.RESET} | EXP: {Colors.MAGENTA}{self.exp}/{self.max_exp}{Colors.RESET}")
        print(f"Precisione: +{self.base_acc}% | Schivata: {self.base_dodge}%")
        print(f"Arma: {self.weapon.display_name} (+{self.weapon.atk} ATK)")
        print(f"Armatura: {self.armor.display_name} (+{self.armor.defense} DEF)")
        print(f"{Colors.CYAN}============================================{Colors.RESET}")

    def manage_inventory(self):
        while True:
            clear_screen()
            print(f"\n{Colors.MAGENTA}{Colors.BOLD}--- ZAINO E INVENTARIO ---{Colors.RESET}")
            
            print(f"{Colors.CYAN}[ EQUIPAGGIAMENTO ATTUALE ]{Colors.RESET}")
            print(f"⚔️ Arma: {self.weapon.display_name} (+{self.weapon.atk} ATK)")
            print(f"🛡️ Armatura: {self.armor.display_name} (+{self.armor.defense} DEF)")
            print("-" * 35)
            
            if not self.inventory: 
                print("L'inventario è vuoto.")
            else:
                display_items =[]
                consumables_map = {}
                for i, item in enumerate(self.inventory):
                    if item.type == "consumable":
                        if item.name not in consumables_map:
                            consumables_map[item.name] = []
                        consumables_map[item.name].append(i)
                    else:
                        display_items.append((i, item, 1))
                
                for name, indices in consumables_map.items():
                    display_items.append((indices[0], self.inventory[indices[0]], len(indices)))
                
                display_items.sort(key=lambda x: (x[1].type, x[1].name))
                
                for disp_idx, (real_idx, item, count) in enumerate(display_items):
                    count_str = f" {Colors.YELLOW}[Quantità: {count}]{Colors.RESET}" if count > 1 else ""
                    if item.type == "weapon":
                        print(f"{disp_idx+1}. [Arma] {item.display_name} (+{item.atk} ATK) - Val: {item.value}")
                    elif item.type == "armor":
                        print(f"{disp_idx+1}. [Armatura] {item.display_name} (+{item.defense} DEF) - Val: {item.value}")
                    elif item.type == "consumable":
                        print(f"{disp_idx+1}. [Oggetto] {item.display_name}{count_str} - Val: {item.value}")
                        
            print("\n0. Chiudi Zaino")
            # Usiamo la nuova funzione get_choice!
            choice = get_choice("Scegli un oggetto da usare/equipaggiare > ")
            
            if choice == '0': break
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(display_items):
                    real_idx, item, count = display_items[idx]
                    if item.type == "consumable":
                        self.hp = min(self.max_hp, self.hp + item.heal_amount)
                        print(f"{Colors.GREEN}\n-> Usi il consumabile. Recuperi {item.heal_amount} HP! (HP: {self.hp}/{self.max_hp}){Colors.RESET}")
                        self.inventory.pop(real_idx)
                        input("Premi INVIO per continuare...")
                    elif item.type == "weapon":
                        old_w = self.weapon
                        self.weapon = item
                        self.inventory[real_idx] = old_w
                        print(f"{Colors.GREEN}\n-> Equipaggiato: {self.weapon.display_name}!{Colors.RESET}")
                        input("Premi INVIO per continuare...")
                    elif item.type == "armor":
                        old_a = self.armor
                        self.armor = item
                        self.inventory[real_idx] = old_a
                        print(f"{Colors.GREEN}\n-> Equipaggiato: {self.armor.display_name}!{Colors.RESET}")
                        input("Premi INVIO per continuare...")
                else: 
                    print(f"{Colors.RED}Scelta non valida.{Colors.RESET}")
                    time.sleep(1)
            except ValueError: pass

class Enemy:
    def __init__(self, floor: int, is_boss: bool = False):
        self.is_boss = is_boss
        category = "bosses" if is_boss else "enemies"
        self.name = random.choice(list(GAME_DATA[category].keys()))
        data = GAME_DATA[category][self.name]
        
        self.element = data["element"]
        self.base_acc = data["base_acc"]
        self.base_dodge = data["base_dodge"]
        
        if is_boss:
            self.hp = data["base_hp"] + (floor * 25) + random.randint(0, 10)
            self.atk = data["base_atk"] + int(floor * 3) + random.randint(0, 2)
            self.gold_drop = 40 + (floor * 15)
            self.exp_drop = 100 + (floor * 25)
        else:
            self.hp = data["base_hp"] + (floor * 10) + random.randint(-5, 5)
            self.atk = data["base_atk"] + (floor * 2) + random.randint(0, 2)
            self.gold_drop = 8 + (floor * 5) + random.randint(0, 5)
            self.exp_drop = 20 + (floor * 10)

# --- FUNZIONI STANZE E GIOCO ---
def combat_room(player: Player, floor: int, is_boss: bool = False):
    lore_type = "boss" if is_boss else "combat"
    delay_print(f"\n{random.choice(GAME_DATA['lore'][lore_type])}")
    
    enemy = Enemy(floor, is_boss)
    boss_tag = f"{Colors.MAGENTA} [BOSS]{Colors.RESET}" if is_boss else ""
    delay_print(f"{Colors.RED}!!! Incontri un {enemy.name.upper()}{boss_tag}[{get_element_icon(enemy.element)}] !!!{Colors.RESET}", 0.04)
    
    while enemy.hp > 0 and player.hp > 0:
        print(f"\n{Colors.BOLD}--- ⚔️ IN COMBATTIMENTO ⚔️ ---{Colors.RESET}")
        print(f"Tu: {Colors.GREEN}{player.hp}/{player.max_hp} HP{Colors.RESET} | {enemy.name}: {Colors.RED}{enemy.hp} HP{Colors.RESET}")
        print("1. Attacca")
        print("2. Difenditi (Dimezza i danni in questo turno)")
        print("3. Apri Inventario")
        print("4. Tenta la Fuga")
        
        choice = get_choice("Cosa fai? > ")
        is_defending = False
        
        if choice in ['1', '2', '3', '4']:
            clear_screen()
            
        if choice == '1':
            multiplier = MULTIPLIERS.get(player.weapon.element, {}).get(enemy.element, 1.0)
            hit_chance = 85 + player.base_acc - enemy.base_dodge
            if multiplier > 1.0: hit_chance += 15
            elif multiplier < 1.0: hit_chance -= 20
            hit_chance = max(10, min(100, hit_chance))

            if random.randint(1, 100) <= hit_chance:
                base_dmg = max(1, player.weapon.atk + random.randint(-1, 2))
                dmg_dealt = int(base_dmg * multiplier)
                eff_msg = f"{Colors.GREEN}[SUPER EFFICACE!]{Colors.RESET}" if multiplier > 1.0 else f"{Colors.RED}[Poco efficace...]{Colors.RESET}" if multiplier < 1.0 else ""
                enemy.hp -= dmg_dealt
                print(f"\n-> Colpisci con {player.weapon.name} infliggendo {Colors.CYAN}{dmg_dealt} danni!{Colors.RESET} {eff_msg}")
            else:
                print(f"\n{Colors.YELLOW}-> Attacchi con {player.weapon.name}... ma fallisci! {enemy.name} schiva il colpo.{Colors.RESET}")
            
            if enemy.hp <= 0:
                print(f"\n{Colors.YELLOW}{Colors.BOLD}*** Hai sconfitto {enemy.name}! ***{Colors.RESET}")
                player.gold += enemy.gold_drop
                print(f"Ottieni {Colors.YELLOW}{enemy.gold_drop} oro{Colors.RESET}.")
                player.gain_exp(enemy.exp_drop)
                
                if is_boss:
                    drop = generate_weapon(floor + 1, True) if random.random() > 0.5 else generate_armor(floor + 1, True)
                    print(f"\n{Colors.MAGENTA}Il boss ha droppato un oggetto LEGGENDARIO: {drop.display_name}!{Colors.RESET}")
                    player.inventory.append(drop)
                elif random.random() > 0.6:
                    drop = generate_potion(floor)
                    print(f"Tra i resti trovi: {Colors.CYAN}{drop.display_name}{Colors.RESET}!")
                    player.inventory.append(drop)
                input("\nPremi INVIO per continuare...")
                return
                
        elif choice == '2':
            is_defending = True
            print(f"\n{Colors.BLUE}-> Assumi una posizione difensiva! Prevedi gli attacchi nemici e riduci i danni subiti.{Colors.RESET}")
        elif choice == '3':
            player.manage_inventory()
            continue
        elif choice == '4':
            if is_boss:
                print(f"\n{Colors.RED}-> Impossibile fuggire dalla stanza di un Boss!{Colors.RESET}")
                continue
            flee_chance = max(10, min(90, 20 + player.base_dodge - enemy.base_dodge))
            if random.randint(1, 100) <= flee_chance:
                print(f"\n{Colors.YELLOW}-> Sei riuscito a scappare lasciandoti dietro una nuvola di polvere!{Colors.RESET}")
                input("\nPremi INVIO per continuare...")
                return
            else:
                print(f"\n{Colors.RED}-> Tentativo di fuga fallito!{Colors.RESET}")
        else:
            print(f"{Colors.RED}Azione non valida!{Colors.RESET}")
            continue
            
        if enemy.hp > 0:
            en_multiplier = MULTIPLIERS.get(enemy.element, {}).get(player.armor.element, 1.0)
            en_hit_chance = 85 + enemy.base_acc - player.base_dodge
            if en_multiplier > 1.0: en_hit_chance += 15
            elif en_multiplier < 1.0: en_hit_chance -= 20
            en_hit_chance = max(10, min(100, en_hit_chance))

            if random.randint(1, 100) <= en_hit_chance:
                base_enemy_dmg = enemy.atk + random.randint(-1, 2)
                modified_atk = int(base_enemy_dmg * en_multiplier)
                dmg_taken = max(0, modified_atk - player.armor.defense)
                if is_defending: dmg_taken = dmg_taken // 2
                    
                en_eff_msg = f"{Colors.RED}[Il tuo equipaggiamento è vulnerabile!]{Colors.RESET}" if en_multiplier > 1.0 else f"{Colors.GREEN}[Resisti all'elemento!]{Colors.RESET}" if en_multiplier < 1.0 else ""
                player.hp -= dmg_taken
                
                if dmg_taken == 0:
                    print(f"<- {enemy.name} attacca, ma la tua corazza blocca TUTTO il danno! {en_eff_msg}")
                else:
                    dif_msg = f"{Colors.BLUE}[DIFESA]{Colors.RESET}" if is_defending else ""
                    print(f"<- {enemy.name} ti colpisce! Subisci {Colors.RED}{dmg_taken} danni{Colors.RESET}. {en_eff_msg}{dif_msg}")
            else:
                print(f"{Colors.CYAN}<- {enemy.name} tenta un colpo letale... ma riesci a schivarlo!{Colors.RESET}")

def vendor_room(player: Player, floor: int):
    delay_print(f"\n{random.choice(GAME_DATA['lore']['vendor'])}")
    items_for_sale =[generate_weapon(floor + 1), generate_armor(floor + 1), generate_potion(floor), generate_potion(floor)]
    while True:
        clear_screen()
        print(f"\n{Colors.YELLOW}[ 💰 MERCANTE ] | Tuo Oro: {player.gold}{Colors.RESET}")
        print("1. Guarda Merce (Compra)")
        print("2. Mostra Zaino (Vendi)")
        print("0. Saluta ed esci")
        action = get_choice("Scegli > ")
        
        if action == '1':
            while True:
                clear_screen()
                print(f"\n{Colors.CYAN}--- NEGOZIO (COMPRA) --- Tuo Oro: {player.gold}{Colors.RESET}")
                for i, item in enumerate(items_for_sale):
                    tipo = "Arma" if item.type=="weapon" else "Armatura" if item.type=="armor" else "Pozione"
                    print(f"{i+1}. [{tipo}] {item.display_name} - Prezzo: {Colors.YELLOW}{item.value} Oro{Colors.RESET}")
                print("0. Indietro")
                buy_choice = get_choice("Cosa compri? > ")
                if buy_choice == '0': break
                try:
                    idx = int(buy_choice) - 1
                    if 0 <= idx < len(items_for_sale):
                        item = items_for_sale[idx]
                        if player.gold >= item.value:
                            player.gold -= item.value
                            player.inventory.append(item)
                            print(f"{Colors.GREEN}Hai comprato {item.name}!{Colors.RESET}")
                            items_for_sale.pop(idx)
                            time.sleep(1)
                        else: 
                            print(f"{Colors.RED}Oro insufficiente!{Colors.RESET}")
                            time.sleep(1)
                except ValueError: pass
        elif action == '2':
            while True:
                clear_screen()
                print(f"\n{Colors.CYAN}--- NEGOZIO (VENDI) ---{Colors.RESET}")
                if not player.inventory: 
                    print("Non hai nulla nello zaino da vendere.")
                else:
                    for i, item in enumerate(player.inventory):
                        print(f"{i+1}. {item.display_name} - Val di vendita: {Colors.YELLOW}{max(1, item.value // 2)} Oro{Colors.RESET}")
                print("0. Indietro")
                sell_choice = get_choice("Cosa vendi? > ")
                if sell_choice == '0': break
                try:
                    idx = int(sell_choice) - 1
                    if 0 <= idx < len(player.inventory):
                        item = player.inventory.pop(idx)
                        gain = max(1, item.value // 2)
                        player.gold += gain
                        print(f"{Colors.GREEN}Hai venduto {item.name} per {gain} oro!{Colors.RESET}")
                        time.sleep(1)
                except ValueError: pass
        elif action == '0': break

def campfire_room(player: Player, floor: int):
    delay_print(f"\n{Colors.YELLOW}{random.choice(GAME_DATA['lore']['campfire'])}{Colors.RESET}")
    while True:
        clear_screen()
        print(f"\n{Colors.YELLOW}[ 🔥 FALÒ ] | Tuo Oro: {player.gold} | HP: {player.hp}/{player.max_hp}{Colors.RESET}")
        print("1. Riposa (Recupera il 50% degli HP massimi, il falò si spegnerà)")
        print(f"2. Migliora Arma (Paga {Colors.YELLOW}50 Oro{Colors.RESET} per +3 ATK, il falò si spegnerà)")
        print("0. Prosegui senza fare nulla")
        
        action = get_choice("Scegli > ")
        if action == '1':
            heal = player.max_hp // 2
            player.hp = min(player.max_hp, player.hp + heal)
            print(f"{Colors.GREEN}Ti riposi profondamente e recuperi {heal} HP!{Colors.RESET}")
            input("\nPremi INVIO per continuare...")
            break
        elif action == '2':
            if player.gold >= 50:
                player.gold -= 50
                player.weapon.atk += 3
                player.weapon.value += 20
                print(f"{Colors.GREEN}Riscaldi l'arma sulle fiamme. Ora la tua {player.weapon.name} ha {player.weapon.atk} ATK!{Colors.RESET}")
                input("\nPremi INVIO per continuare...")
                break
            else:
                print(f"{Colors.RED}Non hai abbastanza oro.{Colors.RESET}")
                time.sleep(1.5)
        elif action == '0': break

def treasure_room(player: Player, floor: int):
    delay_print(f"\n{Colors.YELLOW}{random.choice(GAME_DATA['lore']['treasure'])}{Colors.RESET}")
    gold = random.randint(30, 60) + (floor * 10)
    player.gold += gold
    print(f"{Colors.GREEN}Trovate {gold} monete d'oro nel forziere!{Colors.RESET}")
    if random.random() > 0.4:
        drop = generate_potion(floor)
        print(f"Sul fondo c'era anche: {Colors.CYAN}{drop.display_name}{Colors.RESET}!")
        player.inventory.append(drop)
    input("\nPremi INVIO per continuare...")

def trap_room(player: Player, floor: int):
    delay_print(f"\n{random.choice(GAME_DATA['lore']['trap'])}")
    delay_print(f"{Colors.RED}È UNA TRAPPOLA!{Colors.RESET}", 0.05)
    if random.randint(1, 100) <= player.base_dodge:
        print(f"{Colors.GREEN}Con un salto fulmineo riesci a schivare il meccanismo letale. Ne esci illeso!{Colors.RESET}")
    else:
        dmg = random.randint(8, 16) + (floor * 2)
        player.hp -= dmg
        print(f"{Colors.RED}Subisci {dmg} danni puri.{Colors.RESET} (HP: {player.hp}/{player.max_hp})")
    input("\nPremi INVIO per continuare...")

def generate_floor_deck(floor: int) -> List[str]:
    deck = ["combat"] * (random.randint(3, 4) + (floor // 2))
    deck.append("vendor")
    deck.append("campfire")
    if random.random() > 0.3: deck.append("treasure")
    if random.random() > 0.5: deck.append("trap")
    random.shuffle(deck) 
    deck.append("boss")
    return deck

def main():
    clear_screen()
    delay_print(f"{Colors.MAGENTA}{Colors.BOLD}=== IL LABIRINTO DEGLI ELEMENTI E DEL CAOS ==={Colors.RESET}", 0.05)
    print(f"\n{Colors.CYAN}[REGOLE DEGLI ELEMENTI]{Colors.RESET}")
    print("🔥Fuoco batte 🌪️Vento batte 🪨Terra batte 💧Acqua batte 🔥Fuoco.")
    print("✨Luce e 🌑Tenebra si distruggono a vicenda.")
    
    print("\nScegli il tuo Eroe:")
    c1 = GAME_DATA["classes"]["1"]["role"]
    c2 = GAME_DATA["classes"]["2"]["role"]
    c3 = GAME_DATA["classes"]["3"]["role"]
    print(f"1. {Colors.BOLD}{c1.upper()}{Colors.RESET} (Salute e Difesa)")
    print(f"2. {Colors.BOLD}{c2.upper()}{Colors.RESET} (Altissima schivata)")
    print(f"3. {Colors.BOLD}{c3.upper()}{Colors.RESET} (Danni enormi, vulnerabile)")
    
    while True:
        choice = get_choice("Scelta (1-3): ")
        if choice in ['1', '2', '3']:
            player = Player(choice)
            break

    delay_print(f"\nInizi come {Colors.CYAN}{player.role}{Colors.RESET}. Buona fortuna.", 0.03)
    time.sleep(1)
    floor = 1
    
    while player.hp > 0 and not player.escaped:
        clear_screen()
        delay_print(f"\n{Colors.MAGENTA}{Colors.BOLD}==== PIANO {floor} ===={Colors.RESET}", 0.05)
        room_deck = generate_floor_deck(floor)
        total_rooms = len(room_deck)
        
        for room_num, room_type in enumerate(room_deck, 1):
            if player.hp <= 0 or player.escaped: break
                
            while True:
                print(f"\n{Colors.CYAN}--- Piano {floor} | Porta {room_num} di {total_rooms} ---{Colors.RESET}")
                print("1. Apri la porta (Procedi)")
                print("2. Apri lo Zaino / Controlla Statistiche")
                print("3. Scappa dal Labirinto (Fine Partita)")
                
                action = get_choice("Scegli > ")
                if action == '1': 
                    clear_screen()
                    break 
                elif action == '2':
                    player.print_stats()
                    player.manage_inventory()
                elif action == '3':
                    clear_screen()
                    print(f"{Colors.YELLOW}Hai deciso di abbandonare il labirinto...{Colors.RESET}")
                    player.escaped = True
                    break
            
            if player.hp <= 0 or player.escaped: break
                
            if room_type == "combat": combat_room(player, floor, False)
            elif room_type == "boss": combat_room(player, floor, True)
            elif room_type == "vendor": vendor_room(player, floor)
            elif room_type == "treasure": treasure_room(player, floor)
            elif room_type == "trap": trap_room(player, floor)
            elif room_type == "campfire": campfire_room(player, floor)
        
        if player.hp > 0 and not player.escaped:
            delay_print(f"\n{Colors.YELLOW}{Colors.BOLD}*** PIANO {floor} COMPLETATO! ***{Colors.RESET}", 0.05)
            heal = 20 + (floor * 5)
            player.hp = min(player.max_hp, player.hp + heal)
            print(f"Ti riposi brevemente. Recuperi {heal} HP. (HP: {player.hp}/{player.max_hp})")
            floor += 1
            input("\nPremi INVIO per scendere le scale...")

    if player.hp <= 0:
        print("\n" + Colors.RED + "="*50)
        delay_print("S E I   M O R T O.")
        print(f"Piano raggiunto: {floor} | Livello Eroe: {player.level}")
        print("="*50 + Colors.RESET)
    elif player.escaped:
        print("\n" + Colors.GREEN + "="*50)
        delay_print("S E I   F U G G I T O.")
        print(f"Piano raggiunto: {floor} | Oro guadagnato: {player.gold}💰")
        print("="*50 + Colors.RESET)
        
    input(f"\n{Colors.CYAN}Premi INVIO per uscire dal gioco...{Colors.RESET}")

if __name__ == "__main__":
    main()