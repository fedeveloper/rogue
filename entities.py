import random
from typing import List, Dict
from ui import Colors, delay_print, clear_screen, display_msg, interactive_menu
from data_manager import GAME_DATA, RAW_DATA, PROFILE_MANAGER, ELEMENTS, MULTIPLIERS, cycle_of, echo_name, get_biome, get_element_icon
from relic_effects import create_relic_effect
from archive import get_archive_bonus
from codex import record_relic
import modes
import runes as rune_rules
import attributes
import magic
from constants import BASE_HIT_CHANCE, ENEMY_DEPTH_WINDOW, BOSS_DEPTH_WINDOW, INFINITE_MODE_THRESHOLD, CURSE_CHANCE, CURSE_STAT_MULTIPLIER, BOSS_HP_MULT, BOSS_ATK_MULT, ENEMY_HP_PER_FLOOR, ENEMY_ATK_PER_FLOOR, BULWARK_HEAL_PCT, WEAPON_TARGET_HITS, ARMOR_TARGET_ABSORB, WEAPON_QUALITY, ARMOR_QUALITY, NORMAL_ELEMENT_BONUS, EPIC_MULTIPLIER

class Item:
    def __init__(self, name: str, value: int, item_type: str, level: int = 1, flavor: str = "", is_cursed: bool = False, curse_effect: str = "", element: str = "Normale"):
        self.name, self.value, self.type, self.level, self.flavor = name, value, item_type, level, flavor
        self.is_cursed, self.curse_effect, self.element = is_cursed, curse_effect, element
        self.refresh_display_name()

    def refresh_display_name(self):
        cursed_tag = f"{Colors.MAGENTA}[MALEDETTO]{Colors.RESET} " if self.is_cursed else ""
        el_tag = f" [{get_element_icon(self.element)}]" if self.element != "Normale" and self.element != "" else ""
        self.display_name = f"{cursed_tag}{self.name}{el_tag}{rune_rules.socket_tag(self)}"

# Gli ultimi quattro nascono dalle reazioni elementali e colpiscono solo i nemici
STATUS_NAMES = {"poison": "Veleno", "bleed": "Sanguinamento", "stun": "Gelo", "blind": "Accecato", "slow": "Impantanato", "scorch": "Magma"}

# Proprietà speciali di un'arma che weapons.json può definire
WEAPON_TRAIT_KEYS = ("hit_modifier", "crit_chance", "gold_atk_per", "gold_atk_max", "dodge_bonus", "guard_break", "shield_mult")

