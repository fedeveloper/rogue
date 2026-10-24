"""Gli attributi dell'eroe: a ogni livello un punto da spendere fra Vitalità, Forza, Destrezza, Agilità, Arcano e Fortuna.

I numeri stanno in `data/attributes.json`. Ogni attributo ha degli effetti per punto (`per_point`); `value(player, chiave)`
li somma su tutti gli attributi e li leggono il Player e il combattimento. Gli HP massimi della Vitalità si aggiungono
quando si spende il punto (e si tolgono se si redistribuisce con il Tomo dell'Oblio); tutti gli altri effetti si calcolano
al momento. Gli attributi iniziali vengono dalla classe (`classes.json → attributes`) e non si possono redistribuire.
"""
import talents
from data_manager import GAME_DATA, RAW_DATA
from ui import Colors, clear_screen, display_msg, interactive_menu

LATER = "Più tardi (i punti restano: li spendi dalla mappa)"


def rules() -> dict:
    return GAME_DATA["attributes"]["rules"]


def definitions() -> dict:
    return GAME_DATA["attributes"]["attributes"]


def starting(class_id: str) -> dict:
    """Gli attributi con cui parte la classe: tutti gli attributi, a zero quelli che la classe non nomina."""
    start = RAW_DATA["classes"][class_id].get("attributes", {})
    return {a: start.get(a, 0) for a in definitions()}


def value(player, key: str) -> int:
    """La somma di un effetto (es. "acc", "spell_pct") su tutti gli attributi dell'eroe, più quella dei suoi talenti
    e del suo tratto (`meta.json → traits[id].effects`)."""
    attrs = getattr(player, "attributes", {})
    return (sum(points * definitions()[a]["per_point"].get(key, 0) for a, points in attrs.items()) + talents.value(player, key)
            + getattr(player, "trait_effects", {}).get(key, 0))


def weapon_bonus(player) -> int:
    """I danni in più (in %) dell'arma impugnata: i punti dell'attributo con cui scala × il suo scaled_dmg_pct."""
    attr = player.weapon.scaling
    return player.attributes.get(attr, 0) * definitions()[attr]["per_point"].get("scaled_dmg_pct", 0)


def can_raise(player, attr: str) -> bool:
    return player.unspent_points > 0 and player.attributes[attr] < rules()["max_points"]


def raise_attribute(player, attr: str) -> bool:
    """Spende un punto. La Vitalità aggiunge subito i suoi HP massimi (e altrettanti HP attuali)."""
    if not can_raise(player, attr): return False
    player.unspent_points -= 1
    player.attributes[attr] += 1
    hp = definitions()[attr]["per_point"].get("max_hp", 0)
    player.max_hp += hp
    player.hp += hp
    return True


def reset(player) -> int:
    """Il Tomo dell'Oblio: i punti spesi tornano da spendere, gli attributi della classe restano. Restituisce i punti resi."""
    start, refunded = starting(player.class_id), 0
    for attr, points in player.attributes.items():
        extra = points - start[attr]
        if extra <= 0: continue
        hp = definitions()[attr]["per_point"].get("max_hp", 0) * extra
        player.max_hp -= hp
        player.hp = max(1, min(player.hp - hp, player.max_hp))
        player.attributes[attr] = start[attr]
        refunded += extra
    player.unspent_points += refunded
    return refunded


def summary(player) -> str:
    """Gli attributi in una riga, per le Statistiche e la scelta dei punti."""
    return " · ".join(f"{d['icon']} {d['name']} {player.attributes[a]}" for a, d in definitions().items())


def spend_points(player):
    """Il menu dei punti abilità: un punto alla volta, finché ce ne sono o finché il giocatore rimanda."""
    while player.unspent_points > 0:
        clear_screen()
        prompt = (f"\n{Colors.YELLOW}{Colors.BOLD}--- PUNTI ABILITÀ: {player.unspent_points} da spendere ---{Colors.RESET}\n"
                  f"Livello {player.level} | {summary(player)}\n")
        options = [f"{d['icon']} {d['name']} ({player.attributes[a]}/{rules()['max_points']}): {d['desc']}"
                   + (f" {Colors.RED}[al massimo]{Colors.RESET}" if player.attributes[a] >= rules()["max_points"] else "")
                   for a, d in definitions().items()]
        options.append(LATER)
        idx = interactive_menu(options, prompt)
        if idx < 0 or idx >= len(definitions()): break
        attr = list(definitions())[idx]
        if raise_attribute(player, attr):
            display_msg(f"{Colors.GREEN}{definitions()[attr]['name']} sale a {player.attributes[attr]}.{Colors.RESET}")
    player.points_offered = True
