import random
import time
import sys
import os
import json
import traceback
from typing import List, Dict, Any

# --- SETUP TERMINALE E COLORI ---
if os.name == 'nt': os.system('')

class Colors:
    RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, RESET, BOLD = '\033[91m', '\033[92m', '\033[93m', '\033[94m', '\033[95m', '\033[96m', '\033[0m', '\033[1m'

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
        sys.exit(1)

def load_profile() -> Dict[str, Any]:
    filepath = os.path.join(BASE_DIR, "profile.json")
    default_profile = {
        "essence": 0, "max_floor": 0, "won_normal": False,
        "unlocked_ids":[], "class_xp": {}, "class_lvl": {},
        "stats": {"total_deaths": 0, "total_gold": 0}, "completed_feats":[],
        "perks": {"hp_lvl": 0, "gold_lvl": 0, "discount_lvl": 0, "sesto_senso": False, "scarpisti": False}
    }
    if not os.path.exists(filepath):
        with open(filepath, 'w', encoding='utf-8') as f: json.dump(default_profile, f, indent=4)
        return default_profile
    with open(filepath, 'r', encoding='utf-8') as f: loaded = json.load(f)
    for key, val in default_profile.items():
        if key not in loaded: loaded[key] = val
        elif isinstance(val, dict):
            for sub_k, sub_v in val.items():
                if sub_k not in loaded[key]: loaded[key][sub_k] = sub_v
    with open(filepath, 'w', encoding='utf-8') as f: json.dump(loaded, f, indent=4)
    return loaded

def save_profile(profile: Dict[str, Any]):
    filepath = os.path.join(BASE_DIR, "profile.json")
    with open(filepath, 'w', encoding='utf-8') as f: json.dump(profile, f, indent=4)

# --- CARICAMENTO DI TUTTI I DATI ---
PROFILE = load_profile()
RAW_DATA = {
    "enemies": load_json_file("enemies.json")["enemies"], "bosses": load_json_file("enemies.json")["bosses"],
    "weapons": load_json_file("weapons.json")["weapons"], "armors": load_json_file("armors.json")["armors"],
    "consumables": load_json_file("consumables.json")["consumables"], "classes": load_json_file("classes.json"),
    "lore": load_json_file("lore.json"), "elements": load_json_file("elements.json"),
    "meta": load_json_file("meta.json"), "events": load_json_file("events.json"), "relics": load_json_file("relics.json")["relics"]
}

GAME_DATA = {
    "enemies": RAW_DATA["enemies"], "bosses": RAW_DATA["bosses"], "lore": RAW_DATA["lore"], "elements": RAW_DATA["elements"],
    "meta": RAW_DATA["meta"], "events": RAW_DATA["events"], "relics": RAW_DATA["relics"], "classes": RAW_DATA["classes"],
    "weapons":[w for w in RAW_DATA["weapons"] if w.get("unlock_id") is None or w["unlock_id"] in PROFILE["unlocked_ids"]],
    "armors":[a for a in RAW_DATA["armors"] if a.get("unlock_id") is None or a["unlock_id"] in PROFILE["unlocked_ids"]],
    "consumables":[c for c in RAW_DATA["consumables"] if c.get("unlock_id") is None or c["unlock_id"] in PROFILE["unlocked_ids"]]
}

ELEMENTS = GAME_DATA["elements"]["list"]
E_ICONS = GAME_DATA["elements"]["icons"]
MULTIPLIERS = GAME_DATA["elements"]["multipliers"]

def get_element_icon(el_name: str) -> str: return f"{E_ICONS.get(el_name, '')} {el_name}"

# --- SISTEMA OGGETTI E RELIQUIE ---
class Item:
    def __init__(self, name: str, value: int, item_type: str, level: int = 1):
        self.name, self.value, self.type, self.level = name, value, item_type, level

class Weapon(Item):
    def __init__(self, name: str, value: int, atk: int, element: str, level: int):
        super().__init__(name, value, "weapon", level)
        self.atk, self.element = atk, element
        self.display_name = f"{name}[{get_element_icon(element)}]"

class Armor(Item):
    def __init__(self, name: str, value: int, defense: int, element: str, level: int):
        super().__init__(name, value, "armor", level)
        self.defense, self.element = defense, element
        self.display_name = f"{name}[{get_element_icon(element)}]"

class Consumable(Item):
    def __init__(self, name: str, value: int, heal_amount: int):
        super().__init__(name, value, "consumable", 1)
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
    return Weapon(f"{name} (lv.{level})", atk * 5, atk, element, level)

def generate_armor(level: int, is_epic: bool = False) -> Armor:
    a_data = random.choice(GAME_DATA["armors"])
    name = a_data["name"]
    defense = a_data["base_def"] + int(level * 1.2) + random.randint(0, 2)
    element = generate_random_element()
    if element == "Normale": defense = int(defense * 1.2) + 1
    if is_epic: defense = int(defense * 1.5) + 2; name = f"EPICO {name}"
    return Armor(f"{name} (lv.{level})", defense * 8, defense, element, level)

def generate_potion(level: int) -> Consumable:
    c_data = random.choice(GAME_DATA["consumables"])
    name, heal, val = c_data["name"], c_data["base_heal"] + (level * 5), c_data["val_base"] + (level * 5)
    return Consumable(f"{name} (Cura {heal})" if heal > 0 else name, val, heal)

def get_random_relic(player):
    avail = [r for r in GAME_DATA["relics"] if r["id"] not in player.relic_ids]
    if not avail: return None
    return random.choice(avail)

