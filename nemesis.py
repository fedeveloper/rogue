"""La Nemesi: il nemico che ti uccide se ne ricorda, prende il tuo Oro e torna a cercarti nelle discese successive.

Le Nemesi attive stanno nel profilo (`profile.nemeses`), le regole in `data/nemesis.json`. Ogni Nemesi ha un nome,
un rango (sale ogni volta che ti uccide di nuovo), un tratto imparato da te e il piano in cui ti ha ucciso:
ricompare vicino a quel piano. Sconfiggerla restituisce l'Oro e lascia un trofeo; il Codice ne racconta la storia.
"""
import random
from typing import List, Optional

from data_manager import GAME_DATA, PROFILE_MANAGER


def rules() -> dict:
    return GAME_DATA["nemesis"]["rules"]


def active() -> List[dict]:
    return PROFILE_MANAGER._data.setdefault("nemeses", [])


def fallen() -> List[dict]:
    """Le Nemesi sconfitte, per il Codice."""
    return PROFILE_MANAGER._data.setdefault("nemeses_fallen", [])


def rank_name(nem: dict) -> str:
    ranks = GAME_DATA["nemesis"]["ranks"]
    return ranks[min(nem["rank"], len(ranks)) - 1]


def full_name(nem: dict) -> str:
    return f"{nem['name']} {rank_name(nem)}"


def text(key: str, nem: Optional[dict] = None, **kw) -> str:
    values = dict(kw)
    if nem: values.update(name=nem["name"], rank=rank_name(nem), floor=nem["floor"], gold=nem["gold"])
    return GAME_DATA["nemesis"]["text"][key].format(**values)


def can_become(killer: dict) -> bool:
    """Solo i nemici comuni e le Élite diventano Nemesi; i boss si limitano a ricordarti."""
    enemy = GAME_DATA["enemies"].get(killer.get("name", ""))
    return bool(enemy) and not killer.get("is_boss") and "lair" not in enemy


def on_death(player, floor: int) -> Optional[str]:
    """Chiamata a fine discesa se l'eroe è morto: crea una Nemesi o fa salire di rango quella che l'ha ucciso.
    Restituisce la frase da mostrare."""
    killer = player.run_tracker.get("killer")
    if not killer: return None
    if killer.get("is_boss"):
        grudges = PROFILE_MANAGER._data.setdefault("boss_grudges", {})
        grudges[killer["name"]] = grudges.get(killer["name"], 0) + 1
        return None
    gold = player.gold * rules()["gold_taken_pct"] // 100
    nem = next((n for n in active() if n["id"] == killer.get("nemesis_id")), None)
    if nem:
        nem["rank"] = min(rules()["max_rank"], nem["rank"] + 1)
        nem["kills"] += 1
        nem["gold"] += gold
        nem["floor"] = floor
        return text("rank_up", nem)
    if not can_become(killer): return None
    rng = random.Random()
    used = {n["name"] for n in active()}
    names = [n for n in GAME_DATA["nemesis"]["names"] if n not in used] or GAME_DATA["nemesis"]["names"]
    nem = {"id": f"nem{PROFILE_MANAGER.stats.get('total_deaths', 0)}_{rng.randrange(10 ** 6)}", "enemy": killer["name"],
           "name": rng.choice(names), "rank": 1, "kills": 1, "gold": gold, "floor": floor,
           "trait": rng.choice(sorted(GAME_DATA["nemesis"]["traits"])), "element": killer.get("player_element", "Normale"),
           "class": player.role}
    active().append(nem)
    if len(active()) > rules()["max_active"]: active().pop(0)  # la più vecchia si perde nel Labirinto
    return text("born", nem)


def waiting_on(floor: int, met: set) -> Optional[dict]:
    """La Nemesi che aspetta su questo piano (una per piano, mai due volte nella stessa discesa)."""
    lo, hi = rules()["floor_window"]
    for nem in active():
        if nem["id"] not in met and nem["floor"] + lo <= floor <= nem["floor"] + hi: return nem
    return None


def build_enemy(nem: dict, floor: int, active_pacts: list):
    """Il nemico della Nemesi al piano attuale: più forte di un rango alla volta, con il suo tratto."""
    from entities import Enemy
    from ui import Colors
    e = Enemy(floor, False, active_pacts, name=nem["enemy"])
    mult = 1 + rules()["stats_pct_per_rank"] * nem["rank"] / 100
    trait = GAME_DATA["nemesis"]["traits"][nem["trait"]]
    e.hp = int(e.hp * mult * (1 + trait["value"] / 100 if nem["trait"] == "hp_bonus_pct" else 1))
    e.atk = int(e.atk * mult * (1 + trait["value"] / 100 if nem["trait"] == "atk_bonus_pct" else 1))
    if nem["trait"] == "acc_add": e.base_acc += trait["value"]
    e.max_hp = e.hp
    e.nemesis = nem
    e.name = f"{nem['name']} {rank_name(nem)}{Colors.MAGENTA} (Nemesi ✦){Colors.RESET}"
    return e


def resisted(nem: dict, element: str) -> float:
    """Moltiplicatore dei danni dell'eroe contro la Nemesi (il tratto che resiste all'elemento che l'ha uccisa)."""
    if nem["trait"] == "resist_element" and element == nem["element"] and element != "Normale":
        return 1 - GAME_DATA["nemesis"]["traits"]["resist_element"]["value"] / 100
    return 1.0


def defeat(nem: dict) -> int:
    """La Nemesi è sconfitta: lascia l'elenco delle attive e restituisce l'Oro che aveva preso."""
    if nem in active(): active().remove(nem)
    fallen().append({k: nem[k] for k in ("name", "enemy", "rank", "kills", "floor", "class")})
    del fallen()[:-20]
    return nem["gold"]


def boss_grudge(boss_name: str) -> Optional[str]:
    if PROFILE_MANAGER._data.get("boss_grudges", {}).get(boss_name):
        return text("boss_grudge", boss=boss_name)
    return None
