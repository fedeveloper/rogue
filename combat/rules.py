"""Le regole condivise del combattimento: le mosse del nemico per tipo e la reazione fra due elementi."""
from data_manager import GAME_DATA

# Effetti di controllo delle reazioni: scadono alla fine del turno del nemico, non all'inizio
CONTROL_STATUSES = ("stun", "blind", "slow")
# Mosse del nemico che sono attacchi
ATTACK_MOVES = ("attack", "heavy", "venom", "drain", "unleash", "ether_drain", "spellcast")
# Attacchi da cui conviene difendersi: l'intento lo dice
HEAVY_MOVES = ("heavy", "unleash")


def reaction_key(a: str, b: str):
    """La reazione fra due elementi, nell'ordine in cui compare in elements.json, o None."""
    reactions = GAME_DATA["elements"].get("reactions", {})
    return next((k for k in (f"{a}+{b}", f"{b}+{a}") if k in reactions), None)