# --- CLASSI E PLAYER ---
class Player:
    def __init__(self, class_id: str, trait_id: str, active_pacts: List[str]):
        self.class_id = class_id
        data = RAW_DATA["classes"][class_id]
        
        self.role = data["role"]
        self.max_hp = data["max_hp"] + (PROFILE["perks"]["hp_lvl"] * 15)
        self.hp = self.max_hp
        self.gold = data["gold"] + (PROFILE["perks"]["gold_lvl"] * 20)
        self.base_acc, self.base_dodge = data["acc"], data["dodge"]
        self.active_pacts = active_pacts
        self.relic_ids = []
        self.relics =[]
        self.bonus_atk_relic = 0
        
        self.exp_multiplier = 1.0
        if PROFILE["class_lvl"].get("1", 1) >= 4: self.base_dodge += 5 
        if PROFILE["class_lvl"].get("2", 1) >= 4: self.base_dodge += 10 
        if PROFILE["class_lvl"].get("3", 1) >= 4: self.exp_multiplier = 1.15 
        
        self.trait = GAME_DATA["meta"]["traits"][trait_id]
        self.cursed, self.midas = False, False
        if trait_id == "maledetto":
            self.max_hp //= 2; self.hp = self.max_hp; self.cursed = True
        if trait_id == "midas": self.midas = True
        
        start_weapon_lv = 2 if class_id == "1" and PROFILE["class_lvl"].get("1", 1) >= 2 else 1
        self.thief_save = True if class_id == "2" and PROFILE["class_lvl"].get("2", 1) >= 2 else False
        self.mage_lifesteal = True if class_id == "3" and PROFILE["class_lvl"].get("3", 1) >= 2 else False

        self.level, self.exp, self.max_exp = 1, 0, 100
        self.escaped = False
        self.run_tracker = {"escapes": 0, "fusions": 0, "no_hit_boss_done": False, "kill_1_hp_done": False}
        self.essence_gathered, self.bosses_killed = 0, 0
        
        w_data = data["weapon"]
        self.weapon = Weapon(w_data["name"], w_data["value"], w_data["atk"] + (50 if self.cursed else 0), w_data.get("element", "Normale"), 1) if start_weapon_lv == 1 else generate_weapon(2)
        a_data = data["armor"]
        self.armor = Armor(a_data["name"], a_data["value"], a_data["def"], a_data.get("element", "Normale"), 1)
        self.inventory =[generate_potion(1) for _ in range(data["potions"])]

    def add_relic(self, relic):
        self.relics.append(relic)
        self.relic_ids.append(relic["id"])
        print(f"\n{Colors.MAGENTA}🌟 Hai ottenuto la Reliquia: {relic['name']}!{Colors.RESET}")
        print(f"Effetto: {relic['desc']}")
        if relic["id"] == "idolo_guerra": self.bonus_atk_relic += 5
        elif relic["id"] == "lama_sangue": self.bonus_atk_relic += 10
        elif relic["id"] == "mantello_nebbioso": self.base_dodge += 15
        elif relic["id"] == "occhio_cacciatore": self.base_acc += 20

    def get_total_atk(self): return self.weapon.atk + self.bonus_atk_relic
    
    def get_dodge(self): return 0 if "idolo_avidita" in self.relic_ids else self.base_dodge

    def gain_exp(self, amount: int):
        if self.midas: return
        multi = self.exp_multiplier + (0.3 if "tomo_conoscenza" in self.relic_ids else 0.0)
        amount = int(amount * multi)
        self.exp += amount
        print(f"{Colors.CYAN}Ottieni {amount} EXP! ({self.exp}/{self.max_exp}){Colors.RESET}")
        while self.exp >= self.max_exp:
            self.exp -= self.max_exp
            self.level += 1; self.max_exp = int(self.max_exp * 1.5)
            self.max_hp += 15
            if not self.cursed: self.hp = self.max_hp
            self.base_acc += 2; self.base_dodge += 2
            print(f"\n{Colors.YELLOW}{Colors.BOLD}*** LEVEL UP! Sei salito al livello {self.level}! ***{Colors.RESET}")

    def manage_inventory(self, in_combat=False) -> str:
        while True:
            clear_screen()
            print(f"\n{Colors.MAGENTA}{Colors.BOLD}--- ZAINO E INVENTARIO ---{Colors.RESET}")
            print(f"❤️  HP: {Colors.GREEN}{self.hp}/{self.max_hp}{Colors.RESET} | 💰 Oro: {Colors.YELLOW}{self.gold}{Colors.RESET}")
            print(f"⚔️  Arma: {self.weapon.display_name} (+{self.get_total_atk()} ATK)")
            print(f"🛡️  Armatura: {self.armor.display_name} (+{self.armor.defense} DEF)")
            if self.relics:
                print(f"🌟 Reliquie attive:")
                for r in self.relics: print(f"   - {Colors.YELLOW}{r['name']}{Colors.RESET}: {r['desc']}")
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
                    if item.type == "weapon": print(f"{disp_idx+1}. [Arma] {item.display_name} (+{item.atk}) - Lv.{item.level}")
                    elif item.type == "armor": print(f"{disp_idx+1}. [Armatura] {item.display_name} (+{item.defense}) - Lv.{item.level}")
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
                            time.sleep(1); return "smoke_bomb"
                        elif "Pietra per Affilare" in item.name:
                            self.weapon.atk += 5; self.inventory.pop(real_idx)
                            print(f"{Colors.GREEN}Arma affilata! Ora {self.weapon.name} ha {self.weapon.atk} ATK.{Colors.RESET}")
                            input("Premi INVIO..."); return "turn_used" if in_combat else "used"
                        elif "Tomo del Caos" in item.name:
                            self.weapon.element = generate_random_element()
                            self.weapon.display_name = f"{self.weapon.name.split('[')[0]}[{get_element_icon(self.weapon.element)}]"
                            self.inventory.pop(real_idx)
                            print(f"{Colors.MAGENTA}Il caos avvolge l'arma! Nuovo elemento: {self.weapon.element}.{Colors.RESET}")
                            input("Premi INVIO..."); return "turn_used" if in_combat else "used"
                        else:
                            if self.cursed:
                                print(f"{Colors.RED}La tua Maledizione rende inutile la pozione.{Colors.RESET}")
                                self.inventory.pop(real_idx)
                            else:
                                old_hp = self.hp
                                base_h = item.heal_amount
                                if "calice_alchimista" in self.relic_ids: base_h = int(base_h * 1.5)
                                h_amt = base_h // 2 if "carestia" in self.active_pacts else base_h
                                
                                self.hp = min(self.max_hp, self.hp + h_amt)
                                print(f"{Colors.GREEN}\n-> Recuperi {self.hp - old_hp} HP! (HP: {self.hp}/{self.max_hp}){Colors.RESET}")
                                if self.thief_save and random.random() < 0.3: print(f"{Colors.CYAN}Abilità Ladro: Hai salvato la pozione!{Colors.RESET}")
                                else: self.inventory.pop(real_idx)
                            input("Premi INVIO..."); return "turn_used" if in_combat else "used"
                            
                    elif item.type == "weapon":
                        old_w, self.weapon = self.weapon, item
                        self.inventory[real_idx] = old_w
                        print(f"{Colors.GREEN}\n-> Equipaggiato: {self.weapon.display_name}!{Colors.RESET}")
                        input("Premi INVIO..."); return "turn_used" if in_combat else "used"
                    elif item.type == "armor":
                        old_a, self.armor = self.armor, item
                        self.inventory[real_idx] = old_a
                        print(f"{Colors.GREEN}\n-> Equipaggiato: {self.armor.display_name}!{Colors.RESET}")
                        input("Premi INVIO..."); return "turn_used" if in_combat else "used"
                else: 
                    print(f"{Colors.RED}Scelta non valida.{Colors.RESET}")
                    time.sleep(1)
            except ValueError: pass

class Enemy:
    def __init__(self, floor: int, is_boss: bool, active_pacts: List[str], modifier: str = "normal"):
        self.is_boss = is_boss
        self.modifier = modifier
        category = "bosses" if is_boss else "enemies"
        self.name = random.choice(list(GAME_DATA[category].keys()))
        data = GAME_DATA[category][self.name]
        
        self.element, self.base_acc, self.base_dodge = data["element"], data["base_acc"], data["base_dodge"]
        
        lvl_scale = floor - 1
        if is_boss:
            self.hp = data["base_hp"] + int(lvl_scale * 8) + random.randint(0, 10)
            self.atk = data["base_atk"] + int(lvl_scale * 1.5) + random.randint(0, 2)
            self.gold_drop, self.exp_drop = 50 + (floor * 15), 150 + (floor * 20)
        else:
            self.hp = data["base_hp"] + int(lvl_scale * 5) + random.randint(-5, 5)
            self.atk = data["base_atk"] + int(lvl_scale * 1.0) + random.randint(0, 1)
            self.gold_drop, self.exp_drop = 10 + (floor * 5), 30 + (floor * 10)
            
        if self.modifier == "hard":
            self.hp = int(self.hp * 1.4)
            self.atk = int(self.atk * 1.4)
            self.name += f"{Colors.MAGENTA} (Potenziato){Colors.RESET}"
        elif self.modifier == "easy":
            self.hp = int(self.hp * 0.6)
            self.atk = int(self.atk * 0.6)
            self.name += f"{Colors.CYAN} (Debilitato){Colors.RESET}"
            
        if "durezza" in active_pacts: self.hp = int(self.hp * 1.3)
        if "furia" in active_pacts: self.atk = int(self.atk * 1.3)

