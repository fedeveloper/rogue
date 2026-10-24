"""Le strutture del Fuoco del Campo e i loro livelli (`story.json → camp.structures`), senza interfaccia.

Una struttura ha un solo livello (`cost`, `desc`) o una lista `levels` di `{cost, desc, effects, start}`. Il livello
costruito sta nel profilo: il flag `camp_<id>` dice che esiste (lo leggono anche le strutture di un solo livello) e il
contatore `camp_<id>` quanti livelli ha. `effects` usa le chiavi di `attributes.value` e vale per ogni eroe
(`Player.camp_effects`); `start` sono doni di inizio discesa (`scroll`, `points`), dati da `camp.start_of_run_boon`.
I livelli sono cumulativi: costruire il terzo tiene gli effetti dei primi due.
"""
from data_manager import GAME_DATA, PROFILE_MANAGER


def structures() -> list:
    return GAME_DATA["story"]["camp"]["structures"]


def levels(s: dict) -> list:
    return s.get("levels") or [{"cost": s["cost"], "desc": s["desc"]}]


def level(structure_id: str) -> int:
    """Quanti livelli della struttura sono costruiti (0 se nessuno)."""
    n = PROFILE_MANAGER.get_counter(f"camp_{structure_id}")
    return n if n else (1 if PROFILE_MANAGER.get_flag(f"camp_{structure_id}") else 0)


def set_level(structure_id: str, n: int):
    PROFILE_MANAGER.set_flag(f"camp_{structure_id}")
    PROFILE_MANAGER.story["counters"][f"camp_{structure_id}"] = n


def built_levels(s: dict) -> list:
    return levels(s)[:level(s["id"])]


def total(section: str) -> dict:
    """La somma di `effects` o di `start` su tutti i livelli costruiti di tutte le strutture."""
    out = {}
    for s in structures():
        for lv in built_levels(s):
            for key, v in lv.get(section, {}).items(): out[key] = out.get(key, 0) + v
    return out
