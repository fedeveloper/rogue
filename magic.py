"""La magia: l'Etere e gli incantesimi (`data/spells.json`).

L'Etere è una risorsa della discesa: il massimo viene dalla classe (`classes.json → ether`) più l'Arcano, resta da uno
scontro all'altro e si guadagna agendo (`rules.gain`). Un incantesimo costa il turno e il suo Etere; quelli dell'elemento
della Risonanza costano `resonance_discount` in meno. Gli effetti si applicano in `CombatSession.cast_spell`.
"""
from data_manager import GAME_DATA

SPELL_EFFECT_KEYS = ("damage_pct", "heal_pct", "drain_pct", "status", "dispel", "detonate_pct")


def rules() -> dict:
    return GAME_DATA["spells"]["rules"]


def spell(spell_id: str) -> dict:
    return GAME_DATA["spells"]["spells"][spell_id]


def cost(player, spell_id: str) -> int:
    """L'Etere che costa l'incantesimo all'eroe: meno, se è dell'elemento della sua Risonanza (mai sotto 1)."""
    s = spell(spell_id)
    discount = rules()["resonance_discount"] if s["element"] == player._get_resonance_element() else 0
    return max(1, s["cost"] - discount)


def label(player, spell_id: str) -> str:
    """La voce del menu degli incantesimi: nome, costo, descrizione, e se manca l'Etere."""
    s, c = spell(spell_id), cost(player, spell_id)
    note = " (Risonanza: -1)" if c < s["cost"] else ""
    short = "" if player.ether >= c else " [Etere insufficiente]"
    return f"{s['icon']} {s['name']}: {c} Etere{note}. {s['desc']}{short}"
