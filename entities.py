import random
import time
from typing import List, Dict, Any
from ui import Colors, clear_screen, delay_print, get_choice
from data_manager import GAME_DATA, RAW_DATA, PROFILE, ELEMENTS, MULTIPLIERS, get_element_icon

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

class Accessory(Item):
    def __init__(self, name: str, value: int, element: str, bonus_type: str, bonus_value: int, desc: str):
        super().__init__(name, value, "accessory", 1)
        self.element, self.bonus_type, self.bonus_value, self.desc = element, bonus_type, bonus_value, desc
        self.display_name = f"{name} [{get_element_icon(element)}]"

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

def generate_accessory(level: int) -> Accessory:
    a_data = random.choice(GAME_DATA["accessories"])
    return Accessory(a_data["name"], a_data["base_val"] + (level*10), a_data.get("element", "Normale"), a_data["bonus_type"], a_data["bonus_value"], a_data["desc"])

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
        if PROFILE["class_lvl"].get("4", 1) >= 4: self.max_hp += 15 
        if PROFILE["class_lvl"].get("6", 1) >= 4: self.base_acc += 5 
        
        self.trait = GAME_DATA["meta"]["traits"][trait_id]
        self.cursed, self.midas, self.ethereal_hunter = False, False, False
        if trait_id == "maledetto":
            self.max_hp //= 2; self.hp = self.max_hp; self.cursed = True
        if trait_id == "midas": self.midas = True
        if trait_id == "aristocratico": self.gold += 500
        if trait_id == "cacciatore_etereo": self.base_dodge -= 20; self.ethereal_hunter = True
        if trait_id == "titano": self.max_hp += 100; self.hp += 100; self.base_acc //= 2; self.base_dodge //= 2
        
        self.benedetto_save = False
        if trait_id == "benedetto":
            self.benedetto_save = True
            r = next((x for x in GAME_DATA["relics"] if x["id"] == "scudo_cristallo"), None)
            if r: self.add_relic(r)
        
        self.base_dodge += PROFILE["perks"].get("dodge_lvl", 0) * 2
        self.base_acc += PROFILE["perks"].get("acc_lvl", 0) * 3
        self.exp_multiplier += PROFILE["perks"].get("exp_lvl", 0) * 0.05
        
        start_weapon_lv = 2 if class_id == "1" and PROFILE["class_lvl"].get("1", 1) >= 2 else 1
        self.thief_save = True if class_id == "2" and PROFILE["class_lvl"].get("2", 1) >= 2 else False
        self.mage_lifesteal = True if class_id == "3" and PROFILE["class_lvl"].get("3", 1) >= 2 else False

        self.level, self.exp, self.max_exp = 1, 0, 100
        self.escaped = False
        self.run_tracker = {"escapes": 0, "fusions": 0, "no_hit_boss_done": False, "kill_1_hp_done": False}
        self.essence_gathered, self.bosses_killed = 0, 0
        
        w_data = data["weapon"]
        self.weapon = Weapon(w_data["name"], w_data["value"], w_data["atk"] + (50 if self.cursed else 0) + PROFILE["perks"].get("artigiano_lvl", 0), w_data.get("element", "Normale"), 1) if start_weapon_lv == 1 else generate_weapon(2)
        if PROFILE["perks"].get("artigiano_lvl", 0) > 0 and start_weapon_lv != 1: self.weapon.atk += PROFILE["perks"].get("artigiano_lvl", 0)
        if PROFILE["class_lvl"].get("5", 1) >= 4: self.weapon.atk += 2
        self.temp_dodge = 0
        self.temp_def = 0
        
        a_data = data["armor"]
        self.armor = Armor(a_data["name"], a_data["value"], a_data["def"] + PROFILE["perks"].get("pelle_dura_lvl", 0), a_data.get("element", "Normale"), 1)
        self.accessory = None
        
        potions_count = data["potions"] + (1 if PROFILE["perks"].get("farmacista", False) else 0)
        self.inventory =[generate_potion(1) for _ in range(potions_count)]
        
        if PROFILE["perks"].get("altare_benedizione", False):
            r = get_random_relic(self)
            if r: self.add_relic(r)

    def add_relic(self, relic):
        self.relics.append(relic)
        self.relic_ids.append(relic["id"])
        print(f"\n{Colors.MAGENTA}🌟 Hai ottenuto la Reliquia: {relic['name']}!{Colors.RESET}")
        print(f"Effetto: {relic['desc']}")
        if relic["id"] == "idolo_guerra": self.bonus_atk_relic += 5
        elif relic["id"] == "lama_sangue": self.bonus_atk_relic += 10
        elif relic["id"] == "mantello_nebbioso": self.base_dodge += 15
        elif relic["id"] == "occhio_cacciatore": self.base_acc += 20
        elif relic["id"] == "cuore_drago": self.max_hp += 50; self.hp += 50
        elif relic["id"] == "spirito_spada":
            if self.weapon.level == 1: self.bonus_atk_relic += 15

    def get_total_atk(self): return self.weapon.atk + self.bonus_atk_relic
    
    def get_dodge(self): 
        if "idolo_avidita" in self.relic_ids: return 0
        if self.class_id == "5" and PROFILE["class_lvl"].get("5", 1) >= 2 and self.hp < self.max_hp * 0.3: return 0
        return self.base_dodge + self.temp_dodge

    def _get_resonance_element(self):
        if self.weapon.element != "Normale" and self.weapon.element == self.armor.element:
            return self.weapon.element
        return None

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
            acc_txt = f"{self.accessory.display_name} ({self.accessory.desc})" if self.accessory else "Nessuno"
            print(f"💍 Monile: {acc_txt}")
            res_el = self._get_resonance_element()
            if res_el: print(f"✨ {Colors.CYAN}RISONANZA ATTIVA: {get_element_icon(res_el)}!{Colors.RESET}")
            if self.relics:
                print(f"🌟 Reliquie attive:")
                for r in self.relics: print(f"   - {Colors.YELLOW}{r['name']}{Colors.RESET}: {r['desc']}")
            print("-" * 55)
            
            display_items = []
            if not self.inventory: print("L'inventario è vuoto.")
            else:
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
                    elif item.type == "accessory": print(f"{disp_idx+1}. [Monile] {item.display_name} ({item.desc})")
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
                        elif "Fiala del Caos" in item.name:
                            if not in_combat: print(f"{Colors.RED}Puoi usarla solo in combattimento!{Colors.RESET}"); time.sleep(1); return "used"
                            self.inventory.pop(real_idx)
                            print(f"{Colors.MAGENTA}Lanci la Fiala del Caos!{Colors.RESET}")
                            time.sleep(1); return "fiala_caos"
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
                        elif "Acqua Santa" in item.name:
                            self.inventory.pop(real_idx)
                            self.hp = min(self.max_hp, self.hp + 50)
                            if in_combat: self.temp_def += 5; self.temp_dodge += 5
                            print(f"{Colors.GREEN}Bevi l'Acqua Santa: +50 HP e bonus difensivi temporanei! (HP: {self.hp}/{self.max_hp}){Colors.RESET}")
                            input("Premi INVIO..."); return "turn_used" if in_combat else "used"
                        else:
                            if self.cursed:
                                print(f"{Colors.RED}La tua Maledizione rende inutile la pozione.{Colors.RESET}")
                                self.inventory.pop(real_idx)
                            else:
                                old_hp = self.hp
                                base_h = item.heal_amount
                                if "calice_alchimista" in self.relic_ids: base_h = int(base_h * 1.5)
                                if self.class_id == "6" and PROFILE["class_lvl"].get("6", 1) >= 2: base_h = int(base_h * 1.5)
                                h_amt = base_h // 2 if "carestia" in self.active_pacts else base_h
                                
                                self.hp = min(self.max_hp, self.hp + h_amt)
                                print(f"{Colors.GREEN}\n-> Recuperi {self.hp - old_hp} HP! (HP: {self.hp}/{self.max_hp}){Colors.RESET}")
                                if self.thief_save and random.random() < 0.3: print(f"{Colors.CYAN}Abilità Ladro: Hai salvato la pozione!{Colors.RESET}")
                                elif "pozione_infinita" in self.relic_ids and random.random() < 0.25: print(f"{Colors.CYAN}Pozione Senza Fondo: La fiala si riempie di nuovo!{Colors.RESET}")
                                else: self.inventory.pop(real_idx)
                            input("Premi INVIO..."); return "turn_used" if in_combat else "used"
                            
                    elif item.type == "weapon":
                        self.run_tracker["weapon_changed"] = True
                        old_w, self.weapon = self.weapon, item
                        self.inventory[real_idx] = old_w
                        print(f"{Colors.GREEN}\n-> Equipaggiato: {self.weapon.display_name}!{Colors.RESET}")
                        input("Premi INVIO..."); return "turn_used" if in_combat else "used"
                    elif item.type == "armor":
                        old_a, self.armor = self.armor, item
                        self.inventory[real_idx] = old_a
                        print(f"{Colors.GREEN}\n-> Equipaggiato: {self.armor.display_name}!{Colors.RESET}")
                        input("Premi INVIO..."); return "turn_used" if in_combat else "used"
                    elif item.type == "accessory":
                        old_acc = self.accessory
                        if old_acc:
                            if old_acc.bonus_type == "max_hp": self.max_hp -= old_acc.bonus_value; self.hp = min(self.hp, self.max_hp)
                            if old_acc.bonus_type == "dodge": self.base_dodge -= old_acc.bonus_value
                            if old_acc.bonus_type == "acc": self.base_acc -= old_acc.bonus_value
                        
                        self.accessory = item
                        if self.accessory.bonus_type == "max_hp": self.max_hp += self.accessory.bonus_value; self.hp += self.accessory.bonus_value
                        if self.accessory.bonus_type == "dodge": self.base_dodge += self.accessory.bonus_value
                        if self.accessory.bonus_type == "acc": self.base_acc += self.accessory.bonus_value
                        
                        if old_acc: self.inventory[real_idx] = old_acc
                        else: self.inventory.pop(real_idx)
                        print(f"{Colors.GREEN}\n-> Equipaggiato: {self.accessory.display_name}!{Colors.RESET}")
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

