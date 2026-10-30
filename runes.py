"""Rune e Incastoni: le rune si incastonano in armi e armature e ne restano parte finché non si estraggono.

I dati sono in `data/runes.json`. Ogni runa ha uno `slot` (arma, armatura o entrambe) ed `effects`, chiavi di
RUNE_EFFECT_KEYS che il gioco somma su arma e armatura equipaggiate (la fonte "rune" di `effects.total`).
"""
import random
from typing import Optional

from data_manager import GAME_DATA

# Chiavi degli effetti e cosa fanno (il contratto di ognuna è in tests/test_runes.py)
RUNE_EFFECT_KEYS = (
    "mark_duration_add", "reaction_dmg_pct", "super_effective_pct", "bleed_on_hit", "poison_on_hit", "crit_chance_add",
    "atk_pct", "lifesteal_pct", "first_strike_pct", "def_pct", "dodge_add", "thorns_pct", "defend_heal_pct",
    "gold_pct", "exp_pct", "audacity_start", "trap_chance_add", "scorch_on_hit", "stun_on_hit",
    "ether_max", "spell_pct", "ether_on_hit", "spell_discount",  # magia: sommate alle altre fonti (effects.total)
)
# Status che le rune (e le parole runiche) possono infliggere a ogni colpo: (status, chiave, turni)
ON_HIT_STATUSES = (("bleed", "bleed_on_hit", 3), ("poison", "poison_on_hit", 3), ("scorch", "scorch_on_hit", 3), ("stun", "stun_on_hit", 1))
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


def roll_drop(source: str, bonus: int = 0) -> bool:
    """Una runa dalla fonte, con la sua probabilità in % più un bonus (la Fortuna). Una fonte senza drop resta senza."""
    base = rules()["drops"].get(source, 0)
    return base > 0 and random.random() * 100 < base + bonus


def extract_cost(floor: int) -> int:
    base, per_floor = rules()["extract_cost"]
    return base + per_floor * floor


def word(word_id: str) -> dict:
    return GAME_DATA["runes"]["words"][word_id]


def active_words(item) -> list:
    """Le parole runiche che le rune di un oggetto compongono. Ogni runa vale per una sola parola:
    prima le parole più lunghe, poi nell'ordine dei dati."""
    left = list(getattr(item, "runes", []))
    found = []
    for wid, w in sorted(GAME_DATA["runes"]["words"].items(), key=lambda kv: -len(kv[1]["runes"])):
        if all(left.count(r) >= w["runes"].count(r) for r in set(w["runes"])):
            for r in w["runes"]: left.remove(r)
            found.append(wid)
    return found


def item_effects(item) -> list:
    """Gli effetti delle rune e delle parole runiche di un oggetto."""
    return [rune(r)["effects"] for r in getattr(item, "runes", [])] + [word(w)["effects"] for w in active_words(item)]


def socket_tag(item) -> str:
    """[Incastoni: 🔪◇] «Parola»: le rune incastonate, gli incastoni liberi e le parole runiche di un'arma o di un'armatura."""
    sockets = getattr(item, "sockets", 0)
    if not sockets: return ""
    runes = getattr(item, "runes", [])
    words = "".join(f" «{word(w)['name']}»" for w in active_words(item))
    return " [Incastoni: " + "".join(rune(r)["icon"] for r in runes) + "◇" * (sockets - len(runes)) + "]" + words


def free_sockets(item) -> int:
    return getattr(item, "sockets", 0) - len(getattr(item, "runes", []))


def describe(rune_id: str) -> str:
    r = rune(rune_id)
    return f"{r['icon']} {r['name']} ({SLOT_NAMES[r['slot']]}): {r['desc']}"


def item_value(rune_id: Optional[str], floor: int) -> int:
    base, per_floor = rules()["value"]
    return base + per_floor * floor
