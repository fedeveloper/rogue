"""Il turno dell'eroe: menu, attacco (precisione, danni, critici, colpi a segno), difesa e fuga."""
import random

import runes as rune_rules
import attributes
import effects
import magic
import nemesis
from ui import Colors, clear_screen, interactive_menu, display_msg, wait_enter
from data_manager import GAME_DATA, PROFILE_MANAGER, MULTIPLIERS
from constants import AMBUSH_DMG_PCT
from entities import STATUS_NAMES
from inventory_menu import show_inventory_menu


class PlayerActions:
    """Metodi di `CombatSession` (vedi `combat/session.py`)."""

    def _calc_hit_chance(self, multiplier: float) -> int:
        slow = GAME_DATA["elements"]["conditions"]["slow"] if "slow" in self.enemy.statuses else 0
        return self.player.get_hit_chance(self.enemy.base_dodge - slow, multiplier)

    def attack_multiplier(self) -> float:
        multiplier = MULTIPLIERS.get(self.player.weapon.element, {}).get(self.enemy.element, 1.0)
        for r in self.player.relic_effects: multiplier = r.modify_multiplier(multiplier)
        return multiplier

    def _calc_base_damage(self, multiplier: float) -> tuple[int, str]:
        dmg_dealt = int(max(1, self.player.get_total_atk() + random.randint(-1, 2)) * multiplier)
        eff = f"{Colors.GREEN}[SUPER EFFICACE!]{Colors.RESET}" if multiplier > 1.0 else f"{Colors.RED}[Poco efficace...]{Colors.RESET}" if multiplier < 1.0 else ""
        return self.player.weapon.on_attack(dmg_dealt, eff)

    def execute_player_attack(self) -> bool:
        cancel_attack = False
        for r in self.player.relic_effects:
            if not r.on_before_attack(self): cancel_attack = True
        if cancel_attack: return False

        multiplier = self.attack_multiplier()
        
        was_focused = self.focused_attack
        if self.focused_attack:
            hit_chance = 100
            dmg_dealt = int(max(1, self.player.get_total_atk() + random.randint(-1, 2)) * multiplier * 2)
            eff = f"{Colors.GREEN}[CRITICO!]{Colors.RESET} " + (f"{Colors.GREEN}[SUPER EFFICACE!]{Colors.RESET}" if multiplier > 1.0 else "")
            self.focused_attack = False
        else:
            hit_chance = self._calc_hit_chance(multiplier)
            dmg_dealt, eff = self._calc_base_damage(multiplier)
        
        if self.enemy.is_boss:
            dmg_dealt = int(dmg_dealt * (1 + effects.total(self.player, "boss_dmg_pct") / 100))

        crit = self.player.get_crit_chance()
        if crit > 0 and not was_focused and random.randint(1, 100) <= crit:
            dmg_dealt *= 2
            eff += f" {Colors.MAGENTA}[CRITICO!]{Colors.RESET}"

        # Imboscata (Assassino): il primo attacco di ogni scontro, anche se manca, consuma il bonus.
        # Non si somma all'attacco concentrato, che è già un critico garantito.
        ambush = self.player.assassin_ambush and self.first_player_attack and not was_focused
        first_strike = self.first_player_attack and effects.total(self.player, "first_strike_pct")
        self.first_player_attack = False
        if ambush:
            dmg_dealt = dmg_dealt * AMBUSH_DMG_PCT // 100
            eff += f" {Colors.MAGENTA}[IMBOSCATA!]{Colors.RESET}"

        self.player.run_tracker["floor_attacks"] += 1
        if random.randint(1, 100) <= hit_chance:
            self.player.run_tracker["floor_hits"] += 1
            self.player.gain_ether(magic.rules()["gain"]["hit"] + effects.total(self.player, "ether_on_hit"))
            dmg_dealt = int(dmg_dealt * self.player.get_class_damage_multiplier())
            # L'attributo con cui scala l'arma (Forza, Destrezza o Arcano) e i talenti che aumentano i danni
            dmg_dealt = dmg_dealt * (100 + attributes.weapon_bonus(self.player) + effects.total(self.player, "dmg_pct")) // 100
            # Rune dell'arma: Contrasto sui colpi Super Efficaci, Agguato sul primo attacco dello scontro
            if multiplier > 1.0 and effects.total(self.player, "super_effective_pct"):
                dmg_dealt = dmg_dealt * (100 + effects.total(self.player, "super_effective_pct")) // 100
            if first_strike:
                dmg_dealt = dmg_dealt * (100 + first_strike) // 100
                eff += f" {Colors.MAGENTA}[AGGUATO]{Colors.RESET}"
            if multiplier > 1.0 and self.enemy.is_boss:
                if "super_effective_hits" not in self.player.run_tracker: self.player.run_tracker["super_effective_hits"] = 0
                self.player.run_tracker["super_effective_hits"] += 1
            
            for r in self.player.relic_effects:
                dmg_dealt, eff = r.on_attack(self, dmg_dealt, multiplier, eff)

            if self.resonance == "Tenebra":
                dmg_dealt += int(self._resonance_value("Tenebra"))
                eff += f" {Colors.MAGENTA}[TENEBRA]{Colors.RESET}"
            if self.intent == "guard":
                if self.player.weapon.traits.get("guard_break"):
                    eff += f" {Colors.YELLOW}[SFONDI LA GUARDIA]{Colors.RESET}"
                else:
                    dmg_dealt = int(dmg_dealt * self._move("guard")["damage_taken_mult"])
                    eff += f" {Colors.BLUE}[GUARDIA]{Colors.RESET}"
            dmg_dealt, eff = self._absorb(dmg_dealt, eff)
            nem = getattr(self.enemy, "nemesis", None)
            if nem and nemesis.resisted(nem, self.player.weapon.element) < 1:
                dmg_dealt = int(dmg_dealt * nemesis.resisted(nem, self.player.weapon.element))
                eff += f" {Colors.BLUE}[RESISTE]{Colors.RESET}"
            
            self.enemy.hp -= dmg_dealt
            display_msg(f"\n-> Colpisci con {self.player.weapon.name} infliggendo {Colors.CYAN}{dmg_dealt} danni!{Colors.RESET} {eff}")
            self.apply_element(self.player.weapon.element)
            
            for r in self.player.relic_effects: r.on_attack_landed(self, multiplier)

            ls = self.player.get_lifesteal() + dmg_dealt * effects.total(self.player, "lifesteal_pct") // 100
            stolen = self.player.heal(ls) if ls > 0 else 0
            if stolen > 0: display_msg(f"{Colors.RED}Rubavita: assorbi {stolen} HP!{Colors.RESET}")
            if self.resonance == "Luce":
                healed = self.player.heal(int(self._resonance_value("Luce")))
                if healed > 0: display_msg(f"{Colors.YELLOW}✨ Risonanza di Luce: +{healed} HP!{Colors.RESET}")
            if self.resonance == "Fuoco":
                self.burn_dmg += int(self._resonance_value("Fuoco"))

            for s_type, key, turns in rune_rules.ON_HIT_STATUSES:
                chance = effects.total(self.player, key)
                if chance and self.enemy.hp > 0 and random.randint(1, 100) <= chance:
                    self.enemy.statuses[s_type] = max(self.enemy.statuses.get(s_type, 0), turns)
                    display_msg(f"{Colors.MAGENTA}La runa colpisce: {self.enemy.name} è afflitto da {STATUS_NAMES[s_type].upper()}!{Colors.RESET}")
            s_data = self.player.weapon.status_inflict
            if s_data and self.enemy.hp > 0 and random.randint(1, 100) <= s_data.get("chance", 100):
                s_type = s_data["type"]
                self.enemy.statuses[s_type] = max(self.enemy.statuses.get(s_type, 0), s_data["duration"])
                display_msg(f"{Colors.MAGENTA}{self.enemy.name} è afflitto da {STATUS_NAMES.get(s_type, s_type).upper()}!{Colors.RESET}")
            
            self.player.on_attack_landed(dmg_dealt, multiplier)
        else:
            display_msg(f"\n{Colors.YELLOW}-> Fallisci! {self.enemy.name} schiva.{Colors.RESET}")
        
        if self.enemy.hp <= 0:
            self.on_enemy_death()
            return False
        return True

    def execute_player_defense(self) -> bool:
        """La difesa della classe (defenses.json). False se la tecnica abbatte il nemico."""
        defense = GAME_DATA["defenses"].get(self.def_type, {})
        self.is_defending = True
        self.player.gain_ether(magic.rules()["gain"]["defend"])
        self.player.on_defense_started()
        if effects.total(self.player, "defend_heal_pct"):
            healed = self.player.heal(max(1, self.player.max_hp * effects.total(self.player, "defend_heal_pct") // 100))
            if healed: display_msg(f"{Colors.GREEN}Runa della Quiete: recuperi {healed} HP.{Colors.RESET}")
        if self.def_type == "silenced":
            display_msg(f"\n{Colors.BLUE}-> Ti ripari come puoi: nel gas la tecnica non ti riesce.{Colors.RESET}")
        elif self.def_type == "counter":
            display_msg(f"\n{Colors.BLUE}-> Sollevi la guardia, pronto a sfruttare l'attacco nemico!{Colors.RESET}")
        elif self.def_type == "focus":
            self.focused_attack = True
            healed = self.player.heal(max(1, self.player.max_hp * defense["heal_pct"] // 100))
            display_msg(f"\n{Colors.BLUE}-> Studi il nemico nell'ombra, e riprendi fiato. Il tuo prossimo attacco sarà devastante!"
                        + (f" {Colors.GREEN}Recuperi {healed} HP.{Colors.RESET}" if healed else f"{Colors.RESET}"))
        elif self.def_type == "recovery":
            if self.player.cursed:
                display_msg(f"\n{Colors.BLUE}-> Ti difendi, ma la Maledizione blocca il tuo recupero magico.{Colors.RESET}")
            else:
                heal_amt = max(1, self.player.max_hp * defense["heal_pct"] // 100)
                self.player.heal(heal_amt)
                display_msg(f"\n{Colors.BLUE}-> Evochi una barriera vitale. {Colors.GREEN}Recuperi {heal_amt} HP!{Colors.RESET}")
        elif self.def_type == "cleanse":
            purified = [STATUS_NAMES[s] for s in ("poison", "bleed") if self.player.statuses.pop(s, None)]
            healed = self.player.heal(max(1, self.player.max_hp * defense["heal_pct"] // 100))
            display_msg(f"\n{Colors.BLUE}-> Pronunci il Voto e alzi lo scudo."
                        + (f" {Colors.CYAN}Ti liberi da {' e '.join(purified)}.{Colors.RESET}" if purified else "")
                        + (f" {Colors.GREEN}Recuperi {healed} HP.{Colors.RESET}" if healed else f"{Colors.RESET}"))
        elif self.def_type == "mark":
            healed = self.player.heal(max(1, self.player.max_hp * defense["heal_pct"] // 100))
            display_msg(f"\n{Colors.BLUE}-> Ti ripari, bevi un sorso e lanci una fiala contro il nemico."
                        + (f" {Colors.GREEN}Recuperi {healed} HP.{Colors.RESET}" if healed else f"{Colors.RESET}"))
            self.apply_element(self.player.weapon.element)
        elif self.def_type == "prism":
            gained = self.player.gain_ether(defense["ether_gain"])
            healed = self.player.heal(max(1, self.player.max_hp * defense["heal_pct"] // 100))
            display_msg(f"\n{Colors.BLUE}-> Gli elementi ti girano attorno come un prisma."
                        + (f" {Colors.GREEN}Recuperi {healed} HP.{Colors.RESET}" if healed else "")
                        + (f" {Colors.CYAN}+{gained} Etere ({self.player.ether}/{self.player.max_ether()}).{Colors.RESET}" if gained else f"{Colors.RESET}"))
        elif self.def_type == "siphon":
            stolen = min(self.enemy.hp, max(1, self.enemy.max_hp * defense["drain_pct"] // 100))
            self.enemy.hp -= stolen
            healed = self.player.heal(stolen)
            display_msg(f"\n{Colors.BLUE}-> Il sudario si stringe attorno al nemico: gli strappi {stolen} HP."
                        + (f" {Colors.GREEN}Recuperi {healed} HP.{Colors.RESET}" if healed else f"{Colors.RESET}"))
        if self.enemy.hp <= 0:
            self.on_enemy_death()
            return False
        return True

    def player_turn(self) -> bool:
        """Turno del giocatore. Ritorna False se lo scontro finisce (fuga, morte del nemico o del giocatore).

        Le voci che non consumano il turno (statistiche, inventario chiuso senza usare nulla,
        fuga impossibile dai boss) ripresentano il menu nello stesso ciclo.
        """
        while True:
            # I bonus di Risonanza devono restare attivi per tutto il combattimento
            self._apply_resonance_bonuses()
            self.is_defending = False

            self.def_type, self.def_txt = self.player.get_defense_action()
            if self.silenced: self.def_type, self.def_txt = "silenced", "Difesa (Dimezza danni; il gas soffoca la tecnica)"
            if self.sealed: self.def_txt = f"{Colors.RED}🔒 Difesa sigillata (non puoi difenderti in questo turno){Colors.RESET}"
            if self.intent is None: self.choose_intent()

            prompt = (f"\n{Colors.BOLD}--- ⚔️ IN COMBATTIMENTO ⚔️ ---{Colors.RESET}\nTu: {Colors.GREEN}{self.player.hp}/{self.player.max_hp} HP{Colors.RESET}"
                      + (f" {Colors.CYAN}✨ {self.player.ether}/{self.player.max_ether()} Etere{Colors.RESET}" if self.player.spells else "") + " | "
                      f"{self.enemy.name}: {Colors.RED}{self.enemy.hp}/{self.enemy.max_hp} HP{Colors.RESET}{self.enemy_status_text()}\n"
                      f"Intento del nemico: {self.intent_text()}")
            # Le azioni per nome: la voce degli incantesimi c'è solo per chi ne conosce
            actions = [("attack", "Attacca"), ("defend", self.def_txt)]
            if self.player.spells:
                muted = self.spells_muted()
                actions.append(("spell", f"{Colors.RED}🤫 {muted}{Colors.RESET}" if muted else f"Lancia un incantesimo ({self.player.ether}/{self.player.max_ether()} Etere)"))
            actions += [("inventory", "Apri Inventario (Usa oggetto = Costa Turno)"), ("stats", "Statistiche Eroe"), ("flee", "Tenta la Fuga")]

            idx = interactive_menu([text for _, text in actions], prompt)
            clear_screen()
            action = actions[idx][0] if 0 <= idx < len(actions) else None

            if action == "attack":
                return self.execute_player_attack()

            elif action == "spell":
                if self.spells_muted():
                    display_msg(f"\n{Colors.RED}-> Apri la bocca, ma non esce nessuna parola: ora non puoi lanciare incantesimi.{Colors.RESET}")
                    continue
                spell_id = self.choose_spell()
                if spell_id is None: continue
                return self.cast_spell(spell_id)

            elif action == "defend":
                if self.sealed:
                    display_msg(f"\n{Colors.RED}-> Il Sigillo ti blocca: in questo turno non puoi difenderti.{Colors.RESET}")
                    continue
                return self.execute_player_defense()

            elif action == "inventory":
                action = show_inventory_menu(self.player, in_combat=True)
                self.refresh_resonance()
                if action == "smoke_bomb":
                    if self.enemy.is_boss:
                        display_msg(f"\n{Colors.RED}-> Il fumo si dirada all'istante: impossibile fuggire dai Boss!{Colors.RESET}")
                        return True
                    self.player.run_tracker["escapes"] += 1
                    return False
                elif action == "fiala_caos":
                    caos_dmg = random.randint(10, 100)
                    self.enemy.hp -= caos_dmg
                    display_msg(f"{Colors.MAGENTA}Esplosione caotica: {caos_dmg} danni puri!{Colors.RESET}")
                    if self.enemy.hp <= 0:
                        self.on_enemy_death()
                        return False
                    return True
                elif action == "turn_used" or action == "antidote":
                    clear_screen()
                    return True

            elif action == "stats":
                from inventory_menu import show_player_stats
                show_player_stats(self.player, self)

            elif action == "flee":
                if self.enemy.is_boss:
                    display_msg(f"\n{Colors.RED}-> Impossibile fuggire dai Boss!{Colors.RESET}")
                    continue

                if random.randint(1, 100) <= self._calc_escape_chance():
                    display_msg(f"\n{Colors.YELLOW}-> Sei riuscito a scappare!{Colors.RESET}")
                    self.player.run_tracker["escapes"] += 1
                    wait_enter("\nPremi INVIO...")
                    return False
                display_msg(f"\n{Colors.RED}-> Tentativo di fuga fallito!{Colors.RESET}")
                return True

    def _calc_escape_chance(self) -> int:
        f_chance = 20 + self.player.get_dodge() - self.enemy.base_dodge + (20 if PROFILE_MANAGER.get_perk("scarpisti", False) else 0)
        f_chance += effects.total(self.player, "escape")
        f_chance = max(10, min(90, f_chance))
        for r in self.player.relic_effects:
            mod = r.get_escape_modifier()
            if mod > 0: f_chance = mod
        return f_chance