# --- STANZE E COMBATTIMENTO ---
def combat_room(player: Player, floor: int, enemy_instance: Enemy):
    if enemy_instance.modifier == "normal":
        delay_print(f"\n{random.choice(GAME_DATA['lore']['boss' if enemy_instance.is_boss else 'combat'])}")
        boss_tag = f"{Colors.MAGENTA} [BOSS]{Colors.RESET}" if enemy_instance.is_boss else ""
        delay_print(f"{Colors.RED}!!! Incontri un {enemy_instance.name.upper()}{boss_tag} [{get_element_icon(enemy_instance.element)}] !!!{Colors.RESET}", 0.04)
    
    boss_hit_taken = False
    shield_active = "scudo_cristallo" in player.relic_ids
    focused_attack = False

    def on_enemy_death():
        print(f"\n{Colors.YELLOW}{Colors.BOLD}*** Hai sconfitto {enemy_instance.name}! ***{Colors.RESET}")
        if player.hp == 1: player.run_tracker["kill_1_hp_done"] = True
        if enemy_instance.is_boss and not boss_hit_taken: player.run_tracker["no_hit_boss_done"] = True
        
        g_drop = enemy_instance.gold_drop * 3 if player.midas else enemy_instance.gold_drop
        if "tasca_dorata" in player.relic_ids: g_drop = int(g_drop * 1.25)
        if "idolo_avidita" in player.relic_ids: g_drop *= 2
        
        player.gold += g_drop
        print(f"Ottieni {Colors.YELLOW}{g_drop} oro{Colors.RESET}.")
        player.gain_exp(enemy_instance.exp_drop)
        
        if "cuore_troll" in player.relic_ids:
            player.max_hp += 2; player.hp += 2
            print(f"{Colors.GREEN}Il Cuore di Troll pulsa: +2 HP Massimi!{Colors.RESET}")
        
        if enemy_instance.is_boss:
            player.bosses_killed += 1
            relic = get_random_relic(player)
            if relic: player.add_relic(relic)
            else:
                drop = generate_weapon(floor + 2, True) if random.random() > 0.5 else generate_armor(floor + 2, True)
                print(f"\n{Colors.MAGENTA}DROP LEGGENDARIO: {drop.display_name}!{Colors.RESET}")
                player.inventory.append(drop)
        elif enemy_instance.modifier == "hard":
            drop = generate_weapon(floor, False) if random.random() > 0.5 else generate_armor(floor, False)
            print(f"\n{Colors.MAGENTA}Il nemico lascia cadere: {drop.display_name}!{Colors.RESET}")
            player.inventory.append(drop)
        elif enemy_instance.modifier == "easy":
            print(f"\n{Colors.CYAN}Il nemico era troppo debole e non aveva nulla con sé.{Colors.RESET}")
        elif random.random() > 0.6:
            drop = generate_potion(floor)
            print(f"Trovi: {Colors.CYAN}{drop.display_name}{Colors.RESET}!")
            player.inventory.append(drop)
        input("\nPremi INVIO per continuare...")

    while enemy_instance.hp > 0 and player.hp > 0:
        
        if player.role in["Guerriero", "Berserker"]:
            def_type, def_txt = "counter", "Difesa Aggressiva (Dimezza danni e Contrattacca)"
        elif player.role == "Ladro":
            def_type, def_txt = "focus", "Concentrazione (Dimezza danni, prossimo colpo Critico 100%)"
        else:
            def_type, def_txt = "recovery", "Riparo Magico (Dimezza danni e Cura 5% HP)"

        print(f"\n{Colors.BOLD}--- ⚔️ IN COMBATTIMENTO ⚔️ ---{Colors.RESET}")
        print(f"Tu: {Colors.GREEN}{player.hp}/{player.max_hp} HP{Colors.RESET} | {enemy_instance.name}: {Colors.RED}{enemy_instance.hp} HP{Colors.RESET}")
        print("1. Attacca")
        print(f"2. {def_txt}")
        print("3. Apri Inventario (Usa oggetto = Costa Turno)")
        print("4. Tenta la Fuga")
        
        choice = get_choice("Cosa fai? > ")
        is_defending = False
        
        if choice in['1', '2', '3', '4']: clear_screen()
            
        if choice == '1':
            if "lama_sangue" in player.relic_ids:
                player.hp -= 3
                print(f"{Colors.RED}La Lama di Sangue si nutre di te! Subisci 3 danni.{Colors.RESET}")
                if player.hp <= 0:
                    print(f"\n{Colors.RED}{Colors.BOLD}Sei stato consumato dalla tua stessa arma...{Colors.RESET}"); input("\nPremi INVIO per continuare..."); return
            
            multiplier = MULTIPLIERS.get(player.weapon.element, {}).get(enemy_instance.element, 1.0)
            if "lente_prismatica" in player.relic_ids:
                if multiplier > 1.0: multiplier = 2.0
                elif multiplier < 1.0: multiplier = 0.5
            
            if focused_attack:
                hit_chance = 100
                dmg_dealt = int(max(1, player.get_total_atk() + random.randint(-1, 2)) * multiplier * 2)
                eff = f"{Colors.GREEN}[CRITICO!]{Colors.RESET} " + (f"{Colors.GREEN}[SUPER EFFICACE!]{Colors.RESET}" if multiplier > 1.0 else "")
                focused_attack = False
            else:
                hit_chance = max(10, min(100, 85 + player.base_acc - enemy_instance.base_dodge + (15 if multiplier > 1.0 else -20 if multiplier < 1.0 else 0)))
                dmg_dealt = int(max(1, player.get_total_atk() + random.randint(-1, 2)) * multiplier)
                eff = f"{Colors.GREEN}[SUPER EFFICACE!]{Colors.RESET}" if multiplier > 1.0 else f"{Colors.RED}[Poco efficace...]{Colors.RESET}" if multiplier < 1.0 else ""

            if random.randint(1, 100) <= hit_chance:
                enemy_instance.hp -= dmg_dealt
                print(f"\n-> Colpisci con {player.weapon.name} infliggendo {Colors.CYAN}{dmg_dealt} danni!{Colors.RESET} {eff}")
                
                if not player.cursed:
                    if player.mage_lifesteal and multiplier > 1.0:
                        h = max(1, dmg_dealt // 10); player.hp = min(player.max_hp, player.hp + h); print(f"{Colors.MAGENTA}Sintonia: Assorbi {h} HP!{Colors.RESET}")
                    if "artiglio_vampiro" in player.relic_ids:
                        player.hp = min(player.max_hp, player.hp + 5); print(f"{Colors.RED}Artiglio Vampirico ti cura 5 HP!{Colors.RESET}")
            else: 
                print(f"\n{Colors.YELLOW}-> Fallisci! {enemy_instance.name} schiva.{Colors.RESET}")
            
            if enemy_instance.hp <= 0:
                on_enemy_death()
                return
                
        elif choice == '2':
            is_defending = True
            if def_type == "counter": print(f"\n{Colors.BLUE}-> Sollevi la guardia, pronto a sfruttare l'attacco nemico!{Colors.RESET}")
            elif def_type == "focus": focused_attack = True; print(f"\n{Colors.BLUE}-> Studi il nemico nell'ombra. Il tuo prossimo attacco sarà devastante!{Colors.RESET}")
            elif def_type == "recovery":
                if player.cursed: print(f"\n{Colors.BLUE}-> Ti difendi, ma la Maledizione blocca il tuo recupero magico.{Colors.RESET}")
                else:
                    heal_amt = max(1, player.max_hp // 20); player.hp = min(player.max_hp, player.hp + heal_amt)
                    print(f"\n{Colors.BLUE}-> Evochi una barriera vitale. {Colors.GREEN}Recuperi {heal_amt} HP!{Colors.RESET}")
                    
        elif choice == '3':
            action = player.manage_inventory(in_combat=True)
            if action == "smoke_bomb": player.run_tracker["escapes"] += 1; return
            elif action == "turn_used": pass 
            else: continue
            
        elif choice == '4':
            if enemy_instance.is_boss: print(f"\n{Colors.RED}-> Impossibile fuggire dai Boss!{Colors.RESET}"); continue
            
            if "bussola_perfetta" in player.relic_ids: f_chance = 100
            else: f_chance = max(10, min(90, 20 + player.get_dodge() - enemy_instance.base_dodge + (20 if PROFILE["perks"]["scarpisti"] else 0)))
                
            if random.randint(1, 100) <= f_chance:
                print(f"\n{Colors.YELLOW}-> Sei riuscito a scappare!{Colors.RESET}"); player.run_tracker["escapes"] += 1; input("\nPremi INVIO..."); return
            else: print(f"\n{Colors.RED}-> Tentativo di fuga fallito!{Colors.RESET}")
        else: continue
            
        # TURNO NEMICO
        if enemy_instance.hp > 0:
            en_multiplier = MULTIPLIERS.get(enemy_instance.element, {}).get(player.armor.element, 1.0)
            if "lente_prismatica" in player.relic_ids:
                if en_multiplier > 1.0: en_multiplier = 2.0
                elif en_multiplier < 1.0: en_multiplier = 0.5
            
            en_hit_chance = max(10, min(100, 85 + enemy_instance.base_acc - player.get_dodge() + (15 if en_multiplier > 1.0 else -20 if en_multiplier < 1.0 else 0)))

            if random.randint(1, 100) <= en_hit_chance:
                dmg_taken = max(0, int((enemy_instance.atk + random.randint(-1, 2)) * en_multiplier) - player.armor.defense)
                if is_defending: dmg_taken //= 2
                
                if dmg_taken > 0 and shield_active:
                    print(f"{Colors.CYAN}<- {enemy_instance.name} ti colpisce... Ma lo Scudo di Cristallo assorbe il danno!{Colors.RESET}")
                    shield_active = False; dmg_taken = 0
                
                en_eff = f"{Colors.RED}[Sei vulnerabile!]{Colors.RESET}" if en_multiplier > 1.0 else f"{Colors.GREEN}[Resisti!]{Colors.RESET}" if en_multiplier < 1.0 else ""
                
                if dmg_taken > 0: 
                    boss_hit_taken = True
                    player.hp -= dmg_taken
                    dif = f"{Colors.BLUE}[DIFESA]{Colors.RESET}" if is_defending else ""
                    print(f"<- {enemy_instance.name} ti colpisce! Subisci {Colors.RED}{dmg_taken} danni{Colors.RESET}. {en_eff}{dif}")
                    
                    if is_defending and def_type == "counter":
                        enemy_instance.hp -= dmg_taken
                        print(f"{Colors.YELLOW}   ⚔️ CONTRATTACCO! Restituisci {dmg_taken} danni a {enemy_instance.name}!{Colors.RESET}")
                        if enemy_instance.hp <= 0:
                            on_enemy_death()
                            return
                    
                    if player.hp <= 0:
                        print(f"\n{Colors.RED}{Colors.BOLD}Sei caduto in battaglia contro {enemy_instance.name}...{Colors.RESET}")
                        input("\nPremi INVIO per continuare...")
                        return
                elif not shield_active and dmg_taken == 0:
                    print(f"<- {enemy_instance.name} attacca, ma la corazza blocca TUTTO! {en_eff}")
            else: print(f"{Colors.CYAN}<- {enemy_instance.name} attacca... ma riesci a schivarlo!{Colors.RESET}")

def mystery_room(player: Player, floor: int, active_pacts: List[str]):
    delay_print(f"\n{Colors.MAGENTA}--- LA STANZA DEL MISTERO ---{Colors.RESET}")
    print(f"❤️  HP: {Colors.GREEN}{player.hp}/{player.max_hp}{Colors.RESET} | 💰 Oro: {Colors.YELLOW}{player.gold}{Colors.RESET}\n")
    delay_print("Entri in un ambiente intriso di nebbia magica. I tuoi sensi sono annebbiati...", 0.03)
    time.sleep(1)

    outcome = random.choice(["hard", "easy", "trap", "empty"])

    if outcome == "hard":
        print(f"\n{Colors.RED}Dall'oscurità emerge un mostro eccezionalmente feroce!{Colors.RESET}")
        input("Premi INVIO per difenderti...")
        combat_room(player, floor, Enemy(floor, False, active_pacts, modifier="hard"))
    elif outcome == "easy":
        print(f"\n{Colors.CYAN}Scorgi un nemico ferito e confuso che vaga nella nebbia.{Colors.RESET}")
        input("Premi INVIO per attaccare...")
        combat_room(player, floor, Enemy(floor, False, active_pacts, modifier="easy"))
    elif outcome == "trap":
        trap_room(player, floor, active_pacts)
    elif outcome == "empty":
        print(f"\n{Colors.GREEN}La nebbia si dirada. La stanza è vuota. Tiri un sospiro di sollievo.{Colors.RESET}")
        input("Premi INVIO per proseguire...")

def event_room(player: Player, event_id: str, floor: int):
    ev = GAME_DATA["events"][event_id]
    clear_screen()
    print(f"\n{Colors.MAGENTA}{Colors.BOLD}--- {ev['title']} ---{Colors.RESET}")
    print(f"❤️  HP: {Colors.GREEN}{player.hp}/{player.max_hp}{Colors.RESET} | 💰 Oro: {Colors.YELLOW}{player.gold}{Colors.RESET}\n")
    delay_print(ev["text"], 0.03)
    
    while True:
        print("\nScegli:")
        for i, c in enumerate(ev["choices"]): print(f"{i+1}. {c['text']}")
        choice = get_choice("> ")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(ev["choices"]):
                action = ev["choices"][idx]["action"]
                msg = ev["choices"][idx].get("msg", "")
                msg_alt = ev["choices"][idx].get("msg_alt", "")
                
                if action == "heal_max":
                    player.max_hp += 10
                    if not player.cursed: player.hp = player.max_hp; print(f"{Colors.GREEN}Senti un potere immenso! HP Ripristinati!{Colors.RESET}")
                    else: print(f"{Colors.RED}L'acqua scivola via... la maledizione blocca la cura.{Colors.RESET}")
                elif action == "coin_toss":
                    if player.gold >= 20:
                        player.gold -= 20
                        if random.random() > 0.5:
                            r = get_random_relic(player)
                            if r: player.add_relic(r)
                            else: player.gold += 50; print(f"{Colors.YELLOW}{msg} (+50 Oro){Colors.RESET}")
                        else: print(f"{Colors.YELLOW}{msg_alt}{Colors.RESET}")
                    else: print(f"{Colors.RED}Oro insufficiente!{Colors.RESET}"); continue
                elif action == "trade_weapon":
                    if player.gold >= 50:
                        player.gold -= 50
                        drop = generate_weapon(floor + 2, True)
                        player.inventory.append(drop); print(f"{Colors.MAGENTA}Ottieni: {drop.display_name}!{Colors.RESET}")
                    else: print(f"{Colors.RED}Non hai abbastanza Oro.{Colors.RESET}"); continue
                elif action == "trade_relic":
                    player.hp -= 30
                    print(f"{Colors.RED}{msg}{Colors.RESET}")
                    if player.hp <= 0:
                        print(f"\n{Colors.RED}{Colors.BOLD}Il dissanguamento ti è stato fatale...{Colors.RESET}")
                        input("\nPremi INVIO per continuare...")
                        return
                    r = get_random_relic(player)
                    if r: player.add_relic(r)
                elif action == "blood_gold":
                    player.hp -= 40
                    g = 100 * 3 if player.midas else 100
                    player.gold += g; print(f"{Colors.RED}{msg} (+{g} Oro){Colors.RESET}.")
                    if player.hp <= 0:
                        print(f"\n{Colors.RED}{Colors.BOLD}Hai sacrificato troppa linfa vitale... Sei morto.{Colors.RESET}")
                        input("\nPremi INVIO per continuare...")
                        return
                elif action == "fight_elite":
                    print(f"{Colors.RED}{msg}{Colors.RESET}")
                    e = Enemy(floor + 5, True, player.active_pacts) # Elite
                    input("Premi INVIO per combattere..."); combat_room(player, floor, e)
                    if player.hp <= 0: return 
                elif action == "none": print(f"{Colors.CYAN}{msg}{Colors.RESET}")
                
                input("\nPremi INVIO per proseguire...")
                return
        except ValueError: pass

def vendor_room(player: Player, floor: int):
    delay_print(f"\n{random.choice(GAME_DATA['lore']['vendor'])}")
    items_for_sale =[generate_weapon(floor + 1), generate_armor(floor + 1), generate_potion(floor), generate_potion(floor)]
    discount = 1.0 - (PROFILE["perks"]["discount_lvl"] * 0.10)
    for i in items_for_sale: 
        i.value = max(1, int(i.value * discount))
        if "inflazione" in player.active_pacts: i.value = int(i.value * 2)

    while True:
        clear_screen()
        print(f"\n{Colors.YELLOW}[ 💰 MERCANTE ] | Tuo Oro: {player.gold}{Colors.RESET}")
        if PROFILE["perks"]["discount_lvl"] > 0: print(f"{Colors.GREEN}(Sconto del {PROFILE['perks']['discount_lvl']*10}%!){Colors.RESET}")
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
                            player.gold -= item.value; player.inventory.append(item)
                            print(f"{Colors.GREEN}Hai comprato {item.name}!{Colors.RESET}"); items_for_sale.pop(idx); time.sleep(1)
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
                        item = player.inventory.pop(idx); gain = max(1, item.value // 2)
                        player.gold += gain; print(f"{Colors.GREEN}Hai venduto {item.name} per {gain} oro!{Colors.RESET}"); time.sleep(1)
                except ValueError: pass
        elif action == '0': break

def campfire_room(player: Player, floor: int):
    delay_print(f"\n{Colors.YELLOW}{random.choice(GAME_DATA['lore']['campfire'])}{Colors.RESET}")
    while True:
        clear_screen()
        print(f"\n{Colors.YELLOW}[ 🔥 FALÒ E FORGIA ] | Tuo Oro: {player.gold} | HP: {player.hp}/{player.max_hp}{Colors.RESET}")
        print("1. Riposa (Recupera 50% HP, il falò si spegnerà)")
        print(f"2. Affila Arma Base (Paga {Colors.YELLOW}50 Oro{Colors.RESET} per +3 ATK, il falò si spegnerà)")
        print(f"3. {Colors.MAGENTA}Altare dell'Evoluzione{Colors.RESET} (Fondi due armi/armature per potenziarle)")
        print("0. Prosegui")
        
        action = get_choice("Scegli > ")
        if action == '1':
            player.hp = min(player.max_hp, player.hp + player.max_hp // 2)
            print(f"{Colors.GREEN}Ti riposi profondamente!{Colors.RESET}"); input("\nPremi INVIO..."); break
        elif action == '2':
            if player.gold >= 50:
                player.gold -= 50; player.weapon.atk += 3
                print(f"{Colors.GREEN}Arma migliorata: {player.weapon.atk} ATK!{Colors.RESET}"); input("\nPremi INVIO..."); break
            else: print(f"{Colors.RED}Oro insufficiente.{Colors.RESET}"); time.sleep(1.5)
        elif action == '3':
            while True:
                clear_screen()
                print(f"\n{Colors.MAGENTA}--- FUSIONE EQUIPAGGIAMENTO ---{Colors.RESET}")
                equips =[i for i in player.inventory if i.type in["weapon", "armor"]]
                if len(equips) < 2: print("Hai bisogno di almeno 2 armi/armature nello zaino per usare l'Altare."); input("Premi INVIO..."); break
                
                for i, item in enumerate(equips):
                    stat = f"+{item.atk} ATK" if item.type == "weapon" else f"+{item.defense} DEF"
                    print(f"{i+1}.[{item.type.upper()}] {item.display_name} {stat} (Lv.{item.level})")
                print("0. Indietro")
                
                c1 = get_choice("Seleziona il PRIMO oggetto (Base) > ")
                if c1 == '0': break
                c2 = get_choice("Seleziona il SECONDO oggetto (Sacrificio) > ")
                if c2 == '0': break
                
                try:
                    i1, i2 = int(c1)-1, int(c2)-1
                    if i1 != i2 and 0 <= i1 < len(equips) and 0 <= i2 < len(equips):
                        it1, it2 = equips[i1], equips[i2]
                        if it1.type == it2.type:
                            player.inventory.remove(it2)
                            if it1.type == "weapon": it1.atk += max(1, it2.atk // 2)
                            else: it1.defense += max(1, it2.defense // 2)
                            it1.level += 1
                            it1.display_name = f"Perfetto {it1.name.split('[')[0].strip()}[{get_element_icon(it1.element)}]"
                            player.run_tracker["fusions"] += 1
                            print(f"{Colors.GREEN}FUSIONE RIUSCITA! Il primo oggetto ha assorbito il secondo.{Colors.RESET}")
                            input("Premi INVIO per continuare...")
                            return 
                        else: print(f"{Colors.RED}Puoi fondere solo oggetti dello stesso tipo!{Colors.RESET}"); time.sleep(1.5)
                    else: print(f"{Colors.RED}Selezione non valida.{Colors.RESET}"); time.sleep(1.5)
                except ValueError: pass
        elif action == '0': break

def treasure_room(player: Player, floor: int):
    delay_print(f"\n{Colors.YELLOW}{random.choice(GAME_DATA['lore']['treasure'])}{Colors.RESET}")
    gold = random.randint(30, 60) + (floor * 10)
    g = gold * 3 if player.midas else gold
    if "tasca_dorata" in player.relic_ids: g = int(g * 1.25)
    if "idolo_avidita" in player.relic_ids: g *= 2
    
    player.gold += g
    print(f"{Colors.GREEN}Trovate {g} monete d'oro!{Colors.RESET}")
    
    if random.random() < 0.15:
        r = get_random_relic(player)
        if r: player.add_relic(r)
    elif random.random() > 0.4:
        drop = generate_potion(floor)
        print(f"C'era anche: {Colors.CYAN}{drop.display_name}{Colors.RESET}!"); player.inventory.append(drop)
    input("\nPremi INVIO per continuare...")

def trap_room(player: Player, floor: int, active_pacts: List[str]):
    delay_print(f"\n{random.choice(GAME_DATA['lore']['trap'])}")
    delay_print(f"{Colors.RED}È UNA TRAPPOLA!{Colors.RESET}", 0.05)
    
    if random.randint(1, 100) <= player.get_dodge(): 
        print(f"{Colors.GREEN}Schivi il meccanismo! Ne esci illeso!{Colors.RESET}")
    else:
        dmg = random.randint(15, 30) + (floor * 3)
        if "trappole" in active_pacts: dmg *= 2
        player.hp -= dmg
        print(f"{Colors.RED}Subisci {dmg} danni puri.{Colors.RESET} (HP: {player.hp}/{player.max_hp})")
        if player.hp <= 0:
            print(f"\n{Colors.RED}{Colors.BOLD}La trappola ti è stata fatale...{Colors.RESET}")
            input("\nPremi INVIO per continuare...")
            return
            
    if random.randint(1, 100) <= 20:
        print(f"\n{Colors.GREEN}Tra gli ingranaggi spezzati della trappola noti qualcosa brillare...{Colors.RESET}")
        drop = generate_weapon(floor, False) if random.random() > 0.5 else generate_armor(floor, False)
        print(f"{Colors.MAGENTA}Hai trovato: {drop.display_name}!{Colors.RESET}")
        player.inventory.append(drop)

    input("\nPremi INVIO per continuare...")

# --- CONTROLLO META-PROGRESSIONE (FINE RUN) ---
def evaluate_run(player: Player, floor: int, infinite: bool):
    print("\n" + ("="*50))
    if player.hp <= 0:
        delay_print(f"{Colors.RED}S E I   M O R T O.{Colors.RESET}")
        player.essence_gathered += int(player.gold * 0.20); PROFILE["stats"]["total_deaths"] += 1
    elif player.escaped:
        delay_print(f"{Colors.GREEN}S E I   F U G G I T O.{Colors.RESET}"); player.essence_gathered += player.gold
        
    player.essence_gathered += (player.bosses_killed * 50)
    
    pact_multi = 1.0 + sum([GAME_DATA["meta"]["pacts"][p]["bonus"] for p in player.active_pacts])
    final_essence = int(player.essence_gathered * pact_multi)
    if infinite and floor > 30: final_essence = int(final_essence * 1.5)
    
    PROFILE["essence"] += final_essence
    PROFILE["stats"]["total_gold"] += player.gold

    print(f"Piano raggiunto: {floor} | Boss: {player.bosses_killed}")
    print(f"Moltiplicatore Maledizioni: {pact_multi}x")
    print(f"Essenza Astrale ottenuta: {Colors.CYAN}✨ {final_essence}{Colors.RESET}")
    
    c_id = player.class_id
    xp_gained = (floor * 10) + (player.bosses_killed * 50)
    curr_xp = PROFILE["class_xp"].get(c_id, 0) + xp_gained
    curr_lvl = PROFILE["class_lvl"].get(c_id, 1)
    PROFILE["class_xp"][c_id] = curr_xp
    
    print(f"\n{Colors.MAGENTA}[ Maestria {player.role} ] +{xp_gained} XP (Totale: {curr_xp}){Colors.RESET}")
    reqs = GAME_DATA["meta"]["mastery_xp_requirements"]
    while curr_lvl < 5 and curr_xp >= reqs[str(curr_lvl + 1)]:
        curr_lvl += 1; PROFILE["class_lvl"][c_id] = curr_lvl
        print(f"{Colors.YELLOW}*** MAESTRIA SALITA AL LIVELLO {curr_lvl}! ***{Colors.RESET}")
        reward = GAME_DATA["classes"][c_id]["mastery"][str(curr_lvl)]
        print(f"Sbloccato: {reward['desc']}")
        if reward["type"] in ["unlock", "class"] and reward["id"] != "null" and reward["id"] not in PROFILE["unlocked_ids"]:
            PROFILE["unlocked_ids"].append(reward["id"])
            
    print(f"\n{Colors.CYAN}[ Imprese ]{Colors.RESET}")
    for f_id, f_data in GAME_DATA["meta"]["feats"].items():
        if f_id in PROFILE["completed_feats"]: continue
        completed = False
        if f_id == "feat_pacifista" and player.run_tracker["escapes"] >= f_data["target"]: completed = True
        elif f_id == "feat_fabbro" and player.run_tracker["fusions"] >= f_data["target"]: completed = True
        elif f_id == "feat_vetro" and player.run_tracker["no_hit_boss_done"]: completed = True
        elif f_id == "feat_suicida" and player.run_tracker["kill_1_hp_done"]: completed = True
        
        if completed:
            print(f"{Colors.GREEN}Impresa Completata: {f_data['name']}!{Colors.RESET}"); PROFILE["completed_feats"].append(f_id)
            if f_data["reward_type"] in ["unlock", "class"] and f_data["reward_id"] not in PROFILE["unlocked_ids"]: PROFILE["unlocked_ids"].append(f_data["reward_id"])
            elif f_data["reward_type"] == "perk": PROFILE["perks"][f_data["reward_id"]] = True

    print("="*50); save_profile(PROFILE)
    input(f"\n{Colors.CYAN}Premi INVIO per tornare al Menu Principale...{Colors.RESET}")

# --- HUB E LOOP DI GIOCO ---
def base_camp():
    while True:
        clear_screen()
        print(f"{Colors.MAGENTA}{Colors.BOLD}=== 🏕️ IL CAMPO BASE ==={Colors.RESET}")
        print(f"Essenza: {Colors.CYAN}✨ {PROFILE['essence']}{Colors.RESET}")
        print("1. Il Fuoco dell'Anima (Potenziamenti Base)")
        print("2. La Forgia Dimensionale (Sblocca Oggetti)")
        print("3. La Taverna (Recluta Eroi)")
        print("4. Grimorio e Imprese")
        print("0. Torna al Menu Principale")
        
        choice = get_choice("\nScegli > ")
        if choice == '1':
            while True:
                clear_screen()
                print(f"{Colors.CYAN}--- IL FUOCO DELL'ANIMA --- Essenza: ✨{PROFILE['essence']}{Colors.RESET}")
                hl, gl, dl, ss = PROFILE["perks"]["hp_lvl"], PROFILE["perks"]["gold_lvl"], PROFILE["perks"]["discount_lvl"], PROFILE["perks"]["sesto_senso"]
                print(f"1. Vigore Ereditario[Lv.{hl}/5] (+15 HP Max) - Costo: ✨{50 + (hl*50)}")
                print(f"2. Tasche Profonde[Lv.{gl}/3] (+20 Oro Iniziale) - Costo: ✨{100 + (gl*100)}")
                print(f"3. Mercanteggiare[Lv.{dl}/3] (-10% Prezzi Negozio) - Costo: ✨{150 + (dl*100)}")
                print(f"4. Sesto Senso[{'SBLOCCATO' if ss else 'BLOCCATO'}] (Prevedi bivi) - Costo: ✨300")
                print("0. Indietro")
                p_c = get_choice("> ")
                if p_c == '0': break
                if p_c == '1' and hl < 5 and PROFILE['essence'] >= 50+(hl*50): PROFILE['essence']-=50+(hl*50); PROFILE["perks"]["hp_lvl"]+=1; save_profile(PROFILE)
                elif p_c == '2' and gl < 3 and PROFILE['essence'] >= 100+(gl*100): PROFILE['essence']-=100+(gl*100); PROFILE["perks"]["gold_lvl"]+=1; save_profile(PROFILE)
                elif p_c == '3' and dl < 3 and PROFILE['essence'] >= 150+(dl*100): PROFILE['essence']-=150+(dl*100); PROFILE["perks"]["discount_lvl"]+=1; save_profile(PROFILE)
                elif p_c == '4' and not ss and PROFILE['essence'] >= 300: PROFILE['essence']-=300; PROFILE["perks"]["sesto_senso"]=True; save_profile(PROFILE)
        elif choice == '2':
            while True:
                clear_screen()
                print(f"{Colors.CYAN}--- FORGIA DIMENSIONALE --- Essenza: ✨{PROFILE['essence']}{Colors.RESET}")
                lkd =[i for cat in["weapons", "armors", "consumables"] for i in RAW_DATA[cat] if "unlock_id" in i and i["unlock_id"] not in PROFILE["unlocked_ids"]]
                if not lkd: print("Tutto sbloccato!")
                else:
                    for i, it in enumerate(lkd): print(f"{i+1}. {it['name']} ({it.get('desc', '')}) - Costo: ✨{it['unlock_cost']}")
                print("0. Indietro")
                fc = get_choice("> ")
                if fc == '0': break
                try:
                    idx = int(fc)-1
                    if 0<=idx<len(lkd) and PROFILE['essence']>=lkd[idx]["unlock_cost"] and lkd[idx]["unlock_cost"]>0:
                        PROFILE['essence']-=lkd[idx]["unlock_cost"]; PROFILE["unlocked_ids"].append(lkd[idx]["unlock_id"]); save_profile(PROFILE)
                        print(f"{Colors.GREEN}Sbloccato: {lkd[idx]['name']}!{Colors.RESET}")
                        for cat in["weapons", "armors", "consumables"]: GAME_DATA[cat] =[x for x in RAW_DATA[cat] if x.get("unlock_id") is None or x["unlock_id"] in PROFILE["unlocked_ids"]]
                        time.sleep(1)
                except ValueError: pass
        elif choice == '3':
            while True:
                clear_screen()
                print(f"{Colors.CYAN}--- LA TAVERNA --- Essenza: ✨{PROFILE['essence']}{Colors.RESET}")
                lkc =[(c_id, c) for c_id, c in RAW_DATA["classes"].items() if not c.get("unlocked_by_default") and c_id not in PROFILE["unlocked_ids"] and c.get("unlock_id") not in PROFILE["unlocked_ids"]]
                if not lkc: print("Tutti reclutati!")
                else:
                    for i, (c_id, c) in enumerate(lkc): print(f"{i+1}. {Colors.BOLD}{c['role']}{Colors.RESET} ({c['desc']}) - Costo: ✨{c.get('unlock_cost', 0)}")
                print("0. Indietro")
                cc = get_choice("> ")
                if cc == '0': break
                try:
                    idx = int(cc)-1
                    if 0<=idx<len(lkc) and PROFILE['essence']>=lkc[idx][1].get("unlock_cost", 0) and lkc[idx][1].get("unlock_cost", 0)>0:
                        PROFILE['essence']-=lkc[idx][1]["unlock_cost"]; PROFILE["unlocked_ids"].append(lkc[idx][1]["unlock_id"]); save_profile(PROFILE)
                        print(f"{Colors.GREEN}Reclutato: {lkc[idx][1]['role']}!{Colors.RESET}"); time.sleep(1)
                except ValueError: pass
        elif choice == '4':
            clear_screen()
            print(f"{Colors.CYAN}--- GRIMORIO ---{Colors.RESET}")
            for f_id, f in GAME_DATA["meta"]["feats"].items():
                st = f"{Colors.GREEN}[V]{Colors.RESET}" if f_id in PROFILE["completed_feats"] else f"{Colors.RED}[X]{Colors.RESET}"
                print(f"{st} {f['name']}: {f['desc']}")
            print(f"\n{Colors.CYAN}--- MAESTRIA CLASSI ---{Colors.RESET}")
            for c_id, c in RAW_DATA["classes"].items():
                if c.get("unlocked_by_default") or c_id in PROFILE["unlocked_ids"] or c.get("unlock_id") in PROFILE["unlocked_ids"]:
                    print(f"{c['role']}: Lv.{PROFILE['class_lvl'].get(c_id, 1)} (XP: {PROFILE['class_xp'].get(c_id, 0)})")
            input("\nPremi INVIO per tornare indietro...")
        elif choice == '0': break

def play_game(infinite_mode=False):
    clear_screen()
    print(f"\n{Colors.CYAN}Scegli il tuo Eroe:{Colors.RESET}")
    avail_c = {c_id: c for c_id, c in RAW_DATA["classes"].items() if c.get("unlocked_by_default") or c_id in PROFILE["unlocked_ids"] or c.get("unlock_id") in PROFILE["unlocked_ids"]}
    
    avail_c_list = list(avail_c.items())
    for i, (c_id, c) in enumerate(avail_c_list): 
        print(f"{i+1}. {Colors.BOLD}{c['role'].upper()}{Colors.RESET} (Lv. Maestria: {PROFILE['class_lvl'].get(c_id, 1)})")
        
    while True:
        c_idx_str = get_choice("Classe (Numero): ")
        try:
            idx = int(c_idx_str) - 1
            if 0 <= idx < len(avail_c_list):
                c_choice = avail_c_list[idx][0]
                break
        except ValueError: pass
    
    avail_t_list =[]
    for t_id, t in GAME_DATA["meta"]["traits"].items():
        ul = True
        if t["unlock_req"] == "deaths_10" and PROFILE["stats"]["total_deaths"] < 10: ul = False
        if t["unlock_req"] == "gold_5000" and PROFILE["stats"]["total_gold"] < 5000: ul = False
        if ul: avail_t_list.append((t_id, t))
        
    if len(avail_t_list) == 1:
        t_choice = avail_t_list[0][0]
    else:
        print(f"\n{Colors.CYAN}Scegli un Tratto di partenza:{Colors.RESET}")
        for i, (t_id, t) in enumerate(avail_t_list):
            print(f"{i+1}. {Colors.BOLD}{t['name']}{Colors.RESET} ({t['desc']})")
            
        while True:
            t_idx_str = get_choice("Tratto (Numero): ")
            try:
                idx = int(t_idx_str) - 1
                if 0 <= idx < len(avail_t_list):
                    t_choice = avail_t_list[idx][0]
                    break
            except ValueError: pass

    active_pacts = []
    if PROFILE["won_normal"]:
        print(f"\n{Colors.RED}I PATTI DEL CAOS{Colors.RESET}")
        print("Attiva le maledizioni per aumentare il moltiplicatore di Essenza.")
        avail_p = GAME_DATA["meta"]["pacts"]
        for p_id, p in avail_p.items():
            ans = get_choice(f"Attivare '{p['name']}'? ({p['desc']})[s/N]: ").lower()
            if ans == 's': active_pacts.append(p_id)

    player = Player(c_choice, t_choice, active_pacts)
    delay_print(f"\nLe porte si chiudono alle tue spalle, {player.role}.", 0.03); time.sleep(1)
    
    weights_def = GAME_DATA["meta"]["rooms"]["weights"]
    cooldowns_def = GAME_DATA["meta"]["rooms"]["cooldowns"]
    room_cooldowns = {k: 0 for k in weights_def.keys()}
    
    floor = 1
    while player.hp > 0 and not player.escaped:
        if not infinite_mode and floor > 30:
            clear_screen()
            print(f"{Colors.YELLOW}{Colors.BOLD}="*50); delay_print("H A I   V I N T O ! ! !"); print("="*50 + Colors.RESET)
            PROFILE["won_normal"] = True; player.essence_gathered += 1000; break

        clear_screen()
        delay_print(f"\n{Colors.MAGENTA}{Colors.BOLD}==== PIANO {floor} ===={Colors.RESET}", 0.05)
        
        for step in range(1, 6):
            if player.hp <= 0 or player.escaped: break
            
            for k in room_cooldowns:
                if room_cooldowns[k] > 0: room_cooldowns[k] -= 1
            
            if step == 5: doors =[{"type": "boss", "enemy": Enemy(floor, True, active_pacts)}]
            else:
                doors =[]
                while True:
                    avail_rooms, avail_weights = [],[]
                    
                    for rt, w in weights_def.items():
                        if room_cooldowns.get(rt, 0) <= 0:
                            avail_rooms.append(rt)
                            avail_weights.append(w)
                    
                    if not avail_rooms: 
                        avail_rooms, avail_weights = ["combat"],[100]

                    t1 = random.choices(avail_rooms, weights=avail_weights)[0]
                    t2 = random.choices(avail_rooms, weights=avail_weights)[0]
                    
                    if t1 == t2: continue 
                    combo = {t1, t2}
                    if combo == {"trap", "treasure"} or combo == {"trap", "vendor"} or combo == {"mystery", "mystery"}: 
                        continue 
                    break

                room_cooldowns[t1] = cooldowns_def.get(t1, 0) + 1
                room_cooldowns[t2] = cooldowns_def.get(t2, 0) + 1

                for rt in[t1, t2]:
                    d = {"type": rt}
                    if rt == "combat": d["enemy"] = Enemy(floor, False, active_pacts)
                    if rt == "event": d["event_id"] = random.choice(list(GAME_DATA["events"].keys()))
                    doors.append(d)
            
            while True:
                print(f"\n{Colors.CYAN}--- Piano {floor} | Esplorazione {step}/5 ---{Colors.RESET}")
                print(f"❤️  HP: {Colors.GREEN}{player.hp}/{player.max_hp}{Colors.RESET} | 💰 Oro: {Colors.YELLOW}{player.gold}{Colors.RESET}")
                
                for i, d in enumerate(doors):
                    t_str = d["type"].upper()
                    if PROFILE["perks"]["sesto_senso"]:
                        if d["type"] == "combat": t_str += f" ({d['enemy'].name} {get_element_icon(d['enemy'].element)})"
                        elif d["type"] == "event": t_str += f" ({GAME_DATA['events'][d['event_id']]['title']})"
                        elif d["type"] == "mystery": t_str += f" ({Colors.MAGENTA}Aura illeggibile{Colors.RESET})"
                    print(f"{i+1}. Entra: [{t_str}]")
                print("I. Apri Inventario")
                print("F. Fuga dal Labirinto")
                
                action = get_choice("Scelta > ").upper()
                if action == 'I': player.manage_inventory()
                elif action == 'F':
                    clear_screen(); print(f"{Colors.YELLOW}Fuggi portando in salvo le ricchezze.{Colors.RESET}")
                    player.escaped = True; break
                else:
                    try:
                        idx = int(action) - 1
                        if 0 <= idx < len(doors):
                            chosen_door = doors[idx]; clear_screen(); break
                    except ValueError: pass
            
            if player.hp <= 0 or player.escaped: break
            
            rt = chosen_door["type"]
            if rt == "combat": combat_room(player, floor, chosen_door["enemy"])
            elif rt == "boss": combat_room(player, floor, chosen_door["enemy"])
            elif rt == "vendor": vendor_room(player, floor)
            elif rt == "treasure": treasure_room(player, floor)
            elif rt == "trap": trap_room(player, floor, active_pacts)
            elif rt == "campfire": campfire_room(player, floor)
            elif rt == "event": event_room(player, chosen_door["event_id"], floor)
            elif rt == "mystery": mystery_room(player, floor, active_pacts)
        
        if player.hp > 0 and not player.escaped:
            delay_print(f"\n{Colors.YELLOW}{Colors.BOLD}*** PIANO {floor} SUPERATO! ***{Colors.RESET}", 0.05)
            heal = 20 + (floor * 5)
            if not player.cursed: player.hp = min(player.max_hp, player.hp + heal)
            print(f"Ti riposi prima delle scale. (HP: {player.hp}/{player.max_hp})")
            floor += 1
            if floor > PROFILE["max_floor"]: PROFILE["max_floor"] = floor
            input("\nPremi INVIO per scendere...")

    evaluate_run(player, floor, infinite_mode)

def main():
    try:
        while True:
            clear_screen()
            delay_print(f"{Colors.MAGENTA}{Colors.BOLD}=== IL LABIRINTO DEGLI ELEMENTI E DEL CAOS ==={Colors.RESET}", 0.01)
            print(f"\n{Colors.CYAN}[ MENU PRINCIPALE ]{Colors.RESET}")
            print("1. Inizia Run (Standard - 30 Piani)")
            print("2. Campo Base (Potenziamenti, Forgia, Taverna)")
            if PROFILE["won_normal"]: print(f"3. {Colors.RED}Inizia Run Infinita (Oltre i 30 Piani){Colors.RESET}")
            print("0. Esci dal gioco")
            
            choice = get_choice("\nScelta > ")
            if choice == '1': play_game(infinite_mode=False)
            elif choice == '2': base_camp()
            elif choice == '3' and PROFILE["won_normal"]: play_game(infinite_mode=True)
            elif choice == '0': clear_screen(); print("Arrivederci!"); break
    except Exception as e:
        print(f"\n{Colors.RED}{Colors.BOLD}ERRORE IMPREVISTO! Il gioco è andato in crash:{Colors.RESET}")
        traceback.print_exc()
        input(f"\n{Colors.CYAN}Premi INVIO per uscire...{Colors.RESET}")

if __name__ == "__main__":
    main()