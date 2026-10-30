"""Il registro degli effetti: ogni bonus numerico dell'eroe si legge da qui, con `total(player, chiave)`.

Un effetto è una chiave (es. "acc", "spell_pct", "def_pct") con un numero da sommare. Le fonti che lo danno sono tutte
in SOURCES, una funzione per fonte che risponde a "quanto vale questa chiave per questo eroe":
- attributi: i punti dell'eroe × `per_point` (`data/attributes.json`);
- talenti: `effects` dei talenti presi (`data/talents.json`);
- tratto: `effects` del tratto (`meta.json → traits`), copiati in `Player.trait_effects` quando il tratto li usa;
- Campo: `effects` dei livelli costruiti delle strutture (`camp_rules`, in `Player.camp_effects`);
- rune: rune e parole runiche di arma e armatura, moltiplicate dalle reliquie che le potenziano, più le reliquie che
  danno un bonus con le stesse chiavi (`get_rune_bonus`);
- Maestria: i bonus magici della Maestria Lv.6 della propria classe (`Player.mastery_magic`);
- Archivio: i bonus dei libri sbloccati (`data/books.json`), uguali per ogni eroe.

Una chiave nuova nei dati vale subito per tutte le fonti: basta che il codice la legga con `total`. Restano fuori dal
registro i bonus di partenza (Maestrie globali, Perk del Campo, crescita per livello), che cambiano una volta sola i
valori base dell'eroe, e gli effetti con una regola propria (Maestria Lv.2, tratti come Titano o Maledetto, reliquie
con un comportamento), che non sono numeri da sommare.
"""
from archive import get_archive_bonus
from data_manager import GAME_DATA, PROFILE_MANAGER
import runes as rune_rules


def _attributes(player, key: str) -> int:
    definitions = GAME_DATA["attributes"]["attributes"]
    return sum(points * definitions[a]["per_point"].get(key, 0) for a, points in getattr(player, "attributes", {}).items())


def _talents(player, key: str) -> int:
    definitions = GAME_DATA["talents"]["talents"]
    return sum(definitions[t]["effects"].get(key, 0) for t in getattr(player, "talents", []))


def _trait(player, key: str) -> int:
    return getattr(player, "trait_effects", {}).get(key, 0)


def _camp(player, key: str) -> int:
    return getattr(player, "camp_effects", {}).get(key, 0)


def _runes(player, key: str) -> int:
    relics = getattr(player, "relic_effects", [])
    runes = sum(fx.get(key, 0) for item in (getattr(player, "weapon", None), getattr(player, "armor", None)) for fx in rune_rules.item_effects(item))
    mult = 1 + sum(r.get_rune_multiplier() for r in relics)
    return int(runes * mult) + sum(r.get_rune_bonus(key) for r in relics)


def _mastery(player, key: str) -> int:
    return getattr(player, "mastery_magic", {}).get(key, 0)


def _archive(player, key: str) -> int:
    return get_archive_bonus(key, PROFILE_MANAGER._data)


SOURCES = (
    ("attributi", _attributes), ("talenti", _talents), ("tratto", _trait), ("campo", _camp),
    ("rune", _runes), ("maestria", _mastery), ("archivio", _archive),
)


def total(player, key: str, skip=()) -> int:
    """La somma di un effetto su tutte le fonti, tranne quelle in `skip` (quando una fonte si applica a parte)."""
    return sum(fn(player, key) for name, fn in SOURCES if name not in skip)


def of(player, source: str, key: str) -> int:
    """Quanto vale un effetto per una sola fonte."""
    return dict(SOURCES)[source](player, key)
