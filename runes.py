"""Rune e Incastoni: le rune si incastonano in armi e armature e ne restano parte finché non si estraggono.

I dati sono in `data/runes.json`. Ogni runa ha uno `slot` (arma, armatura o entrambe) ed `effects`, chiavi di
RUNE_EFFECT_KEYS che il gioco somma su arma e armatura equipaggiate (`Player.rune_value`).
"""
import random
from typing import Optional

from data_manager import GAME_DATA

# Chiavi degli effetti e cosa fanno (il contratto di ognuna è in tests/test_runes.py)
RUNE_EFFECT_KEYS = (
    "mark_duration_add", "reaction_dmg_pct", "super_effective_pct", "bleed_on_hit", "poison_on_hit", "crit_chance_add",
    "atk_pct", "lifesteal_pct", "first_strike_pct", "def_pct", "dodge_add", "thorns_pct", "defend_heal_pct",
    "gold_pct", "exp_pct", "audacity_start", "trap_chance_add",
)
SLOT_NAMES = {"weapon": "arma", "armor": "armatura", "any": "arma o armatura"}


def rules() -> dict:
    return GAME_DATA["runes"]["rules"]


def rune(rune_id: str) -> dict:
    return GAME_DATA["runes"]["runes"][rune_id]


def fits(rune_id: str, item_type: str) -> bool:
    return rune(rune_id)["slot"] in ("any", item_type)


def random_rune_id(rng=random) -> str:
    pool = GAME_DATA["runes"]["runes"]
    return rng.choices(list(pool), weights=[r["weight"] for r in pool.values()])[0]


def roll_drop(source: str) -> bool:
    return random.random() * 100 < rules()["drops"].get(source, 0)


def extract_cost(floor: int) -> int:
    base, per_floor = rules()["extract_cost"]
    return base + per_floor * floor


def socket_tag(item) -> str:
    """⟨🔪◇⟩: le rune incastonate e gli incastoni liberi di un'arma o di un'armatura."""
    sockets = getattr(item, "sockets", 0)
    if not sockets: return ""
    runes = getattr(item, "runes", [])
    return " ⟨" + "".join(rune(r)["icon"] for r in runes) + "◇" * (sockets - len(runes)) + "⟩"


def free_sockets(item) -> int:
    return getattr(item, "sockets", 0) - len(getattr(item, "runes", []))


def describe(rune_id: str) -> str:
    r = rune(rune_id)
    return f"{r['icon']} {r['name']} ({SLOT_NAMES[r['slot']]}): {r['desc']}"


def item_value(rune_id: Optional[str], floor: int) -> int:
    base, per_floor = rules()["value"]
    return base + per_floor * floor
