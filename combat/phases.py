"""Le fasi dei boss: quando scattano e cosa cambiano, e gli scudi (`_absorb`)."""
from typing import List

from ui import Colors, display_msg
from data_manager import GAME_DATA, MULTIPLIERS, get_element_icon
from codex import record_phase
from entities import STATUS_NAMES


class Phases:
    """Metodi di `CombatSession` (vedi `combat/session.py`)."""

    def check_phase(self) -> bool:
        """Se il boss è sceso sotto la soglia della sua prossima fase, ci entra. True se ha cambiato fase."""
        e = self.enemy
        changed = False
        while e.hp > 0 and e.phase < len(e.phases) and e.hp * 100 <= e.max_hp * e.phases[e.phase]["at_pct"]:
            ph = e.phases[e.phase]
            e.phase += 1
            changed = True
            record_phase(e.base_name, e.phase)
            display_msg(f"\n{Colors.RED}{Colors.BOLD}⚠ {e.name.upper()}: {ph['name'].upper()}{Colors.RESET}\n{Colors.YELLOW}{ph['text']}{Colors.RESET}")
            for line in self._apply_phase(ph): display_msg(f"{Colors.MAGENTA}  · {line}{Colors.RESET}")
        if changed: self.intent = None
        return changed

    def _apply_phase(self, ph: dict) -> List[str]:
        """Applica gli effetti di una fase e restituisce cosa è cambiato, da mostrare al giocatore."""
        e, out = self.enemy, []
        if "element" in ph:
            element = ph["element"]
            if element == "counter":
                # Diventa l'elemento che colpisce meglio la tua armatura
                armor = self.player.armor.element
                element = max(GAME_DATA["elements"]["list"], key=lambda el: (MULTIPLIERS.get(el, {}).get(armor, 1.0), el == e.element))
            e.element, e.mark = element, None
            out.append(f"Ora è di elemento {get_element_icon(element)}.")
        if "atk_mult" in ph:
            e.atk = int(e.atk * ph["atk_mult"])
            out.append(f"Attacco +{round((ph['atk_mult'] - 1) * 100)}%.")
        if "heal_pct" in ph:
            healed = min(e.max_hp - e.hp, e.max_hp * ph["heal_pct"] // 100)
            e.hp += healed
            out.append(f"Recupera {healed} HP ({e.hp}/{e.max_hp}).")
        if "shield_pct" in ph:
            e.shield += e.max_hp * ph["shield_pct"] // 100
            out.append(f"Uno scudo di {e.shield} assorbe i danni dei tuoi attacchi.")
        if "ward" in ph:
            e.ward = ph["ward"]
            out.append(f"Scaglie: i tuoi attacchi fanno il {round(ph['ward'] * 100)}% dei danni finché una reazione elementale non le infrange.")
        if "status_inflict" in ph:
            e.status_inflict = dict(ph["status_inflict"])
            out.append(f"I suoi colpi infliggono {STATUS_NAMES[ph['status_inflict']['type']]} ({ph['status_inflict']['chance']}%).")
        if "moves" in ph:
            e.moves = dict(ph["moves"])
            for move, w in getattr(e, "extra_moves", {}).items(): e.moves[move] = e.moves.get(move, 0) + w
            new = [self._move(m)["name"] for m in ph["moves"] if m not in ("attack",)]
            out.append("Mosse: " + ", ".join(new) + ".")
        return out

    def _absorb(self, dmg: int, eff: str) -> tuple:
        """Scaglie e scudo riducono i danni degli attacchi dell'eroe."""
        if self.enemy.ward is not None:
            dmg = int(dmg * self.enemy.ward)
            eff += f" {Colors.BLUE}[SCAGLIE]{Colors.RESET}"
        if self.enemy.shield > 0:
            # Le armi con shield_mult consumano lo scudo più in fretta: ogni punto di danno ne toglie shield_mult
            mult = self.player.weapon.traits.get("shield_mult", 1)
            taken = min(self.enemy.shield, dmg * mult)
            self.enemy.shield -= taken
            dmg -= -(-taken // mult)
            eff += f" {Colors.BLUE}[SCUDO -{taken}{', infranto' if not self.enemy.shield else ''}]{Colors.RESET}"
        return dmg, eff
