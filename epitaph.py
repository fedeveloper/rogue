"""L'Epitaffio e il Cimitero: a fine discesa poche frasi raccontano chi eri e come è finita.

Durante la discesa `note(player, tipo, **dati)` annota i momenti chiave in `player.chronicle`. A fine partita
`compose` sceglie dai modelli di `data/epitaph.json` un'apertura, fino a `max_middle` frasi di mezzo nell'ordine di
`priority` e la causa della fine. La scelta fra le varianti dipende solo dai fatti della discesa, quindi lo stesso
racconto dà sempre lo stesso epitaffio. `record` lo conserva nel Cimitero (`profile.cemetery`, ultime `cemetery_size`).
"""
import datetime
import random
from typing import List, Optional

from data_manager import GAME_DATA, PROFILE_MANAGER


def note(player, kind: str, **data):
    player.chronicle.append({"kind": kind, **data})


def _last(player, kind: str) -> Optional[dict]:
    return next((e for e in reversed(player.chronicle) if e["kind"] == kind), None)


def _all(player, kind: str) -> List[dict]:
    return [e for e in player.chronicle if e["kind"] == kind]


def _join(names: List[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " e " + names[-1]


def outcome(player) -> str:
    return "victory" if player.won else "escape" if player.escaped else "death"


def compose(player, floor: int, born_nemesis: Optional[str] = None) -> List[str]:
    data = GAME_DATA["epitaph"]
    rng = random.Random(f"{player.class_id}-{floor}-{player.bosses_killed}-{len(player.chronicle)}")
    out = outcome(player)
    lines = [rng.choice(data["opening"][out]).format(cls=player.role, floor=floor, gold=player.gold)]

    bosses = _all(player, "boss")
    facts = {
        "ascension": {"grade": player.ascension} if player.ascension else None,
        "daily": {"date": player.daily["date"]} if player.daily else None,
        "echo": {"echo": _last(player, "echo")["echo"]} if _last(player, "echo") else None,
        "nemesis": {"nemesis": _last(player, "nemesis_defeated")["name"]} if _last(player, "nemesis_defeated") else None,
        "bosses": {"bosses": len(bosses), "last_boss": bosses[-1]["name"]} if bosses else None,
        "runeword": {"runeword": _last(player, "runeword")["name"]} if _last(player, "runeword") else None,
        "relics": {"relics": _join([r["name"] for r in _all(player, "relic")][-2:])} if _all(player, "relic") else None,
        "event": {"event": _last(player, "event")["title"]} if _last(player, "event") else None,
        "biomes": {"biomes": _join([b["name"] for b in _all(player, "biome")])} if len(_all(player, "biome")) > 1 else None,
        "corruption": {"corruption": player.corruption} if player.corruption >= 50 else None,
    }
    middle = [data["middle"][k].format(**facts[k]) for k in data["priority"] if facts[k]]
    lines += middle[:data["max_middle"]]

    ending = _last(player, "ending")
    if ending: lines.append(data["ending"].format(ending=ending["title"]))
    if out == "death":
        killer = player.run_tracker.get("killer")
        cause = player.run_tracker.get("death_cause")
        if killer and killer.get("nemesis_id"): kind = "nemesis"
        elif killer and killer.get("is_boss"): kind = "boss"
        elif killer: kind = "enemy"
        else: kind = "trap" if cause == "trap" else "other"
        lines.append(data["cause"][kind].format(killer=killer.get("display", killer["name"]) if killer else ""))
        if born_nemesis: lines.append(data["born"].format(nemesis=born_nemesis))
    return lines


def cemetery() -> List[dict]:
    return PROFILE_MANAGER._data.setdefault("cemetery", [])


def record(player, floor: int, lines: List[str]):
    cemetery().append({"date": datetime.date.today().isoformat(), "class": player.role, "floor": floor,
                       "outcome": outcome(player), "epitaph": lines})
    del cemetery()[:-GAME_DATA["epitaph"]["cemetery_size"]]
