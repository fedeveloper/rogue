import os
import sys
import json
from typing import Dict, Any
from ui import Colors

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
        "perks": {
            "hp_lvl": 0, "gold_lvl": 0, "discount_lvl": 0, "sesto_senso": False, "scarpisti": False,
            "dodge_lvl": 0, "acc_lvl": 0, "exp_lvl": 0, "farmacista": False, "altare_benedizione": False,
            "riciclatore_lvl": 0, "banca_anima_lvl": 0, "artigiano_lvl": 0, "pelle_dura_lvl": 0, "speranza_luce_lvl": 0
        }
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

PROFILE = load_profile()

RAW_DATA = {
    "enemies": load_json_file("enemies.json")["enemies"], "bosses": load_json_file("enemies.json")["bosses"],
    "weapons": load_json_file("weapons.json")["weapons"], "armors": load_json_file("armors.json")["armors"],
    "accessories": load_json_file("accessories.json")["accessories"],
    "consumables": load_json_file("consumables.json")["consumables"], "classes": load_json_file("classes.json"),
    "lore": load_json_file("lore.json"), "elements": load_json_file("elements.json"),
    "meta": load_json_file("meta.json"), "events": load_json_file("events.json"), "relics": load_json_file("relics.json")["relics"]
}

def update_game_data():
    global GAME_DATA, ELEMENTS, E_ICONS, MULTIPLIERS
    GAME_DATA.clear()
    GAME_DATA.update({
        "enemies": RAW_DATA["enemies"], "bosses": RAW_DATA["bosses"], "lore": RAW_DATA["lore"], "elements": RAW_DATA["elements"],
        "meta": RAW_DATA["meta"], "events": RAW_DATA["events"], "relics": RAW_DATA["relics"], "classes": RAW_DATA["classes"],
        "weapons":[w for w in RAW_DATA["weapons"] if w.get("unlock_id") is None or w["unlock_id"] in PROFILE["unlocked_ids"]],
        "armors":[a for a in RAW_DATA["armors"] if a.get("unlock_id") is None or a["unlock_id"] in PROFILE["unlocked_ids"]],
        "accessories":[ac for ac in RAW_DATA["accessories"] if ac.get("unlock_id") is None or ac["unlock_id"] in PROFILE["unlocked_ids"]],
        "consumables":[c for c in RAW_DATA["consumables"] if c.get("unlock_id") is None or c["unlock_id"] in PROFILE["unlocked_ids"]]
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

def get_element_icon(el_name: str) -> str: 
    return f"{E_ICONS.get(el_name, '')} {el_name}"
