import random
from typing import List, Dict
from ui import Colors, delay_print, get_choice, clear_screen, display_msg
from data_manager import GAME_DATA, RAW_DATA, PROFILE_MANAGER, ELEMENTS, MULTIPLIERS, get_element_icon
from relic_effects import create_relic_effect
from archive import get_archive_bonus
from constants import BASE_HIT_CHANCE, ENEMY_DEPTH_WINDOW, BOSS_DEPTH_WINDOW, INFINITE_MODE_THRESHOLD, WEAPON_LEVEL_SCALING, ARMOR_LEVEL_SCALING, CURSE_CHANCE, CURSE_STAT_MULTIPLIER

class Item:
    def __init__(self, name: str, value: int, item_type: str, level: int = 1, flavor: str = "", is_cursed: bool = False, curse_effect: str = "", element: str = "Normale"):
        self.name, self.value, self.type, self.level, self.flavor = name, value, item_type, level, flavor
        self.is_cursed, self.curse_effect, self.element = is_cursed, curse_effect, element
        self.refresh_display_name()

    def refresh_display_name(self):
        cursed_tag = f"{Colors.MAGENTA}[MALEDETTO]{Colors.RESET} " if self.is_cursed else ""
        el_tag = f" [{get_element_icon(self.element)}]" if self.element != "Normale" and self.element != "" else ""
        self.display_name = f"{cursed_tag}{self.name}{el_tag}"

STATUS_NAMES = {"poison": "Veleno", "bleed": "Sanguinamento"}

class Weapon(Item):
    def __init__(self, name: str, value: int, atk: int, element: str, level: int, flavor: str = "", is_cursed: bool = False, curse_effect: str = "", status_inflict: dict = None):
        super().__init__(name, value, "weapon", level, flavor, is_cursed, curse_effect, element)
        self.atk = atk
        # Stesso formato di status_inflict dei nemici: {"type", "chance", "duration"}
        self.status_inflict = status_inflict

    def get_hit_chance_modifier(self) -> int:
        if "Ascia del Boia" in self.name:
            return -15
        return 0
        
    def on_attack(self, dmg_dealt: int, eff: str) -> tuple[int, str]:
        if "Ascia del Boia" in self.name and random.random() < 0.35:
            return dmg_dealt * 2, eff + f" {Colors.MAGENTA}[CRITICO DELL'ASCIA!]{Colors.RESET}"
        return dmg_dealt, eff

class Armor(Item):
    def __init__(self, name: str, value: int, defense: int, element: str, level: int, flavor: str = "", is_cursed: bool = False, curse_effect: str = ""):
        super().__init__(name, value, "armor", level, flavor, is_cursed, curse_effect, element)
        self.defense = defense

class Accessory(Item):
    def __init__(self, name: str, value: int, element: str, bonus_type: str, bonus_value: int, desc: str, flavor: str = "", is_cursed: bool = False, curse_effect: str = ""):
        super().__init__(name, value, "accessory", 1, flavor, is_cursed, curse_effect, element)
        self.bonus_type, self.bonus_value, self.desc = bonus_type, bonus_value, desc

class Consumable(Item):
    def __init__(self, name: str, value: int, heal_amount: int, category: str = "heal"):
        super().__init__(name, value, "consumable", 1)
        self.heal_amount = heal_amount
        self.category = category
        self.display_name = name

def generate_random_element() -> str:
    if random.random() < 0.4: return "Normale"
    return random.choice([e for e in ELEMENTS if e != "Normale"])

def generate_weapon(level: int, is_epic: bool = False) -> Weapon:
    w_data = random.choice(GAME_DATA["weapons"])
    name, flavor = w_data["name"], w_data.get("flavor", "")
    atk = w_data["base_atk"] + int(level * WEAPON_LEVEL_SCALING) + random.randint(0, 3)
    element = generate_random_element()
    
    is_cursed, curse_effect = False, ""
    if not is_epic and random.random() < CURSE_CHANCE:
        is_cursed = True
        curse_effect = random.choice(["hp_drain", "gold_drain"])
        atk = int(atk * CURSE_STAT_MULTIPLIER)
        
    if element == "Normale": atk = int(atk * 1.2) + 1
    if is_epic: atk = int(atk * 1.5) + 2; name = f"EPICO {name}"
    return Weapon(f"{name} (lv.{level})", atk * 5, atk, element, level, flavor, is_cursed, curse_effect, w_data.get("status_inflict"))

