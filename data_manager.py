import os
import sys
import json
from typing import Dict, Any
from ui import Colors, set_text_speed
from constants import TEXT_SPEEDS, DEFAULT_TEXT_SPEED

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_json_file(filename: str) -> Dict[str, Any]:
    filepath = os.path.join(BASE_DIR, "data", filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f: return json.load(f)
    except Exception as e:
        print(f"{Colors.RED}ERRORE FATALE:{Colors.RESET} File 'data/{filename}' mancante o corrotto. ({e})")
        sys.exit(1)

class ProfileManager:
    def __init__(self):
        self.filepath = os.path.join(BASE_DIR, "profile.json")
        self._data = self._load()

    def _load(self) -> Dict[str, Any]:
        default_profile = {
            "essence": 0, "max_floor": 0, "won_normal": False,
            "unlocked_ids":[], "class_xp": {}, "class_lvl": {},
            "stats": {"total_deaths": 0, "total_gold": 0, "total_bosses": 0}, "completed_feats":[],
            "story": {"flags": {}, "counters": {}, "seen_events": {}},
            "codex": {"enemies": {}, "letters": [], "relics": [], "reactions": []},
            "settings": {"text_speed": DEFAULT_TEXT_SPEED},
            "perks": {
                "hp_lvl": 0, "gold_lvl": 0, "discount_lvl": 0, "sesto_senso": False, "scarpisti": False,
                "dodge_lvl": 0, "acc_lvl": 0, "exp_lvl": 0, "farmacista": False, "altare_benedizione": False,
                "riciclatore_lvl": 0, "banca_anima_lvl": 0, "artigiano_lvl": 0, "pelle_dura_lvl": 0, "speranza_luce_lvl": 0
            }
        }
        if not os.path.exists(self.filepath):
            self._write(default_profile)
            return default_profile
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f: loaded = json.load(f)
            if not isinstance(loaded, dict): raise ValueError("il profilo non è un oggetto JSON")
        except (ValueError, OSError) as e:
            backup = self.filepath + ".corrotto"
            os.replace(self.filepath, backup)
            print(f"{Colors.RED}ATTENZIONE:{Colors.RESET} profile.json illeggibile ({e}). Copia salvata in '{os.path.basename(backup)}', si riparte da un profilo nuovo.")
            self._write(default_profile)
            return default_profile
        for key, val in default_profile.items():
            if key not in loaded: loaded[key] = val
            elif isinstance(val, dict):
                for sub_k, sub_v in val.items():
                    if sub_k not in loaded[key]: loaded[key][sub_k] = sub_v
        self._write(loaded)
        return loaded

    def _write(self, data: Dict[str, Any]):
        # Scrittura atomica: un crash a metà non lascia un salvataggio troncato
        tmp_path = self.filepath + ".tmp"
        with open(tmp_path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)
        os.replace(tmp_path, self.filepath)

    def save(self):
        self._write(self._data)

    @property
    def essence(self) -> int: return self._data["essence"]
    
    @essence.setter
    def essence(self, value: int): self._data["essence"] = value

    @property
    def max_floor(self) -> int: return self._data["max_floor"]
    
    @max_floor.setter
    def max_floor(self, value: int): self._data["max_floor"] = value

    @property
    def won_normal(self) -> bool: return self._data["won_normal"]
    
    @won_normal.setter
    def won_normal(self, value: bool): self._data["won_normal"] = value

    @property
    def stats(self): return self._data["stats"]

    @property
    def unlocked_ids(self) -> list: return self._data["unlocked_ids"]

    @property
    def completed_feats(self) -> list: return self._data["completed_feats"]

    def get_perk(self, perk_name: str, default=0):
        return self._data["perks"].get(perk_name, default)
        
    def set_perk(self, perk_name: str, value):
        self._data["perks"][perk_name] = value

    def get_class_lvl(self, class_id: str, default=1):
        return self._data["class_lvl"].get(class_id, default)

    def set_class_lvl(self, class_id: str, value):
        self._data["class_lvl"][class_id] = value

    def get_class_xp(self, class_id: str, default=0):
        return self._data["class_xp"].get(class_id, default)

    def set_class_xp(self, class_id: str, value):
        self._data["class_xp"][class_id] = value

    @property
    def text_speed(self) -> str:
        speed = self._data["settings"].get("text_speed", DEFAULT_TEXT_SPEED)
        return speed if speed in TEXT_SPEEDS else DEFAULT_TEXT_SPEED

    @text_speed.setter
    def text_speed(self, value: str):
        self._data["settings"]["text_speed"] = value
        set_text_speed(TEXT_SPEEDS[value])

    # --- Memoria del Labirinto: resta fra una run e l'altra ---
    @property
    def story(self) -> dict:
        return self._data.setdefault("story", {"flags": {}, "counters": {}, "seen_events": {}})

    def get_flag(self, name: str) -> bool:
        return bool(self.story["flags"].get(name, False))

    def set_flag(self, name: str, value: bool = True):
        self.story["flags"][name] = value

    def get_counter(self, name: str) -> int:
        return int(self.story["counters"].get(name, 0))

    def add_counter(self, name: str, amount: int = 1):
        self.story["counters"][name] = self.get_counter(name) + amount

    @property
    def codex(self) -> dict:
        return self._data.setdefault("codex", {"enemies": {}, "letters": [], "relics": [], "reactions": []})

    def get_npc_unlocked(self, npc_name: str) -> bool:
        return self._data.get("npc_unlocked", {}).get(npc_name, False)
        
    def unlock_npc(self, npc_name: str):
        if "npc_unlocked" not in self._data: self._data["npc_unlocked"] = {}
        self._data["npc_unlocked"][npc_name] = True


PROFILE_MANAGER = ProfileManager()
set_text_speed(TEXT_SPEEDS[PROFILE_MANAGER.text_speed])
_ENEMIES_FILE = load_json_file("enemies.json")
RAW_DATA = {
    "enemies": _ENEMIES_FILE["enemies"], "bosses": _ENEMIES_FILE["bosses"],
    "weapons": load_json_file("weapons.json")["weapons"], "armors": load_json_file("armors.json")["armors"],
    "accessories": load_json_file("accessories.json")["accessories"],
    "consumables": load_json_file("consumables.json")["consumables"], "classes": load_json_file("classes.json"),
    "lore": load_json_file("lore.json"), "elements": load_json_file("elements.json"),
    "meta": load_json_file("meta.json"), "events": load_json_file("events.json"), "relics": load_json_file("relics.json")["relics"],
    "story": load_json_file("story.json"),
    "biomes": load_json_file("biomes.json")["biomes"],
    "moves": load_json_file("moves.json")
}

def update_game_data():
    global GAME_DATA, ELEMENTS, E_ICONS, MULTIPLIERS
    GAME_DATA.clear()
    GAME_DATA.update({
        "enemies": RAW_DATA["enemies"], "bosses": RAW_DATA["bosses"], "lore": RAW_DATA["lore"], "elements": RAW_DATA["elements"],
        "meta": RAW_DATA["meta"], "events": RAW_DATA["events"], "classes": RAW_DATA["classes"], "story": RAW_DATA["story"], "biomes": RAW_DATA["biomes"], "moves": RAW_DATA["moves"],
        "relics":[r for r in RAW_DATA["relics"] if r.get("unlock_id") is None or r["unlock_id"] in PROFILE_MANAGER.unlocked_ids],
        "weapons":[w for w in RAW_DATA["weapons"] if w.get("unlock_id") is None or w["unlock_id"] in PROFILE_MANAGER.unlocked_ids],
        "armors":[a for a in RAW_DATA["armors"] if a.get("unlock_id") is None or a["unlock_id"] in PROFILE_MANAGER.unlocked_ids],
        "accessories":[ac for ac in RAW_DATA["accessories"] if ac.get("unlock_id") is None or ac["unlock_id"] in PROFILE_MANAGER.unlocked_ids],
        "consumables":[c for c in RAW_DATA["consumables"] if c.get("unlock_id") is None or c["unlock_id"] in PROFILE_MANAGER.unlocked_ids]
    })
    
    ELEMENTS.clear()
    ELEMENTS.extend(GAME_DATA["elements"]["list"])
    
    E_ICONS.clear()
    E_ICONS.update(GAME_DATA["elements"]["icons"])
    
    MULTIPLIERS.clear()
    MULTIPLIERS.update(GAME_DATA["elements"]["multipliers"])

GAME_DATA = {}
ELEMENTS = []
E_ICONS = {}
MULTIPLIERS = {}

update_game_data()

def get_biome(floor: int):
    """Il bioma del piano, o None oltre l'ultimo (Modalità Infinita)."""
    return next((b for b in GAME_DATA["biomes"] if b["floors"][0] <= floor <= b["floors"][1]), None)

def get_element_icon(el_name: str) -> str: 
    return f"{E_ICONS.get(el_name, '')} {el_name}"
