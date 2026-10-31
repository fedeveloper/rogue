"""I premi fuori dal turno: l'Audacia del piano e il bottino del boss, le rune e le pergamene che cadono."""
import random

import runes as rune_rules
import effects
import magic
from ui import Colors, display_msg
from data_manager import GAME_DATA
from codex import record_rune
from entities import Player, generate_weapon, generate_armor, generate_rune, generate_scroll


def audacity_bonus(audacity: int) -> dict:
    """Cosa aggiunge l'Audacia al bottino del boss: oro in più (in %) e un oggetto, epico alle soglie più alte."""
    rule = GAME_DATA["meta"]["rooms"]["audacity"]
    return {"gold_pct": audacity * rule["gold_pct_per_point"], "item": audacity >= rule["item_at"], "epic": audacity >= rule["epic_at"]}


def audacity_text(audacity: int) -> str:
    bonus = audacity_bonus(audacity)
    if not audacity: return "nessun premio extra dal boss"
    parts = [f"+{bonus['gold_pct']}% oro"]
    if bonus["item"]: parts.append("oggetto epico" if bonus["epic"] else "oggetto")
    return "boss: " + ", ".join(parts)


def gain_audacity(player: Player, room_type: str) -> int:
    points = GAME_DATA["meta"]["rooms"]["audacity"]["points"].get(room_type, 0)
    if points: points += sum(r.get_audacity_bonus() for r in player.relic_effects)
    player.audacity += points
    return points


def audacity_reward(player: Player, floor: int, boss_gold: int):
    """Il premio del boss per i rischi corsi nel piano."""
    if player.audacity <= 0: return
    bonus = audacity_bonus(player.audacity)
    display_msg(f"\n{Colors.RED}🎲 Audacia {player.audacity}: il Labirinto premia chi ha rischiato.{Colors.RESET}")
    if not player.aristocrat:
        extra = player.calculate_gold_gain(boss_gold * bonus["gold_pct"] // 100)
        player.gold += extra
        display_msg(f"Ottieni altri {Colors.YELLOW}{extra} oro{Colors.RESET}.")
    if bonus["item"]:
        drop = generate_weapon(floor + 2, bonus["epic"]) if random.random() > 0.5 else generate_armor(floor + 2, bonus["epic"])
        display_msg(f"{Colors.MAGENTA}Premio dell'Audacia: {drop.display_name}!{Colors.RESET}")
        player.inventory.append(drop)


def scroll_drop(player: Player, floor: int, source: str):
    """Una pergamena con la probabilità della fonte (`spells.json`, `rules.drops`)."""
    if magic.roll_drop(source) and magic.available():
        s = generate_scroll(floor)
        display_msg(f"{Colors.CYAN}Trovi una pergamena: {s.display_name}! (Si legge dallo zaino){Colors.RESET}")
        player.inventory.append(s)


def rune_drop(player: Player, floor: int, source: str):
    """Una runa con la probabilità della fonte (`runes.json`, `rules.drops`)."""
    if rune_rules.roll_drop(source, effects.total(player, "rune_drop_add")) or any(source in r.rune_drop_always for r in player.relic_effects):
        r = generate_rune(floor)
        record_rune(r.rune_id)
        display_msg(f"{Colors.CYAN}Trovi una runa: {r.display_name}! (Si incastona al Falò){Colors.RESET}")
        player.inventory.append(r)
    scroll_drop(player, floor, source)  # le stesse fonti possono custodire anche una pergamena