def generate_armor(level: int, is_epic: bool = False) -> Armor:
    a_data = random.choice(GAME_DATA["armors"])
    name, flavor = a_data["name"], a_data.get("flavor", "")
    defense = a_data["base_def"] + int(level * ARMOR_LEVEL_SCALING) + random.randint(0, 2)
    element = generate_random_element()
    
    is_cursed, curse_effect = False, ""
    if not is_epic and random.random() < CURSE_CHANCE:
        is_cursed = True
        curse_effect = random.choice(["hp_drain", "gold_drain", "heavy"])
        defense = int(defense * CURSE_STAT_MULTIPLIER)

    if element == "Normale": defense = int(defense * 1.2) + 1
    if is_epic: defense = int(defense * 1.5) + 2; name = f"EPICO {name}"
    return Armor(f"{name} (lv.{level})", defense * 8, defense, element, level, flavor, is_cursed, curse_effect)

def generate_accessory(level: int) -> Accessory:
    a_data = random.choice(GAME_DATA["accessories"])
    is_cursed, curse_effect = False, ""
    bonus_val = a_data["bonus_value"]
    if random.random() < CURSE_CHANCE:
        is_cursed = True
        curse_effect = random.choice(["hp_drain", "gold_drain"])
        bonus_val = int(bonus_val * 2)
    return Accessory(a_data["name"], a_data["base_val"] + (level*10), a_data.get("element", "Normale"), a_data["bonus_type"], bonus_val, a_data["desc"], a_data.get("lore", ""), is_cursed, curse_effect)

# Solo questi consumabili curano davvero: gli altri non mostrano "(Cura N)" nel nome
HEALING_CATEGORIES = ("heal", "antidote")

def consumable_name(name: str, heal: int, category: str) -> str:
    return f"{name} (Cura {heal})" if heal > 0 and category in HEALING_CATEGORIES else name

