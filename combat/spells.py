"""Gli incantesimi in combattimento: Silenzio, scelta, danni e lancio (`magic.py` ha i dati e il costo)."""
import effects
import magic
import nemesis
from ui import Colors, clear_screen, interactive_menu, display_msg, wait_enter
from data_manager import MULTIPLIERS, get_element_icon
from codex import record_spell
from entities import STATUS_NAMES


class Spells:
    """Metodi di `CombatSession` (vedi `combat/session.py`)."""

    def spells_muted(self) -> str:
        """Perché ora non si possono lanciare incantesimi (Silenzio del nemico o Gas del Silenzio), o "" se si può."""
        if any(r.ignore_silence for r in self.player.relic_effects): return ""
        if self.mute_turns: return f"Incantesimi ammutoliti dal Silenzio ({self.mute_turns} turni)"
        if self.silenced: return "Incantesimi soffocati dal gas"
        return ""

    def choose_spell(self):
        """Il menu degli incantesimi: quello scelto, o None per tornare indietro (non costa il turno)."""
        options = [magic.label(self.player, sid) for sid in self.player.spells] + ["Indietro"]
        idx = interactive_menu(options, f"\n{Colors.CYAN}{Colors.BOLD}--- INCANTESIMI --- ✨ {self.player.ether}/{self.player.max_ether()} Etere{Colors.RESET}")
        clear_screen()
        if not 0 <= idx < len(self.player.spells): return None
        sid = self.player.spells[idx]
        fx = magic.spell(sid)["effects"]
        if self.player.ether < magic.cost(self.player, sid):
            display_msg(f"\n{Colors.RED}-> Non hai abbastanza Etere per {magic.spell(sid)['name']}.{Colors.RESET}")
            return None
        if fx.get("escape") and self.enemy.is_boss:
            display_msg(f"\n{Colors.RED}-> Dai boss non si fugge, nemmeno con il vento.{Colors.RESET}")
            return None
        if fx.get("weaken_pct") and self.weakened:
            display_msg(f"\n{Colors.RED}-> {self.enemy.name} porta già la tua Maledizione.{Colors.RESET}")
            return None
        return sid

    def spell_damage(self, spell_id: str, pct: int) -> int:
        """Danni di un incantesimo: ATK × pct, elemento contro il nemico, Arcano (prima di Guardia, Scaglie e scudo)."""
        element = magic.spell(spell_id)["element"]
        mult = MULTIPLIERS.get(element, {}).get(self.enemy.element, 1.0)
        nem = getattr(self.enemy, "nemesis", None)
        if nem: mult *= nemesis.spell_resisted(nem, element)
        power = 100 + effects.total(self.player, "spell_pct") + self.player.weapon.traits.get("spell_pct", 0)
        return max(1, int(self.player.get_total_atk() * pct / 100 * mult) * power // 100)

    def cast_spell(self, spell_id: str) -> bool:
        """Lancia un incantesimo: costa il turno e il suo Etere. False se il nemico muore."""
        s, fx = magic.spell(spell_id), magic.spell(spell_id)["effects"]
        self.player.ether -= magic.cost(self.player, spell_id)
        self.player.run_tracker["spells_cast"] = self.player.run_tracker.get("spells_cast", 0) + 1
        record_spell(spell_id)
        display_msg(f"\n{Colors.CYAN}-> {s['icon']} Lanci {s['name']}!{Colors.RESET}")
        if fx.get("cleanse"):
            removed = [STATUS_NAMES[k] for k in ("poison", "bleed") if self.player.statuses.pop(k, None)]
            if removed: display_msg(f"{Colors.CYAN}Ti liberi da {' e '.join(removed)}.{Colors.RESET}")
        if "heal_pct" in fx:
            healed = self.player.heal(self.player.max_hp * fx["heal_pct"] // 100)
            display_msg(f"{Colors.GREEN}Recuperi {healed} HP. ({self.player.hp}/{self.player.max_hp}){Colors.RESET}")
        if "def_pct" in fx:
            self.spell_def += self.player.armor.defense * fx["def_pct"] // 100
            display_msg(f"{Colors.CYAN}La pelle ti si indurisce: +{self.spell_def} Difesa per il resto dello scontro.{Colors.RESET}")
        if "weaken_pct" in fx:
            self.weakened = True
            self.enemy.atk = max(1, self.enemy.atk * (100 - fx["weaken_pct"]) // 100)
            display_msg(f"{Colors.MAGENTA}{self.enemy.name} si indebolisce: ATK {self.enemy.atk}.{Colors.RESET}")
        if fx.get("escape"):
            self.player.run_tracker["escapes"] += 1
            display_msg(f"{Colors.YELLOW}Il vento ti solleva e ti porta lontano dallo scontro.{Colors.RESET}")
            wait_enter("\nPremi INVIO...")
            return False
        if fx.get("dispel") and (self.enemy.shield or self.enemy.ward is not None):
            self.enemy.shield, self.enemy.ward = 0, None
            display_msg(f"{Colors.YELLOW}Lo scudo e le Scaglie di {self.enemy.name} si dissolvono!{Colors.RESET}")
        if "damage_pct" in fx:
            pct, eff = fx["damage_pct"], ""
            if "detonate_pct" in fx and self.enemy.mark:
                pct, eff = fx["detonate_pct"], f" {Colors.MAGENTA}[DETONAZIONE {get_element_icon(self.enemy.mark[0])}]{Colors.RESET}"
                self.enemy.mark = None
            dmg = self.spell_damage(spell_id, pct)
            if MULTIPLIERS.get(s["element"], {}).get(self.enemy.element, 1.0) > 1.0: eff += f" {Colors.GREEN}[SUPER EFFICACE!]{Colors.RESET}"
            if self.intent == "guard":
                dmg = int(dmg * self._move("guard")["damage_taken_mult"])
                eff += f" {Colors.BLUE}[GUARDIA]{Colors.RESET}"
            dmg, eff = self._absorb(dmg, eff)
            nem = getattr(self.enemy, "nemesis", None)
            if nem and nemesis.resisted(nem, s["element"]) < 1:
                dmg = int(dmg * nemesis.resisted(nem, s["element"]))
                eff += f" {Colors.BLUE}[RESISTE]{Colors.RESET}"
            self.enemy.hp -= dmg
            display_msg(f"{s['name']} infligge {Colors.CYAN}{dmg} danni{Colors.RESET} a {self.enemy.name}!{eff}")
            if "drain_pct" in fx and dmg > 0:
                healed = self.player.heal(dmg * fx["drain_pct"] // 100)
                if healed: display_msg(f"{Colors.GREEN}Assorbi {healed} HP.{Colors.RESET}")
            if "status" in fx and self.enemy.hp > 0:
                st = fx["status"]
                self.enemy.statuses[st["type"]] = max(self.enemy.statuses.get(st["type"], 0), st["duration"])
                display_msg(f"{Colors.MAGENTA}{self.enemy.name}: {STATUS_NAMES[st['type']]} per {st['duration']} turni.{Colors.RESET}")
            if s["element"] != "Normale": self.apply_element(s["element"])
        if self.enemy.hp <= 0:
            self.on_enemy_death()
            return False
        return True
