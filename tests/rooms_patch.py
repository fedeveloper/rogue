"""Per i test: sostituire un nome di `rooms` anche nei moduli di `combat/` che lo usano, con un solo oggetto.

Prima della divisione del combattimento in `combat/`, `mock.patch("rooms.wait_enter")` valeva per le stanze e per tutto
lo scontro. Ora lo stesso nome è importato in più moduli: `patch_rooms("wait_enter")` mette lo stesso mock in ognuno,
così un `side_effect` a lista resta una sola sequenza anche se il menu passa da `combat/actions.py` a `combat/spells.py`.
"""
import importlib
from unittest import mock

MODULES = ("rooms", "combat.session", "combat.actions", "combat.spells", "combat.reactions", "combat.phases", "combat.enemy",
           "combat.rewards")


class patch_rooms:
    """Come `mock.patch("rooms.<name>", ...)`, in tutti i moduli di MODULES che hanno quel nome: si usa con `with`
    oppure con `start()` e `stop()`, e dà lo stesso mock."""

    def __init__(self, name: str, new=mock.DEFAULT, **kwargs):
        self.fake = mock.MagicMock(**kwargs) if new is mock.DEFAULT else new
        owners = [m for m in MODULES if hasattr(importlib.import_module(m), name)]
        if not owners: raise AttributeError(f"nessun modulo di rooms o di combat ha {name!r}")
        self.patches = [mock.patch(f"{m}.{name}", self.fake) for m in owners]

    def start(self):
        for p in self.patches: p.start()
        return self.fake

    def stop(self):
        for p in reversed(self.patches): p.stop()

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()
        return False