def generate_potion(level: int) -> Consumable:
    c_data = random.choice(GAME_DATA["consumables"])
    cat = c_data.get("category", "heal")
    heal = c_data["base_heal"] + (level * 5) if cat in HEALING_CATEGORIES else 0
    val = c_data["val_base"] + (level * 15)
    val = int(val * 1.5) # Rende le pozioni molto più costose
    return Consumable(consumable_name(c_data["name"], heal, cat), val, heal, cat)

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
        self.max_hp = data["max_hp"] + (PROFILE_MANAGER.get_perk("hp_lvl", 0) * 15)
        self.hp = self.max_hp
        self.gold = data["gold"] + (PROFILE_MANAGER.get_perk("gold_lvl", 0) * 20)
        self.base_acc, self.base_dodge = data["acc"], data["dodge"]
        self.active_pacts = active_pacts
        self.relic_ids = []
        self.relics = []
        self.relic_effects = []
        self.max_relics = 4
        self.bonus_atk_relic = 0
        self.statuses: Dict[str, int] = {}
        self.quest_items: List[str] = []
        
        self.exp_multiplier = 1.0
        self.bonus_def = 0
        self.base_crit = data.get("crit", 0)
        self.base_lifesteal = 0
        # Effetti personali (Maestria della propria classe) e bonus globali (Maestrie di tutte le classi), definiti in classes.json
        self.mastery_effects = self._own_mastery_effects(class_id)
        global_bonus = self._global_mastery_bonuses()
        self.bonus_def += global_bonus.get("def", 0)
        self.base_dodge += global_bonus.get("dodge", 0)
        self.exp_multiplier += global_bonus.get("exp", 0)
        self.max_hp += global_bonus.get("max_hp", 0)
        self.base_acc += global_bonus.get("acc", 0)
        self.base_crit += global_bonus.get("crit", 0)
        self.base_lifesteal += global_bonus.get("lifesteal", 0)
        self.hp = self.max_hp
        
        self.trait = GAME_DATA["meta"]["traits"][trait_id]
        self.trait_name = self.trait["name"]
        self.cursed, self.midas, self.ethereal_hunter, self.benedetto_save = False, False, False, False
        self.aristocrat = False
        self._apply_trait(trait_id)
        
        self.base_dodge += PROFILE_MANAGER.get_perk("dodge_lvl", 0) * 2
        self.base_acc += PROFILE_MANAGER.get_perk("acc_lvl", 0) * 3
        self.exp_multiplier += PROFILE_MANAGER.get_perk("exp_lvl", 0) * 0.05
        
        self.inventory = []
        self._load_starting_items()
        
        start_weapon_lv = 2 if self.has_mastery_effect("heavy_hand") else 1
        self.thief_save = self.has_mastery_effect("thief_potion_save")
        self.alchemist_potions = self.has_mastery_effect("alchemist_potions")
        self.assassin_ambush = self.has_mastery_effect("assassin_ambush")
        self.necro_harvest = self.has_mastery_effect("necro_harvest")

        self.level, self.exp, self.max_exp = 1, 0, 100
        self.escaped = False
        self.won = False
        self.run_tracker = {"escapes": 0, "fusions": 0, "no_hit_boss_done": False, "kill_1_hp_done": False, "floor_attacks": 0, "floor_hits": 0}
        self.essence_gathered, self.bosses_killed = 0, 0
        
        w_data = data["weapon"]
        self.weapon = Weapon(w_data["name"], w_data["value"], w_data["atk"], w_data.get("element", "Normale"), 1) if start_weapon_lv == 1 else generate_weapon(2)
        self.weapon.atk += PROFILE_MANAGER.get_perk("artigiano_lvl", 0) + (50 if self.cursed else 0)
        self.weapon.atk += global_bonus.get("weapon_atk", 0)
        self.temp_dodge = 0
        self.temp_def = 0
        self.temp_acc = 0
        
        a_data = data["armor"]
        self.armor = Armor(a_data["name"], a_data["value"], a_data["def"] + PROFILE_MANAGER.get_perk("pelle_dura_lvl", 0), a_data.get("element", "Normale"), 1)
        self.accessory = None
        
        potions_count = data["potions"] + (1 if PROFILE_MANAGER.get_perk("farmacista", False) else 0)
        self.inventory.extend([generate_potion(1) for _ in range(potions_count)])
        
        if PROFILE_MANAGER.get_perk("altare_benedizione", False):
            r = get_random_relic(self)
            if r: self.add_relic(r)

    @staticmethod
    def _own_mastery_effects(class_id: str) -> set:
        lvl = PROFILE_MANAGER.get_class_lvl(class_id, 1)
        mastery = RAW_DATA["classes"][class_id].get("mastery", {})
        return {m["effect"] for m_lvl, m in mastery.items() if m.get("effect") and lvl >= int(m_lvl)}

    @staticmethod
    def _global_mastery_bonuses() -> dict:
        totals = {}
        for c_id, c in RAW_DATA["classes"].items():
            lvl = PROFILE_MANAGER.get_class_lvl(c_id, 1)
            for m_lvl, m in c.get("mastery", {}).items():
                bonus = m.get("bonus")
                if m.get("type") == "global" and bonus and lvl >= int(m_lvl):
                    totals[bonus["stat"]] = totals.get(bonus["stat"], 0) + bonus["value"]
        return totals

    def has_mastery_effect(self, effect: str) -> bool:
        return effect in self.mastery_effects

    def _apply_trait(self, trait_id: str):
        def _maledetto(): self.max_hp //= 2; self.hp = self.max_hp; self.cursed = True
        def _midas(): self.midas = True
        def _aristocratico(): self.gold += 500; self.aristocrat = True
        def _cacciatore(): self.base_dodge -= 20; self.ethereal_hunter = True
        def _titano(): self.max_hp += 100; self.hp += 100; self.base_acc //= 2; self.base_dodge //= 2
        def _benedetto():
            self.benedetto_save = True
            r = next((x for x in GAME_DATA["relics"] if x["id"] == "scudo_cristallo"), None)
            if r: self.add_relic(r)
        
        traits_map = {
            "maledetto": _maledetto, "midas": _midas, "aristocratico": _aristocratico,
            "cacciatore_etereo": _cacciatore, "titano": _titano, "benedetto": _benedetto
        }
        if trait_id in traits_map: traits_map[trait_id]()

    def _load_starting_items(self):
        # Il valore di vendita usa la stessa scala degli oggetti generati quando i dati non lo indicano
        mapping = [
            ("starting_consumables", "consumables", lambda d: Consumable(consumable_name(d["name"], d["base_heal"], d.get("category", "heal")), d["val_base"], d["base_heal"], d.get("category", "heal"))),
            ("starting_weapons", "weapons", lambda d: Weapon(d["name"], d.get("val_base", d["base_atk"] * 5), d["base_atk"], "Normale", 1, status_inflict=d.get("status_inflict"))),
            ("starting_armors", "armors", lambda d: Armor(d["name"], d.get("val_base", d["base_def"] * 8), d["base_def"], "Normale", 1)),
            ("starting_accessories", "accessories", lambda d: Accessory(d["name"], d.get("base_val", d.get("val_base", 0)), d.get("element", "Normale"), d["bonus_type"], d["bonus_value"], d["desc"], d.get("lore", "")))
        ]
        for key, game_data_key, builder in mapping:
            # Svuota subito la lista acquistata: un oggetto difettoso non deve bloccare tutte le partite successive
            for item_name in PROFILE_MANAGER._data.pop(key, []) or []:
                item_data = next((x for x in GAME_DATA[game_data_key] if x["name"] == item_name), None)
                try:
                    if item_data: self.inventory.append(builder(item_data))
                except (KeyError, TypeError, ValueError) as e:
                    display_msg(f"{Colors.RED}Impossibile preparare {item_name} ({e}): l'oggetto viene saltato.{Colors.RESET}")
            PROFILE_MANAGER._data[key] = []

    def add_relic(self, relic):
        if len(self.relic_ids) >= self.max_relics:
            display_msg(f"\n{Colors.YELLOW}Non puoi trasportare più di {self.max_relics} Reliquie. Devi sostituirne una!{Colors.RESET}")
            for i, r_id in enumerate(self.relic_ids):
                r_name = next((x["name"] for x in GAME_DATA["relics"] if x["id"] == r_id), r_id)
                display_msg(f"{i+1}. {r_name}")
            display_msg(f"0. Rinuncia alla nuova reliquia ({relic['name']})")
            
            while True:
                choice = get_choice("Quale reliquia vuoi scartare? > ")
                if choice == '0':
                    display_msg(f"{Colors.CYAN}Hai rinunciato a {relic['name']}.{Colors.RESET}")
                    return
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(self.relic_ids):
                        old_id = self.relic_ids[idx]
                        old_name = next((x["name"] for x in GAME_DATA["relics"] if x["id"] == old_id), old_id)
                        display_msg(f"{Colors.RED}Hai distrutto {old_name} per fare spazio!{Colors.RESET}")
                        # Remove old
                        self.relic_ids.pop(idx)
                        self.relics.pop(idx)
                        self.relic_effects.pop(idx).on_unequip(self)
                        break
                    else: display_msg(f"{Colors.RED}Scelta non valida.{Colors.RESET}")
                except ValueError: pass
                
        self.relics.append(relic)
        self.relic_ids.append(relic["id"])
        effect = create_relic_effect(relic["id"])
        self.relic_effects.append(effect)
        effect.on_equip(self)
        display_msg(f"\n{Colors.MAGENTA}🌟 Hai ottenuto la Reliquia: {relic['name']}!{Colors.RESET}")
        display_msg(f"Effetto: {relic['desc']}")
        if "lore" in relic: display_msg(f"{Colors.YELLOW}Lore: {relic['lore']}{Colors.RESET}")

    def get_total_atk(self): return self.weapon.atk + self.bonus_atk_relic

    def get_crit_chance(self) -> int:
        crit = self.base_crit
        if self.accessory and self.accessory.bonus_type == "crit_chance": crit += self.accessory.bonus_value
        return min(100, crit)

    def get_lifesteal(self) -> int:
        ls = self.base_lifesteal
        if self.accessory and self.accessory.bonus_type == "lifesteal": ls += self.accessory.bonus_value
        return ls

    def get_hit_chance(self, enemy_dodge: int = 0, multiplier: float = 1.0) -> int:
        """Probabilità reale di colpire (in %), la stessa usata in combattimento."""
        hit = BASE_HIT_CHANCE + self.base_acc + self.temp_acc - enemy_dodge + (15 if multiplier > 1.0 else -20 if multiplier < 1.0 else 0)
        hit += self.weapon.get_hit_chance_modifier()
        for r in self.relic_effects: hit += r.get_acc_modifier()
        return max(10, min(100, hit))

    def get_total_def(self) -> int:
        return self.armor.defense + self.temp_def + self.bonus_def + get_archive_bonus("def", PROFILE_MANAGER._data)
    
    def get_dodge(self): 
        dodge = self.base_dodge + self.temp_dodge
        for effect in self.relic_effects: dodge += effect.get_dodge_modifier()
        if self._berserker_fury_active(): return 0
        if self.has_curse("heavy"): dodge -= 15
        return max(0, dodge)

    def _get_resonance_element(self):
        if self.weapon.element != "Normale" and self.weapon.element == self.armor.element:
            return self.weapon.element
        return None

    def has_curse(self, curse_type: str) -> bool:
        for item in [self.weapon, self.armor, self.accessory]:
            if item and getattr(item, 'is_cursed', False) and getattr(item, 'curse_effect', "") == curse_type:
                return True
        return False

    def gain_exp(self, amount: int):
        if self.midas: return
        multi = self.exp_multiplier
        for effect in self.relic_effects: multi += effect.get_exp_modifier()
        amount = int(amount * multi)
        self.exp += amount
        display_msg(f"{Colors.CYAN}Ottieni {amount} EXP! ({self.exp}/{self.max_exp}){Colors.RESET}")
        while self.exp >= self.max_exp:
            self.exp -= self.max_exp
            self.level += 1; self.max_exp = int(self.max_exp * 1.5)
            self.max_hp += 15
            self.heal(self.max_hp)
            self.base_acc += 2; self.base_dodge += 2
            display_msg(f"\n{Colors.YELLOW}{Colors.BOLD}*** LEVEL UP! Sei salito al livello {self.level}! ***{Colors.RESET}")

    def heal(self, amount: int) -> int:
        if self.cursed:
            return 0
        for r in self.relic_effects: amount = r.on_heal(self, amount)
        actual_heal = min(amount, self.max_hp - self.hp)
        self.hp += actual_heal
        return actual_heal

    def calculate_gold_gain(self, base_gold: int) -> int:
        g = base_gold * 3 if self.midas else base_gold
        for r in self.relic_effects: g = r.on_gold_gain(self, g)
        g = int(g * (1 + PROFILE_MANAGER.get_perk("banca_anima_lvl", 0) * 0.05))
        g = int(g * (1 + get_archive_bonus("gold_pct", PROFILE_MANAGER._data) / 100))
        return g

    def take_damage(self, amount: int) -> bool:
        self.hp -= amount
        if self.hp <= 0 and self.benedetto_save:
            self.hp = 1
            self.benedetto_save = False
            self.run_tracker["1_hp_survive"] = True
            display_msg(f"{Colors.YELLOW}La Benedizione ti salva dal colpo letale!{Colors.RESET}")
        return self.hp > 0

    def get_class_damage_multiplier(self) -> float:
        return 1.5 if self._berserker_fury_active() else 1.0

    def _berserker_fury_active(self) -> bool:
        return self.has_mastery_effect("berserker_fury") and self.hp < self.max_hp * 0.3

    def on_defense_started(self):
        if self.has_mastery_effect("paladin_bulwark"):
            if self.heal(3) > 0: display_msg(f"{Colors.GREEN}Baluardo della Fede: Recuperi 3 HP!{Colors.RESET}")

    def on_attack_landed(self, dmg_dealt: int, multiplier: float):
        if self.has_mastery_effect("mage_attunement") and multiplier > 1.0:
            h = max(1, dmg_dealt // 10)
            self.heal(h)
            display_msg(f"{Colors.MAGENTA}Sintonia: Assorbi {h} HP!{Colors.RESET}")
            
    def get_defense_action(self) -> tuple[str, str]:
        if self.role in ["Guerriero", "Berserker"]:
            return "counter", "Difesa Aggressiva (Dimezza danni e Contrattacca)"
        elif self.role in ["Ladro", "Assassino"]:
            return "focus", "Concentrazione (Dimezza danni, prossimo colpo Critico 100%)"
        else:
            return "recovery", "Riparo Magico (Dimezza danni e Cura 5% HP)"

def pick_enemy_name(floor: int, is_boss: bool, final: bool = False) -> str:
    """Sceglie un nemico adatto alla profondità: più si scende, più forti sono i candidati."""
    pool = GAME_DATA["bosses" if is_boss else "enemies"]
    if final:
        finals = [n for n, d in pool.items() if d.get("final_boss")]
        if finals: return random.choice(finals)
    ranked = sorted((n for n, d in pool.items() if not d.get("final_boss")), key=lambda n: pool[n]["base_hp"] * pool[n]["base_atk"])
    window = min(len(ranked), BOSS_DEPTH_WINDOW if is_boss else ENEMY_DEPTH_WINDOW)
    progress = min(1.0, max(0.0, (floor - 1) / (INFINITE_MODE_THRESHOLD - 1)))
    lo = round(progress * (len(ranked) - 1) - (window - 1) / 2)
    lo = max(0, min(lo, len(ranked) - window))
    return random.choice(ranked[lo:lo + window])

class Enemy:
    def __init__(self, floor: int, is_boss: bool, active_pacts: List[str], modifier: str = "normal", final: bool = False):
        self.is_boss = is_boss
        self.modifier = modifier
        category = "bosses" if is_boss else "enemies"
        self.name = pick_enemy_name(floor, is_boss, final)
        data = GAME_DATA[category][self.name]
        
        self.element, self.base_acc, self.base_dodge = data["element"], data["base_acc"], data["base_dodge"]
        self.title = data.get("title", "")
        self.lore = data.get("lore", "")
        self.status_inflict = data.get("status_inflict", None)
        self.statuses: Dict[str, int] = {}
        
        lvl_scale = floor - 1
        if is_boss:
            self.hp = data["base_hp"] + int(lvl_scale * 8) + random.randint(0, 10)
            self.atk = data["base_atk"] + int(lvl_scale * 2.5) + random.randint(0, 2)
            self.gold_drop, self.exp_drop = 50 + (floor * 15), 150 + (floor * 20)
        else:
            self.hp = data["base_hp"] + int(lvl_scale * 5) + random.randint(-5, 5)
            self.atk = data["base_atk"] + int(lvl_scale * 1.0) + random.randint(0, 1)
            self.gold_drop, self.exp_drop = max(5, 5 + int(floor * 3.5)), 30 + (floor * 10)
            
        if floor >= 10:
            self.hp = int(self.hp * 1.2)
            self.atk = int(self.atk * 1.2)
        if floor >= 20:
            self.hp = int(self.hp * 1.25)
            self.atk = int(self.atk * 1.25)
            
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

