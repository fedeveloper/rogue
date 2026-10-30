"""Marchi e reazioni elementali: l'elemento lascia un marchio, il secondo lo fa reagire."""
import effects
import magic
from ui import Colors, display_msg
from data_manager import GAME_DATA, get_element_icon
from codex import record_reaction
from constants import ELEMENTAL_CHAIN_ETHER
from entities import STATUS_NAMES
from combat.rules import reaction_key


class Reactions:
    """Metodi di `CombatSession` (vedi `combat/session.py`)."""

    def apply_element(self, element: str):
        """Marchia il nemico con un elemento; se porta già un marchio di un elemento compatibile, scatena la reazione."""
        if not element or element == "Normale" or self.enemy.hp <= 0: return
        mark = self.enemy.mark
        if mark and mark[0] != element and (key := reaction_key(mark[0], element)):
            self._trigger_reaction(key)
            return
        if not mark or mark[0] != element:
            display_msg(f"{Colors.CYAN}{self.enemy.name} porta il marchio {get_element_icon(element)}.{Colors.RESET}")
        self.enemy.mark = [element, GAME_DATA["elements"]["marks"]["duration"] + effects.total(self.player, "mark_duration_add")]

    def _trigger_reaction(self, key: str):
        r = GAME_DATA["elements"]["reactions"][key]
        self.enemy.mark = None
        if self.enemy.ward is not None:
            self.enemy.ward = None
            display_msg(f"{Colors.YELLOW}{Colors.BOLD}La reazione infrange le Scaglie di {self.enemy.name}!{Colors.RESET}")
        record_reaction(key)
        self.player.run_tracker["reactions"] = self.player.run_tracker.get("reactions", 0) + 1
        self.player.gain_ether(magic.rules()["gain"]["reaction"])
        if self.player.has_mastery_effect("elemental_chain"):
            self.player.gain_ether(ELEMENTAL_CHAIN_ETHER)
        msg = f"{Colors.MAGENTA}{Colors.BOLD}⚡ REAZIONE: {r['icon']} {r['name'].upper()}!{Colors.RESET}"
        if r.get("bonus_pct"):
            dmg = self.player.get_total_atk() * r["bonus_pct"] // 100 * (100 + effects.total(self.player, "reaction_dmg_pct")) // 100
            self.enemy.hp -= dmg
            msg += f" {Colors.CYAN}{dmg} danni extra.{Colors.RESET}"
        if r.get("status"):
            s_type, turns = r["status"]["type"], r["status"]["duration"]
            self.enemy.statuses[s_type] = max(self.enemy.statuses.get(s_type, 0), turns)
            msg += f" {Colors.MAGENTA}{self.enemy.name}: {STATUS_NAMES[s_type]}.{Colors.RESET}"
        display_msg(msg)
        for relic in self.player.relic_effects: relic.on_reaction(self, key)

    def _tick_enemy_conditions(self):
        """Fine del turno del nemico: scadono marchio, Accecato e Impantanato."""
        if self.enemy.mark:
            self.enemy.mark[1] -= 1
            if self.enemy.mark[1] <= 0: self.enemy.mark = None
        for s in [s for s in self.enemy.statuses if s in ("blind", "slow")]:
            self.enemy.statuses[s] -= 1
            if self.enemy.statuses[s] <= 0: del self.enemy.statuses[s]
