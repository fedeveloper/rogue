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

def get_choice(prompt: str) -> str:
    while True:
        choice = input(prompt).strip()
        if choice: 
            return choice
        sys.stdout.write("\033[1A\r\033[2K")
        sys.stdout.flush()

# --- GESTIONE SALVATAGGIO E DATI (ROGUELITE META-PROGRESSION) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_json_file(filename: str) -> Dict[str, Any]:
    filepath = os.path.join(BASE_DIR, "data", filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"{Colors.RED}ERRORE FATALE:{Colors.RESET} Impossibile trovare 'data/{filename}'.")
        input("\nPremi INVIO per uscire...")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"{Colors.RED}ERRORE FATALE:{Colors.RESET} Il file 'data/{filename}' è corrotto. ({e})")
        input("\nPremi INVIO per uscire...")
        sys.exit(1)

def load_profile() -> Dict[str, Any]:
    filepath = os.path.join(BASE_DIR, "profile.json")
    default_profile = {
        "essence": 0,
        "max_floor": 0,
        "won_normal": False,
        "unlocked_ids":[],
        "perks": {
            "hp_lvl": 0,       # Ogni livello: +15 HP
            "gold_lvl": 0,     # Ogni livello: +20 Oro iniziale
            "discount_lvl": 0, # Ogni livello: 10% sconto mercato
            "sesto_senso": False
        }
    }
    if not os.path.exists(filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(default_profile, f, indent=4)
        return default_profile
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_profile(profile: Dict[str, Any]):
    filepath = os.path.join(BASE_DIR, "profile.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(profile, f, indent=4)

# Caricamento Globale all'avvio
PROFILE = load_profile()
ENEMIES_JSON = load_json_file("enemies.json")
RAW_DATA = {
    "enemies": ENEMIES_JSON["enemies"],
    "bosses": ENEMIES_JSON["bosses"],
    "weapons": load_json_file("weapons.json")["weapons"],
    "armors": load_json_file("armors.json")["armors"],
    "consumables": load_json_file("consumables.json")["consumables"],
    "classes": load_json_file("classes.json"),
    "lore": load_json_file("lore.json"),
    "elements": load_json_file("elements.json")
}

# Filtra gli oggetti del Labirinto in base a ciò che hai sbloccato!
GAME_DATA = {
    "enemies": RAW_DATA["enemies"],
    "bosses": RAW_DATA["bosses"],
    "lore": RAW_DATA["lore"],
    "elements": RAW_DATA["elements"],
    "weapons":[w for w in RAW_DATA["weapons"] if w.get("unlock_id") is None or w["unlock_id"] in PROFILE["unlocked_ids"]],
    "armors":[a for a in RAW_DATA["armors"] if a.get("unlock_id") is None or a["unlock_id"] in PROFILE["unlocked_ids"]],
    "consumables":[c for c in RAW_DATA["consumables"] if c.get("unlock_id") is None or c["unlock_id"] in PROFILE["unlocked_ids"]]
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
    atk = w_data["base_atk"] + int(level * 1.5) + random.randint(0, 3)
    element = generate_random_element()
    
    if element == "Normale": atk = int(atk * 1.2) + 1
    if is_epic:
        atk = int(atk * 1.5) + 2
        name = f"EPICO {name}"
    return Weapon(f"{name} (lv.{level})", atk * 5, atk, element)

def generate_armor(level: int, is_epic: bool = False) -> Armor:
    a_data = random.choice(GAME_DATA["armors"])
    name = a_data["name"]
    defense = a_data["base_def"] + int(level * 1.2) + random.randint(0, 2)
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
    def __init__(self, class_id: str):
        data = RAW_DATA["classes"][class_id]
        
        self.role = data["role"]
        self.max_hp = data["max_hp"] + (PROFILE["perks"]["hp_lvl"] * 15) # APPLICA PERK HP
        self.hp = self.max_hp
        self.gold = data["gold"] + (PROFILE["perks"]["gold_lvl"] * 20)   # APPLICA PERK ORO
        self.base_acc = data["acc"]
        self.base_dodge = data["dodge"]
        
        self.level = 1
        self.exp = 0
        self.max_exp = 100
        self.escaped = False
        self.essence_gathered = 0
        self.bosses_killed = 0
        
        w_data = data["weapon"]
        self.weapon = Weapon(w_data["name"], w_data["value"], w_data["atk"], w_data["element"])
        a_data = data["armor"]
        self.armor = Armor(a_data["name"], a_data["value"], a_data["def"], a_data["element"])
        self.inventory =[generate_potion(1) for _ in range(data["potions"])]

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
            
            # --- MODIFICA IMPORTANTE: Scheda Eroe completa nell'inventario ---
            print(f"{Colors.CYAN}[ SCHEDA EROE & EQUIPAGGIAMENTO ]{Colors.RESET}")
            print(f"❤️  HP: {Colors.GREEN}{self.hp}/{self.max_hp}{Colors.RESET} | 💰 Oro: {Colors.YELLOW}{self.gold}{Colors.RESET} | 🌟 Livello: {self.level} ({self.exp}/{self.max_exp} EXP)")
            print(f"🎯 Precisione: +{self.base_acc}% | 💨 Schivata: {self.base_dodge}%")
            print(f"⚔️  Arma: {self.weapon.display_name} (+{self.weapon.atk} ATK)")
            print(f"🛡️  Armatura: {self.armor.display_name} (+{self.armor.defense} DEF)")
            print("-" * 55)
            
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
                    count_str = f" {Colors.YELLOW}[x{count}]{Colors.RESET}" if count > 1 else ""
                    if item.type == "weapon":
                        print(f"{disp_idx+1}. [Arma] {item.display_name} (+{item.atk}) - Val: {item.value}")
                    elif item.type == "armor":
                        print(f"{disp_idx+1}. [Armatura] {item.display_name} (+{item.defense}) - Val: {item.value}")
                    elif item.type == "consumable":
                        print(f"{disp_idx+1}. [Oggetto] {item.display_name}{count_str} - Val: {item.value}")
                        
            print("\n0. Chiudi Zaino")
            choice = get_choice("Scegli un oggetto da usare/equipaggiare > ")
            if choice == '0': break
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(display_items):
                    real_idx, item, count = display_items[idx]
                    if item.type == "consumable":
                        old_hp = self.hp
                        self.hp = min(self.max_hp, self.hp + item.heal_amount)
                        healed = self.hp - old_hp
                        print(f"{Colors.GREEN}\n-> Usi {item.name}. Recuperi {healed} HP! (HP: {self.hp}/{self.max_hp}){Colors.RESET}")
                        self.inventory.pop(real_idx)
                        input("Premi INVIO per continuare...")
                    elif item.type == "weapon":
                        old_w, self.weapon = self.weapon, item
                        self.inventory[real_idx] = old_w
                        print(f"{Colors.GREEN}\n-> Equipaggiato: {self.weapon.display_name}!{Colors.RESET}")
                        input("Premi INVIO per continuare...")
                    elif item.type == "armor":
                        old_a, self.armor = self.armor, item
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
            self.hp = data["base_hp"] + int(floor * 15) + random.randint(0, 20)
            self.atk = data["base_atk"] + int(floor * 2.5) + random.randint(0, 3)
            self.gold_drop = 50 + (floor * 20)
            self.exp_drop = 150 + (floor * 30)
        else:
            self.hp = data["base_hp"] + int(floor * 8) + random.randint(-5, 10)
            self.atk = data["base_atk"] + int(floor * 1.5) + random.randint(0, 2)
            self.gold_drop = 10 + (floor * 6) + random.randint(0, 5)
            self.exp_drop = 30 + (floor * 10)

# --- FUNZIONI STANZE ---
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
        
        if choice in['1', '2', '3', '4']: clear_screen()
            
        if choice == '1':
            multiplier = MULTIPLIERS.get(player.weapon.element, {}).get(enemy.element, 1.0)
            hit_chance = max(10, min(100, 85 + player.base_acc - enemy.base_dodge + (15 if multiplier > 1.0 else -20 if multiplier < 1.0 else 0)))

            if random.randint(1, 100) <= hit_chance:
                dmg_dealt = int(max(1, player.weapon.atk + random.randint(-1, 2)) * multiplier)
                eff = f"{Colors.GREEN}[SUPER EFFICACE!]{Colors.RESET}" if multiplier > 1.0 else f"{Colors.RED}[Poco efficace...]{Colors.RESET}" if multiplier < 1.0 else ""
                enemy.hp -= dmg_dealt
                print(f"\n-> Colpisci con {player.weapon.name} infliggendo {Colors.CYAN}{dmg_dealt} danni!{Colors.RESET} {eff}")
            else:
                print(f"\n{Colors.YELLOW}-> Fallisci! {enemy.name} schiva il colpo.{Colors.RESET}")
            
            if enemy.hp <= 0:
                print(f"\n{Colors.YELLOW}{Colors.BOLD}*** Hai sconfitto {enemy.name}! ***{Colors.RESET}")
                player.gold += enemy.gold_drop
                print(f"Ottieni {Colors.YELLOW}{enemy.gold_drop} oro{Colors.RESET}.")
                player.gain_exp(enemy.exp_drop)
                if is_boss:
                    player.bosses_killed += 1
                    drop = generate_weapon(floor + 2, True) if random.random() > 0.5 else generate_armor(floor + 2, True)
                    print(f"\n{Colors.MAGENTA}DROP LEGGENDARIO: {drop.display_name}!{Colors.RESET}")
                    player.inventory.append(drop)
                elif random.random() > 0.6:
                    drop = generate_potion(floor)
                    print(f"Tra i resti trovi: {Colors.CYAN}{drop.display_name}{Colors.RESET}!")
                    player.inventory.append(drop)
                input("\nPremi INVIO per continuare...")
                return
                
        elif choice == '2':
            is_defending = True
            print(f"\n{Colors.BLUE}-> Assumi una posizione difensiva!{Colors.RESET}")
        elif choice == '3':
            player.manage_inventory()
            continue
        elif choice == '4':
            if is_boss:
                print(f"\n{Colors.RED}-> Impossibile fuggire dalla stanza di un Boss!{Colors.RESET}")
                continue
            flee_chance = max(10, min(90, 20 + player.base_dodge - enemy.base_dodge))
            if random.randint(1, 100) <= flee_chance:
                print(f"\n{Colors.YELLOW}-> Sei riuscito a scappare!{Colors.RESET}")
                input("\nPremi INVIO per continuare...")
                return
            else:
                print(f"\n{Colors.RED}-> Tentativo di fuga fallito!{Colors.RESET}")
        else:
            continue
            
        if enemy.hp > 0:
            en_multiplier = MULTIPLIERS.get(enemy.element, {}).get(player.armor.element, 1.0)
            en_hit_chance = max(10, min(100, 85 + enemy.base_acc - player.base_dodge + (15 if en_multiplier > 1.0 else -20 if en_multiplier < 1.0 else 0)))

            if random.randint(1, 100) <= en_hit_chance:
                dmg_taken = max(0, int((enemy.atk + random.randint(-1, 2)) * en_multiplier) - player.armor.defense)
                if is_defending: dmg_taken //= 2
                en_eff = f"{Colors.RED}[Sei vulnerabile!]{Colors.RESET}" if en_multiplier > 1.0 else f"{Colors.GREEN}[Resisti!]{Colors.RESET}" if en_multiplier < 1.0 else ""
                player.hp -= dmg_taken
                
                if dmg_taken == 0:
                    print(f"<- {enemy.name} attacca, ma la corazza blocca TUTTO! {en_eff}")
                else:
                    dif = f"{Colors.BLUE}[DIFESA]{Colors.RESET}" if is_defending else ""
                    print(f"<- {enemy.name} ti colpisce! Subisci {Colors.RED}{dmg_taken} danni{Colors.RESET}. {en_eff}{dif}")
            else:
                print(f"{Colors.CYAN}<- {enemy.name} attacca... ma riesci a schivarlo!{Colors.RESET}")

def vendor_room(player: Player, floor: int):
    delay_print(f"\n{random.choice(GAME_DATA['lore']['vendor'])}")
    items_for_sale =[generate_weapon(floor + 1), generate_armor(floor + 1), generate_potion(floor), generate_potion(floor)]
    
    discount = 1.0 - (PROFILE["perks"]["discount_lvl"] * 0.10)
    for i in items_for_sale: i.value = max(1, int(i.value * discount))

    while True:
        clear_screen()
        print(f"\n{Colors.YELLOW}[ 💰 MERCANTE ] | Tuo Oro: {player.gold}{Colors.RESET}")
        if PROFILE["perks"]["discount_lvl"] > 0: print(f"{Colors.GREEN}(Hai uno sconto del {PROFILE['perks']['discount_lvl']*10}%!){Colors.RESET}")
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
                print(f"{Colors.GREEN}Riscaldi l'arma. Ora la {player.weapon.name} ha {player.weapon.atk} ATK!{Colors.RESET}")
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
        print(f"C'era anche: {Colors.CYAN}{drop.display_name}{Colors.RESET}!")
        player.inventory.append(drop)
    input("\nPremi INVIO per continuare...")

def trap_room(player: Player, floor: int):
    delay_print(f"\n{random.choice(GAME_DATA['lore']['trap'])}")
    delay_print(f"{Colors.RED}È UNA TRAPPOLA!{Colors.RESET}", 0.05)
    if random.randint(1, 100) <= player.base_dodge:
        print(f"{Colors.GREEN}Con un salto fulmineo schivi il meccanismo! Ne esci illeso!{Colors.RESET}")
    else:
        dmg = random.randint(15, 30) + (floor * 3)
        player.hp -= dmg
        print(f"{Colors.RED}Subisci {dmg} danni puri.{Colors.RESET} (HP: {player.hp}/{player.max_hp})")
    input("\nPremi INVIO per continuare...")

def generate_floor_deck(floor: int) -> List[str]:
    deck = ["combat"] * (random.randint(3, 5) + (floor // 5))
    deck.append("vendor")
    deck.append("campfire")
    if random.random() > 0.3: deck.append("treasure")
    if random.random() > 0.4: deck.append("trap")
    random.shuffle(deck) 
    deck.append("boss")
    return deck

# --- HUB PRINCIPALE E LOOP DI GIOCO ---
def base_camp():
    while True:
        clear_screen()
        print(f"{Colors.MAGENTA}{Colors.BOLD}=== 🏕️ IL CAMPO BASE ==={Colors.RESET}")
        print(f"Essenza Astrale: {Colors.CYAN}✨ {PROFILE['essence']}{Colors.RESET}")
        print("Spendi l'Essenza per ottenere potenziamenti permanenti per le run future.\n")
        print("1. Il Fuoco dell'Anima (Potenziamenti Statistiche)")
        print("2. La Forgia Dimensionale (Sblocca nuovi Oggetti nel Labirinto)")
        print("3. La Taverna (Sblocca nuove Classi)")
        print("0. Torna al Menu Principale")
        
        choice = get_choice("\nDove vuoi andare? > ")
        
        if choice == '1':
            while True:
                clear_screen()
                print(f"{Colors.CYAN}--- IL FUOCO DELL'ANIMA --- Essenza: ✨{PROFILE['essence']}{Colors.RESET}")
                hp_lvl = PROFILE["perks"]["hp_lvl"]
                g_lvl = PROFILE["perks"]["gold_lvl"]
                d_lvl = PROFILE["perks"]["discount_lvl"]
                s_senso = PROFILE["perks"]["sesto_senso"]
                
                print(f"1. Vigore Ereditario [Lv.{hp_lvl}/5] (+15 HP Max) - Costo: ✨{50 + (hp_lvl*50)}")
                print(f"2. Tasche Profonde[Lv.{g_lvl}/3] (+20 Oro Iniziale) - Costo: ✨{100 + (g_lvl*100)}")
                print(f"3. Mercanteggiare [Lv.{d_lvl}/3] (-10% Prezzi Negozio) - Costo: ✨{150 + (d_lvl*100)}")
                print(f"4. Sesto Senso[{'SBLOCCATO' if s_senso else 'BLOCCATO'}] (Prevedi la prossima stanza) - Costo: ✨300")
                print("0. Indietro")
                
                p_choice = get_choice("> ")
                if p_choice == '0': break
                
                if p_choice == '1' and hp_lvl < 5:
                    cost = 50 + (hp_lvl*50)
                    if PROFILE['essence'] >= cost:
                        PROFILE['essence'] -= cost
                        PROFILE["perks"]["hp_lvl"] += 1
                        save_profile(PROFILE)
                elif p_choice == '2' and g_lvl < 3:
                    cost = 100 + (g_lvl*100)
                    if PROFILE['essence'] >= cost:
                        PROFILE['essence'] -= cost
                        PROFILE["perks"]["gold_lvl"] += 1
                        save_profile(PROFILE)
                elif p_choice == '3' and d_lvl < 3:
                    cost = 150 + (d_lvl*100)
                    if PROFILE['essence'] >= cost:
                        PROFILE['essence'] -= cost
                        PROFILE["perks"]["discount_lvl"] += 1
                        save_profile(PROFILE)
                elif p_choice == '4' and not s_senso:
                    if PROFILE['essence'] >= 300:
                        PROFILE['essence'] -= 300
                        PROFILE["perks"]["sesto_senso"] = True
                        save_profile(PROFILE)

        elif choice == '2':
            while True:
                clear_screen()
                print(f"{Colors.CYAN}--- FORGIA DIMENSIONALE --- Essenza: ✨{PROFILE['essence']}{Colors.RESET}")
                
                locked_items =[]
                for cat in ["weapons", "armors", "consumables"]:
                    for item in RAW_DATA[cat]:
                        if "unlock_id" in item and item["unlock_id"] not in PROFILE["unlocked_ids"]:
                            locked_items.append(item)
                
                if not locked_items:
                    print("Hai sbloccato tutto l'equipaggiamento disponibile!")
                else:
                    for i, item in enumerate(locked_items):
                        print(f"{i+1}. {item['name']} ({item['desc']}) - Costo: ✨{item['unlock_cost']}")
                print("0. Indietro")
                
                f_choice = get_choice("> ")
                if f_choice == '0': break
                try:
                    idx = int(f_choice) - 1
                    if 0 <= idx < len(locked_items):
                        item = locked_items[idx]
                        if PROFILE['essence'] >= item["unlock_cost"]:
                            PROFILE['essence'] -= item["unlock_cost"]
                            PROFILE["unlocked_ids"].append(item["unlock_id"])
                            save_profile(PROFILE)
                            print(f"{Colors.GREEN}Hai sbloccato {item['name']}! Ora potrà apparire nel Labirinto.{Colors.RESET}")
                            for cat in["weapons", "armors", "consumables"]:
                                GAME_DATA[cat] = [x for x in RAW_DATA[cat] if x.get("unlock_id") is None or x["unlock_id"] in PROFILE["unlocked_ids"]]
                            time.sleep(2)
                except ValueError: pass

        elif choice == '3':
            while True:
                clear_screen()
                print(f"{Colors.CYAN}--- LA TAVERNA --- Essenza: ✨{PROFILE['essence']}{Colors.RESET}")
                locked_classes =[]
                for c_id, c_data in RAW_DATA["classes"].items():
                    if not c_data.get("unlocked_by_default") and c_data.get("unlock_id") not in PROFILE["unlocked_ids"]:
                        locked_classes.append((c_id, c_data))
                
                if not locked_classes:
                    print("Hai reclutato tutti gli eroi!")
                else:
                    for i, (c_id, c_data) in enumerate(locked_classes):
                        print(f"{i+1}. {Colors.BOLD}{c_data['role'].upper()}{Colors.RESET} ({c_data['desc']}) - Costo: ✨{c_data['unlock_cost']}")
                print("0. Indietro")
                
                c_choice = get_choice("> ")
                if c_choice == '0': break
                try:
                    idx = int(c_choice) - 1
                    if 0 <= idx < len(locked_classes):
                        c_id, c_data = locked_classes[idx]
                        if PROFILE['essence'] >= c_data["unlock_cost"]:
                            PROFILE['essence'] -= c_data["unlock_cost"]
                            PROFILE["unlocked_ids"].append(c_data["unlock_id"])
                            save_profile(PROFILE)
                            print(f"{Colors.GREEN}Hai reclutato la classe {c_data['role']}!{Colors.RESET}")
                            time.sleep(2)
                except ValueError: pass
        elif choice == '0': break

def play_game(infinite_mode=False):
    clear_screen()
    print(f"\n{Colors.CYAN}Scegli il tuo Eroe:{Colors.RESET}")
    
    available_classes = {}
    for c_id, c_data in RAW_DATA["classes"].items():
        if c_data.get("unlocked_by_default") or c_data.get("unlock_id") in PROFILE["unlocked_ids"]:
            available_classes[c_id] = c_data
            print(f"{c_id}. {Colors.BOLD}{c_data['role'].upper()}{Colors.RESET} (HP: {c_data['max_hp']})")
            
    while True:
        choice = get_choice("Scelta: ")
        if choice in available_classes:
            player = Player(choice)
            break

    delay_print(f"\nLe porte del labirinto si chiudono alle tue spalle, {player.role}.", 0.03)
    time.sleep(1)
    floor = 1
    
    while player.hp > 0 and not player.escaped:
        if not infinite_mode and floor > 30:
            clear_screen()
            print(f"{Colors.YELLOW}{Colors.BOLD}="*50)
            delay_print("H A I   V I N T O ! ! !")
            print("Hai sconfitto il Dio Antico e sei fuggito dal labirinto!")
            print("="*50 + Colors.RESET)
            PROFILE["essence"] += 1000
            PROFILE["won_normal"] = True
            save_profile(PROFILE)
            input(f"\n{Colors.CYAN}Premi INVIO per tornare al Menu...{Colors.RESET}")
            return

        clear_screen()
        delay_print(f"\n{Colors.MAGENTA}{Colors.BOLD}==== PIANO {floor} ===={Colors.RESET}", 0.05)
        room_deck = generate_floor_deck(floor)
        total_rooms = len(room_deck)
        
        for room_num, room_type in enumerate(room_deck, 1):
            if player.hp <= 0 or player.escaped: break
                
            while True:
                print(f"\n{Colors.CYAN}--- Piano {floor} | Porta {room_num} di {total_rooms} ---{Colors.RESET}")
                
                if PROFILE["perks"]["sesto_senso"]:
                    hint = {"combat": "Senti odore di sangue...", "boss": "Un'aura terrificante proviene da lì...", "treasure": "Scorgi un luccichio dorato...", "trap": "La stanza è fin troppo silenziosa...", "vendor": "Senti profumo di incenso...", "campfire": "Senti odore di legna bruciata..."}
                    print(f"{Colors.BLUE}[Sesto Senso] {hint.get(room_type, 'Ignoto')}{Colors.RESET}")
                
                print("1. Apri la porta (Procedi)")
                print("2. Apri lo Zaino / Controlla Statistiche")
                print("3. Scappa dal Labirinto (Fine Partita)")
                
                action = get_choice("Scegli > ")
                if action == '1': 
                    clear_screen()
                    break 
                elif action == '2':
                    player.manage_inventory()
                elif action == '3':
                    clear_screen()
                    print(f"{Colors.YELLOW}Hai deciso di fuggire... portando in salvo le tue ricchezze.{Colors.RESET}")
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
            if floor > PROFILE["max_floor"]:
                PROFILE["max_floor"] = floor
            input("\nPremi INVIO per scendere le scale...")

    print("\n" + ("="*50))
    if player.hp <= 0:
        delay_print(f"{Colors.RED}S E I   M O R T O.{Colors.RESET}")
        player.essence_gathered += int(player.gold * 0.20)
    elif player.escaped:
        delay_print(f"{Colors.GREEN}S E I   F U G G I T O.{Colors.RESET}")
        player.essence_gathered += player.gold
        
    player.essence_gathered += (player.bosses_killed * 50)

    print(f"Piano raggiunto: {floor}")
    print(f"Boss sconfitti: {player.bosses_killed}")
    print(f"Essenza Astrale accumulata: {Colors.CYAN}✨ {player.essence_gathered}{Colors.RESET}")
    print("="*50)
    
    PROFILE["essence"] += player.essence_gathered
    save_profile(PROFILE)
    input(f"\n{Colors.CYAN}Premi INVIO per tornare al Menu Principale...{Colors.RESET}")

def main():
    while True:
        clear_screen()
        delay_print(f"{Colors.MAGENTA}{Colors.BOLD}=== IL LABIRINTO DEGLI ELEMENTI E DEL CAOS ==={Colors.RESET}", 0.01)
        print(f"\n{Colors.CYAN}[ MENU PRINCIPALE ]{Colors.RESET}")
        print("1. Inizia Run (Standard - 30 Piani)")
        if PROFILE["won_normal"]:
            print(f"2. {Colors.RED}Inizia Run (Modalità Infinita){Colors.RESET}")
        print("3. Campo Base (Potenziamenti e Sblocchi)")
        print("0. Esci dal gioco")
        
        choice = get_choice("\nScelta > ")
        
        if choice == '1':
            play_game(infinite_mode=False)
        elif choice == '2' and PROFILE["won_normal"]:
            play_game(infinite_mode=True)
        elif choice == '3':
            base_camp()
        elif choice == '0':
            clear_screen()
            print("Arrivederci!")
            break

if __name__ == "__main__":
    main()