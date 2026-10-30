"""La magia: l'Etere e gli incantesimi (`data/spells.json`).

L'Etere è una risorsa della discesa: il massimo viene dalla classe (`classes.json → ether`) più l'Arcano, resta da uno
scontro all'altro e si guadagna agendo (`rules.gain`). Un incantesimo costa il turno e il suo Etere; quelli dell'elemento
della Risonanza costano `resonance_discount` in meno. Gli effetti si applicano in `CombatSession.cast_spell`.
"""
import random

import effects
from data_manager import GAME_DATA

SPELL_EFFECT_KEYS = ("damage_pct", "heal_pct", "drain_pct", "status", "dispel", "detonate_pct", "cleanse", "def_pct", "escape", "weaken_pct")


def rules() -> dict:
    return GAME_DATA["spells"]["rules"]


def spell(spell_id: str) -> dict:
    return GAME_DATA["spells"]["spells"][spell_id]


def cost(player, spell_id: str) -> int:
    """L'Etere che costa l'incantesimo all'eroe: meno se è dell'elemento della sua Risonanza o con uno sconto
    (talento Parsimonia Arcana, parola runica, reliquia: `spell_discount`), mai sotto 1."""
    s = spell(spell_id)
    discount = rules()["resonance_discount"] if s["element"] == player._get_resonance_element() else 0
    return max(1, s["cost"] - discount - effects.total(player, "spell_discount"))


def label(player, spell_id: str) -> str:
    """La voce del menu degli incantesimi: nome, costo, descrizione, e se manca l'Etere."""
    s, c = spell(spell_id), cost(player, spell_id)
    why = [w for w, on in (("Risonanza", s["element"] == player._get_resonance_element()), ("sconto", effects.total(player, "spell_discount"))) if on]
    note = f" ({' e '.join(why)}: era {s['cost']})" if c < s["cost"] else ""
    short = "" if player.ether >= c else " [Etere insufficiente]"
    return f"{s['icon']} {s['name']}: {c} Etere{note}. {s['desc']}{short}"


def available() -> list:
    """Gli incantesimi che si possono trovare in pergamena: quelli senza sblocco e quelli già sbloccati alla Forgia."""
    from data_manager import PROFILE_MANAGER
    return [sid for sid, s in GAME_DATA["spells"]["spells"].items() if not s.get("unlock_id") or s["unlock_id"] in PROFILE_MANAGER.unlocked_ids]


def roll_drop(source: str) -> bool:
    chance = rules()["drops"].get(source, 0)
    return chance > 0 and random.random() * 100 < chance


def scroll_value(floor: int) -> int:
    base, per_floor = rules()["scroll_value"]
    return base + per_floor * floor


def castable_outside(player) -> list:
    """Gli incantesimi che l'eroe può lanciare fuori dal combattimento (le cure), con il loro Etere."""
    return [sid for sid in player.spells if spell(sid).get("outside")]


def cast_outside(player, spell_id: str) -> str:
    """Lancia una cura fuori dal combattimento. Restituisce il messaggio da mostrare."""
    s, c = spell(spell_id), cost(player, spell_id)
    if player.ether < c: return f"Non hai abbastanza Etere per {s['name']} ({c})."
    player.ether -= c
    fx, parts = s["effects"], []
    if fx.get("cleanse"):
        removed = [k for k in ("poison", "bleed") if player.statuses.pop(k, None)]
        if removed: parts.append("ti liberi da " + " e ".join({"poison": "Veleno", "bleed": "Sanguinamento"}[k] for k in removed))
    if "heal_pct" in fx:
        parts.append(f"recuperi {player.heal(player.max_hp * fx['heal_pct'] // 100)} HP")
    return f"{s['icon']} {s['name']}: " + (", ".join(parts) if parts else "nessun effetto") + f". (Etere {player.ether}/{player.max_ether()})"
