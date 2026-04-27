import random
import time
import sys
import os
import json
from typing import List, Dict, Any

# --- SETUP TERMINALE E COLORI ---
if os.name == 'nt': os.system('')

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def clear_screen(): os.system('cls' if os.name == 'nt' else 'clear')
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

# --- GESTIONE SALVATAGGIO E DATI ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_json_file(filename: str) -> Dict[str, Any]:
    filepath = os.path.join(BASE_DIR, "data", filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f: return json.load(f)
    except Exception as e:
        print(f"{Colors.RED}ERRORE FATALE:{Colors.RESET} File 'data/{filename}' mancante o corrotto. ({e})")
        input("\nPremi INVIO per uscire...")
        sys.exit(1)

def load_profile() -> Dict[str, Any]:
    filepath = os.path.join(BASE_DIR, "profile.json")
    default_profile = {
        "essence": 0, "max_floor": 0, "won_normal": False,
        "unlocked_ids":[],
        "class_xp": {}, "class_lvl": {},
        "stats": {"total_deaths": 0, "total_gold": 0},
        "completed_feats":[],
        "perks": {"hp_lvl": 0, "gold_lvl": 0, "discount_lvl": 0, "sesto_senso": False, "scarpisti": False}
    }
    
    if not os.path.exists(filepath):
        with open(filepath, 'w', encoding='utf-8') as f: json.dump(default_profile, f, indent=4)
        return default_profile
        
    with open(filepath, 'r', encoding='utf-8') as f:
        loaded = json.load(f)
        
    for key, val in default_profile.items():
        if key not in loaded:
            loaded[key] = val
        elif isinstance(val, dict):
            for sub_k, sub_v in val.items():
                if sub_k not in loaded[key]:
                    loaded[key][sub_k] = sub_v
                    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(loaded, f, indent=4)
        
    return loaded

def save_profile(profile: Dict[str, Any]):
    filepath = os.path.join(BASE_DIR, "profile.json")
    with open(filepath, 'w', encoding='utf-8') as f: json.dump(profile, f, indent=4)

# --- CARICAMENTO DI TUTTI I DATI ---
PROFILE = load_profile()
RAW_DATA = {
    "enemies": load_json_file("enemies.json")["enemies"],
    "bosses": load_json_file("enemies.json")["bosses"],
    "weapons": load_json_file("weapons.json")["weapons"],
    "armors": load_json_file("armors.json")["armors"],
    "consumables": load_json_file("consumables.json")["consumables"],
    "classes": load_json_file("classes.json"),
    "lore": load_json_file("lore.json"),
    "elements": load_json_file("elements.json"),
    "meta": load_json_file("meta.json")
}

GAME_DATA = {
    "enemies": RAW_DATA["enemies"], "bosses": RAW_DATA["bosses"], "lore": RAW_DATA["lore"], "elements": RAW_DATA["elements"], "meta": RAW_DATA["meta"],
    "weapons":[w for w in RAW_DATA["weapons"] if w.get("unlock_id") is None or w["unlock_id"] in PROFILE["unlocked_ids"]],
    "armors":[a for a in RAW_DATA["armors"] if a.get("unlock_id") is None or a["unlock_id"] in PROFILE["unlocked_ids"]],
    "consumables":[c for c in RAW_DATA["consumables"] if c.get("unlock_id") is None or c["unlock_id"] in PROFILE["unlocked_ids"]]
}

ELEMENTS = GAME_DATA["elements"]["list"]
E_ICONS = GAME_DATA["elements"]["icons"]
MULTIPLIERS = GAME_DATA["elements"]["multipliers"]

def get_element_icon(el_name: str) -> str: return f"{E_ICONS.get(el_name, '')} {el_name}"

# --- SISTEMA OGGETTI ---
class Item:
    def __init__(self, name: str, value: int, item_type: str):
        self.name, self.value, self.type = name, value, item_type 

class Weapon(Item):
    def __init__(self, name: str, value: int, atk: int, element: str = "Normale"):
        super().__init__(name, value, "weapon")
        self.atk, self.element = atk, element
        self.display_name = f"{name}[{get_element_icon(element)}]"

class Armor(Item):
    def __init__(self, name: str, value: int, defense: int, element: str = "Normale"):
        super().__init__(name, value, "armor")
        self.defense, self.element = defense, element
        self.display_name = f"{name}[{get_element_icon(element)}]"

class Consumable(Item):
    def __init__(self, name: str, value: int, heal_amount: int):
        super().__init__(name, value, "consumable")
        self.heal_amount = heal_amount
        self.display_name = name

def generate_random_element() -> str:
    if random.random() < 0.4: return "Normale"
    return random.choice([e for e in ELEMENTS if e != "Normale"])

def generate_weapon(level: int, is_epic: bool = False) -> Weapon:
    w_data = random.choice(GAME_DATA["weapons"])
    name = w_data["name"]
    atk = w_data["base_atk"] + int(level * 1.5) + random.randint(0, 3)
    element = generate_random_element()
    if element == "Normale": atk = int(atk * 1.2) + 1
    if is_epic: atk = int(atk * 1.5) + 2; name = f"EPICO {name}"
    return Weapon(f"{name} (lv.{level})", atk * 5, atk, element)

def generate_armor(level: int, is_epic: bool = False) -> Armor:
    a_data = random.choice(GAME_DATA["armors"])
    name = a_data["name"]
    defense = a_data["base_def"] + int(level * 1.2) + random.randint(0, 2)
    element = generate_random_element()
    if element == "Normale": defense = int(defense * 1.2) + 1
    if is_epic: defense = int(defense * 1.5) + 2; name = f"EPICO {name}"
    return Armor(f"{name} (lv.{level})", defense * 8, defense, element)

def generate_potion(level: int) -> Consumable:
    c_data = random.choice(GAME_DATA["consumables"])
    name, heal, val = c_data["name"], c_data["base_heal"] + (level * 5), c_data["val_base"] + (level * 5)
    return Consumable(f"{name} (Cura {heal})" if heal > 0 else name, val, heal)

# --- CLASSI E PLAYER ---
class Player:
    def __init__(self, class_id: str, trait_id: str):
        self.class_id = class_id
        data = RAW_DATA["classes"][class_id]
        
        self.role = data["role"]
        self.max_hp = data["max_hp"] + (PROFILE["perks"]["hp_lvl"] * 15)
        self.hp = self.max_hp
        self.gold = data["gold"] + (PROFILE["perks"]["gold_lvl"] * 20)
        self.base_acc, self.base_dodge = data["acc"], data["dodge"]
        
        self.exp_multiplier = 1.0
        if PROFILE["class_lvl"].get("1", 1) >= 4: self.base_dodge += 5 
        if PROFILE["class_lvl"].get("2", 1) >= 4: self.base_dodge += 10 
        if PROFILE["class_lvl"].get("3", 1) >= 4: self.exp_multiplier = 1.15 
        
        self.trait = GAME_DATA["meta"]["traits"][trait_id]
        self.cursed = False
        self.midas = False
        if trait_id == "maledetto":
            self.max_hp = self.max_hp // 2
            self.hp = self.max_hp
            self.cursed = True
        if trait_id == "midas": self.midas = True
        
        start_weapon_lv = 2 if class_id == "1" and PROFILE["class_lvl"].get("1", 1) >= 2 else 1
        self.thief_save = True if class_id == "2" and PROFILE["class_lvl"].get("2", 1) >= 2 else False
        self.mage_lifesteal = True if class_id == "3" and PROFILE["class_lvl"].get("3", 1) >= 2 else False

        self.level, self.exp, self.max_exp = 1, 0, 100
        self.escaped = False
        
        self.run_tracker = {"escapes": 0, "gold_spent": 0, "no_hit_boss_done": False, "kill_1_hp_done": False}
        self.essence_gathered, self.bosses_killed = 0, 0
        
        w_data = data["weapon"]
        self.weapon = Weapon(w_data["name"], w_data["value"], w_data["atk"] + (50 if self.cursed else 0), w_data["element"]) if start_weapon_lv == 1 else generate_weapon(2)
        a_data = data["armor"]
        self.armor = Armor(a_data["name"], a_data["value"], a_data["def"], a_data["element"])
        self.inventory =[generate_potion(1) for _ in range(data["potions"])]

    def gain_exp(self, amount: int):
        if self.midas: return
        amount = int(amount * self.exp_multiplier)
        self.exp += amount
        print(f"{Colors.CYAN}Ottieni {amount} EXP! ({self.exp}/{self.max_exp}){Colors.RESET}")
        while self.exp >= self.max_exp:
            self.exp -= self.max_exp
            self.level += 1; self.max_exp = int(self.max_exp * 1.5)
            self.max_hp += 15
            if not self.cursed: self.hp = self.max_hp
            self.base_acc += 2; self.base_dodge += 2
            print(f"\n{Colors.YELLOW}{Colors.BOLD}*** LEVEL UP! Sei salito al livello {self.level}! ***{Colors.RESET}")

    def print_stats(self):
        print(f"\n{Colors.CYAN}=== SCHEDA: {self.role.upper()} (Lv. {self.level}) ==={Colors.RESET}")
        print(f"Tratto: {self.trait['name']}")
        print(f"HP: {Colors.GREEN}{self.hp}/{self.max_hp}{Colors.RESET} | Oro: {Colors.YELLOW}{self.gold}💰{Colors.RESET} | EXP: {Colors.MAGENTA}{self.exp}/{self.max_exp}{Colors.RESET}")
        print(f"Precisione: +{self.base_acc}% | Schivata: {self.base_dodge}%")
        print(f"Arma: {self.weapon.display_name} (+{self.weapon.atk} ATK)")
        print(f"Armatura: {self.armor.display_name} (+{self.armor.defense} DEF)")
        print(f"{Colors.CYAN}============================================{Colors.RESET}")

    # Aggiunto parametro "in_combat" per gestire il costo dell'azione
    def manage_inventory(self, in_combat=False) -> str:
        while True:
            clear_screen()
            print(f"\n{Colors.MAGENTA}{Colors.BOLD}--- ZAINO E INVENTARIO ---{Colors.RESET}")
            print(f"❤️  HP: {Colors.GREEN}{self.hp}/{self.max_hp}{Colors.RESET} | 💰 Oro: {Colors.YELLOW}{self.gold}{Colors.RESET}")
            print(f"⚔️  Arma: {self.weapon.display_name} (+{self.weapon.atk} ATK)")
            print(f"🛡️  Armatura: {self.armor.display_name} (+{self.armor.defense} DEF)")
            print("-" * 55)
            
            if not self.inventory: print("L'inventario è vuoto.")
            else:
                display_items =[]
                consumables_map = {}
                for i, item in enumerate(self.inventory):
                    if item.type == "consumable":
                        if item.name not in consumables_map: consumables_map[item.name] =[]
                        consumables_map[item.name].append(i)
                    else: display_items.append((i, item, 1))
                for name, indices in consumables_map.items(): display_items.append((indices[0], self.inventory[indices[0]], len(indices)))
                display_items.sort(key=lambda x: (x[1].type, x[1].name))
                
                for disp_idx, (real_idx, item, count) in enumerate(display_items):
                    count_str = f" {Colors.YELLOW}[x{count}]{Colors.RESET}" if count > 1 else ""
                    if item.type == "weapon": print(f"{disp_idx+1}. [Arma] {item.display_name} (+{item.atk})")
                    elif item.type == "armor": print(f"{disp_idx+1}. [Armatura] {item.display_name} (+{item.defense})")
                    elif item.type == "consumable": print(f"{disp_idx+1}. [Oggetto] {item.display_name}{count_str}")
                        
            print("\n0. Chiudi Zaino")
            choice = get_choice("Scegli un oggetto da usare/equipaggiare > ")
            if choice == '0': return "closed"
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(display_items):
                    real_idx, item, count = display_items[idx]
                    
                    if item.type == "consumable":
                        if "Bomba Fumogena" in item.name:
                            self.inventory.pop(real_idx)
                            print(f"{Colors.YELLOW}Lanci la bomba fumogena! Fuga garantita.{Colors.RESET}")
                            time.sleep(1)
                            return "smoke_bomb"
                        elif "Pietra per Affilare" in item.name:
                            self.weapon.atk += 5
                            self.inventory.pop(real_idx)
                            print(f"{Colors.GREEN}Arma affilata! Ora {self.weapon.name} ha {self.weapon.atk} ATK.{Colors.RESET}")
                            input("Premi INVIO per continuare...")
                            if in_combat: return "turn_used"
                        elif "Tomo del Caos" in item.name:
                            self.weapon.element = generate_random_element()
                            self.weapon.display_name = f"{self.weapon.name.split('[')[0]}[{get_element_icon(self.weapon.element)}]"
                            self.inventory.pop(real_idx)
                            print(f"{Colors.MAGENTA}Il potere del caos avvolge l'arma! Nuovo elemento: {self.weapon.element}.{Colors.RESET}")
                            input("Premi INVIO per continuare...")
                            if in_combat: return "turn_used"
                        else:
                            if self.cursed:
                                print(f"{Colors.RED}La tua Maledizione rende inutile la pozione.{Colors.RESET}")
                                self.inventory.pop(real_idx)
                            else:
                                old_hp = self.hp
                                self.hp = min(self.max_hp, self.hp + item.heal_amount)
                                print(f"{Colors.GREEN}\n-> Recuperi {self.hp - old_hp} HP! (HP: {self.hp}/{self.max_hp}){Colors.RESET}")
                                if self.thief_save and random.random() < 0.3:
                                    print(f"{Colors.CYAN}Abilità Ladro: Hai salvato la pozione!{Colors.RESET}")
                                else:
                                    self.inventory.pop(real_idx)
                            input("Premi INVIO per continuare...")
                            if in_combat: return "turn_used"
                            
                    elif item.type == "weapon":
                        old_w, self.weapon = self.weapon, item
                        self.inventory[real_idx] = old_w
                        print(f"{Colors.GREEN}\n-> Equipaggiato: {self.weapon.display_name}!{Colors.RESET}")
                        input("Premi INVIO per continuare...")
                        if in_combat: return "turn_used"
                        
                    elif item.type == "armor":
                        old_a, self.armor = self.armor, item
                        self.inventory[real_idx] = old_a
                        print(f"{Colors.GREEN}\n-> Equipaggiato: {self.armor.display_name}!{Colors.RESET}")
                        input("Premi INVIO per continuare...")
                        if in_combat: return "turn_used"
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
        
        self.element, self.base_acc, self.base_dodge = data["element"], data["base_acc"], data["base_dodge"]
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

# --- COMBATTIMENTO E STANZE ---
def combat_room(player: Player, floor: int, is_boss: bool = False):
    delay_print(f"\n{random.choice(GAME_DATA['lore']['boss' if is_boss else 'combat'])}")
    enemy = Enemy(floor, is_boss)
    boss_tag = f"{Colors.MAGENTA} [BOSS]{Colors.RESET}" if is_boss else ""
    delay_print(f"{Colors.RED}!!! Incontri un {enemy.name.upper()}{boss_tag}[{get_element_icon(enemy.element)}] !!!{Colors.RESET}", 0.04)
    
    boss_hit_taken = False

    while enemy.hp > 0 and player.hp > 0:
        print(f"\n{Colors.BOLD}--- ⚔️ IN COMBATTIMENTO ⚔️ ---{Colors.RESET}")
        print(f"Tu: {Colors.GREEN}{player.hp}/{player.max_hp} HP{Colors.RESET} | {enemy.name}: {Colors.RED}{enemy.hp} HP{Colors.RESET}")
        print("1. Attacca")
        print("2. Difenditi (Dimezza i danni in questo turno)")
        # Testo del menu aggiornato per avvisare il giocatore
        print("3. Apri Inventario (Usa oggetto / Cambia Equip. = Costa 1 Turno)")
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
                
                if player.mage_lifesteal and multiplier > 1.0 and not player.cursed:
                    heal = max(1, dmg_dealt // 10)
                    player.hp = min(player.max_hp, player.hp + heal)
                    print(f"{Colors.MAGENTA}Assorbi {heal} HP dal nemico!{Colors.RESET}")

            else:
                print(f"\n{Colors.YELLOW}-> Fallisci! {enemy.name} schiva il colpo.{Colors.RESET}")
            
            if enemy.hp <= 0:
                print(f"\n{Colors.YELLOW}{Colors.BOLD}*** Hai sconfitto {enemy.name}! ***{Colors.RESET}")
                if player.hp == 1: player.run_tracker["kill_1_hp_done"] = True
                if is_boss and not boss_hit_taken: player.run_tracker["no_hit_boss_done"] = True
                
                g_drop = enemy.gold_drop * 3 if player.midas else enemy.gold_drop
                player.gold += g_drop
                print(f"Ottieni {Colors.YELLOW}{g_drop} oro{Colors.RESET}.")
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
            # Ora passiamo in_combat=True.
            action = player.manage_inventory(in_combat=True)
            if action == "smoke_bomb":
                player.run_tracker["escapes"] += 1
                return
            elif action == "turn_used":
                # Il giocatore ha usato un oggetto, passa al turno del nemico
                pass 
            else:
                # Il giocatore ha chiuso lo zaino con "0" senza far nulla.
                continue
                
        elif choice == '4':
            if is_boss:
                print(f"\n{Colors.RED}-> Impossibile fuggire dalla stanza di un Boss!{Colors.RESET}")
                continue
            flee_chance = max(10, min(90, 20 + player.base_dodge - enemy.base_dodge + (20 if PROFILE["perks"]["scarpisti"] else 0)))
            if random.randint(1, 100) <= flee_chance:
                print(f"\n{Colors.YELLOW}-> Sei riuscito a scappare!{Colors.RESET}")
                player.run_tracker["escapes"] += 1
                input("\nPremi INVIO per continuare...")
                return
            else: print(f"\n{Colors.RED}-> Tentativo di fuga fallito!{Colors.RESET}")
        else: continue
            
        # TURNO DEL NEMICO (viene eseguito anche se il giocatore ha restituito "turn_used")
        if enemy.hp > 0:
            en_multiplier = MULTIPLIERS.get(enemy.element, {}).get(player.armor.element, 1.0)
            en_hit_chance = max(10, min(100, 85 + enemy.base_acc - player.base_dodge + (15 if en_multiplier > 1.0 else -20 if en_multiplier < 1.0 else 0)))

            if random.randint(1, 100) <= en_hit_chance:
                dmg_taken = max(0, int((enemy.atk + random.randint(-1, 2)) * en_multiplier) - player.armor.defense)
                if is_defending: dmg_taken //= 2
                en_eff = f"{Colors.RED}[Sei vulnerabile!]{Colors.RESET}" if en_multiplier > 1.0 else f"{Colors.GREEN}[Resisti!]{Colors.RESET}" if en_multiplier < 1.0 else ""
                
                if dmg_taken > 0: 
                    boss_hit_taken = True
                    player.hp -= dmg_taken
                    dif = f"{Colors.BLUE}[DIFESA]{Colors.RESET}" if is_defending else ""
                    print(f"<- {enemy.name} ti colpisce! Subisci {Colors.RED}{dmg_taken} danni{Colors.RESET}. {en_eff}{dif}")
                else: print(f"<- {enemy.name} attacca, ma la corazza blocca TUTTO! {en_eff}")
            else: print(f"{Colors.CYAN}<- {enemy.name} attacca... ma riesci a schivarlo!{Colors.RESET}")

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
                            items_for_sale.pop(idx); time.sleep(1)
                        else: print(f"{Colors.RED}Oro insufficiente!{Colors.RESET}"); time.sleep(1)
                except ValueError: pass
        elif action == '2':
            while True:
                clear_screen()
                print(f"\n{Colors.CYAN}--- NEGOZIO (VENDI) ---{Colors.RESET}")
                if not player.inventory: print("Non hai nulla nello zaino da vendere.")
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
                        print(f"{Colors.GREEN}Hai venduto {item.name} per {gain} oro!{Colors.RESET}"); time.sleep(1)
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
            player.hp = min(player.max_hp, player.hp + player.max_hp // 2)
            print(f"{Colors.GREEN}Ti riposi profondamente!{Colors.RESET}"); input("\nPremi INVIO..."); break
        elif action == '2':
            if player.gold >= 50:
                player.gold -= 50
                player.run_tracker["gold_spent"] += 50
                player.weapon.atk += 3
                print(f"{Colors.GREEN}Riscaldi l'arma. Ora la {player.weapon.name} ha {player.weapon.atk} ATK!{Colors.RESET}"); input("\nPremi INVIO..."); break
            else: print(f"{Colors.RED}Non hai abbastanza oro.{Colors.RESET}"); time.sleep(1.5)
        elif action == '0': break

def treasure_room(player: Player, floor: int):
    delay_print(f"\n{Colors.YELLOW}{random.choice(GAME_DATA['lore']['treasure'])}{Colors.RESET}")
    gold = random.randint(30, 60) + (floor * 10)
    player.gold += gold if not player.midas else gold * 3
    print(f"{Colors.GREEN}Trovate {gold} monete d'oro nel forziere!{Colors.RESET}")
    if random.random() > 0.4:
        drop = generate_potion(floor)
        print(f"C'era anche: {Colors.CYAN}{drop.display_name}{Colors.RESET}!")
        player.inventory.append(drop)
    input("\nPremi INVIO per continuare...")

def trap_room(player: Player, floor: int):
    delay_print(f"\n{random.choice(GAME_DATA['lore']['trap'])}")
    delay_print(f"{Colors.RED}È UNA TRAPPOLA!{Colors.RESET}", 0.05)
    if random.randint(1, 100) <= player.base_dodge: print(f"{Colors.GREEN}Schivi il meccanismo! Ne esci illeso!{Colors.RESET}")
    else:
        dmg = random.randint(15, 30) + (floor * 3)
        player.hp -= dmg
        print(f"{Colors.RED}Subisci {dmg} danni puri.{Colors.RESET} (HP: {player.hp}/{player.max_hp})")
    input("\nPremi INVIO per continuare...")

def generate_floor_deck(floor: int) -> List[str]:
    deck = ["combat"] * (random.randint(3, 5) + (floor // 5))
    deck.append("vendor"); deck.append("campfire")
    if random.random() > 0.3: deck.append("treasure")
    if random.random() > 0.4: deck.append("trap")
    random.shuffle(deck); deck.append("boss")
    return deck

# --- CONTROLLO META-PROGRESSIONE (FINE RUN) ---
def evaluate_run(player: Player, floor: int):
    print("\n" + ("="*50))
    if player.hp <= 0:
        delay_print(f"{Colors.RED}S E I   M O R T O.{Colors.RESET}")
        player.essence_gathered += int(player.gold * 0.20)
        PROFILE["stats"]["total_deaths"] += 1
    elif player.escaped:
        delay_print(f"{Colors.GREEN}S E I   F U G G I T O.{Colors.RESET}")
        player.essence_gathered += player.gold
        
    player.essence_gathered += (player.bosses_killed * 50)
    PROFILE["essence"] += player.essence_gathered
    PROFILE["stats"]["total_gold"] += player.gold

    print(f"Piano raggiunto: {floor} | Boss: {player.bosses_killed}")
    print(f"Essenza Astrale accumulata: {Colors.CYAN}✨ {player.essence_gathered}{Colors.RESET}")
    
    # Maestria
    c_id = player.class_id
    xp_gained = (floor * 10) + (player.bosses_killed * 50)
    curr_xp = PROFILE["class_xp"].get(c_id, 0) + xp_gained
    curr_lvl = PROFILE["class_lvl"].get(c_id, 1)
    PROFILE["class_xp"][c_id] = curr_xp
    
    print(f"\n{Colors.MAGENTA}[ Maestria {player.role} ] +{xp_gained} XP (Totale: {curr_xp}){Colors.RESET}")
    
    reqs = GAME_DATA["meta"]["mastery_xp_requirements"]
    while curr_lvl < 5 and curr_xp >= reqs[str(curr_lvl + 1)]:
        curr_lvl += 1
        PROFILE["class_lvl"][c_id] = curr_lvl
        print(f"{Colors.YELLOW}*** MAESTRIA SALITA AL LIVELLO {curr_lvl}! ***{Colors.RESET}")
        reward = GAME_DATA["classes"][c_id]["mastery"][str(curr_lvl)]
        print(f"Sbloccato: {reward['desc']}")
        if reward["type"] == "unlock" and reward["id"] not in PROFILE["unlocked_ids"]:
            PROFILE["unlocked_ids"].append(reward["id"])
        elif reward["type"] == "class" and reward["id"] not in PROFILE["unlocked_ids"] and reward["id"] != "null":
            PROFILE["unlocked_ids"].append(reward["id"])
            
    # Imprese
    print(f"\n{Colors.CYAN}[ Aggiornamento Imprese ]{Colors.RESET}")
    feats = GAME_DATA["meta"]["feats"]
    for f_id, f_data in feats.items():
        if f_id in PROFILE["completed_feats"]: continue
        
        completed = False
        if f_id == "feat_pacifista" and player.run_tracker["escapes"] >= f_data["target"]: completed = True
        elif f_id == "feat_fabbro" and player.run_tracker["gold_spent"] >= f_data["target"]: completed = True
        elif f_id == "feat_vetro" and player.run_tracker["no_hit_boss_done"]: completed = True
        elif f_id == "feat_suicida" and player.run_tracker["kill_1_hp_done"]: completed = True
        
        if completed:
            print(f"{Colors.GREEN}Impresa Completata: {f_data['name']}!{Colors.RESET}")
            PROFILE["completed_feats"].append(f_id)
            if f_data["reward_type"] in ["unlock", "class"]:
                if f_data["reward_id"] not in PROFILE["unlocked_ids"]: PROFILE["unlocked_ids"].append(f_data["reward_id"])
            elif f_data["reward_type"] == "perk":
                PROFILE["perks"][f_data["reward_id"]] = True

    print("="*50)
    save_profile(PROFILE)
    input(f"\n{Colors.CYAN}Premi INVIO per tornare al Menu Principale...{Colors.RESET}")

# --- HUB E LOOP DI GIOCO ---
def base_camp():
    while True:
        clear_screen()
        print(f"{Colors.MAGENTA}{Colors.BOLD}=== 🏕️ IL CAMPO BASE ==={Colors.RESET}")
        print(f"Essenza: {Colors.CYAN}✨ {PROFILE['essence']}{Colors.RESET}")
        print("1. Il Fuoco dell'Anima (Potenziamenti Base)")
        print("2. La Forgia Dimensionale (Sblocca Oggetti nel Labirinto)")
        print("3. La Taverna (Recluta Eroi)")
        print("4. Grimorio e Imprese (Controlla Obiettivi e Maestrie)")
        print("0. Torna al Menu Principale")
        
        choice = get_choice("\nScegli > ")
        
        if choice == '1':
            while True:
                clear_screen()
                print(f"{Colors.CYAN}--- IL FUOCO DELL'ANIMA --- Essenza: ✨{PROFILE['essence']}{Colors.RESET}")
                hp_lvl = PROFILE["perks"]["hp_lvl"]
                g_lvl = PROFILE["perks"]["gold_lvl"]
                d_lvl = PROFILE["perks"]["discount_lvl"]
                s_senso = PROFILE["perks"]["sesto_senso"]
                
                print(f"1. Vigore Ereditario [Lv.{hp_lvl}/5] (+15 HP Max) - Costo: ✨{50 + (hp_lvl*50)}")
                print(f"2. Tasche Profonde [Lv.{g_lvl}/3] (+20 Oro Iniziale) - Costo: ✨{100 + (g_lvl*100)}")
                print(f"3. Mercanteggiare [Lv.{d_lvl}/3] (-10% Prezzi Negozio) - Costo: ✨{150 + (d_lvl*100)}")
                print(f"4. Sesto Senso[{'SBLOCCATO' if s_senso else 'BLOCCATO'}] (Prevedi la stanza) - Costo: ✨300")
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
                for cat in["weapons", "armors", "consumables"]:
                    for item in RAW_DATA[cat]:
                        if "unlock_id" in item and item["unlock_id"] not in PROFILE["unlocked_ids"]:
                            locked_items.append(item)
                
                if not locked_items:
                    print("Hai sbloccato tutto l'equipaggiamento disponibile!")
                else:
                    for i, item in enumerate(locked_items):
                        print(f"{i+1}. {item['name']} ({item.get('desc', '')}) - Costo: ✨{item['unlock_cost']}")
                print("0. Indietro")
                
                f_choice = get_choice("> ")
                if f_choice == '0': break
                try:
                    idx = int(f_choice) - 1
                    if 0 <= idx < len(locked_items):
                        item = locked_items[idx]
                        if PROFILE['essence'] >= item["unlock_cost"] and item["unlock_cost"] > 0:
                            PROFILE['essence'] -= item["unlock_cost"]
                            PROFILE["unlocked_ids"].append(item["unlock_id"])
                            save_profile(PROFILE)
                            print(f"{Colors.GREEN}Hai sbloccato {item['name']}!{Colors.RESET}")
                            for cat in["weapons", "armors", "consumables"]:
                                GAME_DATA[cat] = [x for x in RAW_DATA[cat] if x.get("unlock_id") is None or x["unlock_id"] in PROFILE["unlocked_ids"]]
                            time.sleep(2)
                        elif item["unlock_cost"] == 0:
                            print(f"{Colors.RED}Questo oggetto si ottiene solo tramite Maestrie o Imprese.{Colors.RESET}")
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
                        print(f"{i+1}. {Colors.BOLD}{c_data['role'].upper()}{Colors.RESET} ({c_data['desc']}) - Costo: ✨{c_data.get('unlock_cost', 0)}")
                print("0. Indietro")
                
                c_choice = get_choice("> ")
                if c_choice == '0': break
                try:
                    idx = int(c_choice) - 1
                    if 0 <= idx < len(locked_classes):
                        c_id, c_data = locked_classes[idx]
                        cost = c_data.get("unlock_cost", 0)
                        if PROFILE['essence'] >= cost and cost > 0:
                            PROFILE['essence'] -= cost
                            PROFILE["unlocked_ids"].append(c_data["unlock_id"])
                            save_profile(PROFILE)
                            print(f"{Colors.GREEN}Hai reclutato {c_data['role']}!{Colors.RESET}")
                            time.sleep(2)
                        elif cost == 0:
                            print(f"{Colors.RED}Questa classe si sblocca solo completando Imprese o Maestrie!{Colors.RESET}")
                            time.sleep(2)
                except ValueError: pass

        elif choice == '4':
            clear_screen()
            print(f"{Colors.CYAN}--- GRIMORIO DELLE IMPRESE ---{Colors.RESET}")
            for f_id, f_data in GAME_DATA["meta"]["feats"].items():
                status = f"{Colors.GREEN}[COMPLETATO]{Colors.RESET}" if f_id in PROFILE["completed_feats"] else f"{Colors.RED}[IN CORSO]{Colors.RESET}"
                print(f"{status} {f_data['name']}: {f_data['desc']}")
            
            print(f"\n{Colors.CYAN}--- MAESTRIA CLASSI ---{Colors.RESET}")
            for c_id, c_data in RAW_DATA["classes"].items():
                if c_data.get("unlocked_by_default") or c_data.get("unlock_id") in PROFILE["unlocked_ids"]:
                    lvl = PROFILE["class_lvl"].get(c_id, 1)
                    xp = PROFILE["class_xp"].get(c_id, 0)
                    print(f"{c_data['role']}: Lv. {lvl} (XP: {xp})")
            input("\nPremi INVIO per tornare indietro...")
        elif choice == '0': break

def play_game(infinite_mode=False):
    clear_screen()
    print(f"\n{Colors.CYAN}Scegli il tuo Eroe:{Colors.RESET}")
    avail_c = {c_id: c for c_id, c in RAW_DATA["classes"].items() if c.get("unlocked_by_default") or c.get("unlock_id") in PROFILE["unlocked_ids"]}
    for c_id, c in avail_c.items(): print(f"{c_id}. {Colors.BOLD}{c['role'].upper()}{Colors.RESET} (Lv. Maestria: {PROFILE['class_lvl'].get(c_id, 1)})")
            
    while True:
        c_choice = get_choice("Classe: ")
        if c_choice in avail_c: break
    
    print(f"\n{Colors.CYAN}Scegli un Tratto di partenza:{Colors.RESET}")
    avail_t = {}
    for t_id, t in GAME_DATA["meta"]["traits"].items():
        unlocked = True
        if t["unlock_req"] == "deaths_10" and PROFILE["stats"]["total_deaths"] < 10: unlocked = False
        if t["unlock_req"] == "gold_5000" and PROFILE["stats"]["total_gold"] < 5000: unlocked = False
        if unlocked:
            avail_t[t_id] = t
            print(f"- {t_id}: {Colors.BOLD}{t['name']}{Colors.RESET} ({t['desc']})")
            
    while True:
        t_choice = get_choice("Digita il nome breve (es. 'base'): ")
        if t_choice in avail_t: break

    player = Player(c_choice, t_choice)
    delay_print(f"\nLe porte si chiudono alle tue spalle, {player.role}.", 0.03)
    time.sleep(1)
    floor = 1
    
    while player.hp > 0 and not player.escaped:
        if not infinite_mode and floor > 30:
            clear_screen()
            print(f"{Colors.YELLOW}{Colors.BOLD}="*50); delay_print("H A I   V I N T O ! ! !"); print("="*50 + Colors.RESET)
            PROFILE["won_normal"] = True
            player.essence_gathered += 1000
            break

        clear_screen()
        delay_print(f"\n{Colors.MAGENTA}{Colors.BOLD}==== PIANO {floor} ===={Colors.RESET}", 0.05)
        room_deck = generate_floor_deck(floor)
        total_rooms = len(room_deck)
        
        for room_num, room_type in enumerate(room_deck, 1):
            if player.hp <= 0 or player.escaped: break
            while True:
                print(f"\n{Colors.CYAN}--- Piano {floor} | Porta {room_num} di {total_rooms} ---{Colors.RESET}")
                if PROFILE["perks"]["sesto_senso"]:
                    h = {"combat": "Odore di sangue...", "boss": "Un'aura terrificante...", "treasure": "Un luccichio dorato...", "trap": "Fin troppo silenzioso...", "vendor": "Profumo di incenso...", "campfire": "Odore di legna bruciata..."}
                    print(f"{Colors.BLUE}[Sesto Senso] {h.get(room_type, '')}{Colors.RESET}")
                
                print("1. Apri la porta (Procedi)")
                print("2. Apri lo Zaino / Controlla Statistiche")
                print("3. Scappa dal Labirinto (Fine Partita)")
                action = get_choice("Scegli > ")
                
                if action == '1': clear_screen(); break 
                elif action == '2': player.manage_inventory() # Nessun turno speso fuori dal combattimento
                elif action == '3':
                    clear_screen()
                    print(f"{Colors.YELLOW}Fuggi portando in salvo le ricchezze.{Colors.RESET}")
                    player.escaped = True; break
            
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
            if not player.cursed: player.hp = min(player.max_hp, player.hp + heal)
            print(f"Ti riposi brevemente. (HP: {player.hp}/{player.max_hp})")
            floor += 1
            if floor > PROFILE["max_floor"]: PROFILE["max_floor"] = floor
            input("\nPremi INVIO per scendere le scale...")

    evaluate_run(player, floor)

def main():
    while True:
        clear_screen()
        delay_print(f"{Colors.MAGENTA}{Colors.BOLD}=== IL LABIRINTO DEGLI ELEMENTI E DEL CAOS ==={Colors.RESET}", 0.01)
        print(f"\n{Colors.CYAN}[ MENU PRINCIPALE ]{Colors.RESET}")
        print("1. Inizia Run (Standard - 30 Piani)")
        print("2. Campo Base (Potenziamenti e Sblocchi)")
        if PROFILE["won_normal"]: print(f"3. {Colors.RED}Inizia Run (Modalità Infinita){Colors.RESET}")
        print("0. Esci dal gioco")
        
        choice = get_choice("\nScelta > ")
        if choice == '1': play_game(infinite_mode=False)
        elif choice == '2': base_camp()
        elif choice == '3' and PROFILE["won_normal"]: play_game(infinite_mode=True)
        elif choice == '0': clear_screen(); print("Arrivederci!"); break

if __name__ == "__main__":
    main()