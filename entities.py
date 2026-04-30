import random
from typing import List, Dict, Any
from ui import Colors, delay_print
from data_manager import GAME_DATA, RAW_DATA, PROFILE, ELEMENTS, MULTIPLIERS, get_element_icon
from relic_effects import create_relic_effect

class Item:
    def __init__(self, name: str, value: int, item_type: str, level: int = 1, flavor: str = ""):
        self.name, self.value, self.type, self.level, self.flavor = name, value, item_type, level, flavor

class Weapon(Item):
    def __init__(self, name: str, value: int, atk: int, element: str, level: int, flavor: str = ""):
        super().__init__(name, value, "weapon", level, flavor)
        self.atk, self.element = atk, element
        self.display_name = f"{name}[{get_element_icon(element)}]"

class Armor(Item):
    def __init__(self, name: str, value: int, defense: int, element: str, level: int, flavor: str = ""):
        super().__init__(name, value, "armor", level, flavor)
        self.defense, self.element = defense, element
        self.display_name = f"{name}[{get_element_icon(element)}]"

class Accessory(Item):
    def __init__(self, name: str, value: int, element: str, bonus_type: str, bonus_value: int, desc: str, flavor: str = ""):
        super().__init__(name, value, "accessory", 1, flavor)
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
    name, flavor = w_data["name"], w_data.get("flavor", "")
    atk = w_data["base_atk"] + int(level * 1.5) + random.randint(0, 3)
    element = generate_random_element()
    if element == "Normale": atk = int(atk * 1.2) + 1
    if is_epic: atk = int(atk * 1.5) + 2; name = f"EPICO {name}"
    return Weapon(f"{name} (lv.{level})", atk * 5, atk, element, level, flavor)

def generate_armor(level: int, is_epic: bool = False) -> Armor:
    a_data = random.choice(GAME_DATA["armors"])
    name, flavor = a_data["name"], a_data.get("flavor", "")
    defense = a_data["base_def"] + int(level * 1.2) + random.randint(0, 2)
    element = generate_random_element()
    if element == "Normale": defense = int(defense * 1.2) + 1
    if is_epic: defense = int(defense * 1.5) + 2; name = f"EPICO {name}"
    return Armor(f"{name} (lv.{level})", defense * 8, defense, element, level, flavor)

def generate_accessory(level: int) -> Accessory:
    a_data = random.choice(GAME_DATA["accessories"])
    return Accessory(a_data["name"], a_data["base_val"] + (level*10), a_data.get("element", "Normale"), a_data["bonus_type"], a_data["bonus_value"], a_data["desc"], a_data.get("lore", ""))

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
        self.relics = []
        self.relic_effects = []
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
        effect = create_relic_effect(relic["id"])
        self.relic_effects.append(effect)
        effect.on_equip(self)
        print(f"\n{Colors.MAGENTA}🌟 Hai ottenuto la Reliquia: {relic['name']}!{Colors.RESET}")
        print(f"Effetto: {relic['desc']}")
        if "lore" in relic: print(f"{Colors.YELLOW}Lore: {relic['lore']}{Colors.RESET}")

    def get_total_atk(self): return self.weapon.atk + self.bonus_atk_relic
    
    def get_dodge(self): 
        dodge = self.base_dodge + self.temp_dodge
        for effect in self.relic_effects: dodge += effect.get_dodge_modifier()
        if self.class_id == "5" and PROFILE["class_lvl"].get("5", 1) >= 2 and self.hp < self.max_hp * 0.3: return 0
        return max(0, dodge)

    def _get_resonance_element(self):
        if self.weapon.element != "Normale" and self.weapon.element == self.armor.element:
            return self.weapon.element
        return None

    def gain_exp(self, amount: int):
        if self.midas: return
        multi = self.exp_multiplier
        for effect in self.relic_effects: multi += effect.get_exp_modifier()
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



class Enemy:
    def __init__(self, floor: int, is_boss: bool, active_pacts: List[str], modifier: str = "normal"):
        self.is_boss = is_boss
        self.modifier = modifier
        category = "bosses" if is_boss else "enemies"
        self.name = random.choice(list(GAME_DATA[category].keys()))
        data = GAME_DATA[category][self.name]
        
        self.element, self.base_acc, self.base_dodge = data["element"], data["base_acc"], data["base_dodge"]
        self.title = data.get("title", "")
        self.lore = data.get("lore", "")
        
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

