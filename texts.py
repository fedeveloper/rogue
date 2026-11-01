"""I testi d'atmosfera scelti a caso: frasi delle stanze, atmosfera del bioma, quale lettera insanguinata si legge.

Hanno un generatore casuale loro (`RNG`), separato da quello del gioco: aggiungere o togliere una frase nei dati non
cambia nessun tiro di dado della discesa (mappe, nemici, bottino, esiti). `tests/test_texts.py` lo controlla. Ciò che
ha un effetto sul gioco (se una lettera si trova, quale evento compare) resta sul generatore del gioco.
"""
import random

from data_manager import GAME_DATA, get_biome

RNG = random.Random()


def pick(options):
    """Una frase a caso fra `options`."""
    return RNG.choice(options)


def room(kind: str, floor: int) -> str:
    """La frase d'ingresso di una stanza (`combat`, `boss`, `vendor`, `treasure`, `trap`, `campfire`, `mystery`): quelle del
    bioma del piano (`data/atmosfere.json`), anche nelle sue Eco, oppure quelle generiche di `lore.json`."""
    own = GAME_DATA["atmosfere"]["biomes"].get((get_biome(floor) or {}).get("id"), {}).get(kind)
    return pick(own or GAME_DATA["lore"][kind])


def index(n: int) -> int:
    """Un indice a caso fra 0 e n-1 (per esempio la lettera insanguinata da leggere)."""
    return RNG.randrange(n)
