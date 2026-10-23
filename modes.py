"""Modalità di gioco: i gradi di Ascensione e la Sfida del Giorno.

Entrambe cambiano le regole di una discesa con gli stessi effetti (`data/modes.json`). Le regole della discesa
in corso sono in `RUN`: le leggono nemici, stanze e oggetti. `start_run` le imposta, `end_run` le azzera.
"""
import datetime
import random
from typing import List, Optional

from data_manager import GAME_DATA, PROFILE_MANAGER

# Come si combinano gli effetti di più gradi: moltiplicatori, somme, pesi delle stanze e patti
MULT_KEYS = ("rest_heal_mult", "campfire_heal_mult", "boss_hp_mult", "boss_atk_mult", "elite_hp_mult", "enemy_hp_mult", "enemy_atk_mult",
             "enemy_gold_mult", "chest_risk_mult", "curse_chance_mult", "start_gold_mult", "final_boss_hp_mult")
ADD_KEYS = ("enemy_acc_add", "start_corruption", "start_gold_add", "start_relic", "start_potions_add")

RUN = {}


def combine(effect_lists: List[dict]) -> dict:
    rules = {k: 1.0 for k in MULT_KEYS}
    rules.update({k: 0 for k in ADD_KEYS})
    rules.update(room_weights={}, pacts=[])
    for effects in effect_lists:
        for key, value in effects.items():
            if key in MULT_KEYS: rules[key] *= value
            elif key in ADD_KEYS: rules[key] += value
            elif key == "room_weights":
                for room, mult in value.items(): rules["room_weights"][room] = rules["room_weights"].get(room, 1.0) * mult
            elif key == "pact": rules["pacts"].append(value)
            else: raise KeyError(f"effetto di modalità sconosciuto: {key}")
    return rules


def start_run(rules: Optional[dict] = None):
    RUN.clear()
    RUN.update(rules or combine([]))


def end_run():
    start_run()


def rule(key: str):
    """Il valore di una regola nella discesa in corso (neutro se nessuna modalità è attiva)."""
    if not RUN: start_run()
    return RUN[key]


# ------------------------------------------------------------------ Ascensione
def grades() -> list:
    return GAME_DATA["modes"]["ascension"]["grades"]


def max_grade() -> int:
    """Il grado più alto disponibile: il primo dopo la prima vittoria, poi uno in più per ogni grado vinto."""
    if not PROFILE_MANAGER.won_normal: return 0
    best = PROFILE_MANAGER._data.get("ascension", {}).get("best_win", 0)
    return min(GAME_DATA["modes"]["ascension"]["max"], best + 1)


def ascension_rules(grade: int) -> dict:
    """Le regole cumulative di un grado: valgono tutti i gradi fino a quello scelto."""
    return combine([g["effects"] for g in grades()[:grade]])


def ascension_essence_mult(grade: int) -> float:
    return 1.0 + sum(g["essence_bonus"] for g in grades()[:grade])


def record_ascension_win(grade: int) -> bool:
    """Registra una vittoria della discesa standard; True se sblocca un grado nuovo."""
    data = PROFILE_MANAGER._data.setdefault("ascension", {"best_win": 0})
    before = max_grade()
    data["best_win"] = max(data.get("best_win", 0), grade)
    return max_grade() > before


# ------------------------------------------------------------------ Sfida del Giorno
def today() -> datetime.date:
    return datetime.date.today()


def daily_seed(day: datetime.date) -> int:
    return day.year * 10000 + day.month * 100 + day.day


def daily_setup(day: datetime.date) -> dict:
    """La sfida di un giorno: uguale per chiunque la giochi quel giorno. Eroe e tratto sono scelti fra tutti,
    anche quelli non ancora sbloccati: la sfida è anche un assaggio."""
    cfg = GAME_DATA["modes"]["daily"]
    rng = random.Random(daily_seed(day))
    maluses = rng.sample(range(len(grades())), cfg["maluses"])
    boon = rng.randrange(len(cfg["boons"]))
    return {
        "date": day.isoformat(), "seed": daily_seed(day),
        "class_id": rng.choice(sorted(GAME_DATA["classes"], key=int)),
        "trait_id": rng.choice(sorted(GAME_DATA["meta"]["traits"])),
        "maluses": sorted(maluses), "boon": boon,
    }


def daily_rules(setup: dict) -> dict:
    cfg = GAME_DATA["modes"]["daily"]
    return combine([grades()[i]["effects"] for i in setup["maluses"]] + [cfg["boons"][setup["boon"]]["effects"]])


def daily_score(floor: int, bosses: int, won: bool, gold: int) -> int:
    s = GAME_DATA["modes"]["daily"]["score"]
    return floor * s["per_floor"] + bosses * s["per_boss"] + (s["victory"] if won else 0) + gold // s["gold_div"]


def daily_history() -> dict:
    return PROFILE_MANAGER._data.setdefault("daily", {})


def record_daily(setup: dict, floor: int, bosses: int, won: bool, gold: int, class_role: str) -> Optional[int]:
    """Registra il primo tentativo del giorno e ne restituisce il punteggio; i tentativi successivi non contano (None)."""
    history = daily_history()
    if setup["date"] in history: return None
    score = daily_score(floor, bosses, won, gold)
    history[setup["date"]] = {"score": score, "floor": floor, "won": won, "class": class_role}
    for old in sorted(history)[:-GAME_DATA["modes"]["daily"]["history"]]: del history[old]
    return score


def daily_streak(day: datetime.date) -> int:
    """Giorni consecutivi di sfida giocata, fino a `day` (o al giorno prima, se oggi non è ancora giocata)."""
    history = daily_history()
    if day.isoformat() not in history: day -= datetime.timedelta(days=1)
    streak = 0
    while day.isoformat() in history:
        streak += 1; day -= datetime.timedelta(days=1)
    return streak
