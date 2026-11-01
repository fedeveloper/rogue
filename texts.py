"""I testi d'atmosfera scelti a caso: frasi delle stanze, atmosfera del bioma, quale lettera insanguinata si legge.

Hanno un generatore casuale loro (`RNG`), separato da quello del gioco: aggiungere o togliere una frase nei dati non
cambia nessun tiro di dado della discesa (mappe, nemici, bottino, esiti). `tests/test_texts.py` lo controlla. Ciò che
ha un effetto sul gioco (se una lettera si trova, quale evento compare) resta sul generatore del gioco.
"""
import random

RNG = random.Random()


def pick(options):
    """Una frase a caso fra `options`."""
    return RNG.choice(options)


def index(n: int) -> int:
    """Un indice a caso fra 0 e n-1 (per esempio la lettera insanguinata da leggere)."""
    return RNG.randrange(n)