class Weapon(Item):
    def __init__(self, name: str, value: int, atk: int, element: str, level: int, flavor: str = "", is_cursed: bool = False, curse_effect: str = "", status_inflict: dict = None, traits: dict = None):
        self.sockets, self.runes = rune_rules.rules()["sockets"]["normal"], []  # incastoni e rune incastonate
        super().__init__(name, value, "weapon", level, flavor, is_cursed, curse_effect, element)
        self.atk = atk
        # Stesso formato di status_inflict dei nemici: {"type", "chance", "duration"}
        self.status_inflict = status_inflict
        self.traits = {k: v for k, v in (traits or {}).items() if k in WEAPON_TRAIT_KEYS}

    def get_hit_chance_modifier(self) -> int:
        return self.traits.get("hit_modifier", 0)

    def get_gold_atk_bonus(self, gold: int) -> int:
        """Armi come lo Zweihander d'Oro: +1 ATK ogni gold_atk_per Oro posseduto, fino a gold_atk_max."""
        per = self.traits.get("gold_atk_per")
        if not per: return 0
        return min(self.traits.get("gold_atk_max", 999), max(0, gold) // per)

    def trait_text(self) -> str:
        """Le proprietà speciali dell'arma in breve, per lo zaino e le statistiche ("" se non ne ha)."""
        t, parts = self.traits, []
        if t.get("hit_modifier"): parts.append(f"{t['hit_modifier']:+d}% Precisione")
        if t.get("crit_chance"): parts.append(f"{t['crit_chance']}% critico")
        if t.get("dodge_bonus"): parts.append(f"{t['dodge_bonus']:+d}% Schivata")
        if t.get("guard_break"): parts.append("sfonda la Guardia")
        if t.get("shield_mult"): parts.append(f"scudi ×{t['shield_mult']}")
        if self.status_inflict: parts.append(f"{self.status_inflict['chance']}% {STATUS_NAMES[self.status_inflict['type']]}")
        if t.get("gold_atk_per"): parts.append(f"+1 ATK ogni {t['gold_atk_per']} Oro")
        return ", ".join(parts)

    def on_attack(self, dmg_dealt: int, eff: str) -> tuple[int, str]:
        crit = self.traits.get("crit_chance", 0)
        if crit and random.randint(1, 100) <= crit:
            return dmg_dealt * 2, eff + f" {Colors.MAGENTA}[CRITICO!]{Colors.RESET}"
        return dmg_dealt, eff

class Armor(Item):
    def __init__(self, name: str, value: int, defense: int, element: str, level: int, flavor: str = "", is_cursed: bool = False, curse_effect: str = "", dodge_bonus: int = 0):
        self.sockets, self.runes = rune_rules.rules()["sockets"]["normal"], []
        super().__init__(name, value, "armor", level, flavor, is_cursed, curse_effect, element)
        self.defense = defense
        self.dodge_bonus = dodge_bonus

class Accessory(Item):
    def __init__(self, name: str, value: int, element: str, bonus_type: str, bonus_value: int, desc: str, flavor: str = "", is_cursed: bool = False, curse_effect: str = ""):
        super().__init__(name, value, "accessory", 1, flavor, is_cursed, curse_effect, element)
        self.bonus_type, self.bonus_value, self.desc = bonus_type, bonus_value, desc

class Rune(Item):
    """Una runa nello zaino: si incastona al Falò in un'arma o in un'armatura (vedi runes.py)."""
    def __init__(self, rune_id: str, floor: int = 1):
        data = rune_rules.rune(rune_id)
        super().__init__(f"{data['icon']} {data['name']}", rune_rules.item_value(rune_id, floor), "rune")
        self.rune_id, self.desc = rune_id, data["desc"]


class Scroll(Item):
    """Una pergamena nello zaino: leggendola si impara il suo incantesimo (vedi magic.py)."""
    def __init__(self, spell_id: str, floor: int = 1):
        data = magic.spell(spell_id)
        super().__init__(f"📜 Pergamena: {data['name']}", magic.scroll_value(floor), "scroll")
        self.spell_id, self.desc = spell_id, data["desc"]


def generate_scroll(floor: int, spell_id: str = "") -> "Scroll":
    return Scroll(spell_id or random.choice(magic.available()), floor)


def generate_rune(floor: int, rune_id: str = "") -> "Rune":
    return Rune(rune_id or rune_rules.random_rune_id(), floor)


def set_sockets(item, kind: str, at_least: int = 0):
    """Incastoni di un oggetto generato: normale, epico o premio di un boss (e almeno quelli dei suoi dati)."""
    item.sockets = max(rune_rules.rules()["sockets"][kind], at_least)
    item.refresh_display_name()
    return item


class Consumable(Item):
    def __init__(self, name: str, value: int, heal_amount: int, category: str = "heal"):
        super().__init__(name, value, "consumable", 1)
        self.heal_amount = heal_amount
        self.category = category
        self.display_name = name

def generate_random_element() -> str:
    if random.random() < 0.4: return "Normale"
    return random.choice([e for e in ELEMENTS if e != "Normale"])

def floor_multiplier(floor: int) -> float:
    """I salti di forza dei nemici ai piani 10 e 20 (vedi Enemy)."""
    return (1.2 if floor >= 10 else 1.0) * (1.25 if floor >= 20 else 1.0)


_TYPICAL = {}

def generic_base(floor: int) -> tuple:
    """(HP, ATK) di base medi dei nemici generici nella finestra di profondità del piano, senza crescita."""
    pool = {n: d for n, d in RAW_DATA["enemies"].items() if "biome" not in d and "lair" not in d}
    ranked = sorted(pool, key=lambda n: pool[n]["base_hp"] * pool[n]["base_atk"])
    window = min(len(ranked), ENEMY_DEPTH_WINDOW)
    progress = min(1.0, (max(1, floor) - 1) / (INFINITE_MODE_THRESHOLD - 1))
    lo = max(0, min(round(progress * (len(ranked) - 1) - (window - 1) / 2), len(ranked) - window))
    names = ranked[lo:lo + window]
    return sum(pool[n]["base_hp"] for n in names) / window, sum(pool[n]["base_atk"] for n in names) / window

def typical_enemy(floor: int) -> tuple:
    """(HP, ATK) attesi di un nemico normale al piano: media della finestra di profondità, crescita e salti di piano."""
    floor = max(1, floor)
    if floor not in _TYPICAL:
        base_hp, base_atk = generic_base(floor)
        hp = (base_hp + int((floor - 1) * ENEMY_HP_PER_FLOOR)) * floor_multiplier(floor)
        atk = (base_atk + int((floor - 1) * ENEMY_ATK_PER_FLOOR) + 0.5) * floor_multiplier(floor)
        _TYPICAL[floor] = (hp, atk)
    return _TYPICAL[floor]

def echo_native_base(data: dict) -> tuple:
    """Le statistiche di base di un nativo quando il suo bioma torna in un'Eco: forte, rispetto ai nemici più profondi,
    quanto lo era rispetto ai generici dei piani del suo bioma."""
    lo, hi = next(b["floors"] for b in RAW_DATA["biomes"] if b["id"] == data["biome"])
    home = [generic_base(lo), generic_base(hi)]
    home_hp, home_atk = sum(h for h, _ in home) / 2, sum(a for _, a in home) / 2
    deep_hp, deep_atk = generic_base(INFINITE_MODE_THRESHOLD)
    return round(data["base_hp"] * deep_hp / home_hp), round(data["base_atk"] * deep_atk / home_atk)


def boss_quality(data: dict) -> tuple:
    """Qualità (HP, ATK) di un boss rispetto alla media dei boss: 0.75 + 0.25 · base / media."""
    bosses = [d for d in RAW_DATA["bosses"].values()]
    mean_hp = sum(d["base_hp"] for d in bosses) / len(bosses)
    mean_atk = sum(d["base_atk"] for d in bosses) / len(bosses)
    return 0.75 + 0.25 * data["base_hp"] / mean_hp, 0.75 + 0.25 * data["base_atk"] / mean_atk


def _quality(base: float, rule: tuple) -> float:
    return rule[0] + base / rule[1]


def generate_weapon(level: int, is_epic: bool = False) -> Weapon:
    w_data = random.choice(GAME_DATA["weapons"])
    name, flavor = w_data["name"], w_data.get("flavor", "")
    hp, _ = typical_enemy(level)
    power = hp / WEAPON_TARGET_HITS * _quality(w_data["base_atk"], WEAPON_QUALITY) * random.uniform(0.9, 1.1)
    # Le armi a tema (es. il Bastone dell'Alba) hanno sempre il loro elemento
    element = w_data.get("element") or generate_random_element()
    
    is_cursed, curse_effect = False, ""
    if not is_epic and random.random() < CURSE_CHANCE * modes.rule("curse_chance_mult"):
        is_cursed = True
        curse_effect = random.choice(["hp_drain", "gold_drain"])
        power *= CURSE_STAT_MULTIPLIER
        
    if element == "Normale": power *= NORMAL_ELEMENT_BONUS
    if is_epic: power *= EPIC_MULTIPLIER; name = f"EPICO {name}"
    atk = max(1, round(power))
    w = Weapon(f"{name} (lv.{level})", atk * 5, atk, element, level, flavor, is_cursed, curse_effect, w_data.get("status_inflict"), w_data)
    return set_sockets(w, "epic" if is_epic else "normal", w_data.get("sockets", 0))

def generate_armor(level: int, is_epic: bool = False) -> Armor:
    a_data = random.choice(GAME_DATA["armors"])
    name, flavor = a_data["name"], a_data.get("flavor", "")
    _, atk = typical_enemy(level)
    power = atk * ARMOR_TARGET_ABSORB * _quality(a_data["base_def"], ARMOR_QUALITY) * random.uniform(0.9, 1.1)
    element = a_data.get("element") or generate_random_element()
    
    is_cursed, curse_effect = False, ""
    if not is_epic and random.random() < CURSE_CHANCE * modes.rule("curse_chance_mult"):
        is_cursed = True
        curse_effect = random.choice(["hp_drain", "gold_drain", "heavy"])
        power *= CURSE_STAT_MULTIPLIER

    if element == "Normale": power *= NORMAL_ELEMENT_BONUS
    if is_epic: power *= EPIC_MULTIPLIER; name = f"EPICO {name}"
    defense = max(1, round(power))
    a = Armor(f"{name} (lv.{level})", defense * 8, defense, element, level, flavor, is_cursed, curse_effect, a_data.get("dodge_bonus", 0))
    return set_sockets(a, "epic" if is_epic else "normal", a_data.get("sockets", 0))

def generate_accessory(level: int) -> Accessory:
    a_data = random.choice(GAME_DATA["accessories"])
    is_cursed, curse_effect = False, ""
    bonus_val = a_data["bonus_value"]
    desc = a_data["desc"]
    if random.random() < CURSE_CHANCE * modes.rule("curse_chance_mult"):
        is_cursed = True
        curse_effect = random.choice(["hp_drain", "gold_drain"])
        bonus_val = int(bonus_val * 2)
        # La maledizione raddoppia il bonus: la descrizione deve mostrare il valore reale
        desc = desc.replace(str(a_data["bonus_value"]), str(bonus_val), 1)
    return Accessory(a_data["name"], a_data["base_val"] + (level*10), a_data.get("element", "Normale"), a_data["bonus_type"], bonus_val, desc, a_data.get("lore", ""), is_cursed, curse_effect)

# Solo questi consumabili curano davvero: gli altri non mostrano "(Cura N)" nel nome
HEALING_CATEGORIES = ("heal", "antidote")

def consumable_name(name: str, heal: int, category: str) -> str:
    return f"{name} (Cura {heal})" if heal > 0 and category in HEALING_CATEGORIES else name

CONSUMABLE_WEIGHT = 10  # peso di un consumabile senza "weight" nei dati: il Tomo dell'Oblio ha 1, quindi è raro

def generate_potion(level: int) -> Consumable:
    pool = GAME_DATA["consumables"]
    c_data = random.choices(pool, weights=[c.get("weight", CONSUMABLE_WEIGHT) for c in pool])[0]
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
        self.chronicle = []  # momenti chiave della discesa, per l'Epitaffio (vedi epitaph.note)
        self.class_id = class_id
        data = RAW_DATA["classes"][class_id]
        
        self.role = data["role"]
        self.defense = data["defense"]  # la tecnica di difesa della classe (defenses.json)
        self.max_hp = data["max_hp"] + (PROFILE_MANAGER.get_perk("hp_lvl", 0) * 15)
        # Attributi (attributes.py): quelli della classe, e i punti da spendere che arrivano a ogni livello
        self.attributes = attributes.starting(class_id)
        self.unspent_points, self.points_offered = 0, True
        self.max_hp += attributes.value(self, "max_hp")
        # Magia (magic.py): gli incantesimi della classe e l'Etere, pieno all'inizio della discesa
        self.base_ether, self.spells = data.get("ether", 0), list(data.get("spells", []))
        self.ether = self.max_ether()
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
        self.seen_events: set = set()  # eventi già incontrati in questa run
        self.run_flags: set = set()  # scelte che valgono solo per la discesa in corso
        self.pending_events: list = []  # [piano, evento] richiamati da scelte passate
        self.fallen = False  # Caduta Astrale: il piano finisce e si scende subito al successivo
        self.dissolved = 0  # HP massimi tolti dalla Dissoluzione dell'Io, resi all'uscita dal bioma
        self.biome_id = None
        self.audacity = 0  # rischi corsi nel piano: fanno crescere il bottino del boss
        self.corruption = 0  # 0-100: cresce con le scelte oscure, vale per la sola discesa
        
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
        
        self.trait_id = trait_id
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
        self.nemeses_met = set()  # Nemesi già comparse in questa discesa
        self.ascension, self.daily = 0, None  # grado di Ascensione e Sfida del Giorno della discesa (vedi modes)
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
            ("starting_weapons", "weapons", lambda d: Weapon(d["name"], d.get("val_base", d["base_atk"] * 5), d["base_atk"], d.get("element", "Normale"), 1, status_inflict=d.get("status_inflict"), traits=d)),
            ("starting_armors", "armors", lambda d: Armor(d["name"], d.get("val_base", d["base_def"] * 8), d["base_def"], d.get("element", "Normale"), 1, dodge_bonus=d.get("dodge_bonus", 0))),
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
            # Stessi comandi del resto del gioco: frecce e Invio, nessun numero da digitare
            prompt = (f"\n{Colors.YELLOW}Non puoi trasportare più di {self.max_relics} Reliquie. Devi sostituirne una!{Colors.RESET}\n"
                      f"Nuova reliquia: {Colors.MAGENTA}{relic['name']}{Colors.RESET} — {relic['desc']}\nQuale reliquia vuoi scartare?")
            options = [f"Scarta {r['name']} ({r['desc']})" for r in self.relics]
            options.append(f"Rinuncia alla nuova reliquia ({relic['name']})")
            idx = interactive_menu(options, prompt)
            if idx == len(options) - 1:
                display_msg(f"{Colors.CYAN}Hai rinunciato a {relic['name']}.{Colors.RESET}")
                return
            display_msg(f"{Colors.RED}Hai distrutto {self.relics[idx]['name']} per fare spazio!{Colors.RESET}")
            self.relic_ids.pop(idx)
            self.relics.pop(idx)
            self.relic_effects.pop(idx).on_unequip(self)


        self.relics.append(relic)
        self.relic_ids.append(relic["id"])
        record_relic(relic["id"])
        self.chronicle.append({"kind": "relic", "name": relic["name"]})
        effect = create_relic_effect(relic["id"])
        self.relic_effects.append(effect)
        effect.on_equip(self)
        display_msg(f"\n{Colors.MAGENTA}🌟 Hai ottenuto la Reliquia: {relic['name']}!{Colors.RESET}")
        display_msg(f"Effetto: {relic['desc']}")
        if "lore" in relic: display_msg(f"{Colors.YELLOW}Lore: {relic['lore']}{Colors.RESET}")

    def add_corruption(self, amount: int) -> int:
        """Varia la Corruzione e ritorna la variazione reale. L'Altare della Purificazione riduce gli aumenti."""
        cfg = GAME_DATA["meta"]["corruption"]
        if amount > 0:
            altar = next((s for s in GAME_DATA["story"]["camp"]["structures"] if s["id"] == "altare_purificazione"), None)
            if altar and PROFILE_MANAGER.get_flag("camp_altare_purificazione"): amount = amount * altar["corruption_gain_pct"] // 100
        before = self.corruption
        self.corruption = max(0, min(cfg["max"], self.corruption + amount))
        return self.corruption - before

    def corruption_atk(self) -> int:
        return self.corruption // 10 * GAME_DATA["meta"]["corruption"]["atk_per_10"]

    def rune_value(self, key: str):
        """Somma di un effetto delle rune (e delle parole runiche) dell'arma e dell'armatura equipaggiate."""
        runes = sum(effects.get(key, 0) for item in (self.weapon, self.armor) for effects in rune_rules.item_effects(item))
        mult = 1 + sum(r.get_rune_multiplier() for r in self.relic_effects)
        return int(runes * mult) + sum(r.get_rune_bonus(key) for r in self.relic_effects)

    def get_total_atk(self):
        atk = self.weapon.atk + self.bonus_atk_relic + self.weapon.get_gold_atk_bonus(self.gold) + self.corruption_atk()
        for r in self.relic_effects: atk += r.get_atk_modifier(self)
        return atk + self.weapon.atk * self.rune_value("atk_pct") // 100

    def get_crit_chance(self) -> int:
        crit = self.base_crit + self.rune_value("crit_chance_add") + attributes.value(self, "crit")
        if self.accessory and self.accessory.bonus_type == "crit_chance": crit += self.accessory.bonus_value
        return min(100, crit)

    def get_lifesteal(self) -> int:
        ls = self.base_lifesteal
        if self.accessory and self.accessory.bonus_type == "lifesteal": ls += self.accessory.bonus_value
        return ls

    def get_hit_chance(self, enemy_dodge: int = 0, multiplier: float = 1.0) -> int:
        """Probabilità reale di colpire (in %), la stessa usata in combattimento."""
        hit = BASE_HIT_CHANCE + self.base_acc + attributes.value(self, "acc") + self.temp_acc - enemy_dodge + (15 if multiplier > 1.0 else -20 if multiplier < 1.0 else 0)
        hit += self.weapon.get_hit_chance_modifier()
        for r in self.relic_effects: hit += r.get_acc_modifier()
        return max(10, min(100, hit))

    def get_total_def(self) -> int:
        return (self.armor.defense + self.armor.defense * self.rune_value("def_pct") // 100 + self.temp_def + self.bonus_def
                + get_archive_bonus("def", PROFILE_MANAGER._data))
    
    def get_dodge(self): 
        dodge = self.base_dodge + attributes.value(self, "dodge") + self.temp_dodge + getattr(self.armor, "dodge_bonus", 0) + self.weapon.traits.get("dodge_bonus", 0) + self.rune_value("dodge_add")
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

    def max_ether(self) -> int:
        return self.base_ether + attributes.value(self, "ether_max")

    def gain_ether(self, amount: int) -> int:
        """Aggiunge Etere fino al massimo; restituisce quanto ne è entrato davvero."""
        gained = max(0, min(amount, self.max_ether() - self.ether))
        self.ether += gained
        return gained

    def gain_exp(self, amount: int):
        if self.midas: return
        multi = self.exp_multiplier + self.rune_value("exp_pct") / 100
        for effect in self.relic_effects: multi += effect.get_exp_modifier()
        amount = int(amount * multi)
        self.exp += amount
        display_msg(f"{Colors.CYAN}Ottieni {amount} EXP! ({self.exp}/{self.max_exp}){Colors.RESET}")
        while self.exp >= self.max_exp:
            self.exp -= self.max_exp
            self.level += 1; self.max_exp = int(self.max_exp * 1.5)
            growth = attributes.rules()["per_level"]
            self.max_hp += growth["max_hp"]
            self.heal(self.max_hp)
            self.base_acc += growth["acc"]; self.base_dodge += growth["dodge"]
            self.unspent_points += attributes.rules()["points_per_level"]
            self.points_offered = False
            display_msg(f"\n{Colors.YELLOW}{Colors.BOLD}*** LEVEL UP! Sei salito al livello {self.level}! ***{Colors.RESET}"
                        f"\n{Colors.YELLOW}Hai {self.unspent_points} punti abilità da spendere negli attributi.{Colors.RESET}")

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
        return g * (100 + self.rune_value("gold_pct") + attributes.value(self, "gold_pct")) // 100

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
            healed = self.heal(max(1, self.max_hp * BULWARK_HEAL_PCT // 100))
            if healed > 0: display_msg(f"{Colors.GREEN}Baluardo della Fede: Recuperi {healed} HP!{Colors.RESET}")

    def on_attack_landed(self, dmg_dealt: int, multiplier: float):
        if self.has_mastery_effect("mage_attunement") and multiplier > 1.0:
            h = max(1, dmg_dealt // 10)
            self.heal(h)
            display_msg(f"{Colors.MAGENTA}Sintonia: Assorbi {h} HP!{Colors.RESET}")
            
    def get_defense_action(self) -> tuple[str, str]:
        d = GAME_DATA["defenses"][self.defense]
        return self.defense, f"{d['name']} ({d['short']})"

def pick_enemy_name(floor: int, is_boss: bool, final: bool = False) -> str:
    """Sceglie un nemico adatto alla profondità: più si scende, più forti sono i candidati."""
    pool = GAME_DATA["bosses" if is_boss else "enemies"]
    if final:
        finals = [n for n, d in pool.items() if d.get("final_boss")]
        if finals: return random.choice(finals)
    biome = get_biome(floor)
    # Un boss il cui destino si è compiuto in una storia (es. Sir Alaric liberato) non torna più
    # Le creature legate a una stanza (es. il Mimic dei forzieri) non si incontrano mai per caso
    alive = {n: d for n, d in pool.items() if not d.get("final_boss") and "lair" not in d and not PROFILE_MANAGER.get_flag(d.get("retired_by_flag", ""))}
    # I nativi di un bioma vivono solo lì, e lì si aggiungono sempre ai candidati della profondità
    natives = [n for n, d in alive.items() if biome and d.get("biome") == biome["id"]]
    candidates = [n for n, d in alive.items() if "biome" not in d]
    ranked = sorted(candidates, key=lambda n: pool[n]["base_hp"] * pool[n]["base_atk"])
    window = min(len(ranked), BOSS_DEPTH_WINDOW if is_boss else ENEMY_DEPTH_WINDOW)
    progress = min(1.0, max(0.0, (floor - 1) / (INFINITE_MODE_THRESHOLD - 1)))
    lo = round(progress * (len(ranked) - 1) - (window - 1) / 2)
    lo = max(0, min(lo, len(ranked) - window))
    picks = ranked[lo:lo + window] + natives
    affinity = (biome or {}).get("enemy_elements", {})
    return random.choices(picks, weights=[affinity.get(pool[n]["element"], 1) for n in picks])[0]

class Enemy:
    def __init__(self, floor: int, is_boss: bool, active_pacts: List[str], modifier: str = "normal", final: bool = False, name: str = ""):
        self.is_boss = is_boss
        self.modifier = modifier
        category = "bosses" if is_boss else "enemies"
        self.name = name or pick_enemy_name(floor, is_boss, final)
        self.base_name = self.name  # senza i suffissi (Potenziato)/(Debilitato): è la voce del Bestiario
        data = GAME_DATA[category][self.name]
        
        self.element, self.base_acc, self.base_dodge = data["element"], data["base_acc"], data["base_dodge"]
        self.title = data.get("title", "")
        self.lore = data.get("lore", "")
        self.status_inflict = data.get("status_inflict", None)
        self.statuses: Dict[str, int] = {}
        
        lvl_scale = floor - 1
        if is_boss:
            hp, atk = typical_enemy(floor)
            q_hp, q_atk = boss_quality(data)
            # typical_enemy include già i salti di forza dei piani 10 e 20: qui si tolgono per non applicarli due volte
            self.hp = int(hp * BOSS_HP_MULT * q_hp / floor_multiplier(floor)) + random.randint(0, 10)
            self.atk = int(atk * BOSS_ATK_MULT * q_atk / floor_multiplier(floor)) + random.randint(0, 2)
            self.gold_drop, self.exp_drop = 50 + (floor * 15), 150 + (floor * 20)
        elif data.get("lair"):
            # Forte quanto il nemico tipico del piano, qualunque sia la profondità (i salti di piano si applicano sotto)
            hp, atk = typical_enemy(floor)
            self.hp = int(hp * data["hp_mult"] / floor_multiplier(floor)) + random.randint(-5, 5)
            self.atk = int(atk * data["atk_mult"] / floor_multiplier(floor)) + random.randint(0, 1)
            self.gold_drop, self.exp_drop = max(5, 5 + int(floor * 3.5)), 30 + (floor * 10)
        else:
            # Nelle Eco oltre il piano 30 i nativi tornano forti quanto i nemici più profondi
            base_hp, base_atk = echo_native_base(data) if data.get("biome") and cycle_of(floor) else (data["base_hp"], data["base_atk"])
            self.hp = base_hp + int(lvl_scale * ENEMY_HP_PER_FLOOR) + random.randint(-5, 5)
            self.atk = base_atk + int(lvl_scale * ENEMY_ATK_PER_FLOOR) + random.randint(0, 1)
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
        elif self.modifier == "elite":
            rule = GAME_DATA["meta"]["rooms"]["elite"]
            self.hp = int(self.hp * rule["hp_mult"])
            self.atk = int(self.atk * rule["atk_mult"])
            self.gold_drop *= rule["reward_mult"]; self.exp_drop *= rule["reward_mult"]
            self.name += f"{Colors.RED} (Élite){Colors.RESET}"
        elif self.modifier == "easy":
            self.hp = int(self.hp * 0.6)
            self.atk = int(self.atk * 0.6)
            self.name += f"{Colors.CYAN} (Debilitato){Colors.RESET}"
        # Il DIO ANTICO che attende alla fine di ogni ciclo porta il nome della sua Eco
        if data.get("final_boss") and cycle_of(floor): self.name += f"{Colors.MAGENTA} ({echo_name(cycle_of(floor))}){Colors.RESET}"
            
        # Gradi di Ascensione e modificatori della Sfida del Giorno
        self.atk = int(self.atk * modes.rule("enemy_atk_mult"))
        if is_boss:
            self.hp = int(self.hp * modes.rule("boss_hp_mult") * (modes.rule("final_boss_hp_mult") if data.get("final_boss") else 1.0))
            self.atk = int(self.atk * modes.rule("boss_atk_mult"))
        else:
            self.hp = int(self.hp * modes.rule("enemy_hp_mult") * (modes.rule("elite_hp_mult") if modifier == "elite" else 1.0))
        self.base_acc += modes.rule("enemy_acc_add")
        self.gold_drop = int(self.gold_drop * modes.rule("enemy_gold_mult"))
        self.max_hp = self.hp

        # Mosse annunciate in anticipo (intenti): pesi del nemico, del suo profilo o quelli predefiniti della sua categoria
        defaults = GAME_DATA["moves"]["defaults"]
        own = data.get("moves") or GAME_DATA["moves"]["profiles"].get(data.get("profile"), {}).get("moves")
        self.moves = dict(own or defaults["boss" if is_boss else "enemy"])
        if self.status_inflict and not own: self.moves.update(defaults["with_status"])
        self.last_move = None
        self.heals_used = 0
        self.mark = None  # [elemento, turni]: il marchio elementale che una reazione può far esplodere
        # Fasi dei boss (phases.json): a ogni soglia di HP cambiano mosse e regole; vedi CombatSession.check_phase
        self.phases = sorted(GAME_DATA["phases"].get(self.base_name, []), key=lambda ph: -ph["at_pct"]) if is_boss else []
        self.phase = 0      # fasi già attraversate
        self.shield = 0     # scudo della Barriera: assorbe i danni degli attacchi dell'eroe
        self.ward = None    # Scaglie: moltiplicatore dei danni degli attacchi, finché una reazione non le infrange
        self.charged = False  # dopo la Carica arriva sempre il Colpo caricato

    def choose_move(self) -> str:
        """La prossima mossa, annunciata al giocatore prima del suo turno."""
        if self.charged:
            self.charged = False
            self.last_move = "unleash"
            return "unleash"
        rules = GAME_DATA["moves"]["rules"]
        weights = dict(self.moves)
        if self.last_move in rules["no_repeat"]: weights.pop(self.last_move, None)
        if self.hp * 100 >= self.max_hp * rules["heal_below_pct"] or self.heals_used >= rules["max_heals"]: weights.pop("heal", None)
        if not self.status_inflict: weights.pop("venom", None)
        weights = {m: w for m, w in weights.items() if w > 0}
        move = random.choices(list(weights), weights=list(weights.values()))[0] if weights else "attack"
        self.last_move = move
        return move

